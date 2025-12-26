# Structure Contract: Samsung Proposal 2511

**Template ID:** `SAMSUNG_CANCER_2024_proposal_2511_a840f677`
**Product:** SAMSUNG_CANCER_2024 (무배당 삼성화재 건강보험 마이헬스 파트너)
**Version:** 2511
**Fingerprint:** a840f677596d939927c730475379125da3eb8d3a9e6eb0c3b753494387ce0f3d
**Extraction Method:** structure_first_v1

---

## Purpose

This document defines the **Structure Contract** for Samsung Proposal 2511 template.

Structure Contract = Deterministic rules for PDF table extraction + Universe classification.

**Constitutional Principle:**
PDF는 레이아웃 문서로 취급한다. 추출은 반드시 구조(테이블) → 행(row) → 컬럼(column) 순서다.

---

## PDF Document Structure

### Pages
- **Total pages:** 13
- **Coverage table pages:** 1-3 (front pages)
- **Detailed conditions:** Pages 4+ (OUT OF SCOPE for Stage-1)

### Table Detection

**Tool:** pdfplumber.extract_tables()

**Header Row Identification:**
- Look for keywords: "담보가입현황", "가입금액", "보험료"
- Header row index: varies by page (typically row 1-2)

---

## Table Column Mapping

**Samsung Proposal 2511 Table Structure:**

| Column Index | Column Name | Content | Extraction Rule |
|--------------|-------------|---------|-----------------|
| 0 | Category | 진단/입원/수술 | Optional (may be empty) |
| 1 | Coverage Name | 담보가입현황 | **PRIMARY KEY** for row |
| 2 | Coverage Amount | 가입금액 (e.g., "3,000만원") | Parse to amount_value |
| 3 | Premium | 보험료(원) | Not used in Stage-1 |
| 4 | Period/Code | 납입기간/보험기간 | Not used in Stage-1 |

**Extraction Priority:**
1. Column 1 (Coverage Name) → insurer_coverage_name
2. Column 2 (Amount) → amount_text → amount_value

---

## Amount Parsing Rules

**Pattern Matching (Regex):**

| Pattern | Example | Parsed Value | Unit |
|---------|---------|--------------|------|
| `(\d+(?:,\d+)?)만원` | "3,000만원" | 30,000,000 | 만원 |
| `(\d+(?:,\d+)?)만원` | "600만원" | 6,000,000 | 만원 |
| `(\d+(?:,\d+)?)만원` | "10만원" | 100,000 | 만원 |
| `(\d+(?:,\d+)?)원` | "10,000,000원" | 10,000,000 | 원 |

**Failure Handling:**
- If parsing fails → amount_value = NULL
- Store amount_text as-is for audit

---

## Non-Coverage Row Patterns

**NON_UNIVERSE_META Classification Rules:**

### Customer Info Keywords
- "피보험자"
- "통합고객"
- "보험나이변경일"

### Header Keywords
- "담보가입현황"
- "가입금액"

### Summary Keywords
- "합계"
- "총보험료"
- "갱신보험료 합계"
- "비갱신보험료 합계"

**Classification Logic:**
```python
if keyword in coverage_name:
    lock_class = 'NON_UNIVERSE_META'
```

---

## Universe Classification Rules

**3-Class System:**

### 1. UNIVERSE_COVERAGE (SSOT eligible)
- Has `amount_value` (NOT NULL)
- Has `coverage_name` (non-empty)
- NOT matching NON_UNIVERSE_META patterns

**Count:** 29 rows

**Sample:**
- 암 진단비(유사암 제외)
- 유사암 진단비(기타피부암)(1년50%)
- 보험료 납입면제대상Ⅱ

### 2. NON_UNIVERSE_META (exclude from Universe)
- Matches customer info / header / summary keywords

**Count:** 3 rows

**Sample:**
- 통합고객 (보험나이변경일 : 매년 04월 02일)
- 갱신보험료 합계
- 비갱신보험료 합계

### 3. UNCLASSIFIED (ambiguous)
- Edge cases requiring manual review

**Count:** 0 rows (none in Samsung 2511)

---

## Extraction Quality Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total rows extracted | 32 | ✅ |
| UNIVERSE_COVERAGE | 29 | ✅ 90.6% |
| NON_UNIVERSE_META | 3 | ✅ 9.4% |
| UNCLASSIFIED | 0 | ✅ 0% |
| Amount parsing success | 29/29 | ✅ 100% |

---

## Re-run Stability

**Idempotency Guarantee:**

1. **Same PDF → Same coverage rows**
   - content_hash prevents duplicates
   - ON CONFLICT DO NOTHING

2. **Same rows → Same classification**
   - Deterministic rules (no randomness)
   - ON CONFLICT DO UPDATE (lock results)

3. **Template change detection**
   - fingerprint changes → new template_id
   - Old template_id data preserved

**Verification:**
```bash
python apps/api/scripts/ingest_v2_proposal_stage1.py \
  data/samsung/가입설계서/삼성_가입설계서_2511.pdf \
  --product-id SAMSUNG_CANCER_2024 \
  --version 2511

# Result: 0 new inserts (all duplicates)

python apps/api/scripts/universe_lock_v2_stage1.py \
  --product-id SAMSUNG_CANCER_2024

# Result: Same 29 UNIVERSE_COVERAGE, 3 NON_UNIVERSE_META
```

---

## Template Evolution

**If Samsung changes proposal format:**

1. PDF structure changes → new fingerprint → new template_id
2. New template_id triggers new Structure Contract document
3. Old template data preserved (no deletion)

**Version History:**
- v2511 (current): structure_first_v1 extraction
- Future versions: TBD

---

## Out of Scope (Stage-1)

The following are **NOT** handled in this Structure Contract:

- ❌ Excel mapping (담보명mapping자료.xlsx)
- ❌ coverage_standard reference
- ❌ proposal_coverage_mapped
- ❌ Normalization / canonical code assignment
- ❌ Policy / summary / business method documents
- ❌ Detailed conditions (pages 4+)
- ❌ Premium / period / code parsing

**Rationale:** Stage-1 focuses on Universe Lock only (raw coverage table extraction + classification).

---

## Validation Checklist

- [x] Table structure extracted (pdfplumber)
- [x] Column mapping verified (coverage name + amount)
- [x] Amount parsing tested (만원/원)
- [x] NON_UNIVERSE_META patterns identified
- [x] Universe Lock results stored separately
- [x] Raw data preserved (no modification)
- [x] Re-run idempotency verified
- [x] Legacy public schema unaffected

---

## References

- **Extraction Script:** `apps/api/scripts/ingest_v2_proposal_stage1.py`
- **Classification Script:** `apps/api/scripts/universe_lock_v2_stage1.py`
- **Lock Table:** `v2.proposal_coverage_universe_lock`
- **Raw Data:** `v2.proposal_coverage`

---

**Document Version:** 1.0
**Last Updated:** 2025-12-26
**Status:** ✅ Active
