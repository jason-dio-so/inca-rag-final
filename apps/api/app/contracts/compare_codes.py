"""
Compare API Code Registry (STEP 24)

SSOT for allowed comparison_result and next_action codes.

Constitutional Rules:
- These codes are part of the Runtime Contract (not just documentation)
- Adding/removing codes = breaking change (requires golden snapshot + CHANGELOG)
- Code validation MUST reference this registry (no hardcoded strings elsewhere)
- Text messages are NOT contracts - only codes are

Historical Context:
- STEP 16-22: Golden snapshots freeze semantic contract
- STEP 24: Enum codes freeze to prevent string drift
"""

from typing import Set


# ============================================================================
# comparison_result: Main comparison outcome category
# ============================================================================

ALLOWED_COMPARISON_RESULTS: Set[str] = {
    # Coverage successfully matched and comparable
    "comparable",

    # Coverage not mapped to canonical code (Excel mapping failed)
    "unmapped",

    # Coverage mapped but requires policy verification (e.g., disease_scope)
    "policy_required",

    # Query is outside coverage universe (STEP 6-C Universe Lock)
    "out_of_universe",
}

# Description mapping (for documentation only - NOT part of contract)
COMPARISON_RESULT_DESCRIPTIONS = {
    "comparable": {
        "ko": "비교 가능 (모든 핵심 정보 확정)",
        "en": "Comparable (all essential slots resolved)",
    },
    "unmapped": {
        "ko": "매핑 실패 (Excel에 없는 담보)",
        "en": "Unmapped (coverage not found in Excel mapping)",
    },
    "policy_required": {
        "ko": "약관 검증 필요 (질병 범위 등)",
        "en": "Policy verification required (e.g., disease scope)",
    },
    "out_of_universe": {
        "ko": "Universe 외부 (가입설계서에 없음)",
        "en": "Out of universe (not in proposal coverage universe)",
    },
}


# ============================================================================
# next_action: Recommended next step for UX/client
# ============================================================================

ALLOWED_NEXT_ACTIONS: Set[str] = {
    # Proceed to comparison (coverage A vs B)
    "COMPARE",

    # Request more information from user (unmapped/ambiguous)
    "REQUEST_MORE_INFO",

    # Verify against actual policy document (disease_scope, etc.)
    "VERIFY_POLICY",
}

# Description mapping (for documentation only - NOT part of contract)
NEXT_ACTION_DESCRIPTIONS = {
    "COMPARE": {
        "ko": "비교 진행 (A vs B 화면으로)",
        "en": "Proceed to comparison view (A vs B)",
    },
    "REQUEST_MORE_INFO": {
        "ko": "추가 정보 요청 (매핑 실패 또는 Universe 외부)",
        "en": "Request more information (unmapped or out-of-universe)",
    },
    "VERIFY_POLICY": {
        "ko": "약관 확인 필요 (질병 범위 등)",
        "en": "Verify against policy document (disease scope, etc.)",
    },
}


# ============================================================================
# Validation Functions (Runtime Guard)
# ============================================================================

def validate_comparison_result(code: str) -> None:
    """
    Validate comparison_result code against registry.

    Args:
        code: comparison_result value to validate

    Raises:
        ValueError: If code is not in ALLOWED_COMPARISON_RESULTS

    Usage:
        Call this BEFORE returning Compare API response.
        Fail-fast on unknown codes to prevent contract drift.
    """
    if code not in ALLOWED_COMPARISON_RESULTS:
        raise ValueError(
            f"Invalid comparison_result code: '{code}'\n"
            f"Allowed codes: {sorted(ALLOWED_COMPARISON_RESULTS)}\n"
            f"This is a STEP 24 contract violation.\n"
            f"Update apps/api/app/contracts/compare_codes.py if adding new codes."
        )


def validate_next_action(code: str) -> None:
    """
    Validate next_action code against registry.

    Args:
        code: next_action value to validate

    Raises:
        ValueError: If code is not in ALLOWED_NEXT_ACTIONS

    Usage:
        Call this BEFORE returning Compare API response.
        Fail-fast on unknown codes to prevent contract drift.
    """
    if code not in ALLOWED_NEXT_ACTIONS:
        raise ValueError(
            f"Invalid next_action code: '{code}'\n"
            f"Allowed codes: {sorted(ALLOWED_NEXT_ACTIONS)}\n"
            f"This is a STEP 24 contract violation.\n"
            f"Update apps/api/app/contracts/compare_codes.py if adding new codes."
        )


def validate_compare_response(comparison_result: str, next_action: str) -> None:
    """
    Validate both comparison_result and next_action codes.

    Args:
        comparison_result: comparison_result value to validate
        next_action: next_action value to validate

    Raises:
        ValueError: If either code is invalid

    Usage:
        Call this as final check before returning Compare API response.
    """
    validate_comparison_result(comparison_result)
    validate_next_action(next_action)
