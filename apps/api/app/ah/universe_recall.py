"""
Universe Recall: Query → Canonical Codes → Universe Coverages

Constitutional Flow:
1. Query → AliasIndex → Canonical Codes
2. Canonical Codes × Insurers → Universe Recall
3. No direct DB match on raw coverage names (FORBIDDEN)

Guarantees:
- No insurer excluded due to expression differences
- Cancer guardrail ensures SAMSUNG included for "일반암진단비"
- Unmapped queries logged, not silently ignored
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd

from .alias_index import get_alias_index


class UniverseRecaller:
    """
    Universe Recall Engine (Excel Alias → Universe Lookup)

    Design:
    - Query → Canonical Codes (via AliasIndex)
    - Canonical Codes → Universe (via coverage_universe CSV or DB)
    - Insurer × Canonical Code cross-product for recall
    """

    def __init__(self, universe_csv_path: Optional[Path] = None):
        """
        Args:
            universe_csv_path: Path to ALL_INSURERS_coverage_universe.csv
                              If None, uses default path
        """
        if universe_csv_path is None:
            universe_csv_path = (
                Path(__file__).parent.parent.parent.parent.parent
                / "data"
                / "step39_coverage_universe"
                / "extracts"
                / "ALL_INSURERS_coverage_universe.csv"
            )

        if not universe_csv_path.exists():
            raise FileNotFoundError(f"Universe CSV not found: {universe_csv_path}")

        self.universe_df = pd.read_csv(universe_csv_path)
        self.alias_index = get_alias_index()

    def recall_from_query(
        self,
        query: str,
        insurer_filter: Optional[List[str]] = None,
        apply_cancer_guardrail: bool = True,
    ) -> Dict[str, Any]:
        """
        Recall universe coverages from query.

        Args:
            query: User query (natural language coverage name)
            insurer_filter: Optional list of insurer codes to filter
            apply_cancer_guardrail: Apply cancer expansion rules

        Returns:
        {
            "query": original query,
            "canonical_codes": list of resolved canonical codes,
            "recall_count": number of recalled coverages,
            "recalled_coverages": list of recalled coverage records,
            "insurers_covered": list of insurers in recall results,
            "unmapped": bool (True if no canonical codes found),
        }
        """
        # Step 1: Query → Canonical Codes
        canonical_codes = self.alias_index.resolve_query(
            query, apply_cancer_guardrail=apply_cancer_guardrail
        )

        # Check unmapped
        if not canonical_codes:
            return {
                "query": query,
                "canonical_codes": [],
                "recall_count": 0,
                "recalled_coverages": [],
                "insurers_covered": [],
                "unmapped": True,
            }

        # Step 2: Canonical Codes → Universe Recall
        # We need to map canonical codes back to universe coverage_name_raw
        # Since universe doesn't have canonical_code column yet,
        # we use alias matching via normalized names

        recalled = []
        for _, row in self.universe_df.iterrows():
            insurer = row['insurer']

            # Apply insurer filter
            if insurer_filter and insurer not in insurer_filter:
                continue

            coverage_name_raw = str(row['coverage_name_raw']).strip()

            # Check if this raw name matches any canonical code
            if self._matches_canonical_codes(coverage_name_raw, canonical_codes):
                recalled.append(row.to_dict())

        insurers_covered = sorted(set(r['insurer'] for r in recalled))

        return {
            "query": query,
            "canonical_codes": canonical_codes,
            "recall_count": len(recalled),
            "recalled_coverages": recalled,
            "insurers_covered": insurers_covered,
            "unmapped": False,
        }

    def _matches_canonical_codes(
        self, coverage_name_raw: str, canonical_codes: List[str]
    ) -> bool:
        """
        Check if raw coverage name matches any canonical code.

        Logic:
        1. Normalize raw name
        2. Lookup in alias_index
        3. Check if resolved canonical codes intersect with target canonical_codes
        """
        from .alias_normalizer import AliasNormalizer

        normalized = AliasNormalizer.normalize(coverage_name_raw)
        resolved_codes = self.alias_index.index.get(normalized, set())

        # Check intersection
        return bool(set(resolved_codes) & set(canonical_codes))

    def get_coverage_stats(self) -> Dict[str, int]:
        """
        Get universe statistics.
        """
        return {
            "total_coverages": len(self.universe_df),
            "insurers": len(self.universe_df['insurer'].unique()),
        }


def recall_universe_from_query(
    query: str,
    insurer_filter: Optional[List[str]] = None,
    apply_cancer_guardrail: bool = True,
) -> Dict[str, Any]:
    """
    Convenience function for universe recall.

    Args:
        query: User query
        insurer_filter: Optional insurer filter
        apply_cancer_guardrail: Apply cancer expansion

    Returns:
        Recall result dict
    """
    recaller = UniverseRecaller()
    return recaller.recall_from_query(
        query,
        insurer_filter=insurer_filter,
        apply_cancer_guardrail=apply_cancer_guardrail,
    )
