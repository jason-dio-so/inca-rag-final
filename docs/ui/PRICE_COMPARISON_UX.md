# Premium Comparison UX Design (STEP 29)

> **Constitutional Principle**: This system is **proposal-centered**, not policy-centered.
> Premium comparison is an **additional feature** on top of the existing proposal comparison system.

---

## 1. Core Principle

### What This Is
**"Find and compare the cheapest proposals with identical coverage conditions"**

- Comparison target = Proposals (가입설계서)
- Premium = Result value already in proposals
- Policy/coverage comparison = Evidence to explain why one proposal is cheaper

### What This Is NOT
- ❌ Premium calculator
- ❌ Product-level premium comparison
- ❌ Policy-only comparison system

---

## 2. User Flow

### 2.1. Entry Point (from STEP 28)

**Current State**: User compares two specific proposals (Scenario A: SAMSUNG vs MERITZ)

**New State**: User wants to see "which insurer offers the cheapest premium for the same coverage"

```
User Input:
- Coverage: "일반암진단비"
- Conditions: 가입금액 3천만원, 100세만기, 10년납
- Age: 30세
- Gender: 남성
```

### 2.2. Top-N Ranking View

**Display**: Card list of cheapest proposals (sorted by premium)

```
┌─────────────────────────────────────────────────┐
│ 보험료 최저가 비교 결과                           │
│ 담보: 일반암진단비 (3천만원, 100세만기, 10년납)    │
├─────────────────────────────────────────────────┤
│ 1위 │ KB손해보험    │ 월 15,000원 │ 비교하기    │
│ 2위 │ 메리츠화재    │ 월 16,200원 │ 비교하기    │
│ 3위 │ 삼성화재      │ 월 17,500원 │ 비교하기    │
│ 4위 │ 현대해상      │ 월 18,800원 │ 비교하기    │
│ 5위 │ DB손해보험    │ 월 19,500원 │ 비교하기    │
└─────────────────────────────────────────────────┘
```

**Data Source**:
- Proposals from `proposal_coverage_universe` + `proposal_coverage_mapped`
- Premium from proposal parser (existing STEP 6-C infrastructure)
- NOT from policy documents or coverage_standard alone

### 2.3. Single Proposal Comparison View

**Trigger**: User clicks "비교하기" on KB vs SAMSUNG

**Display**: Two-column comparison (enhancement of STEP 28 ComparableView)

```
┌──────────────────────┬──────────────────────┐
│   KB손해보험          │   삼성화재            │
├──────────────────────┼──────────────────────┤
│ 월 15,000원 (최저가) │ 월 17,500원 (+16%)   │
├──────────────────────┴──────────────────────┤
│ 핵심 보장 비교                              │
├──────────────────────┬──────────────────────┤
│ 일반암진단비          │ 일반암진단비          │
│ 3천만원              │ 3천만원              │
│ 질병 범위: C00-C97   │ 질병 범위: C00-C97   │
│ (유사암 5종 제외)    │ (유사암 5종 제외)    │
├──────────────────────┴──────────────────────┤
│ 왜 보험료가 다른가요?                        │
├─────────────────────────────────────────────┤
│ ✓ 담보 조건 동일 (canonical_coverage_code)  │
│ ⚠ 면책기간 차이: KB 90일 vs 삼성 없음       │
│ ⚠ 감액기간 차이: KB 1년 50% vs 삼성 2년 50% │
│                                             │
│ 📄 약관 근거: [삼성 무배당 NEW... 23조]     │
└─────────────────────────────────────────────┘
```

**Key Differences from STEP 28**:
- Premium highlighted as primary metric
- "Why different?" section added
- Policy evidence as **supporting explanation**, not main content

---

## 3. UI Components (Extension of STEP 28)

### 3.1. New Components

**PriceRankingView** (NEW)
- Top-N proposal cards sorted by premium
- Displays: rank, insurer, premium, CTA ("비교하기")
- Data: Array of proposals from backend

**PriceComparisonView** (EXTENDS ComparableView)
- Two-column layout (reuse STEP 28 structure)
- Premium diff highlighted
- "Why different?" section with:
  - Coverage match status (from comparison_result)
  - Exclusion/reduction differences (from policy_evidence)
  - Policy reference links (from policy_evidence.document_id)

### 3.2. Reused Components (No Change)

- ComparableView (base structure)
- Card, Button (UI primitives)
- ViewRenderer (contract-driven routing)

---

## 4. Data Flow (Proposal-Centered)

### 4.1. Input
```
User Query:
- coverage_name: "일반암진단비"
- amount: 30000000
- conditions: {age: 30, gender: "M", term: 100, payment: 10}
```

### 4.2. Backend Processing (Existing Infrastructure)

```
1. Universe Lookup (STEP 6-C)
   → proposal_coverage_universe
   WHERE coverage_name LIKE '%일반암진단비%'

2. Mapping Resolution (STEP 6-C)
   → proposal_coverage_mapped
   JOIN coverage_standard ON canonical_coverage_code

3. Premium Extraction (Existing Parser)
   → Extract premium from proposal JSON

4. Ranking
   → ORDER BY premium ASC
   LIMIT 10
```

### 4.3. Response
```json
{
  "query": {
    "coverage_name": "일반암진단비",
    "conditions": {"age": 30, "gender": "M", "term": 100, "payment": 10}
  },
  "ranking": [
    {
      "rank": 1,
      "insurer": "KB손해보험",
      "premium": 15000,
      "proposal_id": "KB_proposal_001",
      "canonical_coverage_code": "CRE_CVR_001"
    },
    {
      "rank": 2,
      "insurer": "메리츠화재",
      "premium": 16200,
      "proposal_id": "MERITZ_proposal_002",
      "canonical_coverage_code": "CRE_CVR_001"
    }
  ],
  "comparison_result": "comparable",
  "next_action": "COMPARE",
  "ux_message_code": "COVERAGE_MATCH_COMPARABLE"
}
```

---

## 5. "Why Different Premium?" Explanation

### 5.1. Data Sources (in priority order)

1. **Proposal** (primary)
   - Premium amount (definitive)
   - Coverage name, amount (universe)

2. **Coverage Mapping** (canonical identity)
   - canonical_coverage_code (comparison basis)

3. **Policy Evidence** (explanation)
   - Exclusion period (면책기간)
   - Reduction period (감액기간)
   - Disease scope differences
   - Document references

### 5.2. Explanation Logic

```
IF canonical_coverage_code identical:
  → Check policy_evidence for:
    - exclusion_period_days
    - reduction_period_years
    - reduction_percentage
    - disease_scope_raw vs disease_scope_norm

IF differences found:
  → Display: "⚠ 면책기간 차이: A사 90일 vs B사 없음"
  → Link to policy_evidence.document_id

IF no differences found:
  → Display: "보험료 차이 원인: 보험사 가격 정책"
```

### 5.3. Policy Evidence Display

**Format**:
```
📄 약관 근거:
  [삼성화재 무배당 NEW암보험 23조 "일반암 진단 시 보험금 지급"]
  - 면책기간: 계약일로부터 90일
  - 감액기간: 계약일로부터 1년, 50% 지급
```

**NOT**:
- ❌ Policy document viewer (requires inca-rag)
- ❌ Full policy text extraction
- ✅ Reference link + key excerpts only

---

## 6. Limitations (inca-rag Dependency)

The following features require full inca-rag integration:

1. **Actual Premium Calculation**
   - Proposals must exist in database
   - Premium = extracted value, not calculated

2. **Full Insurer Coverage**
   - Currently limited to seed data (3 insurers)
   - Top-N ranking limited by available proposals

3. **Policy Document Viewer**
   - Document storage not in inca-RAG-final
   - Only text excerpts from policy_evidence

**Placeholder Handling**:
- If proposal count < N → Show available only
- If premium missing → "보험료 정보 없음" (NOT error)
- If policy_evidence empty → "약관 확인 필요" (NOT error)

---

## 7. Constitutional Guarantees

### 7.1. Proposal-Centered Architecture

- ✅ Comparison target = Proposals only
- ✅ Premium = Proposal field (not calculated)
- ✅ Universe Lock principle (STEP 6-C) maintained
- ✅ Canonical coverage_code as comparison basis

### 7.2. Backend Contract Immutability (STEP 14-26)

- ✅ No changes to comparison_result enum
- ✅ No changes to next_action enum
- ✅ No changes to ux_message_code registry
- ✅ No changes to golden snapshots

### 7.3. Data Absence ≠ Error

- ✅ Missing premium → UI shows placeholder
- ✅ Missing policy_evidence → "약관 확인 필요"
- ✅ Single proposal → "비교 대상 없음" (valid state)

---

## 8. Design Principles

### 8.1. Proposal-First

**Correct Flow**:
```
Proposal → Premium → Comparison → Policy Explanation
```

**Prohibited Flow**:
```
Policy → Coverage → Premium Calculation ❌
```

### 8.2. Policy as Evidence, Not Source

**Policy Role**:
- Explain why premiums differ
- Validate proposal coverage details
- Provide legal reference

**Policy NOT**:
- ❌ Define comparison universe
- ❌ Source of premium data
- ❌ Primary comparison target

### 8.3. UX Freedom with Contract Constraints

**UI Can Change**:
- Layout, colors, text
- Ranking algorithm (price vs value)
- Number of cards displayed

**UI Cannot Change**:
- Backend Contract states
- comparison_result / next_action / ux_message_code
- Golden snapshot format

---

## 9. User Scenarios

### Scenario A: Perfect Match, Different Premiums
- Input: "일반암진단비", 3천만원, 100세만기
- Result: Top-5 proposals, all canonical_coverage_code identical
- Display: Premium ranking + "면책/감액 차이" explanation

### Scenario B: Partial Coverage, Premium Unavailable
- Input: "유사암진단비", 5백만원, 80세만기
- Result: Some proposals missing premium field
- Display: Available proposals + "보험료 정보 없음" placeholder

### Scenario C: Unmapped Coverage
- Input: "다빈치 수술비"
- Result: out_of_universe (STEP 6-C Universe Lock)
- Display: UnmappedView or OutOfUniverseView (STEP 28 existing)

### Scenario D: Single Insurer Only
- Input: Coverage only in one proposal
- Result: 1 proposal returned
- Display: "비교 대상 없음 (단일 보험사)" (valid state, not error)

---

## 10. Success Criteria (DoD)

This document defines:

- ✅ Proposal-centered user flow
- ✅ Top-N ranking UI spec
- ✅ Single comparison view spec
- ✅ "Why different?" explanation logic
- ✅ Data sources prioritized (Proposal > Mapping > Policy)
- ✅ Policy role clarified (evidence, not source)
- ✅ Limitations documented (inca-rag dependency)
- ✅ Constitutional principles maintained

**NOT Implemented** (intentionally):
- ❌ Backend API changes
- ❌ Frontend component code
- ❌ Database schema changes

**Next Steps** (if approved):
- PRICE_STATE_EXTENSION.md (UI aggregation state design)
- GAP_ANALYSIS_PRICE_VS_CONTRACT.md (contract compatibility check)
