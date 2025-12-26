"""
Deterministic compilation rules.

Constitutional Principles:
- No LLM, no inference
- Rule-based only
- Deterministic (same input → same output)
- No recommendation/judgment
"""

from typing import Dict, List, Set, Optional
from enum import Enum


class SurgeryMethod(str, Enum):
    """Surgery method options (deterministic)."""
    DA_VINCI = "da_vinci"
    ROBOT = "robot"
    LAPAROSCOPIC = "laparoscopic"
    ANY = "any"
    UNKNOWN = "unknown"


class CancerSubtype(str, Enum):
    """Cancer subtype options (deterministic)."""
    IN_SITU = "제자리암"
    BORDERLINE = "경계성종양"
    SIMILAR = "유사암"
    GENERAL = "일반암"


class ComparisonFocus(str, Enum):
    """Comparison focus options (deterministic)."""
    AMOUNT = "amount"
    DEFINITION = "definition"
    CONDITION = "condition"


# Coverage domain mapping (deterministic, no LLM)
COVERAGE_DOMAIN_RULES: Dict[str, str] = {
    # Cancer domain
    "암진단비": "cancer",
    "일반암진단비": "cancer",
    "유사암진단비": "cancer",
    "소액암진단비": "cancer",
    "암재진단비": "cancer",
    "제자리암진단비": "cancer",
    "경계성종양진단비": "cancer",

    # Surgery domain
    "수술비": "surgery",
    "암수술비": "surgery",
    "뇌수술비": "surgery",
    "심장수술비": "surgery",

    # Brain domain
    "뇌출혈진단비": "brain",
    "뇌졸중진단비": "brain",
    "뇌혈관질환진단비": "brain",

    # Heart domain
    "급성심근경색진단비": "heart",
    "허혈성심장질환진단비": "heart",
}


# Surgery method keywords (deterministic pattern matching)
SURGERY_METHOD_KEYWORDS: Dict[str, List[str]] = {
    "da_vinci": ["다빈치", "da vinci", "davinci"],
    "robot": ["로봇", "robot"],
    "laparoscopic": ["복강경", "laparoscopic"],
}


# Cancer subtype keywords (deterministic pattern matching)
CANCER_SUBTYPE_KEYWORDS: Dict[str, List[str]] = {
    "제자리암": ["제자리암", "carcinoma in situ"],
    "경계성종양": ["경계성종양", "경계성", "borderline"],
    "유사암": ["유사암", "similar cancer"],
    "일반암": ["일반암", "general cancer", "암진단비"],
}


def detect_surgery_method(query: str) -> Optional[SurgeryMethod]:
    """
    Detect surgery method from query (deterministic).

    Args:
        query: User query string

    Returns:
        SurgeryMethod enum or None
    """
    query_lower = query.lower()

    for method, keywords in SURGERY_METHOD_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                return SurgeryMethod(method)

    return None


def detect_cancer_subtypes(query: str) -> Set[CancerSubtype]:
    """
    Detect cancer subtypes from query (deterministic).

    Args:
        query: User query string

    Returns:
        Set of CancerSubtype enums
    """
    query_lower = query.lower()
    detected = set()

    for subtype, keywords in CANCER_SUBTYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                detected.add(CancerSubtype(subtype))

    return detected


def detect_comparison_focus(query: str) -> Optional[ComparisonFocus]:
    """
    Detect comparison focus from query (deterministic).

    Args:
        query: User query string

    Returns:
        ComparisonFocus enum or None
    """
    query_lower = query.lower()

    # Amount-related keywords
    if any(kw in query_lower for kw in ["금액", "얼마", "보장금액", "지급금액"]):
        return ComparisonFocus.AMOUNT

    # Definition-related keywords
    if any(kw in query_lower for kw in ["정의", "범위", "무엇", "어떤"]):
        return ComparisonFocus.DEFINITION

    # Condition-related keywords
    if any(kw in query_lower for kw in ["조건", "요건", "면책", "한도"]):
        return ComparisonFocus.CONDITION

    return None


def resolve_coverage_domain(coverage_name: str) -> Optional[str]:
    """
    Resolve coverage domain from coverage name (deterministic).

    Args:
        coverage_name: Coverage name (normalized)

    Returns:
        Domain string or None
    """
    return COVERAGE_DOMAIN_RULES.get(coverage_name)


def get_main_coverage_priority(domain: str) -> List[str]:
    """
    Get main coverage priority for domain (deterministic).

    Args:
        domain: Coverage domain

    Returns:
        List of coverage names in priority order
    """
    priorities = {
        "cancer": ["일반암진단비", "암진단비"],
        "surgery": ["수술비", "암수술비"],
        "brain": ["뇌출혈진단비", "뇌졸중진단비"],
        "heart": ["급성심근경색진단비"],
    }

    return priorities.get(domain, [])
