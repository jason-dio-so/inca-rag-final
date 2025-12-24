"""
STEP 12: UX User Message Contract (Deterministic)

Purpose: Provide deterministic user messages for all comparison states

Constitutional Requirements:
- NO value judgments (가장 넓은, 가장 유리함, 추천)
- NO policy-first language
- Factual statements only
- next_action guidance (not recommendations)
"""
from enum import Enum
from typing import Optional
from dataclasses import dataclass


class MessageCode(str, Enum):
    """Message codes for user responses (deterministic)"""
    # Success states
    COMPARABLE = "comparable"
    COMPARABLE_WITH_GAPS = "comparable_with_gaps"

    # Error states
    OUT_OF_UNIVERSE = "out_of_universe"
    UNMAPPED = "unmapped"
    AMBIGUOUS = "ambiguous"
    NON_COMPARABLE = "non_comparable"

    # System states
    POLICY_REQUIRED = "policy_required"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class NextAction(str, Enum):
    """Next action guidance (deterministic)"""
    VIEW_COMPARISON = "view_comparison"
    CHECK_PROPOSAL = "check_proposal"
    VERIFY_POLICY = "verify_policy"
    CONTACT_ADMIN = "contact_admin"
    RETRY_WITH_DIFFERENT_COVERAGE = "retry_with_different_coverage"


@dataclass
class UserMessage:
    """
    User message with deterministic code and next action

    Constitutional requirement:
    - message_code: enum value (deterministic)
    - message_ko: template-based Korean message (no LLM generation)
    - next_action: enum value (guidance, not recommendation)
    - explanation: optional factual details
    """
    message_code: MessageCode
    message_ko: str
    next_action: NextAction
    explanation: Optional[str] = None


# Message templates (deterministic, no value judgments)
MESSAGE_TEMPLATES = {
    MessageCode.COMPARABLE: UserMessage(
        message_code=MessageCode.COMPARABLE,
        message_ko="비교 가능한 담보입니다. 모든 보험사의 정보가 확인되었습니다.",
        next_action=NextAction.VIEW_COMPARISON,
    ),
    MessageCode.COMPARABLE_WITH_GAPS: UserMessage(
        message_code=MessageCode.COMPARABLE_WITH_GAPS,
        message_ko="비교 가능하나 일부 정보가 확인되지 않았습니다. 약관 확인이 필요합니다.",
        next_action=NextAction.VERIFY_POLICY,
        explanation="일부 보험사의 질병 정의 또는 지급 조건이 약관에서 추출되지 않았습니다.",
    ),
    MessageCode.OUT_OF_UNIVERSE: UserMessage(
        message_code=MessageCode.OUT_OF_UNIVERSE,
        message_ko="해당 담보는 가입설계서에 존재하지 않아 비교할 수 없습니다.",
        next_action=NextAction.CHECK_PROPOSAL,
        explanation="비교 가능한 담보는 가입설계서에 포함된 담보만 해당됩니다.",
    ),
    MessageCode.UNMAPPED: UserMessage(
        message_code=MessageCode.UNMAPPED,
        message_ko="담보명이 매핑되지 않았습니다. 관리자 확인이 필요합니다.",
        next_action=NextAction.CONTACT_ADMIN,
        explanation="해당 담보명은 신정원 표준 담보 코드와 매핑되지 않았습니다.",
    ),
    MessageCode.AMBIGUOUS: UserMessage(
        message_code=MessageCode.AMBIGUOUS,
        message_ko="담보명이 여러 표준 담보 코드에 매칭됩니다. 수동 확인이 필요합니다.",
        next_action=NextAction.CONTACT_ADMIN,
        explanation="하나의 담보명이 여러 신정원 표준 담보 코드 후보를 가지고 있습니다.",
    ),
    MessageCode.NON_COMPARABLE: UserMessage(
        message_code=MessageCode.NON_COMPARABLE,
        message_ko="보험사 간 담보 정의가 달라 직접 비교가 어렵습니다.",
        next_action=NextAction.VERIFY_POLICY,
        explanation="각 보험사의 약관에서 담보 정의를 개별적으로 확인하세요.",
    ),
    MessageCode.POLICY_REQUIRED: UserMessage(
        message_code=MessageCode.POLICY_REQUIRED,
        message_ko="약관 확인이 필요합니다.",
        next_action=NextAction.VERIFY_POLICY,
        explanation="정확한 비교를 위해 약관에서 질병 정의 또는 지급 조건을 확인하세요.",
    ),
    MessageCode.MANUAL_REVIEW_REQUIRED: UserMessage(
        message_code=MessageCode.MANUAL_REVIEW_REQUIRED,
        message_ko="수동 검토가 필요합니다.",
        next_action=NextAction.CONTACT_ADMIN,
        explanation="시스템이 자동으로 처리할 수 없는 케이스입니다.",
    ),
}


def get_user_message(message_code: MessageCode) -> UserMessage:
    """
    Get user message for a message code

    Args:
        message_code: MessageCode enum

    Returns:
        UserMessage with deterministic template

    Raises:
        KeyError: If message_code not in templates
    """
    return MESSAGE_TEMPLATES[message_code]


def validate_no_prohibited_phrases(message_ko: str) -> bool:
    """
    Validate that message contains no prohibited phrases

    Constitutional prohibition:
    - NO value judgments (가장 넓은, 가장 유리함)
    - NO recommendations (추천)
    - NO policy-first language

    Args:
        message_ko: Korean message text

    Returns:
        True if valid, False if prohibited phrases found
    """
    prohibited_phrases = [
        "가장 넓은",
        "가장 유리",
        "추천",
        "더 나은",
        "더 좋은",
        "최고",
        "최선",
        "우수",
        "약관 중심",
        "policy-first",
        "약관 기준",
    ]

    for phrase in prohibited_phrases:
        if phrase in message_ko:
            return False

    return True


def validate_all_templates():
    """
    Validate that all message templates comply with Constitutional requirements

    Returns:
        True if all templates valid, False otherwise
    """
    for message_code, user_message in MESSAGE_TEMPLATES.items():
        if not validate_no_prohibited_phrases(user_message.message_ko):
            return False
        if user_message.explanation and not validate_no_prohibited_phrases(user_message.explanation):
            return False

    return True
