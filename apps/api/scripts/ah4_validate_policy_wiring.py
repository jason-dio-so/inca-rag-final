#!/usr/bin/env python3
"""
AH-4 Validation Script: Policy Evidence Retrieval Wiring + Evidence Typing

This script validates:
1. Evidence typing (DEFINITION_INCLUDED vs SEPARATE_BENEFIT vs EXCLUSION)
2. Policy evidence retrieval from DB
3. End-to-end canonical split with evidence typing

Validation Scenarios:
- Scenario 1: Definition-only ("유사암은 ... 제자리암/경계성종양을 포함")
- Scenario 2: Separate benefit ("제자리암 별도 지급/별도 담보")
- Scenario 3: Exclusion ("일반암 ... 단 유사암/제자리암/경계성종양 제외")
- Scenario 4: DB wiring smoke test (실제 DB 조회)

Exit Code:
- 0: All scenarios PASS
- 1: One or more scenarios FAIL
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ah.cancer_evidence_typer import (
    CancerEvidenceTyper,
    CancerEvidenceType,
)
from app.ah.cancer_scope_detector import (
    CancerScopeDetector,
    PolicyTextSpan,
)
from app.ah.cancer_canonical import CancerCanonicalCode


def validate_scenario_1():
    """
    Scenario 1: Definition-only

    Policy span: "유사암은 ... 제자리암/경계성종양을 포함"
    Coverage name: "유사암진단비"

    Expected:
    - evidence_type = DEFINITION_INCLUDED
    - decided = {CA_DIAG_SIMILAR}
    - IN_SITU/BORDERLINE NOT in decided (they're just in definition)
    """
    print("\n=== Scenario 1: Definition-only ===")

    policy_text = "유사암 정의: 갑상선암(C73), 기타피부암(C44), 제자리암(D00-D09), 경계성종양(D37-D48)을 포함한다."

    # Test evidence typing
    typer = CancerEvidenceTyper()
    type_result = typer.classify_evidence(policy_text)

    print(f"Policy text: {policy_text}")
    print(f"Evidence type: {type_result.evidence_type}")
    print(f"Matched pattern: {type_result.matched_pattern}")

    assert type_result.evidence_type == CancerEvidenceType.DEFINITION_INCLUDED, \
        f"Expected DEFINITION_INCLUDED, got {type_result.evidence_type}"

    # Test scope detection
    detector = CancerScopeDetector()
    span = PolicyTextSpan(
        document_id="TEST_DOC_1",
        page=10,
        span_text=policy_text,
        section="보장내용",
    )
    evidence = detector.detect_scope_from_text(policy_text, span)

    print(f"includes_general: {evidence.includes_general}")
    print(f"includes_similar: {evidence.includes_similar}")
    print(f"includes_in_situ: {evidence.includes_in_situ}")
    print(f"includes_borderline: {evidence.includes_borderline}")
    print(f"canonical_code: {evidence.get_canonical_code()}")

    # Assertions
    assert evidence.includes_similar, "Expected includes_similar=True"
    assert not evidence.includes_in_situ, \
        "Expected includes_in_situ=False (definition only, not separate benefit)"
    assert not evidence.includes_borderline, \
        "Expected includes_borderline=False (definition only, not separate benefit)"
    assert evidence.get_canonical_code() == CancerCanonicalCode.SIMILAR, \
        f"Expected CA_DIAG_SIMILAR, got {evidence.get_canonical_code()}"

    print("✅ Scenario 1 PASS")
    return True


def validate_scenario_2():
    """
    Scenario 2: Separate benefit

    Policy span: "제자리암(D00-D09) 진단 시 별도 지급/별도 담보"
    Coverage name: "제자리암진단비"

    Expected:
    - evidence_type = SEPARATE_BENEFIT
    - decided = {CA_DIAG_IN_SITU}
    """
    print("\n=== Scenario 2: Separate benefit ===")

    policy_text = "제자리암 진단비: 제자리암(D00-D09)으로 진단 시 별도 지급. 유사암과 별도 담보."

    # Test evidence typing
    typer = CancerEvidenceTyper()
    type_result = typer.classify_evidence(policy_text)

    print(f"Policy text: {policy_text}")
    print(f"Evidence type: {type_result.evidence_type}")
    print(f"Matched pattern: {type_result.matched_pattern}")

    assert type_result.evidence_type == CancerEvidenceType.SEPARATE_BENEFIT, \
        f"Expected SEPARATE_BENEFIT, got {type_result.evidence_type}"

    # Test scope detection
    detector = CancerScopeDetector()
    span = PolicyTextSpan(
        document_id="TEST_DOC_2",
        page=12,
        span_text=policy_text,
        section="보장내용",
    )
    evidence = detector.detect_scope_from_text(policy_text, span)

    print(f"includes_general: {evidence.includes_general}")
    print(f"includes_similar: {evidence.includes_similar}")
    print(f"includes_in_situ: {evidence.includes_in_situ}")
    print(f"includes_borderline: {evidence.includes_borderline}")
    print(f"canonical_code: {evidence.get_canonical_code()}")

    # Assertions
    assert evidence.includes_in_situ, "Expected includes_in_situ=True"
    assert not evidence.includes_similar, \
        "Expected includes_similar=False (별도 담보 context)"
    assert evidence.get_canonical_code() == CancerCanonicalCode.IN_SITU, \
        f"Expected CA_DIAG_IN_SITU, got {evidence.get_canonical_code()}"

    print("✅ Scenario 2 PASS")
    return True


def validate_scenario_3():
    """
    Scenario 3: Exclusion

    Policy span: "일반암 ... 단 유사암/제자리암/경계성종양 제외"
    Coverage name: "일반암진단비"

    Expected:
    - evidence_type = EXCLUSION
    - decided = {CA_DIAG_GENERAL}
    - SIMILAR/IN_SITU/BORDERLINE excluded
    """
    print("\n=== Scenario 3: Exclusion ===")

    policy_text = "일반암 진단비: 악성신생물(C00-C97) 진단 시 지급. 단, 유사암(C73, C44), 제자리암(D00-D09), 경계성종양(D37-D48)은 제외한다."

    # Test evidence typing
    typer = CancerEvidenceTyper()
    type_result = typer.classify_evidence(policy_text)

    print(f"Policy text: {policy_text}")
    print(f"Evidence type: {type_result.evidence_type}")
    print(f"Matched pattern: {type_result.matched_pattern}")

    assert type_result.evidence_type == CancerEvidenceType.EXCLUSION, \
        f"Expected EXCLUSION, got {type_result.evidence_type}"

    # Test scope detection
    detector = CancerScopeDetector()
    span = PolicyTextSpan(
        document_id="TEST_DOC_3",
        page=8,
        span_text=policy_text,
        section="보장내용",
    )
    evidence = detector.detect_scope_from_text(policy_text, span)

    print(f"includes_general: {evidence.includes_general}")
    print(f"includes_similar: {evidence.includes_similar}")
    print(f"includes_in_situ: {evidence.includes_in_situ}")
    print(f"includes_borderline: {evidence.includes_borderline}")
    print(f"canonical_code: {evidence.get_canonical_code()}")

    # Assertions
    assert evidence.includes_general, "Expected includes_general=True"
    assert not evidence.includes_similar, "Expected includes_similar=False (excluded)"
    assert not evidence.includes_in_situ, "Expected includes_in_situ=False (excluded)"
    assert not evidence.includes_borderline, "Expected includes_borderline=False (excluded)"
    assert evidence.get_canonical_code() == CancerCanonicalCode.GENERAL, \
        f"Expected CA_DIAG_GENERAL, got {evidence.get_canonical_code()}"

    print("✅ Scenario 3 PASS")
    return True


async def validate_scenario_4():
    """
    Scenario 4: DB wiring smoke test

    Test actual DB retrieval (if DB available).
    Skip if DB not available.
    """
    print("\n=== Scenario 4: DB wiring smoke test ===")

    try:
        import asyncpg
        from app.ah.policy_evidence_store import PolicyEvidenceStore
        from app.core.db import get_db_pool

        # Try to get DB pool
        try:
            db_pool = await get_db_pool()
        except Exception as e:
            print(f"⚠️  DB not available, skipping Scenario 4: {e}")
            return True

        # Create policy store
        store = PolicyEvidenceStore(db_pool)

        # Test retrieval for SAMSUNG
        print("\nTesting policy evidence retrieval for SAMSUNG...")
        spans = await store.get_policy_spans_for_cancer(
            insurer_code="SAMSUNG",
            limit=5,
        )

        print(f"Retrieved {len(spans)} policy spans")
        for i, span in enumerate(spans[:3]):
            print(f"\nSpan {i+1}:")
            print(f"  doc_id: {span.get('doc_id')}")
            print(f"  page: {span.get('page')}")
            print(f"  text (first 100 chars): {span.get('text', '')[:100]}...")
            print(f"  keyword_hits: {span.get('keyword_hits')}")

        # Basic assertions
        assert len(spans) > 0, "Expected at least one policy span for SAMSUNG"

        for span in spans:
            assert "doc_id" in span, "Expected doc_id in span"
            assert "page" in span, "Expected page in span"
            assert "text" in span, "Expected text in span"

        print("✅ Scenario 4 PASS (DB wiring OK)")
        return True

    except ImportError as e:
        print(f"⚠️  DB dependencies not available, skipping Scenario 4: {e}")
        return True
    except Exception as e:
        print(f"❌ Scenario 4 FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """
    Run all validation scenarios.
    """
    print("=" * 80)
    print("AH-4 Validation: Policy Evidence Wiring + Evidence Typing")
    print("=" * 80)

    all_pass = True

    # Scenario 1
    try:
        validate_scenario_1()
    except AssertionError as e:
        print(f"❌ Scenario 1 FAIL: {e}")
        all_pass = False
    except Exception as e:
        print(f"❌ Scenario 1 ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_pass = False

    # Scenario 2
    try:
        validate_scenario_2()
    except AssertionError as e:
        print(f"❌ Scenario 2 FAIL: {e}")
        all_pass = False
    except Exception as e:
        print(f"❌ Scenario 2 ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_pass = False

    # Scenario 3
    try:
        validate_scenario_3()
    except AssertionError as e:
        print(f"❌ Scenario 3 FAIL: {e}")
        all_pass = False
    except Exception as e:
        print(f"❌ Scenario 3 ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_pass = False

    # Scenario 4 (async)
    try:
        result = asyncio.run(validate_scenario_4())
        if not result:
            all_pass = False
    except Exception as e:
        print(f"❌ Scenario 4 ERROR: {e}")
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
