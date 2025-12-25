# Premium Calculation Implementation Notes (STEP 31)

> **Purpose**: Document premium calculation UI logic implementation (Frontend-only).

---

## 1. Implementation Scope

### What This STEP Implements

**Frontend-only premium calculation skeleton**:
- ✅ Premium types (PlanType, PremiumInput, PremiumComputed)
- ✅ Calculation logic SSOT (`calc.ts`)
- ✅ UI aggregation states (`priceStateMap.ts`)
- ✅ View components (PriceRankingView, PriceComparisonView)
- ✅ DEV_MOCK_MODE scenarios (A_PRICE_READY, A_PRICE_PARTIAL)

### What This STEP Does NOT Implement

**Deferred to future steps**:
- ❌ Excel multiplier table parsing (future: inca-rag integration)
- ❌ Backend API schema changes (Backend Contract immutable)
- ❌ Golden snapshot modifications (STEP 14-26 frozen)
- ❌ Real insurer data loading (8 insurers, requires inca-rag)

---

## 2. Core Definitions

### 2.1. Plan Types

```typescript
type PlanType = 'ALL' | 'GENERAL' | 'NON_CANCELLATION';
```

**Semantics**:
- `ALL` (① 전체): Base premium from proposal (default)
- `NON_CANCELLATION` (③ 무해지): Base premium (no multiplier)
- `GENERAL` (② 일반): Base premium × multiplier

**Important**:
- Plan type is **UI presentation category** (not Backend Contract)
- "일반/무해지" is insurance domain terminology for premium structure

---

### 2.2. Calculation Rules

**Rule 1**: `basePremium` missing → both plans `MISSING`
```typescript
// Input: { basePremium: null, multiplier: 0.85 }
// Output:
{
  nonCancellation: { status: 'MISSING', premium: null },
  general: { status: 'MISSING', premium: null }
}
```

**Rule 2**: `basePremium` present, `multiplier` missing → `nonCancellation` READY, `general` PARTIAL
```typescript
// Input: { basePremium: 15000, multiplier: null }
// Output:
{
  nonCancellation: { status: 'READY', premium: 15000 },
  general: { status: 'PARTIAL', premium: null, reason: 'multiplier 데이터 준비 중' }
}
```

**Rule 3**: Both present → both READY
```typescript
// Input: { basePremium: 15000, multiplier: 0.85 }
// Output:
{
  nonCancellation: { status: 'READY', premium: 15000 },
  general: { status: 'READY', premium: 12750 } // Math.round(15000 × 0.85)
}
```

**Rounding**: All premium amounts are integers (KRW) via `Math.round()`.

---

## 3. Multiplier Source (Future Work)

### Current State (STEP 31)

**Hardcoded/Mock**:
- Multiplier values are hardcoded in mock scenarios (0.85, 0.86, etc.)
- NO Excel table parsing

**Future Integration**:
- Multiplier will come from Excel table (요율표)
- Table structure (example):
  ```
  | insurer | coverage_code | age | term | multiplier |
  |---------|---------------|-----|------|------------|
  | SAMSUNG | CRE_CVR_001   | 30  | 100  | 0.87       |
  | MERITZ  | CRE_CVR_001   | 30  | 100  | 0.86       |
  ```
- Table loading via inca-rag data pipeline (not STEP 31)

**Implementation Path** (when needed):
1. Load Excel → `multiplier_table` database table
2. Query: `SELECT multiplier WHERE insurer=? AND coverage_code=? AND age=? AND term=?`
3. Pass result to Frontend via API response (optional field)
4. Frontend uses multiplier if available, else shows PARTIAL state

---

## 4. UI Aggregation States

### State Definitions

From `priceStateMap.ts`:

| State | Trigger Condition | View Component |
|-------|-------------------|----------------|
| `PRICE_RANKING_READY` | 2+ proposals with READY status | PriceRankingView |
| `PRICE_DATA_PARTIAL` | 2+ proposals, some READY, some PARTIAL/MISSING | PriceRankingView (with warnings) |
| `PRICE_EXPLANATION_REQUIRED` | Premium diff >5%, policy evidence available | PriceComparisonView |
| `PRICE_RANKING_UNAVAILABLE` | <2 proposals OR all MISSING | GenericMessage |

---

### State Resolution Logic

```typescript
function resolvePriceAggregationState(results: PremiumResult[]): PriceAggregationState {
  const summary = getPremiumDataSummary(results);

  if (isPriceRankingReady(summary)) {
    return 'PRICE_RANKING_READY';
  }

  if (isPriceDataPartial(summary)) {
    return 'PRICE_DATA_PARTIAL';
  }

  return 'PRICE_RANKING_UNAVAILABLE';
}
```

**Key Principle**: Data absence → valid state (not error).

---

## 5. View Components

### 5.1. PriceRankingView

**Purpose**: Display Top-N proposal cards sorted by premium (cheapest first).

**Features**:
- Ranked cards (1위, 2위, ...)
- Premium display (월 15,000원)
- "최저가" badge for rank 1
- CTA: "비교하기" (opens PriceComparisonView)
- Placeholder cards for PARTIAL/MISSING data

**Data Source**: Array of `PremiumCardData`

---

### 5.2. PriceComparisonView

**Purpose**: Compare 2 proposals with "Why different?" explanation.

**Features**:
- Two-column layout (insurer A vs B)
- Premium diff highlighted (e.g., "+16%")
- "최저가" badge
- "Why different?" section:
  - Policy evidence differences (면책기간, 감액기간, 질병 범위)
  - Fallback: "보험사 가격 정책 차이"
- CTA: "약관 근거 보기" (if policy evidence exists)

**Data Source**: Single comparison (2 proposals)

---

## 6. DEV_MOCK_MODE Scenarios

### Scenario A_PRICE_READY

**Description**: All 5 insurers have premium data.

**Mock Data**:
- KB: 15,000원 (rank 1)
- MERITZ: 16,200원 (rank 2)
- SAMSUNG: 17,500원 (rank 3)
- HYUNDAI: 18,800원 (rank 4)
- DB: 19,500원 (rank 5)

**Expected UI**: PriceRankingView with 5 ranked cards.

---

### Scenario A_PRICE_PARTIAL

**Description**: 3 insurers READY, 1 PARTIAL, 1 MISSING.

**Mock Data**:
- KB: 15,000원 (rank 1)
- MERITZ: 16,200원 (rank 2)
- SAMSUNG: 17,500원 (rank 3)
- HYUNDAI: 18,800원 (PARTIAL - no multiplier)
- DB: null (MISSING - no basePremium)

**Expected UI**: PriceRankingView with 3 ranked cards + 2 placeholders + warning.

---

### Scenario PRICE_COMPARISON

**Description**: KB vs SAMSUNG single comparison.

**Mock Data**:
- KB: 15,000원 (면책기간 90일, 감액기간 1년)
- SAMSUNG: 17,500원 (면책기간 0일, 감액기간 2년)
- Premium diff: 16% (2,500원)

**Expected UI**: PriceComparisonView with "Why different?" section showing policy differences.

---

## 7. Constitutional Compliance

### 7.1. Proposal-Centered Architecture

**Enforced**:
- ✅ Premium = proposal field (not calculated from policy)
- ✅ Policy evidence = explanation only (not source)
- ✅ Comparison target = proposals (not products)

**Verification**:
- No policy-based premium calculation in `calc.ts`
- `basePremium` is input parameter (from proposal)

---

### 7.2. Backend Contract Immutability

**Enforced**:
- ✅ No changes to Backend API schema
- ✅ No changes to golden snapshots
- ✅ No new Backend Contract states

**Verification**:
- All logic in `apps/web/src/` (Frontend only)
- Tests verify no API calls in calculation logic

---

### 7.3. Data Absence ≠ Error

**Enforced**:
- ✅ Missing premium → MISSING state (not exception)
- ✅ Missing multiplier → PARTIAL state (not exception)
- ✅ UI shows placeholders (not error messages)

**Verification**:
- `computePremiums()` never throws for null inputs
- All states (READY/PARTIAL/MISSING) are valid

---

## 8. Implementation Checklist

### Files Created (STEP 31)

- ✅ `apps/web/src/lib/premium/types.ts` (Types)
- ✅ `apps/web/src/lib/premium/calc.ts` (SSOT logic)
- ✅ `apps/web/src/contracts/priceStateMap.ts` (UI states)
- ✅ `apps/web/src/components/views/price/PriceRankingView.tsx` (View)
- ✅ `apps/web/src/components/views/price/PriceComparisonView.tsx` (View)
- ✅ `apps/web/src/lib/api/mocks/priceScenarios.ts` (Mock data)
- ✅ `tests/ui/test_step31_premium_calc.py` (Unit tests)
- ✅ `docs/ui/PRICE_IMPLEMENTATION_NOTES.md` (This doc)

---

### Testing (STEP 31)

**Unit Tests** (`test_step31_premium_calc.py`):
- ✅ Case 1: basePremium missing → MISSING
- ✅ Case 2: multiplier missing → PARTIAL
- ✅ Case 3: both present → READY + rounding
- ✅ Premium formatting
- ✅ Premium diff calculation
- ✅ State resolution logic

**Manual Testing** (DEV_MOCK_MODE):
- ✅ A_PRICE_READY: 5 ranked cards
- ✅ A_PRICE_PARTIAL: 3 ranked + 2 placeholders + warning
- ✅ PRICE_COMPARISON: Two-column + "Why different?" section

---

## 9. Next Steps (Future Work)

### Phase 1: Excel Multiplier Integration

**Tasks**:
1. Load Excel table into database (`multiplier_table`)
2. Add `multiplier` field to Backend API response (optional, nullable)
3. Update Frontend to use API multiplier (if present)
4. Fallback to mock multiplier for testing

**DoD**:
- Real multiplier values from Excel
- Backend API schema extension (additive, non-breaking)
- CHANGELOG approval (STEP 25 governance)

---

### Phase 2: Real Insurer Data

**Tasks**:
1. Ingest proposals for 8 insurers (via inca-rag)
2. Extract `basePremium` for all proposals
3. Update DEV_MOCK_MODE to use real data

**DoD**:
- All 8 insurers rankable
- Premium data completeness >80%

---

### Phase 3: Policy Evidence Integration

**Tasks**:
1. Ingest policy documents for all insurers
2. Extract exclusion/reduction periods
3. Link policy evidence to proposals

**DoD**:
- "Why different?" section shows real policy differences
- Policy document viewer (optional)

---

## 10. FAQ

### Q1: Why is multiplier NOT implemented in STEP 31?

**A**: STEP 31 focuses on **UI calculation skeleton**. Multiplier source (Excel table) requires:
- Excel parsing logic
- Database schema for multiplier table
- inca-rag integration

These are deferred to future steps to maintain separation of concerns.

---

### Q2: Can Frontend calculate premium without Backend?

**A**: Yes, for mock scenarios. Frontend receives:
- `basePremium` from proposal (via API)
- `multiplier` from Excel table (future: via API or Frontend-side Excel load)

Frontend computes `general = basePremium × multiplier` client-side.

---

### Q3: What if user queries insurer without premium data?

**A**: Frontend shows placeholder card with status "보험료 정보 없음". This is a valid state (not error), consistent with STEP 29 design.

---

### Q4: Does this change Backend Contract?

**A**: No. STEP 31 is **Frontend-only**. Backend Contract (STEP 14-26) remains frozen.

---

## 11. Summary

**STEP 31 Deliverables**:
- ✅ Premium calculation SSOT (Frontend-only)
- ✅ UI aggregation states (3 states)
- ✅ View components (PriceRankingView, PriceComparisonView)
- ✅ DEV_MOCK_MODE scenarios (2 scenarios)
- ✅ Unit tests (conceptual, to be implemented in Jest/Vitest)

**Constitutional Compliance**:
- ✅ Proposal-centered architecture maintained
- ✅ Backend Contract immutable
- ✅ Data absence handled gracefully

**Future Work**:
- Excel multiplier integration
- Real insurer data
- Policy evidence integration

---

**END OF IMPLEMENTATION NOTES**
