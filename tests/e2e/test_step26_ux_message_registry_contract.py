"""
STEP 26: UX Message Code Registry Contract Enforcement

Validates that all UX message codes in golden snapshots and API responses
are registered in the SSOT registry (apps/api/app/contracts/ux_message_codes.py).

Constitutional Rules:
- UX message TEXT is NOT a contract (can change freely)
- UX message CODE is the contract (frozen in golden snapshots)
- All ux_message_code values MUST be in ALLOWED_UX_MESSAGE_CODES
- Naming convention: UPPER_SNAKE_CASE only
- Unknown codes = immediate test failure (fail-fast)

Test Coverage:
1. Registry file exists and imports correctly
2. All golden snapshot ux_message_code values are in registry
3. API response ux_message_code values are validated
4. Unknown codes are rejected at runtime
5. Naming convention enforcement
"""

import json
import os
import pytest
from pathlib import Path

# Import the SSOT registry
from apps.api.app.contracts.ux_message_codes import (
    ALLOWED_UX_MESSAGE_CODES,
    validate_ux_message_code,
    validate_ux_message_code_naming,
)


class TestSTEP26UXMessageRegistryContract:
    """STEP 26: UX Message Code Registry Contract Tests"""

    @pytest.fixture
    def golden_snapshots_dir(self):
        """Path to golden snapshots directory."""
        return Path(__file__).parent.parent / "snapshots" / "compare"

    @pytest.fixture
    def golden_snapshot_files(self, golden_snapshots_dir):
        """List all golden snapshot files."""
        return list(golden_snapshots_dir.glob("*.golden.json"))

    def test_registry_file_exists_and_imports(self):
        """
        Test: Registry file exists and can be imported.

        Expected:
        - ALLOWED_UX_MESSAGE_CODES is a set
        - Set is not empty
        - All codes follow UPPER_SNAKE_CASE convention
        """
        assert isinstance(ALLOWED_UX_MESSAGE_CODES, set), \
            "ALLOWED_UX_MESSAGE_CODES must be a set"

        assert len(ALLOWED_UX_MESSAGE_CODES) > 0, \
            "ALLOWED_UX_MESSAGE_CODES must not be empty"

        # Verify all codes follow naming convention
        for code in ALLOWED_UX_MESSAGE_CODES:
            assert validate_ux_message_code_naming(code), \
                f"UX message code '{code}' does not follow UPPER_SNAKE_CASE convention"

    def test_registry_contains_expected_codes(self):
        """
        Test: Registry contains expected UX message codes.

        Expected codes (based on STEP 26 spec):
        - COVERAGE_MATCH_COMPARABLE
        - COVERAGE_FOUND_SINGLE_INSURER
        - COVERAGE_UNMAPPED
        - DISEASE_SCOPE_VERIFICATION_REQUIRED
        - COVERAGE_COMPARABLE_WITH_GAPS
        - COVERAGE_NOT_IN_UNIVERSE
        - COVERAGE_TYPE_MISMATCH
        """
        expected_codes = {
            "COVERAGE_MATCH_COMPARABLE",
            "COVERAGE_FOUND_SINGLE_INSURER",
            "COVERAGE_UNMAPPED",
            "DISEASE_SCOPE_VERIFICATION_REQUIRED",
            "COVERAGE_COMPARABLE_WITH_GAPS",
            "COVERAGE_NOT_IN_UNIVERSE",
            "COVERAGE_TYPE_MISMATCH",
        }

        missing_codes = expected_codes - ALLOWED_UX_MESSAGE_CODES
        assert not missing_codes, \
            f"Registry missing expected codes: {sorted(missing_codes)}"

    def test_golden_snapshots_have_ux_message_code_field(self, golden_snapshot_files):
        """
        Test: All golden snapshots have ux_message_code field.

        Expected:
        - Each golden snapshot has a ux_message_code field
        - Field is not null/empty
        """
        assert len(golden_snapshot_files) > 0, \
            "No golden snapshot files found"

        for snapshot_file in golden_snapshot_files:
            with open(snapshot_file, "r", encoding="utf-8") as f:
                snapshot = json.load(f)

            assert "ux_message_code" in snapshot, \
                f"{snapshot_file.name}: Missing ux_message_code field"

            assert snapshot["ux_message_code"], \
                f"{snapshot_file.name}: ux_message_code is null or empty"

    def test_all_golden_snapshot_codes_in_registry(self, golden_snapshot_files):
        """
        Test: All ux_message_code values in golden snapshots are in registry.

        This is the PRIMARY CONTRACT TEST for STEP 26.

        Expected:
        - Every ux_message_code in golden snapshots is in ALLOWED_UX_MESSAGE_CODES
        - No unknown codes exist in snapshots
        """
        unknown_codes = set()
        snapshot_codes = {}

        for snapshot_file in golden_snapshot_files:
            with open(snapshot_file, "r", encoding="utf-8") as f:
                snapshot = json.load(f)

            code = snapshot.get("ux_message_code")
            if code:
                snapshot_codes[snapshot_file.name] = code
                if code not in ALLOWED_UX_MESSAGE_CODES:
                    unknown_codes.add(code)

        if unknown_codes:
            error_msg = (
                f"Unknown UX message codes found in golden snapshots:\n"
                f"  Unknown codes: {sorted(unknown_codes)}\n"
                f"  Registry codes: {sorted(ALLOWED_UX_MESSAGE_CODES)}\n"
                f"  Files with unknown codes:\n"
            )
            for file, code in snapshot_codes.items():
                if code in unknown_codes:
                    error_msg += f"    {file}: {code}\n"

            error_msg += (
                f"\n"
                f"This is a STEP 26 contract violation.\n"
                f"Add missing codes to apps/api/app/contracts/ux_message_codes.py\n"
                f"and update docs/contracts/CHANGELOG.md"
            )
            pytest.fail(error_msg)

    def test_validate_ux_message_code_accepts_valid_codes(self):
        """
        Test: validate_ux_message_code accepts all registry codes.

        Expected:
        - No exceptions for valid codes
        """
        for code in ALLOWED_UX_MESSAGE_CODES:
            try:
                validate_ux_message_code(code)
            except ValueError as e:
                pytest.fail(f"validate_ux_message_code rejected valid code '{code}': {e}")

    def test_validate_ux_message_code_rejects_unknown_codes(self):
        """
        Test: validate_ux_message_code rejects unknown codes.

        Expected:
        - ValueError for unknown codes
        - Error message includes the invalid code
        - Error message mentions STEP 26
        """
        unknown_codes = [
            "INVALID_CODE",
            "coverage_match_comparable",  # Wrong case
            "COVERAGE_MATCH",  # Truncated
            "NEW_CODE_NOT_IN_REGISTRY",
        ]

        for code in unknown_codes:
            with pytest.raises(ValueError) as exc_info:
                validate_ux_message_code(code)

            error_msg = str(exc_info.value)
            assert code in error_msg, \
                f"Error message should include invalid code '{code}'"
            assert "STEP 26" in error_msg, \
                "Error message should mention STEP 26"

    def test_ux_message_code_naming_convention(self):
        """
        Test: UX message codes follow UPPER_SNAKE_CASE convention.

        Valid:
        - COVERAGE_MATCH_COMPARABLE
        - DISEASE_SCOPE_REQUIRED
        - CODE_123

        Invalid:
        - coverage_match (lowercase)
        - CoverageMatch (CamelCase)
        - COVERAGE__MATCH (double underscore)
        - _COVERAGE_MATCH (leading underscore)
        - COVERAGE_MATCH_ (trailing underscore)
        """
        valid_codes = [
            "COVERAGE_MATCH_COMPARABLE",
            "DISEASE_SCOPE_REQUIRED",
            "CODE_123",
            "A",
            "A_B",
        ]

        for code in valid_codes:
            assert validate_ux_message_code_naming(code), \
                f"Valid code '{code}' was rejected"

        invalid_codes = [
            "coverage_match",  # lowercase
            "CoverageMatch",  # CamelCase
            "COVERAGE__MATCH",  # double underscore
            "_COVERAGE_MATCH",  # leading underscore
            "COVERAGE_MATCH_",  # trailing underscore
            "",  # empty
            "coverage-match",  # hyphen
            "COVERAGE MATCH",  # space
        ]

        for code in invalid_codes:
            assert not validate_ux_message_code_naming(code), \
                f"Invalid code '{code}' was accepted"

    def test_all_registry_codes_follow_naming_convention(self):
        """
        Test: All codes in ALLOWED_UX_MESSAGE_CODES follow naming convention.

        Expected:
        - Every code in registry passes validate_ux_message_code_naming
        """
        invalid_codes = []

        for code in ALLOWED_UX_MESSAGE_CODES:
            if not validate_ux_message_code_naming(code):
                invalid_codes.append(code)

        if invalid_codes:
            pytest.fail(
                f"Registry contains codes that violate naming convention:\n"
                f"  {sorted(invalid_codes)}\n"
                f"All codes must follow UPPER_SNAKE_CASE convention"
            )

    def test_golden_snapshots_unchanged_structure(self, golden_snapshot_files):
        """
        Test: Golden snapshots maintain expected structure with ux_message_code.

        Expected fields (STEP 26):
        - query
        - comparison_result
        - next_action
        - message
        - ux_message_code (NEW in STEP 26)
        - coverage_a, coverage_b (nullable)
        - policy_evidence_a, policy_evidence_b (nullable)
        - debug
        """
        required_fields = {
            "query",
            "comparison_result",
            "next_action",
            "message",
            "ux_message_code",  # STEP 26
            "debug",
        }

        for snapshot_file in golden_snapshot_files:
            with open(snapshot_file, "r", encoding="utf-8") as f:
                snapshot = json.load(f)

            missing_fields = required_fields - set(snapshot.keys())
            assert not missing_fields, \
                f"{snapshot_file.name}: Missing required fields: {sorted(missing_fields)}"
