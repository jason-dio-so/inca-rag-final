"""
Cancer Scope Detector: Policy Evidence → Coverage Scope

Constitutional Principle:
- Policy (약관) determines coverage scope, NOT proposal documents
- Evidence MUST include: document_id, page, span_text
- No LLM inference allowed (deterministic rule-based only)

This module detects cancer coverage scope from policy text using deterministic rules.
"""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .cancer_canonical import CancerScopeEvidence


@dataclass
class PolicyTextSpan:
    """
    Policy text span for evidence.
    """

    document_id: str
    page: int
    span_text: str
    section: Optional[str] = None


class CancerScopeDetector:
    """
    Deterministic cancer scope detector from policy text.

    Design:
    - Rule-based pattern matching (no LLM)
    - Evidence-backed (document_id, page, span_text required)
    - Conservative (unknown > wrong)
    """

    # Patterns for detecting cancer types in policy text
    GENERAL_CANCER_PATTERNS = [
        r"일반암",
        r"암\s*진단",
        r"악성신생물",
        r"C00\s*[-~]\s*C97",  # KCD-7 general cancer range
    ]

    SIMILAR_CANCER_PATTERNS = [
        r"유사암",
        r"갑상선암",
        r"기타피부암",
        r"C73",  # Thyroid
        r"C44",  # Other skin cancer
    ]

    IN_SITU_PATTERNS = [
        r"제자리암",
        r"상피내암",
        r"D0[0-9]",  # KCD-7 in-situ range
    ]

    BORDERLINE_PATTERNS = [
        r"경계성종양",
        r"D3[0-9]",  # KCD-7 borderline range
        r"D4[0-9]",
    ]

    EXCLUSION_PATTERNS = [
        r"제외",
        r"않는",
        r"해당하지",
        r"대상이\s*아님",
    ]

    @staticmethod
    def detect_scope_from_text(
        policy_text: str, policy_span: PolicyTextSpan
    ) -> CancerScopeEvidence:
        """
        Detect cancer coverage scope from policy text.

        Args:
            policy_text: Policy text to analyze
            policy_span: Evidence metadata (document_id, page, span_text)

        Returns:
            CancerScopeEvidence with scope flags

        Logic (Deterministic):
        1. Search for inclusion patterns (일반암, 유사암, etc.)
        2. Search for exclusion patterns (제외, 않는, etc.)
        3. Combine to determine scope
        4. Conservative: if unclear → False (don't include)
        """
        text_lower = policy_text.lower()

        # Detect inclusions
        includes_general = CancerScopeDetector._detect_pattern(
            text_lower, CancerScopeDetector.GENERAL_CANCER_PATTERNS
        )
        includes_similar = CancerScopeDetector._detect_pattern(
            text_lower, CancerScopeDetector.SIMILAR_CANCER_PATTERNS
        )
        includes_in_situ = CancerScopeDetector._detect_pattern(
            text_lower, CancerScopeDetector.IN_SITU_PATTERNS
        )
        includes_borderline = CancerScopeDetector._detect_pattern(
            text_lower, CancerScopeDetector.BORDERLINE_PATTERNS
        )

        # Detect exclusions
        has_exclusion = CancerScopeDetector._detect_pattern(
            text_lower, CancerScopeDetector.EXCLUSION_PATTERNS
        )

        # Apply exclusion logic
        # If "유사암 제외" appears → includes_similar = False
        if has_exclusion and "유사암" in text_lower:
            includes_similar = False

        # If "제자리암 제외" appears → includes_in_situ = False
        if has_exclusion and "제자리암" in text_lower:
            includes_in_situ = False

        # If "경계성종양 제외" appears → includes_borderline = False
        if has_exclusion and "경계성" in text_lower:
            includes_borderline = False

        # Determine confidence
        confidence = "policy_confirmed" if any([
            includes_general,
            includes_similar,
            includes_in_situ,
            includes_borderline,
        ]) else "unknown"

        return CancerScopeEvidence(
            includes_general=includes_general,
            includes_similar=includes_similar,
            includes_in_situ=includes_in_situ,
            includes_borderline=includes_borderline,
            evidence_source=f"{policy_span.document_id}:p{policy_span.page}",
            confidence=confidence,
        )

    @staticmethod
    def _detect_pattern(text: str, patterns: List[str]) -> bool:
        """
        Detect if any pattern matches in text.
        """
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def detect_scope_from_coverage_name(coverage_name_raw: str) -> CancerScopeEvidence:
        """
        Heuristic-based scope detection from coverage name.

        WARNING: This is NOT constitutional.
        Only use when policy evidence is unavailable.

        Returns:
            CancerScopeEvidence with confidence='inferred'

        Logic Priority (to avoid ambiguity):
        1. If "유사암" appears → Check if specific sub-types mentioned in parentheses
           - "유사암 진단비(제자리암)" → CA_DIAG_IN_SITU (specific wins)
           - "유사암 진단비(경계성종양)" → CA_DIAG_BORDERLINE (specific wins)
           - "유사암 진단비(갑상선암)" → CA_DIAG_SIMILAR (similar category)
           - "유사암 진단비" (no parentheses) → CA_DIAG_SIMILAR (general similar)
        2. If "암진단(유사암제외)" → CA_DIAG_GENERAL
        3. If "제자리암" alone → CA_DIAG_IN_SITU
        4. If "경계성종양" alone → CA_DIAG_BORDERLINE
        """
        name_lower = coverage_name_raw.lower().replace(" ", "")

        includes_general = False
        includes_similar = False
        includes_in_situ = False
        includes_borderline = False

        # Priority 1: Specific sub-types within "유사암" context
        if "유사암" in name_lower:
            # Check if specific sub-type mentioned in parentheses
            if "유사암" in name_lower and "제자리암" in name_lower:
                # "유사암 진단비(제자리암)" → IN_SITU (specific wins)
                includes_in_situ = True
            elif "유사암" in name_lower and ("경계성종양" in name_lower or "경계성" in name_lower):
                # "유사암 진단비(경계성종양)" → BORDERLINE (specific wins)
                includes_borderline = True
            else:
                # "유사암 진단비" or "유사암 진단비(갑상선암)" → SIMILAR
                includes_similar = True
        else:
            # Not in "유사암" context → Independent detection
            if "제자리암" in name_lower:
                includes_in_situ = True
            if "경계성종양" in name_lower or "경계성" in name_lower:
                includes_borderline = True

        # Detect general cancer
        if "암진단" in name_lower or "일반암" in name_lower:
            # If no specific type mentioned, assume general
            if not (includes_similar or includes_in_situ or includes_borderline):
                includes_general = True

        # Handle exclusion clauses
        if "유사암제외" in name_lower or "유사암 제외" in name_lower or "4대유사암제외" in name_lower:
            includes_similar = False
            includes_in_situ = False
            includes_borderline = False
            includes_general = True  # If excluding similar, likely general

        return CancerScopeEvidence(
            includes_general=includes_general,
            includes_similar=includes_similar,
            includes_in_situ=includes_in_situ,
            includes_borderline=includes_borderline,
            evidence_source="coverage_name_heuristic",
            confidence="inferred",
        )


def build_scope_evidence_from_policy(
    policy_documents: List[Dict[str, Any]], coverage_id: str
) -> Optional[CancerScopeEvidence]:
    """
    Build CancerScopeEvidence from policy documents.

    Args:
        policy_documents: List of policy document chunks
        coverage_id: Coverage ID to find evidence for

    Returns:
        CancerScopeEvidence if found, None otherwise

    Logic:
    1. Search for coverage definition in policy documents
    2. Extract relevant text span
    3. Run CancerScopeDetector.detect_scope_from_text()
    4. Return evidence with metadata
    """
    # This is a placeholder for actual policy document search
    # In production, this would query v2.coverage_evidence table

    # For now, return None (use heuristic fallback)
    return None
