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

    Fields:
    - original_coverage_name: Original coverage name from proposal
    - canonical_codes: Set of applicable CancerCanonicalCode values
    - evidence: CancerScopeEvidence used for split
    - split_method: Method used (policy_evidence | heuristic | legacy_mapping)
    """

    original_coverage_name: str
    canonical_codes: Set[CancerCanonicalCode]
    evidence: Optional[CancerScopeEvidence]
    split_method: str  # policy_evidence | heuristic | legacy_mapping

    def is_ambiguous(self) -> bool:
        """
        Check if split is ambiguous (multiple canonical codes).
        """
        return len(self.canonical_codes) > 1

    def is_unmapped(self) -> bool:
        """
        Check if no canonical codes found.
        """
        return len(self.canonical_codes) == 0

    def get_primary_canonical_code(self) -> Optional[CancerCanonicalCode]:
        """
        Get primary canonical code.

        If multiple codes, returns None (ambiguous).
        If single code, returns that code.
        """
        if len(self.canonical_codes) == 1:
            return next(iter(self.canonical_codes))
        else:
            return None


class CanonicalSplitMapper:
    """
    Maps coverage instances to cancer canonical codes.

    Priority:
    1. Policy evidence (preferred)
    2. Heuristic from coverage name (backward compatibility)
    3. Legacy Excel mapping (fallback)
    """

    def __init__(self):
        self.detector = CancerScopeDetector()

    def split_coverage(
        self,
        coverage_name_raw: str,
        policy_documents: Optional[List[Dict[str, Any]]] = None,
        coverage_id: Optional[str] = None,
    ) -> CoverageSplitResult:
        """
        Split coverage into canonical codes.

        Args:
            coverage_name_raw: Raw coverage name from proposal
            policy_documents: Optional policy documents for evidence
            coverage_id: Optional coverage ID for policy lookup

        Returns:
            CoverageSplitResult with canonical codes and evidence

        Logic:
        1. Try policy evidence (if available)
        2. Fall back to heuristic from coverage name
        3. Fall back to legacy Excel mapping (if applicable)
        """
        # Try policy evidence first
        if policy_documents and coverage_id:
            evidence = build_scope_evidence_from_policy(policy_documents, coverage_id)
            if evidence and evidence.confidence == "policy_confirmed":
                codes = split_cancer_coverage_by_scope(
                    coverage_name_raw, evidence=evidence
                )
                return CoverageSplitResult(
                    original_coverage_name=coverage_name_raw,
                    canonical_codes=codes,
                    evidence=evidence,
                    split_method="policy_evidence",
                )

        # Fall back to heuristic
        evidence = self.detector.detect_scope_from_coverage_name(coverage_name_raw)
        codes = split_cancer_coverage_by_scope(coverage_name_raw, evidence=evidence)

        return CoverageSplitResult(
            original_coverage_name=coverage_name_raw,
            canonical_codes=codes,
            evidence=evidence,
            split_method="heuristic",
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
        "ambiguous_count": int,
        "unmapped_count": int,
        "canonical_distribution": {code: count},
    }
    """
    total = len(split_results)
    split_by_method = {}
    ambiguous = 0
    unmapped = 0
    canonical_dist = {}

    for result in split_results:
        # Count by method
        method = result.split_method
        split_by_method[method] = split_by_method.get(method, 0) + 1

        # Count ambiguous
        if result.is_ambiguous():
            ambiguous += 1

        # Count unmapped
        if result.is_unmapped():
            unmapped += 1

        # Count by canonical code
        for code in result.canonical_codes:
            code_str = code.value
            canonical_dist[code_str] = canonical_dist.get(code_str, 0) + 1

    return {
        "total_coverages": total,
        "split_by_method": split_by_method,
        "ambiguous_count": ambiguous,
        "unmapped_count": unmapped,
        "canonical_distribution": canonical_dist,
    }
