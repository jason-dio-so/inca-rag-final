#!/usr/bin/env python3
"""
STEP 3.11′ HOTFIX: Proposal-based Fact Comparison Engine (PRIME-aligned)

PRIME Constitution Compliance:
1. Proposal = SSOT (Fact Table only)
2. PRIME 4-State: in_universe_comparable/unmapped/with_gaps, out_of_universe
3. NO inference-based matching (substring search only)
4. Shinjeongwon code = reference key (NOT filter/primary key)
5. UNMAPPED ≠ "similar coverage" (fact-based comparison only)

Hard Bans:
❌ No similarity/score/ranking logic
❌ No "similar coverage" inference
❌ No policy/summary/business_rules reference
❌ No filtering by Shinjeongwon code
❌ No coverage unification
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


class PRIMEState(Enum):
    """PRIME 4-State classification"""
    IN_UNIVERSE_COMPARABLE = "in_universe_comparable"
    IN_UNIVERSE_UNMAPPED = "in_universe_unmapped"
    IN_UNIVERSE_WITH_GAPS = "in_universe_with_gaps"
    OUT_OF_UNIVERSE = "out_of_universe"


@dataclass
class ProposalCoverageRow:
    """Single proposal coverage row (fact-based)"""
    insurer: str
    proposal_file: str
    proposal_variant: str
    row_id: str
    coverage_name_raw: str
    amount_raw: str
    premium_raw: str
    pay_term_raw: str
    maturity_raw: str
    renewal_raw: str
    notes: str
    mapping_status: str  # MAPPED | UNMAPPED
    shinjeongwon_code: Optional[str]
    prime_state: PRIMEState


@dataclass
class ComparisonResult:
    """PRIME-aligned comparison result"""
    comparison_table: pd.DataFrame
    comparison_possible: bool
    limitation_reasons: List[str]
    evidence_block: str
    state_summary: Dict[str, PRIMEState]


class ProposalFactComparisonEngine:
    """
    Proposal-based Fact Comparison Engine (PRIME-aligned)

    STEP 3.11′ HOTFIX implementation.
    """

    def __init__(self):
        """Load data sources"""
        self.universe_df = pd.read_csv(UNIVERSE_CSV)
        self.mapping_df = pd.read_csv(MAPPING_CSV)

        print("Proposal Fact Comparison Engine initialized")
        print(f"  Universe rows: {len(self.universe_df)}")
        print(f"  Mapping rows: {len(self.mapping_df)}")

        # Verify no AMBIGUOUS in insurer-filtered mapping
        ambiguous_count = len(self.mapping_df[self.mapping_df['mapping_status'] == 'AMBIGUOUS'])
        if ambiguous_count > 0:
            raise ValueError(f"AMBIGUOUS rows found in mapping ({ambiguous_count}). Must use insurer-filtered version.")

    def compare(self, insurers: List[str], coverage_query: str) -> ComparisonResult:
        """
        Main comparison entry point.

        Args:
            insurers: List of insurer names
            coverage_query: Coverage query (substring search only, no inference)

        Returns:
            ComparisonResult with fact table and PRIME states
        """
        print("=" * 80)
        print("STEP 3.11′: Proposal Fact Comparison (PRIME-aligned)")
        print("=" * 80)
        print(f"Insurers: {insurers}")
        print(f"Query: {coverage_query}")

        # Step 1: Resolve candidate rows per insurer (deterministic substring search)
        print("\n[1] Resolving candidate rows (substring search only)...")
        candidates_by_insurer = {}

        for insurer in insurers:
            candidates = self._resolve_candidates_deterministic(insurer, coverage_query)
            candidates_by_insurer[insurer] = candidates
            print(f"  {insurer}: {len(candidates)} candidates")

        # Step 2: Classify PRIME states
        print("\n[2] Classifying PRIME states...")
        state_summary = {}

        for insurer, candidates in candidates_by_insurer.items():
            if len(candidates) == 0:
                state_summary[insurer] = PRIMEState.OUT_OF_UNIVERSE
            else:
                # Classify based on first candidate (or mark WITH_GAPS if multiple)
                state = self._classify_prime_state(candidates)
                state_summary[insurer] = state

            print(f"  {insurer}: {state_summary[insurer].value}")

        # Step 3: Build fact-based comparison table
        print("\n[3] Building fact-based comparison table...")
        table = self._build_fact_table(candidates_by_insurer, state_summary)

        # Step 4: Determine comparison_possible and limitations
        print("\n[4] Determining comparison_possible and limitations...")
        comparison_possible, limitations = self._determine_comparison_possible(state_summary, candidates_by_insurer)

        # Step 5: Build evidence block
        print("\n[5] Building evidence block...")
        evidence = self._build_evidence_block(candidates_by_insurer)

        result = ComparisonResult(
            comparison_table=table,
            comparison_possible=comparison_possible,
            limitation_reasons=limitations,
            evidence_block=evidence,
            state_summary=state_summary
        )

        print("\n✅ Comparison complete")
        return result

    def _normalize_for_search(self, text: str) -> str:
        """
        Minimal normalization for substring search.

        Allowed:
        - Strip leading/trailing whitespace
        - Collapse multiple spaces to single space
        - Lowercase for case-insensitive search

        NOT allowed:
        - Remove parentheses/special characters (meaning-changing)
        """
        if pd.isna(text):
            return ""
        text = str(text).strip()
        text = re.sub(r'\s+', ' ', text)  # Collapse whitespace
        return text.lower()

    def _resolve_candidates_deterministic(self, insurer: str, coverage_query: str) -> List[ProposalCoverageRow]:
        """
        Deterministic substring search (NO similarity/score/inference).

        Rules:
        1. coverage_name_raw contains query (after normalization)
        2. If multiple rows match, return ALL (no selection/inference)
        3. NO ranking, NO scoring
        """
        # Filter by insurer
        insurer_mappings = self.mapping_df[self.mapping_df['insurer'] == insurer].copy()

        if len(insurer_mappings) == 0:
            return []

        # Normalize query
        query_normalized = self._normalize_for_search(coverage_query)

        # Substring search
        insurer_mappings['name_normalized'] = insurer_mappings['coverage_name_raw'].apply(self._normalize_for_search)
        matches = insurer_mappings[insurer_mappings['name_normalized'].str.contains(query_normalized, na=False)].copy()

        # Convert to ProposalCoverageRow objects
        candidates = []

        for idx, row in matches.iterrows():
            # Get additional fields from universe
            universe_row = self.universe_df[
                (self.universe_df['insurer'] == insurer) &
                (self.universe_df['coverage_name_raw'] == row['coverage_name_raw'])
            ]

            if len(universe_row) == 0:
                continue

            universe_row = universe_row.iloc[0]

            # Classify PRIME state (will be overridden if multiple candidates)
            prime_state = self._classify_single_row_state(row, universe_row)

            candidate = ProposalCoverageRow(
                insurer=insurer,
                proposal_file=str(universe_row['proposal_file']),
                proposal_variant=str(universe_row['proposal_variant']) if pd.notna(universe_row['proposal_variant']) else "",
                row_id=str(universe_row['row_id']),
                coverage_name_raw=row['coverage_name_raw'],
                amount_raw=str(universe_row['amount_raw']) if pd.notna(universe_row['amount_raw']) else "",
                premium_raw=str(universe_row['premium_raw']) if pd.notna(universe_row['premium_raw']) else "",
                pay_term_raw=str(universe_row['pay_term_raw']) if pd.notna(universe_row['pay_term_raw']) else "",
                maturity_raw=str(universe_row['maturity_raw']) if pd.notna(universe_row['maturity_raw']) else "",
                renewal_raw=str(universe_row['renewal_raw']) if pd.notna(universe_row['renewal_raw']) else "",
                notes=str(universe_row['notes']) if pd.notna(universe_row['notes']) else "",
                mapping_status=row['mapping_status'],
                shinjeongwon_code=row['shinjeongwon_code'] if pd.notna(row['shinjeongwon_code']) and row['shinjeongwon_code'] else None,
                prime_state=prime_state
            )

            candidates.append(candidate)

        return candidates

    def _classify_single_row_state(self, mapping_row, universe_row) -> PRIMEState:
        """
        Classify PRIME state for a single row.

        Rules (deterministic):
        1. UNMAPPED → in_universe_unmapped
        2. MAPPED + any NULL/empty in (amount, premium, pay_term, maturity) → in_universe_with_gaps
        3. MAPPED + all values present → in_universe_comparable
        """
        mapping_status = mapping_row['mapping_status']

        if mapping_status == 'UNMAPPED':
            return PRIMEState.IN_UNIVERSE_UNMAPPED

        # Check for gaps in core axes
        amount = universe_row['amount_raw']
        premium = universe_row['premium_raw']
        pay_term = universe_row['pay_term_raw']
        maturity = universe_row['maturity_raw']

        has_gaps = (
            pd.isna(amount) or str(amount).strip() == "" or
            pd.isna(premium) or str(premium).strip() == "" or
            pd.isna(pay_term) or str(pay_term).strip() == "" or
            pd.isna(maturity) or str(maturity).strip() == ""
        )

        if has_gaps:
            return PRIMEState.IN_UNIVERSE_WITH_GAPS
        else:
            return PRIMEState.IN_UNIVERSE_COMPARABLE

    def _classify_prime_state(self, candidates: List[ProposalCoverageRow]) -> PRIMEState:
        """
        Classify PRIME state for multiple candidates.

        Rules:
        - If multiple candidates → force IN_UNIVERSE_WITH_GAPS (no inference)
        - If single candidate → use its state
        """
        if len(candidates) == 0:
            return PRIMEState.OUT_OF_UNIVERSE

        if len(candidates) > 1:
            # Multiple candidates → no inference allowed
            return PRIMEState.IN_UNIVERSE_WITH_GAPS

        # Single candidate → use its state
        return candidates[0].prime_state

    def _build_fact_table(self, candidates_by_insurer: Dict[str, List[ProposalCoverageRow]],
                          state_summary: Dict[str, PRIMEState]) -> pd.DataFrame:
        """
        Build fact-based comparison table (PRIME axes only).

        Columns:
        - 보험사, 담보명, 가입금액, 보험료, 납입기간, 만기, 갱신, 비고
        - PRIME상태, 매핑상태, 신정원코드
        - (추적용) proposal_file, proposal_variant, row_id
        """
        rows = []

        for insurer, candidates in candidates_by_insurer.items():
            if len(candidates) == 0:
                # OUT_OF_UNIVERSE
                rows.append({
                    '보험사': insurer,
                    '담보명': '해당 담보 없음',
                    '가입금액': '-',
                    '보험료': '-',
                    '납입기간': '-',
                    '만기': '-',
                    '갱신': '-',
                    '비고': '-',
                    'PRIME상태': PRIMEState.OUT_OF_UNIVERSE.value,
                    '매핑상태': '-',
                    '신정원코드': '-',
                    'proposal_file': '-',
                    'proposal_variant': '-',
                    'row_id': '-'
                })
                continue

            # If multiple candidates, show all (no selection)
            if len(candidates) > 1:
                for i, candidate in enumerate(candidates):
                    rows.append(self._candidate_to_table_row(candidate, state_summary[insurer], is_multiple=(i == 0)))
            else:
                # Single candidate
                rows.append(self._candidate_to_table_row(candidates[0], state_summary[insurer], is_multiple=False))

        return pd.DataFrame(rows)

    def _candidate_to_table_row(self, candidate: ProposalCoverageRow, prime_state: PRIMEState, is_multiple: bool) -> dict:
        """Convert ProposalCoverageRow to table row dict"""
        row = {
            '보험사': candidate.insurer,
            '담보명': candidate.coverage_name_raw,
            '가입금액': candidate.amount_raw if candidate.amount_raw else '-',
            '보험료': candidate.premium_raw if candidate.premium_raw else '-',
            '납입기간': candidate.pay_term_raw if candidate.pay_term_raw else '-',
            '만기': candidate.maturity_raw if candidate.maturity_raw else '-',
            '갱신': candidate.renewal_raw if candidate.renewal_raw else '-',
            '비고': candidate.notes if candidate.notes else '-',
            'PRIME상태': prime_state.value + (" (MULTIPLE_CANDIDATES)" if is_multiple else ""),
            '매핑상태': candidate.mapping_status,
            '신정원코드': candidate.shinjeongwon_code if candidate.shinjeongwon_code else '-',
            'proposal_file': candidate.proposal_file,
            'proposal_variant': candidate.proposal_variant,
            'row_id': candidate.row_id
        }

        return row

    def _determine_comparison_possible(self, state_summary: Dict[str, PRIMEState],
                                      candidates_by_insurer: Dict[str, List[ProposalCoverageRow]]) -> tuple:
        """
        Determine comparison_possible and limitation_reasons.

        Rules:
        - comparison_possible = true if at least 1 insurer has in_universe_* state
        - limitation_reasons = fact-based only
        """
        in_universe_count = sum(1 for state in state_summary.values() if state != PRIMEState.OUT_OF_UNIVERSE)

        comparison_possible = in_universe_count > 0

        limitations = []

        # Check for specific limitations
        unmapped_count = sum(1 for state in state_summary.values() if state == PRIMEState.IN_UNIVERSE_UNMAPPED)
        gaps_count = sum(1 for state in state_summary.values() if state == PRIMEState.IN_UNIVERSE_WITH_GAPS)
        out_count = sum(1 for state in state_summary.values() if state == PRIMEState.OUT_OF_UNIVERSE)

        # Check for multiple candidates
        multiple_candidates_insurers = [
            insurer for insurer, candidates in candidates_by_insurer.items()
            if len(candidates) > 1
        ]

        if unmapped_count > 0:
            limitations.append(f"UNMAPPED_PRESENT ({unmapped_count} insurers)")

        if gaps_count > 0:
            limitations.append(f"GAPS_PRESENT ({gaps_count} insurers)")

        if len(multiple_candidates_insurers) > 0:
            limitations.append(f"MULTIPLE_CANDIDATES_NO_INFERENCE ({', '.join(multiple_candidates_insurers)})")

        if out_count > 0:
            limitations.append(f"OUT_OF_UNIVERSE_PRESENT ({out_count} insurers)")

        return comparison_possible, limitations

    def _build_evidence_block(self, candidates_by_insurer: Dict[str, List[ProposalCoverageRow]]) -> str:
        """
        Build evidence block with file/variant/row_id/coverage_name_raw.
        """
        lines = ["[Evidence]"]

        for insurer, candidates in candidates_by_insurer.items():
            if len(candidates) == 0:
                lines.append(f'- {insurer}: OUT_OF_UNIVERSE')
                continue

            if len(candidates) > 1:
                lines.append(f'- {insurer}: MULTIPLE_CANDIDATES ({len(candidates)} rows)')
                for i, candidate in enumerate(candidates):
                    lines.append(f'    [{i+1}] file={candidate.proposal_file}, variant={candidate.proposal_variant}, '
                               f'row_id={candidate.row_id}, coverage_name_raw="{candidate.coverage_name_raw}"')
            else:
                candidate = candidates[0]
                lines.append(f'- {insurer}: file={candidate.proposal_file}, variant={candidate.proposal_variant}, '
                           f'row_id={candidate.row_id}, coverage_name_raw="{candidate.coverage_name_raw}"')

        return "\n".join(lines)

    def print_result(self, result: ComparisonResult):
        """Print comparison result in PRIME-aligned format"""
        print("\n" + "=" * 80)
        print("COMPARISON RESULT (PRIME-aligned)")
        print("=" * 80)

        print("\n[비교 테이블 - Fact-based only]")
        # Select display columns
        display_cols = ['보험사', '담보명', '가입금액', '보험료', '납입기간', '만기', 'PRIME상태', '매핑상태']
        print(result.comparison_table[display_cols].to_string(index=False))

        print(f"\n[비교 가능 여부] {'가능' if result.comparison_possible else '불가'}")

        if result.limitation_reasons:
            print(f"\n[제한 사유 - Fact-based]")
            for reason in result.limitation_reasons:
                print(f"  - {reason}")

        print(f"\n{result.evidence_block}")

        # PRIME state summary
        print("\n[PRIME State Summary]")
        for insurer, state in result.state_summary.items():
            print(f"  {insurer}: {state.value}")

        # UNMAPPED warning (fact-based only)
        unmapped_insurers = [k for k, v in result.state_summary.items() if v == PRIMEState.IN_UNIVERSE_UNMAPPED]
        if unmapped_insurers:
            print("\n⚠️  UNMAPPED 담보 처리 (사실 기반):")
            print(f"   다음 보험사의 담보는 표준 코드에 매핑되지 않았습니다: {', '.join(unmapped_insurers)}")
            print("   가입설계서 요약표 기준 사실(fact) 비교만 가능합니다.")

        print("\n" + "=" * 80)


def main():
    """Demo usage with 3 samples"""
    engine = ProposalFactComparisonEngine()

    # Sample 1: 암진단비
    print("\n\n" + "=" * 80)
    print("SAMPLE 1: 암진단비")
    print("=" * 80)

    result1 = engine.compare(
        insurers=['SAMSUNG', 'HANWHA', 'MERITZ'],
        coverage_query='암진단비'
    )

    engine.print_result(result1)

    # Sample 2: 뇌졸중진단비
    print("\n\n" + "=" * 80)
    print("SAMPLE 2: 뇌졸중진단비")
    print("=" * 80)

    result2 = engine.compare(
        insurers=['SAMSUNG', 'KB', 'LOTTE'],
        coverage_query='뇌졸중진단비'
    )

    engine.print_result(result2)

    # Sample 3: 다빈치수술비 (expected: mostly OUT_OF_UNIVERSE)
    print("\n\n" + "=" * 80)
    print("SAMPLE 3: 다빈치수술비")
    print("=" * 80)

    result3 = engine.compare(
        insurers=['DB', 'HYUNDAI', 'HEUNGKUK'],
        coverage_query='다빈치수술비'
    )

    engine.print_result(result3)


if __name__ == "__main__":
    main()
