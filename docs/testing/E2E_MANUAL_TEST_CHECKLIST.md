# E2E Manual Test Checklist - Example 1-4

**Purpose:** Validate Real API → ViewModel → UI rendering flow

**Page:** http://localhost:3000/compare-live

**Schema:** next4.v2

**Date:** 2025-12-26

---

## Pre-requisites

1. Backend API running: `http://localhost:8001`
2. Frontend dev server running: `http://localhost:3000`
3. Test data loaded (minimal coverage universe + mapping)

---

## Example 1: Premium Sorting (보험료 정렬)

### Input
```
Query: "가장 저렴한 보험료 정렬순으로 4개만 비교해줘"
```

### Expected ViewModel Features
- [ ] `snapshot.filter_criteria.slot_key` present (보험료 관련)
- [ ] `fact_table.sort_metadata.sort_by` present (정렬 기준)
- [ ] `fact_table.sort_metadata.sort_order` = "asc"
- [ ] `fact_table.sort_metadata.limit` = 4
- [ ] `fact_table.visual_emphasis` present (optional)

### UI Validation
- [ ] Query appears in chat (user message)
- [ ] ViewModel renders without errors
- [ ] Filter criteria displayed (if present)
- [ ] Sort metadata label shows: "정렬: ... (오름차순) / 상위 4개"
- [ ] Fact table shows sorted rows
- [ ] NO recommendation text ("추천", "권장", etc.)
- [ ] NO judgment text ("더 좋다", "유리하다", etc.)

### Evidence Panel
- [ ] Evidence panels grouped by insurer
- [ ] Click insurer → accordion expands
- [ ] Evidence excerpts displayed as-is (no rewriting)

---

## Example 2: Condition Difference (보장한도 차이)

### Input
```
Query: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
```

### Expected ViewModel Features
- [ ] `snapshot.filter_criteria.slot_key` = "payout_limit"
- [ ] `snapshot.filter_criteria.difference_detected` = true
- [ ] `fact_table.rows[].highlight` contains "payout_limit" (for differing rows)

### UI Validation
- [ ] Query appears in chat
- [ ] ViewModel renders without errors
- [ ] Filter criteria shows: "비교 항목: payout_limit" + "차이 감지: 있음"
- [ ] Highlighted cells (yellow background) for differing values
- [ ] NO interpretation text ("불리하다", "사실상 같다", etc.)

### Evidence Panel
- [ ] Evidence showing payout_limit from different insurers
- [ ] Click → expand → see excerpt

---

## Example 3: Specific Insurers (특정 보험사 비교)

### Input
```
Query: "삼성화재, 메리츠화재의 암진단비를 비교해줘"
```

### Expected ViewModel Features
- [ ] `snapshot.filter_criteria.insurer_filter` = ["SAMSUNG", "MERITZ"]
- [ ] `snapshot.insurers` contains only SAMSUNG, MERITZ

### UI Validation
- [ ] Query appears in chat
- [ ] ViewModel renders without errors
- [ ] Filter criteria shows: "보험사: SAMSUNG, MERITZ"
- [ ] Fact table shows only requested insurers
- [ ] Evidence panels show only SAMSUNG, MERITZ
- [ ] NO recommendation/judgment text

---

## Example 4: Disease-based O/X Matrix (질병별 보장 가능 여부)

### Input
```
Query: "제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 상품 비교해줘"
```

### Expected ViewModel Features
- [ ] `snapshot.filter_criteria.disease_scope` = ["제자리암", "경계성종양"]
- [ ] `snapshot.filter_criteria.insurer_filter` = ["SAMSUNG", "MERITZ"]
- [ ] `fact_table.table_type` = "ox_matrix"

### UI Validation
- [ ] Query appears in chat
- [ ] ViewModel renders without errors
- [ ] Filter criteria shows disease scope + insurers
- [ ] **O/X Matrix Table** rendered (not default table)
- [ ] Table header: "보장 가능 여부 (O: 보장, X: 미보장, —: 정보 없음)"
- [ ] O/X/— values displayed
- [ ] NO judgment text ("O가 더 좋다", "종합적으로...", etc.)

### Evidence Panel
- [ ] Evidence from policy documents (약관)
- [ ] Shows disease scope definitions
- [ ] Click → expand → see excerpt

---

## Constitutional Compliance Checks

For **ALL** examples, verify:

### Forbidden Phrases (Must NOT appear in UI)
- [ ] NO "추천" (recommendation)
- [ ] NO "권장" (advice)
- [ ] NO "선택하세요" (selection prompt)
- [ ] NO "더 좋다" / "더 나은" (superiority)
- [ ] NO "유리하다" / "불리하다" (advantage/disadvantage)
- [ ] NO "사실상" / "유사" (interpretation - except "유사암" domain term)
- [ ] NO "종합적으로" / "판단" / "평가" (judgment/inference)

### Allowed Phrases (Fact-only)
- [ ] "다릅니다" / "같습니다" (difference/sameness)
- [ ] "보장" / "미보장" / "O" / "X" (coverage facts)
- [ ] "정렬" / "최저" / "최고" (sorting/extremes - NO judgment)
- [ ] "약관 확인 필요" (evidence requirement)

### Evidence Integrity
- [ ] All displayed values traceable to evidence panels
- [ ] Evidence excerpts are direct quotes (NO rewriting)
- [ ] Evidence ref_id linkage (if implemented)

### UI Layout
- [ ] ChatGPT style: left (chat) + right (info/evidence)
- [ ] User messages: right-aligned, blue background
- [ ] Assistant messages: left-aligned, white background with ViewModel
- [ ] Evidence panels: grouped by insurer, collapsible

---

## Error Handling

### API Errors
- [ ] Network error → error message displayed (NO crash)
- [ ] 4xx/5xx response → error message displayed
- [ ] Error message is fact-only (NO judgment)

### Missing Data
- [ ] UNMAPPED coverage → row_status shows "UNMAPPED"
- [ ] Missing evidence → "근거 문서 정보 없음"
- [ ] OUT_OF_UNIVERSE → status shows "가입설계서 미포함"

---

## Performance

- [ ] Query submission → response within reasonable time (<5s)
- [ ] ViewModel rendering smooth (no lag)
- [ ] Evidence panel expand/collapse smooth

---

## Cross-browser Testing (Optional)

- [ ] Chrome
- [ ] Firefox
- [ ] Safari

---

## Notes

**Test Data Requirement:**
- Examples 1-4 require specific coverage data in proposal universe
- If API returns UNMAPPED/OUT_OF_UNIVERSE, verify test data exists

**Deterministic Compiler:**
- Same query → same ViewModel (reproducible)
- NO LLM randomness in response

**Next Steps:**
- Convert to Playwright automated tests (optional)
- Add visual regression testing (optional)
- Add accessibility testing (optional)

---

**Checklist Status:**
- [ ] Example 1 passed
- [ ] Example 2 passed
- [ ] Example 3 passed
- [ ] Example 4 passed
- [ ] Constitutional compliance verified
- [ ] All forbidden phrases absent

**Tester:** _______________
**Date:** _______________
**Result:** PASS / FAIL
**Notes:** _______________
