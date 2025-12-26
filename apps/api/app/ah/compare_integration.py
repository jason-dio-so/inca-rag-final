"""
AH-6: Cancer Canonical Decision Integration for Compare Pipeline

Constitutional Principle:
- Query → Excel Alias Recall → Policy Evidence → DECIDED/UNDECIDED
- Compare execution ONLY uses DECIDED canonical codes
- UNDECIDED → empty set for compare (audit/display only)
- No LLM/heuristic/fallback to recalled_candidates for comparison
"""

from typing import List, Set, Optional, Dict, Any
from psycopg2.extensions import connection as PGConnection

from .alias_index import AliasIndex, get_alias_index
from .universe_recall import UniverseRecaller
from .policy_evidence_store import PolicyEvidenceStore
from .cancer_evidence_typer import CancerEvidenceTyper
from .cancer_canonical import CancerCanonicalCode
from .cancer_decision import CancerCanonicalDecision, DecisionStatus, CancerCompareContext


class CancerCompareIntegration:
    """
    Cancer Canonical Decision integration for /compare endpoint.

    Constitutional Flow (AH-1 → AH-4 → AH-5 → AH-6):
    1. Query → AliasIndex → recalled_candidates (over-recall OK)
    2. For each insurer:
       a. PolicyEvidenceStore → fetch evidence spans
       b. CancerEvidenceTyper → type evidence (DEFINITION_INCLUDED vs SEPARATE_BENEFIT)
       c. Decide canonical codes based on evidence
    3. Compare pipeline uses ONLY decided codes (UNDECIDED → empty set)
    """

    def __init__(
        self,
        conn: PGConnection,
        alias_index: Optional[AliasIndex] = None,
        policy_store: Optional[PolicyEvidenceStore] = None,
    ):
        """
        Initialize compare integration.

        Args:
            conn: Database connection
            alias_index: Excel-based alias index (optional, will use global singleton if None)
            policy_store: Policy evidence store (optional, will create if None)
        """
        self.conn = conn
        self.alias_index = alias_index or get_alias_index()
        self.policy_store = policy_store or PolicyEvidenceStore(conn)
        self.evidence_typer = CancerEvidenceTyper()

    def resolve_cancer_canonical(
        self,
        query: str,
        insurer_code: str,
    ) -> CancerCanonicalDecision:
        """
        Resolve cancer canonical codes for a query + insurer.

        Constitutional Flow:
        1. Query → Excel Alias → recalled_candidates
        2. Insurer → Policy Evidence → evidence spans
        3. Evidence → Typer → DEFINITION_INCLUDED | SEPARATE_BENEFIT
        4. Decide canonical codes based on evidence

        Args:
            query: User query (e.g., "일반암진단비", "유사암진단금")
            insurer_code: Insurer code (e.g., "SAMSUNG")

        Returns:
            CancerCanonicalDecision with:
            - recalled_candidates (from Excel)
            - decided_canonical_codes (from evidence)
            - decision_status (DECIDED | UNDECIDED)
            - decision_evidence_spans (if DECIDED)
        """
        # Step 1: Recall from Excel Alias
        recalled = self._recall_from_alias(query)

        # Step 2: Initialize decision
        decision = CancerCanonicalDecision(
            coverage_name_raw=query,
            insurer_code=insurer_code,
            recalled_candidates=recalled,
        )

        # Step 3: Fetch policy evidence
        # Note: PolicyEvidenceStore is async (uses asyncpg)
        # For sync usage (psycopg2), we query v2.coverage_evidence directly
        evidence_spans = self._fetch_cancer_evidence_sync(insurer_code)

        if not evidence_spans:
            # No evidence → UNDECIDED
            decision.decision_status = DecisionStatus.UNDECIDED
            decision.decision_method = "no_policy_evidence"
            return decision

        # Step 4: Type evidence and decide
        decided_codes, typed_spans = self._decide_from_evidence(
            query=query,
            evidence_spans=evidence_spans,
            recalled_candidates=recalled,
        )

        if decided_codes:
            decision.decided_canonical_codes = decided_codes
            decision.decision_status = DecisionStatus.DECIDED
            decision.decision_method = "policy_evidence"
            decision.decision_evidence_spans = [
                {
                    "doc_id": span["doc_id"],
                    "page": span["page"],
                    "span_text": span["span_text"],
                    "evidence_type": span["evidence_type"],
                    "rule_id": span.get("matched_pattern", "unknown"),
                }
                for span in typed_spans
                if span.get("evidence_type") in ["definition_included", "separate_benefit", "exclusion"]
            ]
        else:
            decision.decision_status = DecisionStatus.UNDECIDED
            decision.decision_method = "insufficient_evidence"

        return decision

    def resolve_compare_context(
        self,
        query: str,
        insurer_codes: List[str],
    ) -> CancerCompareContext:
        """
        Resolve cancer canonical decisions for all insurers in a compare request.

        Args:
            query: User query
            insurer_codes: List of insurer codes (e.g., ["SAMSUNG", "MERITZ"])

        Returns:
            CancerCompareContext with decisions for all insurers
        """
        context = CancerCompareContext(query=query)

        for insurer_code in insurer_codes:
            decision = self.resolve_cancer_canonical(
                query=query,
                insurer_code=insurer_code,
            )
            context.decisions.append(decision)

        return context

    def _fetch_cancer_evidence_sync(self, insurer_code: str) -> List[Dict[str, Any]]:
        """
        Fetch cancer policy evidence from DB (sync version for psycopg2).

        Args:
            insurer_code: Insurer code (e.g., "SAMSUNG")

        Returns:
            List of evidence spans with doc_id, page, span_text
        """
        cancer_keywords = [
            "암", "악성신생물", "유사암", "갑상선암", "기타피부암",
            "제자리암", "상피내암", "경계성종양",
            "C00", "C97", "D00", "D09", "D37", "D48", "C73", "C44",
        ]

        # Build keyword filter
        keyword_conditions = " OR ".join(
            [f"excerpt ILIKE %s" for _ in cancer_keywords]
        )
        keyword_params = [f"%{kw}%" for kw in cancer_keywords]

        query = f"""
        SELECT
            source_doc_id,
            source_page,
            excerpt,
            canonical_coverage_code,
            evidence_type
        FROM v2.coverage_evidence
        WHERE insurer_code = %s
          AND source_doc_type = 'policy'
          AND ({keyword_conditions})
        ORDER BY source_page ASC
        LIMIT 50
        """

        with self.conn.cursor() as cur:
            cur.execute(query, [insurer_code] + keyword_params)
            rows = cur.fetchall()

        evidence_spans = []
        for row in rows:
            source_doc_id, source_page, excerpt, canonical_coverage_code, evidence_type = row
            evidence_spans.append({
                "doc_id": source_doc_id,
                "page": source_page,
                "span_text": excerpt,
                "canonical_coverage_code": canonical_coverage_code,
                "evidence_type": evidence_type,
            })

        return evidence_spans

    def _recall_from_alias(self, query: str) -> Set[CancerCanonicalCode]:
        """
        Recall canonical codes from Excel alias index.

        Args:
            query: User query

        Returns:
            Set of recalled canonical codes (may be over-recalled)
        """
        # Use AliasIndex to get recalled canonical codes
        recalled_canonical_strs = self.alias_index.resolve_query(query, apply_cancer_guardrail=True)

        # Convert to CancerCanonicalCode enum
        recalled_codes = set()
        for code_str in recalled_canonical_strs:
            try:
                code = CancerCanonicalCode(code_str)
                recalled_codes.add(code)
            except ValueError:
                # Not a cancer canonical code, skip
                pass

        return recalled_codes

    def _decide_from_evidence(
        self,
        query: str,
        evidence_spans: List[Dict[str, Any]],
        recalled_candidates: Set[CancerCanonicalCode],
    ) -> tuple[Set[CancerCanonicalCode], List[Dict[str, Any]]]:
        """
        Decide canonical codes from policy evidence.

        Constitutional Rule (AH-4):
        - DEFINITION_INCLUDED → code is IN the definition (e.g., "제자리암" in "유사암" definition)
        - SEPARATE_BENEFIT → code is a SEPARATE benefit (e.g., "제자리암" as separate coverage)
        - Evidence typing is deterministic (keyword-based, no LLM)

        Args:
            query: User query
            evidence_spans: List of policy evidence spans
            recalled_candidates: Recalled canonical codes from alias

        Returns:
            Tuple of (decided_codes, typed_spans)
            - decided_codes: Set of decided canonical codes (empty if insufficient evidence)
            - typed_spans: List of evidence spans with evidence_type classification
        """
        # Type all evidence spans
        typed_spans = []
        for span in evidence_spans:
            evidence_result = self.evidence_typer.classify_evidence(
                policy_text=span["span_text"]
            )
            typed_span = span.copy()
            typed_span["evidence_type"] = evidence_result.evidence_type.value
            typed_span["evidence_confidence"] = evidence_result.confidence
            typed_span["matched_pattern"] = evidence_result.matched_pattern
            typed_spans.append(typed_span)

        # Decide based on evidence types
        decided = set()

        # Check for SEPARATE_BENEFIT evidence (highest priority)
        separate_benefit_codes = self._extract_codes_from_separate_benefit(typed_spans)
        if separate_benefit_codes:
            decided.update(separate_benefit_codes)

        # Check for DEFINITION_INCLUDED evidence
        definition_codes = self._extract_codes_from_definition(typed_spans)
        if definition_codes:
            decided.update(definition_codes)

        # If no evidence-based decision, return empty set
        # DO NOT fallback to recalled_candidates
        return decided, typed_spans

    def _extract_codes_from_separate_benefit(
        self,
        typed_spans: List[Dict[str, Any]],
    ) -> Set[CancerCanonicalCode]:
        """
        Extract canonical codes from SEPARATE_BENEFIT evidence.

        Constitutional Rule:
        - "제자리암진단비" → CA_DIAG_IN_SITU
        - "경계성종양진단비" → CA_DIAG_BORDERLINE
        - Evidence must explicitly mention separate benefit
        """
        codes = set()

        for span in typed_spans:
            if span.get("evidence_type") != "separate_benefit":
                continue

            span_text = span["span_text"]

            # Check for IN_SITU separate benefit
            if "제자리암" in span_text and "진단" in span_text:
                codes.add(CancerCanonicalCode.IN_SITU)

            # Check for BORDERLINE separate benefit
            if "경계성종양" in span_text and "진단" in span_text:
                codes.add(CancerCanonicalCode.BORDERLINE)

        return codes

    def _extract_codes_from_definition(
        self,
        typed_spans: List[Dict[str, Any]],
    ) -> Set[CancerCanonicalCode]:
        """
        Extract canonical codes from DEFINITION_INCLUDED evidence.

        Constitutional Rule:
        - "유사암" definition includes "제자리암" → CA_DIAG_SIMILAR
        - "일반암" definition excludes "유사암" → CA_DIAG_GENERAL
        - Evidence must be from policy definitions
        """
        codes = set()

        for span in typed_spans:
            if span.get("evidence_type") != "definition_included":
                continue

            span_text = span["span_text"]

            # Check for SIMILAR definition
            if "유사암" in span_text:
                codes.add(CancerCanonicalCode.SIMILAR)

            # Check for GENERAL definition
            if "일반암" in span_text or ("암" in span_text and "유사암" not in span_text):
                codes.add(CancerCanonicalCode.GENERAL)

        return codes
