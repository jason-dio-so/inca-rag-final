"""
Compare queries (COMPARE AXIS)

Constitutional HARD RULES:
- chunk.is_synthetic = false ALWAYS (hard-coded in SQL)
- No synthetic chunks allowed in compare axis
- Evidence filtering enforced at SQL level
"""
from typing import List, Dict, Any, Optional
from psycopg2.extensions import connection as PGConnection
from ..db import execute_readonly_query


# SQL template for compare evidence
# CONSTITUTIONAL GUARANTEE: c.is_synthetic = false is HARD-CODED
COMPARE_EVIDENCE_SQL = """
SELECT
  c.chunk_id,
  c.document_id,
  c.page_number,
  c.is_synthetic,
  c.synthetic_source_chunk_id,
  LEFT(c.content, 400) AS snippet,
  d.document_type AS doc_type
FROM public.document d
JOIN public.chunk c ON c.document_id = d.document_id
JOIN public.chunk_entity ce ON ce.chunk_id = c.chunk_id
WHERE d.product_id = %(product_id)s
  AND (%(coverage_code)s IS NULL OR ce.coverage_code = %(coverage_code)s)
  AND c.is_synthetic = false              -- HARD RULE: Compare axis forbids synthetic
ORDER BY d.doc_type_priority ASC, c.page_number ASC, c.chunk_id ASC
LIMIT %(limit)s;
"""


def get_compare_evidence(
    conn: PGConnection,
    product_id: int,
    coverage_code: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Get evidence chunks for product comparison (COMPARE AXIS).

    Constitutional guarantee:
    - Returns ONLY non-synthetic chunks (is_synthetic = false)
    - This is enforced in SQL WHERE clause
    - No option to include synthetic chunks
    - Coverage filtering via chunk_entity.coverage_code (신정원 통일 코드)

    Args:
        conn: Read-only database connection
        product_id: Product ID to get evidence for
        coverage_code: Optional canonical coverage code filter
        limit: Max evidence items

    Returns:
        List of evidence dictionaries (all with is_synthetic=false)
    """
    params = {
        "product_id": product_id,
        "coverage_code": coverage_code,
        "limit": limit
    }

    return execute_readonly_query(conn, COMPARE_EVIDENCE_SQL, params)


# SQL template for product comparison results
COMPARE_PRODUCTS_SQL = """
SELECT
  p.product_id,
  i.insurer_code,
  p.product_name,
  p.product_code
FROM public.product p
JOIN public.insurer i ON i.insurer_id = p.insurer_id
WHERE 1=1
  AND (%(product_ids)s IS NULL OR p.product_id = ANY(%(product_ids)s))
  AND (%(insurer_codes)s IS NULL OR i.insurer_code = ANY(%(insurer_codes)s))
ORDER BY p.product_id DESC
LIMIT %(limit)s;
"""


def get_products_for_compare(
    conn: PGConnection,
    product_ids: Optional[List[int]] = None,
    insurer_codes: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get products for comparison.

    Args:
        conn: Read-only database connection
        product_ids: Specific product IDs to compare
        insurer_codes: Filter by insurer codes
        limit: Max products

    Returns:
        List of product dictionaries
    """
    params = {
        "product_ids": product_ids,
        "insurer_codes": insurer_codes,
        "limit": limit
    }

    return execute_readonly_query(conn, COMPARE_PRODUCTS_SQL, params)


# SQL template for coverage amount
COVERAGE_AMOUNT_SQL = """
SELECT pc.coverage_amount
FROM public.product_coverage pc
JOIN public.coverage_standard cs ON cs.coverage_id = pc.coverage_id
WHERE pc.product_id = %(product_id)s
  AND cs.coverage_code = %(coverage_code)s
LIMIT 1;
"""


def get_coverage_amount_for_product(
    conn: PGConnection,
    product_id: int,
    coverage_code: str
) -> Optional[float]:
    """
    Get coverage amount for product from product_coverage table.

    Args:
        conn: Read-only database connection
        product_id: Product ID
        coverage_code: Canonical coverage code (신정원 통일 코드)

    Returns:
        Coverage amount or None
    """
    params = {
        "product_id": product_id,
        "coverage_code": coverage_code
    }

    rows = execute_readonly_query(conn, COVERAGE_AMOUNT_SQL, params)
    if rows:
        return rows[0].get("coverage_amount")
    return None
