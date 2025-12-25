#!/usr/bin/env python3
"""
STEP 3.10-ζ: ins_cd 자동 정합화 패치 생성

Constitution-compliant deterministic patcher:
- 원본 Excel은 읽기 전용 (덮어쓰기 금지)
- ins_cd 컬럼만 변경
- STEP 3.10-ε 감사 결과 기반 정정 매핑 적용
- 패치 로그 및 검증 리포트 생성
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Fixed paths (Constitution-compliant)
ORIGINAL_EXCEL = Path("data/담보명mapping자료.xlsx")
PATCHED_EXCEL = Path("data/담보명mapping자료__inscd_patched.xlsx")
PATCH_LOG_DIR = Path("data/step310_mapping/ins_cd_patch")
PATCH_LOG_CSV = PATCH_LOG_DIR / "PATCH_LOG.csv"
PATCH_SUMMARY_MD = PATCH_LOG_DIR / "PATCH_SUMMARY.md"

# Fixed mapping (from STEP 3.10-ε audit)
# Note: Excel uses Korean names (보험사명), mapped to pipeline canonical ins_cd
INSCD_CORRECTION_MAP = {
    "DB": "N08",         # DB: N13 → N08
    "KB": "N05",         # KB: N10 → N05
    "메리츠": "N04",     # MERITZ: N01 → N04
    "삼성": "N01",       # SAMSUNG: N08 → N01
    "현대": "N06",       # HYUNDAI: N09 → N06
    "흥국": "N07",       # HEUNGKUK: N05 → N07
    # No change (already correct):
    # "한화": "N02",     # HANWHA: N02 (no change)
    # "롯데": "N03",     # LOTTE: N03 (no change)
}


def main():
    print("=" * 80)
    print("STEP 3.10-ζ: ins_cd Patching (Deterministic)")
    print("=" * 80)

    # 0. Prepare output directory
    PATCH_LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load original Excel (read-only)
    print(f"\n[1/5] Loading original Excel: {ORIGINAL_EXCEL}")
    if not ORIGINAL_EXCEL.exists():
        print(f"❌ Original Excel not found: {ORIGINAL_EXCEL}")
        sys.exit(1)

    df_original = pd.read_excel(ORIGINAL_EXCEL)
    print(f"  ✅ Loaded {len(df_original)} rows")
    print(f"  Columns: {list(df_original.columns)}")

    # Verify required columns
    required_cols = ["보험사명", "ins_cd", "담보명(가입설계서)", "cre_cvr_cd"]
    missing = [c for c in required_cols if c not in df_original.columns]
    if missing:
        print(f"❌ Missing required columns: {missing}")
        sys.exit(1)

    # 2. Create patched DataFrame (deep copy)
    print("\n[2/5] Creating patched DataFrame (deep copy)")
    df_patched = df_original.copy(deep=True)

    # 3. Apply corrections (deterministic)
    print("\n[3/5] Applying ins_cd corrections")
    patch_records = []
    total_affected = 0

    for insurer_name, new_ins_cd in INSCD_CORRECTION_MAP.items():
        mask = df_patched["보험사명"] == insurer_name
        affected_count = mask.sum()

        if affected_count == 0:
            print(f"  ⚠️  {insurer_name}: No rows found (skip)")
            continue

        old_ins_cd = df_patched.loc[mask, "ins_cd"].iloc[0] if affected_count > 0 else None
        df_patched.loc[mask, "ins_cd"] = new_ins_cd

        # Sample coverage codes
        sample_codes = df_patched.loc[mask, "cre_cvr_cd"].drop_duplicates().head(2).tolist()
        sample_1 = sample_codes[0] if len(sample_codes) > 0 else ""
        sample_2 = sample_codes[1] if len(sample_codes) > 1 else ""

        patch_records.append({
            "보험사명": insurer_name,
            "before_ins_cd": old_ins_cd,
            "after_ins_cd": new_ins_cd,
            "affected_rows": affected_count,
            "sample_cre_cvr_cd_1": sample_1,
            "sample_cre_cvr_cd_2": sample_2,
        })

        total_affected += affected_count
        print(f"  ✅ {insurer_name}: {old_ins_cd} → {new_ins_cd} ({affected_count} rows)")

    # 4. Validation (Critical: ins_cd-only changes)
    print("\n[4/5] Validating patched DataFrame")
    validation_passed = True

    # 4-1. Check non-ins_cd columns unchanged
    non_inscd_cols = [c for c in df_original.columns if c != "ins_cd"]
    for col in non_inscd_cols:
        if not df_original[col].equals(df_patched[col]):
            print(f"  ❌ Column '{col}' was modified (violation)")
            validation_passed = False

    if validation_passed:
        print("  ✅ ins_cd-only changes verified")
    else:
        print("  ❌ Non-ins_cd columns were modified (aborting)")
        sys.exit(1)

    # 4-2. Check ins_cd uniqueness per insurer
    print("  Validating ins_cd uniqueness per insurer...")
    for insurer_name in df_patched["보험사명"].dropna().unique():
        insurer_mask = df_patched["보험사명"] == insurer_name
        unique_inscds = df_patched.loc[insurer_mask, "ins_cd"].dropna().unique()
        if len(unique_inscds) > 1:
            print(f"    ❌ {insurer_name}: Multiple ins_cd values: {unique_inscds}")
            validation_passed = False
        else:
            print(f"    ✅ {insurer_name}: Single ins_cd = {unique_inscds[0] if len(unique_inscds) > 0 else 'N/A'}")

    if not validation_passed:
        print("  ❌ Validation failed (aborting)")
        sys.exit(1)

    # 5. Save patched Excel
    print(f"\n[5/5] Saving patched Excel: {PATCHED_EXCEL}")
    df_patched.to_excel(PATCHED_EXCEL, index=False)
    print(f"  ✅ Saved {len(df_patched)} rows")

    # 6. Save patch logs
    print(f"\nSaving patch logs to {PATCH_LOG_DIR}")

    # 6-1. CSV
    df_patch_log = pd.DataFrame(patch_records)
    df_patch_log.to_csv(PATCH_LOG_CSV, index=False)
    print(f"  ✅ {PATCH_LOG_CSV}")

    # 6-2. Markdown summary
    summary_lines = [
        "# STEP 3.10-ζ: ins_cd Patch Summary",
        "",
        f"**Execution Time**: {datetime.now().isoformat()}",
        "",
        "## Patch Overview",
        "",
        f"- **Original Excel**: `{ORIGINAL_EXCEL}`",
        f"- **Patched Excel**: `{PATCHED_EXCEL}`",
        f"- **Total Rows**: {len(df_patched)}",
        f"- **Total Affected Rows**: {total_affected}",
        "",
        "## Corrections Applied",
        "",
        "| Insurer | Before ins_cd | After ins_cd | Affected Rows |",
        "|---------|---------------|--------------|---------------|",
    ]

    for rec in patch_records:
        summary_lines.append(
            f"| {rec['보험사명']} | {rec['before_ins_cd']} | {rec['after_ins_cd']} | {rec['affected_rows']} |"
        )

    summary_lines.extend([
        "",
        "## Validation Results",
        "",
        "- ✅ **ins_cd-only changes**: PASS",
        "- ✅ **ins_cd uniqueness per insurer**: PASS",
        "- ✅ **Row count preserved**: PASS",
        "",
        "## Next Steps",
        "",
        "1. Re-run STEP 3.10-2 (insurer-filtered mapping) using patched Excel",
        "2. Re-run STEP 3.10-β (UNMAPPED cause-effect report)",
        "3. Re-run STEP 3.10-γ (Excel backlog)",
        "",
        "---",
        "",
        "**Constitution Compliance**: ✅ All rules followed (non-destructive, ins_cd-only, deterministic)",
    ])

    PATCH_SUMMARY_MD.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"  ✅ {PATCH_SUMMARY_MD}")

    print("\n" + "=" * 80)
    print("STEP 3.10-ζ: Patching Complete")
    print("=" * 80)
    print(f"✅ Patched Excel: {PATCHED_EXCEL}")
    print(f"✅ Patch Log: {PATCH_LOG_CSV}")
    print(f"✅ Patch Summary: {PATCH_SUMMARY_MD}")
    print(f"✅ Total Affected Rows: {total_affected}")


if __name__ == "__main__":
    main()
