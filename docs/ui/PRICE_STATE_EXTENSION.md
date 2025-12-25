# UI State Extension for Premium Comparison (STEP 29)

> **Constitutional Principle**: Backend Contract (STEP 14-26) is immutable.
> Premium comparison states are **UI-level aggregations**, not Backend Contract states.

---

## 1. Core Principle

### Backend Contract Immutability

**What Cannot Change**:
- ✅ `comparison_result` registry (STEP 24)
- ✅ `next_action` registry (STEP 24)
- ✅ `ux_message_code` registry (STEP 26)
- ✅ State key format: `{result}:{action}:{ux_code}`

**What This Document Defines**:
- ❌ NOT new Backend states
- ✅ UI aggregation patterns
- ✅ View component selection rules
- ✅ Premium-specific display configs

---

## 2. UI Aggregation States (Premium Context)

### 2.1. PRICE_RANKING_READY

**Definition**: UI state for displaying Top-N premium ranking.

**Backend Contract Mapping**:
- Backend returns **array of comparison results** (one per proposal)
- Each result has state: `comparable:COMPARE:COVERAGE_MATCH_COMPARABLE`
- UI aggregates array → single "ranking ready" state

**Trigger Conditions**:
```typescript
interface PriceRankingReady {
  // Backend responses (array)
  comparisons: ProposalCompareResponse[];

  // UI aggregation check
  allMapped: boolean;  // all canonical_coverage_code identical
  premiumsAvailable: boolean;  // all proposals have premium field
  minProposals: number;  // at least 2 proposals
}

function isPriceRankingReady(data): boolean {
  return (
    data.comparisons.length >= 2 &&
    data.allMapped &&
    data.premiumsAvailable
  );
}
```

**View Component**: `PriceRankingView`

**Display**:
- Top-N proposal cards sorted by premium ASC
- Rank, insurer, premium, CTA per card

**CTAs**:
- Primary: "비교하기" (per card)
- Secondary: "다른 담보 검색"

---

### 2.2. PRICE_DATA_PARTIAL

**Definition**: UI state for partial premium data (some proposals missing premium).

**Backend Contract Mapping**:
- Backend returns mixed array:
  - Some: `comparable:COMPARE:COVERAGE_MATCH_COMPARABLE` + premium
  - Some: `comparable:COMPARE:COVERAGE_MATCH_COMPARABLE` + premium=null

**Trigger Conditions**:
```typescript
interface PriceDataPartial {
  comparisons: ProposalCompareResponse[];

  // Partial data check
  someHavePremium: boolean;  // at least 1 has premium
  someNullPremium: boolean;  // at least 1 missing premium
}

function isPriceDataPartial(data): boolean {
  const withPremium = data.comparisons.filter(c => c.premium !== null);
  const withoutPremium = data.comparisons.filter(c => c.premium === null);

  return (
    withPremium.length > 0 &&
    withoutPremium.length > 0
  );
}
```

**View Component**: `PriceRankingView` (with partial data warning)

**Display**:
- Proposals with premium → ranked cards
- Proposals without premium → placeholder cards with "보험료 정보 없음"

**CTAs**:
- Primary: "비교하기" (available proposals only)
- Secondary: "전체 보험사 보기"

**Warning**:
```
⚠ 일부 보험사의 보험료 정보가 준비 중입니다
현재 {N}개 보험사 비교 가능
```

---

### 2.3. PRICE_EXPLANATION_REQUIRED

**Definition**: UI state for explaining why premiums differ (detail view).

**Backend Contract Mapping**:
- Backend returns **single comparison** (2 proposals):
  - `comparable:COMPARE:COVERAGE_MATCH_COMPARABLE`
  - + `policy_evidence_a` (optional)
  - + `policy_evidence_b` (optional)

**Trigger Conditions**:
```typescript
interface PriceExplanationRequired {
  comparison: ProposalCompareResponse;

  // Premium difference check
  premiumDiff: number;  // abs(premium_a - premium_b)
  premiumDiffPercent: number;  // (diff / min) * 100

  // Explanation data availability
  hasPolicyEvidence: boolean;
  hasExclusionDiff: boolean;
  hasReductionDiff: boolean;
}

function isPriceExplanationRequired(data): boolean {
  return (
    data.premiumDiffPercent > 5 &&  // >5% difference
    data.comparison.comparison_result === "comparable"
  );
}
```

**View Component**: `PriceComparisonView` (extends `ComparableView`)

**Display**:
- Two-column comparison (existing STEP 28 layout)
- Premium diff highlighted
- "Why different?" section:
  - IF policy_evidence exists:
    - Show exclusion_period diff
    - Show reduction_period diff
    - Show disease_scope diff
  - ELSE:
    - Show "보험사 가격 정책 차이"

**CTAs**:
- Primary: "약관 보기" (if policy_evidence available)
- Secondary: "다른 보험사 비교"

---

## 3. State Resolution Flow

### 3.1. Single Proposal Comparison (Existing STEP 28)

**Input**: User selects 2 specific insurers
**Backend**: Returns 1 comparison result
**UI State**: Resolve from 3-tuple directly (no aggregation)

```typescript
// Existing flow (unchanged)
const stateKey = `${comparison_result}:${next_action}:${ux_message_code}`;
const uiState = UI_STATE_MAP[stateKey];
```

**Example**: Scenario A (SAMSUNG vs MERITZ)
- State: `comparable:COMPARE:COVERAGE_MATCH_COMPARABLE`
- View: `ComparableView`
- NO premium context (just coverage comparison)

---

### 3.2. Premium Ranking (NEW STEP 29)

**Input**: User queries coverage without specifying insurers
**Backend**: Returns array of comparison results (1 per proposal)
**UI State**: Aggregate array → premium ranking state

```typescript
// New flow (premium context)
function resolvePriceUIState(comparisons: ProposalCompareResponse[]) {
  if (isPriceRankingReady(comparisons)) {
    return {
      view: "PriceRankingView",
      aggregationState: "PRICE_RANKING_READY",
      severity: "success"
    };
  }

  if (isPriceDataPartial(comparisons)) {
    return {
      view: "PriceRankingView",
      aggregationState: "PRICE_DATA_PARTIAL",
      severity: "warning"
    };
  }

  // Fallback: single proposal or all unmapped
  return {
    view: "GenericMessage",
    aggregationState: "PRICE_RANKING_UNAVAILABLE",
    severity: "info"
  };
}
```

**Example**: Query "일반암진단비" (no insurer specified)
- Backend returns: [comparison_A, comparison_B, comparison_C, ...]
- All states: `comparable:COMPARE:COVERAGE_MATCH_COMPARABLE`
- UI aggregation: `PRICE_RANKING_READY`
- View: `PriceRankingView`

---

### 3.3. Premium Explanation (NEW STEP 29)

**Input**: User clicks "비교하기" on 2 proposals from ranking
**Backend**: Returns 1 comparison result (same as STEP 28)
**UI State**: Check premium diff → add explanation section

```typescript
// Enhanced flow (premium + explanation)
function resolvePriceComparisonUIState(comparison: ProposalCompareResponse) {
  const baseState = resolveUIState(comparison);  // STEP 27 logic

  if (isPriceExplanationRequired(comparison)) {
    return {
      ...baseState,
      view: "PriceComparisonView",  // extends ComparableView
      aggregationState: "PRICE_EXPLANATION_REQUIRED",
      showExplanation: true
    };
  }

  return baseState;  // fallback to base view
}
```

**Example**: KB vs SAMSUNG (from ranking)
- Backend state: `comparable:COMPARE:COVERAGE_MATCH_COMPARABLE`
- Premium diff: 16% (15,000원 vs 17,500원)
- UI aggregation: `PRICE_EXPLANATION_REQUIRED`
- View: `PriceComparisonView` (with "Why different?" section)

---

## 4. Backend Contract Boundary

### What Backend Provides (Unchanged)

**Single Comparison** (`POST /compare`):
```json
{
  "comparison_result": "comparable",
  "next_action": "COMPARE",
  "ux_message_code": "COVERAGE_MATCH_COMPARABLE",
  "coverage_a": { "amount_value": 50000000, "premium": 15000 },
  "coverage_b": { "amount_value": 50000000, "premium": 17500 },
  "policy_evidence_a": { /* ... */ },
  "policy_evidence_b": { /* ... */ }
}
```

**What Backend Does NOT Provide**:
- ❌ Premium ranking (array of proposals)
- ❌ Top-N cheapest proposals
- ❌ Premium diff calculation
- ❌ "Why different?" explanation logic

---

### What UI Does (Premium Extension)

**Ranking Aggregation**:
- Call `/compare` multiple times (once per insurer pair)
- Aggregate responses client-side
- Sort by premium ASC
- Display top N

**Explanation Derivation**:
- Calculate premium_diff from response
- Extract policy_evidence differences
- Format "Why different?" message
- Display in extended view

---

## 5. UI State Map Extension

### 5.1. Existing States (STEP 27 - Unchanged)

```typescript
// From UI_CONTRACT.md
export const UI_STATE_MAP: Record<string, UIStateConfig> = {
  "comparable:COMPARE:COVERAGE_MATCH_COMPARABLE": {
    view: "CompareResult",
    primaryCta: "compare",
    severity: "success"
  },
  "unmapped:REQUEST_MORE_INFO:COVERAGE_UNMAPPED": {
    view: "GenericMessage",
    primaryCta: "search_again",
    severity: "warning"
  },
  // ... other states
};
```

**No Changes**: These states remain as-is.

---

### 5.2. Premium Aggregation States (NEW)

```typescript
// Premium-specific UI aggregation
export const PRICE_AGGREGATION_STATE_MAP = {
  PRICE_RANKING_READY: {
    view: "PriceRankingView",
    title: "보험료 최저가 비교",
    description: "{N}개 보험사 중 가장 저렴한 순위입니다",
    primaryCta: "compare",  // per card
    secondaryCta: "search_again",
    severity: "success",
    requiresAggregation: true  // flag for UI logic
  },

  PRICE_DATA_PARTIAL: {
    view: "PriceRankingView",
    title: "보험료 비교 (일부 데이터)",
    description: "현재 {N}개 보험사 비교 가능 (일부 준비 중)",
    primaryCta: "compare",
    secondaryCta: "view_all_insurers",
    severity: "warning",
    requiresAggregation: true
  },

  PRICE_EXPLANATION_REQUIRED: {
    view: "PriceComparisonView",
    title: "보험료 비교 상세",
    description: "왜 보험료가 다른지 확인하세요",
    primaryCta: "view_policy",
    secondaryCta: "compare_other",
    severity: "info",
    requiresAggregation: false  // single comparison
  },

  PRICE_RANKING_UNAVAILABLE: {
    view: "GenericMessage",
    title: "보험료 비교 불가",
    description: "비교 가능한 가입설계서가 부족합니다",
    primaryCta: "search_again",
    severity: "info",
    requiresAggregation: false
  }
};
```

---

### 5.3. Resolution Logic

```typescript
// Main resolver (frontend)
export function resolveUIState(
  response: ProposalCompareResponse | ProposalCompareResponse[]
): UIStateConfig {
  // Case 1: Array of responses → Premium ranking context
  if (Array.isArray(response)) {
    const aggregationState = resolvePriceAggregationState(response);
    return PRICE_AGGREGATION_STATE_MAP[aggregationState];
  }

  // Case 2: Single response → Check for premium explanation
  if (isPriceExplanationRequired(response)) {
    return PRICE_AGGREGATION_STATE_MAP.PRICE_EXPLANATION_REQUIRED;
  }

  // Case 3: Single response → Use base contract state (STEP 27)
  const stateKey = `${response.comparison_result}:${response.next_action}:${response.ux_message_code}`;
  return UI_STATE_MAP[stateKey] || FALLBACK_STATE;
}
```

---

## 6. Premium Data Handling

### 6.1. Premium Field in Backend Response

**Current Schema** (from STEP 6-C proposal parser):
```python
# Assumed proposal schema (not in Backend Contract)
{
  "premium": 15000,  # monthly premium in KRW
  "premium_term": "monthly",  # or "annual"
  "premium_currency": "KRW"
}
```

**Backend Contract**: DOES NOT guarantee premium field.

**UI Handling**:
```typescript
interface PremiumDisplay {
  value: number | null;
  term: "monthly" | "annual";
  currency: "KRW";
  unavailable: boolean;  // true if null
}

function getPremiumDisplay(response: ProposalCompareResponse): PremiumDisplay {
  if (response.coverage_a?.premium === null) {
    return { value: null, term: "monthly", currency: "KRW", unavailable: true };
  }
  return {
    value: response.coverage_a.premium,
    term: response.coverage_a.premium_term || "monthly",
    currency: "KRW",
    unavailable: false
  };
}
```

---

### 6.2. Data Absence Handling

**Missing Premium** (proposal field null):
- UI State: `PRICE_DATA_PARTIAL` (if some proposals have premium)
- Display: "보험료 정보 없음" placeholder card
- NOT an error: Data preparation ongoing

**All Premiums Missing**:
- UI State: `PRICE_RANKING_UNAVAILABLE`
- Display: "보험료 비교를 위한 데이터가 준비 중입니다"
- CTA: "알림 받기"

**Single Proposal Only**:
- UI State: `PRICE_RANKING_UNAVAILABLE`
- Display: "비교 대상 보험사가 1개뿐입니다"
- CTA: "다른 담보 검색"

---

## 7. Constitutional Guarantees

### 7.1. Backend Contract Immutability

**Confirmed**:
- ✅ No changes to `comparison_result` registry
- ✅ No changes to `next_action` registry
- ✅ No changes to `ux_message_code` registry
- ✅ No changes to golden snapshots
- ✅ No new Backend states

**All Premium Logic**:
- ✅ UI-level aggregation only
- ✅ Client-side ranking
- ✅ Client-side explanation derivation

---

### 7.2. Proposal-Centered Architecture

**Premium Source**:
- ✅ Proposal field (not calculated)
- ✅ Extracted by existing parser (STEP 6-C)
- ✅ NOT from policy documents

**Comparison Target**:
- ✅ Proposals only (Universe Lock maintained)
- ✅ canonical_coverage_code as comparison basis
- ✅ Policy as explanation evidence only

---

### 7.3. Graceful Degradation

**Unknown Aggregation State**:
- Fallback to `PRICE_RANKING_UNAVAILABLE`
- Log to monitoring (contract drift)
- Display generic message

**Partial Data**:
- Show available proposals
- Mark unavailable as "준비 중"
- NOT an error

---

## 8. Frontend Implementation Notes

### 8.1. State Resolution Order

```typescript
// Priority order
1. Check if array (premium ranking context)
   → resolvePriceAggregationState()

2. Check if premium explanation needed (single comparison)
   → isPriceExplanationRequired()

3. Fallback to base contract state (STEP 27)
   → UI_STATE_MAP[stateKey]

4. Unknown state fallback
   → FALLBACK_STATE
```

---

### 8.2. API Call Pattern

**Scenario 1: Premium Ranking**
```typescript
// Call /compare for each insurer pair
const insurers = ["SAMSUNG", "MERITZ", "KB", "HYUNDAI"];
const query = { coverage_name: "일반암진단비", conditions: {...} };

const comparisons = await Promise.all(
  insurers.map(insurer =>
    compareClient.compare({ ...query, insurer_a: insurer, insurer_b: "SAMSUNG" })
  )
);

// Aggregate and resolve
const uiState = resolveUIState(comparisons);  // returns PRICE_RANKING_READY
```

**Scenario 2: Premium Explanation**
```typescript
// User clicks "비교하기" on KB vs SAMSUNG
const comparison = await compareClient.compare({
  coverage_name: "일반암진단비",
  insurer_a: "KB",
  insurer_b: "SAMSUNG"
});

// Resolve with premium context
const uiState = resolveUIState(comparison);  // returns PRICE_EXPLANATION_REQUIRED
```

---

### 8.3. Component Reuse

**PriceRankingView** (NEW):
- Uses `Card` primitive (STEP 28)
- Uses `Button` primitive (STEP 28)
- NO changes to existing components

**PriceComparisonView** (EXTENDS `ComparableView`):
- Inherits two-column layout
- Adds "Why different?" section
- Uses existing `policy_evidence` display

**No Impact on**:
- `UnmappedView`
- `PolicyRequiredView`
- `OutOfUniverseView`
- `UnknownStateView`

---

## 9. Testing Strategy

### 9.1. Unit Tests (Frontend)

**Test Cases**:
```typescript
describe("resolvePriceAggregationState", () => {
  it("returns PRICE_RANKING_READY when all proposals have premium", () => {
    const comparisons = [
      { premium: 15000, comparison_result: "comparable" },
      { premium: 16200, comparison_result: "comparable" }
    ];
    expect(resolvePriceAggregationState(comparisons)).toBe("PRICE_RANKING_READY");
  });

  it("returns PRICE_DATA_PARTIAL when some premiums missing", () => {
    const comparisons = [
      { premium: 15000, comparison_result: "comparable" },
      { premium: null, comparison_result: "comparable" }
    ];
    expect(resolvePriceAggregationState(comparisons)).toBe("PRICE_DATA_PARTIAL");
  });
});
```

---

### 9.2. Integration Tests (No Backend Changes)

**Test Scenarios**:
- Premium ranking with mock data
- Partial data warning display
- Premium explanation with policy evidence
- Fallback to unavailable state

**Mock Data**: Use existing golden snapshots + premium field added.

---

## 10. DoD (Definition of Done)

This document defines:

- ✅ UI aggregation states (3 states: RANKING_READY, DATA_PARTIAL, EXPLANATION_REQUIRED)
- ✅ State resolution flow (array vs single response)
- ✅ Backend Contract boundary (what UI does vs Backend does)
- ✅ Premium data handling (field extraction, null handling)
- ✅ Constitutional guarantees (Backend Contract unchanged)
- ✅ Implementation notes (API call pattern, component reuse)

**NOT Implemented** (intentionally):
- ❌ Backend API changes
- ❌ New Backend states
- ❌ Frontend component code
- ❌ Golden snapshot updates

**Next Steps** (if approved):
- GAP_ANALYSIS_PRICE_VS_CONTRACT.md (verify no contract conflicts)
- Frontend implementation (PriceRankingView, PriceComparisonView)
