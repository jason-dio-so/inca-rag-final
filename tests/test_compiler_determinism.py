"""
Test compiler determinism (STEP NEXT-6)

Constitutional Principles:
- Same input → same output
- No LLM dependency
- Rule-based only
"""

import pytest
from apps.api.app.compiler import (
    compile_request,
    CompileInput,
    CompileOptions,
)


class TestCompilerDeterminism:
    """Test that compiler produces deterministic output."""

    def test_same_input_produces_same_output(self):
        """
        Constitutional Requirement: Determinism
        Same input must produce identical output.
        """
        # Given: Identical inputs
        input1 = CompileInput(
            user_query="암 진단비 비교",
            selected_insurers=["SAMSUNG", "MERITZ"],
            selected_comparison_basis="일반암진단비",
        )

        input2 = CompileInput(
            user_query="암 진단비 비교",
            selected_insurers=["SAMSUNG", "MERITZ"],
            selected_comparison_basis="일반암진단비",
        )

        # When: Compile multiple times
        output1 = compile_request(input1)
        output2 = compile_request(input2)

        # Then: Outputs must be identical
        assert output1.compiled_request == output2.compiled_request
        assert output1.compiler_debug.rule_version == output2.compiler_debug.rule_version
        assert output1.compiler_debug.selected_slots == output2.compiler_debug.selected_slots
        assert output1.compiler_debug.decision_trace == output2.compiler_debug.decision_trace

    def test_determinism_with_surgery_method_option(self):
        """
        Test determinism with surgery_method option.
        """
        # Given: Inputs with surgery_method option
        input1 = CompileInput(
            user_query="다빈치 수술비 비교",
            selected_insurers=["SAMSUNG", "HYUNDAI"],
            options=CompileOptions(surgery_method="da_vinci"),
        )

        input2 = CompileInput(
            user_query="다빈치 수술비 비교",
            selected_insurers=["SAMSUNG", "HYUNDAI"],
            options=CompileOptions(surgery_method="da_vinci"),
        )

        # When: Compile
        output1 = compile_request(input1)
        output2 = compile_request(input2)

        # Then: Must be identical
        assert output1.compiled_request == output2.compiled_request
        assert output1.compiler_debug.selected_slots == output2.compiler_debug.selected_slots

    def test_determinism_with_cancer_subtypes_option(self):
        """
        Test determinism with cancer_subtypes option.
        """
        # Given: Inputs with cancer_subtypes option
        input1 = CompileInput(
            user_query="경계성종양 비교",
            selected_insurers=["HANWHA", "HEUNGKUK"],
            options=CompileOptions(cancer_subtypes=["경계성종양", "제자리암"]),
        )

        input2 = CompileInput(
            user_query="경계성종양 비교",
            selected_insurers=["HANWHA", "HEUNGKUK"],
            options=CompileOptions(cancer_subtypes=["경계성종양", "제자리암"]),
        )

        # When: Compile
        output1 = compile_request(input1)
        output2 = compile_request(input2)

        # Then: Must be identical
        assert output1.compiled_request == output2.compiled_request
        assert output1.compiler_debug.selected_slots == output2.compiler_debug.selected_slots

    def test_different_inputs_produce_different_outputs(self):
        """
        Test that different inputs produce different outputs.
        """
        # Given: Different inputs
        input1 = CompileInput(
            user_query="암 진단비",
            selected_insurers=["SAMSUNG", "MERITZ"],
        )

        input2 = CompileInput(
            user_query="수술비",
            selected_insurers=["SAMSUNG", "MERITZ"],
        )

        # When: Compile
        output1 = compile_request(input1)
        output2 = compile_request(input2)

        # Then: Outputs must be different
        assert output1.compiled_request != output2.compiled_request

    def test_rule_version_is_tracked(self):
        """
        Constitutional Requirement: Rule version must be tracked.
        """
        # Given: Any input
        input_data = CompileInput(
            user_query="암 진단비",
            selected_insurers=["SAMSUNG", "MERITZ"],
        )

        # When: Compile
        output = compile_request(input_data)

        # Then: Rule version must be present
        assert output.compiler_debug.rule_version is not None
        assert len(output.compiler_debug.rule_version) > 0
        assert "v1.0.0-next6" in output.compiler_debug.rule_version

    def test_decision_trace_is_reproducible(self):
        """
        Test that decision trace is reproducible.
        """
        # Given: Same input
        input_data = CompileInput(
            user_query="암 진단비",
            selected_insurers=["SAMSUNG", "MERITZ"],
        )

        # When: Compile multiple times
        output1 = compile_request(input_data)
        output2 = compile_request(input_data)

        # Then: Decision traces must be identical
        assert output1.compiler_debug.decision_trace == output2.compiler_debug.decision_trace
        assert len(output1.compiler_debug.decision_trace) > 0
