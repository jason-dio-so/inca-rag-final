"""
STEP 6-B: Coverage Name → Canonical Code Resolver

Purpose: Map LLM-proposed coverage names to canonical coverage_code (신정원 통일코드).

Constitutional Principles:
- ONLY canonical coverage_code from coverage_standard
- NO auto-INSERT into coverage_standard (forbidden)
- Deterministic mapping (rule-based, reproducible)
- FK constraint enforced (coverage_code MUST exist)
"""
from typing import Optional
from psycopg2.extensions import connection as PGConnection
import logging
from .models import ResolverResult

logger = logging.getLogger(__name__)


class CoverageResolver:
    """
    Resolve LLM-proposed coverage names to canonical coverage_code.

    Resolution Strategy (in order):
    1. Exact alias match (insurer-specific)
    2. Exact coverage_standard match
    3. Fuzzy match (Levenshtein distance ≥ 85%)
    4. Fail → needs_review

    Constitutional Guarantee:
    - All resolved codes verified to exist in coverage_standard (FK)
    - NO new coverage codes created
    """

    def __init__(self, conn: PGConnection):
        """
        Initialize resolver with database connection.

        Args:
            conn: PostgreSQL connection (read-only)
        """
        self.conn = conn

    def resolve(
        self,
        coverage_name_raw: str,
        insurer_code: Optional[str] = None,
        doc_type: Optional[str] = None,
        entity_type_proposed: Optional[str] = None
    ) -> ResolverResult:
        """
        Resolve coverage name to canonical coverage_code.

        Args:
            coverage_name_raw: Coverage name from LLM
            insurer_code: Insurer code (for alias lookup)
            doc_type: Document type (for priority)
            entity_type_proposed: Proposed entity type

        Returns:
            ResolverResult with status and resolved_coverage_code
        """
        # Normalize input
        coverage_name_normalized = coverage_name_raw.strip()

        # Step 1: Exact alias match (insurer-specific)
        if insurer_code:
            result = self._resolve_via_alias(coverage_name_normalized, insurer_code)
            if result.status == "resolved":
                return result

        # Step 2: Exact coverage_standard match
        result = self._resolve_via_standard(coverage_name_normalized)
        if result.status == "resolved":
            return result

        # Step 3: Fuzzy match (if available)
        result = self._resolve_via_fuzzy(coverage_name_normalized, threshold=0.85)
        if result.status == "resolved":
            return result

        # Step 4: No match → needs manual review
        return ResolverResult(
            status="needs_review",
            reason=f"no_match_for_{coverage_name_normalized}",
            resolver_method="none"
        )

    def _resolve_via_alias(
        self,
        coverage_name: str,
        insurer_code: str
    ) -> ResolverResult:
        """
        Resolve via coverage_alias table (insurer-specific).
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT coverage_code
                    FROM coverage_alias
                    WHERE alias_name = %s
                      AND insurer_code = %s
                    LIMIT 1
                """, (coverage_name, insurer_code))

                row = cur.fetchone()
                if row:
                    coverage_code = row[0]
                    # Verify FK exists (double safety)
                    if self._verify_coverage_exists(coverage_code):
                        return ResolverResult(
                            status="resolved",
                            resolved_coverage_code=coverage_code,
                            resolver_method="exact_alias",
                            resolver_confidence=1.0
                        )

        except Exception as e:
            logger.error(f"Alias resolution error: {e}")

        return ResolverResult(status="rejected", reason="alias_lookup_failed")

    def _resolve_via_standard(
        self,
        coverage_name: str
    ) -> ResolverResult:
        """
        Resolve via coverage_standard table (exact match).
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT coverage_code
                    FROM coverage_standard
                    WHERE coverage_name = %s
                    LIMIT 1
                """, (coverage_name,))

                row = cur.fetchone()
                if row:
                    return ResolverResult(
                        status="resolved",
                        resolved_coverage_code=row[0],
                        resolver_method="exact_standard",
                        resolver_confidence=1.0
                    )

        except Exception as e:
            logger.error(f"Standard resolution error: {e}")

        return ResolverResult(status="rejected", reason="standard_lookup_failed")

    def _resolve_via_fuzzy(
        self,
        coverage_name: str,
        threshold: float = 0.85
    ) -> ResolverResult:
        """
        Resolve via fuzzy matching (Levenshtein distance).

        Note: Requires PostgreSQL extension pg_trgm or fuzzystrmatch.
        If not available, returns needs_review.
        """
        try:
            with self.conn.cursor() as cur:
                # Try using similarity function (requires pg_trgm extension)
                cur.execute("""
                    SELECT coverage_code, coverage_name,
                           similarity(coverage_name, %s) AS sim
                    FROM coverage_standard
                    WHERE similarity(coverage_name, %s) >= %s
                    ORDER BY sim DESC
                    LIMIT 5
                """, (coverage_name, coverage_name, threshold))

                rows = cur.fetchall()
                if not rows:
                    return ResolverResult(
                        status="needs_review",
                        reason="no_fuzzy_match"
                    )

                # If exactly one match, resolve
                if len(rows) == 1:
                    return ResolverResult(
                        status="resolved",
                        resolved_coverage_code=rows[0][0],
                        resolver_method="fuzzy",
                        resolver_confidence=rows[0][2]  # similarity score
                    )

                # Multiple matches → ambiguous → needs review
                matches = [{"code": r[0], "name": r[1], "similarity": r[2]} for r in rows]
                return ResolverResult(
                    status="needs_review",
                    reason=f"ambiguous_fuzzy_matches_{len(matches)}"
                )

        except Exception as e:
            # pg_trgm not available or other error
            logger.warning(f"Fuzzy matching not available: {e}")
            return ResolverResult(
                status="needs_review",
                reason="fuzzy_matching_unavailable"
            )

    def _verify_coverage_exists(self, coverage_code: str) -> bool:
        """
        Verify that coverage_code exists in coverage_standard.

        Constitutional Guarantee: FK enforcement.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT 1
                    FROM coverage_standard
                    WHERE coverage_code = %s
                """, (coverage_code,))

                return cur.fetchone() is not None

        except Exception as e:
            logger.error(f"FK verification error: {e}")
            return False

    def resolve_batch(
        self,
        candidates: list[dict],
        insurer_code: Optional[str] = None
    ) -> list[ResolverResult]:
        """
        Resolve multiple candidates in batch (for efficiency).

        Args:
            candidates: List of dicts with coverage_name_raw
            insurer_code: Insurer code (for alias lookup)

        Returns:
            List of ResolverResults
        """
        results = []
        for candidate in candidates:
            result = self.resolve(
                coverage_name_raw=candidate.get("coverage_name_raw", ""),
                insurer_code=insurer_code,
                doc_type=candidate.get("doc_type"),
                entity_type_proposed=candidate.get("entity_type_proposed")
            )
            results.append(result)

        return results
