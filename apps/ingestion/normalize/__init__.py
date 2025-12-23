"""
Normalize stage: Map coverage names to coverage_standard codes.
"""

from .normalizer import normalize_coverage_aliases, normalize_all_coverages

__all__ = ["normalize_coverage_aliases", "normalize_all_coverages"]
