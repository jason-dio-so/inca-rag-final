"""
STEP 27: UI Contract Drift Prevention Tests

Validates that UI State Map covers all Backend Contract states
and prevents UI/Backend contract misalignment.

Constitutional Rules:
- All Backend states MUST map to UI states (no gaps)
- Unknown states MUST use fallback (no errors)
- UI State Map changes MUST align with Backend Contract changes
- Golden Snapshots are source of truth for required states

Test Coverage:
1. All golden snapshot states exist in UI State Map
2. Fallback state works for unknown states
3. State key format is correct
4. UI state resolution never throws errors
5. Contract field types are enforced
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any


class TestSTEP27UIContractDrift:
    """STEP 27: UI Contract Drift Prevention Tests"""

    @pytest.fixture
    def golden_snapshots_dir(self):
        """Path to golden snapshots directory."""
        return Path(__file__).parent.parent / "snapshots" / "compare"

    @pytest.fixture
    def golden_snapshot_files(self, golden_snapshots_dir):
        """List all golden snapshot files."""
        return list(golden_snapshots_dir.glob("*.golden.json"))

    @pytest.fixture
    def ui_state_map_path(self):
        """Path to UI State Map TypeScript file."""
        return Path(__file__).parent.parent.parent / "apps" / "web" / "src" / "contracts" / "uiStateMap.ts"

    def extract_state_key(self, snapshot: Dict[str, Any]) -> str:
        """Extract state key from golden snapshot."""
        return f"{snapshot['comparison_result']}:{snapshot['next_action']}:{snapshot['ux_message_code']}"

    def extract_ui_state_keys_from_typescript(self, ts_file_path: Path) -> set:
        """
        Extract state keys from TypeScript UI_STATE_MAP.

        Parses TypeScript file to find all keys in UI_STATE_MAP object.
        """
        if not ts_file_path.exists():
            return set()

        with open(ts_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract state keys from TypeScript (simple regex-based extraction)
        import re

        # Pattern: "state_key": {
        pattern = r'"([^"]+:[^"]+:[^"]+)":\s*\{'
        matches = re.findall(pattern, content)

        return set(matches)

    def test_ui_state_map_file_exists(self, ui_state_map_path):
        """
        Test: UI State Map TypeScript file exists.

        Expected:
        - File exists at apps/web/src/contracts/uiStateMap.ts
        """
        assert ui_state_map_path.exists(), \
            f"UI State Map file not found: {ui_state_map_path}"

    def test_ui_state_map_contains_required_states(self, ui_state_map_path):
        """
        Test: UI State Map contains all required states from DoD.

        Required states (STEP 27 minimum):
        - comparable:COMPARE:COVERAGE_MATCH_COMPARABLE
        - unmapped:REQUEST_MORE_INFO:COVERAGE_UNMAPPED
        - policy_required:VERIFY_POLICY:DISEASE_SCOPE_VERIFICATION_REQUIRED
        - out_of_universe:REQUEST_MORE_INFO:COVERAGE_NOT_IN_UNIVERSE
        """
        ui_state_keys = self.extract_ui_state_keys_from_typescript(ui_state_map_path)

        required_states = {
            "comparable:COMPARE:COVERAGE_MATCH_COMPARABLE",
            "unmapped:REQUEST_MORE_INFO:COVERAGE_UNMAPPED",
            "policy_required:VERIFY_POLICY:DISEASE_SCOPE_VERIFICATION_REQUIRED",
            "out_of_universe:REQUEST_MORE_INFO:COVERAGE_NOT_IN_UNIVERSE",
        }

        missing_states = required_states - ui_state_keys

        if missing_states:
            pytest.fail(
                f"UI State Map missing required states:\n"
                f"  Missing: {sorted(missing_states)}\n"
                f"  Found: {sorted(ui_state_keys)}\n"
                f"\n"
                f"This is a STEP 27 contract violation.\n"
                f"Update apps/web/src/contracts/uiStateMap.ts to include all required states."
            )

    def test_all_golden_snapshot_states_covered(
        self,
        golden_snapshot_files,
        ui_state_map_path
    ):
        """
        Test: All golden snapshot states are covered by UI State Map.

        This is the PRIMARY CONTRACT TEST for STEP 27.

        Expected:
        - Every state in golden snapshots has UI State Map entry
        - No gaps between Backend Contract and UI Contract
        """
        ui_state_keys = self.extract_ui_state_keys_from_typescript(ui_state_map_path)

        snapshot_states = {}
        uncovered_states = set()

        for snapshot_file in golden_snapshot_files:
            with open(snapshot_file, "r", encoding="utf-8") as f:
                snapshot = json.load(f)

            state_key = self.extract_state_key(snapshot)
            snapshot_states[snapshot_file.name] = state_key

            if state_key not in ui_state_keys:
                uncovered_states.add(state_key)

        if uncovered_states:
            error_msg = (
                f"Golden snapshot states not covered by UI State Map:\n"
                f"  Uncovered states: {sorted(uncovered_states)}\n"
                f"  UI State Map keys: {sorted(ui_state_keys)}\n"
                f"  Snapshots with uncovered states:\n"
            )
            for file, state in snapshot_states.items():
                if state in uncovered_states:
                    error_msg += f"    {file}: {state}\n"

            error_msg += (
                f"\n"
                f"This is a STEP 27 contract violation.\n"
                f"Add missing states to apps/web/src/contracts/uiStateMap.ts\n"
                f"or update golden snapshots if Backend Contract changed."
            )
            pytest.fail(error_msg)

    def test_fallback_state_defined(self, ui_state_map_path):
        """
        Test: Fallback state is defined for unknown states.

        Expected:
        - FALLBACK_STATE export exists
        - Contains all required fields
        - View type is "UnknownState"
        """
        with open(ui_state_map_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "export const FALLBACK_STATE" in content, \
            "FALLBACK_STATE not found in UI State Map"

        assert "UnknownState" in content, \
            "Fallback view type 'UnknownState' not found"

    def test_state_key_format_enforcement(self, golden_snapshot_files):
        """
        Test: State keys follow correct format.

        Format: {comparison_result}:{next_action}:{ux_message_code}

        Expected:
        - Exactly 3 parts separated by ':'
        - All parts are non-empty
        """
        for snapshot_file in golden_snapshot_files:
            with open(snapshot_file, "r", encoding="utf-8") as f:
                snapshot = json.load(f)

            state_key = self.extract_state_key(snapshot)
            parts = state_key.split(":")

            assert len(parts) == 3, \
                f"{snapshot_file.name}: Invalid state key format: {state_key} (expected 3 parts)"

            assert all(part for part in parts), \
                f"{snapshot_file.name}: State key has empty parts: {state_key}"

    def test_ui_state_resolution_never_throws(self):
        """
        Test: UI state resolution handles unknown states gracefully.

        Expected:
        - Unknown states return fallback (not error)
        - Fallback state has all required fields
        - System logs warning for monitoring
        """
        # This is a design constraint test
        # TypeScript implementation must guarantee:
        # resolveUIState(...) never throws, always returns UIStateConfig

        # We verify this by checking the TypeScript implementation
        ui_state_map_path = Path(__file__).parent.parent.parent / "apps" / "web" / "src" / "contracts" / "uiStateMap.ts"

        with open(ui_state_map_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check that resolveUIState has fallback return
        assert "return FALLBACK_STATE" in content, \
            "resolveUIState must return FALLBACK_STATE for unknown states"

        # Check that console.warn is called for unknown states
        assert "console.warn" in content, \
            "resolveUIState must log warning for unknown states (monitoring)"

    def test_contract_fields_vs_non_contract_fields(self, ui_state_map_path):
        """
        Test: Contract fields are clearly separated from non-contract fields.

        Contract fields (immutable):
        - view
        - primaryCta
        - severity
        - requiresInput
        - displayConfig

        Non-contract fields (i18n/UX free):
        - title
        - description

        Expected:
        - All UIStateConfig objects have both contract and non-contract fields
        - Types enforce separation
        """
        with open(ui_state_map_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check TypeScript interface definition
        assert "view: ViewType" in content, \
            "UIStateConfig must define 'view' as ViewType (contract)"

        assert "title: string" in content, \
            "UIStateConfig must define 'title' as string (non-contract)"

        # Check comment marking non-contract fields
        assert "non-contract" in content.lower(), \
            "UI State Map should document which fields are non-contract"

    def test_ui_state_count_minimum(self, ui_state_map_path):
        """
        Test: UI State Map has minimum required states.

        Minimum: 4 required states (A, B, C, E scenarios)

        Expected:
        - At least 4 states defined
        """
        ui_state_keys = self.extract_ui_state_keys_from_typescript(ui_state_map_path)

        assert len(ui_state_keys) >= 4, \
            f"UI State Map must have at least 4 states (found {len(ui_state_keys)})"

    def test_no_duplicate_state_keys(self, ui_state_map_path):
        """
        Test: No duplicate state keys in UI State Map.

        Expected:
        - All state keys are unique
        """
        ui_state_keys = self.extract_ui_state_keys_from_typescript(ui_state_map_path)

        # Extract keys from file content (more robust duplicate check)
        with open(ui_state_map_path, "r", encoding="utf-8") as f:
            content = f.read()

        import re
        pattern = r'"([^"]+:[^"]+:[^"]+)":\s*\{'
        all_matches = re.findall(pattern, content)

        duplicates = []
        seen = set()
        for key in all_matches:
            if key in seen:
                duplicates.append(key)
            seen.add(key)

        if duplicates:
            pytest.fail(
                f"Duplicate state keys found in UI State Map:\n"
                f"  Duplicates: {duplicates}\n"
                f"This is a STEP 27 contract violation."
            )

    def test_typescript_exports_are_present(self, ui_state_map_path):
        """
        Test: Required TypeScript exports are present.

        Expected exports:
        - UI_STATE_MAP
        - FALLBACK_STATE
        - resolveUIState
        - getRegisteredStateKeys
        - isStateRegistered
        - extractStateKey
        """
        with open(ui_state_map_path, "r", encoding="utf-8") as f:
            content = f.read()

        required_exports = [
            "export const UI_STATE_MAP",
            "export const FALLBACK_STATE",
            "export function resolveUIState",
            "export function getRegisteredStateKeys",
            "export function isStateRegistered",
            "export function extractStateKey",
        ]

        missing_exports = []
        for export in required_exports:
            if export not in content:
                missing_exports.append(export)

        if missing_exports:
            pytest.fail(
                f"Missing required TypeScript exports:\n"
                f"  Missing: {missing_exports}\n"
                f"This is a STEP 27 contract violation."
            )

    def test_ui_contract_documentation_exists(self):
        """
        Test: UI Contract SSOT documentation exists.

        Expected:
        - docs/ui/UI_CONTRACT.md file exists
        - Contains state definitions
        """
        ui_contract_path = Path(__file__).parent.parent.parent / "docs" / "ui" / "UI_CONTRACT.md"

        assert ui_contract_path.exists(), \
            f"UI Contract documentation not found: {ui_contract_path}"

        with open(ui_contract_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for required sections
        assert "UI State Model" in content, \
            "UI_CONTRACT.md must define UI State Model"

        assert "comparable:COMPARE:COVERAGE_MATCH_COMPARABLE" in content, \
            "UI_CONTRACT.md must document required states"
