"""
STEP 16: Runtime Contract Freeze - Golden Snapshot Tests

These tests ensure that the Compare API runtime contract remains unchanged
across refactorings, dependency updates, and developer changes.

Golden snapshots are generated from STEP 14 artifacts and must NEVER be
automatically regenerated. Any deviation is considered a breaking change.

Constitutional Principles:
- API Response = Contract (not documentation)
- Proposal = SSOT
- UX Message = code-based contract (not text-based)
- Evidence Order = semantic contract
- Debug = Developer Contract

Test Strategy:
- Deep-equal comparison against golden snapshots
- Allowed exceptions: debug.timestamp, debug.execution_time_ms
- All other changes → FAIL
"""

import json
import os
import pytest


SNAPSHOTS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "snapshots", "compare"
)


def load_golden_snapshot(scenario_name: str) -> dict:
    """Load golden snapshot JSON file."""
    snapshot_path = os.path.join(SNAPSHOTS_DIR, f"{scenario_name}.golden.json")
    assert os.path.exists(snapshot_path), f"Golden snapshot not found: {snapshot_path}"

    with open(snapshot_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize_response(response: dict) -> dict:
    """
    Normalize response for comparison.

    Removes allowed dynamic fields:
    - debug.timestamp (if exists)
    - debug.execution_time_ms (if exists)
    """
    normalized = response.copy()

    # Remove allowed dynamic debug fields
    if "debug" in normalized and isinstance(normalized["debug"], dict):
        debug = normalized["debug"].copy()
        debug.pop("timestamp", None)
        debug.pop("execution_time_ms", None)
        normalized["debug"] = debug

    return normalized


def deep_equal_assert(actual: dict, expected: dict, path: str = "root"):
    """
    Deep equality assertion with detailed error messages.

    Args:
        actual: Actual response JSON
        expected: Expected golden snapshot JSON
        path: Current JSON path (for error reporting)
    """
    # Type check
    assert type(actual) == type(expected), (
        f"Type mismatch at {path}: "
        f"actual={type(actual).__name__}, expected={type(expected).__name__}"
    )

    if isinstance(expected, dict):
        # Key set check
        actual_keys = set(actual.keys())
        expected_keys = set(expected.keys())

        missing_keys = expected_keys - actual_keys
        extra_keys = actual_keys - expected_keys

        assert not missing_keys, f"Missing keys at {path}: {missing_keys}"
        assert not extra_keys, f"Extra keys at {path}: {extra_keys}"

        # Recursive check for each key
        for key in expected_keys:
            deep_equal_assert(actual[key], expected[key], f"{path}.{key}")

    elif isinstance(expected, list):
        # List length check
        assert len(actual) == len(expected), (
            f"List length mismatch at {path}: "
            f"actual={len(actual)}, expected={len(expected)}"
        )

        # Recursive check for each element
        for i, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            deep_equal_assert(actual_item, expected_item, f"{path}[{i}]")

    else:
        # Value equality check
        assert actual == expected, (
            f"Value mismatch at {path}: "
            f"actual={repr(actual)}, expected={repr(expected)}"
        )


@pytest.mark.skipif(
    os.getenv("E2E_DOCKER") != "1",
    reason="Requires Docker environment (set E2E_DOCKER=1)"
)
class TestSTEP16RuntimeContractFreeze:
    """
    Golden snapshot tests for Compare API runtime contract.

    These tests call the actual Docker API and compare responses against
    golden snapshots from STEP 14.

    CRITICAL: Do NOT auto-regenerate golden snapshots.
    Any change must be explicitly approved as a breaking change.
    """

    API_BASE = "http://localhost:8000"

    def test_scenario_a_normal_comparison_golden_snapshot(self):
        """
        Scenario A: Normal Comparison (일반암진단비)

        Expected:
        - comparison_result: "comparable"
        - next_action: "COMPARE"
        - Both coverages MAPPED
        - No policy evidence
        - debug.universe_lock_enforced: true
        """
        import requests

        # Call actual API
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

        actual = response.json()
        golden = load_golden_snapshot("scenario_a")

        # Normalize and compare
        actual_normalized = normalize_response(actual)
        golden_normalized = normalize_response(golden)

        deep_equal_assert(actual_normalized, golden_normalized)

    def test_scenario_b_unmapped_coverage_golden_snapshot(self):
        """
        Scenario B: UNMAPPED Coverage (매핑안된담보)

        Expected:
        - comparison_result: "unmapped"
        - next_action: "REQUEST_MORE_INFO"
        - mapping_status: "UNMAPPED"
        - canonical_coverage_code: null
        - policy_evidence forbidden
        """
        import requests

        response = requests.post(
            f"{self.API_BASE}/compare",
            json={
                "query": "매핑안된담보",
                "insurer_a": "KB",
                "insurer_b": None,
                "include_policy_evidence": False
            },
            timeout=10
        )

        assert response.status_code == 200, f"HTTP {response.status_code}: {response.text}"

        actual = response.json()
        golden = load_golden_snapshot("scenario_b")

        actual_normalized = normalize_response(actual)
        golden_normalized = normalize_response(golden)

        deep_equal_assert(actual_normalized, golden_normalized)

    def test_scenario_c_disease_scope_required_golden_snapshot(self):
        """
        Scenario C: Disease Scope Required (유사암진단금)

        Expected:
        - comparison_result: "policy_required"
        - next_action: "VERIFY_POLICY"
        - disease_scope_norm: {include_group_id: null, exclude_group_id: null}
        - policy_evidence_a: exists (group_name, insurer, member_count)
        - source_confidence: "policy_required"
        """
        import requests

        response = requests.post(
            f"{self.API_BASE}/compare",
            json={
                "query": "유사암진단금",
                "insurer_a": "SAMSUNG",
                "insurer_b": None,
                "include_policy_evidence": True
            },
            timeout=10
        )

        assert response.status_code == 200, f"HTTP {response.status_code}: {response.text}"

        actual = response.json()
        golden = load_golden_snapshot("scenario_c")

        actual_normalized = normalize_response(actual)
        golden_normalized = normalize_response(golden)

        deep_equal_assert(actual_normalized, golden_normalized)

    def test_scenario_d_kb_meritz_comparison_golden_snapshot(self):
        """
        Scenario D: KB vs MERITZ Comparison (일반암진단비) - STEP 22

        Expected:
        - comparison_result: "comparable"
        - next_action: "COMPARE"
        - Both coverages MAPPED
        - Insurer pair: KB vs MERITZ
        - Different amounts (KB: 4000만원, MERITZ: 3000만원)
        - No policy evidence (disease_scope_norm is null)

        Contract Extension: Demonstrates new insurer pair pattern
        """
        import requests

        response = requests.post(
            f"{self.API_BASE}/compare",
            json={
                "query": "일반암진단비",
                "insurer_a": "KB",
                "insurer_b": None,
                "include_policy_evidence": False
            },
            timeout=10
        )

        assert response.status_code == 200, f"HTTP {response.status_code}: {response.text}"

        actual = response.json()
        golden = load_golden_snapshot("scenario_d")

        actual_normalized = normalize_response(actual)
        golden_normalized = normalize_response(golden)

        deep_equal_assert(actual_normalized, golden_normalized)

    def test_ux_message_code_contract(self):
        """
        UX Message Code Contract Validation.

        Ensures that UX message codes remain stable:
        - Scenario A: comparison_result = "comparable"
        - Scenario B: comparison_result = "unmapped"
        - Scenario C: comparison_result = "policy_required"

        Text may change, but codes MUST NOT.
        """
        golden_a = load_golden_snapshot("scenario_a")
        golden_b = load_golden_snapshot("scenario_b")
        golden_c = load_golden_snapshot("scenario_c")

        # Code contract assertions
        assert golden_a["comparison_result"] == "comparable", \
            "Scenario A: comparison_result code changed (breaking change)"

        assert golden_b["comparison_result"] == "unmapped", \
            "Scenario B: comparison_result code changed (breaking change)"

        assert golden_c["comparison_result"] == "policy_required", \
            "Scenario C: comparison_result code changed (breaking change)"

        # Next action contract
        assert golden_a["next_action"] == "COMPARE"
        assert golden_b["next_action"] == "REQUEST_MORE_INFO"
        assert golden_c["next_action"] == "VERIFY_POLICY"

    def test_debug_contract_lock(self):
        """
        Debug Contract Lock Validation.

        Ensures debug fields exist and remain stable:
        - universe_lock_enforced (required)
        - canonical_code_resolved (required)
        - raw_name_used (required)

        These fields are part of the developer contract and MUST NOT be removed.
        """
        golden_a = load_golden_snapshot("scenario_a")
        golden_b = load_golden_snapshot("scenario_b")
        golden_c = load_golden_snapshot("scenario_c")

        # Required debug fields
        required_debug_fields = {
            "universe_lock_enforced",
            "canonical_code_resolved",
            "raw_name_used"
        }

        for scenario_name, golden in [
            ("scenario_a", golden_a),
            ("scenario_b", golden_b),
            ("scenario_c", golden_c)
        ]:
            assert "debug" in golden, f"{scenario_name}: debug field missing"

            debug = golden["debug"]
            assert isinstance(debug, dict), f"{scenario_name}: debug must be dict"

            actual_fields = set(debug.keys())
            missing_fields = required_debug_fields - actual_fields

            assert not missing_fields, (
                f"{scenario_name}: Missing required debug fields: {missing_fields}"
            )

    def test_evidence_source_lock(self):
        """
        Evidence Source Lock Validation (STEP 17 clarification).

        Current API evidence sources:
        1. PROPOSAL (always - from proposal_coverage_universe)
        2. POLICY (conditional - only when disease_scope_norm exists)

        Note: PRODUCT_SUMMARY and BUSINESS_METHOD are not currently generated by API.
        Evidence order: PROPOSAL → POLICY (conditional)

        Order changes are breaking changes.
        """
        golden_a = load_golden_snapshot("scenario_a")
        golden_c = load_golden_snapshot("scenario_c")

        # Scenario A: No policy evidence (disease_scope_norm is null)
        assert golden_a["policy_evidence_a"] is None, \
            "Scenario A: policy_evidence must be null when disease_scope_norm is null"
        assert golden_a["policy_evidence_b"] is None

        # Scenario C: Policy evidence exists (disease_scope_norm present)
        assert golden_c["policy_evidence_a"] is not None, \
            "Scenario C: policy_evidence must exist when disease_scope_norm present"

        # Policy evidence structure validation
        policy_ev = golden_c["policy_evidence_a"]
        assert "group_name" in policy_ev
        assert "insurer" in policy_ev
        assert "member_count" in policy_ev

    def test_snapshot_canonical_json_policy(self):
        """
        Snapshot Canonical JSON Policy Enforcement (STEP 20).

        Ensures golden snapshots are stored in key-sorted canonical JSON format.
        This is NOT just a policy - it's an enforced contract.

        Contract:
        - Semantic equality (key order doesn't affect comparison)
        - Canonical storage (snapshots MUST be stored in sorted format)

        This test enforces canonical storage to prevent:
        - Manual edits that break formatting
        - Key order drift
        - Inconsistent snapshot formats
        """
        import json

        required_snapshots = ["scenario_a", "scenario_b", "scenario_c", "scenario_d"]

        for scenario_name in required_snapshots:
            snapshot_path = os.path.join(SNAPSHOTS_DIR, f"{scenario_name}.golden.json")

            # Load raw file content
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()

            # Parse JSON
            snapshot_dict = json.loads(raw_content)

            # Re-serialize with canonical format (sorted keys, 4-space indent, no ASCII escaping)
            canonical_json = json.dumps(snapshot_dict, indent=4, sort_keys=True, ensure_ascii=False)

            # Add trailing newline (standard for text files)
            canonical_with_newline = canonical_json + "\n"

            # ENFORCE: File content must exactly match canonical format
            assert raw_content == canonical_with_newline, (
                f"{scenario_name}: Snapshot is not in canonical JSON format.\n"
                f"Expected canonical format with:\n"
                f"  - sort_keys=True\n"
                f"  - indent=4\n"
                f"  - ensure_ascii=False\n"
                f"  - trailing newline\n"
                f"\n"
                f"To fix, regenerate with:\n"
                f"  python -m json.tool --sort-keys {snapshot_path} > {snapshot_path}.tmp && mv {snapshot_path}.tmp {snapshot_path}\n"
                f"\n"
                f"CRITICAL: This is a contract violation. Golden snapshots must maintain canonical format."
            )

    def test_golden_snapshots_exist(self):
        """
        Golden Snapshot Existence Validation.

        Ensures all required golden snapshots exist and are valid JSON.
        """
        required_snapshots = ["scenario_a", "scenario_b", "scenario_c", "scenario_d"]

        for scenario_name in required_snapshots:
            snapshot = load_golden_snapshot(scenario_name)

            # Basic structure validation
            assert isinstance(snapshot, dict), \
                f"{scenario_name}: golden snapshot must be dict"

            assert "query" in snapshot, \
                f"{scenario_name}: missing 'query' field"

            assert "comparison_result" in snapshot, \
                f"{scenario_name}: missing 'comparison_result' field"

            assert "debug" in snapshot, \
                f"{scenario_name}: missing 'debug' field"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
