# STEP NEXT-10 Implementation Plan

**Status:** Schema v2 LOCKED (Commit: 1f85282)
**Remaining:** Backend Assembler + E2E Tests

---

## Completed (2025-12-26)

### 1. ViewModel Schema v2 ✅
- **File:** `docs/ui/compare_view_model.schema.json`
- **Version:** next4.v2
- **Changes:** 5 optional fields added (non-breaking)
- **Changelog:** `docs/ui/VIEWMODEL_SCHEMA_CHANGELOG.md`

---

## Remaining Work

### 2. Backend ViewModel Assembler (High Priority)

**File:** `apps/api/app/view_model/assembler.py`

**Required Enhancements:**

#### 2.1. Add v2 Field Population
```python
def assemble_viewmodel_v2(compare_result: CompareResult, request: CompareRequest) -> dict:
    """
    Assemble ViewModel v2 from comparison results.

    NO new decisions, follow INCA_DIO_REQUIREMENTS.md compilation rules only.
    """
    viewmodel = {
        "schema_version": "next4.v2",
        "generated_at": datetime.utcnow().isoformat(),
        "header": _assemble_header(request),
        "snapshot": _assemble_snapshot_v2(compare_result, request),  # NEW: filter_criteria
        "fact_table": _assemble_fact_table_v2(compare_result, request),  # NEW: 4 fields
        "evidence_panels": _assemble_evidence_panels(compare_result),
        "debug": _assemble_debug(compare_result)
    }
    return viewmodel
```

#### 2.2. snapshot.filter_criteria Population
```python
def _assemble_snapshot_v2(compare_result, request):
    snapshot = _assemble_snapshot_v1(compare_result)  # Keep v1 logic

    # v2 enhancement
    filter_criteria = None
    if request.insurers:  # Explicit insurer filter (Example 3)
        filter_criteria = {"insurer_filter": request.insurers}

    if request.disease_scope:  # Disease filter (Example 4)
        if not filter_criteria:
            filter_criteria = {}
        filter_criteria["disease_scope"] = request.disease_scope

    if request.slot_comparison:  # Slot-specific comparison (Example 2)
        if not filter_criteria:
            filter_criteria = {}
        filter_criteria["slot_key"] = request.slot_comparison.slot_key
        filter_criteria["difference_detected"] = _detect_differences(compare_result)

    snapshot["filter_criteria"] = filter_criteria
    return snapshot
```

#### 2.3. fact_table v2 Fields
```python
def _assemble_fact_table_v2(compare_result, request):
    fact_table = _assemble_fact_table_v1(compare_result)  # Keep v1 logic

    # v2 enhancements
    fact_table["table_type"] = _detect_table_type(request)  # "default" | "ox_matrix"
    fact_table["sort_metadata"] = _get_sort_metadata(request)  # Sort config
    fact_table["visual_emphasis"] = _get_visual_emphasis(request)  # Min/max styling

    # Add highlight to rows where differences detected
    for row in fact_table["rows"]:
        row["highlight"] = _detect_row_highlights(row, compare_result)

    return fact_table
```

**Helper Functions:**

```python
def _detect_table_type(request):
    """Detect if O/X matrix needed (Example 4: disease-based coverage)."""
    if request.disease_scope and len(request.coverages) > 1:
        return "ox_matrix"
    return "default"

def _get_sort_metadata(request):
    """Extract sort config from request (Example 1: premium sorting)."""
    if request.sort_by:
        return {
            "sort_by": request.sort_by,
            "sort_order": request.sort_order or "asc",
            "limit": request.limit
        }
    return None

def _get_visual_emphasis(request):
    """Get min/max styling config (Example 1: premium emphasis)."""
    if request.emphasis_premium:
        return {
            "min_value_style": "blue",
            "max_value_style": "red"
        }
    return None

def _detect_row_highlights(row, compare_result):
    """Detect which cells to highlight (Example 2: difference emphasis)."""
    highlights = []
    # Logic: Compare row values across insurers, mark differences
    # Implementation: Check slot value variance
    return highlights if highlights else None
```

---

### 3. E2E Tests (High Priority)

**File:** `tests/test_next10_examples_e2e.py`

**Test Structure:**

```python
import pytest
import re
from apps.api.app.view_model.assembler import assemble_viewmodel_v2

# Forbidden phrase patterns (from INCA_DIO_REQUIREMENTS.md)
FORBIDDEN_PATTERNS = [
    r'추천|권장|선택하세요|고르세요|가입하세요',
    r'더 좋|더 나[은음]|유리|불리|뛰어남|우수|최선|최고',
    r'사실상|실질적으로|거의|유사|비슷|같은 담보|동일',
    r'종합적으로|결론적으로|판단|평가|분석 결과'
]

def test_example1_premium_sorting():
    """Example 1: 가장 저렴한 보험료 정렬순으로 4개만 비교해줘"""
    request = CompareRequest(
        query="가장 저렴한 보험료 정렬순으로 4개만 비교해줘",
        sort_by="총납입보험료_일반",
        sort_order="asc",
        limit=4,
        emphasis_premium=True
    )

    viewmodel = assemble_viewmodel_v2(compare_result, request)

    # Schema v2 validation
    assert viewmodel["schema_version"] == "next4.v2"

    # sort_metadata presence
    assert viewmodel["fact_table"]["sort_metadata"] is not None
    assert viewmodel["fact_table"]["sort_metadata"]["sort_by"] == "총납입보험료_일반"
    assert viewmodel["fact_table"]["sort_metadata"]["limit"] == 4

    # visual_emphasis presence
    assert viewmodel["fact_table"]["visual_emphasis"] is not None
    assert viewmodel["fact_table"]["visual_emphasis"]["min_value_style"] == "blue"
    assert viewmodel["fact_table"]["visual_emphasis"]["max_value_style"] == "red"

    # Forbidden phrase check
    viewmodel_str = json.dumps(viewmodel, ensure_ascii=False)
    for pattern in FORBIDDEN_PATTERNS:
        assert not re.search(pattern, viewmodel_str), f"Forbidden phrase found: {pattern}"

def test_example2_condition_difference():
    """Example 2: 암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"""
    request = CompareRequest(
        query="암직접입원비 담보 중 보장한도가 다른 상품 찾아줘",
        coverage="암직접입원비",
        slot_comparison={"slot_key": "payout_limit"}
    )

    viewmodel = assemble_viewmodel_v2(compare_result, request)

    # filter_criteria presence
    assert viewmodel["snapshot"]["filter_criteria"] is not None
    assert viewmodel["snapshot"]["filter_criteria"]["slot_key"] == "payout_limit"
    assert "difference_detected" in viewmodel["snapshot"]["filter_criteria"]

    # highlight field in rows
    rows_with_highlight = [r for r in viewmodel["fact_table"]["rows"] if r.get("highlight")]
    assert len(rows_with_highlight) > 0, "At least one row should have highlight"

    # Forbidden phrase check
    viewmodel_str = json.dumps(viewmodel, ensure_ascii=False)
    for pattern in FORBIDDEN_PATTERNS:
        assert not re.search(pattern, viewmodel_str), f"Forbidden phrase found: {pattern}"

def test_example3_specific_insurers():
    """Example 3: 삼성화재, 메리츠화재의 암진단비를 비교해줘"""
    request = CompareRequest(
        query="삼성화재, 메리츠화재의 암진단비를 비교해줘",
        insurers=["SAMSUNG", "MERITZ"],
        coverage="암진단비"
    )

    viewmodel = assemble_viewmodel_v2(compare_result, request)

    # filter_criteria.insurer_filter
    assert viewmodel["snapshot"]["filter_criteria"] is not None
    assert viewmodel["snapshot"]["filter_criteria"]["insurer_filter"] == ["SAMSUNG", "MERITZ"]

    # Only requested insurers in snapshot
    insurers = [i["insurer"] for i in viewmodel["snapshot"]["insurers"]]
    assert set(insurers) == {"SAMSUNG", "MERITZ"}

    # Forbidden phrase check
    viewmodel_str = json.dumps(viewmodel, ensure_ascii=False)
    for pattern in FORBIDDEN_PATTERNS:
        assert not re.search(pattern, viewmodel_str), f"Forbidden phrase found: {pattern}"

def test_example4_ox_matrix():
    """Example 4: 제자리암, 경계성종양 보장내용에 따라 A사, B사 상품 비교해줘"""
    request = CompareRequest(
        query="제자리암, 경계성종양 보장내용에 따라 A사, B사 상품 비교해줘",
        insurers=["A사", "B사"],
        disease_scope=["제자리암", "경계성종양"],
        coverages=["진단비", "수술비", "항암약물", "표적항암", "다빈치치료"]
    )

    viewmodel = assemble_viewmodel_v2(compare_result, request)

    # table_type = ox_matrix
    assert viewmodel["fact_table"]["table_type"] == "ox_matrix"

    # filter_criteria.disease_scope
    assert viewmodel["snapshot"]["filter_criteria"] is not None
    assert viewmodel["snapshot"]["filter_criteria"]["disease_scope"] == ["제자리암", "경계성종양"]

    # O/X values in table cells
    row_values = [row.get("benefit_amount") for row in viewmodel["fact_table"]["rows"]]
    ox_values = [v for v in row_values if v in ["O", "X", "-"]]
    assert len(ox_values) > 0, "O/X matrix should contain O/X values"

    # Forbidden phrase check
    viewmodel_str = json.dumps(viewmodel, ensure_ascii=False)
    for pattern in FORBIDDEN_PATTERNS:
        assert not re.search(pattern, viewmodel_str), f"Forbidden phrase found: {pattern}"

def test_schema_v2_validation():
    """Validate ViewModel v2 against JSON Schema"""
    from jsonschema import validate
    import json

    with open("docs/ui/compare_view_model.schema.json") as f:
        schema = json.load(f)

    viewmodel = assemble_viewmodel_v2(sample_compare_result, sample_request)

    # Should not raise ValidationError
    validate(instance=viewmodel, schema=schema)

def test_required_blocks_present():
    """All 4 required blocks must be present"""
    viewmodel = assemble_viewmodel_v2(sample_compare_result, sample_request)

    assert "header" in viewmodel
    assert "snapshot" in viewmodel
    assert "fact_table" in viewmodel
    assert "evidence_panels" in viewmodel

def test_warnings_fact_only():
    """Warnings must be fact-only, no judgment"""
    viewmodel = assemble_viewmodel_v2(sample_compare_result, sample_request)

    warnings = viewmodel.get("debug", {}).get("warnings", [])
    for warning in warnings:
        # Check no forbidden phrases in warnings
        for pattern in FORBIDDEN_PATTERNS:
            assert not re.search(pattern, warning), f"Judgment in warning: {warning}"
```

---

### 4. Frontend Renderer Enhancements (Medium Priority)

**Files:**
- `apps/web/src/components/compare/CompareViewModelRenderer.tsx`
- `apps/web/src/components/compare/FactTable.tsx`
- `apps/web/src/components/compare/OXMatrix.tsx` (new)

**Required Changes:**

1. **FactTable.tsx**: Add sorting/highlighting support
2. **OXMatrix.tsx**: New component for `table_type: "ox_matrix"`
3. **CompareViewModelRenderer.tsx**: Route to OXMatrix if needed

**Implementation Priority:** LOWER (Schema + Backend + Tests first)

---

## Implementation Order

1. ✅ Schema v2 locked (Commit: 1f85282)
2. ⏳ Backend assembler v2 enhancements
3. ⏳ E2E tests (examples 1-4)
4. ⏳ Frontend renderer (if time permits)
5. ⏳ STATUS.md update + final commit

---

## DoD Checklist

- [x] Schema v2 confirmed
- [ ] Assembler v2 implemented
- [ ] Examples 1-4 E2E tests pass
- [ ] Forbidden phrase regex tests pass
- [ ] STATUS.md updated
- [ ] Git commit/push complete

---

**Next Action:** Implement backend assembler v2 with v2 field population
