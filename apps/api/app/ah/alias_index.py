"""
Alias Index: Excel → (normalized_alias → canonical_coverage_code[])

Constitutional Principles:
1. Excel is the SSOT for alias → canonical mapping
2. Index is built deterministically (no LLM)
3. One normalized alias may map to multiple canonical codes (over-recall acceptable)
4. Cancer-related coverages have special expansion rules
"""

import pandas as pd
from typing import Dict, List, Set, Optional
from collections import defaultdict
from pathlib import Path

from .alias_normalizer import AliasNormalizer


class AliasIndex:
    """
    Excel-based alias index for Query → Canonical Code resolution.

    Design:
    - normalized_alias → Set[canonical_coverage_code]
    - Cancer guardrail: cancer queries expand to full cancer group
    - Insurer-agnostic (one alias may appear across multiple insurers)
    """

    def __init__(self):
        self.index: Dict[str, Set[str]] = defaultdict(set)
        self.canonical_to_display: Dict[str, str] = {}
        self.cancer_canonical_codes: Set[str] = set()
        self._loaded = False

    def load_from_excel(self, excel_path: Path) -> None:
        """
        Load alias index from Excel.

        Expected columns:
        - ins_cd: insurer code (N01, N02, ...)
        - 보험사명: insurer display name
        - cre_cvr_cd: canonical coverage code (SSOT)
        - 신정원코드명: canonical display name
        - 담보명(가입설계서): raw coverage name (alias)
        """
        df = pd.read_excel(excel_path)

        # Validate required columns
        required_cols = ['cre_cvr_cd', '신정원코드명', '담보명(가입설계서)']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns in Excel: {missing}")

        # Build index
        for _, row in df.iterrows():
            canonical_code = str(row['cre_cvr_cd']).strip()
            canonical_display = str(row['신정원코드명']).strip()
            raw_alias = str(row['담보명(가입설계서)']).strip()

            if not canonical_code or canonical_code == 'nan':
                continue

            # Normalize alias
            normalized_alias = AliasNormalizer.normalize(raw_alias)

            if not normalized_alias:
                continue

            # Add to index
            self.index[normalized_alias].add(canonical_code)

            # Store canonical display name
            if canonical_code not in self.canonical_to_display:
                self.canonical_to_display[canonical_code] = canonical_display

            # Detect cancer-related canonical codes
            if self._is_cancer_code(canonical_code, canonical_display):
                self.cancer_canonical_codes.add(canonical_code)

        self._loaded = True

    def _is_cancer_code(self, code: str, display: str) -> bool:
        """
        Detect if canonical code is cancer-related.

        Criteria:
        - Code contains 'A42' or 'A52' or 'A62' or 'A96' (cancer domains)
        - Display contains '암'
        """
        cancer_code_prefixes = ['A42', 'A52', 'A62', 'A96']
        if any(code.startswith(prefix) for prefix in cancer_code_prefixes):
            return True
        if '암' in display:
            return True
        return False

    def resolve_query(self, query: str, apply_cancer_guardrail: bool = True) -> List[str]:
        """
        Resolve query to canonical coverage codes.

        Args:
            query: User query (natural language coverage name)
            apply_cancer_guardrail: If True, expand cancer queries to full cancer group

        Returns:
            List of canonical coverage codes (may be empty if unmapped)

        Logic:
        1. Normalize query
        2. Lookup in index
        3. If cancer query + guardrail enabled → expand to all cancer codes
        4. Return deduplicated list
        """
        if not self._loaded:
            raise RuntimeError("AliasIndex not loaded. Call load_from_excel() first.")

        # Normalize query
        normalized_query = AliasNormalizer.normalize(query)

        if not normalized_query:
            return []

        # Direct lookup
        canonical_codes = set(self.index.get(normalized_query, set()))

        # Cancer guardrail
        if apply_cancer_guardrail and self._is_cancer_query(query, normalized_query):
            canonical_codes.update(self.cancer_canonical_codes)

        return sorted(canonical_codes)

    def _is_cancer_query(self, original_query: str, normalized_query: str) -> bool:
        """
        Detect if query is cancer-related.

        Cancer guardrail triggers:
        - Query contains '암진단', '암 진단', '일반암', '유사암', etc.
        """
        cancer_keywords = [
            '암진단',
            '암 진단',
            '일반암',
            '유사암',
            '제자리암',
            '경계성종양',
            '기타피부암',
            '갑상선암',
        ]

        for keyword in cancer_keywords:
            if keyword.replace(' ', '') in normalized_query:
                return True

        return False

    def get_display_name(self, canonical_code: str) -> Optional[str]:
        """
        Get canonical display name for a canonical code.
        """
        return self.canonical_to_display.get(canonical_code)

    def get_stats(self) -> Dict[str, int]:
        """
        Get index statistics.
        """
        return {
            "total_aliases": len(self.index),
            "total_canonical_codes": len(self.canonical_to_display),
            "cancer_canonical_codes": len(self.cancer_canonical_codes),
        }


# Singleton instance
_GLOBAL_ALIAS_INDEX: Optional[AliasIndex] = None


def get_alias_index() -> AliasIndex:
    """
    Get global singleton AliasIndex instance.

    Lazy-loads from Excel on first access.
    """
    global _GLOBAL_ALIAS_INDEX

    if _GLOBAL_ALIAS_INDEX is None:
        _GLOBAL_ALIAS_INDEX = AliasIndex()

        # Default Excel path
        excel_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "담보명mapping자료.xlsx"

        if not excel_path.exists():
            raise FileNotFoundError(f"Excel mapping file not found: {excel_path}")

        _GLOBAL_ALIAS_INDEX.load_from_excel(excel_path)

    return _GLOBAL_ALIAS_INDEX
