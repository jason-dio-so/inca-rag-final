#!/usr/bin/env python3
"""
STEP 3.10-β: UNMAPPED Cause-Effect Analysis

Purpose:
- Analyze WHY coverage is UNMAPPED (cause)
- Document system impact (effect)
- Generate fact-based reports (NO recommendations)

Rules:
✅ Fact-based cause classification (7 fixed Enum codes)
✅ Effect classification (5 fixed codes)
✅ Evidence-based notes only
❌ No mapping rule changes
❌ No UNMAPPED → MAPPED conversion
❌ No coverage unification/inference
❌ No recommendations

Output:
1. CSV report: unmapped_cause_effect_report.csv
2. MD summary: UNMAPPED_CAUSE_EFFECT_SUMMARY.md
"""

import pandas as pd
import re
from pathlib import Path
from collections import Counter
from typing import List, Tuple


class UnmappedCauseEffectAnalyzer:
    """
    STEP 3.10-β: Analyze UNMAPPED causes and effects
    """

    # Cause codes (fixed Enum)
    CAUSE_CODES = {
        'C1_NO_EXCEL_ENTRY': 'Excel에 해당 보험사 매핑 행 없음',
        'C2_NAME_VARIANT_ONLY': '타 보험사에는 존재하나 현재 보험사 ins_cd 매핑 없음',
        'C3_SUBCATEGORY_SPLIT': '가입설계서는 하위 담보, Excel은 상위 개념만',
        'C4_COMPOSITE_COVERAGE': '가입설계서는 단일 담보, Excel은 복합 담보만',
        'C5_NEW_OR_SPECIAL_COVERAGE': 'Excel에 아직 정의되지 않은 신규/특수 담보',
        'C6_TERMINOLOGY_MISMATCH': '공백/조사/접두어 차이로 결정론적 매칭 불가',
        'C7_POLICY_LEVEL_ONLY': '가입설계서 요약표에는 있으나 Excel은 약관 단위만'
    }

    # Effect codes (fixed Enum)
    EFFECT_CODES = {
        'E1_COMPARISON_POSSIBLE': 'PRIME 비교 가능 (in_universe_unmapped)',
        'E2_LIMITED_COMPARISON': '다건 후보/축 누락으로 제한적 비교',
        'E3_EXPLANATION_REQUIRED': '고객 응답 시 설명 레이어 필수',
        'E4_MAPPING_EXPANSION_CANDIDATE': 'Excel 보강 시 MAPPED 가능성 높음',
        'E5_STRUCTURAL_DIFFERENCE': '구조적 차이로 매핑 자체 부적합'
    }

    def __init__(self):
        """Initialize analyzer"""
        self.mapping_csv = Path("data/step310_mapping/proposal_coverage_mapping_insurer_filtered.csv")
        self.excel_file = Path("data/담보명mapping자료__inscd_patched.xlsx")  # STEP 3.10-ζ patched version

        print("UNMAPPED Cause-Effect Analyzer initialized (STEP 3.10-β)")
        print(f"  Input CSV: {self.mapping_csv}")
        print(f"  Excel reference: {self.excel_file}")

    def analyze(self):
        """
        Main analysis entry point.

        Steps:
        1. Load UNMAPPED rows (191)
        2. Classify causes (C1-C7)
        3. Classify effects (E1-E5)
        4. Generate CSV report
        5. Generate MD summary
        """
        print("\n" + "=" * 80)
        print("STEP 3.10-β: UNMAPPED Cause-Effect Analysis")
        print("=" * 80)

        # Load UNMAPPED rows
        print("\n[1] Loading UNMAPPED rows...")
        df = pd.read_csv(self.mapping_csv, encoding='utf-8-sig')
        unmapped = df[df['mapping_status'] == 'UNMAPPED'].copy()

        print(f"  Total UNMAPPED rows: {len(unmapped)}")

        # Load Excel for reference
        print("\n[2] Loading Excel mapping reference...")
        excel_df = pd.read_excel(self.excel_file, sheet_name=0)
        print(f"  Excel rows: {len(excel_df)}")

        # Analyze each UNMAPPED row
        print("\n[3] Classifying causes and effects...")
        results = []

        for idx, row in unmapped.iterrows():
            insurer = row['insurer']
            coverage_name = row['coverage_name_raw']
            mapping_basis = row.get('mapping_basis', '')

            # Classify cause
            cause_codes, cause_evidence = self._classify_cause(
                insurer, coverage_name, mapping_basis, excel_df
            )

            # Classify effect
            effect_codes = self._classify_effect(cause_codes, coverage_name)

            results.append({
                'insurer': insurer,
                'coverage_name_raw': coverage_name,
                'cause_codes': '|'.join(cause_codes),
                'effect_codes': '|'.join(effect_codes),
                'evidence_note': cause_evidence
            })

        results_df = pd.DataFrame(results)

        print(f"  Analyzed {len(results_df)} UNMAPPED rows")

        # Generate reports
        print("\n[4] Generating CSV report...")
        self._generate_csv_report(results_df)

        print("\n[5] Generating MD summary...")
        self._generate_md_summary(results_df)

        print("\n✅ Analysis complete")

    def _classify_cause(
        self,
        insurer: str,
        coverage_name: str,
        mapping_basis: str,
        excel_df: pd.DataFrame
    ) -> Tuple[List[str], str]:
        """
        Classify cause for UNMAPPED coverage.

        Returns:
            (cause_codes, evidence_note)
        """
        causes = []
        evidence = []

        # C1: NO_EXCEL_ENTRY (check mapping_basis)
        if 'no entry' in mapping_basis.lower():
            causes.append('C1_NO_EXCEL_ENTRY')
            evidence.append(f"Excel {mapping_basis}")

        # C3: SUBCATEGORY_SPLIT (하위 담보 분리)
        subcategory_keywords = ['제자리암', '경계성종양', '기타피부암', '갑상선암']
        if any(kw in coverage_name for kw in subcategory_keywords):
            causes.append('C3_SUBCATEGORY_SPLIT')
            evidence.append(f"하위 담보: {coverage_name}")

        # C4: COMPOSITE_COVERAGE (복합 담보)
        composite_keywords = ['4대유사암', '3대진단비', '5종']
        if any(kw in coverage_name for kw in composite_keywords):
            causes.append('C4_COMPOSITE_COVERAGE')
            evidence.append(f"복합 담보: {coverage_name}")

        # C5: NEW_OR_SPECIAL_COVERAGE (신규/특수 담보)
        special_keywords = ['고액치료비', '특정', '신규', '특별']
        if any(kw in coverage_name for kw in special_keywords):
            causes.append('C5_NEW_OR_SPECIAL_COVERAGE')
            evidence.append(f"특수 담보: {coverage_name}")

        # C6: TERMINOLOGY_MISMATCH (공백/접두어 차이)
        if not causes:  # Fallback for simple naming mismatches
            # Check if similar name exists in Excel for other insurers
            # (This is a simplified check - production would need more sophisticated logic)
            normalized_name = self._normalize_coverage_name(coverage_name)

            # Check if any Excel row has similar normalized name
            excel_has_similar = False
            for _, excel_row in excel_df.iterrows():
                excel_coverage = str(excel_row.get('담보명(가입설계서)', ''))
                if excel_coverage and self._normalize_coverage_name(excel_coverage) == normalized_name:
                    excel_has_similar = True
                    break

            if excel_has_similar:
                causes.append('C2_NAME_VARIANT_ONLY')
                evidence.append(f"타 보험사에 유사명 존재")
            else:
                causes.append('C6_TERMINOLOGY_MISMATCH')
                evidence.append(f"표기 차이: {coverage_name}")

        # Default: C1 if no other causes found
        if not causes:
            causes.append('C1_NO_EXCEL_ENTRY')
            evidence.append("매핑 근거 없음")

        evidence_note = "; ".join(evidence)
        return causes, evidence_note

    def _classify_effect(self, cause_codes: List[str], coverage_name: str) -> List[str]:
        """
        Classify effect for UNMAPPED coverage.

        Args:
            cause_codes: Classified cause codes
            coverage_name: Coverage name

        Returns:
            List of effect codes
        """
        effects = []

        # E1: Always possible (in_universe_unmapped)
        effects.append('E1_COMPARISON_POSSIBLE')

        # E3: Explanation always required for UNMAPPED
        effects.append('E3_EXPLANATION_REQUIRED')

        # E4: Mapping expansion candidate (if C1, C2, C6)
        if any(c in cause_codes for c in ['C1_NO_EXCEL_ENTRY', 'C2_NAME_VARIANT_ONLY', 'C6_TERMINOLOGY_MISMATCH']):
            effects.append('E4_MAPPING_EXPANSION_CANDIDATE')

        # E5: Structural difference (if C3, C4, C7)
        if any(c in cause_codes for c in ['C3_SUBCATEGORY_SPLIT', 'C4_COMPOSITE_COVERAGE', 'C7_POLICY_LEVEL_ONLY']):
            effects.append('E5_STRUCTURAL_DIFFERENCE')

        return effects

    def _normalize_coverage_name(self, name: str) -> str:
        """
        Normalize coverage name for comparison.

        Rules:
        - Strip whitespace
        - Collapse multiple spaces
        - Remove common particles (의, 을, 를, 에)
        """
        normalized = name.strip()
        normalized = re.sub(r'\s+', '', normalized)  # Remove all whitespace
        normalized = normalized.replace('의', '').replace('을', '').replace('를', '').replace('에', '')
        return normalized.lower()

    def _generate_csv_report(self, results_df: pd.DataFrame):
        """
        Generate CSV report.

        Output: data/step310_mapping/unmapped_cause_effect_report.csv
        """
        output_path = Path("data/step310_mapping/unmapped_cause_effect_report.csv")
        results_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"  ✅ CSV report saved: {output_path}")

    def _generate_md_summary(self, results_df: pd.DataFrame):
        """
        Generate MD summary report.

        Output: data/step310_mapping/UNMAPPED_CAUSE_EFFECT_SUMMARY.md
        """
        output_path = Path("data/step310_mapping/UNMAPPED_CAUSE_EFFECT_SUMMARY.md")

        lines = []
        lines.append("# UNMAPPED Cause-Effect Analysis Summary")
        lines.append("")
        lines.append("**Generated by:** STEP 3.10-β")
        lines.append(f"**Total UNMAPPED:** {len(results_df)}")
        lines.append("")

        # Section 1: Overall cause statistics
        lines.append("## 1. 전체 UNMAPPED 통계 (원인별 비중)")
        lines.append("")

        # Count causes (split by | if multiple)
        cause_counter = Counter()
        for causes_str in results_df['cause_codes']:
            for cause in causes_str.split('|'):
                cause_counter[cause] += 1

        lines.append("| Cause Code | Count | Percentage |")
        lines.append("|------------|-------|------------|")
        for cause, count in cause_counter.most_common():
            percentage = (count / len(results_df)) * 100
            cause_desc = self.CAUSE_CODES.get(cause, cause)
            lines.append(f"| {cause} | {count} | {percentage:.1f}% |")
            lines.append(f"| {cause_desc} | | |")

        lines.append("")

        # Section 2: Top causes by insurer
        lines.append("## 2. 보험사별 Top Cause")
        lines.append("")

        for insurer in sorted(results_df['insurer'].unique()):
            insurer_df = results_df[results_df['insurer'] == insurer]
            insurer_causes = Counter()
            for causes_str in insurer_df['cause_codes']:
                for cause in causes_str.split('|'):
                    insurer_causes[cause] += 1

            if insurer_causes:
                top_cause = insurer_causes.most_common(1)[0]
                lines.append(f"- **{insurer}**: {top_cause[0]} ({top_cause[1]} cases)")

        lines.append("")

        # Section 3: Frequent coverage names
        lines.append("## 3. 자주 반복되는 담보명 Top 10")
        lines.append("")

        coverage_counter = Counter(results_df['coverage_name_raw'])

        lines.append("| Coverage Name | Count |")
        lines.append("|---------------|-------|")
        for coverage, count in coverage_counter.most_common(10):
            lines.append(f"| {coverage} | {count} |")

        lines.append("")

        # Section 4: Mapping expansion candidates
        lines.append("## 4. Excel 보강 시 해소 가능 담보군")
        lines.append("")

        expansion_candidates = results_df[
            results_df['effect_codes'].str.contains('E4_MAPPING_EXPANSION_CANDIDATE')
        ]

        lines.append(f"**Total:** {len(expansion_candidates)} cases")
        lines.append("")

        lines.append("| Insurer | Coverage | Cause |")
        lines.append("|---------|----------|-------|")
        for _, row in expansion_candidates.head(20).iterrows():
            lines.append(f"| {row['insurer']} | {row['coverage_name_raw']} | {row['cause_codes']} |")

        lines.append("")

        # Section 5: Structural differences
        lines.append("## 5. 구조적으로 통합 불가 담보군")
        lines.append("")

        structural_diff = results_df[
            results_df['effect_codes'].str.contains('E5_STRUCTURAL_DIFFERENCE')
        ]

        lines.append(f"**Total:** {len(structural_diff)} cases")
        lines.append("")

        lines.append("| Insurer | Coverage | Cause |")
        lines.append("|---------|----------|-------|")
        for _, row in structural_diff.head(20).iterrows():
            lines.append(f"| {row['insurer']} | {row['coverage_name_raw']} | {row['cause_codes']} |")

        lines.append("")

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"  ✅ MD summary saved: {output_path}")


def main():
    """Main entry point"""
    analyzer = UnmappedCauseEffectAnalyzer()
    analyzer.analyze()


if __name__ == "__main__":
    main()
