# UI Contract SSOT (STEP 27)

> **Purpose**: Define UI states and behaviors based on Backend Contract (STEP 14-26)
>
> **Constitutional Principle**: Backend Contract is immutable. UI adapts to Contract, not vice versa.
>
> **Version**: 1.0.0
> **Date**: 2025-12-25

---

## 1. UI State Model

### State Identification

Every Compare API response defines a unique UI state through a **3-tuple**:

```
(comparison_result, next_action, ux_message_code)
```

**Rules**:
- State key is deterministic (no runtime inference)
- All 3 fields are **Backend Contract** (STEP 24/26 registries)
- UI must handle all states emitted by Backend
- Unknown states → Fallback UI (not error)

**Example State Keys**:
```
comparable:COMPARE:COVERAGE_MATCH_COMPARABLE
unmapped:REQUEST_MORE_INFO:COVERAGE_UNMAPPED
policy_required:VERIFY_POLICY:DISEASE_SCOPE_VERIFICATION_REQUIRED
out_of_universe:REQUEST_MORE_INFO:COVERAGE_NOT_IN_UNIVERSE
```

---

## 2. UI State Definitions (Golden Snapshot Coverage)

### 2.1 State: `comparable:COMPARE:COVERAGE_MATCH_COMPARABLE`

**Scenarios**: A, D

**UX Purpose**: Show successful comparison between two insurers with same coverage type.

**User Understanding**:
- Both insurers offer the same coverage
- Comparison is valid and ready
- User can proceed to detailed comparison view

**Screen Layout**:
- **Title**: "비교 가능" (Comparison Available)
- **Description**: "두 보험사 모두 {coverage_name} 담보를 보유하고 있습니다"
- **Primary CTA**: "상세 비교하기" (View Detailed Comparison)
  - Action: Navigate to comparison view (coverage A vs B)
- **Secondary CTA**: "다른 담보 검색" (Search Other Coverage)
  - Action: Return to search input

**Display Data**:
- Coverage A: `coverage_name_raw`, `amount_value`, `insurer`
- Coverage B: `coverage_name_raw`, `amount_value`, `insurer`
- Canonical code: `canonical_coverage_code`
- Mapping status: `MAPPED` (green badge)

**Additional Input Required**: None

**Error Handling**: None (success state)

---

### 2.2 State: `unmapped:REQUEST_MORE_INFO:COVERAGE_UNMAPPED`

**Scenario**: B

**UX Purpose**: Inform user that coverage name is not recognized in system mapping.

**User Understanding**:
- Query coverage name exists in proposal but not in canonical mapping
- Cannot proceed to comparison (no canonical code)
- User should provide more specific coverage name

**Screen Layout**:
- **Title**: "담보 매핑 실패" (Coverage Not Mapped)
- **Description**: "{coverage_name}은(는) 아직 신정원 코드로 매핑되지 않았습니다"
- **Primary CTA**: "다시 검색" (Search Again)
  - Action: Return to search input
- **Secondary CTA**: "관리자 문의" (Contact Support)
  - Action: Open support contact form

**Display Data**:
- Raw coverage name: `coverage_name_raw`
- Insurer: `insurer`
- Mapping status: `UNMAPPED` (yellow badge)
- Suggestion: "더 구체적인 담보명을 입력해주세요"

**Additional Input Required**: Yes (refined coverage name)

**Error Handling**:
- Not a system error (expected state)
- Show "데이터 준비 중" label if applicable

---

### 2.3 State: `policy_required:VERIFY_POLICY:DISEASE_SCOPE_VERIFICATION_REQUIRED`

**Scenario**: C

**UX Purpose**: Inform user that coverage exists but requires policy document verification (disease scope).

**User Understanding**:
- Coverage is mapped and found
- Disease scope definition exists but needs verification
- Cannot fully compare without policy evidence

**Screen Layout**:
- **Title**: "약관 확인 필요" (Policy Verification Required)
- **Description**: "{coverage_name}의 질병 범위(disease_scope)를 확인하려면 약관 검증이 필요합니다"
- **Primary CTA**: "약관 보기" (View Policy)
  - Action: Show policy_evidence (disease code group details)
- **Secondary CTA**: "비교 진행" (Continue Comparison)
  - Action: Navigate to comparison view with warning badge

**Display Data**:
- Coverage: `coverage_name_raw`, `amount_value`
- Disease scope (raw): `disease_scope_raw`
- Policy evidence: `policy_evidence_a.group_name`, `member_count`
- Source confidence: `policy_required` (orange badge)

**Additional Input Required**: None (policy view optional)

**Error Handling**: None (expected state)

---

### 2.4 State: `out_of_universe:REQUEST_MORE_INFO:COVERAGE_NOT_IN_UNIVERSE`

**Scenario**: E

**UX Purpose**: Inform user that query coverage does not exist in proposal universe.

**User Understanding**:
- Coverage name is not in selected insurer's proposal
- Universe Lock principle enforced (STEP 6-C)
- User should verify insurer or coverage name

**Screen Layout**:
- **Title**: "담보 없음" (Coverage Not Found)
- **Description**: "{query}은(는) {insurer} 가입설계서에 존재하지 않습니다"
- **Primary CTA**: "다시 검색" (Search Again)
  - Action: Return to search input
- **Secondary CTA**: "다른 보험사 선택" (Select Other Insurer)
  - Action: Return to insurer selection

**Display Data**:
- Query: `query`
- Insurer: `insurer_a`
- Universe lock enforced: `true` (blue badge)
- Suggestion: "보험사 또는 담보명을 확인해주세요"

**Additional Input Required**: Yes (new query or insurer)

**Error Handling**:
- Not a system error (expected state)
- Show "Universe 외부" label

---

## 3. Data Incompleteness Handling Principles

### 3.1 Missing Insurer Data

**Situation**: User queries coverage for insurer without proposal data.

**UI Response**:
- State: `out_of_universe:REQUEST_MORE_INFO:COVERAGE_NOT_IN_UNIVERSE`
- Message: "{insurer} 가입설계서 데이터가 아직 준비되지 않았습니다"
- CTA: "준비된 보험사 보기" (View Available Insurers)

**NOT an Error**: Data preparation is ongoing (inca-rag dependency)

---

### 3.2 Missing Policy Document

**Situation**: `disease_scope_norm` exists but policy_evidence is null.

**UI Response**:
- State: `policy_required:VERIFY_POLICY:DISEASE_SCOPE_VERIFICATION_REQUIRED`
- Message: "약관 데이터를 준비 중입니다"
- Primary CTA: "알림 받기" (Notify When Ready)
- Secondary CTA: "비교 진행" (Continue Without Policy)

**NOT an Error**: Policy ingestion is ongoing

---

### 3.3 Non-Comparable Coverage (Different Canonical Codes)

**Situation**: Backend returns `non_comparable:REQUEST_MORE_INFO:COVERAGE_TYPE_MISMATCH`

**UI Response**:
- Title: "비교 불가" (Not Comparable)
- Message: "서로 다른 담보 유형입니다: {code_a} vs {code_b}"
- Primary CTA: "다시 검색"
- Display both coverages with "비교 불가" badge

**NOT an Error**: Intentional user query mismatch

---

## 4. Customer Requirements Mapping

### 4.1 Fulfilled Requirements

Based on customer request analysis (inca-rag-final context):

| Requirement | UI State | Status |
|-------------|----------|--------|
| 담보 비교 (Coverage Comparison) | `comparable:COMPARE:*` | ✅ Fulfilled |
| 매핑 실패 안내 (Unmapped Coverage) | `unmapped:REQUEST_MORE_INFO:*` | ✅ Fulfilled |
| 약관 확인 필요 안내 (Policy Required) | `policy_required:VERIFY_POLICY:*` | ✅ Fulfilled |
| Universe 외부 처리 (Out of Universe) | `out_of_universe:REQUEST_MORE_INFO:*` | ✅ Fulfilled |
| 금액 비교 (Amount Comparison) | `comparable:COMPARE:*` + display data | ✅ Fulfilled |

---

### 4.2 Partially Fulfilled Requirements

| Requirement | UI State | Gap | Decision Required |
|-------------|----------|-----|-------------------|
| 질병 범위 상세 비교 (Disease Scope Detail) | `policy_required:VERIFY_POLICY:*` | Policy evidence UI needed | Frontend implementation |
| 다중 보험사 비교 (Multi-insurer Comparison) | N/A | Backend supports 2 insurers only | Product decision |
| 약관 원문 보기 (Policy Document Viewer) | `policy_required:VERIFY_POLICY:*` | Document viewer not implemented | Future enhancement |

---

### 4.3 Out of Scope (Data Dependency)

| Requirement | Reason | Dependency |
|-------------|--------|------------|
| 모든 보험사 커버 (All Insurers Coverage) | inca-rag seed data limited | inca-rag ingestion pipeline |
| 전체 담보 목록 (Full Coverage List) | Proposal universe incomplete | Proposal extraction (inca-rag) |
| 약관 자동 분석 (Auto Policy Analysis) | Policy ingestion not complete | inca-rag policy pipeline |

---

## 5. UI State Completeness Matrix

### Required States (DoD Minimum)

| State Key | Scenario | UI Defined | Frontend Implemented |
|-----------|----------|------------|---------------------|
| `comparable:COMPARE:COVERAGE_MATCH_COMPARABLE` | A, D | ✅ | 🔲 (STEP 27) |
| `unmapped:REQUEST_MORE_INFO:COVERAGE_UNMAPPED` | B | ✅ | 🔲 (STEP 27) |
| `policy_required:VERIFY_POLICY:DISEASE_SCOPE_VERIFICATION_REQUIRED` | C | ✅ | 🔲 (STEP 27) |
| `out_of_universe:REQUEST_MORE_INFO:COVERAGE_NOT_IN_UNIVERSE` | E | ✅ | 🔲 (STEP 27) |

---

### Extended States (Future Coverage)

| State Key | Use Case | Priority |
|-----------|----------|----------|
| `comparable_with_gaps:VERIFY_POLICY:COVERAGE_COMPARABLE_WITH_GAPS` | Partial data comparison | Medium |
| `non_comparable:REQUEST_MORE_INFO:COVERAGE_TYPE_MISMATCH` | Different canonical codes | Low |
| `comparable:COMPARE:COVERAGE_FOUND_SINGLE_INSURER` | Single insurer query | Low |

---

## 6. Fallback Strategy

### Unknown State Handling

**Trigger**: Backend returns state not in UI_STATE_MAP

**Response**:
```typescript
{
  view: "GenericMessage",
  title: "처리 중",
  message: "요청하신 담보 정보를 확인하고 있습니다",
  primaryCta: "다시 시도",
  severity: "warning"
}
```

**Logging**: Send unknown state to monitoring (contract drift detection)

**NOT Allowed**:
- ❌ Treat as error (breaks UX)
- ❌ Guess UI behavior (breaks contract)
- ❌ Silently ignore (breaks observability)

---

## 7. Contract Stability Guarantees

### What is Contract (Immutable)

- ✅ `comparison_result` codes (STEP 24 registry)
- ✅ `next_action` codes (STEP 24 registry)
- ✅ `ux_message_code` codes (STEP 26 registry)
- ✅ State key format: `{result}:{action}:{ux_code}`
- ✅ Response schema: `ProposalCompareResponse` (FastAPI)

### What is NOT Contract (Mutable)

- ❌ UI titles/messages (i18n free)
- ❌ CTA button text (UX iteration)
- ❌ View component names (frontend refactoring)
- ❌ Color/icon/badge styles (design system)

---

## 8. Assumptions & Constraints (STEP 27)

### Assumptions

1. **Frontend Stack**: TypeScript-based (React/Next.js assumed)
2. **API Call Pattern**: REST (POST `/compare`)
3. **State Management**: Client-side (no server-side rendering for state)
4. **I18n**: Korean primary, English optional

### Constraints

1. **No Backend Contract Changes**: STEP 14-26 frozen
2. **No Golden Snapshot Updates**: CHANGELOG required for changes
3. **No Registry Bypass**: All states must map to registry codes
4. **No inca-rag Dependency**: UI works with current seed data only

---

## 9. Frontend Development Checklist

### Phase 1: UI State Map Implementation (STEP 27)

- [ ] Create `apps/web/src/contracts/uiStateMap.ts`
- [ ] Map all 4 required states (A/B/C/E)
- [ ] Implement fallback state
- [ ] Write UI contract drift tests

### Phase 2: Component Development (Future)

- [ ] `CompareResult` view (state: comparable)
- [ ] `GenericMessage` view (state: unmapped, out_of_universe)
- [ ] `PolicyVerificationRequired` view (state: policy_required)
- [ ] `UnknownState` fallback view

### Phase 3: Integration (Future)

- [ ] Connect to Backend API (`POST /compare`)
- [ ] State resolution logic
- [ ] Error boundary for contract violations
- [ ] Telemetry for unknown states

---

## 10. Governance

### UI Contract Changes

**When to Update This Document**:
- New state added to Backend Contract (registry change)
- New UI behavior pattern discovered
- Customer requirement clarification

**Approval Process**:
- Same as Backend Contract (CHANGELOG required)
- Frontend/UX team review

**Versioning**:
- Follow semver (1.0.0 → 1.1.0 for additions)

---

## Appendix A: State Transition Diagram

```
[User Input: Coverage Query]
        ↓
[Backend: Resolve Query + Universe Lookup]
        ↓
    ┌───────────────────────────────┐
    │  comparison_result            │
    │  next_action                  │
    │  ux_message_code              │
    └───────────────────────────────┘
        ↓
[Frontend: State Key Resolution]
        ↓
    ┌───────────────────────────────┐
    │  UI_STATE_MAP[stateKey]      │
    └───────────────────────────────┘
        ↓
[Render: View Component + CTAs]
```

---

## Appendix B: Example API Response → UI State

### Example 1: Scenario A

**API Response**:
```json
{
  "comparison_result": "comparable",
  "next_action": "COMPARE",
  "ux_message_code": "COVERAGE_MATCH_COMPARABLE",
  "coverage_a": { "amount_value": 50000000 },
  "coverage_b": { "amount_value": 30000000 }
}
```

**State Key**: `comparable:COMPARE:COVERAGE_MATCH_COMPARABLE`

**UI Rendering**:
- View: `CompareResult`
- Title: "비교 가능"
- Primary CTA: "상세 비교하기"
- Display: Amount values (5000만원 vs 3000만원)

---

### Example 2: Scenario E

**API Response**:
```json
{
  "comparison_result": "out_of_universe",
  "next_action": "REQUEST_MORE_INFO",
  "ux_message_code": "COVERAGE_NOT_IN_UNIVERSE",
  "coverage_a": null,
  "coverage_b": null,
  "message": "'다빈치 수술비' coverage not found in SAMSUNG proposal universe"
}
```

**State Key**: `out_of_universe:REQUEST_MORE_INFO:COVERAGE_NOT_IN_UNIVERSE`

**UI Rendering**:
- View: `GenericMessage`
- Title: "담보 없음"
- Message: "다빈치 수술비은(는) SAMSUNG 가입설계서에 존재하지 않습니다"
- Primary CTA: "다시 검색"
- Badge: "Universe 외부"

---

**END OF UI CONTRACT SSOT**
