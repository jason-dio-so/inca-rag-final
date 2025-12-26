"""
STEP NEXT-10-β: Forbidden Phrase Guard Test

Purpose: Ensure ViewModel never contains recommendation/judgment/interpretation phrases.

Constitutional Compliance:
- CLAUDE.md Article II: Deterministic Compiler Principle
- No LLM-generated recommendation/judgment/interpretation text
- All text must be fact-only or template-based

Forbidden Phrases (CLAUDE.md):
1. 추천/권장 phrases: "추천", "권장", "선택하세요", "고르세요", "가입하세요"
2. 우열 판단: "더 좋", "더 나은", "유리", "불리", "뛰어남", "우수", "최선", "최고"
3. 해석 문구: "사실상", "실질적으로", "거의", "유사", "비슷", "같은 담보", "동일"
4. 추론 문구: "종합적으로", "결론적으로", "판단", "평가", "분석 결과"

This test prevents regression to AI-generated judgment text.
"""

import re
from typing import Any, Dict, List, Optional

import pytest


# Forbidden phrase patterns (from CLAUDE.md + INCA_DIO_REQUIREMENTS.md)
FORBIDDEN_PATTERNS = [
    # 추천 문구
    r"추천",
    r"권장",
    r"선택하세요",
    r"고르세요",
    r"가입하세요",

    # 우열 판단
    r"더\s*좋",
    r"더\s*나[은음]",
    r"유리",
    r"불리",
    r"뛰어남",
    r"우수",
    r"최선",
    r"최고",

    # 해석 문구 (context-aware: exclude domain-specific terms)
    r"사실상",
    r"실질적으로",
    r"거의",
    r"(?<!유사암)유사(?!암)",  # "유사" but not "유사암" (domain term)
    r"비슷",
    r"같은\s*담보",
    r"동일",

    # 추론 문구
    r"종합적으로",
    r"결론적으로",
    r"판단",
    r"평가",
    r"분석\s*결과",
]

# Compile regex patterns
FORBIDDEN_REGEX = re.compile("|".join(FORBIDDEN_PATTERNS), re.IGNORECASE)


def extract_all_text(obj: Any, texts: List[str]) -> None:
    """
    Recursively extract all text fields from ViewModel JSON.

    Args:
        obj: ViewModel object (dict, list, or primitive)
        texts: List to accumulate all text values
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            # Extract text fields
            if isinstance(value, str):
                texts.append(value)
            else:
                extract_all_text(value, texts)
    elif isinstance(obj, list):
        for item in obj:
            extract_all_text(item, texts)
    elif isinstance(obj, str):
        texts.append(obj)


def check_forbidden_phrases(view_model: Dict[str, Any]) -> List[str]:
    """
    Check ViewModel for forbidden phrases.

    Args:
        view_model: ViewModel JSON dict

    Returns:
        List of violations (empty if compliant)

    Each violation format: "{field_path}: {matched_phrase}"
    """
    violations = []

    # Extract all text fields
    texts = []
    extract_all_text(view_model, texts)

    # Check each text field
    for text in texts:
        if not text:
            continue

        match = FORBIDDEN_REGEX.search(text)
        if match:
            violations.append(f"Text: '{text}' contains forbidden phrase: '{match.group()}'")

    return violations


def test_forbidden_phrases_empty_view_model():
    """Test: Empty ViewModel passes (no text to check)"""
    view_model = {
        "schema_version": "next4.v2",
        "generated_at": "2025-12-26T00:00:00Z",
        "header": {"user_query": ""},
        "snapshot": {"comparison_basis": "", "insurers": []},
        "fact_table": {"rows": []},
        "evidence_panels": []
    }

    violations = check_forbidden_phrases(view_model)
    assert violations == [], f"Empty ViewModel should have no violations: {violations}"


def test_forbidden_phrases_safe_text():
    """Test: Safe fact-only text passes"""
    view_model = {
        "schema_version": "next4.v2",
        "generated_at": "2025-12-26T00:00:00Z",
        "header": {
            "user_query": "삼성화재와 메리츠화재의 암진단비를 비교해줘"
        },
        "snapshot": {
            "comparison_basis": "암진단비",
            "insurers": [
                {"insurer": "SAMSUNG", "status": "OK"},
                {"insurer": "MERITZ", "status": "OK"}
            ],
            "filter_criteria": {
                "insurer_filter": ["SAMSUNG", "MERITZ"]
            }
        },
        "fact_table": {
            "columns": ["보험사", "담보명(정규화)", "보장금액"],
            "rows": [
                {
                    "insurer": "SAMSUNG",
                    "coverage_title_normalized": "암진단비",
                    "benefit_amount": {
                        "amount_value": 3000,
                        "amount_unit": "만원",
                        "display_text": "3,000만원"
                    },
                    "payout_conditions": [],
                    "row_status": "OK"
                }
            ],
            "table_type": "default"
        },
        "evidence_panels": [
            {
                "id": "ev_samsung_001",
                "insurer": "SAMSUNG",
                "doc_type": "가입설계서",
                "page": 2,
                "excerpt": "암진단비 3,000만원 (최초 1회 한, 90일 대기기간)"
            }
        ]
    }

    violations = check_forbidden_phrases(view_model)
    assert violations == [], f"Safe fact-only text should pass: {violations}"


def test_forbidden_phrases_recommendation():
    """Test: Recommendation phrases are detected"""
    view_model = {
        "schema_version": "next4.v2",
        "generated_at": "2025-12-26T00:00:00Z",
        "header": {
            "user_query": "암진단비 비교"
        },
        "snapshot": {
            "comparison_basis": "암진단비",
            "insurers": []
        },
        "fact_table": {
            "rows": [
                {
                    "insurer": "SAMSUNG",
                    "coverage_title_normalized": "암진단비",
                    "note_text": "이 상품을 추천합니다",  # FORBIDDEN
                    "row_status": "OK"
                }
            ]
        },
        "evidence_panels": []
    }

    violations = check_forbidden_phrases(view_model)
    assert len(violations) > 0, "Should detect '추천' phrase"
    assert any("추천" in v for v in violations), f"Should mention '추천' in violation: {violations}"


def test_forbidden_phrases_judgment():
    """Test: Judgment phrases are detected"""
    view_model = {
        "schema_version": "next4.v2",
        "generated_at": "2025-12-26T00:00:00Z",
        "header": {
            "user_query": "보험료 비교"
        },
        "snapshot": {
            "comparison_basis": "보험료",
            "insurers": []
        },
        "fact_table": {
            "rows": [
                {
                    "insurer": "SAMSUNG",
                    "coverage_title_normalized": "담보",
                    "note_text": "A사가 더 좋은 조건입니다",  # FORBIDDEN
                    "row_status": "OK"
                }
            ]
        },
        "evidence_panels": []
    }

    violations = check_forbidden_phrases(view_model)
    assert len(violations) > 0, "Should detect '더 좋' phrase"


def test_forbidden_phrases_interpretation():
    """Test: Interpretation phrases are detected"""
    view_model = {
        "schema_version": "next4.v2",
        "generated_at": "2025-12-26T00:00:00Z",
        "header": {
            "user_query": "담보 비교"
        },
        "snapshot": {
            "comparison_basis": "담보",
            "insurers": []
        },
        "fact_table": {
            "rows": [
                {
                    "insurer": "SAMSUNG",
                    "coverage_title_normalized": "담보",
                    "note_text": "사실상 같은 담보입니다",  # FORBIDDEN
                    "row_status": "OK"
                }
            ]
        },
        "evidence_panels": []
    }

    violations = check_forbidden_phrases(view_model)
    assert len(violations) > 0, "Should detect '사실상', '같은 담보' phrases"


def test_forbidden_phrases_inference():
    """Test: Inference phrases are detected"""
    view_model = {
        "schema_version": "next4.v2",
        "generated_at": "2025-12-26T00:00:00Z",
        "header": {
            "user_query": "보험료 비교"
        },
        "snapshot": {
            "comparison_basis": "보험료",
            "insurers": []
        },
        "fact_table": {
            "rows": [
                {
                    "insurer": "SAMSUNG",
                    "coverage_title_normalized": "담보",
                    "note_text": "종합적으로 판단하면 유리합니다",  # FORBIDDEN (multiple)
                    "row_status": "OK"
                }
            ]
        },
        "evidence_panels": []
    }

    violations = check_forbidden_phrases(view_model)
    assert len(violations) > 0, "Should detect '종합적으로', '판단', '유리' phrases"


def test_forbidden_phrases_evidence_excerpt():
    """Test: Evidence excerpts quote original documents (acceptable but flagged)"""
    view_model = {
        "schema_version": "next4.v2",
        "generated_at": "2025-12-26T00:00:00Z",
        "header": {
            "user_query": "암진단비"
        },
        "snapshot": {
            "comparison_basis": "암진단비",
            "insurers": []
        },
        "fact_table": {
            "rows": []
        },
        "evidence_panels": [
            {
                "id": "ev_001",
                "insurer": "SAMSUNG",
                "doc_type": "약관",
                "page": 5,
                # NOTE: Evidence excerpts quote original documents verbatim.
                # If the original document contains forbidden phrases, this is acceptable
                # because we're not generating judgment - we're quoting.
                "excerpt": "보험료가 저렴하여 유리한 상품입니다 (원문 인용)"
            }
        ]
    }

    violations = check_forbidden_phrases(view_model)
    # Evidence excerpts are direct quotes from original documents
    # Forbidden phrases in evidence are acceptable (we're quoting, not judging)
    # This test verifies the guard detects them, but we accept them as quotes
    assert len(violations) > 0, "Should detect forbidden phrases even in evidence"
    # Violations are expected and acceptable for evidence excerpts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
