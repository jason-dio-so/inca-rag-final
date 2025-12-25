#!/usr/bin/env python3
"""
STEP 4.0 FINAL: Customer Response Formatter (출력 전용 레이어)

Purpose:
- Transform STEP 3.13's ExplainedComparisonResult into customer-friendly format
- Display ONLY (no judgment, no modification, no inference)
- Fixed 3-section structure: Summary Header → Fact Table → Explanation Blocks

Constitution Rules:
✅ STEP 3.11 results are IMMUTABLE (판결문)
✅ STEP 3.12 explanations are IMMUTABLE (이유서)
✅ STEP 4.0 is presentation only (출력)
❌ No PRIME state changes
❌ No result recalculation
❌ No coverage integration
❌ No similarity judgment
❌ No recommendations
❌ Forbidden phrases strictly enforced

This layer ONLY answers:
"How do we present STEP 3.11 + STEP 3.12 results to customers?"
"""

import sys
from typing import Dict, List

sys.path.insert(0, 'scripts')
from step313_query_pipeline import QueryPipeline
from step312_explanation_layer import ExplainedComparisonResult
from step311_comparison_engine import PRIMEState


class CustomerResponseFormatter:
    """
    STEP 4.0: Customer Response Formatter

    Transform ExplainedComparisonResult into customer-friendly output.

    Forbidden Actions:
    - Modifying PRIME states
    - Recalculating comparison results
    - Adding new interpretations
    - Recommending options
    - Using forbidden phrases
    """

    # PRIME state → Customer label mapping (표현 변경만, 의미 동일)
    PRIME_STATE_LABELS = {
        PRIMEState.IN_UNIVERSE_COMPARABLE.value: "비교 가능",
        PRIMEState.IN_UNIVERSE_WITH_GAPS.value: "제한적 비교 가능",
        PRIMEState.IN_UNIVERSE_UNMAPPED.value: "비교 가능 (표준 코드 미대응)",
        PRIMEState.OUT_OF_UNIVERSE.value: "비교 대상 아님",
    }

    # Forbidden phrases (Hard Ban) - Recommendation/Inference contexts only
    FORBIDDEN_PHRASES = [
        "사실상 같은 담보",
        "유사한 담보",
        "일반적으로",
        "보통은",
        "고객에게 유리",
        "추천합니다",
        "추천드립니다",
        "선택하세요",
        "선택하시면",
        "선택하는 것이",
        "더 나은",
        "거의 동일",
    ]

    def __init__(self):
        """Initialize formatter"""
        print("Customer Response Formatter initialized (STEP 4.0)")

    def format(self, result: ExplainedComparisonResult, coverage_query: str) -> str:
        """
        Format ExplainedComparisonResult into customer-friendly response.

        Args:
            result: STEP 3.13 output (IMMUTABLE)
            coverage_query: Original coverage query

        Returns:
            Formatted customer response string

        Structure:
            1. Summary Header
            2. Comparison Table (Fact Table Only)
            3. Insurer-specific Explanation Blocks
        """
        sections = []

        # Section 1: Summary Header
        sections.append(self._format_summary_header(result, coverage_query))

        # Section 2: Comparison Table
        sections.append(self._format_comparison_table(result))

        # Section 3: Explanation Blocks
        sections.append(self._format_explanation_blocks(result))

        # Combine sections
        formatted_response = "\n\n".join(sections)

        # Validate forbidden phrases
        self._validate_no_forbidden_phrases(formatted_response)

        return formatted_response

    def _format_summary_header(self, result: ExplainedComparisonResult, coverage_query: str) -> str:
        """
        Format summary header section.

        Rules:
        - PRIME 상태를 자연어로 치환만 한다
        - 새로운 해석 추가 금지
        """
        header_lines = []
        header_lines.append("[비교 요약]")
        header_lines.append("")

        # Coverage query
        header_lines.append(f"요청하신 담보: {coverage_query}")

        # Target insurers
        insurers = list(result.comparison_result.state_summary.keys())
        insurers_str = ", ".join(insurers)
        header_lines.append(f"비교 보험사: {insurers_str}")

        header_lines.append("")
        header_lines.append("비교 결과 요약:")

        # Overall comparison status
        if result.comparison_result.comparison_possible:
            comparable_count = sum(
                1 for state in result.comparison_result.state_summary.values()
                if state == PRIMEState.IN_UNIVERSE_COMPARABLE
            )
            total_count = len(result.comparison_result.state_summary)

            if comparable_count == total_count:
                header_lines.append("- 비교 가능 여부: 완전 비교 가능")
            else:
                header_lines.append("- 비교 가능 여부: 제한적 가능")
        else:
            header_lines.append("- 비교 가능 여부: 비교 불가")

        # Limitation reasons (직접 전달, 해석 없음)
        if result.comparison_result.limitation_reasons:
            header_lines.append("- 제한 사유:")
            for reason in result.comparison_result.limitation_reasons:
                header_lines.append(f"  • {reason}")

        return "\n".join(header_lines)

    def _format_comparison_table(self, result: ExplainedComparisonResult) -> str:
        """
        Format comparison table section.

        Rules:
        - STEP 3.11의 comparison_table을 그대로 시각화
        - 컬럼 추가/삭제/가공 금지
        - 정렬은 보험사명 기준 고정
        """
        table_lines = []
        table_lines.append("[비교 테이블]")
        table_lines.append("")

        # Display columns
        display_cols = ['보험사', '담보명', '가입금액', '보험료', '납입기간', '만기', 'PRIME상태', '매핑상태']

        # Map PRIME states to customer labels
        table_df = result.comparison_result.comparison_table.copy()
        table_df['PRIME상태_고객용'] = table_df['PRIME상태'].map(
            lambda x: self.PRIME_STATE_LABELS.get(x, x)
        )

        # Display columns with customer labels
        display_cols_mapped = ['보험사', '담보명', '가입금액', '보험료', '납입기간', '만기', 'PRIME상태_고객용', '매핑상태']

        # Rename for display
        table_display = table_df[display_cols_mapped].copy()
        table_display.columns = ['보험사', '담보명', '가입금액', '보험료', '납입기간', '만기', 'PRIME 상태', '매핑 상태']

        # Sort by insurer name
        table_display = table_display.sort_values('보험사')

        # Convert to string
        table_str = table_display.to_string(index=False)
        table_lines.append(table_str)

        return "\n".join(table_lines)

    def _format_explanation_blocks(self, result: ExplainedComparisonResult) -> str:
        """
        Format explanation blocks section.

        Rules:
        - STEP 3.12의 explanation.details를 보험사별로 그대로 출력
        - 문장 수정 금지
        - 요약 금지
        - 의미 강조 금지
        """
        block_lines = []
        block_lines.append("[보험사별 상세 설명]")
        block_lines.append("")

        for detail in result.explanation.details:
            # Insurer header
            customer_label = self.PRIME_STATE_LABELS.get(detail.prime_state, detail.prime_state)
            block_lines.append(f"▶ {detail.insurer}")
            block_lines.append("")
            block_lines.append(f"판단 결과: {customer_label}")
            block_lines.append("")
            block_lines.append("사유:")

            # Explanation text (IMMUTABLE)
            explanation_lines = detail.explanation_text.split('\n')
            for line in explanation_lines:
                if line.strip():
                    block_lines.append(line)

            block_lines.append("")
            block_lines.append("-" * 80)
            block_lines.append("")

        return "\n".join(block_lines)

    def _validate_no_forbidden_phrases(self, formatted_response: str):
        """
        Validate that formatted response contains no forbidden phrases.

        If any forbidden phrase is found, raise error (HARD BAN).
        """
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase in formatted_response:
                raise ValueError(
                    f"FORBIDDEN PHRASE DETECTED: '{phrase}'\n"
                    f"Customer response formatting FAILED.\n"
                    f"Constitution violation: STEP 4.0 must not use forbidden phrases."
                )

    def print_customer_response(self, result: ExplainedComparisonResult, coverage_query: str):
        """
        Print customer-friendly response.

        Args:
            result: STEP 3.13 output
            coverage_query: Original coverage query
        """
        print("\n" + "=" * 80)
        print("STEP 4.0: CUSTOMER RESPONSE (고객용 출력)")
        print("=" * 80)
        print("")

        formatted_response = self.format(result, coverage_query)
        print(formatted_response)

        print("=" * 80)
        print("✅ Customer response formatting complete (STEP 4.0)")
        print("=" * 80)


def main():
    """Demo usage with STEP 3.13 queries"""
    # Initialize pipeline + formatter
    pipeline = QueryPipeline()
    formatter = CustomerResponseFormatter()

    # Sample queries
    queries = [
        "삼성과 한화 암진단비 비교해줘",
        "KB 롯데 뇌졸중진단비 보여줘",
    ]

    for query in queries:
        print("\n\n" + "=" * 100)
        print(f"USER QUERY: {query}")
        print("=" * 100)

        # STEP 3.13: Execute pipeline (STEP 3.11 + STEP 3.12)
        result = pipeline.process(query)

        # STEP 4.0: Format for customer
        formatter.print_customer_response(
            result=result,
            coverage_query=query
        )


if __name__ == "__main__":
    main()
