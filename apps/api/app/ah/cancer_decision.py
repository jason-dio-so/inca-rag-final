"""
Cancer Canonical Decision: Data structures for compare pipeline integration

Constitutional Principle (AH-5):
- recalled_candidates (over-recall allowed, from Excel Alias)
- decided_canonical_codes (evidence-based only)
- decision_status (DECIDED | UNDECIDED)
- decision_evidence_spans (SSOT: doc_id + page + span_text)

This module provides clean data structures for compare pipeline integration.
"""

from enum import Enum
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass, field

from .cancer_canonical import CancerCanonicalCode


class DecisionStatus(str, Enum):
    """
    Decision status for cancer canonical codes.

    Constitutional Rule (AH-5):
    - DECIDED: Policy evidence available, canonical codes confirmed
    - UNDECIDED: No policy evidence, canonical codes unconfirmed
    """

    DECIDED = "decided"
    UNDECIDED = "undecided"


@dataclass
class CancerCanonicalDecision:
    """
    Cancer canonical decision result for compare pipeline.

    Constitutional Rule (AH-5):
    - recalled_candidates: Over-recall from Excel Alias (AH-1)
    - decided_canonical_codes: Evidence-based confirmation (AH-3 + AH-4)
    - decision_status: DECIDED only if evidence exists
    - decision_evidence_spans: SSOT evidence (doc_id + page + span_text + type)

    Fields:
    - coverage_name_raw: Original coverage name from proposal
    - insurer_code: Insurer code
    - recalled_candidates: Set of recalled canonical codes from alias
    - decided_canonical_codes: Set of decided canonical codes (evidence-based)
    - decision_status: DECIDED | UNDECIDED
    - decision_evidence_spans: List of evidence spans (only for DECIDED)
    - decision_method: Method used for decision (policy_evidence | undecided)
    """

    coverage_name_raw: str
    insurer_code: str
    recalled_candidates: Set[CancerCanonicalCode] = field(default_factory=set)
    decided_canonical_codes: Set[CancerCanonicalCode] = field(default_factory=set)
    decision_status: DecisionStatus = DecisionStatus.UNDECIDED
    decision_evidence_spans: Optional[List[Dict[str, Any]]] = None
    decision_method: str = "undecided"  # policy_evidence | undecided

    def is_decided(self) -> bool:
        """Check if decision is confirmed."""
        return self.decision_status == DecisionStatus.DECIDED

    def is_undecided(self) -> bool:
        """Check if decision is unconfirmed."""
        return self.decision_status == DecisionStatus.UNDECIDED

    def get_canonical_codes_for_compare(self) -> Set[CancerCanonicalCode]:
        """
        Get canonical codes for comparison.

        Constitutional Rule (AH-5):
        - If DECIDED: return decided_canonical_codes
        - If UNDECIDED: return empty set (do NOT use recalled_candidates for comparison)
        """
        if self.is_decided():
            return self.decided_canonical_codes
        else:
            # UNDECIDED: do NOT use recalled_candidates for comparison
            # They are only for display/debug purposes
            return set()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "coverage_name_raw": self.coverage_name_raw,
            "insurer_code": self.insurer_code,
            "recalled_candidates": [c.value for c in self.recalled_candidates],
            "decided_canonical_codes": [c.value for c in self.decided_canonical_codes],
            "decision_status": self.decision_status.value,
            "decision_evidence_spans": self.decision_evidence_spans or [],
            "decision_method": self.decision_method,
        }


@dataclass
class CancerCompareContext:
    """
    Cancer canonical decision context for compare request.

    This aggregates all cancer canonical decisions for a compare request.

    Fields:
    - query: Original user query
    - decisions: List of CancerCanonicalDecision (one per insurer x coverage)
    - decided_count: Count of DECIDED decisions
    - undecided_count: Count of UNDECIDED decisions
    """

    query: str
    decisions: List[CancerCanonicalDecision] = field(default_factory=list)

    def get_decided_count(self) -> int:
        """Get count of decided decisions."""
        return sum(1 for d in self.decisions if d.is_decided())

    def get_undecided_count(self) -> int:
        """Get count of undecided decisions."""
        return sum(1 for d in self.decisions if d.is_undecided())

    def get_decided_rate(self) -> float:
        """Get percentage of decided decisions."""
        total = len(self.decisions)
        if total == 0:
            return 0.0
        return self.get_decided_count() / total

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "query": self.query,
            "decisions": [d.to_dict() for d in self.decisions],
            "stats": {
                "total_decisions": len(self.decisions),
                "decided_count": self.get_decided_count(),
                "undecided_count": self.get_undecided_count(),
                "decided_rate": self.get_decided_rate(),
            },
        }
