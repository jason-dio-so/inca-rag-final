"""
Chunking implementation.

Strategy:
- Semantic chunking based on document structure
- Original chunks only (is_synthetic=false)
- Preserve page_number for traceability
- UNIQUE constraint enforced by (document_id, page_number, content hash)
"""
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from psycopg2.extensions import connection as PGConnection


class Chunk:
    """Represents a single chunk."""

    def __init__(self, document_id: int, page_number: int, content: str,
                 meta: Optional[Dict[str, Any]] = None):
        self.document_id = document_id
        self.page_number = page_number
        self.content = content
        self.meta = meta or {}
        self.is_synthetic = False  # Always false for original chunks
        self.synthetic_source_chunk_id = None  # Always None for original chunks
        # Calculate content_hash for idempotency
        self.content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()


def split_text_into_chunks(text: str, page_number: int, max_chunk_size: int = 1000,
                          overlap: int = 100) -> List[str]:
    """
    Split text into chunks with overlap.

    Args:
        text: Input text
        page_number: Page number for metadata
        max_chunk_size: Maximum characters per chunk
        overlap: Overlap between chunks (characters)

    Returns:
        List of chunk strings
    """
    if not text or not text.strip():
        return []

    # Simple sentence-based chunking
    # Split by period, newline, or other delimiters
    sentences = []
    current = ""

    for char in text:
        current += char
        if char in ['.', '\n', '!', '?'] and len(current) > 50:
            sentences.append(current.strip())
            current = ""

    if current.strip():
        sentences.append(current.strip())

    # Combine sentences into chunks
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chunk_size:
            current_chunk += " " + sentence if current_chunk else sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())

            # Start new chunk with overlap
            if overlap > 0 and chunks:
                # Take last N characters from previous chunk
                overlap_text = chunks[-1][-overlap:]
                current_chunk = overlap_text + " " + sentence
            else:
                current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def load_parsed_document(derived_dir: Path, document_id: int) -> Dict[str, Any]:
    """
    Load parsed document JSON.

    Args:
        derived_dir: Path to data/derived/
        document_id: Document ID

    Returns:
        Parsed document dict

    Raises:
        FileNotFoundError: If parsed document doesn't exist
    """
    json_path = derived_dir / f"document_{document_id}.json"

    if not json_path.exists():
        raise FileNotFoundError(f"Parsed document not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_chunks_from_parsed_doc(parsed_doc: Dict[str, Any],
                                  max_chunk_size: int = 1000) -> List[Chunk]:
    """
    Create chunks from parsed document.

    Args:
        parsed_doc: Parsed document dictionary
        max_chunk_size: Maximum chunk size

    Returns:
        List of Chunk objects
    """
    document_id = parsed_doc["document_id"]
    chunks = []

    for page in parsed_doc["pages"]:
        page_number = page["page_number"]
        text = page["text"]

        if not text or not text.strip():
            continue

        # Split text into chunks
        chunk_texts = split_text_into_chunks(text, page_number, max_chunk_size)

        for chunk_text in chunk_texts:
            chunk = Chunk(
                document_id=document_id,
                page_number=page_number,
                content=chunk_text,
                meta={"chunk_method": "semantic_v1"}
            )
            chunks.append(chunk)

    return chunks


def insert_chunk(conn: PGConnection, chunk: Chunk) -> int:
    """
    Insert chunk into database with idempotency via content_hash.

    Args:
        conn: Database connection
        chunk: Chunk object

    Returns:
        chunk_id

    Note:
        Uses ON CONFLICT (document_id, page_number, content_hash) DO NOTHING
        to ensure idempotency. If chunk already exists, retrieves existing chunk_id.
    """
    with conn.cursor() as cur:
        # Try INSERT with content_hash
        cur.execute("""
            INSERT INTO chunk (document_id, page_number, content, content_hash,
                             is_synthetic, synthetic_source_chunk_id, meta)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (document_id, page_number, content_hash) DO NOTHING
            RETURNING chunk_id
        """, (chunk.document_id, chunk.page_number, chunk.content, chunk.content_hash,
              chunk.is_synthetic, chunk.synthetic_source_chunk_id,
              json.dumps(chunk.meta)))

        result = cur.fetchone()

        if result:
            return result[0]

        # If INSERT was skipped (conflict), fetch existing chunk_id
        cur.execute("""
            SELECT chunk_id
            FROM chunk
            WHERE document_id = %s
              AND page_number = %s
              AND content_hash = %s
            LIMIT 1
        """, (chunk.document_id, chunk.page_number, chunk.content_hash))

        result = cur.fetchone()
        if result:
            return result[0]

        raise RuntimeError(f"Failed to insert or retrieve chunk for document {chunk.document_id}")


def chunk_document(conn: PGConnection, document_id: int, derived_dir: Path,
                  max_chunk_size: int = 1000) -> List[int]:
    """
    Chunk a single document.

    Args:
        conn: Database connection
        document_id: Document ID
        derived_dir: Path to data/derived/
        max_chunk_size: Maximum chunk size

    Returns:
        List of chunk_ids
    """
    # Load parsed document
    parsed_doc = load_parsed_document(derived_dir, document_id)

    # Create chunks
    chunks = create_chunks_from_parsed_doc(parsed_doc, max_chunk_size)

    # Insert into DB
    chunk_ids = []
    for chunk in chunks:
        chunk_id = insert_chunk(conn, chunk)
        chunk_ids.append(chunk_id)

    return chunk_ids


def chunk_all_documents(conn: PGConnection, derived_dir: Path,
                       insurer_code: Optional[str] = None,
                       document_type: Optional[str] = None,
                       max_chunk_size: int = 1000) -> Dict[str, int]:
    """
    Chunk all documents (or filtered by insurer/doc_type).

    Args:
        conn: Database connection
        derived_dir: Path to data/derived/
        insurer_code: Optional filter by insurer code
        document_type: Optional filter by document type
        max_chunk_size: Maximum chunk size

    Returns:
        Statistics dictionary
    """
    # Build query
    query = """
        SELECT d.document_id
        FROM document d
        JOIN product p ON d.product_id = p.product_id
        JOIN insurer i ON p.insurer_id = i.insurer_id
        WHERE 1=1
    """
    params = []

    if insurer_code:
        query += " AND i.insurer_code = %s"
        params.append(insurer_code)

    if document_type:
        query += " AND d.document_type = %s"
        params.append(document_type)

    query += " ORDER BY d.document_id"

    # Fetch document IDs
    with conn.cursor() as cur:
        cur.execute(query, tuple(params))
        document_ids = [row[0] for row in cur.fetchall()]

    # Chunk each document
    stats = {
        "documents_processed": 0,
        "chunks_created": 0,
        "errors": 0
    }

    for doc_id in document_ids:
        try:
            chunk_ids = chunk_document(conn, doc_id, derived_dir, max_chunk_size)
            stats["documents_processed"] += 1
            stats["chunks_created"] += len(chunk_ids)
        except FileNotFoundError:
            print(f"⚠️  Skipping document {doc_id}: Parsed file not found (run Parse first)")
            stats["errors"] += 1
        except Exception as e:
            print(f"⚠️  Failed to chunk document {doc_id}: {e}")
            stats["errors"] += 1

    return stats
