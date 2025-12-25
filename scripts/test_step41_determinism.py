#!/usr/bin/env python3
"""
STEP 4.1 Determinism Test

Verify that STEP 4.1 produces identical output for identical input.

Test:
- Same query → Same evidence attachment
- 100% reproducible
"""

import sys

sys.path.insert(0, 'scripts')
from step313_query_pipeline import QueryPipeline
from step41_detail_evidence_attach import ProposalDetailEvidenceAttacher
from step40_customer_formatter import CustomerResponseFormatter


def test_determinism():
    """
    Test determinism: same query → same output.

    Test queries:
    1. "삼성과 한화 암진단비 비교해줘"
    2. "KB 롯데 뇌졸중진단비 보여줘"
    3. "다빈치수술비"
    """
    print("=" * 80)
    print("STEP 4.1 Determinism Test")
    print("=" * 80)

    pipeline = QueryPipeline()
    formatter = CustomerResponseFormatter()
    attacher = ProposalDetailEvidenceAttacher()

    test_queries = [
        "삼성과 한화 암진단비 비교해줘",
        "KB 롯데 뇌졸중진단비 보여줘",
        "다빈치수술비",
    ]

    for query in test_queries:
        print(f"\n\n[Test Query] {query}")
        print("-" * 80)

        # Execute query twice
        print("\n[Execution 1]")
        result1 = pipeline.process(query)
        response1 = formatter.format(result1, query)
        enhanced1 = attacher.attach_evidence(result1, response1)

        print("\n[Execution 2]")
        result2 = pipeline.process(query)
        response2 = formatter.format(result2, query)
        enhanced2 = attacher.attach_evidence(result2, response2)

        # Compare outputs
        if enhanced1 == enhanced2:
            print("\n✅ DETERMINISM VERIFIED: Outputs are identical")
        else:
            print("\n❌ DETERMINISM FAILED: Outputs differ")
            print("\n[Diff Preview - First 500 chars]")
            print("Response 1:")
            print(enhanced1[:500])
            print("\nResponse 2:")
            print(enhanced2[:500])
            raise AssertionError(f"Determinism test failed for query: {query}")

    print("\n\n" + "=" * 80)
    print("✅ ALL DETERMINISM TESTS PASSED")
    print("=" * 80)


if __name__ == "__main__":
    test_determinism()
