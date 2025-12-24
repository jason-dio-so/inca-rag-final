"""
Multi-party comparison logic (STEP 8)

Purpose: Handle 3+ insurer disease group overlap detection and comparison
"""
from .overlap import (
    GroupOverlapState,
    detect_pairwise_overlap,
    aggregate_multi_party_overlap
)
from .explainer import (
    ComparisonReason,
    InsurerGroupDetail,
    generate_comparison_reason
)

__all__ = [
    'GroupOverlapState',
    'detect_pairwise_overlap',
    'aggregate_multi_party_overlap',
    'ComparisonReason',
    'InsurerGroupDetail',
    'generate_comparison_reason',
]
