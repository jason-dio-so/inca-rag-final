#!/usr/bin/env python3
"""
STEP 3.10-ε: ins_cd Consistency Audit

Purpose:
- Cross-validate ins_cd consistency across Excel/Pipeline/Proposal
- Detect mismatches, collisions, missing mappings
- Generate audit reports (NO fixes)

Rules:
✅ 3-way cross-validation (Excel/Pipeline/Proposal)
✅ 7 fixed issue codes (I1-I7)
✅ Audit reports only (no modifications)
❌ No Excel/code modifications
❌ No ins_cd inference/auto-correction

Output:
1. CSV: data/step310_mapping/ins_cd_audit/ins_cd_audit_table.csv
2. MD: data/step310_mapping/ins_cd_audit/INSCD_AUDIT_REPORT.md
3. JSON: data/step310_mapping/ins_cd_audit/ins_cd_audit_findings.json
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple


class InsCdAuditor:
    """
    STEP 3.10-ε: ins_cd Consistency Auditor
    """

    # Issue codes (fixed Enum)
    ISSUE_CODES = {
        'I1_PIPELINE_INSCD_MISSING': '파이프라인에 ins_cd 매핑 없음',
        'I2_EXCEL_INSCD_MISSING': 'Excel에 해당 보험사 매핑 행 없음',
        'I3_MISMATCH_PIPELINE_VS_EXCEL': '파이프라인 ins_cd와 Excel ins_cd 불일치',
        'I4_COLLISION_EXCEL_INSCD_MULTI_COMPANY': 'Excel에서 하나의 ins_cd가 여러 보험사명 사용',
        'I5_COLLISION_PIPELINE_INSCD_MULTI_INSURER': '파이프라인에서 하나의 ins_cd가 여러 insurer 할당',
        'I6_PROPOSAL_INSURER_MISSING': 'Proposal Universe에 insurer 없음',
        'I7_NAME_ALIAS_REQUIRED': '보험사명/코드 alias 테이블 없어서 자동 매칭 불가'
    }

    # Pipeline registry (from step310_gamma_excel_backlog.py)
    PIPELINE_INSURER_NAMES = {
        'N01': 'SAMSUNG',
        'N02': 'HANWHA',
        'N03': 'LOTTE',
        'N04': 'MERITZ',
        'N05': 'KB',
        'N06': 'HYUNDAI',
        'N07': 'HEUNGKUK',
        'N08': 'DB'
    }

    # Company name aliases (for Excel matching)
    # This is deterministic mapping only (no inference)
    COMPANY_NAME_ALIASES = {
        'SAMSUNG': ['삼성', '삼성화재'],
        'HANWHA': ['한화', '한화생명'],
        'LOTTE': ['롯데', '롯데손해보험'],
        'MERITZ': ['메리츠', '메리츠화재'],
        'KB': ['KB', 'KB손해보험'],
        'HYUNDAI': ['현대', '현대해상'],
        'HEUNGKUK': ['흥국', '흥국화재'],
        'DB': ['DB', 'DB손해보험']
    }

    def __init__(self):
        """Initialize auditor"""
        self.excel_path = Path("data/담보명mapping자료.xlsx")
        self.proposal_path = Path("data/step39_coverage_universe/extracts/ALL_INSURERS_coverage_universe.csv")
        self.audit_dir = Path("data/step310_mapping/ins_cd_audit")

        print("ins_cd Consistency Auditor initialized (STEP 3.10-ε)")
        print(f"  Excel: {self.excel_path}")
        print(f"  Proposal: {self.proposal_path}")
        print(f"  Audit dir: {self.audit_dir}")

    def audit(self):
        """
        Main audit entry point.

        Steps:
        1. Collect Excel ins_cd mappings
        2. Collect Pipeline ins_cd mappings
        3. Collect Proposal insurers
        4. Cross-validate (3-way)
        5. Classify issues (I1-I7)
        6. Generate reports (CSV/MD/JSON)
        """
        print("\n" + "=" * 80)
        print("STEP 3.10-ε: ins_cd Consistency Audit")
        print("=" * 80)

        # Step 1: Collect Excel data
        print("\n[1] Collecting Excel ins_cd mappings...")
        excel_data = self._collect_excel_data()

        # Step 2: Collect Pipeline data
        print("\n[2] Collecting Pipeline ins_cd mappings...")
        pipeline_data = self._collect_pipeline_data()

        # Step 3: Collect Proposal data
        print("\n[3] Collecting Proposal insurers...")
        proposal_data = self._collect_proposal_data()

        # Step 4: Cross-validate
        print("\n[4] Performing 3-way cross-validation...")
        audit_results = self._cross_validate(excel_data, pipeline_data, proposal_data)

        # Step 5: Generate reports
        print("\n[5] Generating audit reports...")
        self._generate_reports(audit_results)

        print("\n✅ Audit complete")

    def _collect_excel_data(self) -> Dict:
        """
        Collect Excel ins_cd data.

        Returns:
            Dict with:
            - company_to_inscd: {company_name: set(ins_cd)}
            - inscd_to_companies: {ins_cd: set(company_name)}
            - inscd_counts: {ins_cd: row_count}
        """
        df = pd.read_excel(self.excel_path, sheet_name=0)

        company_to_inscd = defaultdict(set)
        inscd_to_companies = defaultdict(set)
        inscd_counts = Counter()

        for _, row in df.iterrows():
            company_name = str(row.get('보험사명', '')).strip()
            ins_cd = str(row.get('ins_cd', '')).strip()

            if company_name and ins_cd:
                company_to_inscd[company_name].add(ins_cd)
                inscd_to_companies[ins_cd].add(company_name)
                inscd_counts[ins_cd] += 1

        print(f"  Excel companies found: {len(company_to_inscd)}")
        print(f"  Excel ins_cd values: {sorted(inscd_counts.keys())}")

        return {
            'company_to_inscd': dict(company_to_inscd),
            'inscd_to_companies': dict(inscd_to_companies),
            'inscd_counts': dict(inscd_counts)
        }

    def _collect_pipeline_data(self) -> Dict:
        """
        Collect Pipeline ins_cd mappings.

        Returns:
            Dict with:
            - insurer_to_inscd: {INSURER: ins_cd}
            - inscd_to_insurers: {ins_cd: set(INSURER)}
        """
        insurer_to_inscd = {
            insurer: ins_cd
            for ins_cd, insurer in self.PIPELINE_INSURER_NAMES.items()
        }

        inscd_to_insurers = defaultdict(set)
        for insurer, ins_cd in insurer_to_inscd.items():
            inscd_to_insurers[ins_cd].add(insurer)

        print(f"  Pipeline insurers: {len(insurer_to_inscd)}")
        print(f"  Pipeline ins_cd values: {sorted(set(insurer_to_inscd.values()))}")

        return {
            'insurer_to_inscd': insurer_to_inscd,
            'inscd_to_insurers': dict(inscd_to_insurers)
        }

    def _collect_proposal_data(self) -> Dict:
        """
        Collect Proposal Universe insurers.

        Returns:
            Dict with:
            - insurers: set(insurer)
            - insurer_counts: {insurer: row_count}
        """
        df = pd.read_csv(self.proposal_path, encoding='utf-8-sig')

        insurer_counts = Counter(df['insurer'])

        print(f"  Proposal insurers: {sorted(insurer_counts.keys())}")
        print(f"  Total proposal rows: {len(df)}")

        return {
            'insurers': set(insurer_counts.keys()),
            'insurer_counts': dict(insurer_counts)
        }

    def _cross_validate(
        self,
        excel_data: Dict,
        pipeline_data: Dict,
        proposal_data: Dict
    ) -> List[Dict]:
        """
        Perform 3-way cross-validation.

        For each insurer in pipeline:
        1. Check if pipeline has ins_cd
        2. Check if Excel has matching ins_cd
        3. Check if Proposal has insurer
        4. Detect mismatches/collisions

        Returns:
            List of audit result dicts
        """
        results = []

        # Get all insurers from pipeline
        all_insurers = set(pipeline_data['insurer_to_inscd'].keys())

        for insurer in sorted(all_insurers):
            result = self._audit_single_insurer(
                insurer,
                excel_data,
                pipeline_data,
                proposal_data
            )
            results.append(result)

        return results

    def _audit_single_insurer(
        self,
        insurer: str,
        excel_data: Dict,
        pipeline_data: Dict,
        proposal_data: Dict
    ) -> Dict:
        """
        Audit single insurer.

        Returns:
            Audit result dict
        """
        issues = []
        notes = []

        # Pipeline ins_cd
        pipeline_ins_cd = pipeline_data['insurer_to_inscd'].get(insurer)

        if not pipeline_ins_cd:
            issues.append('I1_PIPELINE_INSCD_MISSING')
            notes.append(f"Pipeline has no ins_cd for {insurer}")

        # Excel matching
        excel_company_names = self._find_excel_company_names(insurer)
        excel_ins_cd_set = set()

        for company_name in excel_company_names:
            excel_ins_cd_set.update(excel_data['company_to_inscd'].get(company_name, set()))

        if not excel_ins_cd_set:
            issues.append('I2_EXCEL_INSCD_MISSING')
            notes.append(f"Excel has no ins_cd for {insurer} (aliases: {excel_company_names})")

        # Mismatch detection
        if pipeline_ins_cd and excel_ins_cd_set:
            if pipeline_ins_cd not in excel_ins_cd_set:
                issues.append('I3_MISMATCH_PIPELINE_VS_EXCEL')
                notes.append(f"Pipeline: {pipeline_ins_cd}, Excel: {excel_ins_cd_set}")

        # Collision detection (Excel)
        for ins_cd in excel_ins_cd_set:
            companies = excel_data['inscd_to_companies'].get(ins_cd, set())
            if len(companies) > 1:
                issues.append('I4_COLLISION_EXCEL_INSCD_MULTI_COMPANY')
                notes.append(f"Excel ins_cd={ins_cd} used by: {companies}")

        # Collision detection (Pipeline)
        if pipeline_ins_cd:
            pipeline_insurers = pipeline_data['inscd_to_insurers'].get(pipeline_ins_cd, set())
            if len(pipeline_insurers) > 1:
                issues.append('I5_COLLISION_PIPELINE_INSCD_MULTI_INSURER')
                notes.append(f"Pipeline ins_cd={pipeline_ins_cd} used by: {pipeline_insurers}")

        # Proposal existence
        proposal_rows = proposal_data['insurer_counts'].get(insurer, 0)

        if insurer not in proposal_data['insurers']:
            issues.append('I6_PROPOSAL_INSURER_MISSING')
            notes.append(f"Proposal Universe has no rows for {insurer}")

        # Recommended fix target
        recommended_fix = self._recommend_fix_target(issues)

        return {
            'insurer': insurer,
            'pipeline_ins_cd': pipeline_ins_cd or 'NULL',
            'excel_company_names_found': '|'.join(sorted(excel_company_names)) if excel_company_names else 'NULL',
            'excel_ins_cd_set': '|'.join(sorted(excel_ins_cd_set)) if excel_ins_cd_set else 'NULL',
            'proposal_rows': proposal_rows,
            'issue_codes': '|'.join(sorted(set(issues))) if issues else 'NONE',
            'recommended_fix_target': recommended_fix,
            'notes': '; '.join(notes) if notes else 'OK'
        }

    def _find_excel_company_names(self, insurer: str) -> Set[str]:
        """
        Find Excel company names for insurer using COMPANY_NAME_ALIASES.

        Args:
            insurer: Pipeline insurer code (e.g., HEUNGKUK)

        Returns:
            Set of Excel company names
        """
        aliases = self.COMPANY_NAME_ALIASES.get(insurer, [])
        return set(aliases)

    def _recommend_fix_target(self, issues: List[str]) -> str:
        """
        Recommend fix target based on issues.

        Rules:
        - I3 → EXCEL (usually Excel needs correction)
        - I4 → EXCEL
        - I5 → PIPELINE
        - I1, I2, I6 → ALIAS_TABLE or PROPOSAL_DATA
        - No issues → NONE
        """
        if not issues:
            return 'NONE'

        if 'I3_MISMATCH_PIPELINE_VS_EXCEL' in issues:
            return 'EXCEL'
        if 'I4_COLLISION_EXCEL_INSCD_MULTI_COMPANY' in issues:
            return 'EXCEL'
        if 'I5_COLLISION_PIPELINE_INSCD_MULTI_INSURER' in issues:
            return 'PIPELINE'
        if 'I1_PIPELINE_INSCD_MISSING' in issues:
            return 'PIPELINE'
        if 'I2_EXCEL_INSCD_MISSING' in issues:
            return 'ALIAS_TABLE'
        if 'I6_PROPOSAL_INSURER_MISSING' in issues:
            return 'PROPOSAL_DATA'

        return 'REVIEW'

    def _generate_reports(self, audit_results: List[Dict]):
        """
        Generate audit reports (CSV/MD/JSON).

        Outputs:
        1. CSV: ins_cd_audit_table.csv
        2. MD: INSCD_AUDIT_REPORT.md
        3. JSON: ins_cd_audit_findings.json
        """
        # Create audit directory
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        # Generate CSV
        self._generate_csv(audit_results)

        # Generate MD
        self._generate_md(audit_results)

        # Generate JSON
        self._generate_json(audit_results)

    def _generate_csv(self, audit_results: List[Dict]):
        """Generate CSV report"""
        output_path = self.audit_dir / "ins_cd_audit_table.csv"

        df = pd.DataFrame(audit_results)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

        print(f"  ✅ CSV: {output_path}")

    def _generate_md(self, audit_results: List[Dict]):
        """Generate MD report"""
        output_path = self.audit_dir / "INSCD_AUDIT_REPORT.md"

        lines = []
        lines.append("# STEP 3.10-ε: ins_cd Consistency Audit Report")
        lines.append("")
        lines.append("**Generated by:** STEP 3.10-ε")
        lines.append("")

        # Summary
        total_insurers = len(audit_results)
        insurers_with_issues = sum(1 for r in audit_results if r['issue_codes'] != 'NONE')
        insurers_ok = total_insurers - insurers_with_issues

        lines.append("## 1. 전체 요약")
        lines.append("")
        lines.append(f"- **Total insurers audited**: {total_insurers}")
        lines.append(f"- **Insurers OK**: {insurers_ok}")
        lines.append(f"- **Insurers with issues**: {insurers_with_issues}")
        lines.append("")

        # Issue type breakdown
        lines.append("## 2. 이슈 유형별 카운트")
        lines.append("")

        issue_counter = Counter()
        for result in audit_results:
            if result['issue_codes'] != 'NONE':
                for issue in result['issue_codes'].split('|'):
                    issue_counter[issue] += 1

        lines.append("| Issue Code | Count | Description |")
        lines.append("|------------|-------|-------------|")
        for issue, count in issue_counter.most_common():
            desc = self.ISSUE_CODES.get(issue, issue)
            lines.append(f"| {issue} | {count} | {desc} |")

        lines.append("")

        # Top 5 critical issues
        lines.append("## 3. 가장 위험한 Top 5 (collision, mismatch 우선)")
        lines.append("")

        critical_issues = [
            r for r in audit_results
            if any(code in r['issue_codes'] for code in ['I3', 'I4', 'I5'])
        ]

        lines.append("| Insurer | Pipeline ins_cd | Excel ins_cd | Issue Codes | Recommended Fix |")
        lines.append("|---------|-----------------|--------------|-------------|-----------------|")
        for result in critical_issues[:5]:
            lines.append(f"| {result['insurer']} | {result['pipeline_ins_cd']} | {result['excel_ins_cd_set']} | {result['issue_codes']} | {result['recommended_fix_target']} |")

        lines.append("")

        # Full results
        lines.append("## 4. 전체 감사 결과")
        lines.append("")

        lines.append("| Insurer | Pipeline | Excel ins_cd | Proposal Rows | Issues | Fix Target |")
        lines.append("|---------|----------|--------------|---------------|--------|------------|")
        for result in audit_results:
            lines.append(f"| {result['insurer']} | {result['pipeline_ins_cd']} | {result['excel_ins_cd_set']} | {result['proposal_rows']} | {result['issue_codes']} | {result['recommended_fix_target']} |")

        lines.append("")

        # Next steps
        lines.append("## 5. 다음 단계 권장사항")
        lines.append("")
        lines.append("**이 감사는 리포트만 생성하며, 수정은 수행하지 않습니다.**")
        lines.append("")
        lines.append("권장 조치:")
        lines.append("")
        lines.append("1. **EXCEL 수정 대상**: recommended_fix_target = EXCEL인 항목")
        lines.append("   - Excel 담보명mapping자료.xlsx의 ins_cd 값 정정")
        lines.append("")
        lines.append("2. **PIPELINE 수정 대상**: recommended_fix_target = PIPELINE인 항목")
        lines.append("   - 파이프라인 INSURER_NAMES 레지스트리 정정")
        lines.append("")
        lines.append("3. **ALIAS_TABLE 추가 대상**: recommended_fix_target = ALIAS_TABLE인 항목")
        lines.append("   - 보험사명 동의어 매핑 테이블 보강")
        lines.append("")

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"  ✅ MD: {output_path}")

    def _generate_json(self, audit_results: List[Dict]):
        """Generate JSON report"""
        output_path = self.audit_dir / "ins_cd_audit_findings.json"

        findings = {
            'audit_timestamp': '2025-12-25',
            'total_insurers': len(audit_results),
            'results': audit_results
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(findings, f, indent=2, ensure_ascii=False)

        print(f"  ✅ JSON: {output_path}")


def main():
    """Main entry point"""
    auditor = InsCdAuditor()
    auditor.audit()


if __name__ == "__main__":
    main()
