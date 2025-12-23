"""
Amount Bridge evidence queries (AMOUNT_BRIDGE AXIS)

Constitutional rules:
- Synthetic chunks ALLOWED via include_synthetic option
- Axis separation: completely different from compare
- is_synthetic filter controlled by option parameter
"""
from typing import List, Dict, Any, Optional
from psycopg2.extensions import connection as PGConnection
from ..db import execute_readonly_query


# SQL template for amount bridge evidence
# CONSTITUTIONAL FLEXIBILITY: include_synthetic option controls filtering
AMOUNT_BRIDGE_EVIDENCE_SQL = """
SELECT
  c.chunk_id,
  c.document_id,
  c.page_number,
  c.is_synthetic,
  c.synthetic_source_chunk_id,
  ae.amount_value,
  ae.amount_text,
  COALESCE(ae.currency, 'KRW') AS currency,
  ae.context_type,
  LEFT(c.content, 500) AS snippet,
  i.insurer_code,
  p.product_id,
  p.product_name
FROM amount_entity ae
JOIN chunk c ON c.chunk_id = ae.chunk_id
JOIN document d ON d.document_id = c.document_id
JOIN product p ON p.product_id = d.product_id
JOIN insurer i ON i.insurer_id = p.insurer_id
WHERE
  ae.coverage_code = %(coverage_code)s
  AND (%(insurer_codes)s IS NULL OR i.insurer_code = ANY(%(insurer_codes)s))
  AND (
    %(include_synthetic)s = true
    OR c.is_synthetic = false
  )
ORDER BY
  ae.amount_value DESC NULLS LAST,
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


def get_amount_bridge_evidence(
    conn: PGConnection,
    coverage_code: str,
    insurer_codes: Optional[List[str]] = None,
    include_synthetic: bool = True,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get amount evidence for coverage code (AMOUNT_BRIDGE AXIS).

    Constitutional flexibility:
    - include_synthetic=true: Allow synthetic chunks (axis separation)
    - include_synthetic=false: Only non-synthetic chunks
    - This is the ONLY axis where synthetic is allowed

    Args:
        conn: Read-only database connection
        coverage_code: Coverage code (required)
        insurer_codes: Optional insurer filter
        include_synthetic: Whether to include synthetic chunks (default: True)
        limit: Max evidence items

    Returns:
        List of amount evidence dictionaries
    """
    params = {
        "coverage_code": coverage_code,
        "insurer_codes": insurer_codes,
        "include_synthetic": include_synthetic,
        "limit": limit
    }

    return execute_readonly_query(conn, AMOUNT_BRIDGE_EVIDENCE_SQL, params)
