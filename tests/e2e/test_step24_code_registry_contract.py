"""
STEP 24: Code Registry Contract Tests

These tests enforce that comparison_result and next_action codes
are governed by a SSOT registry, preventing string drift.

Constitutional Principles:
- Codes are contracts (not just documentation)
- Registry SSOT must exist and be loadable
- All golden snapshots must use only allowed codes
- API runtime responses must use only allowed codes

Relationship to STEP 16:
- STEP 16: Freezes semantic contract (values, structure)
- STEP 24: Freezes enum codes (allowed strings)

These are complementary, not overlapping.
"""

import json
import os
import pytest


SNAPSHOTS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "snapshots", "compare"
)


@pytest.mark.skipif(
    os.getenv("E2E_DOCKER") != "1",
    reason="Requires Docker environment (set E2E_DOCKER=1)"
)
class TestSTEP24CodeRegistryContract:
    """
    Code Registry Contract Tests.

    Ensures comparison_result and next_action codes are governed
    by SSOT registry, preventing ad-hoc string additions.
    """

    API_BASE = "http://localhost:8000"

    def test_registry_ssot_exists_and_loadable(self):
        """
        Registry SSOT Existence Test.

        Ensures:
        - Registry module exists and is importable
        - ALLOWED_COMPARISON_RESULTS is defined
        - ALLOWED_NEXT_ACTIONS is defined
        - Both are non-empty sets/lists
        """
        from apps.api.app.contracts import (
            ALLOWED_COMPARISON_RESULTS,
            ALLOWED_NEXT_ACTIONS,
        )

        # Registry must be non-empty
        assert len(ALLOWED_COMPARISON_RESULTS) > 0, \
            "ALLOWED_COMPARISON_RESULTS must not be empty"
        assert len(ALLOWED_NEXT_ACTIONS) > 0, \
            "ALLOWED_NEXT_ACTIONS must not be empty"

        # Must be iterable collections
        assert hasattr(ALLOWED_COMPARISON_RESULTS, '__iter__'), \
            "ALLOWED_COMPARISON_RESULTS must be iterable"
        assert hasattr(ALLOWED_NEXT_ACTIONS, '__iter__'), \
            "ALLOWED_NEXT_ACTIONS must be iterable"

    def test_all_golden_snapshots_use_allowed_codes(self):
        """
        Golden Snapshots Code Validation.

        Ensures ALL golden snapshots (A/B/C/D/E) use only codes
        from the registry SSOT.

        Failure indicates:
        - Golden contains unknown code (contract violation)
        - Registry is incomplete (update required)
        """
        from apps.api.app.contracts import (
            ALLOWED_COMPARISON_RESULTS,
            ALLOWED_NEXT_ACTIONS,
        )

        required_snapshots = ["scenario_a", "scenario_b", "scenario_c", "scenario_d", "scenario_e"]

        violations = []

        for scenario_name in required_snapshots:
            snapshot_path = os.path.join(SNAPSHOTS_DIR, f"{scenario_name}.golden.json")

            with open(snapshot_path, 'r', encoding='utf-8') as f:
                golden = json.load(f)

            # Check comparison_result
            comparison_result = golden.get("comparison_result")
            if comparison_result not in ALLOWED_COMPARISON_RESULTS:
                violations.append(
                    f"{scenario_name}: Unknown comparison_result '{comparison_result}' "
                    f"(allowed: {sorted(ALLOWED_COMPARISON_RESULTS)})"
                )

            # Check next_action
            next_action = golden.get("next_action")
            if next_action not in ALLOWED_NEXT_ACTIONS:
                violations.append(
                    f"{scenario_name}: Unknown next_action '{next_action}' "
                    f"(allowed: {sorted(ALLOWED_NEXT_ACTIONS)})"
                )

        # Report all violations at once
        assert not violations, (
            "Golden snapshot code violations detected:\n" +
            "\n".join(f"  - {v}" for v in violations) +
            "\n\nThis is a STEP 24 contract violation.\n"
            "Update apps/api/app/contracts/compare_codes.py if adding new codes."
        )

    def test_api_scenario_a_returns_allowed_codes(self):
        """
        API Runtime Code Validation - Scenario A (Comparable).

        Ensures API returns only allowed codes for normal comparison.
        """
        import requests
        from apps.api.app.contracts import (
            ALLOWED_COMPARISON_RESULTS,
            ALLOWED_NEXT_ACTIONS,
        )

        response = requests.post(
            f"{self.API_BASE}/compare",
            json={
                "query": "일반암진단비",
                "insurer_a": "SAMSUNG",
                "insurer_b": "MERITZ",
                "include_policy_evidence": False
            },
            timeout=10
        )

        assert response.status_code == 200, f"HTTP {response.status_code}: {response.text}"

        data = response.json()

        # Validate comparison_result
        comparison_result = data.get("comparison_result")
        assert comparison_result in ALLOWED_COMPARISON_RESULTS, (
            f"API returned unknown comparison_result: '{comparison_result}'\n"
            f"Allowed codes: {sorted(ALLOWED_COMPARISON_RESULTS)}\n"
            f"This is a STEP 24 contract violation."
        )

        # Validate next_action
        next_action = data.get("next_action")
        assert next_action in ALLOWED_NEXT_ACTIONS, (
            f"API returned unknown next_action: '{next_action}'\n"
            f"Allowed codes: {sorted(ALLOWED_NEXT_ACTIONS)}\n"
            f"This is a STEP 24 contract violation."
        )

    def test_api_scenario_e_out_of_universe_returns_allowed_codes(self):
        """
        API Runtime Code Validation - Scenario E (Out-of-Universe).

        Ensures API returns only allowed codes for edge cases.
        """
        import requests
        from apps.api.app.contracts import (
            ALLOWED_COMPARISON_RESULTS,
            ALLOWED_NEXT_ACTIONS,
        )

        response = requests.post(
            f"{self.API_BASE}/compare",
            json={
                "query": "다빈치 수술비",
                "insurer_a": "SAMSUNG",
                "insurer_b": None,
                "include_policy_evidence": False
            },
            timeout=10
        )

        assert response.status_code == 200, f"HTTP {response.status_code}: {response.text}"

        data = response.json()

        # Validate comparison_result
        comparison_result = data.get("comparison_result")
        assert comparison_result in ALLOWED_COMPARISON_RESULTS, (
            f"API returned unknown comparison_result: '{comparison_result}'\n"
            f"Allowed codes: {sorted(ALLOWED_COMPARISON_RESULTS)}\n"
            f"This is a STEP 24 contract violation."
        )

        # Validate next_action
        next_action = data.get("next_action")
        assert next_action in ALLOWED_NEXT_ACTIONS, (
            f"API returned unknown next_action: '{next_action}'\n"
            f"Allowed codes: {sorted(ALLOWED_NEXT_ACTIONS)}\n"
            f"This is a STEP 24 contract violation."
        )

    def test_registry_completeness_for_known_scenarios(self):
        """
        Registry Completeness Validation.

        Ensures registry contains all codes expected from STEP 14-23:
        - comparison_result: comparable, unmapped, policy_required, out_of_universe
        - next_action: COMPARE, REQUEST_MORE_INFO, VERIFY_POLICY

        This test encodes historical contract knowledge from STEP 14-23.
        """
        from apps.api.app.contracts import (
            ALLOWED_COMPARISON_RESULTS,
            ALLOWED_NEXT_ACTIONS,
        )

        # Expected codes from golden scenarios A/B/C/D/E
        expected_comparison_results = {
            "comparable",        # Scenario A, D
            "unmapped",          # Scenario B
            "policy_required",   # Scenario C
            "out_of_universe",   # Scenario E
        }

        expected_next_actions = {
            "COMPARE",           # Scenario A, D
            "REQUEST_MORE_INFO", # Scenario B, E
            "VERIFY_POLICY",     # Scenario C
        }

        # Check completeness
        missing_comparison_results = expected_comparison_results - set(ALLOWED_COMPARISON_RESULTS)
        missing_next_actions = expected_next_actions - set(ALLOWED_NEXT_ACTIONS)

        assert not missing_comparison_results, (
            f"Registry is missing expected comparison_result codes: {missing_comparison_results}\n"
            f"These codes are used in golden scenarios A/B/C/D/E.\n"
            f"Update apps/api/app/contracts/compare_codes.py"
        )

        assert not missing_next_actions, (
            f"Registry is missing expected next_action codes: {missing_next_actions}\n"
            f"These codes are used in golden scenarios A/B/C/D/E.\n"
            f"Update apps/api/app/contracts/compare_codes.py"
        )

    def test_validation_functions_exist(self):
        """
        Validation Functions Existence Test.

        Ensures runtime validation functions are available:
        - validate_comparison_result()
        - validate_next_action()
        - validate_compare_response()
        """
        from apps.api.app.contracts import (
            validate_comparison_result,
            validate_next_action,
        )

        # Functions must be callable
        assert callable(validate_comparison_result), \
            "validate_comparison_result must be callable"
        assert callable(validate_next_action), \
            "validate_next_action must be callable"

    def test_validation_functions_reject_unknown_codes(self):
        """
        Validation Functions Rejection Test.

        Ensures validation functions raise ValueError for unknown codes.
        """
        from apps.api.app.contracts import (
            validate_comparison_result,
            validate_next_action,
        )

        # Test invalid comparison_result
        with pytest.raises(ValueError, match="Invalid comparison_result code"):
            validate_comparison_result("unknown_code")

        # Test invalid next_action
        with pytest.raises(ValueError, match="Invalid next_action code"):
            validate_next_action("UNKNOWN_ACTION")

    def test_validation_functions_accept_valid_codes(self):
        """
        Validation Functions Acceptance Test.

        Ensures validation functions accept all codes from registry.
        """
        from apps.api.app.contracts import (
            ALLOWED_COMPARISON_RESULTS,
            ALLOWED_NEXT_ACTIONS,
            validate_comparison_result,
            validate_next_action,
        )

        # All allowed codes should pass validation
        for code in ALLOWED_COMPARISON_RESULTS:
            validate_comparison_result(code)  # Should not raise

        for code in ALLOWED_NEXT_ACTIONS:
            validate_next_action(code)  # Should not raise

    def test_code_naming_convention_enforcement(self):
        """
        Code Naming Convention Enforcement (STEP 25 Meta-Test).

        Ensures code naming follows consistent patterns:
        - comparison_result: lower_snake_case
        - next_action: UPPER_SNAKE_CASE

        This prevents style drift that could confuse UX/client code.
        """
        from apps.api.app.contracts import (
            ALLOWED_COMPARISON_RESULTS,
            ALLOWED_NEXT_ACTIONS,
        )

        violations = []

        # Check comparison_result: must be lower_snake_case (no uppercase)
        for code in ALLOWED_COMPARISON_RESULTS:
            if not code.islower() or not all(c.isalnum() or c == '_' for c in code):
                violations.append(
                    f"comparison_result '{code}' violates lower_snake_case convention"
                )

        # Check next_action: must be UPPER_SNAKE_CASE (no lowercase)
        for code in ALLOWED_NEXT_ACTIONS:
            if not code.isupper() or not all(c.isalnum() or c == '_' for c in code):
                violations.append(
                    f"next_action '{code}' violates UPPER_SNAKE_CASE convention"
                )

        assert not violations, (
            "Code naming convention violations detected:\n" +
            "\n".join(f"  - {v}" for v in violations) +
            "\n\nThis is a STEP 25 contract violation.\n"
            "Code naming conventions are part of the contract:\n"
            "  - comparison_result: lower_snake_case\n"
            "  - next_action: UPPER_SNAKE_CASE"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
