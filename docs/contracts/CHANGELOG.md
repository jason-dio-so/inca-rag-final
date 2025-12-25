# Contract Change Log (Golden Snapshots)

> **Purpose**: Track all changes to Compare API runtime contract (golden snapshots).
>
> **Policy**: Any change to `tests/snapshots/compare/*.golden.json` MUST have an entry here.
>
> **Format**:
> - Date (YYYY-MM-DD)
> - STEP number
> - Change type: FORMAT_ONLY / CONTRACT_CHANGE / BUGFIX_CONTRACT_CHANGE
> - Affected scenarios
> - Reason for change
> - Approver/Author

---

## 2025-12-25 (STEP 26) - CONTRACT_CHANGE

**Change Type**: CONTRACT_CHANGE

**Affected Files**:
- `tests/snapshots/compare/scenario_a.golden.json`
- `tests/snapshots/compare/scenario_b.golden.json`
- `tests/snapshots/compare/scenario_c.golden.json`
- `tests/snapshots/compare/scenario_d.golden.json`
- `tests/snapshots/compare/scenario_e.golden.json`

**Changes**:
- Added `ux_message_code` field to all golden snapshots
- New field complements existing `message` field (text remains free-form)
- UX message codes are now part of the runtime contract

**Details**:
- Scenario A: `ux_message_code: "COVERAGE_MATCH_COMPARABLE"`
- Scenario B: `ux_message_code: "COVERAGE_UNMAPPED"`
- Scenario C: `ux_message_code: "DISEASE_SCOPE_VERIFICATION_REQUIRED"`
- Scenario D: `ux_message_code: "COVERAGE_MATCH_COMPARABLE"`
- Scenario E: `ux_message_code: "COVERAGE_NOT_IN_UNIVERSE"`

**Registry**:
- SSOT: `apps/api/app/contracts/ux_message_codes.py`
- ALLOWED_UX_MESSAGE_CODES: 7 codes
- Naming convention: UPPER_SNAKE_CASE
- Runtime validation: `validate_ux_message_code()`

**Reason**:
- Decouple UX message "codes" (contract) from "text" (non-contract)
- Enable i18n/UX improvements without breaking runtime contract
- Provide deterministic UX state identification
- Extend STEP 24/25 registry governance to UX messages

**Impact**:
- Non-breaking addition (new field only)
- Existing fields (message, comparison_result, next_action) unchanged
- CI enforcement: STEP 26 tests + governance gate
- Future UX message text changes do NOT require CHANGELOG update
- Future UX message CODE changes DO require CHANGELOG update

**Approver**: STEP 26 Implementation (UX Message Code Registry & Contract Enforcement)

---

## 2025-12-25 (STEP 23) - CONTRACT_CHANGE

**Change Type**: CONTRACT_CHANGE

**Affected Files**:
- `tests/snapshots/compare/scenario_e.golden.json` (NEW)

**Changes**:
- Added Scenario E: Out-of-Universe query contract
- Query: "다빈치 수술비" (Da Vinci surgery cost)
- Insurer: SAMSUNG (primary)
- Contract pattern: `out_of_universe` with `next_action: REQUEST_MORE_INFO`

**Details**:
- comparison_result: out_of_universe
- next_action: REQUEST_MORE_INFO
- coverage_a: null
- coverage_b: null
- policy_evidence_a: null
- policy_evidence_b: null
- debug.universe_lock_enforced: true
- debug.canonical_code_resolved: null

**Reason**:
- Establish "data not found" as a meaningful contract state (not a failure)
- Formalize Universe Lock enforcement (STEP 6-C constitutional principle)
- Provide explicit runtime contract for out-of-scope queries
- Ensure UX/CI/Runtime consistency for edge cases

**Impact**:
- Non-breaking addition (extends contract, does not modify existing)
- Existing scenarios A/B/C/D unchanged
- New test: `test_scenario_e_out_of_universe_golden_snapshot`
- Total golden scenarios: 5 (A/B/C/D/E)
- Proves graceful degradation is part of the contract

**Approver**: STEP 23 Implementation (Out-of-Universe Contract Formalization)

---

## 2025-12-25 (STEP 22) - CONTRACT_CHANGE

**Change Type**: CONTRACT_CHANGE

**Affected Files**:
- `tests/snapshots/compare/scenario_d.golden.json` (NEW)

**Changes**:
- Added Scenario D: KB vs MERITZ general cancer comparison
- Query: "일반암진단비"
- Insurer pair: KB (primary) vs MERITZ (auto-matched)
- Contract pattern: `comparable` with different amounts

**Details**:
- coverage_a: KB 일반암 진단비 (4000만원)
- coverage_b: MERITZ 암진단금(일반암) (3000만원)
- canonical_coverage_code: CA_DIAG_GENERAL
- comparison_result: comparable
- next_action: COMPARE

**Reason**:
- Demonstrate contract extension via new golden scenario (STEP 22)
- Validate governance protocol: new scenarios require CHANGELOG approval
- Expand test coverage to KB insurer (previously untested in runtime contracts)
- Prove existing golden scenarios (A/B/C) remain unchanged

**Impact**:
- Non-breaking addition (extends contract, does not modify existing)
- Existing scenarios A/B/C unchanged
- New test: `test_scenario_d_kb_meritz_comparison_golden_snapshot`
- Total golden scenarios: 4 (A/B/C/D)

**Approver**: STEP 22 Implementation (Contract Extension Validation)

---

## 2025-12-25 (STEP 21) - GOVERNANCE_SETUP

**Change Type**: GOVERNANCE_SETUP

**Affected Files**: None (initial setup)

**Changes**:
- Established Golden Change Approval Protocol
- Created this CHANGELOG to track all future golden snapshot changes
- Added CI gate to enforce approval process

**Reason**:
- Prevent unauthorized runtime contract changes
- Ensure all API contract modifications are documented and approved
- Enable 1-minute traceability for "why did the contract change?"

**Impact**: None (no golden snapshots modified in this STEP)

**Approver**: System (initial governance setup)

---

## 2025-12-25 (STEP 20) - FORMAT_ONLY

**Change Type**: FORMAT_ONLY

**Affected Files**:
- `tests/snapshots/compare/scenario_a.golden.json`
- `tests/snapshots/compare/scenario_b.golden.json`
- `tests/snapshots/compare/scenario_c.golden.json`

**Changes**:
- Regenerated all snapshots to canonical JSON format
- Format: `json.dumps(sort_keys=True, indent=4, ensure_ascii=False) + '\n'`
- No semantic changes to contract data

**Reason**:
- Enforce canonical storage format (STEP 20)
- Enable format violation detection via tests
- Prevent manual edits that break formatting

**Impact**: Semantic contract unchanged, storage format standardized

**Approver**: STEP 20 Implementation (canonical format enforcement)

---

## Template for Future Changes

```markdown
## YYYY-MM-DD (STEP XX) - CHANGE_TYPE

**Change Type**: FORMAT_ONLY / CONTRACT_CHANGE / BUGFIX_CONTRACT_CHANGE

**Affected Files**:
- `tests/snapshots/compare/scenario_*.golden.json`

**Changes**:
- Describe what changed in the golden snapshot
- List affected scenarios (A/B/C)

**Reason**:
- Why was this change necessary?
- What bug/feature/refactoring triggered it?

**Impact**:
- Breaking change? (yes/no)
- Backward compatibility?
- User-facing behavior change?

**Approver**: [Name/Role]
```

---

## Change Type Definitions

- **FORMAT_ONLY**: Formatting/whitespace changes only, no semantic change
- **CONTRACT_CHANGE**: Intentional API contract modification (breaking or non-breaking)
- **BUGFIX_CONTRACT_CHANGE**: Contract change due to bug fix (semantic correction)

---

## Approval Process

1. Modify golden snapshot(s) as needed
2. Add entry to this CHANGELOG (latest on top)
3. Commit both changes together
4. CI will verify CHANGELOG was updated
5. PR reviewer approves contract change
6. Merge after CI passes
