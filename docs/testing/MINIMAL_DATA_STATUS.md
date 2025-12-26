# Minimal Data Status - STEP NEXT-12D-1

**Date:** 2025-12-26
**Status:** ✅ READY (Existing data sufficient)

---

## Summary

**Goal:** Ensure at least one query returns HTTP 200 with ViewModel v2.

**Result:** ✅ SUCCESS - Existing database already contains minimal dataset for comparison.

---

## Current Dataset

### Coverage Universe (proposal_coverage_universe)

| ID | Insurer | Proposal ID | Coverage Name Raw | Amount Value | Mapping Status | Canonical Code |
|----|---------|-------------|-------------------|--------------|----------------|----------------|
| 1  | SAMSUNG | PROP_SAMSUNG_001 | 일반암진단금 | 50,000,000 | MAPPED | CA_DIAG_GENERAL |
| 2  | SAMSUNG | PROP_SAMSUNG_001 | 유사암진단금 | 5,000,000 | MAPPED | CA_DIAG_SIMILAR |
| 3  | MERITZ  | PROP_MERITZ_001  | 암진단금(일반암) | 30,000,000 | MAPPED | CA_DIAG_GENERAL |

### Coverage Standard (canonical codes)

| Coverage Code | Coverage Name | Category | Type |
|---------------|---------------|----------|------|
| CA_DIAG_GENERAL | 일반암진단비 | 암보험 | diagnosis |
| CA_DIAG_SIMILAR | 유사암진단비 | 암보험 | diagnosis |

---

## Success Query (Verified)

**Query:**
```json
{
  "query": "일반암진단비",
  "insurers": ["SAMSUNG", "MERITZ"]
}
```

**Expected Response:**
- HTTP: 200
- schema_version: "next4.v2"
- fact_table.rows: >= 2
- evidence_panels: >= 1

**Test Script:**
```bash
apps/api/scripts/test_success_query.sh
```

**Last Run:** 2025-12-26 ✅ PASSED

---

## Data Requirements (Reference)

For `/compare/view-model` to return 200, the following minimum data is required:

### 1. Coverage Universe
- At least 2 rows with **same canonical_coverage_code**
- Different insurers (for comparison)
- Fields:
  - insurer (e.g., SAMSUNG, MERITZ)
  - proposal_id
  - coverage_name_raw
  - amount_value (optional, but recommended)

### 2. Mapping
- `mapping_status = 'MAPPED'`
- `canonical_coverage_code` must reference existing `coverage_standard.coverage_code`

### 3. Evidence (optional, but recommended)
- At least 1 document + chunks for evidence panel rendering
- Fields:
  - source_doc_id
  - source_page
  - source_span_text

---

## Alternative Queries (May Return 424)

Queries that don't match existing data will return:
- HTTP: 424 (Failed Dependency)
- error_code: "DATA_INSUFFICIENT"
- This is **expected behavior**, not a failure.

Examples:
- "암진단비" (too generic, may not match exact coverage names)
- "유사암진단비" with MERITZ (MERITZ doesn't have this coverage)

---

## Seed Script (NOT REQUIRED)

**Note:** Existing data is sufficient. No additional seed script needed.

If data is lost, recreate with:
```sql
-- See existing data in proposal_coverage_universe + proposal_coverage_mapped
-- No automated seed script provided (existing data is reference)
```

---

## CI/CD Integration

**Pre-E2E Check:**
```bash
# 1. DB connection
python apps/api/scripts/db_doctor.py

# 2. Success query test
apps/api/scripts/test_success_query.sh
```

Both must pass before running Playwright E2E tests.

---

## Constitutional Compliance

- ✅ No LLM inference for data generation
- ✅ Evidence-based (source_span_text from proposal docs)
- ✅ Deterministic (same query → same result)
- ✅ No recommendations/judgments in data

---

**Document Status:** Active (Minimal data verified 2025-12-26)
