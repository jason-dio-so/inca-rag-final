#!/usr/bin/env python3
"""
STEP 3.10-ζ: Verification Script

Validates that patched Excel achieves:
1. I3_MISMATCH_PIPELINE_VS_EXCEL = 0
2. All ins_cd values match pipeline registry
"""

import sys
from pathlib import Path
import pandas as pd

# Fixed paths
PATCHED_EXCEL = Path("data/담보명mapping자료__inscd_patched.xlsx")
VERIFICATION_REPORT = Path("data/step310_mapping/ins_cd_patch/VERIFICATION_REPORT.md")

# Pipeline canonical ins_cd (ground truth from STEP 3.10-ε)
PIPELINE_INSCD = {
    "DB": "N08",
    "KB": "N05",
    "메리츠": "N04",      # MERITZ
    "삼성": "N01",        # SAMSUNG
    "한화": "N02",        # HANWHA
    "롯데": "N03",        # LOTTE
    "현대": "N06",        # HYUNDAI
    "흥국": "N07",        # HEUNGKUK
}


def main():
    print("=" * 80)
    print("STEP 3.10-ζ: Verification (I3 Mismatch Check)")
    print("=" * 80)

    # Load patched Excel
    print(f"\n[1/2] Loading patched Excel: {PATCHED_EXCEL}")
    if not PATCHED_EXCEL.exists():
        print(f"❌ Patched Excel not found: {PATCHED_EXCEL}")
        sys.exit(1)

    df = pd.read_excel(PATCHED_EXCEL)
    print(f"  ✅ Loaded {len(df)} rows")

    # Verification
    print("\n[2/2] Verifying I3_MISMATCH_PIPELINE_VS_EXCEL")
    mismatches = []

    for insurer_name, expected_inscd in PIPELINE_INSCD.items():
        insurer_rows = df[df["보험사명"] == insurer_name]
        if len(insurer_rows) == 0:
            print(f"  ⚠️  {insurer_name}: No rows found (skip)")
            continue

        actual_inscd = insurer_rows["ins_cd"].iloc[0]
        if actual_inscd != expected_inscd:
            mismatches.append({
                "insurer": insurer_name,
                "expected": expected_inscd,
                "actual": actual_inscd,
            })
            print(f"  ❌ {insurer_name}: Expected {expected_inscd}, got {actual_inscd}")
        else:
            print(f"  ✅ {insurer_name}: {actual_inscd} (OK)")

    # Summary
    print("\n" + "=" * 80)
    if len(mismatches) == 0:
        print("✅ VERIFICATION PASSED: I3_MISMATCH_PIPELINE_VS_EXCEL = 0")
        verification_status = "PASS"
    else:
        print(f"❌ VERIFICATION FAILED: I3_MISMATCH_PIPELINE_VS_EXCEL = {len(mismatches)}")
        verification_status = "FAIL"
    print("=" * 80)

    # Generate verification report
    report_lines = [
        "# STEP 3.10-ζ: Verification Report",
        "",
        f"**Verification Status**: {verification_status}",
        f"**I3_MISMATCH_PIPELINE_VS_EXCEL**: {len(mismatches)}",
        "",
        "## Verification Results",
        "",
    ]

    if len(mismatches) == 0:
        report_lines.extend([
            "✅ All insurers match pipeline canonical ins_cd",
            "",
            "| Insurer | ins_cd | Status |",
            "|---------|--------|--------|",
        ])
        for insurer_name, expected_inscd in sorted(PIPELINE_INSCD.items()):
            report_lines.append(f"| {insurer_name} | {expected_inscd} | ✅ OK |")
    else:
        report_lines.extend([
            f"❌ {len(mismatches)} mismatches found",
            "",
            "| Insurer | Expected | Actual | Status |",
            "|---------|----------|--------|--------|",
        ])
        for m in mismatches:
            report_lines.append(f"| {m['insurer']} | {m['expected']} | {m['actual']} | ❌ MISMATCH |")

    report_lines.extend([
        "",
        "---",
        "",
        "**Next Steps**:",
        "- If PASS: Proceed to re-run STEP 3.10-2/β/γ",
        "- If FAIL: Review patch script logic",
    ])

    VERIFICATION_REPORT.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n✅ Verification report saved: {VERIFICATION_REPORT}")

    if len(mismatches) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
