#!/usr/bin/env python3
"""
STEP 3.13 FINAL: User Query → PRIME Comparison Pipeline

Purpose:
- Connect natural language queries to STEP 3.11 → STEP 3.12 pipeline
- Query interpretation + routing ONLY
- NO comparison logic (already exists)

Rules:
✅ Deterministic query parsing
✅ Single query → Single comparison
✅ Automatic STEP 3.11 → STEP 3.12 connection
❌ No semantic inference
❌ No coverage expansion
❌ No "similar coverage"
❌ No recommendation intent interpretation

This is the LAST step before:
- UI
- Customer response formatting
- Recommendations
- Policy expansion
- Shinjeongwon enhancement
"""

import re
from dataclasses import dataclass
from typing import List, Optional
import sys

sys.path.insert(0, 'scripts')
from step311_comparison_engine import ProposalFactComparisonEngine
from step312_explanation_layer import PRIMEExplanationLayer, ExplainedComparisonResult


@dataclass
class ParsedQuery:
    """Parsed user query"""
    raw_query: str
    normalized_coverage_keyword: str
    target_insurers: List[str]
    execution_plan: dict


class QueryPipeline:
    """
    STEP 3.13: User Query → PRIME Comparison Pipeline

    This orchestrator connects user queries to the comparison engine.
    """

    # Insurer name mappings (Korean → System Code)
    INSURER_MAPPINGS = {
        '삼성': 'SAMSUNG',
        '한화': 'HANWHA',
        '롯데': 'LOTTE',
        '메리츠': 'MERITZ',
        'kb': 'KB',
        'KB': 'KB',
        '현대': 'HYUNDAI',
        '흥국': 'HEUNGKUK',
        'db': 'DB',
        'DB': 'DB',
    }

    def __init__(self):
        """Initialize pipeline components"""
        self.comparison_engine = ProposalFactComparisonEngine()
        self.explanation_layer = PRIMEExplanationLayer()

        print("Query Pipeline initialized")
        print("  Comparison Engine: STEP 3.11")
        print("  Explanation Layer: STEP 3.12")

    def process(self, user_query: str) -> ExplainedComparisonResult:
        """
        Main pipeline entry point.

        Args:
            user_query: Natural language query from user

        Returns:
            ExplainedComparisonResult (STEP 3.11 + STEP 3.12)

        Example:
            "삼성과 한화 암진단비 비교해줘"
            → coverage: "암진단비"
            → insurers: ["SAMSUNG", "HANWHA"]
            → STEP 3.11 → STEP 3.12
        """
        print("=" * 80)
        print("STEP 3.13: Query Pipeline")
        print("=" * 80)
        print(f"User Query: {user_query}")

        # Step 1: Parse query
        print("\n[1] Parsing query...")
        parsed = self._parse_query(user_query)

        print(f"  Normalized coverage: {parsed.normalized_coverage_keyword}")
        print(f"  Target insurers: {parsed.target_insurers}")

        # Step 2: Execute STEP 3.11 (Comparison)
        print("\n[2] Executing STEP 3.11 (Comparison Engine)...")
        comparison_result = self.comparison_engine.compare(
            insurers=parsed.target_insurers,
            coverage_query=parsed.normalized_coverage_keyword
        )

        # Step 3: Execute STEP 3.12 (Explanation)
        print("\n[3] Executing STEP 3.12 (Explanation Layer)...")
        explained_result = self.explanation_layer.explain(
            comparison_result=comparison_result,
            coverage_query=parsed.normalized_coverage_keyword
        )

        print("\n✅ Pipeline complete")
        return explained_result

    def _parse_query(self, user_query: str) -> ParsedQuery:
        """
        Parse user query into structured format.

        Allowed:
        - Insurer name extraction
        - Coverage keyword extraction
        - Whitespace normalization

        Forbidden:
        - Semantic inference
        - Coverage expansion
        - Intent interpretation
        """
        # Extract insurers
        insurers = self._extract_insurers(user_query)

        # Extract coverage keyword
        coverage = self._extract_coverage_keyword(user_query, insurers)

        # Normalize coverage keyword (whitespace/case only)
        normalized_coverage = self._normalize_coverage_keyword(coverage)

        parsed = ParsedQuery(
            raw_query=user_query,
            normalized_coverage_keyword=normalized_coverage,
            target_insurers=insurers,
            execution_plan={
                'comparison_engine': 'STEP_3.11',
                'explanation_layer': 'STEP_3.12'
            }
        )

        return parsed

    def _extract_insurers(self, query: str) -> List[str]:
        """
        Extract insurer names from query.

        Rules:
        - Match known insurer names
        - Return system codes (e.g., "삼성" → "SAMSUNG")
        - If no insurers found, default to all available
        """
        insurers = []

        for korean_name, system_code in self.INSURER_MAPPINGS.items():
            if korean_name in query:
                if system_code not in insurers:
                    insurers.append(system_code)

        # If no insurers specified, use default set
        if not insurers:
            # Default: major insurers
            insurers = ['SAMSUNG', 'HANWHA', 'KB']

        return insurers

    def _extract_coverage_keyword(self, query: str, insurers: List[str]) -> str:
        """
        Extract coverage keyword from query.

        Rules:
        - Remove insurer names
        - Remove common words (비교, 보여줘, etc.)
        - Keep coverage name only

        Forbidden:
        - Semantic interpretation
        - Synonym expansion
        """
        # Remove insurer names
        coverage = query
        for korean_name in self.INSURER_MAPPINGS.keys():
            coverage = coverage.replace(korean_name, '')

        # Remove common action words (deterministic list)
        # Order matters: longer phrases first
        common_words = [
            '비교해주세요', '비교해줘', '보여주세요', '보여줘', '알려주세요', '알려줘',
            '비교해', '비교', '보여', '알려', '해줘', '해주세요',
            '와', '과', '랑', '하고', '의', '를', '을', '에서', '에'
        ]

        for word in common_words:
            coverage = coverage.replace(word, ' ')

        # Clean whitespace
        coverage = ' '.join(coverage.split())

        return coverage.strip()

    def _normalize_coverage_keyword(self, coverage: str) -> str:
        """
        Normalize coverage keyword.

        Allowed:
        - Strip whitespace
        - Collapse multiple spaces

        NOT allowed:
        - Remove special characters (meaning-changing)
        - Synonym expansion
        """
        normalized = coverage.strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def print_result(self, result: ExplainedComparisonResult):
        """
        Print pipeline result.

        This delegates to STEP 3.12's print method.
        """
        self.explanation_layer.print_explained_result(result)


def main():
    """Demo usage with natural language queries"""
    pipeline = QueryPipeline()

    # Sample queries
    queries = [
        "삼성과 한화 암진단비 비교해줘",
        "KB 롯데 뇌졸중진단비 보여줘",
        "암 진단비",  # No insurers specified → default
    ]

    for query in queries:
        print("\n\n" + "=" * 80)
        print(f"USER QUERY: {query}")
        print("=" * 80)

        result = pipeline.process(query)
        pipeline.print_result(result)


if __name__ == "__main__":
    main()
