"""
Test that compiler has no LLM dependency (STEP NEXT-6)

Constitutional Principle:
- Compiler must be deterministic
- No LLM calls allowed in compilation
- Rule-based only
"""

import pytest
from unittest.mock import patch, MagicMock
from apps.api.app.compiler import compile_request, CompileInput


class TestNoLLMDependency:
    """
    Test that compiler does not depend on LLM.

    This is a critical constitutional requirement.
    """

    def test_no_openai_calls_during_compilation(self):
        """
        Verify that no OpenAI API calls are made during compilation.
        """
        # Given: Mock OpenAI client
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # Given: Valid compile input
            input_data = CompileInput(
                user_query="암 진단비",
                selected_insurers=["SAMSUNG", "MERITZ"],
            )

            # When: Compile
            output = compile_request(input_data)

            # Then: Should succeed without any OpenAI calls
            assert output is not None
            mock_client.chat.completions.create.assert_not_called()

    def test_no_anthropic_calls_during_compilation(self):
        """
        Verify that no Anthropic API calls are made during compilation.
        """
        # Given: Mock Anthropic client
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            # Given: Valid compile input
            input_data = CompileInput(
                user_query="암 진단비",
                selected_insurers=["SAMSUNG", "MERITZ"],
            )

            # When: Compile
            output = compile_request(input_data)

            # Then: Should succeed without any Anthropic calls
            assert output is not None
            # No messages.create should be called
            if hasattr(mock_client, "messages"):
                mock_client.messages.create.assert_not_called()

    def test_compilation_is_fast(self):
        """
        Verify that compilation is fast (no network calls).

        LLM calls would take >100ms typically.
        Rule-based compilation should be <10ms.
        """
        import time

        # Given: Valid compile input
        input_data = CompileInput(
            user_query="암 진단비",
            selected_insurers=["SAMSUNG", "MERITZ"],
        )

        # When: Compile and measure time
        start_time = time.time()
        output = compile_request(input_data)
        elapsed_ms = (time.time() - start_time) * 1000

        # Then: Should be very fast (<100ms)
        assert output is not None
        assert elapsed_ms < 100  # Much faster than any LLM call

    def test_no_external_api_calls(self):
        """
        Verify that no external API calls are made.
        """
        # Given: Mock requests library
        with patch("requests.post") as mock_post, \
             patch("requests.get") as mock_get:

            # Given: Valid compile input
            input_data = CompileInput(
                user_query="암 진단비",
                selected_insurers=["SAMSUNG", "MERITZ"],
            )

            # When: Compile
            output = compile_request(input_data)

            # Then: Should succeed without any HTTP requests
            assert output is not None
            mock_post.assert_not_called()
            mock_get.assert_not_called()

    def test_compilation_uses_only_rules(self):
        """
        Verify that compilation uses only deterministic rules.
        """
        # Given: Same input
        input_data = CompileInput(
            user_query="암 진단비",
            selected_insurers=["SAMSUNG", "MERITZ"],
        )

        # When: Compile multiple times
        outputs = [compile_request(input_data) for _ in range(5)]

        # Then: All outputs must be identical (deterministic)
        for i in range(1, len(outputs)):
            assert outputs[i].compiled_request == outputs[0].compiled_request
            assert outputs[i].compiler_debug.decision_trace == outputs[0].compiler_debug.decision_trace

        # This proves no randomness/LLM involved
