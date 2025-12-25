#!/usr/bin/env python3
"""
STEP 3.10-γ: Excel Backlog Generator

Purpose:
- Generate Excel backlog for UNMAPPED coverages
- Per-insurer action lists (NO mapping changes)
- Mathematical prioritization (occurrence_count)
- Prepare for STEP 3.10-δ (Excel enhancement)

Rules:
✅ UNMAPPED → Backlog (no state change)
✅ Rule-based recommended_action (C1/C2/C6 → ADD, C3/C4/C7 → REVIEW)
✅ Mathematical priority (occurrence count DESC)
❌ No UNMAPPED → MAPPED conversion
❌ No inference/semantic judgment
❌ No Excel modification

Output:
1. Per-insurer backlog CSVs: data/step310_mapping/excel_backlog/backlog_{ins_cd}_{INSURER}.csv
2. Summary report: STEP310_GAMMA_EXCEL_BACKLOG_SUMMARY.md
"""

import pandas as pd
from pathlib import Path
from collections import Counter, defaultdict


class ExcelBacklogGenerator:
    """
    STEP 3.10-γ: Generate Excel backlog for UNMAPPED coverages
    """

    # Insurer code → name mapping
    INSURER_NAMES = {
        'N01': 'SAMSUNG',
        'N02': 'HANWHA',
        'N03': 'LOTTE',
        'N04': 'MERITZ',
        'N05': 'KB',
        'N06': 'HYUNDAI',
        'N07': 'HEUNGKUK',
        'N08': 'DB'
    }

    def __init__(self):
        """Initialize backlog generator"""
        self.mapping_csv = Path("data/step310_mapping/proposal_coverage_mapping_insurer_filtered.csv")
        self.cause_effect_csv = Path("data/step310_mapping/unmapped_cause_effect_report.csv")
        self.backlog_dir = Path("data/step310_mapping/excel_backlog")

        print("Excel Backlog Generator initialized (STEP 3.10-γ)")
        print(f"  Input CSV: {self.mapping_csv}")
        print(f"  Cause-Effect CSV: {self.cause_effect_csv}")
        print(f"  Output dir: {self.backlog_dir}")

    def generate(self):
        """
        Main generation entry point.

        Steps:
        1. Load UNMAPPED rows
        2. Aggregate by insurer + coverage_name
        3. Classify recommended_action
        4. Generate per-insurer backlog CSVs
        5. Generate summary MD report
        """
        print("\n" + "=" * 80)
        print("STEP 3.10-γ: Excel Backlog Generation")
        print("=" * 80)

        # Load UNMAPPED rows
        print("\n[1] Loading UNMAPPED rows...")
        mapping_df = pd.read_csv(self.mapping_csv, encoding='utf-8-sig')
        unmapped = mapping_df[mapping_df['mapping_status'] == 'UNMAPPED'].copy()
        print(f"  Total UNMAPPED rows: {len(unmapped)}")

        # Load cause-effect analysis
        print("\n[2] Loading cause-effect analysis...")
        cause_effect_df = pd.read_csv(self.cause_effect_csv, encoding='utf-8-sig')
        print(f"  Cause-effect rows: {len(cause_effect_df)}")

        # Aggregate by insurer + coverage_name
        print("\n[3] Aggregating by insurer + coverage_name...")
        backlog_items = self._aggregate_backlog(unmapped, cause_effect_df)
        print(f"  Unique backlog items: {len(backlog_items)}")

        # Generate per-insurer backlogs
        print("\n[4] Generating per-insurer backlog CSVs...")
        self._generate_per_insurer_backlogs(backlog_items)

        # Generate summary report
        print("\n[5] Generating summary MD report...")
        self._generate_summary_report(backlog_items)

        print("\n✅ Backlog generation complete")

    def _aggregate_backlog(self, unmapped_df, cause_effect_df):
        """
        Aggregate UNMAPPED rows into backlog items.

        Aggregation:
        - Group by insurer + coverage_name_raw
        - Count occurrences
        - Merge cause/effect codes
        - Calculate priority (occurrence_count DESC)

        Returns:
            List[dict] - Backlog items
        """
        # Merge with cause-effect
        merged = unmapped_df.merge(
            cause_effect_df,
            on=['insurer', 'coverage_name_raw'],
            how='left'
        )

        # Aggregate
        backlog = []

        for (insurer, coverage_name), group in merged.groupby(['insurer', 'coverage_name_raw']):
            occurrence_count = len(group)

            # Get first row's cause/effect (all rows in group should have same cause/effect)
            first_row = group.iloc[0]
            cause_codes = first_row.get('cause_codes', '')
            effect_codes = first_row.get('effect_codes', '')
            evidence_note = first_row.get('evidence_note', '')

            # Classify recommended_action
            recommended_action = self._classify_recommended_action(cause_codes)

            # Build notes
            notes = self._build_notes(cause_codes, evidence_note, occurrence_count)

            backlog.append({
                'ins_cd': self._get_ins_cd(insurer),
                'insurer_name': insurer,
                'coverage_name_raw': coverage_name,
                'occurrence_count': occurrence_count,
                'cause_codes': cause_codes,
                'effect_codes': effect_codes,
                'recommended_action': recommended_action,
                'notes': notes
            })

        # Sort by priority (occurrence_count DESC, coverage_name ASC)
        backlog.sort(key=lambda x: (-x['occurrence_count'], x['coverage_name_raw']))

        return backlog

    def _get_ins_cd(self, insurer_name: str) -> str:
        """
        Get ins_cd from insurer name.

        Returns:
            ins_cd (e.g., N01 for SAMSUNG)
        """
        for ins_cd, name in self.INSURER_NAMES.items():
            if name == insurer_name:
                return ins_cd
        return 'N99'  # Fallback

    def _classify_recommended_action(self, cause_codes: str) -> str:
        """
        Classify recommended_action based on cause codes.

        Rules (deterministic):
        - C1, C2, C6 포함 → ADD_EXCEL_ROW
        - C3, C4, C7 포함 → STRUCTURAL_REVIEW
        - 혼합 → ADD_EXCEL_ROW_WITH_NOTE

        Args:
            cause_codes: Pipe-separated cause codes (e.g., "C1_NO_EXCEL_ENTRY|C3_SUBCATEGORY_SPLIT")

        Returns:
            recommended_action
        """
        if not cause_codes:
            return 'ADD_EXCEL_ROW'

        causes = cause_codes.split('|')

        # Check for add-friendly causes
        add_causes = {'C1_NO_EXCEL_ENTRY', 'C2_NAME_VARIANT_ONLY', 'C6_TERMINOLOGY_MISMATCH'}
        has_add = any(c in add_causes for c in causes)

        # Check for structural causes
        structural_causes = {'C3_SUBCATEGORY_SPLIT', 'C4_COMPOSITE_COVERAGE', 'C7_POLICY_LEVEL_ONLY'}
        has_structural = any(c in structural_causes for c in causes)

        if has_structural and has_add:
            return 'ADD_EXCEL_ROW_WITH_NOTE'
        elif has_structural:
            return 'STRUCTURAL_REVIEW'
        else:
            return 'ADD_EXCEL_ROW'

    def _build_notes(self, cause_codes: str, evidence_note: str, occurrence_count: int) -> str:
        """
        Build notes for backlog item.

        Rules:
        - Fact-based only
        - NO inference ("추정", "유사", "의미상")
        """
        notes_parts = []

        # Occurrence
        notes_parts.append(f"가입설계서 {occurrence_count}회 출현")

        # Evidence
        if evidence_note:
            notes_parts.append(evidence_note)

        return "; ".join(notes_parts)

    def _generate_per_insurer_backlogs(self, backlog_items):
        """
        Generate per-insurer backlog CSVs.

        Output: data/step310_mapping/excel_backlog/backlog_{ins_cd}_{INSURER}.csv
        """
        # Create backlog directory
        self.backlog_dir.mkdir(parents=True, exist_ok=True)

        # Group by insurer
        by_insurer = defaultdict(list)
        for item in backlog_items:
            by_insurer[item['insurer_name']].append(item)

        # Generate CSV per insurer
        for insurer, items in by_insurer.items():
            ins_cd = items[0]['ins_cd']
            output_path = self.backlog_dir / f"backlog_{ins_cd}_{insurer}.csv"

            df = pd.DataFrame(items)
            df.to_csv(output_path, index=False, encoding='utf-8-sig')

            print(f"  ✅ {insurer}: {len(items)} items → {output_path.name}")

    def _generate_summary_report(self, backlog_items):
        """
        Generate summary MD report.

        Output: STEP310_GAMMA_EXCEL_BACKLOG_SUMMARY.md
        """
        output_path = Path("data/step310_mapping/STEP310_GAMMA_EXCEL_BACKLOG_SUMMARY.md")

        lines = []
        lines.append("# STEP 3.10-γ: Excel Backlog Summary")
        lines.append("")
        lines.append("**Generated by:** STEP 3.10-γ")
        lines.append(f"**Total Backlog Items:** {len(backlog_items)}")
        lines.append("")

        # Section 1: Per-insurer UNMAPPED totals
        lines.append("## 1. 보험사별 UNMAPPED 총량")
        lines.append("")

        by_insurer = defaultdict(list)
        for item in backlog_items:
            by_insurer[item['insurer_name']].append(item)

        lines.append("| Insurer | Backlog Items | Total Occurrences |")
        lines.append("|---------|---------------|-------------------|")
        for insurer in sorted(by_insurer.keys()):
            items = by_insurer[insurer]
            total_occurrences = sum(item['occurrence_count'] for item in items)
            lines.append(f"| {insurer} | {len(items)} | {total_occurrences} |")

        lines.append("")

        # Section 2: Per-insurer Top 10 backlog
        lines.append("## 2. 보험사별 Top 10 Backlog (우선순위 높음)")
        lines.append("")

        for insurer in sorted(by_insurer.keys()):
            items = by_insurer[insurer]
            lines.append(f"### {insurer}")
            lines.append("")
            lines.append("| Coverage Name | Occurrences | Action |")
            lines.append("|---------------|-------------|--------|")

            for item in items[:10]:
                lines.append(f"| {item['coverage_name_raw']} | {item['occurrence_count']} | {item['recommended_action']} |")

            lines.append("")

        # Section 3: Excel 보강 시 해소 가능한 담보 수
        lines.append("## 3. Excel 보강 시 해소 가능한 담보 수")
        lines.append("")

        add_items = [
            item for item in backlog_items
            if item['recommended_action'] in ['ADD_EXCEL_ROW', 'ADD_EXCEL_ROW_WITH_NOTE']
        ]

        lines.append(f"**Total:** {len(add_items)} items")
        lines.append("")

        lines.append("| Action | Count |")
        lines.append("|--------|-------|")
        action_counter = Counter(item['recommended_action'] for item in add_items)
        for action, count in action_counter.most_common():
            lines.append(f"| {action} | {count} |")

        lines.append("")

        # Section 4: 구조적으로 매핑 부적합 담보 목록
        lines.append("## 4. 구조적으로 매핑 부적합 담보 목록")
        lines.append("")

        structural_items = [
            item for item in backlog_items
            if item['recommended_action'] == 'STRUCTURAL_REVIEW'
        ]

        lines.append(f"**Total:** {len(structural_items)} items")
        lines.append("")

        lines.append("| Insurer | Coverage | Cause |")
        lines.append("|---------|----------|-------|")
        for item in structural_items[:20]:
            lines.append(f"| {item['insurer_name']} | {item['coverage_name_raw']} | {item['cause_codes']} |")

        lines.append("")

        # Section 5: 예상 효과 (정량)
        lines.append("## 5. 예상 효과 (정량)")
        lines.append("")

        total_items = len(backlog_items)
        add_count = len(add_items)
        structural_count = len(structural_items)

        lines.append("**현재 상태 (STEP 3.10-2 기준):**")
        lines.append(f"- Total UNMAPPED: 191 rows")
        lines.append(f"- Unique coverage items: {total_items}")
        lines.append("")

        lines.append("**Excel 보강 후 예상 효과:**")
        lines.append(f"- ADD_EXCEL_ROW 완료 시: {add_count} items → MAPPED 전환 가능")
        lines.append(f"- STRUCTURAL_REVIEW 필요: {structural_count} items (별도 전략 필요)")
        lines.append("")

        lines.append("**비율 예상:**")
        if total_items > 0:
            add_ratio = (add_count / total_items) * 100
            lines.append(f"- Excel 보강만으로 해소 가능: {add_ratio:.1f}%")

        lines.append("")

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"  ✅ Summary report saved: {output_path}")


def main():
    """Main entry point"""
    generator = ExcelBacklogGenerator()
    generator.generate()


if __name__ == "__main__":
    main()
