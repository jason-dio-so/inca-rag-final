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
  ae.coverage_code,
  ae.amount_value,
  ae.amount_text,
  ae.amount_unit,
  ae.context_type,

  c.chunk_id,
  c.is_synthetic,
  c.synthetic_source_chunk_id,
  LEFT(c.content, 500) AS snippet,

  d.document_id,
  d.document_type AS doc_type,
  d.product_id,

  i.insurer_code,
  p.product_name
FROM public.amount_entity ae
JOIN public.chunk c ON c.chunk_id = ae.chunk_id
JOIN public.document d ON d.document_id = c.document_id
JOIN public.product p ON p.product_id = d.product_id
JOIN public.insurer i ON i.insurer_id = p.insurer_id
WHERE ae.coverage_code = %(coverage_code)s
  AND (%(insurer_codes)s IS NULL OR i.insurer_code = ANY(%(insurer_codes)s))
  AND (%(include_synthetic)s = true OR c.is_synthetic = false)
ORDER BY c.is_synthetic ASC, d.doc_type_priority ASC, c.page_number ASC, c.chunk_id ASC
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
    Get amount evidence (AMOUNT_BRIDGE AXIS).

    Constitutional flexibility:
    - include_synthetic=true: Allow synthetic chunks (axis separation)
    - include_synthetic=false: Only non-synthetic chunks
    - This is the ONLY axis where synthetic is allowed

    Amount data from amount_entity table (신정원 통일 코드 기준).

    Args:
        conn: Read-only database connection
        coverage_code: Canonical coverage code (required)
        insurer_codes: Optional insurer filter
        include_synthetic: Whether to include synthetic chunks (default: True)
        limit: Max evidence items

    Returns:
        List of amount evidence dictionaries with DB-sourced amount fields
    """
    params = {
        "coverage_code": coverage_code,
        "insurer_codes": insurer_codes,
        "include_synthetic": include_synthetic,
        "limit": limit
    }

    return execute_readonly_query(conn, AMOUNT_BRIDGE_EVIDENCE_SQL, params)
