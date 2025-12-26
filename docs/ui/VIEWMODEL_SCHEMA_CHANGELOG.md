# ViewModel Schema Changelog

**Schema File:** `compare_view_model.schema.json`

---

## v2 (2025-12-26) - INCA DIO Requirements Integration

**Status:** LOCKED

**Purpose:** Add optional fields to support inca_dio.pdf examples 1-4 (sorting, filtering, O/X matrix, highlighting)

**Breaking Changes:** NONE (all amendments optional)

**New Fields:**

### 1. snapshot.filter_criteria (Optional)
**Type:** object | null
**Description:** Fact-only filter criteria applied to comparison
**Properties:**
- `insurer_filter`: string[] - Explicitly requested insurers
- `disease_scope`: string[] - Diseases/conditions in scope
- `slot_key`: string - Specific slot being compared
- `difference_detected`: boolean - Whether differences detected

**Use Case:** Example 2 (암직접입원비 보장한도 차이), Example 3 (특정 보험사 필터), Example 4 (질병별 보장)

### 2. fact_table.table_type (Optional)
**Type:** enum ("default" | "ox_matrix")
**Default:** "default"
**Description:** Table display mode (standard vs O/X coverage availability)

**Use Case:** Example 4 (제자리암/경계성종양 O/X 매트릭스)

### 3. fact_table.sort_metadata (Optional)
**Type:** object | null
**Description:** Sorting configuration (UI hint, NOT business logic)
**Properties:**
- `sort_by`: string - Column name
- `sort_order`: enum ("asc" | "desc")
- `limit`: number - Max rows to display

**Use Case:** Example 1 (보험료 정렬순 4개)

### 4. fact_table.visual_emphasis (Optional)
**Type:** object | null
**Description:** Visual styling for min/max values (NO judgment, UI hint only)
**Properties:**
- `min_value_style`: enum ("blue" | "green" | "default")
- `max_value_style`: enum ("red" | "orange" | "default")

**Use Case:** Example 1 (최저/최고 보험료 색상 강조)

### 5. fact_table.rows[].highlight (Optional)
**Type:** string[] | null
**Description:** Cell keys to emphasize (difference detection, NO judgment)

**Use Case:** Example 2 (보장한도 차이 하이라이트)

---

## v1 (2025-12-24) - Initial Schema

**Status:** DEPRECATED (use v2)

**Purpose:** Base ViewModel schema for ChatGPT-style UI (3-Block structure)

**Fields:**
- `schema_version`: string (pattern: next4.v1)
- `generated_at`: ISO 8601 timestamp
- `header`: User query (BLOCK 0)
- `snapshot`: Coverage snapshot (BLOCK 1)
- `fact_table`: Comparison table (BLOCK 2)
- `evidence_panels`: Evidence accordion (BLOCK 3)
- `debug`: Non-UI debugging info

---

## Constitutional Compliance (All Versions)

### Absolute Rules
- ✅ Fact-only (all values evidence-backed)
- ✅ No recommendation/inference fields
- ✅ Presentation layer only (no business logic)
- ✅ Canonical coverage rule (신정원 통일 코드)

### Prohibited in Schema
- ❌ Judgment fields ("better", "recommended", "superior")
- ❌ Comparative phrases ("same as", "no difference")
- ❌ Opinion sections ("summary opinion", "conclusion")
- ❌ Ranking/scoring fields

### v2 Amendments Compliance
- ✅ `filter_criteria`: Fact-only filters (NO judgment)
- ✅ `table_type`: Display mode (NOT evaluation type)
- ✅ `sort_metadata`: UI hint (NOT business ranking)
- ✅ `visual_emphasis`: Color hint (NOT judgment label)
- ✅ `highlight`: Difference emphasis (NOT superiority marker)

---

## Migration Guide (v1 → v2)

### Backward Compatibility
- ✅ v1 consumers can read v2 ViewModel (ignore unknown optional fields)
- ✅ v2 backend can emit v1-compatible ViewModel (omit v2 fields)

### Implementation Checklist
- [ ] Backend: Update assembler to populate v2 fields
- [ ] Frontend: Add renderers for v2 fields (sorting, O/X, highlighting)
- [ ] Tests: Verify schema v2 validation
- [ ] Tests: Verify forbidden phrase detection still works

---

## Example-Specific Field Usage

### Example 1: Premium Sorting
**Required v2 Fields:**
- `fact_table.sort_metadata` (sort_by, sort_order, limit)
- `fact_table.visual_emphasis` (min_value_style: blue, max_value_style: red)

### Example 2: Condition Difference
**Required v2 Fields:**
- `snapshot.filter_criteria` (slot_key, difference_detected)
- `fact_table.rows[].highlight` (difference cells)

### Example 3: Specific Insurers
**Required v2 Fields:**
- `snapshot.filter_criteria` (insurer_filter)

### Example 4: O/X Coverage Matrix
**Required v2 Fields:**
- `fact_table.table_type` ("ox_matrix")
- `snapshot.filter_criteria` (disease_scope, insurer_filter)

---

**Schema Status:** v2 LOCKED (2025-12-26)
**Next Version:** v3 (TBD - requires new customer requirements)
