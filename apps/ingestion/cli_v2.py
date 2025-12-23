"""
Ingestion CLI - Full Pipeline (STEP 4).

Supports all stages:
- discover: File scanning + hash
- register: DB metadata (insurer/product/document)
- parse: PDF → text
- chunk: Text → chunks (is_synthetic=false)
- embed: Chunks → embeddings
- extract: Entity + amount extraction
- normalize: Coverage alias mapping
- synthetic: Mixed chunk splitting (Amount Bridge)
- validate: Report generation
- run-all: Execute full pipeline
"""
import argparse
import sys
from pathlib import Path

from .db import db_transaction
from .discover import discover
from .register import register_manifest_rows
from .parse import parse_all_documents
from .chunk import chunk_all_documents
from .embed import embed_all_chunks
from .extract import extract_all_entities
from .normalize import normalize_all_coverages
from .synthetic import generate_all_synthetic_chunks
from .validate import generate_validation_report


def cmd_discover(args):
    """Discover command."""
    print("=" * 60)
    print("Discover: File scanning + hash calculation")
    print("=" * 60)

    rows = discover(args.manifest, args.base_path)
    print(f"✅ Discovered {len(rows)} documents")

    for row in rows:
        print(f"  - {row.insurer_code}/{row.product_code}: {row.document_type}")
        print(f"    Hash: {row.file_hash}")


def cmd_register(args):
    """Register command."""
    print("=" * 60)
    print("Register: DB UPSERT (insurer/product/document)")
    print("=" * 60)

    rows = discover(args.manifest, args.base_path)

    with db_transaction() as conn:
        stats = register_manifest_rows(conn, rows)

    print(f"✅ Register completed")
    print(f"  - Insurers: {stats['insurers_processed']}")
    print(f"  - Products: {stats['products_processed']}")
    print(f"  - Documents: {stats['documents_processed']}")


def cmd_parse(args):
    """Parse command."""
    print("=" * 60)
    print("Parse: PDF → text extraction")
    print("=" * 60)

    output_dir = args.base_path / "data/derived"

    with db_transaction() as conn:
        parsed_docs = parse_all_documents(
            conn, args.base_path, output_dir,
            insurer_code=args.insurer,
            document_type=args.doc_type
        )

    print(f"✅ Parse completed")
    print(f"  - Documents parsed: {len(parsed_docs)}")


def cmd_chunk(args):
    """Chunk command."""
    print("=" * 60)
    print("Chunk: Text → chunks (is_synthetic=false)")
    print("=" * 60)

    derived_dir = args.base_path / "data/derived"

    with db_transaction() as conn:
        stats = chunk_all_documents(
            conn, derived_dir,
            insurer_code=args.insurer,
            document_type=args.doc_type,
            max_chunk_size=args.chunk_size
        )

    print(f"✅ Chunk completed")
    print(f"  - Documents: {stats['documents_processed']}")
    print(f"  - Chunks created: {stats['chunks_created']}")
    print(f"  - Errors: {stats['errors']}")


def cmd_embed(args):
    """Embed command."""
    print("=" * 60)
    print("Embed: Generate embeddings")
    print("=" * 60)

    with db_transaction() as conn:
        stats = embed_all_chunks(
            conn,
            model=args.embed_model,
            batch_size=args.batch_size,
            insurer_code=args.insurer,
            limit=args.limit
        )

    print(f"✅ Embed completed")
    print(f"  - Processed: {stats['processed']}")
    print(f"  - Success: {stats['success']}")
    print(f"  - Failed: {stats['failed']}")


def cmd_extract(args):
    """Extract command."""
    print("=" * 60)
    print("Extract: Entity + amount extraction")
    print("=" * 60)

    with db_transaction() as conn:
        stats = extract_all_entities(
            conn,
            model=args.extract_model,
            insurer_code=args.insurer,
            limit=args.limit
        )

    print(f"✅ Extract completed")
    print(f"  - Chunks: {stats['chunks_processed']}")
    print(f"  - Entities: {stats['entities_extracted']}")
    print(f"  - Amounts: {stats['amounts_extracted']}")


def cmd_normalize(args):
    """Normalize command."""
    print("=" * 60)
    print("Normalize: Coverage alias mapping")
    print("=" * 60)

    with db_transaction() as conn:
        stats = normalize_all_coverages(conn)

    print(f"✅ Normalize completed")
    print(f"  - Insurers: {stats['insurers_processed']}")
    print(f"  - Matched: {stats['total_matched']}")
    print(f"  - Unmapped: {stats['total_unmapped']}")

    if stats["unmapped_by_insurer"]:
        print(f"\n⚠️  Unmapped coverages by insurer:")
        for insurer, names in stats["unmapped_by_insurer"].items():
            print(f"  {insurer}: {len(names)} unmapped")


def cmd_synthetic(args):
    """Synthetic command."""
    print("=" * 60)
    print("Synthetic: Mixed chunk splitting (Amount Bridge only)")
    print("=" * 60)

    with db_transaction() as conn:
        stats = generate_all_synthetic_chunks(
            conn,
            model=args.synthetic_model,
            limit=args.limit
        )

    print(f"✅ Synthetic completed")
    print(f"  - Chunks processed: {stats['chunks_processed']}")
    print(f"  - Synthetic created: {stats['synthetic_created']}")


def cmd_validate(args):
    """Validate command."""
    print("=" * 60)
    print("Validate: Generate report")
    print("=" * 60)

    output_dir = args.base_path / "artifacts/ingestion"

    with db_transaction() as conn:
        report_dir = generate_validation_report(conn, output_dir)

    print(f"✅ Validation completed")
    print(f"  - Report: {report_dir}")


def cmd_run_all(args):
    """Run all stages."""
    print("=" * 60)
    print("Run All: Full ingestion pipeline")
    print("=" * 60)

    # 1. Discover + Register
    print("\n[1/9] Discover + Register")
    rows = discover(args.manifest, args.base_path)
    with db_transaction() as conn:
        register_manifest_rows(conn, rows)
    print("✅ Discover + Register completed")

    # 2. Parse
    print("\n[2/9] Parse")
    output_dir = args.base_path / "data/derived"
    with db_transaction() as conn:
        parse_all_documents(conn, args.base_path, output_dir, insurer_code=args.insurer)
    print("✅ Parse completed")

    # 3. Chunk
    print("\n[3/9] Chunk")
    derived_dir = args.base_path / "data/derived"
    with db_transaction() as conn:
        chunk_all_documents(conn, derived_dir, insurer_code=args.insurer)
    print("✅ Chunk completed")

    # 4. Embed (optional - requires OpenAI key)
    print("\n[4/9] Embed (skipping if no API key)")
    try:
        with db_transaction() as conn:
            stats = embed_all_chunks(conn, insurer_code=args.insurer, limit=10)  # Limited for validation
        if stats['success'] > 0:
            print("✅ Embed completed (sample)")
        else:
            print("⚠️  Embed skipped (no API key or chunks)")
    except Exception as e:
        print(f"⚠️  Embed skipped: {e}")

    # 5. Extract (optional - requires OpenAI key)
    print("\n[5/9] Extract (skipping if no API key)")
    try:
        with db_transaction() as conn:
            stats = extract_all_entities(conn, insurer_code=args.insurer, limit=10)  # Limited for validation
        if stats['chunks_processed'] > 0:
            print("✅ Extract completed (sample)")
        else:
            print("⚠️  Extract skipped (no API key or chunks)")
    except Exception as e:
        print(f"⚠️  Extract skipped: {e}")

    # 6. Normalize
    print("\n[6/9] Normalize")
    with db_transaction() as conn:
        normalize_all_coverages(conn)
    print("✅ Normalize completed")

    # 7. Synthetic (optional - requires OpenAI key)
    print("\n[7/9] Synthetic (skipping if no API key)")
    try:
        with db_transaction() as conn:
            stats = generate_all_synthetic_chunks(conn, limit=5)  # Limited for validation
        if stats['chunks_processed'] > 0:
            print("✅ Synthetic completed (sample)")
        else:
            print("⚠️  Synthetic skipped (no mixed chunks or API key)")
    except Exception as e:
        print(f"⚠️  Synthetic skipped: {e}")

    # 8. Validate
    print("\n[8/9] Validate")
    output_dir = args.base_path / "artifacts/ingestion"
    with db_transaction() as conn:
        generate_validation_report(conn, output_dir)
    print("✅ Validate completed")

    print("\n" + "=" * 60)
    print("✅ Full pipeline completed")
    print("=" * 60)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="inca-RAG-final Ingestion Pipeline")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Common arguments
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--base-path", type=Path, default=Path.cwd(),
                       help="Base path (default: current directory)")
    common.add_argument("--insurer", type=str, help="Filter by insurer code")

    # Discover
    sp_discover = subparsers.add_parser("discover", parents=[common])
    sp_discover.add_argument("--manifest", type=Path, required=True)

    # Register
    sp_register = subparsers.add_parser("register", parents=[common])
    sp_register.add_argument("--manifest", type=Path, required=True)

    # Parse
    sp_parse = subparsers.add_parser("parse", parents=[common])
    sp_parse.add_argument("--doc-type", type=str, help="Filter by document type")

    # Chunk
    sp_chunk = subparsers.add_parser("chunk", parents=[common])
    sp_chunk.add_argument("--doc-type", type=str)
    sp_chunk.add_argument("--chunk-size", type=int, default=1000)

    # Embed
    sp_embed = subparsers.add_parser("embed", parents=[common])
    sp_embed.add_argument("--embed-model", type=str, default="text-embedding-3-small")
    sp_embed.add_argument("--batch-size", type=int, default=100)
    sp_embed.add_argument("--limit", type=int)

    # Extract
    sp_extract = subparsers.add_parser("extract", parents=[common])
    sp_extract.add_argument("--extract-model", type=str, default="gpt-4o")
    sp_extract.add_argument("--limit", type=int)

    # Normalize
    sp_normalize = subparsers.add_parser("normalize", parents=[common])

    # Synthetic
    sp_synthetic = subparsers.add_parser("synthetic", parents=[common])
    sp_synthetic.add_argument("--synthetic-model", type=str, default="gpt-4o")
    sp_synthetic.add_argument("--limit", type=int)

    # Validate
    sp_validate = subparsers.add_parser("validate", parents=[common])

    # Run-all
    sp_run_all = subparsers.add_parser("run-all", parents=[common])
    sp_run_all.add_argument("--manifest", type=Path, required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Route to command
    commands = {
        "discover": cmd_discover,
        "register": cmd_register,
        "parse": cmd_parse,
        "chunk": cmd_chunk,
        "embed": cmd_embed,
        "extract": cmd_extract,
        "normalize": cmd_normalize,
        "synthetic": cmd_synthetic,
        "validate": cmd_validate,
        "run-all": cmd_run_all,
    }

    try:
        commands[args.command](args)
    except Exception as e:
        print(f"\n❌ Command failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
