"""
Compare API Runtime Contract Registry

This module contains SSOT (Single Source of Truth) for all allowed
comparison_result and next_action codes in the Compare API.

DO NOT duplicate these definitions elsewhere.
All code validation must reference this registry.
"""

from .compare_codes import (
    ALLOWED_COMPARISON_RESULTS,
    ALLOWED_NEXT_ACTIONS,
    validate_comparison_result,
    validate_next_action,
)

__all__ = [
    "ALLOWED_COMPARISON_RESULTS",
    "ALLOWED_NEXT_ACTIONS",
    "validate_comparison_result",
    "validate_next_action",
]
