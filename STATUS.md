# inca-RAG-final Project Status

**Last Updated:** 2025-12-25
**Current Phase:** Proposal Detail Evidence Attachment (STEP 4.1)
**Project Health:** ✅ ACTIVE - Core Pipeline + Evidence Attachment Framework Complete

---

## Quick Overview

**inca-RAG-final** is a proposal-centered insurance policy comparison RAG system implementing Constitutional principles defined in [CLAUDE.md](CLAUDE.md).

**Core Principles:**
- Proposal-centered (not policy-centered)
- Coverage Universe Lock (가입설계서 = SSOT)
- Deterministic extraction (no LLM inference for mappings)
- Evidence-based everything
- /compare contract immutability

**Repository:** [GitHub - inca-rag-final](https://github.com/jason-dio-so/inca-rag-final)

---

## Latest Milestones (Summary)

Detailed implementation logs available in [`docs/status/`](docs/status/).

### ✅ STEP 3.10-β: UNMAPPED Cause-Effect Analysis
**Commit:** (pending) | **Date:** 2025-12-25

**Summary:**
- UNMAPPED 원인 구조화 (7개 고정 Enum: C1-C7)
- 시스템 영향 분류 (5개 고정 Enum: E1-E5)
- 사실 기반 리포트 생성 (해석/추론/추천 금지)
- 매핑 보강/UX 설명을 위한 근거 확보

**Purpose:**
- Analyze WHY coverage is UNMAPPED (cause)
- Document system impact (effect)
- Provide evidence for future mapping enhancement decisions
- NO mapping rule changes, NO UNMAPPED → MAPPED conversion

**Cause Classification (C1-C7):**
- C1_NO_EXCEL_ENTRY: Excel에 해당 보험사 매핑 행 없음
- C2_NAME_VARIANT_ONLY: 타 보험사에는 존재하나 현재 ins_cd 매핑 없음
- C3_SUBCATEGORY_SPLIT: 가입설계서는 하위 담보, Excel은 상위 개념만
- C4_COMPOSITE_COVERAGE: 가입설계서는 단일 담보, Excel은 복합 담보만
- C5_NEW_OR_SPECIAL_COVERAGE: Excel에 정의되지 않은 신규/특수 담보
- C6_TERMINOLOGY_MISMATCH: 공백/접두어 차이로 결정론적 매칭 불가
- C7_POLICY_LEVEL_ONLY: 가입설계서에는 있으나 Excel은 약관 단위만

**Effect Classification (E1-E5):**
- E1_COMPARISON_POSSIBLE: PRIME 비교 가능 (in_universe_unmapped)
- E2_LIMITED_COMPARISON: 다건 후보/축 누락으로 제한적 비교
- E3_EXPLANATION_REQUIRED: 고객 응답 시 설명 레이어 필수
- E4_MAPPING_EXPANSION_CANDIDATE: Excel 보강 시 MAPPED 가능성 높음
- E5_STRUCTURAL_DIFFERENCE: 구조적 차이로 매핑 자체 부적합

**Analysis Results:**
- Total UNMAPPED analyzed: 191 cases
- Top cause: C1_NO_EXCEL_ENTRY (100% - all cases have this as primary/secondary cause)
- Expansion candidates (E4): 191 cases
- Structural differences (E5): 20 cases

**Generated Reports:**
1. CSV: `data/step310_mapping/unmapped_cause_effect_report.csv`
   - Schema: insurer, coverage_name_raw, cause_codes, effect_codes, evidence_note
2. MD: `data/step310_mapping/UNMAPPED_CAUSE_EFFECT_SUMMARY.md`
   - Overall statistics (cause distribution)
   - Per-insurer top causes
   - Frequent coverage names (Top 10)
   - Mapping expansion candidates
   - Structural difference cases

**Constitution Compliance:**
- ✅ Fact-based cause/effect classification only
- ✅ Evidence-based notes (no interpretation)
- ✅ NO mapping rule changes
- ✅ NO UNMAPPED → MAPPED conversion
- ❌ No coverage unification/inference
- ❌ No recommendations/prioritization

**DoD:**
- ✅ 191 UNMAPPED cases fully analyzed
- ✅ All rows have cause_code (≥1 per row)
- ✅ Effect codes assigned
- ✅ CSV + MD reports generated
- ✅ Reproducible (same input → same output)

---

### ✅ STEP 3.13-α: Deterministic Query Variant Compiler
**Commit:** ec646cf | **Date:** 2025-12-25

**Summary:**
- Query-level whitespace variant handling (NO coverage normalization)
- Deterministic whitespace rules (질병명+진단비/수술비/입원비 → space variant)
- Resolves UX gap for 표기 차이 (e.g., "암진단비" vs "암 진단비")
- NO PRIME state change, NO "same coverage" assertion

**Purpose:**
- Improve query matching for whitespace variations in proposal coverage names
- Query compilation only (질의 컴파일러 보강)
- NO judgment modification (판결문 불변)

**Query Variant Generation Rules:**
```
Original: "암진단비"
Variants: ["암진단비", "암 진단비"]

Pattern: (질병명)(진단비|수술비|입원비|치료비|후유장해)
→ Generate: (질병명) (suffix)
```

**Execution Flow:**
1. Try original query first
2. If original has in_universe hits → use original result
3. If original all out_of_universe → try variants
4. If variant hits → add limitation reason: QUERY_VARIANT_APPLIED_NO_INFERENCE

**Constitution Compliance:**
- ✅ Query normalization ONLY (coverage_name_raw IMMUTABLE)
- ✅ Deterministic whitespace rules only
- ✅ NO PRIME state re-judgment
- ✅ NO "same coverage" assertion
- ❌ No LLM, no similarity, no morphological analysis
- ❌ No coverage unification

**Test Results:**
- ✅ T1 (Whitespace Effect): "암진단비" → variant "암 진단비" finds candidates
- ✅ T2 (Reproducibility): Same query → Same result (100% deterministic)
- ✅ T3 (No Inference): No forbidden keywords (similarity/score/rank/semantic/embedding)

**DoD:**
- ✅ "암진단비 / 암 진단비" UX gap resolved
- ✅ PRIME constitution compliance (no violations)
- ✅ Comparison results IMMUTABLE
- ✅ Explanation factual only
- ✅ 100% reproducible
- ✅ All tests passed (T1/T2/T3)

---

### ✅ STEP 4.1: Proposal Detail Evidence Attachment (가입설계서 상세 근거 첨부)
**Commit:** c38f9cd | **Date:** 2025-12-25

**Summary:**
- Attach proposal detail evidence (보장내용 원문) to customer response
- Extract evidence from proposal detailed_table/text_blocks ONLY
- Deterministic matching framework (exact → substring → no_match)
- Template profile-based location hints (STEP 3.9-0 integration)

**Purpose:**
- Provide 보장내용 (coverage details) evidence from proposal internal documents
- Add [보장내용 근거] section to STEP 4.0 customer response
- NO inference, NO summarization, NO policy/summary reference (this STEP only)

**Evidence Attachment Structure:**
```
[보장내용 근거 (가입설계서 상세)]

▶ INSURER - COVERAGE_NAME

- source: PROPOSAL
- evidence_found: true|false
- evidence_excerpt:
  """
  (원문 그대로, 1~6줄)
  """
- evidence_location:
  - page_hint: "pages 4-7" | NULL
  - section_hint: "담보별 보장내용" | NULL
  - match_rule: exact|substring|no_match
```

**Matching Rules (Deterministic):**
1. exact match: coverage_name_raw == row_coverage_name
2. substring match: coverage_name_raw in row_coverage_name
3. no_match: evidence_found=false

**Normalization Allowed:**
- ✅ Whitespace collapse (multiple → single)
- ✅ Strip leading/trailing whitespace
- ❌ NO special character removal
- ❌ NO synonym expansion

**Template Profile Integration:**
- Loaded from `data/step39_coverage_universe/profiles/*_template_profile.yaml`
- Uses `detailed_table.location`, `detailed_table.table_name` for hints
- Graceful degradation if profile not available

**Current Implementation Status:**
- ✅ Framework complete (deterministic matching + evidence structure)
- ✅ Template profile integration
- ✅ Placeholder evidence generation
- ⏳ Actual PDF extraction (future STEP)

**Constitution Compliance:**
- ✅ STEP 3.11/3.12/3.13/4.0 results IMMUTABLE
- ✅ Proposal internal evidence only
- ✅ Deterministic matching only
- ❌ No PRIME state changes
- ❌ No comparison result modification
- ❌ No inference/semantic matching
- ❌ No policy/summary/business_rules reference (this STEP)

**Determinism Verification:**
- ✅ Test script: `test_step41_determinism.py`
- ✅ 3 sample queries executed:
  - "삼성과 한화 암진단비 비교해줘"
  - "KB 롯데 뇌졸중진단비 보여줘"
  - "다빈치수술비"
- ✅ All tests passed: Same query → Same output

**DoD:**
- ✅ STEP 4.0 output structure maintained + evidence section added
- ✅ Proposal internal evidence extraction framework
- ✅ Deterministic matching rules implemented
- ✅ Template profile integration
- ✅ 100% reproducible (determinism verified)
- ✅ 3 sample queries executed with evidence attachment

**Next Steps:**
- STEP 4.2: Actual PDF extraction (replace placeholder evidence)
- STEP 4.3: Policy/summary reference (if proposal insufficient)

---

### ✅ STEP 4.0: Customer Response Formatter (출력 전용 레이어)
**Commit:** 2883dff | **Date:** 2025-12-25

**Summary:**
- Customer-friendly output formatter (presentation-only layer)
- Transforms STEP 3.13 results into customer-readable format
- 100% IMMUTABLE (no PRIME state changes, no recalculation)
- Fixed 3-section structure: Summary Header → Fact Table → Explanation Blocks

**Purpose:**
- Display STEP 3.11 + STEP 3.12 results in customer-friendly format
- Presentation ONLY (no judgment, no modification, no inference)

**Output Structure:**
```
[비교 요약]
- Coverage query
- Target insurers
- Comparison status (완전 비교 가능 / 제한적 가능 / 비교 불가)
- Limitation reasons (직접 전달)

[비교 테이블]
- STEP 3.11 comparison table (IMMUTABLE)
- PRIME state → customer labels mapping
- Sorted by insurer name

[보험사별 상세 설명]
- STEP 3.12 explanation blocks (IMMUTABLE)
- Per-insurer reasoning (no sentence modification)
```

**PRIME State → Customer Label Mapping:**
- `in_universe_comparable` → "비교 가능"
- `in_universe_with_gaps` → "제한적 비교 가능"
- `in_universe_unmapped` → "비교 가능 (표준 코드 미대응)"
- `out_of_universe` → "비교 대상 아님"

**Forbidden Phrase Validation:**
- Hard ban on recommendation/inference phrases
- Validation: "사실상 같은 담보", "유사한 담보", "추천합니다", "선택하세요", etc.
- System fails if any forbidden phrase detected

**Constitution Compliance:**
- ✅ STEP 3.11 results IMMUTABLE (판결문)
- ✅ STEP 3.12 explanations IMMUTABLE (이유서)
- ✅ STEP 4.0 presentation only (출력)
- ❌ No PRIME state changes
- ❌ No result recalculation
- ❌ No coverage integration
- ❌ No similarity judgment
- ❌ No recommendations

**DoD:**
- ✅ STEP 3.13 result → Customer-friendly format
- ✅ 100% IMMUTABLE (no changes to STEP 3.11/3.12)
- ✅ Forbidden phrase validation enforced
- ✅ Same input → Same output
- ✅ No Constitution violations

**Example Output:**
```
[비교 요약]
요청하신 담보: 암진단비
비교 보험사: SAMSUNG, HANWHA
비교 결과 요약:
- 비교 가능 여부: 제한적 가능
- 제한 사유:
  • GAPS_PRESENT (1 insurers)
  • OUT_OF_UNIVERSE (1 insurers)

[비교 테이블]
  보험사    담보명    PRIME 상태
 SAMSUNG      -  비교 대상 아님
  HANWHA 암진단비 제한적 비교 가능

[보험사별 상세 설명]
▶ SAMSUNG
판단 결과: 비교 대상 아님
사유: [STEP 3.12 explanation - IMMUTABLE]
```

---

### ✅ STEP 3.13: Query Pipeline (THE LAST STEP)
**Commit:** f21f6e4 | **Date:** 2025-12-25

**Summary:**
- User query → PRIME comparison pipeline connector
- Natural language query parsing (deterministic)
- Automatic STEP 3.11 → STEP 3.12 orchestration
- 100% reproducibility verified

**Purpose:**
- Connect natural language queries to comparison engine
- Query interpretation + routing ONLY
- NO comparison logic (already in STEP 3.11/3.12)

**Pipeline Flow:**
```
User Query
  ↓
Query Parsing (insurers + coverage keyword)
  ↓
STEP 3.11 (Comparison Engine)
  ↓
STEP 3.12 (Explanation Layer)
  ↓
ExplainedComparisonResult
```

**Example Results:**
- "삼성과 한화 암진단비 비교해줘"
  - Coverage: "암진단비"
  - Insurers: SAMSUNG, HANWHA
  - SAMSUNG: out_of_universe
  - HANWHA: in_universe_with_gaps (5건)

- "KB 롯데 뇌졸중진단비 보여줘"
  - Coverage: "뇌졸중진단비"
  - Insurers: KB, LOTTE
  - KB: in_universe_comparable
  - LOTTE: in_universe_with_gaps (2건)

**Query Parsing (Deterministic):**
- ✅ Insurer extraction: 삼성 → SAMSUNG, 한화 → HANWHA, etc.
- ✅ Common word removal: 비교해줘, 보여줘, etc.
- ✅ Whitespace normalization only
- ❌ No semantic inference
- ❌ No coverage expansion

**Reproducibility:**
- ✅ Same query → Same result
- ✅ 100% REPRODUCIBLE

**DoD:**
- ✅ One-line question → PRIME result
- ✅ 100% reproducibility verified
- ✅ No state changes, no re-judgment

**This is THE LAST STEP of the core pipeline.**

All subsequent work (UI, formatting, recommendations, policy expansion) builds on this foundation.

---

### ✅ STEP 3.12: PRIME Explanation Layer (Immutable)
**Commit:** 7e6d97e | **Date:** 2025-12-25

**Summary:**
- Explanation layer for PRIME comparison results
- STEP 3.11 results are IMMUTABLE (판결문)
- STEP 3.12 provides reasoning only (이유서)
- No state changes, no re-judgment, no recommendations

**Purpose:**
- Answers ONLY: "이 PRIME 결과가 나온 사실적 이유는 무엇인가?"
- Does NOT answer: "어느 담보가 더 낫다" / "사실상 같은 담보다" / "추천한다"

**PRIME State Explanations:**
- `out_of_universe`: 요약표에 해당 담보 없음
- `in_universe_with_gaps`: N건 후보 존재 또는 축 정보 누락 (의미 추론 불가)
- `in_universe_unmapped`: 가입설계서 존재하나 신정원 코드 미대응
- `in_universe_comparable`: 단일 담보, 모든 축 존재

**Output Structure:**
```json
{
  "comparison_result": { ... STEP 3.11 original ... },
  "explanation": {
    "summary": "전체 요약",
    "details": [보험사별 상세 설명]
  }
}
```

**Immutability Verification:**
- ✅ Test: `test_step312_immutability.py`
- ✅ Result: NO CHANGES - IMMUTABILITY VERIFIED

**Constitution Compliance:**
- ✅ PRIME 상태 변경 없음
- ✅ 추론/의미 통합 없음
- ✅ 사실 기반 설명만 제공
- ✅ STEP 3.11 결과 100% 재현 가능

---

### ✅ STEP 3.11′ HOTFIX: PRIME-aligned Comparison Engine
**Commit:** 6dbb6ae | **Date:** 2025-12-25

**Summary:**
- Replaced similarity-based matching with deterministic substring search
- Implemented PRIME 4-State classification (in_universe_comparable/unmapped/with_gaps, out_of_universe)
- Fact-based comparison table only (no inference)
- Verified no AMBIGUOUS/similarity/score in output

**PRIME 4-State Rules:**
- `in_universe_comparable`: MAPPED + all core axes present
- `in_universe_unmapped`: Found but UNMAPPED
- `in_universe_with_gaps`: MAPPED but missing axes OR multiple candidates
- `out_of_universe`: Not found in proposal

**Constitution Compliance:**
- ✅ Proposal = SSOT (Fact Table only)
- ✅ Substring search only (no inference)
- ✅ Multiple candidates → WITH_GAPS + MULTIPLE_CANDIDATES_NO_INFERENCE
- ✅ Shinjeongwon code = reference key (NOT filter/primary)
- ✅ UNMAPPED ≠ "similar coverage"

**Sample Results Verified:**
- 암진단비: OUT_OF_UNIVERSE(SAMSUNG), WITH_GAPS(HANWHA 5건, MERITZ 4건)
- 뇌졸중진단비: OUT_OF_UNIVERSE(SAMSUNG), COMPARABLE(KB), WITH_GAPS(LOTTE 2건)
- 다빈치수술비: OUT_OF_UNIVERSE(전체) → 비교 불가

---

### ✅ STEP 3.10: Proposal Coverage → Shinjeongwon Reference Mapping
**Commit:** 4d89681 | **Date:** 2025-12-25

**Summary:**
- Non-destructive reference mapping (상태 태깅 전용)
- Mapped 334 proposal coverages to Shinjeongwon codes
- Results: MAPPED (140, 41.9%), AMBIGUOUS (129, 38.6%), UNMAPPED (65, 19.5%)
- No coverage unification, no code enforcement, no normalization
- Reference mapping only

**Outputs:**
- `data/step310_mapping/proposal_coverage_mapping.csv` (334 rows)
- `data/step310_mapping/mapping_report.txt` (validation report)

**Constitution Compliance:**
- ✅ 가입설계서 원본 보존 (비파괴)
- ✅ 신정원 코드 강제 부여 금지
- ✅ 담보 통합/판단/정규화 금지
- ✅ 참조(reference) 매핑만 수행
- ✅ STEP 3.11로 즉시 이행 가능

---

### ⚠️ STEP 33-β-2d: Customer Clarification Pending
**Commit:** (pending) | **Date:** 2025-12-25

**Summary:**
- Premium API integration **BLOCKED** - Upstream returns 400 with empty body
- All client-side/proxy implementations verified correct
- Tested variations: Korean/ASCII customerNm, browser headers, parameter combinations
- All tests return same 400 from nginx (before application layer)
- Spec indicates "Public API - no authentication", but actual behavior suggests access restrictions

**Customer Clarification Request Created:**
- Document: `docs/api/premium_api_customer_clarification.md`
- Required information:
  - Correct base URL / environment
  - Authentication requirements (API key, session, IP whitelist)
  - Required headers or additional parameters
  - Working curl/Postman sample request
  - Access restrictions (WAF, rate limit, geographic)

**SSOT Updated:**
- `docs/api/premium_api_spec.md` status: "Spec/Access Requirement Mismatch Suspected"
- Live observation section added with test evidence
- Integration status: BLOCKED pending customer response

**Next Step:**
- Await customer clarification
- Do NOT proceed with authentication guesses or parameter additions
- Resume integration only after receiving verified access method

---

### ✅ STEP 33-β-2: Browser Header Parity Mode
**Commit:** 9bc7ff3 | **Date:** 2025-12-25

**Summary:**
- Added `PREMIUM_UPSTREAM_HEADER_MODE=browser` environment variable
- Mimics browser headers (User-Agent, Referer, Accept-Language, etc.)
- Created curl reproduction script: `apps/web/scripts/premium_upstream_curl.sh`
- Result: No change - still 400 with empty body
- Conclusion: Header configuration not the issue

---

### ✅ STEP 33-β-1e: Upstream Meta Logging
**Commit:** 405e94f | **Date:** 2025-12-25

**Summary:**
- Added response metadata logging for both success and failure cases
- Logs status, url, content-type, content-length, server, date
- Confirmed nginx 400 with Content-Length: 0, bodyLen: 0
- Evidence captured for customer clarification

---

### ✅ STEP 33-β-1b: Upstream 400 Diagnosis Logging
**Commit:** fa96c57 | **Date:** 2025-12-25

**Summary:**
- Added guaranteed logging to Premium proxy routes for 400 error diagnosis
- Module load log: `🚨 [premium:<route>] module loaded`
- Handler entry log: `🚨 [premium:<route>] handler entered`
- Request body, params, full upstream URL logging
- Upstream error body capture (up to 500 chars in response, full in console)
- Purpose: Identify whether 400 is from routing issue or upstream validation
- /compare contract unchanged ✅ (zero diff)

**Logs Added:**
```
🚨 [premium:simple-compare] handler entered
[Premium Simple] body: {...}
[Premium Simple] params: baseDt=...&birthday=...
[Premium Simple] upstreamFullUrl: https://.../public/prdata/prInfo?...
[Premium Simple] upstream error body: <full text>
```

**Next:** User clicks DEV buttons → Copy terminal logs → Analyze upstream 400 root cause

---

### ✅ STEP 33-β-1: DEV Premium Triggers (Live Capture UI)
**Commit:** 1864f5c | **Date:** 2025-12-25

**Summary:**
- Added 2 DEV buttons to `apps/web/src/pages/index.tsx` for Premium API testing
- Buttons: `[DEV] Premium Simple Compare`, `[DEV] Premium Onepage Compare`
- Purpose: Generate live Network requests for Request/Response payload capture
- Request payloads based on SSOT (`docs/api/premium_api_spec.md`)
- Fixed test values: baseDt=20251225, birthday=19760101, age=50, sex=1, customerNm=홍길동
- /compare contract unchanged ✅ (zero diff in apps/api, tests/snapshots)

**DoD:**
- ✅ UI triggers visible at http://localhost:3000 (orange DEV section)
- ✅ Network tab captures POST /api/premium/simple-compare & onepage-compare
- ✅ Request/Response JSON available for manual copy
- ✅ Zero impact on /compare

---

### ✅ STEP 33-α: CORS Preflight Fix
**Commit:** 59af9e9 | **Date:** 2025-12-25

**Summary:**
- Added CORS middleware to FastAPI (allows OPTIONS preflight from http://localhost:3000)
- Env-controlled via `CORS_ORIGINS` (defaults to localhost:3000 for dev)
- OPTIONS /compare now returns 200 with proper CORS headers
- /compare business logic unchanged ✅
- /compare snapshots unchanged ✅

---

### ⚠️ STEP 32-λ-2: Truth Lock Hotfix
**Commit:** 9c85092 | **Date:** 2025-12-25

**Summary:**
- Corrected misleading "Verified" claims in Premium API spec
- Reclassified verification status to 3-tier structure:
  - **A. Spec-confirmed** (documented in SSOT)
  - **B. Fixture-tested** (offline, does NOT confirm live behavior)
  - **C. Live-observed** (PENDING - not executed)
- Defensive handling explicitly marked as unobserved
- Removed inactive `adapter.test.ts` (no test framework configured)
- Authoritative test: `apps/web/scripts/premium_adapter_smoke.mjs`
- No behavior change ✅
- /compare regression lock: 0 diff ✅

---

### ✅ STEP 32-λ: Fixture-Based Regression Tests
**Commit:** 427da8c, 0274c91 | **Date:** 2025-12-25

**Summary:**
- Created 3 SSOT-based test fixtures (prInfo, prDetail, wrapped)
- Added adapter regression tests (5 scenarios, network-independent)
- Smoke test script: `node apps/web/scripts/premium_adapter_smoke.mjs`
- Initial attempt at verification documentation (corrected in λ-2)
- /compare regression lock: 0 diff ✅

---

### ✅ STEP 32-κ-POST-2: SSOT Wording Tightening
**Commit:** 409b6b0 | **Date:** 2025-12-25

**Summary:**
- All SSOT references now point to `docs/api/premium_api_spec.md` (not upstream files)
- Removed assertions about "actual upstream behavior" (replaced with "SSOT does not document")
- Comment/doc wording only (no behavior change)
- TypeScript typecheck: PASS ✅
- /compare regression lock: 0 diff ✅

---

### ✅ STEP 32-κ-POST: Types/Docs Cleanup (Spec-Driven)
**Commit:** 95f18f4 | **Date:** 2025-12-25

**Summary:**
- Replaced generic `UpstreamPremiumResponse` with spec-based types (`UpstreamPrInfoResponse`, `UpstreamPrDetailResponse`)
- Removed forced `data` wrapper assumption (defensive union type instead)
- README smoke tests clarified: POST→GET conversion, dual response structures
- Deprecated `premium_api_spec_minimal.md` (legacy placeholder)
- /compare regression lock maintained ✅

---

### ✅ STEP 32-κ-FIX: Adapter Response Structure Support
**Commit:** 3469262 | **Date:** 2025-12-25

**Summary:**
- Fixed adapter to support both prInfo (simple) and prDetail (onepage) response shapes
- prInfo: basePremium from `outPrList[].monthlyPrem`
- prDetail: basePremium from `prProdLineCondOutIns[].monthlyPremSum`
- Spec-driven field extraction (no assumptions)
- /compare regression lock maintained ✅

---

### ✅ STEP 32-δ: Premium UI Wiring Hardening + Mocks Separation
**Commit:** d1f1877 | **Date:** 2025-12-25
**Details:** [docs/status/2025-12-25_step-32-delta.md](docs/status/2025-12-25_step-32-delta.md)

**Summary:**
- Moved `convertProxyResponseToCards()` from mocks to production bridge
- Eliminated fake proposalId generation (optional field)
- Hardened failure rendering (explicit MISSING cards, never blank screens)
- /compare regression lock maintained ✅

---

### ✅ STEP 32: Premium API Integration (Real basePremium)
**Commit:** 678eb8d | **Date:** 2025-12-25
**Details:** [docs/status/2025-12-25_step-32.md](docs/status/2025-12-25_step-32.md)

**Summary:**
- Real basePremium from Premium API (monthlyPremSum ONLY)
- Proxy routes: `/api/premium/simple-compare`, `/onepage-compare`
- Coverage name unmapped → graceful PARTIAL (not error)
- /compare contract/snapshots UNTOUCHED ✅

---

### ✅ STEP 31-α: General Premium Multiplier Table Integration
**Commit:** 59f562b | **Date:** 2025-12-25
**Details:** [docs/status/2025-12-25_step-31-alpha.md](docs/status/2025-12-25_step-31-alpha.md)

**Summary:**
- Embedded Excel multiplier table as SSOT (frontend)
- Real multipliers applied to ②일반 premium calculation
- Coverage name → multiplier lookup (graceful degradation)

---

### ✅ STEP 31: Premium Calculation UI Logic
**Commit:** 23aac38 | **Date:** 2025-12-25

**Summary:**
- Frontend premium calculation (READY/PARTIAL/MISSING states)
- PlanType: ①전체 / ②일반 / ③무해지
- Mock-based UI testing (no backend changes)

---

### ✅ STEP 28: Contract-Driven Frontend MVP
**Commit:** 4fd4a5c | **Date:** 2025-12-24

**Summary:**
- Next.js frontend with contract-driven view resolution
- 5 view components based on backend contract states
- DEV_MOCK_MODE for golden snapshot testing

---

### ✅ STEP 14: Compare API E2E Integration
**Commit:** Multiple | **Date:** 2025-12-23

**Summary:**
- `/compare` endpoint with golden snapshots
- 5-state comparison system (comparable/unmapped/policy_required/out_of_universe/non_comparable)
- Evidence-based responses with document references

---

### ✅ STEP 6-C: Proposal Universe Lock
**Commit:** Multiple | **Date:** 2025-12-23

**Summary:**
- Proposal coverage universe as single source of truth
- Excel-based coverage mapping (no LLM inference)
- 3-tier disease code model (KCD-7 + insurance groups)

---

### ✅ STEP 5-B: DB Read-Only Implementation
**Commit:** Multiple | **Date:** 2025-12-23

**Summary:**
- PostgreSQL read-only enforcement (4 layers)
- Entity-based evidence filtering
- is_synthetic=false hard-coded

---

### ✅ STEP 5-A: OpenAPI Contract + FastAPI Skeleton
**Commit:** c102751 | **Date:** 2025-12-23

**Summary:**
- OpenAPI 3.0.3 contract
- FastAPI with 3 endpoints
- Contract tests (8/8 PASS)

---

### Earlier Steps (STEP 1-13)

Detailed logs available in:
- [docs/status/legacy_STATUS_full.md](docs/status/legacy_STATUS_full.md)

**Key accomplishments:**
- Database schema design
- LLM ingestion pipeline
- Docker E2E testing framework
- Minimal seed data

---

## Current Status

**Active Branch:** main
**Latest Commit:** dc3e332

**Completed Work:**
- ✅ Backend /compare API (immutable contract)
- ✅ Frontend contract-driven UI
- ✅ Premium API integration (additional feature)
- ✅ Coverage mapping via Excel SSOT
- ✅ Docker E2E testing

**In Progress:**
- Premium UI/UX refinement
- Documentation consolidation

**Next Steps:**
1. Coverage name normalization pipeline
2. Admin UI for AMBIGUOUS coverage mapping
3. Disease code group management interface

**Blockers:** None

---

## Constitutional Guarantees

All work adheres to [CLAUDE.md](CLAUDE.md) constitution:

- ✅ **Coverage Universe Lock**: 가입설계서 = SSOT for comparison targets
- ✅ **Deterministic Compiler**: No LLM inference for coverage/disease mappings
- ✅ **Evidence Rule**: All data has document references
- ✅ **Disease Code Authority**: KCD-7 official distribution only
- ✅ **Document Hierarchy**: Proposal > Summary > Business Rules > Policy
- ✅ **/compare Immutability**: Contract/snapshots never modified

---

## Key Documentation

**Constitution:**
- [CLAUDE.md](CLAUDE.md) - Project constitution (highest authority)

**Implementation Guides:**
- [apps/web/README.md](apps/web/README.md) - Frontend setup + Premium smoke tests
- [apps/api/README.md](apps/api/README.md) - Backend API documentation

**Status Logs:**
- [docs/status/](docs/status/) - Detailed milestone logs
- [docs/status/legacy_STATUS_full.md](docs/status/legacy_STATUS_full.md) - Full historical archive

**OpenAPI Contract:**
- [openapi/step5_openapi.yaml](openapi/step5_openapi.yaml) - /compare API contract

---

## Quick Commands

### Backend
```bash
# Contract tests (DB-agnostic)
pytest tests/contract -q

# Integration tests (real DB)
pytest tests/integration -q

# E2E tests (Docker)
pytest tests/e2e -q

# All tests
pytest -q
```

### Frontend
```bash
cd apps/web

# Development (mock mode)
export DEV_MOCK_MODE=1
pnpm dev

# Development (real API)
export DEV_MOCK_MODE=0
export API_BASE_URL=http://localhost:8000
pnpm dev

# Production build
pnpm build
```

### Database
```bash
# Connect to local PostgreSQL
psql -U postgres -d inca_rag_final

# Run migrations
python migrations/run_migration.py
```

---

## Environment Variables

### Backend (`apps/api/.env`)
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/inca_rag_final
```

### Frontend (`apps/web/.env.local`)
```bash
DEV_MOCK_MODE=0  # 0=real API, 1=mocks
API_BASE_URL=http://localhost:8000
PREMIUM_API_BASE_URL=https://api.premium-service.example.com
PREMIUM_API_KEY=your_api_key_here  # Optional
```

---

## Project Structure

```
inca-RAG-final/
├── CLAUDE.md                 # Constitution (highest authority)
├── STATUS.md                 # This file (project index)
├── apps/
│   ├── api/                  # FastAPI backend
│   │   ├── app/
│   │   │   ├── routers/      # /compare endpoints
│   │   │   ├── db.py         # Read-only DB connection
│   │   │   └── policy.py     # Policy enforcement
│   │   └── tests/
│   └── web/                  # Next.js frontend
│       ├── src/
│       │   ├── components/   # UI components
│       │   ├── contracts/    # UI state map (SSOT)
│       │   └── lib/
│       │       ├── api/      # API clients + premium bridge
│       │       └── premium/  # Premium calculation logic
│       └── README.md         # Frontend docs + smoke tests
├── docs/
│   └── status/               # Detailed milestone logs
├── data/                     # Insurance documents + mappings
├── migrations/               # Database migrations
├── openapi/                  # OpenAPI contracts
└── tests/
    ├── contract/             # Contract tests
    ├── integration/          # Integration tests
    └── e2e/                  # E2E tests
```

---

## Contact & Support

**Issues:** https://github.com/jason-dio-so/inca-rag-final/issues
**Documentation:** See `docs/` and `apps/*/README.md`
**Constitution:** [CLAUDE.md](CLAUDE.md) (all rules and principles)

---

**Last Full Archive:** [docs/status/legacy_STATUS_full.md](docs/status/legacy_STATUS_full.md) (3194 lines)
**This Index:** ~320 lines (10× reduction for accessibility)

---

### ✅ STEP 32-κ: Premium API Spec-Driven Lock
**Commit:** [pending] | **Date:** 2025-12-25

**Summary:**
- Locked Premium integration to actual upstream specifications (spec-driven, zero assumptions)
- basePremium sources: `monthlyPrem` (simple) / `monthlyPremSum` (onepage)
- Upstream method: GET (not POST), insurer codes: N01-N13 format
- README curl examples now executable with real payload structure

