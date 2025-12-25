"""
Compare API Runtime Contract Registry

This module contains SSOT (Single Source of Truth) for all allowed
comparison_result, next_action, and ux_message codes in the Compare API.

DO NOT duplicate these definitions elsewhere.
All code validation must reference this registry.
"""

from .compare_codes import (
    ALLOWED_COMPARISON_RESULTS,
    ALLOWED_NEXT_ACTIONS,
    validate_comparison_result,
    validate_next_action,
    validate_compare_response,
)
from .ux_message_codes import (
    ALLOWED_UX_MESSAGE_CODES,
    validate_ux_message_code,
    validate_ux_message_code_naming,
)

__all__ = [
    "ALLOWED_COMPARISON_RESULTS",
    "ALLOWED_NEXT_ACTIONS",
    "ALLOWED_UX_MESSAGE_CODES",
    "validate_comparison_result",
    "validate_next_action",
    "validate_compare_response",
    "validate_ux_message_code",
    "validate_ux_message_code_naming",
]
