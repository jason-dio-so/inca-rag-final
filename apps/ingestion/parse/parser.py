"""
PDF parsing implementation.

Strategy:
- Use PyMuPDF (fitz) for PDF text extraction
- Extract page-by-page with metadata
- Store results in data/derived/
- Document type-specific strategies supported
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False

from psycopg2.extensions import connection as PGConnection


class ParsedPage:
    """Represents a single parsed page."""

    def __init__(self, page_number: int, text: str, metadata: Optional[Dict[str, Any]] = None):
        self.page_number = page_number
        self.text = text
        self.metadata = metadata or {}


class ParsedDocument:
    """Represents a parsed document with all pages."""

    def __init__(self, document_id: int, file_path: str, pages: List[ParsedPage]):
        self.document_id = document_id
        self.file_path = file_path
        self.pages = pages

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        return {
            "document_id": self.document_id,
            "file_path": self.file_path,
            "pages": [
                {
                    "page_number": p.page_number,
                    "text": p.text,
                    "metadata": p.metadata
                }
                for p in self.pages
            ]
        }


def extract_text_from_pdf(pdf_path: Path, document_type: str) -> List[ParsedPage]:
    """
    Extract text from PDF file.

    Args:
        pdf_path: Path to PDF file
        document_type: Document type (약관/사업방법서/상품요약서/가입설계서)

    Returns:
        List of ParsedPage objects

    Raises:
        ImportError: If PyMuPDF is not installed
        FileNotFoundError: If PDF file doesn't exist
    """
    if not FITZ_AVAILABLE:
        raise ImportError("PyMuPDF (fitz) is required. Install with: pip install PyMuPDF")

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages = []

    # Open PDF
    doc = fitz.open(str(pdf_path))

    try:
        for page_num in range(len(doc)):
            page = doc[page_num]

            # Extract text
            text = page.get_text()

            # Extract metadata
            metadata = {
                "width": page.rect.width,
                "height": page.rect.height,
                "rotation": page.rotation,
            }

            # Document type-specific processing
            if document_type in ["약관", "terms"]:
                # 약관: Keep original structure, preserve line breaks
                text = text.strip()
            elif document_type in ["사업방법서", "business"]:
                # 사업방법서: Similar to 약관
                text = text.strip()
            elif document_type in ["상품요약서", "summary"]:
                # 상품요약서: May have tables - preserve structure
                text = text.strip()
            elif document_type in ["가입설계서", "proposal"]:
                # 가입설계서: Table-heavy, keep structure
                text = text.strip()

            pages.append(ParsedPage(
                page_number=page_num + 1,  # 1-indexed
                text=text,
                metadata=metadata
            ))

    finally:
        doc.close()

    return pages


def save_parsed_document(parsed_doc: ParsedDocument, output_dir: Path) -> Path:
    """
    Save parsed document to JSON file.

    Args:
        parsed_doc: ParsedDocument object
        output_dir: Output directory (data/derived/)

    Returns:
        Path to saved JSON file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    output_path = output_dir / f"document_{parsed_doc.document_id}.json"

    # Save to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parsed_doc.to_dict(), f, ensure_ascii=False, indent=2)

    return output_path


def parse_document(conn: PGConnection, document_id: int, base_path: Path,
                   output_dir: Path) -> ParsedDocument:
    """
    Parse a single document.

    Args:
        conn: Database connection
        document_id: Document ID to parse
        base_path: Base path for resolving file paths
        output_dir: Output directory for parsed results

    Returns:
        ParsedDocument object

    Raises:
        ValueError: If document not found in DB
    """
    # Fetch document info from DB
    with conn.cursor() as cur:
        cur.execute("""
            SELECT d.document_id, d.document_type, d.file_path
            FROM document d
            WHERE d.document_id = %s
        """, (document_id,))

        row = cur.fetchone()
        if not row:
            raise ValueError(f"Document {document_id} not found in database")

        doc_id, doc_type, file_path = row

    # Resolve file path
    pdf_path = Path(file_path)
    if not pdf_path.is_absolute():
        pdf_path = base_path / file_path

    # Extract text
    pages = extract_text_from_pdf(pdf_path, doc_type)

    # Create ParsedDocument
    parsed_doc = ParsedDocument(
        document_id=doc_id,
        file_path=file_path,
        pages=pages
    )

    # Save to disk
    save_parsed_document(parsed_doc, output_dir)

    return parsed_doc


def parse_all_documents(conn: PGConnection, base_path: Path, output_dir: Path,
                       insurer_code: Optional[str] = None,
                       document_type: Optional[str] = None) -> List[ParsedDocument]:
    """
    Parse all documents (or filtered by insurer/doc_type).

    Args:
        conn: Database connection
        base_path: Base path for resolving file paths
        output_dir: Output directory for parsed results
        insurer_code: Optional filter by insurer code
        document_type: Optional filter by document type

    Returns:
        List of ParsedDocument objects
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

    # Parse each document
    parsed_docs = []
    for doc_id in document_ids:
        try:
            parsed_doc = parse_document(conn, doc_id, base_path, output_dir)
            parsed_docs.append(parsed_doc)
        except Exception as e:
            print(f"⚠️  Failed to parse document {doc_id}: {e}")
            continue

    return parsed_docs
