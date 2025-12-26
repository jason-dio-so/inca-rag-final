"""
Alias Normalizer: Query/Raw name → Normalized form

Constitutional Rules (Non-Negotiable):
1. Normalization is deterministic (no LLM)
2. All whitespace variations must collapse to same form
3. Parentheses are stripped
4. Conditional clauses (유사암 제외, 1년50% etc.) are preserved in metadata but removed from match key
5. Roman numerals (Ⅰ,Ⅱ,Ⅲ) are removed
6. Arabic numerals in version/suffix context are removed
"""

import re
from typing import Dict, Any


class AliasNormalizer:
    """
    Deterministic alias normalization for Query → Canonical Code resolution.

    Design Principles:
    - High recall priority (over-match acceptable, under-match forbidden)
    - Repeatable normalization across Query/Excel/Universe
    - No LLM inference
    """

    # Patterns for conditional clauses to extract (then remove from match key)
    CONDITIONAL_PATTERNS = [
        r'\(유사암\s*제외\)',
        r'\(특정암\s*제외\)',
        r'\(갑상선암\s*제외\)',
        r'\(기타피부암\s*제외\)',
        r'\(\d+년\s*\d+%\)',
        r'\(\d+년\s*감액\)',
        r'\(최초\s*\d+회한\)',
        r'\(연간\s*\d+회한\)',
        r'\(\d+일.*?\d+일\)',
        r'\(요양.*?제외\)',
        r'\(갱신형\)',
    ]

    # Patterns for version markers to remove
    VERSION_PATTERNS = [
        r'[ⅠⅡⅢⅣⅤ]+',  # Roman numerals
        r'\d+대',  # N대 (5대고액, 10대고액 etc.)
    ]

    @staticmethod
    def normalize(text: str) -> str:
        """
        Main normalization function.

        Returns normalized match key (for lookup).
        """
        if not text or not isinstance(text, str):
            return ""

        # 1. Strip leading/trailing whitespace
        result = text.strip()

        # 2. Remove all parentheses and their contents
        # (We extract conditionals first if needed, but for match key we remove all)
        result = re.sub(r'\([^)]*\)', '', result)
        result = re.sub(r'\[[^\]]*\]', '', result)

        # 3. Remove version markers (Roman numerals, N대)
        for pattern in AliasNormalizer.VERSION_PATTERNS:
            result = re.sub(pattern, '', result)

        # 4. Collapse all whitespace (including no-break spaces)
        result = re.sub(r'\s+', '', result)

        # 5. Convert to lowercase for case-insensitive matching
        # (Korean doesn't have case, but some Latin chars might appear)
        result = result.lower()

        # 6. Remove common suffixes (담보, 비, 금)
        # Only if they are truly suffix (avoid removing from middle)
        # For now, we keep them to avoid over-normalization

        return result

    @staticmethod
    def normalize_with_metadata(text: str) -> Dict[str, Any]:
        """
        Normalize and extract metadata (conditionals, versions).

        Returns:
        {
            "match_key": normalized string for lookup,
            "original": original text,
            "conditionals": list of extracted conditional clauses,
            "has_exclusion": bool,
            "has_payout_rate": bool,
        }
        """
        if not text or not isinstance(text, str):
            return {
                "match_key": "",
                "original": "",
                "conditionals": [],
                "has_exclusion": False,
                "has_payout_rate": False,
            }

        original = text.strip()
        conditionals = []

        # Extract conditionals before removal
        for pattern in AliasNormalizer.CONDITIONAL_PATTERNS:
            matches = re.findall(pattern, original)
            conditionals.extend(matches)

        # Determine flags
        has_exclusion = any('제외' in c for c in conditionals)
        has_payout_rate = any('%' in c for c in conditionals)

        # Generate match key
        match_key = AliasNormalizer.normalize(original)

        return {
            "match_key": match_key,
            "original": original,
            "conditionals": conditionals,
            "has_exclusion": has_exclusion,
            "has_payout_rate": has_payout_rate,
        }

    @staticmethod
    def normalize_cancer_query(query: str) -> str:
        """
        Special normalization for cancer-related queries.

        Rules:
        - "암진단비" / "일반암진단비" / "암 진단비" → "암진단비"
        - All map to same canonical base form
        """
        normalized = AliasNormalizer.normalize(query)

        # Cancer-specific aliases
        cancer_aliases = {
            "일반암진단비": "암진단비",
            "암진단": "암진단비",
            "암진단금": "암진단비",
        }

        for alias, canonical_form in cancer_aliases.items():
            if normalized == alias.replace(' ', '').lower():
                return canonical_form

        return normalized
