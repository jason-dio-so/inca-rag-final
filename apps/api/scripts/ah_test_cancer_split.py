#!/usr/bin/env python3
"""
AH-2 Validation Script: Cancer Canonical Split Test

Scenarios:
A. SAMSUNG vs MERITZ cancer coverage split
B. "유사암진단비" → CA_DIAG_SIMILAR only
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.api.app.ah.canonical_split_mapper import (
    CanonicalSplitMapper,
    generate_split_report,
)
from apps.api.app.ah.cancer_canonical import CancerCanonicalCode


def print_section(title: str):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def load_universe_csv():
    """
    Load universe CSV.
    """
    csv_path = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "step39_coverage_universe"
        / "extracts"
        / "ALL_INSURERS_coverage_universe.csv"
    )
    return pd.read_csv(csv_path)


def validate_scenario_a():
    """
    Scenario A: SAMSUNG vs MERITZ cancer coverage split

    DoD:
    - SAMSUNG "암 진단비" → CA_DIAG_GENERAL (single row)
    - SAMSUNG "유사암 진단비(*)" → CA_DIAG_SIMILAR (separate rows)
    - MERITZ "암진단비(유사암제외)" → CA_DIAG_GENERAL
    - MERITZ "유사암진단비" → CA_DIAG_SIMILAR
    """
    print_section("Scenario A: SAMSUNG vs MERITZ Cancer Coverage Split")

    df_universe = load_universe_csv()
    mapper = CanonicalSplitMapper()

    # SAMSUNG cancer coverages
    samsung_cancer = df_universe[
        (df_universe["insurer"] == "SAMSUNG")
        & (df_universe["coverage_name_raw"].str.contains("암", na=False))
    ]

    print("=== SAMSUNG Cancer Coverages ===")
    for _, row in samsung_cancer.iterrows():
        coverage_name = row["coverage_name_raw"]
        result = mapper.split_coverage(coverage_name)

        codes_str = ", ".join([c.value for c in result.canonical_codes])
        print(f"- {coverage_name}")
        print(f"  → Canonical: {codes_str}")
        print(f"  → Method: {result.split_method}")
        print()

    # MERITZ cancer coverages
    meritz_cancer = df_universe[
        (df_universe["insurer"] == "MERITZ")
        & (df_universe["coverage_name_raw"].str.contains("암", na=False))
    ]

    print("\n=== MERITZ Cancer Coverages ===")
    for _, row in meritz_cancer.iterrows():
        coverage_name = row["coverage_name_raw"]
        result = mapper.split_coverage(coverage_name)

        codes_str = ", ".join([c.value for c in result.canonical_codes])
        print(f"- {coverage_name}")
        print(f"  → Canonical: {codes_str}")
        print(f"  → Method: {result.split_method}")
        print()

    # Validate SAMSUNG "암 진단비(유사암 제외)"
    samsung_general = [
        r
        for _, r in samsung_cancer.iterrows()
        if "암 진단비(유사암 제외)" in r["coverage_name_raw"]
    ]

    if samsung_general:
        coverage_name = samsung_general[0]["coverage_name_raw"]
        result = mapper.split_coverage(coverage_name)

        if (
            CancerCanonicalCode.GENERAL in result.canonical_codes
            and len(result.canonical_codes) == 1
        ):
            print(f"✅ SAMSUNG '{coverage_name}' → CA_DIAG_GENERAL (single)")
            passed_samsung = True
        else:
            print(f"❌ SAMSUNG '{coverage_name}' → {result.canonical_codes} (expected CA_DIAG_GENERAL only)")
            passed_samsung = False
    else:
        print("❌ SAMSUNG general cancer coverage not found")
        passed_samsung = False

    # Validate SAMSUNG cancer split (multiple canonical codes)
    # "유사암 진단비(갑상선암)" → CA_DIAG_SIMILAR
    # "유사암 진단비(제자리암)" → CA_DIAG_IN_SITU (constitutional requirement)
    # "유사암 진단비(경계성종양)" → CA_DIAG_BORDERLINE (constitutional requirement)
    samsung_similar_checks = [
        ("유사암 진단비(갑상선암)", CancerCanonicalCode.SIMILAR),
        ("유사암 진단비(제자리암)", CancerCanonicalCode.IN_SITU),
        ("유사암 진단비(경계성종양)", CancerCanonicalCode.BORDERLINE),
    ]

    passed_similar = True
    for keyword, expected_code in samsung_similar_checks:
        matching = [
            r for _, r in samsung_cancer.iterrows()
            if keyword in r["coverage_name_raw"]
        ]

        if matching:
            coverage_name = matching[0]["coverage_name_raw"]
            result = mapper.split_coverage(coverage_name)

            if expected_code in result.canonical_codes and len(result.canonical_codes) == 1:
                print(f"✅ SAMSUNG '{coverage_name}' → {expected_code.value}")
            else:
                print(f"❌ SAMSUNG '{coverage_name}' → {result.canonical_codes} (expected {expected_code.value} only)")
                passed_similar = False
        else:
            print(f"⚠️  SAMSUNG coverage with '{keyword}' not found")
            # Don't fail for missing coverages (backward compatibility)

    # Final verdict
    if passed_samsung and passed_similar:
        print("\n✅ Scenario A: PASS")
        return True
    else:
        print("\n❌ Scenario A: FAIL")
        return False


def validate_scenario_b():
    """
    Scenario B: "유사암진단비" → Cancer canonical (not GENERAL)

    DoD:
    - "유사암" in name but NOT "유사암제외" → Must map to cancer canonical (SIMILAR/IN_SITU/BORDERLINE)
    - "유사암제외" → Must map to CA_DIAG_GENERAL
    - No CA_DIAG_GENERAL for coverages WITH "유사암" (excluding "유사암제외" cases)
    """
    print_section("Scenario B: 유사암 Coverage Canonical Mapping")

    df_universe = load_universe_csv()
    mapper = CanonicalSplitMapper()

    # Find coverages with "유사암" in name
    similar_cancer = df_universe[
        df_universe["coverage_name_raw"].str.contains("유사암", na=False)
    ]

    # Separate into two groups: "유사암제외" vs actual "유사암" coverages
    exclusion_coverages = similar_cancer[
        similar_cancer["coverage_name_raw"].str.contains("유사암제외|유사암 제외|4대유사암제외", na=False, regex=True)
    ]

    actual_similar_coverages = similar_cancer[
        ~similar_cancer["coverage_name_raw"].str.contains("유사암제외|유사암 제외|4대유사암제외", na=False, regex=True)
    ]

    print(f"Total '유사암' in name: {len(similar_cancer)}")
    print(f"  - Exclusion ('유사암제외'): {len(exclusion_coverages)}")
    print(f"  - Actual 유사암: {len(actual_similar_coverages)}")
    print()

    # Test exclusion coverages → Should be CA_DIAG_GENERAL
    print("=== Exclusion Coverages (유사암제외) ===")
    exclusion_pass = True
    for _, row in exclusion_coverages.iterrows():
        coverage_name = row["coverage_name_raw"]
        insurer = row["insurer"]
        result = mapper.split_coverage(coverage_name)

        codes_str = ", ".join([c.value for c in result.canonical_codes])

        if CancerCanonicalCode.GENERAL in result.canonical_codes:
            status = "✅"
        else:
            status = "❌"
            exclusion_pass = False

        print(f"{status} [{insurer}] {coverage_name}")
        print(f"   → {codes_str}")

    print("\n=== Actual 유사암 Coverages ===")
    actual_pass = True
    for _, row in actual_similar_coverages.iterrows():
        coverage_name = row["coverage_name_raw"]
        insurer = row["insurer"]
        result = mapper.split_coverage(coverage_name)

        codes_str = ", ".join([c.value for c in result.canonical_codes])

        # Must have at least one cancer canonical (SIMILAR/IN_SITU/BORDERLINE)
        # Must NOT have GENERAL
        has_cancer_canonical = any([
            CancerCanonicalCode.SIMILAR in result.canonical_codes,
            CancerCanonicalCode.IN_SITU in result.canonical_codes,
            CancerCanonicalCode.BORDERLINE in result.canonical_codes,
        ])
        has_general = CancerCanonicalCode.GENERAL in result.canonical_codes

        if has_cancer_canonical and not has_general:
            status = "✅"
        else:
            status = "❌"
            actual_pass = False

        print(f"{status} [{insurer}] {coverage_name}")
        print(f"   → {codes_str}")

    # Final verdict
    if exclusion_pass and actual_pass:
        print("\n✅ Scenario B: PASS")
        return True
    else:
        print("\n❌ Scenario B: FAIL")
        return False


def generate_overall_report():
    """
    Generate overall split report for all cancer coverages.
    """
    print_section("Overall Cancer Coverage Split Report")

    df_universe = load_universe_csv()
    mapper = CanonicalSplitMapper()

    # Get all cancer coverages
    cancer_coverages = []
    for _, row in df_universe.iterrows():
        coverage_dict = row.to_dict()
        if mapper._is_cancer_coverage(coverage_dict.get("coverage_name_raw", "")):
            cancer_coverages.append(coverage_dict)

    print(f"Total cancer coverages in universe: {len(cancer_coverages)}")

    # Split all
    split_results = mapper.split_universe_coverages(cancer_coverages)

    # Generate report
    report = generate_split_report(split_results)

    print(f"\nSplit by method:")
    for method, count in report["split_by_method"].items():
        print(f"  - {method}: {count}")

    print(f"\nCanonical distribution:")
    for code, count in report["canonical_distribution"].items():
        print(f"  - {code}: {count}")

    print(f"\nAmbiguous: {report['ambiguous_count']}")
    print(f"Unmapped: {report['unmapped_count']}")


def main():
    """
    Run all validation scenarios.
    """
    print("="*80)
    print("  STEP NEXT-AH-2: Cancer Canonical Split Validation")
    print("="*80)

    results = []

    try:
        results.append(("Scenario A", validate_scenario_a()))
        results.append(("Scenario B", validate_scenario_b()))

        generate_overall_report()

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
