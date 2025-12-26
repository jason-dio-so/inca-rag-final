"""
Canonical Split Mapper: Coverage Instance → Cancer Canonical Code(s)

Constitutional Flow:
1. Coverage Instance (가입설계서 row)
2. Policy Evidence (약관 보장 정의)
3. CancerScopeEvidence (includes_general, includes_similar, etc.)
4. CancerCanonicalCode(s) (CA_DIAG_GENERAL, CA_DIAG_SIMILAR, etc.)

This mapper splits a single coverage instance into multiple canonical codes
when evidence supports it.
"""

from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass

from .cancer_canonical import (
    CancerCanonicalCode,
    CancerScopeEvidence,
    split_cancer_coverage_by_scope,
    get_canonical_display_name,
)
from .cancer_scope_detector import (
    CancerScopeDetector,
    build_scope_evidence_from_policy,
)


@dataclass
class CoverageSplitResult:
    """
    Result of splitting a coverage instance into canonical codes.

    AH-3 Constitutional Rule:
    - canonical_codes can only be decided if split_method = "policy_evidence"
    - If split_method = "undecided", canonical_codes must be empty
    - hint field is for debug only

    Fields:
    - original_coverage_name: Original coverage name from proposal
    - decided_canonical_codes: Set of decided CancerCanonicalCode values (policy evidence required)
    - recalled_candidates: Set of recalled canonical codes (from AH-1 Excel Alias)
    - evidence: CancerScopeEvidence used for split (None if undecided)
    - split_method: Method used (policy_evidence | undecided)
    """

    original_coverage_name: str
    decided_canonical_codes: Set[CancerCanonicalCode]
    recalled_candidates: Set[CancerCanonicalCode]
    evidence: Optional[CancerScopeEvidence]
    split_method: str  # policy_evidence | undecided

    def is_decided(self) -> bool:
        """
        Check if split is decided (has policy evidence).
        """
        return self.split_method == "policy_evidence" and len(self.decided_canonical_codes) > 0

    def is_undecided(self) -> bool:
        """
        Check if split is undecided (no policy evidence).
        """
        return self.split_method == "undecided"

    def is_ambiguous(self) -> bool:
        """
        Check if split is ambiguous (multiple decided canonical codes).
        """
        return len(self.decided_canonical_codes) > 1

    def get_primary_canonical_code(self) -> Optional[CancerCanonicalCode]:
        """
        Get primary canonical code.

        If multiple codes, returns None (ambiguous).
        If single code, returns that code.
        """
        if len(self.decided_canonical_codes) == 1:
            return next(iter(self.decided_canonical_codes))
        else:
            return None


class CanonicalSplitMapper:
    """
    Maps coverage instances to cancer canonical codes.

    AH-3 + AH-4 Constitutional Rule:
    - ONLY policy evidence can decide canonical codes
    - Name-based patterns produce hints only (for debug)
    - If no policy evidence → split_method = "undecided"
    - Policy evidence retrieval via PolicyEvidenceStore (AH-4)
    """

    def __init__(self, policy_store=None):
        """
        Initialize mapper.

        Args:
            policy_store: Optional PolicyEvidenceStore for DB retrieval (AH-4)
        """
        self.detector = CancerScopeDetector()
        self.policy_store = policy_store

    async def split_coverage(
        self,
        coverage_name_raw: str,
        insurer_code: Optional[str] = None,
        policy_documents: Optional[List[Dict[str, Any]]] = None,
        coverage_id: Optional[str] = None,
        recalled_candidates: Optional[Set[CancerCanonicalCode]] = None,
    ) -> CoverageSplitResult:
        """
        Split coverage into canonical codes (evidence-first).

        Args:
            coverage_name_raw: Raw coverage name from proposal
            insurer_code: Optional insurer code for DB retrieval (AH-4)
            policy_documents: Optional policy documents for evidence (backward compat)
            coverage_id: Optional coverage ID for policy lookup
            recalled_candidates: Optional recalled candidates from AH-1 Excel Alias

        Returns:
            CoverageSplitResult with decided_canonical_codes (if evidence exists)

        AH-3 + AH-4 Logic:
        1. Fetch policy evidence from DB (if policy_store available)
        2. Fall back to policy_documents parameter (backward compat)
        3. Try policy evidence ONLY
        4. If no policy evidence → return undecided (with hint)
        5. DO NOT use name-based heuristic for final decision
        """
        # Extract hint from name (for debug/audit only)
        hint = self.detector.extract_hint_from_coverage_name(coverage_name_raw)

        # AH-4: Fetch policy evidence from DB if available
        if not policy_documents and self.policy_store and insurer_code:
            try:
                policy_documents = await self.policy_store.get_policy_spans_for_cancer(
                    insurer_code=insurer_code,
                    coverage_id=coverage_id,
                    coverage_name_key=coverage_name_raw,
                    limit=20,
                )
            except Exception as e:
                # Log error but don't fail (fall back to undecided)
                print(f"Warning: Policy evidence retrieval failed: {e}")
                policy_documents = None

        # Try policy evidence
        if policy_documents:
            evidence = build_scope_evidence_from_policy(policy_documents, coverage_id)
            if evidence and evidence.confidence in ["evidence_strong", "evidence_weak"]:
                # Attach hint to evidence
                evidence.hint = hint

                codes = split_cancer_coverage_by_scope(
                    coverage_name_raw, evidence=evidence
                )
                return CoverageSplitResult(
                    original_coverage_name=coverage_name_raw,
                    decided_canonical_codes=codes,
                    recalled_candidates=recalled_candidates or set(),
                    evidence=evidence,
                    split_method="policy_evidence",
                )

        # No policy evidence → undecided
        # Build undecided evidence (with hint only)
        undecided_evidence = CancerScopeEvidence(
            includes_general=False,
            includes_similar=False,
            includes_in_situ=False,
            includes_borderline=False,
            evidence_spans=None,
            confidence="unknown",
            hint=hint,
        )

        return CoverageSplitResult(
            original_coverage_name=coverage_name_raw,
            decided_canonical_codes=set(),  # Empty = undecided
            recalled_candidates=recalled_candidates or set(),
            evidence=undecided_evidence,
            split_method="undecided",
        )

    def split_universe_coverages(
        self, universe_coverages: List[Dict[str, Any]]
    ) -> List[CoverageSplitResult]:
        """
        Split all coverages in universe.

        Args:
            universe_coverages: List of coverage records from universe

        Returns:
            List of CoverageSplitResult
        """
        results = []

        for coverage in universe_coverages:
            coverage_name = coverage.get("coverage_name_raw", "")

            # Only split cancer-related coverages
            if not self._is_cancer_coverage(coverage_name):
                continue

            result = self.split_coverage(coverage_name)
            results.append(result)

        return results

    def _is_cancer_coverage(self, coverage_name: str) -> bool:
        """
        Check if coverage is cancer-related.
        """
        cancer_keywords = [
            "암",
            "암진단",
            "유사암",
            "제자리암",
            "경계성종양",
            "악성신생물",
        ]

        name_lower = coverage_name.lower()
        return any(keyword in name_lower for keyword in cancer_keywords)


def generate_split_report(
    split_results: List[CoverageSplitResult],
) -> Dict[str, Any]:
    """
    Generate summary report of split results.

    Returns:
    {
        "total_coverages": int,
        "split_by_method": {method: count},
        "decided_count": int,
        "undecided_count": int,
        "ambiguous_count": int,
        "canonical_distribution": {code: count},
    }
    """
    total = len(split_results)
    split_by_method = {}
    decided = 0
    undecided = 0
    ambiguous = 0
    canonical_dist = {}

    for result in split_results:
        # Count by method
        method = result.split_method
        split_by_method[method] = split_by_method.get(method, 0) + 1

        # Count decided/undecided
        if result.is_decided():
            decided += 1
        if result.is_undecided():
            undecided += 1

        # Count ambiguous
        if result.is_ambiguous():
            ambiguous += 1

        # Count by canonical code (decided only)
        for code in result.decided_canonical_codes:
            code_str = code.value
            canonical_dist[code_str] = canonical_dist.get(code_str, 0) + 1

    return {
        "total_coverages": total,
        "split_by_method": split_by_method,
        "decided_count": decided,
        "undecided_count": undecided,
        "ambiguous_count": ambiguous,
        "canonical_distribution": canonical_dist,
    }
