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
  c.is_synthetic,
  c.synthetic_source_chunk_id,
  LEFT(c.content, 500) AS snippet,
  d.document_id,
  d.document_type AS doc_type,
  d.product_id,
  i.insurer_code
FROM public.chunk c
JOIN public.document d ON d.document_id = c.document_id
JOIN public.product p ON p.product_id = d.product_id
JOIN public.insurer i ON i.insurer_id = p.insurer_id
WHERE 1=1
  AND (%(insurer_codes)s IS NULL OR i.insurer_code = ANY(%(insurer_codes)s))
  AND (%(include_synthetic)s = true OR c.is_synthetic = false)
ORDER BY c.is_synthetic ASC, d.doc_type_priority ASC, c.page_number ASC
LIMIT %(limit)s;
"""


def get_amount_bridge_evidence(
    conn: PGConnection,
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

    NOTE: Amount extraction from chunk.content is done in presentation layer.

    Args:
        conn: Read-only database connection
        insurer_codes: Optional insurer filter
        include_synthetic: Whether to include synthetic chunks (default: True)
        limit: Max evidence items

    Returns:
        List of evidence dictionaries with snippet
    """
    params = {
        "insurer_codes": insurer_codes,
        "include_synthetic": include_synthetic,
        "limit": limit
    }

    return execute_readonly_query(conn, AMOUNT_BRIDGE_EVIDENCE_SQL, params)
