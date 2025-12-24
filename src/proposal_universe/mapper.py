"""
Coverage Mapper

Purpose: Map insurer_coverage_name → canonical_coverage_code
Source: Excel (/data/담보명mapping자료.xlsx) ONLY

Constitution: No LLM, no similarity, no inference
Slot Schema v1.1.1: mapping_status required, canonical_coverage_code nullable
"""

import re
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import pandas as pd


class CoverageMapper:
    """
    Map coverage names to canonical codes using Excel source.

    Principles (Article I - Coverage Universe Lock):
    1. Excel is single source of truth
    2. No LLM-based inference
    3. No semantic similarity matching
    4. mapping_status always required
    5. canonical_coverage_code nullable (MAPPED only)
    """

    def __init__(self, excel_path: Path):
        """
        Initialize mapper with Excel source.

        Args:
            excel_path: Path to 담보명mapping자료.xlsx
        """
        self.excel_path = excel_path
        self.alias_map: Dict[str, str] = {}
        self.ambiguous_aliases: Dict[str, List[str]] = {}

        self._load_excel()

    def _load_excel(self):
        """
        Load Excel and build alias → canonical_code mapping.

        Expected Excel structure:
        - 담보명(가입설계서) (column): insurer-specific coverage names (alias)
        - cre_cvr_cd (column): 신정원 통일 코드 (canonical coverage code)
        """
        try:
            df = pd.read_excel(self.excel_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load Excel: {e}")

        # Validate required columns
        # Actual columns: ins_cd, 보험사명, cre_cvr_cd, 신정원코드명, 담보명(가입설계서)
        required = ['담보명(가입설계서)', 'cre_cvr_cd']
        if not all(col in df.columns for col in required):
            actual_cols = df.columns.tolist()
            raise ValueError(
                f"Excel must have columns: {required}\n"
                f"Actual columns: {actual_cols}"
            )

        # Build mapping
        for _, row in df.iterrows():
            alias = str(row['담보명(가입설계서)']).strip()
            canonical = str(row['cre_cvr_cd']).strip()

            # Normalize alias for lookup
            normalized_alias = self._normalize_alias(alias)

            # Check for ambiguity
            if normalized_alias in self.alias_map:
                # Ambiguous alias maps to multiple canonical codes
                if normalized_alias not in self.ambiguous_aliases:
                    self.ambiguous_aliases[normalized_alias] = [
                        self.alias_map[normalized_alias]
                    ]
                if canonical not in self.ambiguous_aliases[normalized_alias]:
                    self.ambiguous_aliases[normalized_alias].append(canonical)
            else:
                self.alias_map[normalized_alias] = canonical

        # Remove ambiguous from main map
        for alias in self.ambiguous_aliases:
            if alias in self.alias_map:
                del self.alias_map[alias]

    def _normalize_alias(self, alias: str) -> str:
        """
        Normalize alias for lookup matching.

        Same normalization as ProposalCoverageParser.
        """
        normalized = alias.strip()
        normalized = re.sub(r'\s+', '', normalized)
        normalized = re.sub(r'\(\s+', '(', normalized)
        normalized = re.sub(r'\s+\)', ')', normalized)

        return normalized

    def map(self, normalized_name: str, insurer_coverage_name: str) -> Dict:
        """
        Map coverage name to canonical code.

        Args:
            normalized_name: Normalized coverage name from universe
            insurer_coverage_name: Original coverage name (for evidence)

        Returns:
            Dict with:
                - mapping_status: MAPPED | UNMAPPED | AMBIGUOUS
                - canonical_coverage_code: str or None
                - mapping_evidence: Dict with lookup details
        """
        # Try exact match first
        if normalized_name in self.alias_map:
            return {
                'mapping_status': 'MAPPED',
                'canonical_coverage_code': self.alias_map[normalized_name],
                'mapping_evidence': {
                    'lookup_key': normalized_name,
                    'matched_alias': normalized_name,
                    'source': str(self.excel_path),
                    'match_type': 'exact',
                }
            }

        # Check if ambiguous
        if normalized_name in self.ambiguous_aliases:
            return {
                'mapping_status': 'AMBIGUOUS',
                'canonical_coverage_code': None,
                'mapping_evidence': {
                    'lookup_key': normalized_name,
                    'candidates': self.ambiguous_aliases[normalized_name],
                    'source': str(self.excel_path),
                    'reason': 'multiple_canonical_codes',
                }
            }

        # Try fuzzy match with parentheses removed
        base_name = self._remove_parentheses(normalized_name)
        if base_name in self.alias_map:
            return {
                'mapping_status': 'MAPPED',
                'canonical_coverage_code': self.alias_map[base_name],
                'mapping_evidence': {
                    'lookup_key': normalized_name,
                    'matched_alias': base_name,
                    'source': str(self.excel_path),
                    'match_type': 'parentheses_removed',
                }
            }

        # No match found
        return {
            'mapping_status': 'UNMAPPED',
            'canonical_coverage_code': None,
            'mapping_evidence': {
                'lookup_key': normalized_name,
                'source': str(self.excel_path),
                'reason': 'no_match_found',
                'insurer_coverage_name': insurer_coverage_name,
            }
        }

    def _remove_parentheses(self, name: str) -> str:
        """Remove all parenthetical content."""
        return re.sub(r'\([^)]*\)', '', name)

    def get_stats(self) -> Dict:
        """Get mapper statistics."""
        return {
            'total_aliases': len(self.alias_map),
            'ambiguous_aliases': len(self.ambiguous_aliases),
            'unique_canonical_codes': len(set(self.alias_map.values())),
        }
