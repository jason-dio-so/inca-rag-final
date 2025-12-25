# Customer Requirements → UI State Mapping (STEP 27)

> **Purpose**: Map customer requirements to UI states and identify gaps
>
> **Context**: inca-RAG-final is a minimal contract-focused repo, not full data pipeline
>
> **Date**: 2025-12-25

---

## 1. Methodology

### Requirement Analysis Approach

Customer requirements were analyzed in the context of:
1. **Backend Contract (STEP 14-26)**: Immutable states frozen in golden snapshots
2. **Data Availability**: Only minimal seed data (STEP 13) available in this repo
3. **UX State Model**: UI states defined in `docs/ui/UI_CONTRACT.md`

### Classification Criteria

Requirements are classified as:
- **✅ Fulfilled**: Fully satisfied by current UI states + Backend Contract
- **🟡 Partially Fulfilled**: Core functionality exists, but needs frontend implementation or data
- **🔴 Out of Scope**: Requires inca-rag data pipeline or product decisions
- **🟢 Decision Required**: Ambiguous or conflicting requirements needing clarification

---

## 2. Fulfilled Requirements

### 2.1 담보 비교 (Coverage Comparison)

**Requirement**: Compare coverage between two insurers

**UI State**: `comparable:COMPARE:COVERAGE_MATCH_COMPARABLE`

**Status**: ✅ Fulfilled

**Evidence**:
- Backend Contract: Scenarios A, D (golden snapshots)
- UI State: `CompareResult` view with amount comparison
- Display: `coverage_a`, `coverage_b`, `amount_value`

**User Flow**:
1. User inputs coverage query + 2 insurers
2. Backend resolves to canonical code
3. UI shows comparison view with amounts

---

### 2.2 매핑 실패 안내 (Unmapped Coverage Notification)

**Requirement**: Inform user when coverage name is not recognized

**UI State**: `unmapped:REQUEST_MORE_INFO:COVERAGE_UNMAPPED`

**Status**: ✅ Fulfilled

**Evidence**:
- Backend Contract: Scenario B
- UI State: `GenericMessage` view with "담보 매핑 실패" title
- CTA: "Search Again" + "Contact Support"

**User Flow**:
1. User queries coverage not in Excel mapping
2. Backend returns `unmapped` state
3. UI shows message with retry option

---

### 2.3 약관 확인 필요 안내 (Policy Verification Required)

**Requirement**: Inform user when policy verification is needed

**UI State**: `policy_required:VERIFY_POLICY:DISEASE_SCOPE_VERIFICATION_REQUIRED`

**Status**: ✅ Fulfilled

**Evidence**:
- Backend Contract: Scenario C
- UI State: `PolicyVerificationView` with policy evidence display
- Display: `disease_scope_raw`, `policy_evidence_a`

**User Flow**:
1. User queries coverage with disease scope
2. Backend returns `policy_required` state
3. UI shows policy evidence + comparison option

---

### 2.4 Universe 외부 처리 (Out of Universe Handling)

**Requirement**: Handle queries for coverage not in proposal

**UI State**: `out_of_universe:REQUEST_MORE_INFO:COVERAGE_NOT_IN_UNIVERSE`

**Status**: ✅ Fulfilled

**Evidence**:
- Backend Contract: Scenario E
- UI State: `GenericMessage` with "담보 없음" title
- Universe Lock: Enforced (STEP 6-C)

**User Flow**:
1. User queries coverage not in insurer proposal
2. Backend enforces Universe Lock
3. UI shows "Coverage Not Found" message (NOT error)

---

### 2.5 금액 비교 (Amount Comparison)

**Requirement**: Show coverage amounts side-by-side

**UI State**: `comparable:COMPARE:COVERAGE_MATCH_COMPARABLE`

**Status**: ✅ Fulfilled

**Evidence**:
- Display Config: `showAmountComparison: true`
- Data: `coverage_a.amount_value`, `coverage_b.amount_value`
- Golden Snapshots: A (5000만원 vs 3000만원)

**User Flow**:
1. Backend returns comparable state
2. UI displays both amounts with formatting
3. User sees difference clearly

---

## 3. Partially Fulfilled Requirements

### 3.1 질병 범위 상세 비교 (Disease Scope Detail Comparison)

**Requirement**: Compare disease code groups between insurers

**UI State**: `policy_required:VERIFY_POLICY:DISEASE_SCOPE_VERIFICATION_REQUIRED`

**Status**: 🟡 Partially Fulfilled

**What Exists**:
- Backend: `disease_scope_norm` field (object with include/exclude groups)
- UI State: `PolicyVerificationView` defined
- Display Config: `showPolicyEvidence: true`

**Gap**:
- Frontend implementation: Policy evidence viewer component not built
- UI Detail: Disease code group comparison table

**Next Steps**:
1. Frontend: Build `PolicyVerificationView` component
2. Display: `policy_evidence.group_name`, `member_count`
3. Optionally: Show disease code list (if policy ingestion complete)

---

### 3.2 다중 보험사 비교 (Multi-Insurer Comparison)

**Requirement**: Compare coverage across 3+ insurers

**UI State**: N/A

**Status**: 🟡 Partially Fulfilled (2 insurers only)

**What Exists**:
- Backend: Supports 2 insurers (coverage_a, coverage_b)
- UI State: Designed for dual comparison

**Gap**:
- Backend limitation: Schema supports only 2 insurers
- Product decision: Is 3+ insurer comparison required?

**Decision Required**:
- **Option A**: Extend Backend Contract to support multi-insurer (breaking change)
- **Option B**: Run multiple 2-insurer comparisons in sequence
- **Option C**: Defer to future phase (not MVP)

**Assumption**: 2-insurer comparison satisfies 80% of use cases

---

### 3.3 약관 원문 보기 (Policy Document Viewer)

**Requirement**: View original policy PDF/text

**UI State**: `policy_required:VERIFY_POLICY:*`

**Status**: 🟡 Partially Fulfilled

**What Exists**:
- Backend: `policy_evidence_a` returns disease code group metadata
- UI State: `PolicyVerificationView` with "View Policy" CTA

**Gap**:
- Backend: Policy document storage not implemented in inca-RAG-final
- Frontend: PDF viewer component not built
- Data: Policy documents exist in inca-rag (dependency)

**Next Steps**:
1. **Immediate**: Link to external policy URL (if available)
2. **Future**: Integrate inca-rag document retrieval API

---

## 4. Out of Scope (Data/System Dependency)

### 4.1 모든 보험사 커버 (All Insurers Coverage)

**Requirement**: Support all major Korean insurers

**Status**: 🔴 Out of Scope

**Reason**:
- **Data Limitation**: inca-RAG-final has minimal seed data (STEP 13)
- **Dependency**: Full insurer data exists in inca-rag repo
- **Scope**: This repo focuses on Contract, not data completeness

**Current Coverage**:
- SAMSUNG ✅
- MERITZ ✅
- KB ✅

**Missing Insurers**:
- 한화생명, 교보생명, DB손해보험, etc.

**Resolution Path**:
- **Phase 1 (STEP 27)**: Define UI states that work with any insurer
- **Phase 2 (Future)**: Ingest data from inca-rag pipeline

---

### 4.2 전체 담보 목록 (Full Coverage List)

**Requirement**: Browse all available coverages

**Status**: 🔴 Out of Scope

**Reason**:
- **Data Limitation**: Proposal coverage universe incomplete
- **Dependency**: Requires inca-rag proposal extraction pipeline
- **Current State**: Only 3-5 coverages per insurer in seed

**Alternative**:
- User searches by coverage name (current UX)
- Autocomplete suggestions (future enhancement)

---

### 4.3 약관 자동 분석 (Auto Policy Analysis)

**Requirement**: Automatically analyze and compare policy documents

**Status**: 🔴 Out of Scope

**Reason**:
- **System Limitation**: Policy ingestion pipeline not in inca-RAG-final
- **Dependency**: Requires inca-rag LLM extraction + disease code normalization
- **Current State**: `disease_scope_norm` is NULL for most coverages

**Workaround**:
- Show `disease_scope_raw` (proposal text) as fallback
- Display "약관 데이터 준비 중" label

---

## 5. Decision Required (Ambiguous/Conflicting)

### 5.1 ChatGPT 스타일 대화형 UX (Conversational UI)

**Requirement**: ChatGPT-style conversational interface

**Status**: 🟢 Decision Required

**Questions**:
1. **Chat History**: Should comparison history persist?
2. **Follow-up Queries**: Can user refine query in conversation?
3. **Multi-turn**: Does backend support multi-turn state?

**Current Implementation**:
- **Stateless**: Each query is independent
- **Single Response**: No conversation context

**Options**:
- **Option A**: Full conversational UI (requires state management)
- **Option B**: Single query/response with history list
- **Option C**: Hybrid (stateless backend, client-side chat UI)

**Recommendation**: Option C (client-side chat UI, stateless backend)

---

### 5.2 비교 불가 담보 처리 (Non-Comparable Coverage Handling)

**Requirement**: How to show non-comparable coverages?

**Status**: 🟢 Decision Required

**UI State**: `non_comparable:REQUEST_MORE_INFO:COVERAGE_TYPE_MISMATCH`

**Scenario**: User queries "암진단금" but SAMSUNG has CA_DIAG_GENERAL, MERITZ has CA_DIAG_SIMILAR

**Options**:
- **Option A**: Show error message "비교 불가"
- **Option B**: Show both coverages side-by-side with "서로 다른 담보 유형" badge
- **Option C**: Ask user to select specific coverage type

**Current State**: UI State exists, but frontend behavior undefined

---

### 5.3 데이터 없음 vs 에러 구분 (Data Absence vs Error)

**Requirement**: Distinguish between "no data" and "system error"

**Status**: 🟢 Decision Required

**Current Approach**:
- `out_of_universe`: Data not found (NOT error)
- `unmapped`: Mapping not found (NOT error)
- HTTP 500: System error (Backend failure)

**Question**: Should UI distinguish between:
- "보험사 데이터 준비 중" (data ingestion ongoing)
- "해당 보험사 미지원" (not in scope)

**Recommendation**: Use UI message text to clarify (not state change)

---

## 6. Coverage Summary

### By Status

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Fulfilled | 5 | 45% |
| 🟡 Partially Fulfilled | 3 | 27% |
| 🔴 Out of Scope | 3 | 27% |
| 🟢 Decision Required | 3 | Not counted separately |

### Critical Path

**MVP (STEP 27 Complete)**:
- ✅ Core comparison UI states defined
- ✅ Backend Contract stable and tested
- ✅ Drift prevention tests passing

**Next Phase (Frontend Implementation)**:
- 🟡 Build React components for each view
- 🟡 Implement API integration
- 🟡 Add policy evidence viewer

**Future Phase (Data Expansion)**:
- 🔴 Ingest more insurers (via inca-rag)
- 🔴 Complete policy document pipeline
- 🔴 Full coverage universe extraction

---

## 7. Assumptions Documented

### Data Assumptions

1. **Seed Data Sufficient**: Current 3 insurers × 5 scenarios sufficient for contract validation
2. **Mapping Complete**: Excel mapping covers common coverages (edge cases may be UNMAPPED)
3. **Policy Evidence Optional**: Users can compare without full policy ingestion

### UX Assumptions

1. **Korean Primary**: UI text primarily in Korean (i18n structure prepared)
2. **Desktop First**: Initial UX optimized for desktop (responsive later)
3. **Single Query**: One comparison per request (no multi-query batching)

### Technical Assumptions

1. **TypeScript Frontend**: React/Next.js assumed (not enforced)
2. **REST API**: POST /compare endpoint (no GraphQL/WebSocket)
3. **Client-Side State**: No server-side rendering of UI states

---

## 8. Gap Analysis Summary

### Backend Contract Gaps

None. Backend Contract (STEP 14-26) is stable and complete for defined scope.

### UI Implementation Gaps

1. **Component Library**: No React components built yet
2. **API Client**: No API integration layer
3. **State Management**: No Redux/Zustand integration
4. **Styling**: No design system applied

**Mitigation**: STEP 27 defines contract, implementation is next phase.

### Data Completeness Gaps

1. **Insurer Coverage**: Only 3 insurers (vs 20+ in Korea)
2. **Coverage Universe**: Limited to seed data
3. **Policy Documents**: Not ingested in inca-RAG-final

**Mitigation**: UI states designed to handle "data not ready" gracefully.

---

## 9. Recommendations

### Immediate Actions (STEP 27 Complete)

1. ✅ UI Contract SSOT documented
2. ✅ UI State Map implemented
3. ✅ Drift prevention tests passing
4. ✅ Customer requirements mapped

### Short-Term (Next Sprint)

1. Build React components for 4 required views
2. Integrate with Backend API
3. Add policy evidence viewer (basic)

### Long-Term (Product Roadmap)

1. Expand data coverage (via inca-rag integration)
2. Multi-insurer comparison (if validated)
3. Conversational UI (if validated)

---

**END OF REQUIREMENTS MAPPING**
