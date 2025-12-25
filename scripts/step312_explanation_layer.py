#!/usr/bin/env python3
"""
STEP 3.12 FINAL: PRIME Comparison Explanation Layer

Purpose:
- Explain WHY a PRIME result occurred (NOT change the result)
- Generate reasoning for limitation states
- Provide evidence from documents (explanation only)

Constitution Rules:
✅ STEP 3.11 results are IMMUTABLE (판결문)
✅ STEP 3.12 is reasoning layer only (이유서)
✅ PRIME 4-State NEVER changes
❌ No re-judgment, no inference, no recommendations
❌ No "practically the same coverage"
❌ No "generally", "usually", "favorable to customer"

This layer ONLY answers:
"What is the FACTUAL reason this PRIME result occurred?"
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import json

from step311_comparison_engine import (
    ProposalFactComparisonEngine,
    ComparisonResult,
    PRIMEState
)


@dataclass
class ExplanationEvidence:
    """Document evidence for explanation (optional)"""
    document_type: str  # proposal_detail, summary, business_rules, policy
    document_name: str
    page: Optional[str]
    quote: str


@dataclass
class InsurerExplanation:
    """Explanation for single insurer's PRIME state"""
    insurer: str
    prime_state: str
    explanation_text: str
    evidence_docs: List[ExplanationEvidence]


@dataclass
class ComparisonExplanation:
    """Explanation wrapper for PRIME comparison result"""
    summary: str
    details: List[InsurerExplanation]


@dataclass
class ExplainedComparisonResult:
    """
    STEP 3.12 output structure.

    Structure:
    - comparison_result: STEP 3.11 result (IMMUTABLE)
    - explanation: STEP 3.12 reasoning (ADDED)
    """
    comparison_result: ComparisonResult  # IMMUTABLE
    explanation: ComparisonExplanation   # ADDED


class PRIMEExplanationLayer:
    """
    STEP 3.12: Explanation layer for PRIME comparison results.

    This layer does NOT modify STEP 3.11 results.
    It ONLY provides reasoning for WHY the result occurred.
    """

    def __init__(self):
        """Initialize explanation layer"""
        print("PRIME Explanation Layer initialized")

    def explain(self, comparison_result: ComparisonResult, coverage_query: str) -> ExplainedComparisonResult:
        """
        Add explanation layer to STEP 3.11 comparison result.

        Args:
            comparison_result: STEP 3.11 result (IMMUTABLE)
            coverage_query: Original coverage query

        Returns:
            ExplainedComparisonResult with explanation added
        """
        print("=" * 80)
        print("STEP 3.12: PRIME Explanation Layer")
        print("=" * 80)
        print(f"Query: {coverage_query}")

        # Generate explanations per insurer
        details = []

        for insurer, prime_state in comparison_result.state_summary.items():
            explanation = self._generate_insurer_explanation(
                insurer=insurer,
                prime_state=prime_state,
                coverage_query=coverage_query,
                comparison_result=comparison_result
            )
            details.append(explanation)

        # Generate summary
        summary = self._generate_summary(comparison_result, coverage_query)

        explanation_layer = ComparisonExplanation(
            summary=summary,
            details=details
        )

        result = ExplainedComparisonResult(
            comparison_result=comparison_result,  # IMMUTABLE - original result preserved
            explanation=explanation_layer
        )

        print("✅ Explanation layer added")
        return result

    def _generate_insurer_explanation(
        self,
        insurer: str,
        prime_state: PRIMEState,
        coverage_query: str,
        comparison_result: ComparisonResult
    ) -> InsurerExplanation:
        """
        Generate explanation for single insurer's PRIME state.

        State-specific templates (FIXED):
        - out_of_universe: Explain non-existence
        - in_universe_with_gaps: Explain limitation reasons
        - in_universe_unmapped: Explain standard code absence
        - in_universe_comparable: Explain comparability basis
        """
        # Get evidence for this insurer
        evidence_lines = comparison_result.evidence_block.split('\n')
        insurer_evidence = [line for line in evidence_lines if line.startswith(f'- {insurer}:')]

        # Extract coverage candidates info
        insurer_rows = comparison_result.comparison_table[
            comparison_result.comparison_table['보험사'] == insurer
        ]

        num_candidates = len(insurer_rows)

        # State-specific explanation templates
        if prime_state == PRIMEState.OUT_OF_UNIVERSE:
            explanation_text = self._explain_out_of_universe(insurer, coverage_query)

        elif prime_state == PRIMEState.IN_UNIVERSE_WITH_GAPS:
            explanation_text = self._explain_with_gaps(insurer, coverage_query, num_candidates, insurer_rows)

        elif prime_state == PRIMEState.IN_UNIVERSE_UNMAPPED:
            explanation_text = self._explain_unmapped(insurer, coverage_query, insurer_rows)

        elif prime_state == PRIMEState.IN_UNIVERSE_COMPARABLE:
            explanation_text = self._explain_comparable(insurer, coverage_query, insurer_rows)

        else:
            explanation_text = f"PRIME 상태: {prime_state.value}"

        # Evidence docs (can be extended with RAG)
        evidence_docs = []  # Currently empty, can add RAG-based evidence

        return InsurerExplanation(
            insurer=insurer,
            prime_state=prime_state.value,
            explanation_text=explanation_text,
            evidence_docs=evidence_docs
        )

    def _explain_out_of_universe(self, insurer: str, coverage_query: str) -> str:
        """
        Explain out_of_universe state.

        Template (FIXED):
        "{보험사} 가입설계서의 요약 담보 표에는
        '{질의 담보 표현}'과 일치하는 담보가 기재되어 있지 않습니다."

        Forbidden:
        - "실제로는 있다"
        - "유사 담보로 볼 수 있다"
        """
        return (
            f"{insurer} 가입설계서의 요약 담보 표에는 "
            f"'{coverage_query}'와 문자열이 일치하는 담보가 기재되어 있지 않습니다.\n\n"
            f"PRIME 시스템은 가입설계서 요약표를 유일한 비교 근거(SSOT)로 사용하므로, "
            f"요약표에 없는 담보는 비교 대상에 포함되지 않습니다."
        )

    def _explain_with_gaps(self, insurer: str, coverage_query: str, num_candidates: int, insurer_rows) -> str:
        """
        Explain in_universe_with_gaps state.

        Allowed explanation elements:
        - Multiple candidates exist
        - Some axes missing
        - Cannot confirm single coverage

        Template:
        "{보험사} 가입설계서에는 질의와 문자열이 일치하는 담보가 {N}건 존재합니다.
        PRIME 시스템은 의미 추론을 수행하지 않으므로 단일 담보로 확정하지 않습니다."
        """
        # Check if multiple candidates
        if num_candidates > 1:
            coverage_names = insurer_rows['담보명'].tolist()
            coverage_list = '\n  - '.join(coverage_names)

            return (
                f"{insurer} 가입설계서에는 질의와 문자열이 일치하는 담보가 {num_candidates}건 존재합니다:\n"
                f"  - {coverage_list}\n\n"
                f"PRIME 시스템은 의미 추론을 수행하지 않으므로, "
                f"여러 후보 중 하나를 선택하거나 통합하지 않습니다. "
                f"따라서 in_universe_with_gaps 상태로 분류되었습니다."
            )

        # Single candidate but has gaps in axes
        else:
            row = insurer_rows.iloc[0]
            missing_axes = []

            if row['가입금액'] == '-' or not row['가입금액']:
                missing_axes.append('가입금액')
            if row['보험료'] == '-' or not row['보험료']:
                missing_axes.append('보험료')
            if row['납입기간'] == '-' or not row['납입기간']:
                missing_axes.append('납입기간')
            if row['만기'] == '-' or not row['만기']:
                missing_axes.append('만기')

            if missing_axes:
                axes_str = ', '.join(missing_axes)
                return (
                    f"{insurer} 가입설계서에는 '{row['담보명']}' 담보가 존재하나, "
                    f"다음 비교 축 정보가 누락되어 있습니다: {axes_str}\n\n"
                    f"PRIME 시스템은 핵심 축 정보(금액, 보험료, 납입기간, 만기)가 모두 존재해야 "
                    f"in_universe_comparable 상태로 분류합니다."
                )
            else:
                return (
                    f"{insurer} 가입설계서에 '{row['담보명']}' 담보가 존재하나, "
                    f"비교 제한 사유가 있어 in_universe_with_gaps 상태로 분류되었습니다."
                )

    def _explain_unmapped(self, insurer: str, coverage_query: str, insurer_rows) -> str:
        """
        Explain in_universe_unmapped state.

        Template:
        "해당 담보는 가입설계서에 명시적으로 존재하나,
        현재 참조 중인 신정원 코드 자료와 직접 대응되지 않습니다."

        Forbidden:
        - "비표준 담보다"
        - "유사 코드가 있다"
        """
        row = insurer_rows.iloc[0]
        coverage_name = row['담보명']

        return (
            f"{insurer} 가입설계서에 '{coverage_name}' 담보가 명시적으로 존재하나, "
            f"현재 참조 중인 신정원 통일 담보 코드 자료와 직접 대응되지 않습니다.\n\n"
            f"이는 다음과 같은 이유로 발생할 수 있습니다:\n"
            f"  - 신정원 코드 자료에 해당 담보명이 미등록\n"
            f"  - 담보명 표기 방식 차이 (공백, 특수문자 등)\n"
            f"  - 보험사 고유 담보명 사용\n\n"
            f"UNMAPPED 상태는 비교 불가를 의미하지 않으며, "
            f"가입설계서 기준 사실(fact) 비교는 가능합니다."
        )

    def _explain_comparable(self, insurer: str, coverage_query: str, insurer_rows) -> str:
        """
        Explain in_universe_comparable state.

        Template:
        "각 보험사 가입설계서에 단일 담보로 명확히 기재되어 있어
        PRIME 기준 비교가 가능합니다."
        """
        row = insurer_rows.iloc[0]
        coverage_name = row['담보명']
        shinjeongwon_code = row['신정원코드']

        return (
            f"{insurer} 가입설계서에 '{coverage_name}' 담보가 단일 담보로 명확히 기재되어 있으며, "
            f"신정원 통일 코드({shinjeongwon_code})와 대응됩니다.\n\n"
            f"핵심 비교 축(가입금액, 보험료, 납입기간, 만기) 정보가 모두 존재하여 "
            f"PRIME 기준 비교가 가능합니다."
        )

    def _generate_summary(self, comparison_result: ComparisonResult, coverage_query: str) -> str:
        """
        Generate overall summary of comparison result.

        Summary structure:
        - comparison_possible status
        - Main limitation reasons
        - No recommendations/judgments
        """
        comparable_count = sum(
            1 for state in comparison_result.state_summary.values()
            if state == PRIMEState.IN_UNIVERSE_COMPARABLE
        )
        total_insurers = len(comparison_result.state_summary)

        if comparison_result.comparison_possible:
            if comparable_count == total_insurers:
                summary = (
                    f"'{coverage_query}' 담보에 대해 모든 보험사({total_insurers}개)가 "
                    f"in_universe_comparable 상태로, PRIME 기준 완전 비교가 가능합니다."
                )
            else:
                summary = (
                    f"'{coverage_query}' 담보에 대해 {total_insurers}개 보험사 중 {comparable_count}개가 "
                    f"in_universe_comparable 상태입니다. "
                    f"나머지 보험사는 제한 사유가 있어 사실(fact) 기반 비교만 가능합니다."
                )
        else:
            summary = (
                f"'{coverage_query}' 담보에 대해 모든 보험사가 out_of_universe 상태로, "
                f"가입설계서 기준 비교가 불가능합니다."
            )

        return summary

    def print_explained_result(self, result: ExplainedComparisonResult):
        """
        Print explained comparison result.

        Output structure:
        1. Original STEP 3.11 comparison result
        2. STEP 3.12 explanation layer
        """
        print("\n" + "=" * 80)
        print("STEP 3.12: EXPLAINED COMPARISON RESULT")
        print("=" * 80)

        # Print original STEP 3.11 result
        print("\n[STEP 3.11 비교 결과 - IMMUTABLE]")
        print("-" * 80)

        display_cols = ['보험사', '담보명', '가입금액', '보험료', 'PRIME상태', '매핑상태']
        print(result.comparison_result.comparison_table[display_cols].to_string(index=False))

        print(f"\n비교 가능 여부: {'가능' if result.comparison_result.comparison_possible else '불가'}")

        if result.comparison_result.limitation_reasons:
            print(f"\n제한 사유:")
            for reason in result.comparison_result.limitation_reasons:
                print(f"  - {reason}")

        # Print STEP 3.12 explanation layer
        print("\n" + "=" * 80)
        print("[STEP 3.12 설명 레이어 - ADDED]")
        print("=" * 80)

        print(f"\n[전체 요약]")
        print(result.explanation.summary)

        print(f"\n[보험사별 상세 설명]")
        for detail in result.explanation.details:
            print(f"\n▶ {detail.insurer} ({detail.prime_state})")
            print(f"{detail.explanation_text}")

            if detail.evidence_docs:
                print(f"\n  [설명 근거 문서]")
                for doc in detail.evidence_docs:
                    print(f"    - {doc.document_type}: {doc.document_name}")
                    if doc.page:
                        print(f"      페이지: {doc.page}")
                    print(f"      인용: {doc.quote}")

        print("\n" + "=" * 80)


def main():
    """Demo usage with STEP 3.11 samples"""
    # Initialize engines
    comparison_engine = ProposalFactComparisonEngine()
    explanation_layer = PRIMEExplanationLayer()

    # Sample 1: 암진단비
    print("\n\n" + "=" * 80)
    print("SAMPLE 1: 암진단비 (with explanation)")
    print("=" * 80)

    comparison_result1 = comparison_engine.compare(
        insurers=['SAMSUNG', 'HANWHA', 'MERITZ'],
        coverage_query='암진단비'
    )

    explained_result1 = explanation_layer.explain(
        comparison_result=comparison_result1,
        coverage_query='암진단비'
    )

    explanation_layer.print_explained_result(explained_result1)

    # Sample 2: 뇌졸중진단비
    print("\n\n" + "=" * 80)
    print("SAMPLE 2: 뇌졸중진단비 (with explanation)")
    print("=" * 80)

    comparison_result2 = comparison_engine.compare(
        insurers=['SAMSUNG', 'KB', 'LOTTE'],
        coverage_query='뇌졸중진단비'
    )

    explained_result2 = explanation_layer.explain(
        comparison_result=comparison_result2,
        coverage_query='뇌졸중진단비'
    )

    explanation_layer.print_explained_result(explained_result2)

    # Sample 3: 다빈치수술비
    print("\n\n" + "=" * 80)
    print("SAMPLE 3: 다빈치수술비 (with explanation)")
    print("=" * 80)

    comparison_result3 = comparison_engine.compare(
        insurers=['DB', 'HYUNDAI', 'HEUNGKUK'],
        coverage_query='다빈치수술비'
    )

    explained_result3 = explanation_layer.explain(
        comparison_result=comparison_result3,
        coverage_query='다빈치수술비'
    )

    explanation_layer.print_explained_result(explained_result3)


if __name__ == "__main__":
    main()
