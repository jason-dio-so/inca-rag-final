#!/usr/bin/env python3
"""
AH-1 Validation Script: Universe Recall Test

Scenarios:
A. "일반암진단비" → 8 insurers (including SAMSUNG)
B. "암진단비" → Full cancer group
C. "unmapped_query_12345" → Unmapped handling
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.api.app.ah.universe_recall import recall_universe_from_query
from apps.api.app.ah.alias_index import get_alias_index


def print_section(title: str):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def validate_scenario_a():
    """
    Scenario A: "일반암진단비" → 8 insurers (including SAMSUNG)

    DoD:
    - All 8 main insurers in insurers_covered
    - SAMSUNG must be included
    - recalled_coverages includes SAMSUNG "암 진단비"
    """
    print_section("Scenario A: 일반암진단비 → 8 Insurers")

    query = "일반암진단비"
    result = recall_universe_from_query(query, apply_cancer_guardrail=True)

    print(f"Query: {query}")
    print(f"Canonical Codes Resolved: {result['canonical_codes']}")
    print(f"Recall Count: {result['recall_count']}")
    print(f"Insurers Covered: {result['insurers_covered']}")
    print(f"Unmapped: {result['unmapped']}")

    # Check SAMSUNG
    if 'SAMSUNG' in result['insurers_covered']:
        print("\n✅ SAMSUNG included in recall")
        samsung_coverages = [
            c for c in result['recalled_coverages'] if c['insurer'] == 'SAMSUNG'
        ]
        print(f"   SAMSUNG coverages: {len(samsung_coverages)}")
        for cov in samsung_coverages[:5]:
            print(f"   - {cov['coverage_name_raw']}")
    else:
        print("\n❌ SAMSUNG NOT included in recall (FAIL)")

    # Check 8 insurers (actual insurers in data)
    main_insurers = ['SAMSUNG', 'MERITZ', 'KB', 'DB', 'HANWHA', 'LOTTE', 'HYUNDAI', 'HEUNGKUK']
    covered_main = [ins for ins in main_insurers if ins in result['insurers_covered']]

    print(f"\nMain insurers covered: {len(covered_main)}/8")
    print(f"Covered: {covered_main}")

    missing = [ins for ins in main_insurers if ins not in result['insurers_covered']]
    if missing:
        print(f"Missing: {missing}")

    # Final verdict
    if len(covered_main) == 8 and 'SAMSUNG' in result['insurers_covered']:
        print("\n✅ Scenario A: PASS")
        return True
    else:
        print("\n❌ Scenario A: FAIL")
        return False


def validate_scenario_b():
    """
    Scenario B: "암진단비" → Full cancer group

    DoD:
    - Cancer guardrail expands to all cancer canonical codes
    - Recall includes 유사암, 제자리암, 경계성종양, etc.
    """
    print_section("Scenario B: 암진단비 → Full Cancer Group")

    query = "암진단비"
    result = recall_universe_from_query(query, apply_cancer_guardrail=True)

    print(f"Query: {query}")
    print(f"Canonical Codes Resolved: {len(result['canonical_codes'])} codes")
    print(f"Canonical Codes: {result['canonical_codes'][:10]}...")  # Show first 10
    print(f"Recall Count: {result['recall_count']}")
    print(f"Insurers Covered: {result['insurers_covered']}")

    # Sample recalled coverages
    print("\nSample Recalled Coverages:")
    for cov in result['recalled_coverages'][:10]:
        print(f"  - [{cov['insurer']}] {cov['coverage_name_raw']}")

    # Check if 유사암, 제자리암 included
    유사암_count = sum(
        1 for c in result['recalled_coverages'] if '유사암' in c['coverage_name_raw']
    )
    제자리암_count = sum(
        1 for c in result['recalled_coverages'] if '제자리암' in c['coverage_name_raw']
    )

    print(f"\n유사암 coverages: {유사암_count}")
    print(f"제자리암 coverages: {제자리암_count}")

    # Final verdict
    if len(result['canonical_codes']) >= 5 and 유사암_count > 0:
        print("\n✅ Scenario B: PASS")
        return True
    else:
        print("\n❌ Scenario B: FAIL")
        return False


def validate_scenario_c():
    """
    Scenario C: Unmapped query handling

    DoD:
    - Unmapped query returns unmapped=True
    - No crash
    - Empty canonical_codes, empty recalled_coverages
    """
    print_section("Scenario C: Unmapped Query Handling")

    query = "unmapped_query_xyz_12345"
    result = recall_universe_from_query(query, apply_cancer_guardrail=True)

    print(f"Query: {query}")
    print(f"Canonical Codes: {result['canonical_codes']}")
    print(f"Recall Count: {result['recall_count']}")
    print(f"Unmapped: {result['unmapped']}")

    # Final verdict
    if result['unmapped'] and result['recall_count'] == 0:
        print("\n✅ Scenario C: PASS")
        return True
    else:
        print("\n❌ Scenario C: FAIL")
        return False


def show_alias_index_stats():
    """
    Show alias index statistics.
    """
    print_section("Alias Index Statistics")

    alias_index = get_alias_index()
    stats = alias_index.get_stats()

    print(f"Total Aliases: {stats['total_aliases']}")
    print(f"Total Canonical Codes: {stats['total_canonical_codes']}")
    print(f"Cancer Canonical Codes: {stats['cancer_canonical_codes']}")


def main():
    """
    Run all validation scenarios.
    """
    print("="*80)
    print("  STEP NEXT-AH-1: Universe Recall Validation")
    print("="*80)

    show_alias_index_stats()

    results = []

    try:
        results.append(("Scenario A", validate_scenario_a()))
        results.append(("Scenario B", validate_scenario_b()))
        results.append(("Scenario C", validate_scenario_c()))
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Summary
    print_section("Summary")
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")

    all_passed = all(passed for _, passed in results)
    print(f"\nOverall: {'✅ ALL PASS' if all_passed else '❌ SOME FAILED'}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
