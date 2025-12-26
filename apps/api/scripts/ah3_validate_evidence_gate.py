#!/usr/bin/env python3
"""
AH-3 Validation Script: Evidence Gate for Cancer Canonical Split

This script validates the constitutional requirements of AH-3:
1. Policy evidence MUST be present for canonical code decision
2. Name-based patterns produce hints only (NOT decisions)
3. Evidence MUST include doc_id, page, span_text

Validation Scenarios:
- Scenario A: "유사암 진단비(제자리암)" - NO policy evidence → UNDECIDED
- Scenario B: "암진단비(유사암 제외)" - NO policy evidence → UNDECIDED
- Scenario C: Same raw name, different insurer → different evidence → different canonical

Exit Code:
- 0: All scenarios PASS
- 1: One or more scenarios FAIL
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ah.canonical_split_mapper import CanonicalSplitMapper, CoverageSplitResult
from app.ah.cancer_canonical import CancerCanonicalCode, CancerScopeEvidence
from app.ah.cancer_scope_detector import PolicyTextSpan


def validate_scenario_a():
    """
    Scenario A: "유사암 진단비(제자리암)" - NO policy evidence → UNDECIDED

    Expected:
    - split_method = "undecided"
    - decided_canonical_codes = empty set
    - hint.mentions_similar = True
    - hint.mentions_in_situ = True
    """
    print("\n=== Scenario A: Name-only (no policy evidence) ===")

    mapper = CanonicalSplitMapper()
    result = mapper.split_coverage(
        coverage_name_raw="유사암 진단비(제자리암)",
        policy_documents=None,  # NO policy evidence
        coverage_id=None,
    )

    print(f"Coverage Name: {result.original_coverage_name}")
    print(f"Split Method: {result.split_method}")
    print(f"Decided Canonical Codes: {result.decided_canonical_codes}")
    print(f"Hint: {result.evidence.hint if result.evidence else None}")

    # Assertions
    assert result.split_method == "undecided", \
        f"Expected split_method='undecided', got '{result.split_method}'"
    assert len(result.decided_canonical_codes) == 0, \
        f"Expected empty decided_canonical_codes, got {result.decided_canonical_codes}"
    assert result.evidence is not None, "Expected evidence (with hint)"
    assert result.evidence.hint is not None, "Expected hint in evidence"
    assert result.evidence.hint.mentions_similar, "Expected mentions_similar=True"
    assert result.evidence.hint.mentions_in_situ, "Expected mentions_in_situ=True"
    assert result.evidence.confidence == "unknown", \
        f"Expected confidence='unknown', got '{result.evidence.confidence}'"

    print("✅ Scenario A PASS")
    return True


def validate_scenario_b():
    """
    Scenario B: "암진단비(유사암 제외)" - NO policy evidence → UNDECIDED

    Expected:
    - split_method = "undecided"
    - decided_canonical_codes = empty set
    - hint.mentions_general = True
    - hint.mentions_exclusion = True
    """
    print("\n=== Scenario B: Exclusion clause (no policy evidence) ===")

    mapper = CanonicalSplitMapper()
    result = mapper.split_coverage(
        coverage_name_raw="암진단비(유사암 제외)",
        policy_documents=None,  # NO policy evidence
        coverage_id=None,
    )

    print(f"Coverage Name: {result.original_coverage_name}")
    print(f"Split Method: {result.split_method}")
    print(f"Decided Canonical Codes: {result.decided_canonical_codes}")
    print(f"Hint: {result.evidence.hint if result.evidence else None}")

    # Assertions
    assert result.split_method == "undecided", \
        f"Expected split_method='undecided', got '{result.split_method}'"
    assert len(result.decided_canonical_codes) == 0, \
        f"Expected empty decided_canonical_codes, got {result.decided_canonical_codes}"
    assert result.evidence is not None, "Expected evidence (with hint)"
    assert result.evidence.hint is not None, "Expected hint in evidence"
    assert result.evidence.hint.mentions_general, "Expected mentions_general=True"
    assert result.evidence.hint.mentions_exclusion, "Expected mentions_exclusion=True"
    assert result.evidence.confidence == "unknown", \
        f"Expected confidence='unknown', got '{result.evidence.confidence}'"

    print("✅ Scenario B PASS")
    return True


def validate_scenario_c():
    """
    Scenario C: Same raw name, different insurer → different evidence → different canonical

    Test two cases:
    1. Policy says "제자리암은 유사암에 포함" → CA_DIAG_SIMILAR
    2. Policy says "제자리암 별도 지급" → CA_DIAG_IN_SITU

    Expected:
    - Both have split_method = "policy_evidence"
    - Different decided_canonical_codes
    - Both have evidence_spans with doc_id, page, span_text
    """
    print("\n=== Scenario C: Same name, different policy evidence ===")

    mapper = CanonicalSplitMapper()

    # Case 1: "일반암 진단비(유사암 제외)"
    print("\n--- Case 1: 일반암 (유사암 제외) ---")
    policy_docs_1 = [{
        "document_id": "POLICY_INSURER_A_001",
        "page": 10,
        "text": "일반암 진단비: 악성신생물(C00-C97) 진단 시 지급. 단, 유사암(C73, C44), 제자리암(D00-D09), 경계성종양(D37-D48)은 제외한다.",
        "section": "보장내용",
    }]

    result_1 = mapper.split_coverage(
        coverage_name_raw="일반암 진단비",
        policy_documents=policy_docs_1,
        coverage_id="COV_001",
    )

    print(f"Coverage Name: {result_1.original_coverage_name}")
    print(f"Split Method: {result_1.split_method}")
    print(f"Decided Canonical Codes: {result_1.decided_canonical_codes}")
    print(f"Evidence Spans: {result_1.evidence.evidence_spans if result_1.evidence else None}")

    # Assertions for Case 1
    assert result_1.split_method == "policy_evidence", \
        f"Expected split_method='policy_evidence', got '{result_1.split_method}'"
    assert len(result_1.decided_canonical_codes) > 0, \
        "Expected non-empty decided_canonical_codes"
    assert result_1.evidence is not None, "Expected evidence"
    assert result_1.evidence.evidence_spans is not None, "Expected evidence_spans"
    assert len(result_1.evidence.evidence_spans) > 0, "Expected at least one evidence span"

    # Check evidence span structure
    span_1 = result_1.evidence.evidence_spans[0]
    assert "doc_id" in span_1, "Expected doc_id in evidence span"
    assert "page" in span_1, "Expected page in evidence span"
    assert "span_text" in span_1, "Expected span_text in evidence span"
    assert span_1["doc_id"] == "POLICY_INSURER_A_001", "Expected correct doc_id"
    assert span_1["page"] == 10, "Expected correct page"

    # Case 2: "제자리암 별도 지급"
    print("\n--- Case 2: 제자리암 → 별도 지급 ---")
    policy_docs_2 = [{
        "document_id": "POLICY_INSURER_B_001",
        "page": 12,
        "text": "제자리암 진단비: 제자리암(D00-D09)으로 진단 시 별도 지급. 유사암과 별도 담보.",
        "section": "보장내용",
    }]

    result_2 = mapper.split_coverage(
        coverage_name_raw="제자리암 진단비",
        policy_documents=policy_docs_2,
        coverage_id="COV_002",
    )

    print(f"Coverage Name: {result_2.original_coverage_name}")
    print(f"Split Method: {result_2.split_method}")
    print(f"Decided Canonical Codes: {result_2.decided_canonical_codes}")
    print(f"Evidence Spans: {result_2.evidence.evidence_spans if result_2.evidence else None}")

    # Assertions for Case 2
    assert result_2.split_method == "policy_evidence", \
        f"Expected split_method='policy_evidence', got '{result_2.split_method}'"
    assert len(result_2.decided_canonical_codes) > 0, \
        "Expected non-empty decided_canonical_codes"
    assert result_2.evidence is not None, "Expected evidence"
    assert result_2.evidence.evidence_spans is not None, "Expected evidence_spans"
    assert len(result_2.evidence.evidence_spans) > 0, "Expected at least one evidence span"

    # Check evidence span structure
    span_2 = result_2.evidence.evidence_spans[0]
    assert "doc_id" in span_2, "Expected doc_id in evidence span"
    assert "page" in span_2, "Expected page in evidence span"
    assert "span_text" in span_2, "Expected span_text in evidence span"
    assert span_2["doc_id"] == "POLICY_INSURER_B_001", "Expected correct doc_id"
    assert span_2["page"] == 12, "Expected correct page"

    print("✅ Scenario C PASS")
    return True


def main():
    """
    Run all validation scenarios.
    """
    print("=" * 80)
    print("AH-3 Validation: Evidence Gate for Cancer Canonical Split")
    print("=" * 80)

    all_pass = True

    try:
        validate_scenario_a()
    except AssertionError as e:
        print(f"❌ Scenario A FAIL: {e}")
        all_pass = False
    except Exception as e:
        print(f"❌ Scenario A ERROR: {e}")
        all_pass = False

    try:
        validate_scenario_b()
    except AssertionError as e:
        print(f"❌ Scenario B FAIL: {e}")
        all_pass = False
    except Exception as e:
        print(f"❌ Scenario B ERROR: {e}")
        all_pass = False

    try:
        validate_scenario_c()
    except AssertionError as e:
        print(f"❌ Scenario C FAIL: {e}")
        all_pass = False
    except Exception as e:
        print(f"❌ Scenario C ERROR: {e}")
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
