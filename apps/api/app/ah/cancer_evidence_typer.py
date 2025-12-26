"""
Cancer Evidence Typer: Policy Span → Evidence Type Classification

Constitutional Principle (AH-4):
- Evidence typing is deterministic (rule-based, no LLM)
- Evidence types distinguish between:
  - DEFINITION_INCLUDED: "유사암은 ... 제자리암/경계성종양을 포함"
  - EXCLUSION: "... 은 제외한다"
  - SEPARATE_BENEFIT: "별도 지급", "별도 담보"
  - UNKNOWN: No clear pattern

Evidence Type Impact on Canonical Split:
- DEFINITION_INCLUDED: Sets parent scope only (e.g., SIMILAR), NOT sub-scopes
- SEPARATE_BENEFIT: Enables sub-scope canonical (e.g., IN_SITU)
- EXCLUSION: Disables scope flags
"""

import re
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass


class CancerEvidenceType(str, Enum):
    """
    Evidence type classification for cancer policy spans.

    Constitutional Rule (AH-4):
    - DEFINITION_INCLUDED: Describes what's included in a category
    - EXCLUSION: Explicitly excludes certain types
    - SEPARATE_BENEFIT: Indicates separate/independent coverage
    - UNKNOWN: No clear classification
    """

    DEFINITION_INCLUDED = "definition_included"
    EXCLUSION = "exclusion"
    SEPARATE_BENEFIT = "separate_benefit"
    UNKNOWN = "unknown"


@dataclass
class EvidenceTypeResult:
    """
    Result of evidence typing.

    Fields:
    - evidence_type: CancerEvidenceType
    - confidence: float (0.0 ~ 1.0)
    - matched_pattern: str (for audit)
    """

    evidence_type: CancerEvidenceType
    confidence: float
    matched_pattern: Optional[str] = None


class CancerEvidenceTyper:
    """
    Deterministic evidence typer for cancer policy spans.

    Design:
    - Rule-based pattern matching only
    - No LLM inference
    - Conservative: UNKNOWN > wrong classification
    """

    # Definition patterns (what's included in a category)
    DEFINITION_PATTERNS = [
        (r"포함", "포함"),
        (r"정의", "정의"),
        (r"해당", "해당"),
        (r"분류", "분류"),
        (r"다음과\s*같다", "다음과 같다"),
        (r"아래와\s*같다", "아래와 같다"),
    ]

    # Exclusion patterns
    EXCLUSION_PATTERNS = [
        (r"제외", "제외"),
        (r"않는", "않는"),
        (r"해당하지", "해당하지"),
        (r"대상이\s*아님", "대상이 아님"),
        (r"지급하지\s*않", "지급하지 않"),
        (r"면책", "면책"),
    ]

    # Separate benefit patterns
    SEPARATE_BENEFIT_PATTERNS = [
        (r"별도\s*담보", "별도 담보"),
        (r"별도\s*지급", "별도 지급"),
        (r"별도로\s*지급", "별도로 지급"),
        (r"독립\s*담보", "독립 담보"),
        (r"독립적\s*으로", "독립적으로"),
        (r"구분\s*하여\s*지급", "구분하여 지급"),
    ]

    @staticmethod
    def classify_evidence(policy_text: str) -> EvidenceTypeResult:
        """
        Classify evidence type from policy text.

        Args:
            policy_text: Policy span text

        Returns:
            EvidenceTypeResult with classification

        Logic (Priority):
        1. Check for SEPARATE_BENEFIT patterns (highest priority)
        2. Check for EXCLUSION patterns
        3. Check for DEFINITION_INCLUDED patterns
        4. Default to UNKNOWN
        """
        text_lower = policy_text.lower().replace(" ", "")

        # Priority 1: Separate benefit (most specific)
        for pattern, label in CancerEvidenceTyper.SEPARATE_BENEFIT_PATTERNS:
            if re.search(pattern, text_lower):
                return EvidenceTypeResult(
                    evidence_type=CancerEvidenceType.SEPARATE_BENEFIT,
                    confidence=0.9,
                    matched_pattern=label,
                )

        # Priority 2: Exclusion
        for pattern, label in CancerEvidenceTyper.EXCLUSION_PATTERNS:
            if re.search(pattern, text_lower):
                return EvidenceTypeResult(
                    evidence_type=CancerEvidenceType.EXCLUSION,
                    confidence=0.9,
                    matched_pattern=label,
                )

        # Priority 3: Definition/Inclusion
        for pattern, label in CancerEvidenceTyper.DEFINITION_PATTERNS:
            if re.search(pattern, text_lower):
                return EvidenceTypeResult(
                    evidence_type=CancerEvidenceType.DEFINITION_INCLUDED,
                    confidence=0.8,
                    matched_pattern=label,
                )

        # Default: Unknown
        return EvidenceTypeResult(
            evidence_type=CancerEvidenceType.UNKNOWN,
            confidence=0.0,
            matched_pattern=None,
        )

    @staticmethod
    def enrich_evidence_span(
        span: Dict[str, Any], policy_text: str
    ) -> Dict[str, Any]:
        """
        Enrich evidence span with evidence type.

        Args:
            span: Evidence span dict (doc_id, page, span_text, etc.)
            policy_text: Policy text to classify

        Returns:
            Enriched span with evidence_type and type_confidence
        """
        type_result = CancerEvidenceTyper.classify_evidence(policy_text)

        enriched = span.copy()
        enriched["evidence_type"] = type_result.evidence_type.value
        enriched["type_confidence"] = type_result.confidence
        enriched["type_matched_pattern"] = type_result.matched_pattern

        return enriched


def classify_policy_spans(
    policy_spans: list[Dict[str, Any]],
) -> list[Dict[str, Any]]:
    """
    Classify all policy spans with evidence types.

    Args:
        policy_spans: List of policy span dicts

    Returns:
        List of enriched spans with evidence_type
    """
    typer = CancerEvidenceTyper()
    enriched_spans = []

    for span in policy_spans:
        text = span.get("span_text") or span.get("text") or ""
        enriched = typer.enrich_evidence_span(span, text)
        enriched_spans.append(enriched)

    return enriched_spans
