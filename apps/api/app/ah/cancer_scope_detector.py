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

from .cancer_canonical import CancerScopeEvidence, NameBasedHint


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

        # Detect inclusions (initial broad detection)
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

        # Filter out "별도" context
        # If "X와 별도" appears, don't include X
        if re.search(r"유사암.*별도", text_lower) or re.search(r"별도.*유사암", text_lower):
            includes_similar = False
        if re.search(r"일반암.*별도", text_lower) or re.search(r"별도.*일반암", text_lower):
            includes_general = False

        # Detect exclusions
        has_exclusion = CancerScopeDetector._detect_pattern(
            text_lower, CancerScopeDetector.EXCLUSION_PATTERNS
        )

        # Apply exclusion logic
        # Pattern: "[X]는 제외" or "[X] 제외" or "단, [X]"
        # Must verify that "제외" is near the cancer type keyword
        if has_exclusion:
            # Check for exclusion patterns with context
            # "유사암은 제외", "유사암 제외", "유사암(C73, C44)은 제외"
            if re.search(r"유사암[^\)]*제외", text_lower) or re.search(r"유사암.*은\s*제외", text_lower):
                includes_similar = False

            # "제자리암은 제외", "제자리암 제외", "제자리암(D00-D09)은 제외"
            if re.search(r"제자리암[^\)]*제외", text_lower) or re.search(r"제자리암.*은\s*제외", text_lower):
                includes_in_situ = False

            # "경계성종양은 제외", "경계성종양 제외", "경계성종양(D37-D48)은 제외"
            if re.search(r"경계성종양[^\)]*제외", text_lower) or re.search(r"경계성.*은\s*제외", text_lower):
                includes_borderline = False

        # Determine confidence
        has_any_match = any([
            includes_general,
            includes_similar,
            includes_in_situ,
            includes_borderline,
        ])

        confidence = "evidence_strong" if has_any_match else "unknown"

        # Build evidence spans
        evidence_spans = [{
            "doc_id": policy_span.document_id,
            "doc_type": "policy",
            "page": policy_span.page,
            "span_text": policy_span.span_text,
            "rule_id": "cancer_scope_detector_v1",
        }] if has_any_match else None

        return CancerScopeEvidence(
            includes_general=includes_general,
            includes_similar=includes_similar,
            includes_in_situ=includes_in_situ,
            includes_borderline=includes_borderline,
            evidence_spans=evidence_spans,
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
    def extract_hint_from_coverage_name(coverage_name_raw: str) -> NameBasedHint:
        """
        Extract hint from coverage name (NOT a final decision).

        AH-3 Constitutional Rule:
        - This ONLY extracts hints for debug/audit
        - DO NOT use this for canonical code determination
        - Final decision requires policy evidence

        Returns:
            NameBasedHint with mentions_* flags

        Example:
        - "유사암 진단비(제자리암)" → mentions_similar=True, mentions_in_situ=True
        - "암진단비(유사암제외)" → mentions_general=True, mentions_exclusion=True
        """
        name_lower = coverage_name_raw.lower().replace(" ", "")

        hint = NameBasedHint(raw_name=coverage_name_raw)

        # Detect mentions (NOT final decision)
        hint.mentions_similar = "유사암" in name_lower
        hint.mentions_in_situ = "제자리암" in name_lower
        hint.mentions_borderline = "경계성종양" in name_lower or "경계성" in name_lower
        hint.mentions_general = "암진단" in name_lower or "일반암" in name_lower
        hint.mentions_exclusion = any([
            "유사암제외" in name_lower,
            "유사암 제외" in name_lower,
            "4대유사암제외" in name_lower,
        ])

        return hint


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

    Constitutional Requirement (AH-3):
    - MUST return evidence with doc_id, page, span_text
    - MUST use deterministic pattern matching only
    - NO LLM inference allowed
    """
    if not policy_documents:
        return None

    detector = CancerScopeDetector()
    all_evidence_spans = []

    # Aggregate flags from all matching policy chunks
    includes_general = False
    includes_similar = False
    includes_in_situ = False
    includes_borderline = False

    for doc in policy_documents:
        # Extract required fields
        doc_id = doc.get("document_id") or doc.get("doc_id")
        page = doc.get("page")
        text = doc.get("text") or doc.get("span_text") or doc.get("content", "")

        if not doc_id or page is None or not text:
            continue

        # Build span
        span = PolicyTextSpan(
            document_id=doc_id,
            page=page,
            span_text=text,
            section=doc.get("section"),
        )

        # Detect scope from this span
        evidence = detector.detect_scope_from_text(text, span)

        # Aggregate flags
        if evidence.includes_general:
            includes_general = True
        if evidence.includes_similar:
            includes_similar = True
        if evidence.includes_in_situ:
            includes_in_situ = True
        if evidence.includes_borderline:
            includes_borderline = True

        # Collect evidence spans
        if evidence.evidence_spans:
            all_evidence_spans.extend(evidence.evidence_spans)

    # If no evidence found, return None
    if not all_evidence_spans:
        return None

    # Build aggregated evidence
    return CancerScopeEvidence(
        includes_general=includes_general,
        includes_similar=includes_similar,
        includes_in_situ=includes_in_situ,
        includes_borderline=includes_borderline,
        evidence_spans=all_evidence_spans,
        confidence="evidence_strong" if all_evidence_spans else "unknown",
    )
