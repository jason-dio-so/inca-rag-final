"""
Multi-party comparison logic (STEP 8 + STEP 9)

Purpose: Handle 3+ insurer disease group overlap detection and comparison

STEP 8: Multi-party overlap detection + explainable reasons
STEP 9: Structured comparison response (가입설계서 중심)
"""
from .overlap import (
    GroupOverlapState,
    InsurerDiseaseScope,
    detect_pairwise_overlap,
    aggregate_multi_party_overlap
)
from .explainer import (
    ComparisonReason,
    InsurerGroupDetail,
    generate_comparison_reason
)
from .response import (
    ComparisonResponse,
    InsurerDiseaseScopeResponse,
    InsurerEvidence,
    generate_comparison_response,
    validate_comparison_response
)

__all__ = [
    # STEP 8: Overlap detection
    'GroupOverlapState',
    'InsurerDiseaseScope',
    'detect_pairwise_overlap',
    'aggregate_multi_party_overlap',
    # STEP 8: Explainable reasons
    'ComparisonReason',
    'InsurerGroupDetail',
    'generate_comparison_reason',
    # STEP 9: Structured response
    'ComparisonResponse',
    'InsurerDiseaseScopeResponse',
    'InsurerEvidence',
    'generate_comparison_response',
    'validate_comparison_response',
]
