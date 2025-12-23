"""
Product search queries

Constitutional rules:
- Read-only queries only
- premium mode requires premium filter (enforced in policy layer)
"""
from typing import List, Dict, Any, Optional
from psycopg2.extensions import connection as PGConnection
from ..db import execute_readonly_query


# SQL template for product search
SEARCH_PRODUCTS_SQL = """
SELECT
  p.product_id,
  i.insurer_code,
  p.product_code,
  p.product_name,
  p.product_type,
  CASE WHEN p.is_active THEN 'ACTIVE' ELSE 'INACTIVE' END AS sale_status
FROM product p
JOIN insurer i ON i.insurer_id = p.insurer_id
WHERE 1=1
  AND (%(insurer_codes)s IS NULL OR i.insurer_code = ANY(%(insurer_codes)s))
  AND (%(product_query)s IS NULL OR p.product_name ILIKE %(product_query_like)s)
  AND (%(sale_status)s IS NULL OR
       (%(sale_status)s = 'ACTIVE' AND p.is_active = true) OR
       (%(sale_status)s = 'INACTIVE' AND p.is_active = false) OR
       (%(sale_status)s = 'ALL'))
ORDER BY p.product_id DESC
LIMIT %(limit)s OFFSET %(offset)s;
"""


def search_products(
    conn: PGConnection,
    insurer_codes: Optional[List[str]] = None,
    product_query: Optional[str] = None,
    sale_status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Search products with filters.

    Args:
        conn: Read-only database connection
        insurer_codes: Filter by insurer codes (e.g., ["SAMSUNG", "MERITZ"])
        product_query: Product name search keyword
        sale_status: "ACTIVE", "INACTIVE", or "ALL"
        limit: Max results
        offset: Pagination offset

    Returns:
        List of product dictionaries
    """
    params = {
        "insurer_codes": insurer_codes,
        "product_query": product_query,
        "product_query_like": f"%{product_query}%" if product_query else None,
        "sale_status": sale_status,
        "limit": limit,
        "offset": offset
    }

    return execute_readonly_query(conn, SEARCH_PRODUCTS_SQL, params)


# SQL template for coverage recommendations (DB-based simple matching)
COVERAGE_RECOMMENDATIONS_SQL = """
SELECT DISTINCT
  ca.coverage_code,
  cs.coverage_name_kr AS canonical_name,
  0.8 AS score
FROM coverage_alias ca
JOIN coverage_standard cs ON cs.coverage_code = ca.coverage_code
WHERE
  ca.alias_name ILIKE %(coverage_name_like)s
ORDER BY score DESC
LIMIT 5;
"""


def get_coverage_recommendations(
    conn: PGConnection,
    coverage_name: str
) -> List[Dict[str, Any]]:
    """
    Get coverage code recommendations based on coverage name.

    Constitutional rule:
    - No automatic INSERT to coverage_standard
    - Return recommendations only
    - If no matches, return empty list

    Args:
        conn: Read-only database connection
        coverage_name: User-provided coverage name

    Returns:
        List of coverage candidates with scores
    """
    params = {
        "coverage_name_like": f"%{coverage_name}%"
    }

    try:
        return execute_readonly_query(conn, COVERAGE_RECOMMENDATIONS_SQL, params)
    except Exception:
        # If coverage_alias table doesn't exist or query fails, return empty
        return []
