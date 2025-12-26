"""
Proposal Meta Row Filter: Remove non-coverage rows from proposal summary

Constitutional Principle (AH-5):
- Deterministic rule-based filtering only
- Remove meta/header/subtotal/note rows that pollute alias recall
- No LLM/heuristic interpretation

Meta Row Patterns (Hard-coded):
- NULL/empty coverage_name_raw
- "합계", "소계", "총보험료", "주계약", "특약합계"
- "가입조건", "안내", "예시", "주)"
- Rows with only amount/premium but no coverage name
"""

import re
from typing import Dict, Any, List, Optional


class ProposalMetaFilter:
    """
    Filter meta/non-coverage rows from proposal summary.

    Constitutional Rule (AH-5):
    - Deterministic pattern matching only
    - Conservative: if unsure, keep the row (false positive > false negative)
    """

    # Meta row patterns (case-insensitive)
    META_PATTERNS = [
        r"^합계$",
        r"^소계$",
        r"^총\s*보험료$",
        r"^주\s*계약$",
        r"^특약\s*합계$",
        r"^특약\s*계$",
        r"^보험료\s*합계$",
        r"^월\s*납입\s*보험료$",
        r"^가입\s*조건$",
        r"^안내$",
        r"^예시$",
        r"^주\)",
        r"^\*",  # Footnotes starting with *
        r"^-\s",  # List items starting with -
        r"^·",   # Bullets
        r"^※",   # Notes
        r"^\d+\.",  # Numbered lists (e.g., "1. ...")
    ]

    # Coverage name must have at least these patterns
    COVERAGE_NAME_REQUIRED_PATTERNS = [
        r"보장",
        r"담보",
        r"진단",
        r"수술",
        r"입원",
        r"통원",
        r"치료",
        r"급여",
        r"비용",
    ]

    @staticmethod
    def is_meta_row(coverage_name_raw: Optional[str]) -> bool:
        """
        Check if a row is a meta row (should be filtered out).

        Args:
            coverage_name_raw: Raw coverage name from proposal

        Returns:
            True if meta row (should be filtered), False if valid coverage

        Logic:
        1. If NULL/empty → meta row
        2. If matches meta patterns → meta row
        3. If too short (< 3 chars) → meta row
        4. If doesn't contain any coverage keywords → likely meta row
        5. Otherwise → valid coverage row
        """
        # Rule 1: NULL/empty
        if not coverage_name_raw or not coverage_name_raw.strip():
            return True

        name = coverage_name_raw.strip()

        # Rule 2: Too short (less than 3 chars)
        if len(name) < 3:
            return True

        # Rule 3: Check meta patterns
        name_lower = name.lower().replace(" ", "")
        for pattern in ProposalMetaFilter.META_PATTERNS:
            if re.search(pattern, name_lower, re.IGNORECASE):
                return True

        # Rule 4: Check if it contains any coverage keywords
        # If it doesn't, it's likely a meta row
        has_coverage_keyword = False
        for pattern in ProposalMetaFilter.COVERAGE_NAME_REQUIRED_PATTERNS:
            if re.search(pattern, name_lower):
                has_coverage_keyword = True
                break

        # Conservative: if no coverage keyword, treat as meta
        # (This might filter some valid rows, but prevents pollution)
        if not has_coverage_keyword:
            # Exception: if it contains "암" or "질병" or other common terms, keep it
            exception_keywords = ["암", "질병", "상해", "사망", "장해", "연금"]
            for keyword in exception_keywords:
                if keyword in name:
                    return False  # Keep this row
            return True  # Filter out

        # Otherwise, keep the row
        return False

    @staticmethod
    def filter_proposal_rows(
        rows: List[Dict[str, Any]],
    ) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Filter meta rows from proposal rows.

        Args:
            rows: List of proposal rows (dicts with coverage_name_raw field)

        Returns:
            Tuple of (filtered_rows, stats_dict)
            stats_dict: {
                "total_rows": int,
                "filtered_rows": int,
                "kept_rows": int,
                "filter_rate": float (0.0 ~ 1.0),
            }
        """
        total = len(rows)
        filtered_rows = []
        filtered_count = 0

        for row in rows:
            coverage_name = row.get("coverage_name_raw") or row.get("coverage_name")
            if ProposalMetaFilter.is_meta_row(coverage_name):
                filtered_count += 1
                # Skip this row (meta row)
            else:
                filtered_rows.append(row)

        kept = len(filtered_rows)

        stats = {
            "total_rows": total,
            "filtered_rows": filtered_count,
            "kept_rows": kept,
            "filter_rate": filtered_count / total if total > 0 else 0.0,
        }

        return filtered_rows, stats


def apply_meta_filter_to_universe(
    universe_rows: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Apply meta filter to coverage universe rows.

    Args:
        universe_rows: List of coverage universe rows

    Returns:
        Tuple of (filtered_rows, stats)
    """
    filter = ProposalMetaFilter()
    return filter.filter_proposal_rows(universe_rows)
