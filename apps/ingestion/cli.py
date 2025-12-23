"""
Ingestion CLI entry point.

STEP 3-Validate scope: Discover + Register only.
"""
import argparse
import sys
from pathlib import Path

from .db import db_transaction
from .discover import discover
from .register import register_manifest_rows


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="inca-RAG-final Ingestion Pipeline (STEP 3-Validate)"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to docs_manifest CSV file"
    )
    parser.add_argument(
        "--dry-run",
        type=str,
        choices=["true", "false"],
        default="false",
        help="Dry run mode (skip DB writes)"
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path.cwd(),
        help="Base path for resolving relative file paths (default: current directory)"
    )

    args = parser.parse_args()
    dry_run = args.dry_run == "true"

    print("=" * 60)
    print("inca-RAG-final Ingestion Pipeline (STEP 3-Validate)")
    print("=" * 60)
    print(f"Manifest: {args.manifest}")
    print(f"Base path: {args.base_path}")
    print(f"Dry run: {dry_run}")
    print()

    # STEP 1: Discover
    print("[1/2] Discover stage: File scanning + hash calculation")
    try:
        rows = discover(args.manifest, args.base_path)
        print(f"✅ Discovered {len(rows)} documents")
        for row in rows:
            print(f"  - {row.insurer_code}/{row.product_code}: {row.document_type}")
            print(f"    File: {row.file_path}")
            print(f"    Hash: {row.file_hash}")
    except Exception as e:
        print(f"❌ Discover failed: {e}")
        sys.exit(1)

    # STEP 2: Register
    print()
    print("[2/2] Register stage: DB UPSERT (insurer/product/document)")

    if dry_run:
        print("⚠️  Dry run mode: Skipping DB writes")
        print("=" * 60)
        sys.exit(0)

    try:
        with db_transaction() as conn:
            stats = register_manifest_rows(conn, rows)
            print(f"✅ Register completed")
            print(f"  - Insurers processed: {stats['insurers_processed']}")
            print(f"  - Products processed: {stats['products_processed']}")
            print(f"  - Documents processed: {stats['documents_processed']}")
    except Exception as e:
        print(f"❌ Register failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print()
    print("=" * 60)
    print("✅ Ingestion completed successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()
