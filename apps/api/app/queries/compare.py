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


# SQL template for coverage amount from Proposal Universe Lock
# UNIVERSE LOCK PRINCIPLE: Only coverages in proposal_coverage_universe can be compared
COVERAGE_AMOUNT_SQL = """
SELECT u.amount_value
FROM public.proposal_coverage_universe u
JOIN public.proposal_coverage_mapped m ON m.universe_id = u.id
WHERE m.canonical_coverage_code = %(coverage_code)s
  AND m.mapping_status = 'MAPPED'
  AND u.insurer = %(insurer_code)s
  AND u.proposal_id = %(proposal_id)s
LIMIT 1;
"""


def get_coverage_amount_for_proposal(
    conn: PGConnection,
    insurer_code: str,
    proposal_id: str,
    coverage_code: str
) -> Optional[int]:
    """
    Get coverage amount from proposal universe (Universe Lock).

    Constitutional guarantee:
    - Only returns amounts from proposal_coverage_universe (가입설계서)
    - Requires mapping_status = 'MAPPED'
    - Returns out_of_universe if not in proposal
    - No product-centered lookup allowed

    Args:
        conn: Read-only database connection
        insurer_code: Insurer code (e.g., 'SAMSUNG')
        proposal_id: Proposal document ID
        coverage_code: Canonical coverage code (신정원 통일 코드)

    Returns:
        Coverage amount (KRW) or None if out_of_universe/unmapped
    """
    params = {
        "insurer_code": insurer_code,
        "proposal_id": proposal_id,
        "coverage_code": coverage_code
    }

    rows = execute_readonly_query(conn, COVERAGE_AMOUNT_SQL, params)
    if rows:
        return rows[0].get("amount_value")
    return None


# STEP 14-α: Proposal Universe-based comparison queries

PROPOSAL_COVERAGE_LOOKUP_SQL = """
SELECT
    u.id AS universe_id,
    u.insurer,
    u.proposal_id,
    u.coverage_name_raw,
    u.amount_value,
    m.id AS mapped_id,
    m.canonical_coverage_code,
    m.mapping_status,
    s.disease_scope_raw,
    s.disease_scope_norm,
    s.source_confidence
FROM proposal_coverage_universe u
LEFT JOIN proposal_coverage_mapped m ON m.universe_id = u.id
LEFT JOIN proposal_coverage_slots s ON s.mapped_id = m.id
WHERE u.insurer = %(insurer)s
  AND (
    m.canonical_coverage_code = %(canonical_code)s
    OR u.coverage_name_raw = %(raw_name)s
  )
LIMIT 1;
"""


def get_proposal_coverage(
    conn: PGConnection,
    insurer: str,
    canonical_code: Optional[str] = None,
    raw_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get coverage from proposal universe by canonical code or raw name.

    Args:
        conn: Database connection
        insurer: Insurer name (e.g., 'SAMSUNG', 'MERITZ', 'KB')
        canonical_code: Canonical coverage code (e.g., 'CA_DIAG_GENERAL')
        raw_name: Raw coverage name from proposal (e.g., '매핑안된담보')

    Returns:
        Coverage dict or None if not in universe
    """
    params = {
        "insurer": insurer,
        "canonical_code": canonical_code,
        "raw_name": raw_name
    }

    rows = execute_readonly_query(conn, PROPOSAL_COVERAGE_LOOKUP_SQL, params)
    if rows:
        return rows[0]
    return None


DISEASE_CODE_GROUP_SQL = """
SELECT
    g.group_id,
    g.group_name,
    g.insurer,
    COUNT(m.code_id) AS member_count
FROM disease_code_group g
LEFT JOIN disease_code_group_member m ON m.group_id = g.group_id
WHERE g.insurer = %(insurer)s
  AND g.group_name LIKE %(group_name_pattern)s
GROUP BY g.group_id, g.group_name, g.insurer
LIMIT 1;
"""


def get_disease_code_group(
    conn: PGConnection,
    insurer: str,
    group_name_pattern: str
) -> Optional[Dict[str, Any]]:
    """
    Get disease code group for policy evidence.

    Args:
        conn: Database connection
        insurer: Insurer name
        group_name_pattern: SQL LIKE pattern (e.g., '%유사암%')

    Returns:
        Group dict or None
    """
    params = {
        "insurer": insurer,
        "group_name_pattern": group_name_pattern
    }

    rows = execute_readonly_query(conn, DISEASE_CODE_GROUP_SQL, params)
    if rows:
        return rows[0]
    return None
