# STEP NEXT-5: ViewModel Assembler + Frontend Renderer (Complete)

> **Status**: Backend Complete | Frontend Complete

---

## 0. Summary

**Completed**:
- Backend: ViewModel assembler, endpoint, validation, and tests
- Frontend: 3-Block React renderer with ChatGPT-style layout

---

## 1. Constitutional Compliance

- ✅ **Fact-only**: No inference, status from existing data only
- ✅ **No Recommendations**: Zero judgment phrases (test-enforced)
- ✅ **Presentation Layer Only**: Assembler is pure mapping/formatting
- ✅ **Deterministic**: Same input → same output (test-verified)
- ✅ **Schema-validated**: Runtime validation against JSON Schema

---

## 2. Backend Implementation

### 2.1 Module Structure

```
apps/api/app/view_model/
├── __init__.py         # Module exports
├── types.py            # Pydantic models matching JSON Schema
├── schema_loader.py    # JSON Schema loader + validator
└── assembler.py        # ProposalCompareResponse → ViewModel
```

### 2.2 Input Shape (ProposalCompareResponse)

**Source**: `apps/api/app/schemas/compare.py:ProposalCompareResponse`

```python
{
    "query": str,
    "comparison_result": str,  # comparable|comparable_with_gaps|non_comparable|unmapped|out_of_universe
    "next_action": str,
    "coverage_a": ProposalCoverageItem | None,
    "coverage_b": ProposalCoverageItem | None,
    "policy_evidence_a": PolicyEvidence | None,
    "policy_evidence_b": PolicyEvidence | None,
    "message": str,
    "ux_message_code": str,
    "debug": dict | None
}
```

**ProposalCoverageItem** fields:
- `insurer`, `proposal_id`, `coverage_name_raw`
- `canonical_coverage_code`, `mapping_status` (MAPPED/UNMAPPED/AMBIGUOUS)
- `amount_value`, `disease_scope_raw`, `disease_scope_norm`
- `source_confidence`

### 2.3 Output Shape (ViewModel)

**Contract**: `docs/ui/compare_view_model.schema.json` (JSON Schema Draft 2020-12)

```json
{
  "schema_version": "next4.v1",
  "generated_at": "ISO8601",
  "header": {...},          // BLOCK 0: User Query
  "snapshot": {...},        // BLOCK 1: Coverage Snapshot
  "fact_table": {...},      // BLOCK 2: Fact Table
  "evidence_panels": [...], // BLOCK 3: Evidence Accordion
  "debug": {...}            // Non-UI (reproducibility)
}
```

### 2.4 Assembler Logic

**File**: `apps/api/app/view_model/assembler.py`

**Key Functions**:
- `assemble_view_model(compare_response, include_debug=True) → ViewModel`
- `map_status(comparison_result, mapping_status, has_policy_evidence) → StatusCode`
- `format_amount(amount_value) → AmountInfo` (만원 conversion)
- `generate_evidence_id(insurer, doc_type, index) → str` (deterministic)
- `extract_payout_conditions(coverage, evidence_id) → List[PayoutCondition]`

**Status Mapping Rules** (Deterministic, Conservative):
| Input | Output | Rationale |
|-------|--------|-----------|
| mapping_status=UNMAPPED | UNMAPPED | Direct mapping |
| mapping_status=AMBIGUOUS | AMBIGUOUS | Direct mapping |
| comparison_result=out_of_universe | OUT_OF_UNIVERSE | Universe Lock |
| comparison_result=comparable + MAPPED | OK | Normal case |
| comparison_result=comparable_with_gaps | MISSING_EVIDENCE | Conservative |
| comparison_result=non_comparable | OK | Fact exists (different type) |
| Otherwise | MISSING_EVIDENCE | Conservative fallback |

**Amount Formatting**:
- Input: `amount_value` in 원 (e.g., 30000000)
- Output: AmountInfo with `amount_value=3000`, `amount_unit="만원"`, `display_text="3,000만원"`

**Evidence ID Generation**:
- Format: `ev_{insurer}_{doc_type}_{index}`
- Example: `ev_samsung_proposal_001`
- Deterministic (same input → same ID)

**Deterministic Sorting**:
- `fact_table.rows`: Sort by (insurer ASC, coverage_title ASC)
- `evidence_panels`: Sort by (insurer ASC, doc_type ASC, id ASC)

---

## 3. Endpoint

**URL**: `/compare/view-model`

**Method**: POST

**Request**: `ProposalCompareRequest` (same as `/compare`)

**Response**: ViewModel JSON (schema-validated)

**Implementation**: `apps/api/app/routers/view_model.py`

**Flow**:
1. Call existing `/compare` logic (reuses `compare_proposals` function)
2. Assemble ViewModel from ProposalCompareResponse
3. **Runtime schema validation** (fail-fast if invalid)
4. Return ViewModel JSON

**Configuration**:
- `ENABLE_VIEW_MODEL_VALIDATION=1` (env, default ON)
- Set to `0` to disable runtime validation (not recommended)

**Registration**: `apps/api/app/main.py` (router registered)

---

## 4. Tests

**File**: `tests/test_view_model_assembler.py`

**Test Coverage** (15/15 passing):

| Test | Purpose |
|------|---------|
| `test_assembler_output_validates_against_schema` | JSON Schema compliance |
| `test_evidence_ref_id_integrity` | All ref_ids resolve to panels |
| `test_no_forbidden_phrases_in_system_fields` | Hard-ban enforcement |
| `test_schema_version_format` | Version pattern compliance |
| `test_deterministic_output` | Reproducibility |
| `test_fact_table_columns_fixed` | Column order immutable |
| `test_fact_table_deterministic_sort` | Stable sorting |
| `test_unmapped_status_mapping` | UNMAPPED → UNMAPPED |
| `test_out_of_universe_handling` | OUT_OF_UNIVERSE edge case |
| `test_policy_evidence_added_to_panels` | Policy evidence integration |
| `test_amount_formatting` | 원 → 만원 conversion |
| `test_debug_section_optional` | Debug can be excluded |
| `test_canonical_coverage_code_in_debug` | Codes in debug only |
| `test_excerpt_length_constraints` | Min 25 chars |
| `test_insurer_codes_uppercase` | Canonical format |

**Golden Samples** (Fixtures):
1. `sample_comparable_response`: Scenario A (both MAPPED)
2. `sample_unmapped_response`: Scenario B (UNMAPPED)
3. `sample_out_of_universe_response`: OUT_OF_UNIVERSE
4. `sample_with_policy_evidence_response`: Scenario C (policy evidence)

**Run Tests**:
```bash
python -m pytest tests/test_view_model_assembler.py -v
```

---

## 5. Schema Updates

**File**: `docs/ui/compare_view_model.schema.json`

**Updates**:
- `bbox`: Type changed to `["object", "null"]` (allow null)
- `source_meta`: Type changed to `["object", "null"]` (allow null)
- `debug.resolved_coverage_codes`: Type changed to `["array", "null"]`
- `debug.retrieval`: Type changed to `["object", "null"]`
- `debug.retrieval.topk`: Type changed to `["number", "null"]`
- `debug.retrieval.strategy`: Type changed to `["string", "null"]`
- `debug.retrieval.doc_priority`: Type changed to `["array", "null"]`
- `debug.warnings`: Type changed to `["array", "null"]`
- `debug.execution_time_ms`: Type changed to `["number", "null"]`

**Rationale**: Pydantic models emit `null` for optional fields when not set, requiring schema to accept `null`.

---

## 6. Frontend Implementation

**Status**: **COMPLETE**

### 6.1 Component Structure

```
apps/web/src/
├── components/compare/
│   ├── CompareViewModelRenderer.tsx  # Entry component (3-Block layout)
│   ├── ChatHeader.tsx                # BLOCK 0: User query display
│   ├── CoverageSnapshot.tsx          # BLOCK 1: Per-insurer snapshot
│   ├── FactTable.tsx                 # BLOCK 2: Comparison table
│   └── EvidenceAccordion.tsx         # BLOCK 3: Collapsible evidence
└── lib/compare/
    └── viewModelTypes.ts             # TypeScript types from JSON Schema
```

### 6.2 Implementation Details

**CompareViewModelRenderer** (Entry):
- Renders 3-Block ChatGPT-style layout
- Takes `CompareViewModel` prop (schema-validated JSON)
- Constitutional enforcement: Debug section NEVER rendered
- No sorting/filtering/scoring (presentation only)

**BLOCK 0: ChatHeader**:
- Displays `user_query` (primary, large font)
- Displays `normalized_query` (optional, small font)
- No coverage_code or internal identifiers shown

**BLOCK 1: CoverageSnapshot**:
- Shows `comparison_basis` (canonical coverage name)
- Lists insurers in ViewModel order (no reordering)
- Displays `headline_amount.display_text` if present
- Shows status text if amount is null (OK/MISSING_EVIDENCE/UNMAPPED/etc.)
- No "same/different" interpretation text

**BLOCK 2: FactTable**:
- Fixed 6-column layout (immutable order per schema)
- Columns: 보험사, 담보명(정규화), 보장금액, 지급 조건 요약, 보험기간, 비고
- Shows "—" for null `benefit_amount`
- `payout_conditions` rendered as bullet list:
  - Each item: Korean label (대기기간, 지급횟수, etc.) + value_text
  - No text generation or interpretation
- Rows displayed in ViewModel order (no frontend sorting)

**BLOCK 3: EvidenceAccordion**:
- Groups evidence by insurer (collapsible accordion UI)
- Shows: doc_type badge, doc_title, page number, excerpt
- Excerpt displayed as-is (no summarization/rewriting)
- Neutral message if no evidence: "근거 문서 정보 없음"

### 6.3 Edge Case Handling

| Case | Behavior |
|------|----------|
| `status=OUT_OF_UNIVERSE` | Snapshot/table/evidence may be empty, no UI crash |
| Empty `evidence_panels` | Shows neutral message, no recommendation phrases |
| `benefit_amount=null` | Shows "—" in table |
| `payout_conditions=[]` | Shows "—" in table |
| UNMAPPED/AMBIGUOUS | Shows status in note_text, displays data as-is |

### 6.4 Test Page

**URL**: `/compare-test`

**Features**:
- Example selector (loads from `/public/data/compare_view_model.examples.json`)
- Live API test button (calls `/compare/view-model` endpoint)
- Renders ViewModel with CompareViewModelRenderer
- Error handling for network failures (neutral message only)

**Verification**:
- ✅ Build passes (type-safe)
- ✅ JSON examples load correctly
- ✅ Page renders without crash
- ✅ Debug section not displayed

### 6.5 Constitutional Compliance

| Principle | Frontend Implementation |
|-----------|-------------------------|
| Fact-only | Display ViewModel data as-is, no modification |
| No Recommendation | Zero "better/worse/same/different" phrases |
| Presentation Only | No sorting/filtering/scoring in frontend |
| Debug Non-UI | Debug section completely hidden (hardcoded) |
| Fixed Layout | 3-Block structure immutable, column order fixed |

---

## 7. Integration Checklist

- ✅ Backend module structure created
- ✅ Assembler implemented (deterministic, no inference)
- ✅ `/compare/view-model` endpoint created
- ✅ Runtime schema validation enabled
- ✅ 15 tests passing (100% coverage)
- ✅ Schema updated (allow null for optional fields)
- ✅ Evidence ref_id integrity guaranteed
- ✅ Hard-ban phrases test-enforced
- ✅ Frontend 5 components implemented
- ✅ TypeScript types from JSON Schema
- ✅ Test page (`/compare-test`) functional
- ✅ Build passes (type-safe)
- ✅ Debug section non-display enforced
- ✅ Documentation complete

---

## 8. Constitutional Verification

| Principle | Implementation |
|-----------|----------------|
| Fact-only | Status from existing data, no new inference |
| No Recommendation | Forbidden phrases test (0 violations) |
| Presentation Only | Assembler is pure mapping/formatting |
| Canonical Coverage | Internal codes in debug, UI uses normalized names |
| Coverage Universe Lock | OUT_OF_UNIVERSE status for non-proposal |
| Evidence Rule | All amounts have evidence_ref_id |
| Deterministic Output | Test-verified reproducibility |

---

## 9. DoD Achievement

**Backend**:
- ✅ `/compare/view-model` endpoint schema-compliant
- ✅ Assembler output validates against JSON Schema
- ✅ Hard-ban auto-test passing
- ✅ Evidence ref_id integrity test passing
- ✅ 15/15 tests passing

**Frontend**:
- ✅ CompareViewModelRenderer renders schema-compliant ViewModel
- ✅ 3-Block structure implemented (Header, Snapshot, FactTable, Evidence)
- ✅ Debug section non-display enforced
- ✅ Edge cases handled (UNMAPPED, OUT_OF_UNIVERSE, empty panels)
- ✅ Test page functional with example data
- ✅ Build passes (type-safe)

**Documentation**:
- ✅ Backend + Frontend implementation documented
- ✅ Constitutional compliance verified

---

**Document Version**: 2.0.0
**Date**: 2025-12-26
**Status**: Backend Complete + Frontend Complete
