"""
STEP 12: User Message Contract Tests

Purpose: Validate user message templates comply with Constitutional requirements

Constitutional Requirements:
- NO value judgments (prohibited phrases)
- Deterministic message_code and next_action
- Factual statements only
"""
import pytest
from src.ux.user_messages import (
    MessageCode,
    NextAction,
    get_user_message,
    validate_no_prohibited_phrases,
    validate_all_templates,
    MESSAGE_TEMPLATES,
)


class TestSTEP12UserMessages:
    """
    STEP 12: User message contract tests

    Constitutional Requirement:
    - All messages must be deterministic
    - NO prohibited phrases
    - NO value judgments or recommendations
    """

    def test_message_code_enum_complete(self):
        """
        Test 1: MessageCode enum covers all comparison states

        Requirement:
        - out_of_universe, unmapped, ambiguous
        - comparable, comparable_with_gaps, non_comparable
        - policy_required, manual_review_required
        """
        required_codes = {
            "out_of_universe",
            "unmapped",
            "ambiguous",
            "comparable",
            "comparable_with_gaps",
            "non_comparable",
            "policy_required",
            "manual_review_required",
        }

        actual_codes = {code.value for code in MessageCode}

        assert required_codes.issubset(actual_codes), \
            f"Missing message codes: {required_codes - actual_codes}"

    def test_next_action_enum_deterministic(self):
        """
        Test 2: NextAction enum provides deterministic guidance

        Requirement:
        - All next_action values are enum (not free-form text)
        - Guidance-only (not recommendations)
        """
        expected_actions = {
            "view_comparison",
            "check_proposal",
            "verify_policy",
            "contact_admin",
            "retry_with_different_coverage",
        }

        actual_actions = {action.value for action in NextAction}

        assert expected_actions == actual_actions, \
            f"NextAction enum mismatch: expected {expected_actions}, got {actual_actions}"

    def test_all_message_codes_have_templates(self):
        """
        Test 3: All MessageCode values have templates

        Requirement:
        - Every message_code must have a template
        - No missing templates
        """
        for message_code in MessageCode:
            assert message_code in MESSAGE_TEMPLATES, \
                f"Missing template for {message_code}"

    def test_prohibited_phrases_validation_detects_violations(self):
        """
        Test 4: Prohibited phrase validation works

        Requirement:
        - Detect all prohibited phrases
        """
        # Valid messages (factual only)
        valid_messages = [
            "비교 가능한 담보입니다.",
            "약관 확인이 필요합니다.",
            "가입설계서에 존재하지 않습니다.",
        ]

        for msg in valid_messages:
            assert validate_no_prohibited_phrases(msg), \
                f"Should accept factual message: {msg}"

        # Invalid messages (prohibited phrases)
        invalid_messages = [
            "가장 넓은 보장을 제공합니다.",
            "가장 유리한 상품입니다.",
            "이 상품을 추천합니다.",
            "더 나은 선택입니다.",
            "약관 중심으로 비교합니다.",
        ]

        for msg in invalid_messages:
            assert not validate_no_prohibited_phrases(msg), \
                f"Should reject prohibited phrase: {msg}"

    def test_all_templates_pass_prohibited_phrase_check(self):
        """
        Test 5: All templates pass prohibited phrase validation

        Constitutional requirement:
        - NO templates contain prohibited phrases
        """
        assert validate_all_templates(), \
            "All message templates must pass prohibited phrase check (Constitutional)"

        # Detailed check for each template
        for message_code, user_message in MESSAGE_TEMPLATES.items():
            assert validate_no_prohibited_phrases(user_message.message_ko), \
                f"{message_code} message_ko contains prohibited phrase: {user_message.message_ko}"

            if user_message.explanation:
                assert validate_no_prohibited_phrases(user_message.explanation), \
                    f"{message_code} explanation contains prohibited phrase: {user_message.explanation}"

    def test_out_of_universe_message(self):
        """
        Test 6: out_of_universe message correct

        Requirement:
        - Explains Universe Lock (proposal-based)
        - next_action = check_proposal
        """
        msg = get_user_message(MessageCode.OUT_OF_UNIVERSE)

        assert msg.message_code == MessageCode.OUT_OF_UNIVERSE
        assert msg.next_action == NextAction.CHECK_PROPOSAL
        assert "가입설계서" in msg.message_ko, \
            "Should mention proposal (Universe Lock)"
        assert validate_no_prohibited_phrases(msg.message_ko)

    def test_unmapped_message(self):
        """
        Test 7: unmapped message correct

        Requirement:
        - Explains Excel mapping failure
        - next_action = contact_admin
        """
        msg = get_user_message(MessageCode.UNMAPPED)

        assert msg.message_code == MessageCode.UNMAPPED
        assert msg.next_action == NextAction.CONTACT_ADMIN
        assert "매핑" in msg.message_ko or "관리자" in msg.message_ko
        assert validate_no_prohibited_phrases(msg.message_ko)

    def test_ambiguous_message(self):
        """
        Test 8: ambiguous message correct

        Requirement:
        - Explains multiple mapping candidates
        - next_action = contact_admin
        """
        msg = get_user_message(MessageCode.AMBIGUOUS)

        assert msg.message_code == MessageCode.AMBIGUOUS
        assert msg.next_action == NextAction.CONTACT_ADMIN
        assert validate_no_prohibited_phrases(msg.message_ko)

    def test_comparable_with_gaps_message(self):
        """
        Test 9: comparable_with_gaps message correct

        Requirement:
        - Explains policy verification needed
        - next_action = verify_policy
        - NO "약관 중심" or "policy-first" language
        """
        msg = get_user_message(MessageCode.COMPARABLE_WITH_GAPS)

        assert msg.message_code == MessageCode.COMPARABLE_WITH_GAPS
        assert msg.next_action == NextAction.VERIFY_POLICY
        assert "약관 확인" in msg.message_ko or "약관" in msg.explanation
        assert "약관 중심" not in msg.message_ko, \
            "Must not use 'policy-first' language (Constitutional)"
        assert validate_no_prohibited_phrases(msg.message_ko)

    def test_comparable_message(self):
        """
        Test 10: comparable message correct

        Requirement:
        - Success message (factual)
        - next_action = view_comparison
        """
        msg = get_user_message(MessageCode.COMPARABLE)

        assert msg.message_code == MessageCode.COMPARABLE
        assert msg.next_action == NextAction.VIEW_COMPARISON
        assert validate_no_prohibited_phrases(msg.message_ko)

    def test_non_comparable_message(self):
        """
        Test 11: non_comparable message correct

        Requirement:
        - Explains different definitions (factual)
        - next_action = verify_policy
        - NO value judgments
        """
        msg = get_user_message(MessageCode.NON_COMPARABLE)

        assert msg.message_code == MessageCode.NON_COMPARABLE
        assert msg.next_action == NextAction.VERIFY_POLICY
        assert validate_no_prohibited_phrases(msg.message_ko)

    def test_policy_required_message(self):
        """
        Test 12: policy_required message correct

        Requirement:
        - Explains policy verification needed
        - next_action = verify_policy
        - Policy as interpretation tool (not comparison source)
        """
        msg = get_user_message(MessageCode.POLICY_REQUIRED)

        assert msg.message_code == MessageCode.POLICY_REQUIRED
        assert msg.next_action == NextAction.VERIFY_POLICY
        assert validate_no_prohibited_phrases(msg.message_ko)

    def test_message_templates_are_deterministic(self):
        """
        Test 13: Message templates are deterministic (not LLM-generated)

        Requirement:
        - Same input → same output
        - No randomness or LLM generation
        """
        # Call get_user_message multiple times for same code
        msg1 = get_user_message(MessageCode.OUT_OF_UNIVERSE)
        msg2 = get_user_message(MessageCode.OUT_OF_UNIVERSE)
        msg3 = get_user_message(MessageCode.OUT_OF_UNIVERSE)

        # Must be identical (deterministic)
        assert msg1.message_ko == msg2.message_ko == msg3.message_ko
        assert msg1.next_action == msg2.next_action == msg3.next_action
        assert msg1.explanation == msg2.explanation == msg3.explanation
