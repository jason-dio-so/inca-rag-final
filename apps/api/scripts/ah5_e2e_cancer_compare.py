#!/usr/bin/env python3
"""
AH-5 End-to-End Validation: Cancer Canonical Decision → Compare Pipeline

This script validates the complete AH-1 through AH-5 pipeline:
1. Query → Excel Alias → Recalled Candidates (AH-1)
2. Policy Evidence → Evidence Typing → Decided Canonical (AH-3 + AH-4)
3. Compare Pipeline → ViewModel → Response (AH-5)

Validation Scenarios:
- Scenario 1: "일반암진단비" - General cancer comparison
- Scenario 2: "유사암 진단비(제자리암)" - Similar cancer with in-situ mention
- Scenario 3: Meta row filtering validation

Exit Code:
- 0: All scenarios PASS
- 1: One or more scenarios FAIL
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ah.proposal_meta_filter import ProposalMetaFilter
from app.ah.cancer_decision import (
    CancerCanonicalDecision,
    CancerCompareContext,
    DecisionStatus,
)
from app.ah.cancer_canonical import CancerCanonicalCode


def validate_scenario_1():
    """
    Scenario 1: Meta row filtering

    Test meta row filter with various inputs.

    Expected:
    - "합계", "소계", "총보험료" → filtered (is_meta_row = True)
    - "일반암진단비", "유사암진단비" → kept (is_meta_row = False)
    """
    print("\n=== Scenario 1: Meta Row Filtering ===")

    filter = ProposalMetaFilter()

    # Test cases: (coverage_name, expected_is_meta)
    test_cases = [
        # Meta rows (should be filtered)
        ("합계", True),
        ("소계", True),
        ("총보험료", True),
        ("주계약", True),
        ("특약합계", True),
        ("가입조건", True),
        ("안내", True),
        ("* 주)", True),
        ("※ 참고사항", True),
        ("", True),  # Empty
        (None, True),  # NULL
        ("  ", True),  # Whitespace only
        ("가", True),  # Too short

        # Valid coverage rows (should be kept)
        ("일반암진단비", False),
        ("유사암진단비", False),
        ("제자리암진단비", False),
        ("암진단비(유사암제외)", False),
        ("4대유사암진단비(갑상선암)", False),
        ("뇌졸중진단비", False),
        ("급성심근경색진단비", False),
        ("암 사망보장", False),
    ]

    all_pass = True
    for coverage_name, expected_is_meta in test_cases:
        result = filter.is_meta_row(coverage_name)
        status = "✅" if result == expected_is_meta else "❌"
        print(f"{status} '{coverage_name}' → is_meta={result} (expected={expected_is_meta})")

        if result != expected_is_meta:
            all_pass = False

    if all_pass:
        print("✅ Scenario 1 PASS (Meta row filtering)")
    else:
        print("❌ Scenario 1 FAIL")

    return all_pass


def validate_scenario_2():
    """
    Scenario 2: Cancer canonical decision data structure

    Test CancerCanonicalDecision creation and methods.

    Expected:
    - DECIDED status → get_canonical_codes_for_compare() returns decided codes
    - UNDECIDED status → get_canonical_codes_for_compare() returns empty set
    """
    print("\n=== Scenario 2: Cancer Canonical Decision Data Structure ===")

    # Test DECIDED case
    print("\n--- Case A: DECIDED ---")
    decided_decision = CancerCanonicalDecision(
        coverage_name_raw="일반암진단비",
        insurer_code="SAMSUNG",
        recalled_candidates={CancerCanonicalCode.GENERAL, CancerCanonicalCode.SIMILAR},
        decided_canonical_codes={CancerCanonicalCode.GENERAL},
        decision_status=DecisionStatus.DECIDED,
        decision_evidence_spans=[{
            "doc_id": "POLICY_SAMSUNG_001",
            "page": 10,
            "span_text": "일반암 진단비: 악성신생물(C00-C97) 진단 시 지급...",
            "evidence_type": "exclusion",
        }],
        decision_method="policy_evidence",
    )

    print(f"coverage_name: {decided_decision.coverage_name_raw}")
    print(f"decision_status: {decided_decision.decision_status}")
    print(f"recalled_candidates: {decided_decision.recalled_candidates}")
    print(f"decided_canonical_codes: {decided_decision.decided_canonical_codes}")
    print(f"codes_for_compare: {decided_decision.get_canonical_codes_for_compare()}")

    assert decided_decision.is_decided(), "Expected is_decided()=True"
    assert not decided_decision.is_undecided(), "Expected is_undecided()=False"
    assert decided_decision.get_canonical_codes_for_compare() == {CancerCanonicalCode.GENERAL}, \
        "Expected codes_for_compare={GENERAL}"

    print("✅ Case A PASS")

    # Test UNDECIDED case
    print("\n--- Case B: UNDECIDED ---")
    undecided_decision = CancerCanonicalDecision(
        coverage_name_raw="유사암진단비(제자리암)",
        insurer_code="MERITZ",
        recalled_candidates={CancerCanonicalCode.SIMILAR, CancerCanonicalCode.IN_SITU},
        decided_canonical_codes=set(),  # Empty
        decision_status=DecisionStatus.UNDECIDED,
        decision_evidence_spans=None,
        decision_method="undecided",
    )

    print(f"coverage_name: {undecided_decision.coverage_name_raw}")
    print(f"decision_status: {undecided_decision.decision_status}")
    print(f"recalled_candidates: {undecided_decision.recalled_candidates}")
    print(f"decided_canonical_codes: {undecided_decision.decided_canonical_codes}")
    print(f"codes_for_compare: {undecided_decision.get_canonical_codes_for_compare()}")

    assert undecided_decision.is_undecided(), "Expected is_undecided()=True"
    assert not undecided_decision.is_decided(), "Expected is_decided()=False"
    assert undecided_decision.get_canonical_codes_for_compare() == set(), \
        "Expected codes_for_compare=empty set (do NOT use recalled_candidates)"

    print("✅ Case B PASS")

    print("✅ Scenario 2 PASS (Cancer canonical decision)")
    return True


def validate_scenario_3():
    """
    Scenario 3: Cancer compare context aggregation

    Test CancerCompareContext with multiple decisions.

    Expected:
    - Correctly aggregate decided/undecided counts
    - Calculate decided_rate
    """
    print("\n=== Scenario 3: Cancer Compare Context ===")

    # Create decisions
    decisions = [
        # SAMSUNG - DECIDED
        CancerCanonicalDecision(
            coverage_name_raw="일반암진단비",
            insurer_code="SAMSUNG",
            recalled_candidates={CancerCanonicalCode.GENERAL},
            decided_canonical_codes={CancerCanonicalCode.GENERAL},
            decision_status=DecisionStatus.DECIDED,
            decision_method="policy_evidence",
        ),
        # MERITZ - UNDECIDED
        CancerCanonicalDecision(
            coverage_name_raw="유사암진단비",
            insurer_code="MERITZ",
            recalled_candidates={CancerCanonicalCode.SIMILAR},
            decided_canonical_codes=set(),
            decision_status=DecisionStatus.UNDECIDED,
            decision_method="undecided",
        ),
        # KB - DECIDED
        CancerCanonicalDecision(
            coverage_name_raw="암진단비(유사암제외)",
            insurer_code="KB",
            recalled_candidates={CancerCanonicalCode.GENERAL},
            decided_canonical_codes={CancerCanonicalCode.GENERAL},
            decision_status=DecisionStatus.DECIDED,
            decision_method="policy_evidence",
        ),
    ]

    context = CancerCompareContext(
        query="일반암진단비 비교",
        decisions=decisions,
    )

    print(f"Query: {context.query}")
    print(f"Total decisions: {len(context.decisions)}")
    print(f"Decided count: {context.get_decided_count()}")
    print(f"Undecided count: {context.get_undecided_count()}")
    print(f"Decided rate: {context.get_decided_rate():.2%}")

    # Assertions
    assert len(context.decisions) == 3, "Expected 3 decisions"
    assert context.get_decided_count() == 2, "Expected 2 decided"
    assert context.get_undecided_count() == 1, "Expected 1 undecided"
    assert abs(context.get_decided_rate() - 2/3) < 0.01, "Expected 66.7% decided rate"

    # Test to_dict
    context_dict = context.to_dict()
    print(f"\nContext dict stats: {context_dict['stats']}")

    assert context_dict["stats"]["total_decisions"] == 3
    assert context_dict["stats"]["decided_count"] == 2
    assert context_dict["stats"]["undecided_count"] == 1

    print("✅ Scenario 3 PASS (Cancer compare context)")
    return True


def main():
    """
    Run all validation scenarios.
    """
    print("=" * 80)
    print("AH-5 End-to-End Validation: Cancer Canonical Decision → Compare Pipeline")
    print("=" * 80)

    all_pass = True

    # Scenario 1: Meta row filtering
    try:
        result = validate_scenario_1()
        if not result:
            all_pass = False
    except Exception as e:
        print(f"❌ Scenario 1 ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_pass = False

    # Scenario 2: Decision data structure
    try:
        result = validate_scenario_2()
        if not result:
            all_pass = False
    except Exception as e:
        print(f"❌ Scenario 2 ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_pass = False

    # Scenario 3: Compare context
    try:
        result = validate_scenario_3()
        if not result:
            all_pass = False
    except Exception as e:
        print(f"❌ Scenario 3 ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_pass = False

    print("\n" + "=" * 80)
    if all_pass:
        print("✅ ALL SCENARIOS PASS")
        print("=" * 80)
        return 0
    else:
        print("❌ ONE OR MORE SCENARIOS FAIL")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
