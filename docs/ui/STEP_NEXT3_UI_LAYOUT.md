# STEP NEXT-3: UI Layout Specification
## ChatGPT-style Insurance Comparison UI (MVP)

> **Constitutional Document**: This specification is governed by CLAUDE.md Article 0 (Document Priority) and Article I (Coverage Universe Lock).
> **All content must be fact-only, no inference, no recommendation.**

---

## 0. Constitutional Principles

### Absolute Rules
1. **Fact-only**: All numbers, conditions, and statements must have document evidence
2. **No Inference / No Recommendation**: Absolutely no judgment expressions ("better", "recommended", etc.)
3. **Presentation Layer Only**: UI is a View Model, contains no business logic
4. **Canonical Coverage Rule**: All comparisons based on Shinjungwon unified coverage codes

### Prohibited Elements
- ❌ Summary opinion section
- ❌ Recommendation phrases
- ❌ Icon-based superiority indication
- ❌ Color emphasis implying advantage
- ❌ Any rewriting of original document text
- ❌ Interpretative sentences

---

## 1. UI Structure (Fixed)

The UI consists of exactly **3 Blocks**:

```
┌─────────────────────────────────────────────────────────┐
│ [BLOCK 0] User Query (Chat Header)                     │
├─────────────────────────────────────────────────────────┤
│ [BLOCK 1] Coverage Snapshot                            │
├─────────────────────────────────────────────────────────┤
│ [BLOCK 2] Fact Table (Coverage Comparison)             │
├─────────────────────────────────────────────────────────┤
│ [BLOCK 3] Evidence Panels (Accordion)                  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. BLOCK 0: User Query (Chat Header)

### Purpose
Display user's original question exactly as asked.

### Content
- User question in 1 line
- No exposure of internal processing (coverage_code, slots, etc.)

### Example
```
Q. 암 진단비 기준으로 삼성화재와 메리츠화재를 비교해줘
```

### Prohibited
- Rephrasing user question
- Adding clarifications
- Showing system interpretation

---

## 3. BLOCK 1: Coverage Snapshot

### Purpose
Fact-only summary of comparison scope.

### Required Elements
- Normalized coverage name (canonical)
- List of insurers being compared
- Amount display (if available)

### Allowed Example
```
비교 기준 담보: 암 진단비 (유사암 제외)
  • 삼성화재: 3,000만원
  • 메리츠화재: 3,000만원
```

### Prohibited Examples
- ❌ "동일함"
- ❌ "차이가 없음"
- ❌ "A사가 유리"
- ❌ Any comparative judgment

### Special Cases

#### Case 1: Amount Not Available
```
비교 기준 담보: 암 진단비 (유사암 제외)
  • 삼성화재: (가입설계서 확인 필요)
  • 메리츠화재: 3,000만원
```

#### Case 2: Multiple Coverage Variants
```
비교 기준 담보: 암 진단비
  • 삼성화재: 일반암 3,000만원 / 유사암 제외
  • 메리츠화재: 일반암 3,000만원 / 유사암 300만원
```

---

## 4. BLOCK 2: Fact Table (Core)

### Table Schema (Fixed)

| 보험사 | 담보명(정규화) | 보장금액 | 지급 조건 요약 | 보험기간 | 비고 |
|--------|----------------|----------|----------------|----------|------|

### Column Definitions

#### 4.1 보험사 (Insurer)
- Exact name from proposal document
- No abbreviation

#### 4.2 담보명(정규화) (Normalized Coverage Name)
- Canonical coverage name from `coverage_standard`
- NOT insurer-specific alias
- If UNMAPPED: show proposal coverage name + "(매핑 미완료)" tag

#### 4.3 보장금액 (Coverage Amount)
- Format: `{amount_value} {currency}`
- Example: `3,000만원`, `5,000만원`
- If NULL: leave blank (do not write "확인 필요")

#### 4.4 지급 조건 요약 (Payout Condition Summary)
- **Slot-based summary only**
- Allowed slots:
  - `waiting_period`
  - `payment_frequency`
  - `diagnosis_definition`
  - `payout_limit`
  - `exclusion_scope`
- **No sentence rewriting**
- **No interpretation**

##### Format Rules
```
대기기간: {waiting_period}
지급 횟수: {payment_frequency}
진단 정의: {diagnosis_definition}
지급 한도: {payout_limit}
제외 범위: {exclusion_scope}
```

##### Example (Correct)
```
대기기간: 90일
지급 횟수: 최초 1회
제외 범위: 유사암, 갑상선암, 경계성종양, 제자리암
```

##### Example (Prohibited)
```
❌ "최초 1회만 지급되며 90일 대기기간이 있습니다"
❌ "일반암에 한해 지급"
```

#### 4.5 보험기간 (Insurance Period)
- Exact value from proposal
- Example: `80세 만기`, `100세 만기`

#### 4.6 비고 (Remarks)
- Evidence-based notes only
- Allowed:
  - Mapping status tag: `(UNMAPPED)`, `(AMBIGUOUS)`
  - Slot confidence: `(약관 확인 필요)` if `source_confidence = unknown`
- Prohibited:
  - Comparative notes
  - Interpretations

---

## 5. BLOCK 3: Evidence Panels (Accordion)

### UI Pattern
Collapsible accordion structure per insurer.

```
▶ 삼성화재 근거 보기
▶ 메리츠화재 근거 보기
```

### Expanded Content

#### Required Elements (per insurer)
1. **Document Type** (문서 유형)
   - 가입설계서 / 약관 / 상품요약서 / 사업방법서
2. **Page Number** (페이지)
   - Example: `p.3`, `p.12`
3. **Text Span** (원문 발췌)
   - Direct quote from document
   - Max 200 characters
   - Use `...` for truncation

#### Example (Expanded)
```
▼ 삼성화재 근거 보기
  문서: 가입설계서
  페이지: p.3
  원문: "암 진단비: 3,000만원 (유사암, 갑상선암, 경계성종양, 제자리암 제외)"

  문서: 약관
  페이지: p.45
  원문: "이 특약에서 '암'이라 함은 한국표준질병·사인분류(KCD-7) 중 C00-C97로 분류되는 악성신생물..."
```

### Absolute Prohibitions
- ❌ Rewriting original text
- ❌ Semantic summarization
- ❌ Adding interpretation sentences
- ❌ Combining multiple spans into one narrative

---

## 6. Special Comparison Cases

### 6-1. 경계성종양 / 제자리암 / 유사암 (Borderline/In-situ/Similar Cancer)

#### Problem
These are NOT amount-comparable; they require definition-based comparison.

#### UI Structure (Modified)

| 보험사 | 질병 유형 | 보장 여부 | 지급 비율 | 정의 근거 |
|--------|-----------|-----------|-----------|-----------|

#### Column Definitions
- **질병 유형**: 경계성종양 / 제자리암 / 유사암 5종
- **보장 여부**: 보장 / 제외 / 불명확
- **지급 비율**: `{amount}` or `주계약의 {%}%`
- **정의 근거**: KCD-7 code range (e.g., `C73, C00-C97`)

#### Example
```
| 보험사      | 질병 유형    | 보장 여부 | 지급 비율     | 정의 근거          |
|-------------|--------------|-----------|---------------|--------------------|
| 삼성화재    | 경계성종양   | 제외      | -             | D37-D48 (약관 명시)|
| 메리츠화재  | 경계성종양   | 보장      | 300만원       | D37-D48 (약관 명시)|
```

---

### 6-2. 다빈치/로봇 수술비 (Da Vinci/Robotic Surgery)

#### Problem
"다빈치 수술비" is NOT a canonical coverage; it's a **method condition** of surgical coverage.

#### UI Structure (Modified)

| 보험사 | 수술 방식 | 보장 담보 | 금액 | 제한 조건 |
|--------|-----------|-----------|------|-----------|

#### Column Definitions
- **수술 방식**: 로봇수술 / 다빈치수술 / 복강경수술
- **보장 담보**: Canonical coverage name (e.g., `암 수술비`, `뇌수술비`)
- **금액**: Amount from proposal
- **제한 조건**: `method_condition`, reduction rate, renewal

#### Example
```
| 보험사      | 수술 방식  | 보장 담보  | 금액      | 제한 조건                     |
|-------------|-----------|------------|-----------|-------------------------------|
| 삼성화재    | 로봇수술  | 암 수술비  | 500만원   | 수술 방법 불문 (약관 명시)     |
| 메리츠화재  | 다빈치수술| 암 수술비  | 500만원   | 로봇수술 포함 (갱신형 3년)     |
```

---

## 7. Data Flow (UI ← Backend)

### Input: View Model (from Backend)
```json
{
  "query": "암 진단비 기준으로 삼성화재와 메리츠화재를 비교해줘",
  "snapshot": {
    "canonical_coverage_name": "암 진단비 (유사암 제외)",
    "insurers": [
      {"insurer": "삼성화재", "amount": "3,000만원"},
      {"insurer": "메리츠화재", "amount": "3,000만원"}
    ]
  },
  "fact_table": [
    {
      "insurer": "삼성화재",
      "coverage_name_normalized": "암 진단비",
      "amount": "3,000만원",
      "conditions_summary": {
        "waiting_period": "90일",
        "payment_frequency": "최초 1회",
        "exclusion_scope": "유사암, 갑상선암, 경계성종양, 제자리암"
      },
      "insurance_period": "80세 만기",
      "remarks": null
    },
    {
      "insurer": "메리츠화재",
      "coverage_name_normalized": "암 진단비",
      "amount": "3,000만원",
      "conditions_summary": {
        "waiting_period": "90일",
        "payment_frequency": "최초 1회",
        "exclusion_scope": "유사암, 갑상선암"
      },
      "insurance_period": "100세 만기",
      "remarks": null
    }
  ],
  "evidence": [
    {
      "insurer": "삼성화재",
      "items": [
        {
          "doc_type": "가입설계서",
          "page": "p.3",
          "span_text": "암 진단비: 3,000만원 (유사암, 갑상선암, 경계성종양, 제자리암 제외)"
        },
        {
          "doc_type": "약관",
          "page": "p.45",
          "span_text": "이 특약에서 '암'이라 함은 한국표준질병·사인분류(KCD-7) 중 C00-C97로 분류되는 악성신생물..."
        }
      ]
    },
    {
      "insurer": "메리츠화재",
      "items": [
        {
          "doc_type": "가입설계서",
          "page": "p.2",
          "span_text": "암 진단비: 3,000만원 (유사암, 갑상선암 제외)"
        }
      ]
    }
  ]
}
```

### Output: UI Rendering
- BLOCK 0: `query` field
- BLOCK 1: `snapshot` field
- BLOCK 2: `fact_table` array
- BLOCK 3: `evidence` array (accordion)

---

## 8. Edge Cases

### 8-1. UNMAPPED Coverage
```
| 보험사 | 담보명(정규화) | 보장금액 | 지급 조건 요약 | 보험기간 | 비고 |
|--------|----------------|----------|----------------|----------|------|
| 삼성화재 | 신종수술비 | 200만원 | - | 80세 만기 | (UNMAPPED) |
```

### 8-2. AMBIGUOUS Mapping
```
비고: (AMBIGUOUS - 수동 매핑 필요)
```

### 8-3. Out of Universe
```
UI에 표시하지 않음.
Backend에서 `out_of_universe` 응답 시 별도 메시지 표시:
"해당 담보는 가입설계서에 포함되지 않아 비교할 수 없습니다."
```

### 8-4. Missing Evidence
```
Evidence Panel:
  문서: (근거 없음)
  페이지: -
  원문: -
```

---

## 9. Frontend/Backend Separation

### Backend Responsibility
- Coverage comparison logic
- Slot extraction
- Evidence retrieval
- View Model assembly

### Frontend Responsibility
- Rendering 3 blocks
- Accordion interaction
- Table layout
- **No data processing**
- **No interpretation**

---

## 10. Validation Checklist

Before deployment, verify:

- [ ] No judgment/recommendation phrases
- [ ] All amounts have evidence
- [ ] No rewriting of original text
- [ ] Canonical coverage names used
- [ ] Prohibited elements (opinion, icon, color) absent
- [ ] 3-Block structure strictly followed
- [ ] Evidence panels include doc_type, page, span_text
- [ ] Special cases (borderline tumor, robotic surgery) handled correctly

---

## 11. Next Steps

1. **JSON Schema Definition** (STEP NEXT-4)
   - Formalize View Model structure
   - Define validation rules

2. **Backend API Implementation**
   - `/api/compare` endpoint
   - View Model assembly logic

3. **Frontend Component Development**
   - React/Vue components for 3 blocks
   - Accordion UI

---

## Appendix A: Prohibited Phrases

The following expressions are **absolutely prohibited** in the UI:

- "더 좋다", "유리하다", "불리하다"
- "추천", "권장"
- "우수", "뛰어남"
- "동일함", "차이 없음" (사실 나열만 허용)
- "A사가 B사보다..."
- "종합적으로 볼 때..."
- "고객님께 적합한..."

---

## Appendix B: Constitutional Compliance Matrix

| Principle | UI Implementation |
|-----------|-------------------|
| Fact-only | All data from evidence, no inference |
| No Recommendation | No "better/worse" language |
| Presentation Layer Only | No business logic in UI |
| Canonical Coverage Rule | Normalized coverage names in BLOCK 2 |
| Coverage Universe Lock | Out-of-universe → separate message |
| Evidence Rule | BLOCK 3 includes doc_type, page, span |
| Slot Schema v1.1.1 | Conditions summary uses exact slot names |

---

**Document Version**: 1.0.0
**Date**: 2025-12-26
**Status**: Constitutional (Immutable without Amendment)
