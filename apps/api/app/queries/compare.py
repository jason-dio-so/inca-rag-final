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
  LEFT(c.content, 500) AS snippet,
  d.document_type AS doc_type
FROM chunk c
JOIN document d ON d.document_id = c.document_id
WHERE
  c.is_synthetic = false              -- HARD RULE: Compare axis forbids synthetic
  AND d.product_id = %(product_id)s
  AND (%(coverage_code)s IS NULL OR EXISTS (
    SELECT 1 FROM coverage_entity ce
    WHERE ce.chunk_id = c.chunk_id
      AND ce.coverage_code = %(coverage_code)s
  ))
ORDER BY
  CASE d.document_type
    WHEN '약관' THEN 1
    WHEN '사업방법서' THEN 2
    WHEN '상품요약서' THEN 3
    WHEN '가입설계서' THEN 4
    ELSE 99
  END ASC,
  c.page_number ASC
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

    Args:
        conn: Read-only database connection
        product_id: Product ID to get evidence for
        coverage_code: Optional coverage code filter
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
FROM product p
JOIN insurer i ON i.insurer_id = p.insurer_id
WHERE
  (%(product_ids)s IS NULL OR p.product_id = ANY(%(product_ids)s))
  AND (%(insurer_codes)s IS NULL OR i.insurer_code = ANY(%(insurer_codes)s))
  AND p.is_active = true
ORDER BY p.product_id ASC
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
SELECT
  ce.coverage_code,
  ae.amount_value
FROM coverage_entity ce
LEFT JOIN amount_entity ae ON ae.chunk_id = ce.chunk_id
  AND ae.context_type IN ('payment', 'limit')
WHERE
  ce.coverage_code = %(coverage_code)s
  AND EXISTS (
    SELECT 1 FROM chunk c
    JOIN document d ON d.document_id = c.document_id
    WHERE c.chunk_id = ce.chunk_id
      AND d.product_id = %(product_id)s
      AND c.is_synthetic = false  -- HARD RULE
  )
ORDER BY ae.amount_value DESC NULLS LAST
LIMIT 1;
"""


def get_coverage_amount_for_product(
    conn: PGConnection,
    product_id: int,
    coverage_code: str
) -> Optional[int]:
    """
    Get coverage amount for product.

    Constitutional guarantee:
    - Only queries non-synthetic chunks

    Args:
        conn: Read-only database connection
        product_id: Product ID
        coverage_code: Coverage code

    Returns:
        Amount value or None
    """
    params = {
        "product_id": product_id,
        "coverage_code": coverage_code
    }

    rows = execute_readonly_query(conn, COVERAGE_AMOUNT_SQL, params)
    if rows:
        return rows[0].get("amount_value")
    return None
