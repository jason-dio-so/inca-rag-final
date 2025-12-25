#!/usr/bin/env python3
"""
STEP 3.11: Coverage Comparison Engine (Proposal-Based)

Constitution Principles:
1. Proposal = SSOT (Single Source of Truth)
2. Comparison unit = "proposal coverage row"
3. Shinjeongwon code = reference key (NOT primary key)
4. UNMAPPED ≠ non-comparable
5. AMBIGUOUS is already eliminated (insurer-filtered version)
6. All results must include evidence (row_id, coverage_name_raw)

Hard Bans:
❌ No filtering by Shinjeongwon code
❌ No coverage unification
❌ No recommendation generation
❌ No policy/summary reference
❌ No premium API calls
"""

import pandas as pd
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

# Paths
BASE_DIR = Path(__file__).parent.parent
UNIVERSE_CSV = BASE_DIR / "data/step39_coverage_universe/extracts/ALL_INSURERS_coverage_universe.csv"
MAPPING_CSV = BASE_DIR / "data/step310_mapping/proposal_coverage_mapping_insurer_filtered.csv"


class ComparisonState(Enum):
    """Comparison state for coverage grouping"""
    COMPARABLE = "COMPARABLE"  # Same Shinjeongwon code + MAPPED
    COMPARABLE_WITH_GAPS = "COMPARABLE_WITH_GAPS"  # Similar name + UNMAPPED
    NON_COMPARABLE = "NON_COMPARABLE"  # Coverage nature clearly different
    NOT_FOUND = "NOT_FOUND"  # Coverage not in proposal


@dataclass
class CoverageCandidate:
    """Single coverage candidate from one insurer"""
    insurer: str
    row_id: str
    coverage_name_raw: str
    amount_raw: str
    premium_raw: str
    pay_term_raw: str
    maturity_raw: str
    mapping_status: str  # MAPPED | UNMAPPED
    shinjeongwon_code: Optional[str]
    match_score: float  # String similarity score


@dataclass
class ComparisonResult:
    """Final comparison result"""
    comparison_table: pd.DataFrame
    comparability_judgment: str
    limitation_reasons: List[str]
    evidence_block: str


class CoverageComparisonEngine:
    """
    Proposal-based coverage comparison engine.

    STEP 3.11 FINAL implementation.
    """

    def __init__(self):
        """Load data sources"""
        self.universe_df = pd.read_csv(UNIVERSE_CSV)
        self.mapping_df = pd.read_csv(MAPPING_CSV)

        print("Coverage Comparison Engine initialized")
        print(f"  Universe rows: {len(self.universe_df)}")
        print(f"  Mapping rows: {len(self.mapping_df)}")

    def compare(self, insurers: List[str], coverage_query: str) -> ComparisonResult:
        """
        Main comparison entry point.

        Args:
            insurers: List of insurer names (e.g., ['SAMSUNG', 'KB'])
            coverage_query: Coverage query in natural language (e.g., '뇌졸중 진단비')

        Returns:
            ComparisonResult with table, judgment, and evidence
        """
        print("=" * 80)
        print("STEP 3.11: Coverage Comparison")
        print("=" * 80)
        print(f"Insurers: {insurers}")
        print(f"Query: {coverage_query}")

        # Step 1: Resolve coverage candidates per insurer
        print("\n[1] Resolving coverage candidates...")
        candidates_by_insurer = {}

        for insurer in insurers:
            candidates = self._resolve_candidates(insurer, coverage_query)
            candidates_by_insurer[insurer] = candidates
            print(f"  {insurer}: {len(candidates)} candidates")

        # Step 2: Group by comparison state
        print("\n[2] Grouping by comparison state...")
        grouped = self._group_by_comparison_state(candidates_by_insurer)

        # Step 3: Build comparison table
        print("\n[3] Building comparison table...")
        table = self._build_comparison_table(candidates_by_insurer)

        # Step 4: Generate judgment
        print("\n[4] Generating comparability judgment...")
        judgment, limitations = self._generate_judgment(candidates_by_insurer, grouped)

        # Step 5: Build evidence block
        print("\n[5] Building evidence block...")
        evidence = self._build_evidence_block(candidates_by_insurer)

        result = ComparisonResult(
            comparison_table=table,
            comparability_judgment=judgment,
            limitation_reasons=limitations,
            evidence_block=evidence
        )

        print("\n✅ Comparison complete")
        return result

    def _resolve_candidates(self, insurer: str, coverage_query: str) -> List[CoverageCandidate]:
        """
        Resolve coverage candidates for a given insurer and query.

        Args:
            insurer: Insurer name
            coverage_query: Coverage query string

        Returns:
            List of CoverageCandidate objects
        """
        # Filter by insurer
        insurer_mappings = self.mapping_df[self.mapping_df['insurer'] == insurer].copy()

        if len(insurer_mappings) == 0:
            return []

        # Calculate match scores (simple string similarity)
        query_normalized = self._normalize_text(coverage_query)

        insurer_mappings['match_score'] = insurer_mappings['coverage_name_raw'].apply(
            lambda x: self._calculate_similarity(query_normalized, self._normalize_text(str(x)))
        )

        # Filter candidates with score > threshold
        threshold = 0.3
        candidates_df = insurer_mappings[insurer_mappings['match_score'] > threshold].copy()

        # Sort by score descending
        candidates_df = candidates_df.sort_values('match_score', ascending=False)

        # Convert to CoverageCandidate objects
        candidates = []

        for idx, row in candidates_df.iterrows():
            # Get additional fields from universe
            universe_row = self.universe_df[
                (self.universe_df['insurer'] == insurer) &
                (self.universe_df['coverage_name_raw'] == row['coverage_name_raw'])
            ]

            if len(universe_row) == 0:
                continue

            universe_row = universe_row.iloc[0]

            candidate = CoverageCandidate(
                insurer=insurer,
                row_id=str(universe_row['row_id']),
                coverage_name_raw=row['coverage_name_raw'],
                amount_raw=str(universe_row['amount_raw']) if pd.notna(universe_row['amount_raw']) else "",
                premium_raw=str(universe_row['premium_raw']) if pd.notna(universe_row['premium_raw']) else "",
                pay_term_raw=str(universe_row['pay_term_raw']) if pd.notna(universe_row['pay_term_raw']) else "",
                maturity_raw=str(universe_row['maturity_raw']) if pd.notna(universe_row['maturity_raw']) else "",
                mapping_status=row['mapping_status'],
                shinjeongwon_code=row['shinjeongwon_code'] if pd.notna(row['shinjeongwon_code']) and row['shinjeongwon_code'] else None,
                match_score=row['match_score']
            )

            candidates.append(candidate)

        return candidates

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if pd.isna(text):
            return ""
        text = str(text).lower()
        text = re.sub(r'\s+', '', text)  # Remove whitespace
        text = re.sub(r'[()]', '', text)  # Remove parentheses
        return text

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple string similarity.

        Uses substring matching and common character ratio.
        """
        if not text1 or not text2:
            return 0.0

        # Check if one is substring of the other
        if text1 in text2 or text2 in text1:
            return 0.8

        # Calculate character overlap
        set1 = set(text1)
        set2 = set(text2)

        intersection = set1 & set2
        union = set1 | set2

        if len(union) == 0:
            return 0.0

        jaccard = len(intersection) / len(union)

        return jaccard

    def _group_by_comparison_state(self, candidates_by_insurer: Dict[str, List[CoverageCandidate]]) -> Dict[ComparisonState, List]:
        """
        Group coverage candidates by comparison state.

        Returns:
            Dict mapping ComparisonState to list of (insurer, candidate) tuples
        """
        grouped = {state: [] for state in ComparisonState}

        for insurer, candidates in candidates_by_insurer.items():
            if len(candidates) == 0:
                grouped[ComparisonState.NOT_FOUND].append((insurer, None))
                continue

            # Take best candidate (highest match score)
            best_candidate = candidates[0]

            # Determine state
            if best_candidate.mapping_status == 'MAPPED' and best_candidate.shinjeongwon_code:
                state = ComparisonState.COMPARABLE
            elif best_candidate.mapping_status == 'UNMAPPED':
                state = ComparisonState.COMPARABLE_WITH_GAPS
            else:
                state = ComparisonState.NON_COMPARABLE

            grouped[state].append((insurer, best_candidate))

        return grouped

    def _build_comparison_table(self, candidates_by_insurer: Dict[str, List[CoverageCandidate]]) -> pd.DataFrame:
        """
        Build comparison table with best candidate per insurer.

        Returns:
            DataFrame with columns: 보험사, 담보명, 가입금액, 보험료, 납입/만기, 매핑상태
        """
        rows = []

        for insurer, candidates in candidates_by_insurer.items():
            if len(candidates) == 0:
                rows.append({
                    '보험사': insurer,
                    '담보명': '해당 담보 없음',
                    '가입금액': '-',
                    '보험료': '-',
                    '납입/만기': '-',
                    '매핑상태': 'NOT_FOUND'
                })
                continue

            # Take best candidate
            best = candidates[0]

            # Format pay_term/maturity
            pay_maturity = ""
            if best.pay_term_raw and best.maturity_raw:
                pay_maturity = f"{best.pay_term_raw}/{best.maturity_raw}"
            elif best.pay_term_raw:
                pay_maturity = best.pay_term_raw
            elif best.maturity_raw:
                pay_maturity = best.maturity_raw

            rows.append({
                '보험사': insurer,
                '담보명': best.coverage_name_raw,
                '가입금액': best.amount_raw if best.amount_raw else '-',
                '보험료': best.premium_raw if best.premium_raw else '-',
                '납입/만기': pay_maturity if pay_maturity else '-',
                '매핑상태': best.mapping_status
            })

        return pd.DataFrame(rows)

    def _generate_judgment(self, candidates_by_insurer: Dict[str, List[CoverageCandidate]],
                          grouped: Dict[ComparisonState, List]) -> tuple:
        """
        Generate comparability judgment.

        Returns:
            (judgment_str, limitation_reasons)
        """
        comparable_count = len(grouped[ComparisonState.COMPARABLE])
        gaps_count = len(grouped[ComparisonState.COMPARABLE_WITH_GAPS])
        not_found_count = len(grouped[ComparisonState.NOT_FOUND])
        total = len(candidates_by_insurer)

        limitations = []

        # Determine judgment
        if not_found_count > 0:
            judgment = "제한적 가능"
            limitations.append(f"{not_found_count}개 보험사에 해당 담보 미존재")
        elif gaps_count > 0:
            judgment = "제한적 가능"
            limitations.append(f"{gaps_count}개 담보가 UNMAPPED 상태")
        elif comparable_count == total:
            judgment = "가능"
        else:
            judgment = "불가"
            limitations.append("비교 가능한 담보 부족")

        return judgment, limitations

    def _build_evidence_block(self, candidates_by_insurer: Dict[str, List[CoverageCandidate]]) -> str:
        """
        Build evidence block with row_id and coverage_name_raw for each insurer.

        Returns:
            Formatted evidence string
        """
        lines = ["[Evidence]"]

        for insurer, candidates in candidates_by_insurer.items():
            if len(candidates) == 0:
                lines.append(f'- {insurer}: NOT_FOUND')
                continue

            best = candidates[0]
            lines.append(f'- {insurer}: row_id={best.row_id}, coverage_name_raw="{best.coverage_name_raw}"')

        return "\n".join(lines)

    def print_result(self, result: ComparisonResult):
        """Print comparison result in readable format"""
        print("\n" + "=" * 80)
        print("COMPARISON RESULT")
        print("=" * 80)

        print("\n[비교 테이블]")
        print(result.comparison_table.to_string(index=False))

        print(f"\n[비교 가능 여부] {result.comparability_judgment}")

        if result.limitation_reasons:
            print(f"\n[제한 사유]")
            for reason in result.limitation_reasons:
                print(f"  - {reason}")

        print(f"\n{result.evidence_block}")

        # UNMAPPED warning
        unmapped_rows = result.comparison_table[result.comparison_table['매핑상태'] == 'UNMAPPED']
        if len(unmapped_rows) > 0:
            print("\n⚠️  UNMAPPED 담보 처리:")
            print("   본 담보는 표준 코드에 매핑되지 않았으나, 가입설계서 기준 비교는 가능합니다.")

        print("\n" + "=" * 80)


def main():
    """Demo usage"""
    engine = CoverageComparisonEngine()

    # Example 1: 뇌졸중 진단비
    print("\n\n" + "=" * 80)
    print("EXAMPLE 1: 뇌졸중 진단비")
    print("=" * 80)

    result1 = engine.compare(
        insurers=['SAMSUNG', 'KB', 'LOTTE'],
        coverage_query='뇌졸중 진단비'
    )

    engine.print_result(result1)

    # Example 2: 암진단비
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: 암진단비")
    print("=" * 80)

    result2 = engine.compare(
        insurers=['SAMSUNG', 'HANWHA', 'MERITZ'],
        coverage_query='암진단비'
    )

    engine.print_result(result2)


if __name__ == "__main__":
    main()
