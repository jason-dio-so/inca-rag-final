"""
Register stage: UPSERT insurer/product/document to database.
"""
from typing import List

from psycopg2.extensions import connection as PGConnection

from .models import ManifestRow


# Document type priority mapping (as per schema design)
DOC_TYPE_PRIORITY = {
    "약관": 1,
    "terms": 1,
    "사업방법서": 2,
    "business": 2,
    "상품요약서": 3,
    "summary": 3,
    "가입설계서": 4,
    "proposal": 4,
}


def get_doc_type_priority(doc_type: str) -> int:
    """
    Get document type priority.

    Args:
        doc_type: Document type string

    Returns:
        Priority value (1-4)
    """
    return DOC_TYPE_PRIORITY.get(doc_type, 99)


def upsert_insurer(conn: PGConnection, insurer_code: str) -> int:
    """
    Insert or update insurer, return insurer_id.

    Args:
        conn: Database connection
        insurer_code: Insurer code (e.g., SAMSUNG)

    Returns:
        insurer_id
    """
    # Derive insurer name from code (simple mapping for validation)
    insurer_name_map = {
        "SAMSUNG": "삼성화재",
        "HYUNDAI": "현대해상",
        "MERITZ": "메리츠화재",
        "KB": "KB손해보험",
    }
    insurer_name = insurer_name_map.get(insurer_code, insurer_code)

    with conn.cursor() as cur:
        # UPSERT using ON CONFLICT
        cur.execute("""
            INSERT INTO insurer (insurer_code, insurer_name, is_active)
            VALUES (%s, %s, %s)
            ON CONFLICT (insurer_code)
            DO UPDATE SET
                insurer_name = EXCLUDED.insurer_name,
                is_active = EXCLUDED.is_active
            RETURNING insurer_id
        """, (insurer_code, insurer_name, True))

        result = cur.fetchone()
        return result[0]


def upsert_product(conn: PGConnection, insurer_id: int, product_code: str,
                   product_name: str) -> int:
    """
    Insert or update product, return product_id.

    Args:
        conn: Database connection
        insurer_id: Foreign key to insurer
        product_code: Product code (e.g., SAM-CA-001)
        product_name: Product name

    Returns:
        product_id
    """
    # Infer product type from name (simple heuristic for validation)
    product_type = "암보험"  # Default for validation
    if "암" in product_name:
        product_type = "암보험"
    elif "건강" in product_name:
        product_type = "건강보험"

    with conn.cursor() as cur:
        # UPSERT using ON CONFLICT (insurer_id, product_code)
        cur.execute("""
            INSERT INTO product (insurer_id, product_code, product_name, product_type, is_active)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (insurer_id, product_code)
            DO UPDATE SET
                product_name = EXCLUDED.product_name,
                product_type = EXCLUDED.product_type,
                is_active = EXCLUDED.is_active
            RETURNING product_id
        """, (insurer_id, product_code, product_name, product_type, True))

        result = cur.fetchone()
        return result[0]


def upsert_document(conn: PGConnection, product_id: int, document_type: str,
                    file_path: str, file_hash: str) -> int:
    """
    Insert or update document, return document_id.

    Args:
        conn: Database connection
        product_id: Foreign key to product
        document_type: Document type (약관/사업방법서/상품요약서/가입설계서)
        file_path: Path to PDF file
        file_hash: SHA-256 hash of file

    Returns:
        document_id
    """
    doc_type_priority = get_doc_type_priority(document_type)

    with conn.cursor() as cur:
        # UPSERT using ON CONFLICT (product_id, document_type, file_hash)
        cur.execute("""
            INSERT INTO document (product_id, document_type, file_path, file_hash, doc_type_priority)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (product_id, document_type, file_hash)
            DO UPDATE SET
                file_path = EXCLUDED.file_path,
                doc_type_priority = EXCLUDED.doc_type_priority
            RETURNING document_id
        """, (product_id, document_type, file_path, file_hash, doc_type_priority))

        result = cur.fetchone()
        return result[0]


def register_manifest_rows(conn: PGConnection, rows: List[ManifestRow]) -> dict:
    """
    Register all manifest rows to database.

    Args:
        conn: Database connection
        rows: List of ManifestRow objects

    Returns:
        Statistics dictionary with counts
    """
    stats = {
        "insurers_processed": 0,
        "products_processed": 0,
        "documents_processed": 0,
    }

    for row in rows:
        # 1. UPSERT insurer
        insurer_id = upsert_insurer(conn, row.insurer_code)
        stats["insurers_processed"] += 1

        # 2. UPSERT product
        product_id = upsert_product(conn, insurer_id, row.product_code, row.product_name)
        stats["products_processed"] += 1

        # 3. UPSERT document
        if not row.file_hash:
            raise ValueError(f"file_hash missing for {row.file_path}")

        document_id = upsert_document(conn, product_id, row.document_type,
                                      row.file_path, row.file_hash)
        stats["documents_processed"] += 1

    return stats
