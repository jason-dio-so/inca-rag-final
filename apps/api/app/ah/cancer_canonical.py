"""
Cancer Canonical Code Set (Constitutional)

This module defines the constitutional cancer canonical code set.
These codes are FIXED and cannot be changed without constitutional amendment.

Principle:
- "암진단비" is NOT a single coverage.
- Cancer coverages MUST be split by scope (general / similar / in-situ / borderline).
- Policy (약관) determines the canonical code, NOT proposal documents.
"""

from enum import Enum
from typing import Set, Dict, Optional, List, Any
from dataclasses import dataclass, field


class CancerCanonicalCode(str, Enum):
    """
    Constitutional Cancer Canonical Code Set (FIXED)

    These 4 codes are the ONLY valid canonical codes for cancer diagnosis coverages.
    """

    # 일반암 (유사암/제자리암/경계성종양 제외)
    GENERAL = "CA_DIAG_GENERAL"

    # 유사암 (갑상선암, 기타피부암 등)
    SIMILAR = "CA_DIAG_SIMILAR"

    # 제자리암
    IN_SITU = "CA_DIAG_IN_SITU"

    # 경계성종양
    BORDERLINE = "CA_DIAG_BORDERLINE"


@dataclass
class NameBasedHint:
    """
    Hint extracted from coverage name (NOT a final decision).

    This is for debug/audit purposes only.
    DO NOT use this for canonical code determination.
    """
    mentions_in_situ: bool = False
    mentions_borderline: bool = False
    mentions_similar: bool = False
    mentions_general: bool = False
    mentions_exclusion: bool = False
    raw_name: Optional[str] = None


@dataclass
class CancerScopeEvidence:
    """
    Evidence-based cancer coverage scope determination.

    Constitutional Rule (AH-3):
    - includes_* fields can ONLY be True if policy evidence exists
    - confidence MUST be "evidence_strong" or "evidence_weak" when includes_* is True
    - confidence="unknown" → all includes_* must be False

    Fields:
    - includes_general: 일반암 포함 여부 (policy evidence required)
    - includes_similar: 유사암 포함 여부 (policy evidence required)
    - includes_in_situ: 제자리암 포함 여부 (policy evidence required)
    - includes_borderline: 경계성종양 포함 여부 (policy evidence required)
    - evidence_spans: List of policy spans (doc_id, page, span_text)
    - confidence: evidence_strong | evidence_weak | unknown
    - hint: Optional name-based hint (for debug only)
    """

    includes_general: bool
    includes_similar: bool
    includes_in_situ: bool
    includes_borderline: bool

    evidence_spans: Optional[List[Dict[str, Any]]] = field(default=None)  # [{doc_id, page, span_text, rule_id}]
    confidence: str = "unknown"  # evidence_strong | evidence_weak | unknown
    hint: Optional[NameBasedHint] = None

    def __post_init__(self):
        """
        Validate constitutional constraint (AH-3).

        If confidence="unknown" → all includes_* must be False.
        """
        if self.confidence == "unknown":
            if any([self.includes_general, self.includes_similar,
                   self.includes_in_situ, self.includes_borderline]):
                raise ValueError(
                    "AH-3 Constitutional violation: "
                    "confidence='unknown' cannot have includes_*=True. "
                    "Evidence required for scope determination."
                )

    def get_canonical_code(self) -> Optional[CancerCanonicalCode]:
        """
        Determine canonical code based on scope.

        Logic:
        - If ONLY includes_general → CA_DIAG_GENERAL
        - If ONLY includes_similar → CA_DIAG_SIMILAR
        - If ONLY includes_in_situ → CA_DIAG_IN_SITU
        - If ONLY includes_borderline → CA_DIAG_BORDERLINE
        - If multiple → AMBIGUOUS (needs manual resolution)
        - If none → UNKNOWN

        Returns:
            CancerCanonicalCode if unambiguous, None if ambiguous/unknown
        """
        includes = [
            (self.includes_general, CancerCanonicalCode.GENERAL),
            (self.includes_similar, CancerCanonicalCode.SIMILAR),
            (self.includes_in_situ, CancerCanonicalCode.IN_SITU),
            (self.includes_borderline, CancerCanonicalCode.BORDERLINE),
        ]

        matched = [code for included, code in includes if included]

        if len(matched) == 1:
            return matched[0]
        else:
            # Ambiguous (multiple) or unknown (none)
            return None


# Constitutional mapping: Legacy code → New canonical code
# This is for backward compatibility with existing Excel mapping
LEGACY_TO_CANONICAL_MAP: Dict[str, CancerCanonicalCode] = {
    # A4200_1: 암진단비(유사암제외) → CA_DIAG_GENERAL
    "A4200_1": CancerCanonicalCode.GENERAL,

    # A4210: 유사암진단비 → CA_DIAG_SIMILAR
    "A4210": CancerCanonicalCode.SIMILAR,

    # A4209: 고액암진단비 → CA_DIAG_GENERAL (usually excludes similar)
    "A4209": CancerCanonicalCode.GENERAL,

    # A4299_1: 재진단암진단비 → CA_DIAG_GENERAL (needs evidence verification)
    "A4299_1": CancerCanonicalCode.GENERAL,
}


# Canonical code display names (Korean)
CANONICAL_DISPLAY_NAMES: Dict[CancerCanonicalCode, str] = {
    CancerCanonicalCode.GENERAL: "일반암진단비 (유사암/제자리암/경계성종양 제외)",
    CancerCanonicalCode.SIMILAR: "유사암진단비 (갑상선암, 기타피부암 등)",
    CancerCanonicalCode.IN_SITU: "제자리암진단비",
    CancerCanonicalCode.BORDERLINE: "경계성종양진단비",
}


def get_canonical_display_name(code: CancerCanonicalCode) -> str:
    """
    Get Korean display name for canonical code.
    """
    return CANONICAL_DISPLAY_NAMES.get(code, str(code))


def is_cancer_canonical_code(code: str) -> bool:
    """
    Check if code is a valid cancer canonical code.
    """
    try:
        CancerCanonicalCode(code)
        return True
    except ValueError:
        return False


def split_cancer_coverage_by_scope(
    coverage_name_raw: str, evidence: Optional[CancerScopeEvidence] = None
) -> Set[CancerCanonicalCode]:
    """
    Split cancer coverage by scope.

    This function determines which cancer canonical codes apply to a raw coverage name.

    Args:
        coverage_name_raw: Raw coverage name from proposal
        evidence: Optional evidence-based scope determination

    Returns:
        Set of applicable CancerCanonicalCode values

    Logic:
    1. If evidence provided → use evidence.get_canonical_code()
    2. If no evidence → heuristic-based split (for backward compatibility)

    Constitutional Rule:
    - Evidence-based determination MUST be preferred
    - Heuristic is ONLY for backward compatibility / unmapped cases
    """
    if evidence is not None:
        canonical = evidence.get_canonical_code()
        if canonical is not None:
            return {canonical}
        else:
            # Ambiguous or unknown → return empty set
            return set()

    # Heuristic-based split (backward compatibility)
    # This is NOT constitutional, only for unmapped cases
    codes: Set[CancerCanonicalCode] = set()

    name_lower = coverage_name_raw.lower().replace(" ", "")

    # Detect "유사암" explicitly
    if "유사암" in name_lower:
        codes.add(CancerCanonicalCode.SIMILAR)

    # Detect "제자리암"
    if "제자리암" in name_lower:
        codes.add(CancerCanonicalCode.IN_SITU)

    # Detect "경계성종양"
    if "경계성종양" in name_lower or "경계성" in name_lower:
        codes.add(CancerCanonicalCode.BORDERLINE)

    # Detect general cancer (암진단 but not 유사암/제자리암/경계성종양)
    if "암진단" in name_lower or "일반암" in name_lower:
        if not codes:  # Only if no specific type detected
            codes.add(CancerCanonicalCode.GENERAL)

    # If exclusion clause present, remove SIMILAR
    if "유사암제외" in name_lower or "유사암 제외" in name_lower:
        codes.discard(CancerCanonicalCode.SIMILAR)
        if not codes:  # If empty after removal, add GENERAL
            codes.add(CancerCanonicalCode.GENERAL)

    return codes
