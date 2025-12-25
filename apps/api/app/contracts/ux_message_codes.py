"""
UX Message Code Registry (STEP 26)

SSOT for allowed UX message codes in Compare API responses.

Constitutional Rules:
- UX message TEXT is NOT a contract (can change freely)
- UX message CODE is the contract (frozen in golden snapshots)
- Adding/removing codes = breaking change (requires CHANGELOG approval)
- Code validation MUST reference this registry (no hardcoded strings elsewhere)
- Naming convention: UPPER_SNAKE_CASE only

Historical Context:
- STEP 16-22: Golden snapshots freeze semantic contract
- STEP 24: comparison_result/next_action code freeze
- STEP 26: UX message code freeze (text decoupled from contract)
"""

from typing import Set


# ============================================================================
# UX Message Codes: User-facing message identifiers
# ============================================================================

ALLOWED_UX_MESSAGE_CODES: Set[str] = {
    # Coverage successfully matched between insurers (comparable)
    # Example: "Both insurers have CA_DIAG_GENERAL"
    "COVERAGE_MATCH_COMPARABLE",

    # Coverage found in single insurer (comparable, no comparison target)
    # Example: "일반암진단금 found in SAMSUNG"
    "COVERAGE_FOUND_SINGLE_INSURER",

    # Coverage not mapped to canonical code (Excel mapping failed)
    # Example: "매핑안된담보 is not mapped to canonical coverage code"
    "COVERAGE_UNMAPPED",

    # Coverage requires disease scope verification (policy_required)
    # Example: "Disease scope verification required for 유사암진단금"
    "DISEASE_SCOPE_VERIFICATION_REQUIRED",

    # Coverage comparison possible but policy verification needed (comparable_with_gaps)
    # Example: "Coverage comparison possible but disease scope verification required"
    "COVERAGE_COMPARABLE_WITH_GAPS",

    # Query coverage not found in proposal universe (out_of_universe)
    # Example: "'다빈치 수술비' coverage not found in SAMSUNG proposal universe"
    "COVERAGE_NOT_IN_UNIVERSE",

    # Different coverage types detected (non_comparable)
    # Example: "Different coverage types: CA_DIAG_GENERAL vs CA_DIAG_SIMILAR"
    "COVERAGE_TYPE_MISMATCH",
}


# ============================================================================
# Code Description Mapping (Documentation Only - NOT Contract)
# ============================================================================

UX_MESSAGE_CODE_DESCRIPTIONS = {
    "COVERAGE_MATCH_COMPARABLE": {
        "ko": "두 보험사 모두 동일 담보 보유 (비교 가능)",
        "en": "Both insurers have the same coverage (comparable)",
        "example_text": "Both insurers have CA_DIAG_GENERAL",
    },
    "COVERAGE_FOUND_SINGLE_INSURER": {
        "ko": "단일 보험사 담보 확인 (비교 대상 없음)",
        "en": "Coverage found in single insurer (no comparison target)",
        "example_text": "일반암진단금 found in SAMSUNG",
    },
    "COVERAGE_UNMAPPED": {
        "ko": "담보 매핑 실패 (Excel 매핑 정보 없음)",
        "en": "Coverage not mapped (Excel mapping failed)",
        "example_text": "매핑안된담보 is not mapped to canonical coverage code",
    },
    "DISEASE_SCOPE_VERIFICATION_REQUIRED": {
        "ko": "질병 범위 약관 검증 필요",
        "en": "Disease scope policy verification required",
        "example_text": "Disease scope verification required for 유사암진단금",
    },
    "COVERAGE_COMPARABLE_WITH_GAPS": {
        "ko": "비교 가능하나 약관 검증 필요 (질병 범위 등)",
        "en": "Comparable with policy verification needed (disease scope, etc.)",
        "example_text": "Coverage comparison possible but disease scope verification required",
    },
    "COVERAGE_NOT_IN_UNIVERSE": {
        "ko": "가입설계서에 없는 담보 (Universe 외부)",
        "en": "Coverage not in proposal universe (out of universe)",
        "example_text": "'다빈치 수술비' coverage not found in SAMSUNG proposal universe",
    },
    "COVERAGE_TYPE_MISMATCH": {
        "ko": "서로 다른 담보 유형 (비교 불가)",
        "en": "Different coverage types (non-comparable)",
        "example_text": "Different coverage types: CA_DIAG_GENERAL vs CA_DIAG_SIMILAR",
    },
}


# ============================================================================
# Validation Function (Runtime Guard)
# ============================================================================

def validate_ux_message_code(code: str) -> None:
    """
    Validate UX message code against registry.

    Args:
        code: UX message code to validate

    Raises:
        ValueError: If code is not in ALLOWED_UX_MESSAGE_CODES

    Usage:
        Call this BEFORE returning Compare API response.
        Fail-fast on unknown codes to prevent contract drift.

    Example:
        >>> validate_ux_message_code("COVERAGE_MATCH_COMPARABLE")
        >>> validate_ux_message_code("INVALID_CODE")
        ValueError: Invalid UX message code: 'INVALID_CODE'
    """
    if code not in ALLOWED_UX_MESSAGE_CODES:
        raise ValueError(
            f"Invalid UX message code: '{code}'\n"
            f"Allowed codes: {sorted(ALLOWED_UX_MESSAGE_CODES)}\n"
            f"This is a STEP 26 contract violation.\n"
            f"Update apps/api/app/contracts/ux_message_codes.py if adding new codes.\n"
            f"Remember: Changes require docs/contracts/CHANGELOG.md approval."
        )


def validate_ux_message_code_naming(code: str) -> bool:
    """
    Validate UX message code naming convention.

    Args:
        code: UX message code to validate

    Returns:
        True if code follows UPPER_SNAKE_CASE convention

    Usage:
        Used in STEP 26 contract tests to enforce naming rules.

    Example:
        >>> validate_ux_message_code_naming("COVERAGE_MATCH")
        True
        >>> validate_ux_message_code_naming("coverage_match")
        False
        >>> validate_ux_message_code_naming("CoverageMatch")
        False
    """
    if not code:
        return False

    # Must be uppercase letters, digits, and underscores only
    if not all(c.isupper() or c.isdigit() or c == '_' for c in code):
        return False

    # Must not start/end with underscore
    if code.startswith('_') or code.endswith('_'):
        return False

    # Must not have consecutive underscores
    if '__' in code:
        return False

    return True
