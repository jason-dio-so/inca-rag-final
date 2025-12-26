"""
Policy Evidence Store: DB Retrieval for Cancer Policy Spans

Constitutional Principle (AH-4):
- Evidence retrieval is deterministic (keyword-based, no vector/embedding)
- Source: v2.coverage_evidence table (doc_type='policy')
- Filters: insurer_code, cancer keywords, coverage_id/name
- Returns: doc_id, page, span_text (SSOT for evidence)

Design:
- Keyword-based recall (over-recall allowed)
- Deterministic sorting (keyword hits DESC, page ASC)
- No LLM/embedding for decision-making
"""

from typing import Optional, List, Dict, Any
import asyncpg


class PolicyEvidenceStore:
    """
    Retrieval module for cancer policy evidence from DB.

    Constitutional Rule (AH-4):
    - Deterministic keyword-based retrieval only
    - Returns policy spans with doc_id, page, span_text
    - No vector/embedding for canonical decision
    """

    # Cancer-related keywords for deterministic filtering
    CANCER_KEYWORDS = [
        "암",
        "악성신생물",
        "유사암",
        "갑상선암",
        "기타피부암",
        "제자리암",
        "상피내암",
        "경계성종양",
        "C00",
        "C97",
        "D00",
        "D09",
        "D37",
        "D48",
        "C73",
        "C44",
    ]

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize with database pool.

        Args:
            db_pool: asyncpg connection pool
        """
        self.db_pool = db_pool

    async def get_policy_spans_for_cancer(
        self,
        insurer_code: str,
        coverage_id: Optional[str] = None,
        coverage_name_key: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve policy evidence spans for cancer coverage.

        Args:
            insurer_code: Insurer code (SAMSUNG, MERITZ, etc.)
            coverage_id: Optional coverage ID for targeted retrieval
            coverage_name_key: Optional coverage name keyword
            limit: Max number of spans to return

        Returns:
            List of policy spans with:
            - document_id (doc_id)
            - page
            - span_text (text)
            - keyword_hits (for sorting)

        Logic (Deterministic):
        1. Filter: doc_type='policy' AND insurer_code=...
        2. Filter: span_text contains any cancer keyword
        3. Optional: coverage_id or coverage_name_key match
        4. Sort: keyword_hits DESC, page ASC
        5. Limit results
        """
        # Build keyword filter (OR condition)
        keyword_conditions = " OR ".join(
            [f"span_text ILIKE '%{kw}%'" for kw in self.CANCER_KEYWORDS]
        )

        # Base query
        query = f"""
        WITH keyword_scored AS (
            SELECT
                document_id,
                page,
                span_text,
                section,
                -- Count keyword hits for scoring
                (
                    {' + '.join([f"CASE WHEN span_text ILIKE '%{kw}%' THEN 1 ELSE 0 END" for kw in self.CANCER_KEYWORDS])}
                ) AS keyword_hits
            FROM v2.coverage_evidence
            WHERE
                doc_type = 'policy'
                AND insurer_code = $1
                AND ({keyword_conditions})
        """

        params = [insurer_code]
        param_idx = 2

        # Optional coverage_id filter
        if coverage_id:
            query += f" AND coverage_id = ${param_idx}"
            params.append(coverage_id)
            param_idx += 1

        # Optional coverage_name_key filter
        if coverage_name_key:
            query += f" AND span_text ILIKE ${param_idx}"
            params.append(f"%{coverage_name_key}%")
            param_idx += 1

        query += """
        )
        SELECT
            document_id AS doc_id,
            page,
            span_text AS text,
            section,
            keyword_hits
        FROM keyword_scored
        WHERE keyword_hits > 0
        ORDER BY keyword_hits DESC, page ASC
        LIMIT $""" + str(param_idx)

        params.append(limit)

        # Execute query
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        # Convert to dict list
        results = []
        for row in rows:
            results.append({
                "doc_id": row["doc_id"],
                "page": row["page"],
                "text": row["text"],
                "section": row.get("section"),
                "keyword_hits": row["keyword_hits"],
            })

        return results

    async def get_all_policy_spans_for_insurer(
        self,
        insurer_code: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all cancer-related policy spans for an insurer.

        Args:
            insurer_code: Insurer code
            limit: Max number of spans

        Returns:
            List of policy spans
        """
        return await self.get_policy_spans_for_cancer(
            insurer_code=insurer_code,
            coverage_id=None,
            coverage_name_key=None,
            limit=limit,
        )


async def create_policy_evidence_store(db_pool: asyncpg.Pool) -> PolicyEvidenceStore:
    """
    Factory function to create PolicyEvidenceStore.

    Args:
        db_pool: asyncpg connection pool

    Returns:
        PolicyEvidenceStore instance
    """
    return PolicyEvidenceStore(db_pool)
