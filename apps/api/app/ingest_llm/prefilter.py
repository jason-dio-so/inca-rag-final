"""
STEP 6-B: Prefilter for LLM Candidate Generation

Purpose: Select chunks likely to contain coverage entities (reduce LLM cost).

Constitutional Principles:
- Cost optimization via intelligent filtering
- No false negatives (err on side of calling LLM)
- Deterministic rules (reproducible results)
"""
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ChunkPrefilter:
    """
    Prefilter to determine if chunk should be sent to LLM for candidate generation.

    Strategy:
    - Pattern-based heuristics (fast, cheap)
    - doc_type priority (약관 > 사업방법서 > 상품요약서)
    - Minimum length requirements
    - Keyword presence (coverage-related terms)
    """

    # Coverage-related keywords (Korean)
    COVERAGE_KEYWORDS = [
        "진단비", "수술비", "입원비", "통원비",
        "암", "뇌", "심장", "질병", "상해",
        "보장", "지급", "보험금",
        "면책", "감액", "제외",
        "가입", "계약", "특약",
    ]

    # Condition-related keywords
    CONDITION_KEYWORDS = [
        "기간", "일", "개월", "년",
        "경우", "때", "시",
        "이상", "이하", "미만", "초과",
        "제외", "포함", "한정",
    ]

    # Amount-related patterns
    AMOUNT_PATTERNS = [
        r'\d{1,3}(?:,\d{3})*원',  # 1,000원, 500,000원
        r'\d+만원',  # 500만원
        r'\d+억',  # 1억
        r'\d+천만원',  # 3천만원
    ]

    # Doc type priority (higher = more likely to contain valuable entities)
    DOC_TYPE_PRIORITY = {
        "약관": 10,
        "사업방법서": 8,
        "상품요약서": 6,
        "가입설계서": 4,
    }

    def __init__(
        self,
        min_chunk_length: int = 50,
        min_keyword_count: int = 1,
        enable_doc_type_filter: bool = True,
        allowed_doc_types: Optional[list[str]] = None
    ):
        """
        Initialize prefilter with configuration.

        Args:
            min_chunk_length: Minimum characters (default: 50)
            min_keyword_count: Minimum coverage/condition keywords (default: 1)
            enable_doc_type_filter: Whether to filter by doc_type (default: True)
            allowed_doc_types: Whitelist of doc_types (default: ["약관"])
        """
        self.min_chunk_length = min_chunk_length
        self.min_keyword_count = min_keyword_count
        self.enable_doc_type_filter = enable_doc_type_filter
        self.allowed_doc_types = allowed_doc_types or ["약관"]

        # Compile amount patterns
        self.amount_regex = re.compile('|'.join(self.AMOUNT_PATTERNS))

    def should_process(
        self,
        chunk_content: str,
        doc_type: Optional[str] = None,
        is_synthetic: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if chunk should be processed by LLM.

        Args:
            chunk_content: Chunk text content
            doc_type: Document type (e.g., "약관", "사업방법서")
            is_synthetic: Whether chunk is synthetic (always reject)

        Returns:
            (should_process: bool, reason: Optional[str])

        Constitutional Guarantees:
        - Synthetic chunks NEVER processed (compare-axis forbidden)
        - False negatives minimized (low threshold)
        """
        # Rule 1: Reject synthetic chunks (constitutional rule)
        if is_synthetic:
            return False, "synthetic_chunk_forbidden"

        # Rule 2: Minimum length
        if len(chunk_content) < self.min_chunk_length:
            return False, f"too_short_{len(chunk_content)}_chars"

        # Rule 3: Doc type filter (cost optimization)
        if self.enable_doc_type_filter:
            if doc_type not in self.allowed_doc_types:
                return False, f"doc_type_{doc_type}_not_in_whitelist"

        # Rule 4: Keyword presence
        keyword_count = self._count_keywords(chunk_content)
        if keyword_count < self.min_keyword_count:
            return False, f"insufficient_keywords_{keyword_count}"

        # Rule 5: At least one pattern match (coverage OR condition OR amount)
        has_coverage_keywords = any(kw in chunk_content for kw in self.COVERAGE_KEYWORDS)
        has_condition_keywords = any(kw in chunk_content for kw in self.CONDITION_KEYWORDS)
        has_amount_pattern = bool(self.amount_regex.search(chunk_content))

        if not (has_coverage_keywords or has_condition_keywords or has_amount_pattern):
            return False, "no_coverage_patterns"

        # Passed all filters
        return True, None

    def _count_keywords(self, text: str) -> int:
        """Count coverage + condition keywords in text"""
        count = 0
        all_keywords = self.COVERAGE_KEYWORDS + self.CONDITION_KEYWORDS
        for keyword in all_keywords:
            count += text.count(keyword)
        return count

    def get_priority(self, doc_type: Optional[str] = None) -> int:
        """
        Get priority score for doc_type (higher = more important).

        Used for batching/scheduling LLM calls.
        """
        if doc_type is None:
            return 0
        return self.DOC_TYPE_PRIORITY.get(doc_type, 0)

    def estimate_cost_reduction(self, total_chunks: int, passed_count: int) -> dict:
        """
        Estimate cost reduction from prefiltering.

        Args:
            total_chunks: Total chunks in dataset
            passed_count: Chunks that passed prefilter

        Returns:
            Dictionary with cost reduction metrics
        """
        filter_rate = 1 - (passed_count / total_chunks) if total_chunks > 0 else 0
        cost_per_chunk = 0.00725  # USD (from design doc)
        cost_without_filter = total_chunks * cost_per_chunk
        cost_with_filter = passed_count * cost_per_chunk
        savings = cost_without_filter - cost_with_filter

        return {
            "total_chunks": total_chunks,
            "passed_count": passed_count,
            "rejected_count": total_chunks - passed_count,
            "filter_rate": filter_rate,
            "cost_without_filter_usd": cost_without_filter,
            "cost_with_filter_usd": cost_with_filter,
            "cost_savings_usd": savings,
            "savings_percentage": filter_rate * 100
        }


# Default prefilter instance (약관 only)
default_prefilter = ChunkPrefilter(
    min_chunk_length=50,
    min_keyword_count=1,
    enable_doc_type_filter=True,
    allowed_doc_types=["약관"]
)
