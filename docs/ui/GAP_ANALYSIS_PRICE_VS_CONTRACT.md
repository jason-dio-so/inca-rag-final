# Gap Analysis: Premium Comparison vs Backend Contract (STEP 29)

> **Purpose**: Verify that premium comparison UX (STEP 29) does not violate Backend Contract (STEP 14-26).

---

## 1. Analysis Framework

### 1.1. Questions to Answer

1. **Contract Compatibility**: Can current Backend Contract support premium comparison UX?
2. **Frontend Extension Boundary**: What can Frontend do without Backend changes?
3. **inca-rag Dependency**: What requires full inca-rag integration?
4. **Risk Assessment**: What breaks if we implement premium UX?

---

## 2. Backend Contract Verification

### 2.1. Current Contract State (STEP 14-26)

**Frozen Elements**:
- `comparison_result` enum (STEP 24)
  - Values: `comparable`, `unmapped`, `policy_required`, `out_of_universe`, etc.
- `next_action` enum (STEP 24)
  - Values: `COMPARE`, `REQUEST_MORE_INFO`, `VERIFY_POLICY`
- `ux_message_code` registry (STEP 26)
  - Values: `COVERAGE_MATCH_COMPARABLE`, `COVERAGE_UNMAPPED`, etc.
- Golden snapshots (5 scenarios: A/B/C/D/E)

**API Schema** (FastAPI `ProposalCompareResponse`):
```python
class ProposalCompareResponse(BaseModel):
    comparison_result: str
    next_action: str
    ux_message_code: str
    message: str
    coverage_a: Optional[CoverageDetail]
    coverage_b: Optional[CoverageDetail]
    policy_evidence_a: Optional[PolicyEvidence]
    policy_evidence_b: Optional[PolicyEvidence]
    canonical_coverage_code: Optional[str]
    query: str
    # ... other fields
```

**Contract CI Gates** (`.github/workflows/ci-contract-guard.yml`):
- STEP 24: Registry contract tests
- STEP 25: Governance gate (CHANGELOG required)
- STEP 26: UX message code contract tests

---

### 2.2. Premium Comparison Requirements

**What Premium UX Needs**:
1. Premium field in response (`coverage_a.premium`, `coverage_b.premium`)
2. Multiple proposal comparison (array of responses)
3. Premium ranking (sorted by premium ASC)
4. Premium explanation (why different?)

**Gap Analysis**:

| Requirement | Backend Contract Support | Gap | Solution |
|-------------|-------------------------|-----|----------|
| Premium field in response | ❌ NOT in contract schema | Schema extension needed | ✅ Additive change (non-breaking) |
| Array of responses | ❌ Single comparison only | API pattern change needed | ✅ Frontend aggregation (no Backend change) |
| Premium ranking | ❌ No ranking endpoint | Backend feature gap | ✅ Frontend sorting (no Backend change) |
| Premium explanation | ✅ `policy_evidence` exists | No gap | ✅ Use existing field |

---

## 3. Gap Assessment by Requirement

### Gap 1: Premium Field in Response Schema

**Current State**:
- `CoverageDetail` schema DOES NOT include `premium` field.
- Proposals contain premium (extracted by STEP 6-C parser).
- Premium NOT exposed in Compare API response.

**Impact**:
- ❌ Frontend cannot display premium ranking without Backend change.

**Solutions**:

**Option A: Add premium field to schema (Backend change)**
```python
class CoverageDetail(BaseModel):
    # ... existing fields
    premium: Optional[int] = None  # monthly premium in KRW
    premium_term: Optional[str] = None  # "monthly" | "annual"
```

**Risk**: Schema change requires:
- Golden snapshot updates (all 5 scenarios)
- CHANGELOG approval (STEP 25 governance)
- Contract CI gate pass (STEP 24/26 tests)

**Option B: Frontend-only with mock data (no Backend change)**
```typescript
// DEV_MOCK_MODE: Add premium to golden snapshots locally
GOLDEN_SNAPSHOTS.scenario_a.coverage_a.premium = 15000;
```

**Risk**: Real API won't have premium field.

**Recommendation**: **Option A** (schema extension as additive change).
- Justification: Premium is proposal field (already extracted).
- Non-breaking: Nullable field (`Optional[int]`).
- Governance: Requires CHANGELOG approval (STEP 25).

**Verdict**: **Acceptable gap** - Can be closed with additive schema change.

---

### Gap 2: Multiple Proposal Comparison (Array Responses)

**Current State**:
- Compare API returns single comparison (`insurer_a` vs `insurer_b`).
- No endpoint for "all insurers for coverage X".

**Impact**:
- ❌ Frontend must call `/compare` N times to rank N insurers.

**Solutions**:

**Option A: New endpoint `/compare/ranking` (Backend change)**
```python
@router.post("/compare/ranking")
def compare_ranking(query: str, conditions: dict) -> List[ProposalCompareResponse]:
    # Return all proposals for coverage, sorted by premium
    pass
```

**Risk**: New endpoint requires:
- New Backend Contract state (violates immutability).
- Golden snapshot for ranking endpoint.
- CI gate extension.

**Option B: Frontend aggregation (no Backend change)**
```typescript
// Call /compare for each insurer
const insurers = ["SAMSUNG", "MERITZ", "KB"];
const comparisons = await Promise.all(
  insurers.map(insurer => compareClient.compare({ insurer_a: insurer, ... }))
);
// Sort and rank client-side
comparisons.sort((a, b) => a.coverage_a.premium - b.coverage_a.premium);
```

**Risk**: N API calls (performance).

**Recommendation**: **Option B** (Frontend aggregation).
- Justification: Backend Contract immutable (STEP 29 constraint).
- Performance: Acceptable for N < 10 insurers.
- Governance: No Backend change needed.

**Verdict**: **No gap** - Frontend can handle aggregation.

---

### Gap 3: Premium Ranking Logic

**Current State**:
- No Backend logic for ranking proposals by premium.

**Impact**:
- ✅ Frontend can sort array client-side (no Backend change needed).

**Solutions**:

**Option A: Backend ranking (Backend change)**
- Add `ORDER BY premium ASC` in Backend query.

**Option B: Frontend sorting (no Backend change)**
```typescript
const ranked = comparisons
  .filter(c => c.coverage_a.premium !== null)
  .sort((a, b) => a.coverage_a.premium - b.coverage_a.premium)
  .slice(0, 10);  // top 10
```

**Recommendation**: **Option B** (Frontend sorting).
- Justification: Simple logic, no Backend dependency.
- Performance: Sorting 10-20 items client-side is trivial.

**Verdict**: **No gap** - Frontend handles ranking.

---

### Gap 4: Premium Explanation (Why Different?)

**Current State**:
- `policy_evidence` field exists in Backend Contract.
- Contains: `disease_code_group`, `exclusion_period`, `reduction_period`.

**Impact**:
- ✅ Frontend can extract explanation from existing `policy_evidence` field.

**Example**:
```typescript
function getPremiumExplanation(comparison: ProposalCompareResponse): string {
  const evidenceA = comparison.policy_evidence_a;
  const evidenceB = comparison.policy_evidence_b;

  if (evidenceA?.exclusion_period !== evidenceB?.exclusion_period) {
    return `면책기간 차이: ${evidenceA.exclusion_period}일 vs ${evidenceB.exclusion_period}일`;
  }

  return "보험사 가격 정책 차이";
}
```

**Recommendation**: Use existing field (no Backend change).

**Verdict**: **No gap** - Existing contract supports explanation.

---

## 4. Frontend Extension Boundary

### 4.1. What Frontend CAN Do (No Backend Changes)

✅ **Premium ranking UX**:
- Call `/compare` N times (once per insurer)
- Aggregate responses client-side
- Sort by premium ASC
- Display Top-N cards

✅ **Premium explanation**:
- Extract `policy_evidence` differences
- Format "Why different?" message
- Display in extended view

✅ **Partial data handling**:
- Filter null premiums
- Show "보험료 정보 없음" placeholder
- Treat as valid state (not error)

✅ **UI aggregation states** (STEP 29 PRICE_STATE_EXTENSION.md):
- `PRICE_RANKING_READY`
- `PRICE_DATA_PARTIAL`
- `PRICE_EXPLANATION_REQUIRED`

---

### 4.2. What Frontend CANNOT Do (Requires Backend Changes)

❌ **Premium field in response**:
- Requires schema extension (`CoverageDetail.premium`)
- Requires golden snapshot updates
- Requires CHANGELOG approval

❌ **Optimized ranking endpoint**:
- `/compare/ranking` would reduce N calls to 1
- Requires new Backend Contract state
- Requires new golden snapshot

❌ **Premium calculation**:
- Proposals must exist in database with premium
- Cannot calculate premium from policy (not in scope)

---

## 5. inca-rag Dependency Analysis

### 5.1. What Requires Full inca-rag Integration

**Proposal Universe Completeness**:
- Current: 3 insurers (SAMSUNG, MERITZ, KB) from seed data
- Full: All insurers with proposal extraction pipeline
- Impact: Premium ranking limited to seed data insurers

**Premium Data Availability**:
- Current: Premium extracted from seed proposals
- Full: All proposals with premium field
- Impact: `PRICE_DATA_PARTIAL` state common in current system

**Policy Document Evidence**:
- Current: policy_evidence from seed data only
- Full: Full policy ingestion pipeline
- Impact: "Why different?" explanation limited

---

### 5.2. What Works WITHOUT inca-rag

✅ **Premium ranking with seed data**:
- 3 insurers rankable
- Top-N limited to available proposals
- NOT an error (valid limitation)

✅ **Premium explanation with partial evidence**:
- If policy_evidence exists → show differences
- If policy_evidence null → show "약관 확인 필요"

✅ **DEV_MOCK_MODE testing**:
- Frontend can test full UX with mock data
- No Backend required

---

## 6. Risk Assessment

### 6.1. Contract Violation Risks

**Risk**: Premium field addition breaks golden snapshots.

**Mitigation**:
- Use `Optional[int]` (nullable field)
- Update all 5 golden snapshots
- Get CHANGELOG approval (STEP 25)
- Pass contract CI gates (STEP 24/26)

**Severity**: **Low** (additive change is non-breaking)

---

**Risk**: Premium UX tempts Backend Contract changes (new states, new endpoints).

**Mitigation**:
- Document Frontend extension boundary (this document)
- Use UI aggregation states (not Backend states)
- Resist "optimization" that requires Backend changes

**Severity**: **Medium** (governance enforcement needed)

---

**Risk**: Premium ranking reveals data incompleteness (missing insurers).

**Mitigation**:
- Treat data absence as valid state (not error)
- Show "데이터 준비 중" placeholders
- Document inca-rag dependency

**Severity**: **Low** (UX design accounts for this)

---

### 6.2. System Integrity Risks

**Risk**: Premium comparison shifts system identity to "product comparison" (NOT proposal-centered).

**Mitigation**:
- Enforce STEP 29 constitutional principle (proposal-centered)
- Premium = proposal field (not calculated)
- Policy = explanation evidence (not comparison basis)

**Severity**: **High** (constitutional violation if not enforced)

---

**Risk**: Users expect premium calculator (out of scope).

**Mitigation**:
- UX messaging: "가입설계서 기반 비교" (not "보험료 계산")
- No premium input fields (query coverage only)
- Document limitations in UI

**Severity**: **Medium** (UX clarity needed)

---

## 7. Contract Compatibility Matrix

### 7.1. Backend Contract Elements (STEP 14-26)

| Element | Change Required? | Impact | Approval Needed? |
|---------|------------------|--------|------------------|
| `comparison_result` enum | ❌ No | None | N/A |
| `next_action` enum | ❌ No | None | N/A |
| `ux_message_code` registry | ❌ No | None | N/A |
| `CoverageDetail` schema | ✅ Yes (add `premium` field) | Additive (non-breaking) | ✅ CHANGELOG (STEP 25) |
| Golden snapshots | ✅ Yes (add `premium` to all 5) | Schema consistency | ✅ CHANGELOG (STEP 25) |
| Contract CI gates | ❌ No | None | N/A |

**Verdict**: **Compatible** with additive schema change.

---

### 7.2. UI Contract Elements (STEP 27)

| Element | Change Required? | Impact | Approval Needed? |
|---------|------------------|--------|------------------|
| UI_STATE_MAP | ❌ No | None | N/A |
| State key format | ❌ No | None | N/A |
| View components | ✅ Yes (add PriceRankingView, PriceComparisonView) | Additive | ❌ No (Frontend only) |
| UI aggregation states | ✅ Yes (add PRICE_* states) | Additive | ❌ No (UI layer only) |

**Verdict**: **Compatible** - all Frontend extensions.

---

## 8. Implementation Strategy

### 8.1. Phase 1: Backend Schema Extension (Minimal Change)

**Tasks**:
1. Add `premium` field to `CoverageDetail` schema (nullable)
2. Update golden snapshots (add `premium` to scenarios A/D)
3. Write CHANGELOG entry (STEP 25 governance)
4. Pass contract CI gates

**DoD**:
- ✅ Schema change committed
- ✅ Golden snapshots updated
- ✅ CHANGELOG approved
- ✅ CI gates passing

---

### 8.2. Phase 2: Frontend UI Aggregation States (No Backend Change)

**Tasks**:
1. Implement `resolvePriceAggregationState()` logic
2. Create `PRICE_AGGREGATION_STATE_MAP`
3. Write unit tests (Frontend only)

**DoD**:
- ✅ State resolution logic working
- ✅ Tests passing
- ✅ No Backend API calls

---

### 8.3. Phase 3: Frontend View Components (No Backend Change)

**Tasks**:
1. Implement `PriceRankingView` component
2. Extend `ComparableView` → `PriceComparisonView`
3. Update `ViewRenderer` to route premium states

**DoD**:
- ✅ Components rendering in DEV_MOCK_MODE
- ✅ All scenarios testable (A/B/C/D/E + premium)
- ✅ No Backend changes

---

### 8.4. Phase 4: Frontend Integration (No Backend Change)

**Tasks**:
1. Implement multi-insurer API call pattern
2. Client-side ranking logic
3. Premium explanation extraction from `policy_evidence`

**DoD**:
- ✅ Premium ranking working with real API
- ✅ Top-N display functional
- ✅ Explanation logic tested

---

## 9. Constitutional Compliance Checklist

### 9.1. Proposal-Centered Architecture (CLAUDE.md)

- ✅ Comparison target = Proposals (not policies)
- ✅ Premium = Proposal field (not calculated)
- ✅ Policy = Explanation evidence (not source)
- ✅ Universe Lock maintained (STEP 6-C)

---

### 9.2. Backend Contract Immutability (STEP 14-26)

- ✅ No new `comparison_result` values
- ✅ No new `next_action` values
- ✅ No new `ux_message_code` values
- ✅ Only additive schema change (`premium` field nullable)

---

### 9.3. Data Absence ≠ Error (CLAUDE.md)

- ✅ Missing premium → `PRICE_DATA_PARTIAL` (valid state)
- ✅ Single proposal → `PRICE_RANKING_UNAVAILABLE` (valid state)
- ✅ No policy evidence → "약관 확인 필요" (not error)

---

### 9.4. Governance (STEP 25)

- ✅ Schema change requires CHANGELOG
- ✅ Golden snapshot updates require CHANGELOG
- ✅ UI aggregation states do NOT require CHANGELOG (Frontend only)

---

## 10. Open Questions

### Q1: Should premium field be mandatory or optional?

**Recommendation**: **Optional** (`Optional[int]`).
- Justification: inca-rag seed data may have missing premiums.
- Risk mitigation: Frontend handles null gracefully.

---

### Q2: Should Backend provide ranking endpoint?

**Recommendation**: **No** (for now).
- Justification: Frontend aggregation works for N < 10 insurers.
- Future: If performance issue, add `/compare/ranking` with new golden snapshot.

---

### Q3: Should "Why different?" explanation be Backend logic?

**Recommendation**: **No**.
- Justification: `policy_evidence` already provides data.
- Frontend can format explanation message (UX freedom).

---

### Q4: What if user queries coverage not in any proposal?

**Answer**: Existing Backend Contract handles this.
- State: `out_of_universe:REQUEST_MORE_INFO:COVERAGE_NOT_IN_UNIVERSE`
- UI: OutOfUniverseView (STEP 28)
- No change needed.

---

## 11. Conclusion

### 11.1. Gap Summary

| Gap | Severity | Solution | Backend Change? |
|-----|----------|----------|-----------------|
| Premium field in response | Medium | Add nullable field to schema | ✅ Yes (additive) |
| Multiple proposal comparison | Low | Frontend aggregation | ❌ No |
| Premium ranking logic | Low | Frontend sorting | ❌ No |
| Premium explanation | None | Use existing `policy_evidence` | ❌ No |

---

### 11.2. Contract Compatibility Verdict

**✅ COMPATIBLE** with the following constraints:

1. **Minimal Backend Change**: Add `premium` field to schema (nullable, additive).
2. **Frontend Extension**: All ranking, sorting, explanation logic in Frontend.
3. **Governance Approval**: CHANGELOG required for schema change (STEP 25).
4. **Constitutional Compliance**: Proposal-centered architecture maintained.

---

### 11.3. Risks

**Low Risk**:
- ✅ Schema change is additive (non-breaking)
- ✅ Frontend aggregation is isolated
- ✅ Existing contract CI gates prevent violations

**Medium Risk**:
- ⚠ Premium UX may tempt Backend "optimization" (resist via governance)
- ⚠ Users may expect calculator (UX clarity needed)

**High Risk**:
- ⚠ System identity shift to "product comparison" (enforce constitutional principle)

---

### 11.4. Recommendation

**Proceed with STEP 29 implementation** under the following conditions:

1. **Backend Schema Extension**:
   - Add `premium: Optional[int]` to `CoverageDetail`
   - Update golden snapshots (scenarios A/D)
   - Get CHANGELOG approval

2. **Frontend Extension Only**:
   - All ranking, sorting, explanation in Frontend
   - No new Backend Contract states
   - Use UI aggregation states (STEP 29 PRICE_STATE_EXTENSION.md)

3. **Governance Enforcement**:
   - Document Frontend extension boundary
   - Resist Backend "optimization" requests
   - Maintain proposal-centered principle

4. **Risk Mitigation**:
   - UX messaging: "가입설계서 비교" (not "보험료 계산")
   - Data absence handling (not errors)
   - inca-rag dependency documented

**Next Steps** (if approved):
- Backend: Add `premium` field + golden snapshot update (STEP 29-α)
- Frontend: Implement PriceRankingView + PriceComparisonView (STEP 29-β)
- E2E: Test premium ranking with real API (STEP 29-γ)

---

**END OF GAP ANALYSIS**
