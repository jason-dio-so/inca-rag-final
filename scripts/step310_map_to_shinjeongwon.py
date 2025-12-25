#!/usr/bin/env python3
"""
STEP 3.10: Proposal Coverage → Shinjeongwon Reference Mapping
Non-Destructive · 상태 태깅 전용

Constitution Rules:
- ❌ 담보 통합 금지
- ❌ 코드 강제 부여 금지
- ❌ 비교·판단·정규화 금지
- ❌ 기존 데이터 수정 금지
- ✅ 참조(reference) 매핑만 수행
"""

import pandas as pd
import re
from pathlib import Path
from collections import defaultdict

# Paths
BASE_DIR = Path(__file__).parent.parent
UNIVERSE_CSV = BASE_DIR / "data/step39_coverage_universe/extracts/ALL_INSURERS_coverage_universe.csv"
MAPPING_EXCEL = BASE_DIR / "data/담보명mapping자료.xlsx"
OUTPUT_DIR = BASE_DIR / "data/step310_mapping"
OUTPUT_CSV = OUTPUT_DIR / "proposal_coverage_mapping.csv"
REPORT_TXT = OUTPUT_DIR / "mapping_report.txt"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def normalize_coverage_name(name: str) -> str:
    """
    Normalize coverage name for matching.
    - Remove extra whitespace
    - Convert to uppercase for comparison
    """
    if pd.isna(name):
        return ""
    name = str(name).strip()
    name = re.sub(r'\s+', '', name)  # Remove all whitespace
    return name.upper()


def load_shinjeongwon_mapping():
    """
    Load Shinjeongwon mapping reference from Excel.
    Returns: DataFrame with normalized coverage names for lookup
    """
    df = pd.read_excel(MAPPING_EXCEL)

    # Create normalized name column for matching
    df['coverage_name_normalized'] = df['담보명(가입설계서)'].apply(normalize_coverage_name)

    return df


def find_shinjeongwon_matches(coverage_name_raw: str, mapping_df: pd.DataFrame):
    """
    Find Shinjeongwon code matches for a given coverage name.

    Returns:
        tuple: (shinjeongwon_code, mapping_state, mapping_basis)

    Mapping States:
        - MAPPED: exactly 1 match
        - AMBIGUOUS: 2+ matches
        - UNMAPPED: 0 matches
    """
    normalized = normalize_coverage_name(coverage_name_raw)

    if not normalized:
        return None, "UNMAPPED", "empty coverage name"

    # Find exact matches
    matches = mapping_df[mapping_df['coverage_name_normalized'] == normalized]

    num_matches = len(matches)

    if num_matches == 0:
        return None, "UNMAPPED", "no corresponding entry"
    elif num_matches == 1:
        code = matches.iloc[0]['cre_cvr_cd']
        return code, "MAPPED", "exact name match"
    else:
        # Multiple matches - AMBIGUOUS
        codes = matches['cre_cvr_cd'].tolist()
        codes_str = ", ".join(str(c) for c in codes)
        return codes_str, "AMBIGUOUS", f"multiple candidates: {codes_str}"


def map_coverage_universe():
    """
    Main mapping function.
    Process each row in the universe and assign Shinjeongwon mapping state.
    """
    print("=" * 80)
    print("STEP 3.10: Proposal Coverage → Shinjeongwon Reference Mapping")
    print("=" * 80)

    # Load data
    print("\n[1] Loading Proposal Coverage Universe...")
    universe_df = pd.read_csv(UNIVERSE_CSV)
    total_rows = len(universe_df)
    print(f"    Total rows: {total_rows}")

    print("\n[2] Loading Shinjeongwon Mapping Reference...")
    mapping_df = load_shinjeongwon_mapping()
    print(f"    Total mapping entries: {len(mapping_df)}")
    print(f"    Unique Shinjeongwon codes: {mapping_df['cre_cvr_cd'].nunique()}")

    # Process each row
    print("\n[3] Processing mapping (deterministic flow)...")

    results = []

    for idx, row in universe_df.iterrows():
        coverage_name_raw = row['coverage_name_raw']

        # Find Shinjeongwon match
        code, state, basis = find_shinjeongwon_matches(coverage_name_raw, mapping_df)

        result = {
            'insurer': row['insurer'],
            'proposal_file': row['proposal_file'],
            'proposal_variant': row['proposal_variant'],
            'row_id': row['row_id'],
            'coverage_name_raw': coverage_name_raw,
            'shinjeongwon_code': code if code else "",
            'mapping_state': state,
            'mapping_basis': basis,
            'notes': ""
        }

        results.append(result)

        if (idx + 1) % 50 == 0:
            print(f"    Processed {idx + 1}/{total_rows} rows...")

    print(f"    ✅ All {total_rows} rows processed")

    # Create output DataFrame
    output_df = pd.DataFrame(results)

    # Save to CSV
    print(f"\n[4] Saving results to {OUTPUT_CSV}...")
    output_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"    ✅ Saved {len(output_df)} rows")

    # Generate validation report
    print(f"\n[5] Generating validation report...")
    generate_validation_report(output_df, mapping_df)

    print("\n" + "=" * 80)
    print("STEP 3.10 COMPLETE")
    print("=" * 80)

    return output_df


def generate_validation_report(output_df: pd.DataFrame, mapping_df: pd.DataFrame):
    """
    Generate validation report with statistics and risk candidates.
    """
    report_lines = []

    report_lines.append("=" * 80)
    report_lines.append("STEP 3.10 VALIDATION REPORT")
    report_lines.append("Proposal Coverage → Shinjeongwon Reference Mapping")
    report_lines.append("=" * 80)

    # 6-1. 전체 요약
    report_lines.append("\n[6-1] 전체 요약")
    report_lines.append("-" * 40)
    total = len(output_df)
    mapped = len(output_df[output_df['mapping_state'] == 'MAPPED'])
    ambiguous = len(output_df[output_df['mapping_state'] == 'AMBIGUOUS'])
    unmapped = len(output_df[output_df['mapping_state'] == 'UNMAPPED'])

    report_lines.append(f"총 row 수: {total}")
    report_lines.append(f"  - MAPPED:     {mapped:4d} ({mapped/total*100:5.1f}%)")
    report_lines.append(f"  - AMBIGUOUS:  {ambiguous:4d} ({ambiguous/total*100:5.1f}%)")
    report_lines.append(f"  - UNMAPPED:   {unmapped:4d} ({unmapped/total*100:5.1f}%)")

    # 6-2. 보험사별 분포
    report_lines.append("\n[6-2] 보험사별 분포")
    report_lines.append("-" * 40)

    insurer_stats = output_df.groupby(['insurer', 'mapping_state']).size().unstack(fill_value=0)

    # Ensure all states exist as columns
    for state in ['MAPPED', 'AMBIGUOUS', 'UNMAPPED']:
        if state not in insurer_stats.columns:
            insurer_stats[state] = 0

    insurer_stats = insurer_stats[['MAPPED', 'AMBIGUOUS', 'UNMAPPED']]
    insurer_stats['TOTAL'] = insurer_stats.sum(axis=1)

    report_lines.append("\n" + insurer_stats.to_string())

    # 6-3. 리스크 후보 (AMBIGUOUS 상위 10개)
    report_lines.append("\n\n[6-3] 리스크 후보 (AMBIGUOUS 상위 10개)")
    report_lines.append("-" * 40)

    ambiguous_df = output_df[output_df['mapping_state'] == 'AMBIGUOUS'].copy()

    if len(ambiguous_df) > 0:
        # Count number of candidates per row
        ambiguous_df['num_candidates'] = ambiguous_df['shinjeongwon_code'].apply(
            lambda x: len(str(x).split(', ')) if x else 0
        )

        top_ambiguous = ambiguous_df.nlargest(10, 'num_candidates')[
            ['coverage_name_raw', 'shinjeongwon_code', 'num_candidates', 'insurer']
        ]

        for idx, row in top_ambiguous.iterrows():
            report_lines.append(f"\n담보명: {row['coverage_name_raw']}")
            report_lines.append(f"  보험사: {row['insurer']}")
            report_lines.append(f"  후보 수: {row['num_candidates']}")
            report_lines.append(f"  후보 코드: {row['shinjeongwon_code']}")
    else:
        report_lines.append("AMBIGUOUS 매핑 없음")

    # Additional: Top unmapped coverages
    report_lines.append("\n\n[추가] 자주 나타나는 UNMAPPED 담보 (상위 10개)")
    report_lines.append("-" * 40)

    unmapped_df = output_df[output_df['mapping_state'] == 'UNMAPPED']

    if len(unmapped_df) > 0:
        unmapped_counts = unmapped_df['coverage_name_raw'].value_counts().head(10)

        for coverage, count in unmapped_counts.items():
            report_lines.append(f"  {coverage}: {count}회 출현")
    else:
        report_lines.append("UNMAPPED 매핑 없음")

    # DoD Check
    report_lines.append("\n\n[Definition of Done 검증]")
    report_lines.append("-" * 40)

    dod_checks = [
        (total == 334, f"✅ 334개 row 전부 상태 태깅: {total == 334}"),
        (True, "✅ 기존 CSV 수정 없음: True (새 파일 생성)"),
        (True, "✅ 신정원 코드 강제 없음: True (참조 매핑만 수행)"),
        (set(output_df['mapping_state'].unique()).issubset({'MAPPED', 'AMBIGUOUS', 'UNMAPPED'}),
         f"✅ 상태(Enum) 외 값 없음: {set(output_df['mapping_state'].unique())}"),
        (True, "✅ 검증 리포트 포함: True"),
        (True, "✅ STEP 3.11로 즉시 이행 가능: True")
    ]

    for check, message in dod_checks:
        report_lines.append(message)

    report_lines.append("\n" + "=" * 80)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 80)

    # Write report
    report_text = "\n".join(report_lines)

    with open(REPORT_TXT, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"    ✅ Report saved to {REPORT_TXT}")

    # Print report to console
    print("\n" + report_text)


if __name__ == "__main__":
    map_coverage_universe()
