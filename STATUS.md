# inca-RAG-final Project Status

**Last Updated:** 2025-12-26
**Current Phase:** STEP NEXT-9 Documentation Complete (INCA DIO Requirements Lock)
**Project Health:** ✅ ACTIVE - Customer Requirements Compiled

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

### ✅ STEP NEXT-8B: CLAUDE.md Consistency Recovery (Complete)
**Commit:** [pending] | **Date:** 2025-12-26

**Summary:**
- CLAUDE.md 전체 정합성 회복 (본문 규칙 ↔ Decision Change Log 일치)
- 금지 사항 확장 (코드/데이터 + 매핑/추출 + UI/응답 레벨 분리)
- Deterministic Compiler 적용 범위 명확화 (전 구간: 데이터 추출 ~ UI 응답)
- Decision Change Log 추가 (변경 이력 명시적 기록)
- 현행 시스템 상태 업데이트 (2025-12-26, main branch)

**목적:**
- 기존 문서 간 충돌 제거
- 최신 결정 사항을 본문 규칙에 완전히 반영
- 헌법 신뢰성 회복 (암묵적 추론 방지)

**변경 성격:**
- **규칙 수정 / 충돌 제거** (기능 추가 없음)
- 문서 정합성 작업만 수행

**주요 변경 사항:**

1. **금지 사항 재구조화 (10개 → 15개)**
   - 코드/데이터 레벨: 1~6번 (기존)
   - 매핑/추출 레벨: 7~10번 (기존)
   - **UI/응답 레벨: 11~15번 (신규 추가)**
     - 추천 문구 생성 금지
     - 우열 판단 표현 금지
     - 해석 문구 금지
     - 추론 기반 응답 금지
     - LLM 생성 응답 문구 금지 (템플릿만 허용)

2. **Deterministic Compiler 적용 범위 확장**
   - Before: 데이터 추출만
   - After: 데이터 추출 / 매핑 / **UI 응답** / **비교 결과 생성** 전 구간
   - UI 응답 문구 생성 금지 추가
   - 비교 결과 해석/추론 금지 추가
   - 고정 템플릿 기반 응답 생성만 허용

3. **Decision Change Log 추가**
   - 2025-12-26 변경 사항 7건 기록
   - "After" 내용이 본문 규칙보다 우선함을 명시
   - 암묵적 추론 방지 목적

4. **현행 시스템 상태 업데이트**
   - 날짜: 2025-12-24 → 2025-12-26
   - 브랜치: feature/proposal-universe-lock-v1 → main
   - 완료 단계: NEXT-8A 포함
   - 핵심 모듈: 최신 구조 반영

**정합성 검증 체크리스트:**
- ✅ 고객 요구사항 SSOT (data/inca-dio.pdf) 명확히 고정
- ✅ data/호출_api/ 보류 명시
- ✅ ChatGPT UI 목표 구체화 (좌: 질의 / 우: 근거 패널)
- ✅ 추천/우열/해석 금지 전 구간 적용 (UI/응답 레벨 추가)
- ✅ Deterministic compiler UI/응답 단계까지 확장
- ✅ Decision Change Log 본문 규칙보다 우선함 명시
- ✅ 본문 규칙 ↔ Decision Change Log 충돌 0건

**DoD Achievement:**
- ✅ Decision Change Log ↔ 본문 규칙 충돌 제거
- ✅ 금지 사항 UI/응답 레벨 확장 (11~15번)
- ✅ Deterministic Compiler 전 구간 적용
- ✅ 현행 시스템 상태 최신화
- ✅ 새 설계·구현 추가 없음 (문서 정합성만)
- ✅ STATUS.md NEXT-8B 기록
- ⏳ git commit + push (pending)

**Constitutional Compliance:**
- ✅ 구현이 아닌 헌법 정비 (documentation only)
- ✅ 추론/설계 확장/기능 추가 없음
- ✅ 기존 결정 사항의 본문 반영만 수행

**영향 범위:**
- 문서만 (CLAUDE.md)
- 코드 변경 없음
- 데이터 변경 없음

**다음 단계로 넘어갈 수 있는 조건:**
- ✅ CLAUDE.md + data/inca-dio.pdf = 단일 작업 기준 확립
- ✅ 헌법 내부 충돌 0건
- ✅ Decision Change Log 유지보수 프로세스 확립

---

### ✅ STEP NEXT-8A: CLAUDE.md SSOT Entry Point Lock (Complete)
**Commit:** ba019e2 | **Date:** 2025-12-26

**Summary:**
- CLAUDE.md 최상단에 SSOT 배너 섹션 추가 (🔴 SSOT ENTRY POINT)
- 고객 요구사항 범위 선언 (Customer Intent Lock)
- 보험료/요율 기능 보류 원칙 명문화
- Claude 작업 방식 강제 규칙 추가
- 대화 기억/추론 의존 차단, 레포 내 CLAUDE.md = 유일한 실행 헌법

**목적:**
- Claude의 암묵적 추론/대화 기억 의존을 완전히 차단
- CLAUDE.md + data/inca-dio.pdf를 유일한 작업 기준으로 고정
- 뺑뺑이 방지 (무엇을 하고, 무엇을 하지 않는지 명시)

**추가된 섹션:**
1. **🔴 SSOT ENTRY POINT (MANDATORY)**
   - 고객 요구사항 단일 출처: data/inca-dio.pdf
   - 현재 단계 사용 데이터: 보험용어, 가입설계서, 약관, 사업방법서, 상품요약서
   - 현재 단계 보류: data/호출_api/ (보험료 기능)
   - UI 목표: ChatGPT 스타일 (좌측 질의, 우측 근거 패널)
   - 금지 사항: 추천/우열/해석/추론
   - 작업 시작 규칙: CLAUDE.md + inca-dio.pdf 필수 확인

2. **고객 요구사항 범위 선언 (Customer Intent Lock)**
   - 1차 목표: 보험상품 AI 가이드 (ChatGPT UI)
   - FAQ ①⑦, 예제 14 = 기능 요구사항 (참고 예시 아님)
   - 시스템 목적: 질의 구조화 + 가입설계서 기준 비교 + 근거 제시
   - 보험료 계산/비교: 현 범위 제외

3. **보험료/요율 기능 보류 원칙**
   - data/호출_api/ = 읽기/구현/연결 금지
   - 보험료 기능은 별도 STEP (UI/비교/담보 구조 고정 이후)

4. **Claude 작업 방식 (강제)**
   - CLAUDE.md 범위 밖 변경 금지 (문서 수정 PR 먼저)
   - "뭘 더 해줄까?" 질문 금지
   - 응답 유형: 설계/구현/문서 수정/보류 사유 명시만 허용

**DoD Achievement:**
- ✅ CLAUDE.md 최상단에 SSOT 배너 추가
- ✅ 고객 요구사항 범위 / 보험료 보류 규칙 명문화
- ✅ Claude 작업 방식 강제 섹션 추가
- ✅ STATUS.md 업데이트 (NEXT-8A 항목)
- ⏳ git commit + push (pending)

**Constitutional Compliance:**
- ✅ 구현이 아닌 헌법 정비 (documentation only)
- ✅ 추론/설계 확장/기능 추가 없음
- ✅ 문서 현행화에만 집중

**Next Steps:**
- Git commit + push
- 이후 모든 작업은 CLAUDE.md + inca-dio.pdf 기준으로만 진행

---

### ✅ STEP NEXT-7: Admin Mapping Workbench (Complete)
**Commit:** 946e1e4 | **Date:** 2025-12-26
**Stabilization-β:** 8562a1f | **Date:** 2025-12-26
**Stabilization-γ:** eb5704d | **Date:** 2025-12-26
**Stabilization-δ:** 86fc1da | **Date:** 2025-12-26

**Summary:**
- Backend: Admin mapping service with canonical coverage rule enforcement
- Backend: `/admin/mapping/*` endpoints (queue, approve, reject, snooze)
- Database: 4 new tables (mapping_event_queue, coverage_code_alias, coverage_name_map, admin_audit_log)
- Frontend: Admin UI at `/admin/mapping` (queue + detail + approval workflow)
- Integration: Event population from compare/clarify flow
- Tests: 6 comprehensive backend tests (async fixtures fixed, DB required)
- Constitutional compliance: Canonical Coverage Rule + Safe Defaults + Auditable

**NEXT-7-β Stabilization:**
- Backend Root Consolidation: Moved `src/admin_mapping/` → `apps/api/app/admin_mapping/`
- Single Backend Root: `apps/api/app/` is now the only backend root (Constitutional: Single Backend Root)
- DB Pool: Added asyncpg support to `apps/api/app/db.py` for admin operations
- Router Registration: Admin mapping router registered in `apps/api/app/main.py`
- Async Pool Cleanup: Shutdown handler added for async pool
- Core Tests: 231 tests still passing (no regression)

**NEXT-7-γ Stabilization:**
- Tests Restored: `tests/test_admin_mapping_approve.py` fully restored (no .skip)
- Async Fixtures Fixed: pytest_asyncio decorators applied correctly
- Test Coverage: 6 comprehensive tests (create, approve, invalid code, reject, snooze, dedupe)
- Smoke Tests: Complete documentation in `docs/admin/STEP_NEXT7_GAMMA_SMOKE_TESTS.md`
- Deployment Ready: Migration verified safe, API endpoints documented, UI workflow tested
- Constitutional: No skip/xfail markers (tests require DB but are production-ready)

**NEXT-7-δ Stabilization:**
- Docker Compose: Test-specific DB environment (`docker-compose.test.yml`)
- Migration Script: One-command migration application (`tools/db/apply_migrations_next7.sh`)
- Test Runner: One-command test execution (`tools/test/run_admin_mapping_tests.sh`)
- DB Reflection: Tests verify coverage_name_map + audit_log row creation
- Conflict Test: Restored test_approve_event_conflict (safe defaults verification)
- Test Count: 7 comprehensive tests (added conflict scenario)
- Execution Log: Complete smoke test documentation in `docs/admin/STEP_NEXT7_DELTA_SMOKE_LOG.md`

**Key Features:**
1. **Event Queue Management**: UNMAPPED/AMBIGUOUS events auto-collected with deduplication
2. **Canonical Code Validation**: All approvals validated against 신정원 통일코드
3. **Conflict Detection**: Safe defaults - reject on alias/name conflicts (no auto-overwrite)
4. **Audit Trail**: Complete before/after tracking for all admin actions
5. **Resolution Types**: ALIAS (별칭 등록) / NAME_MAP (담보명 매핑) / MANUAL_NOTE

**Module Structure:**
```
apps/api/app/admin_mapping/
├── __init__.py
├── models.py (Pydantic schemas, 5-state event model)
├── service.py (AdminMappingService with validation)
├── router.py (FastAPI endpoints)
└── integration.py (compare flow integration)

migrations/
└── step_next7_admin_mapping_workbench.sql (4 tables + triggers)

apps/web/src/pages/
├── admin/mapping.tsx (Admin UI)
└── api/admin/mapping/*.ts (Next.js API proxies)

tests/
└── test_admin_mapping_approve.py (8 tests)

docs/admin/
└── STEP_NEXT7_ADMIN_MAPPING_WORKBENCH.md (complete documentation)
```

**DoD Status (NEXT-7-δ):**
- [x] OPEN UNMAPPED/AMBIGUOUS events queued with deduplication
- [x] Admin approval reflects to coverage_code_alias or coverage_name_map
- [x] All actions logged to admin_audit_log
- [x] Conflicts/invalid codes fail conservatively (no auto-overwrite)
- [x] Backend tests enhanced (7 tests, DB reflection verified, conflict test restored)
- [x] Docker Compose test environment created
- [x] One-command migration script (`./tools/db/apply_migrations_next7.sh`)
- [x] One-command test runner (`./tools/test/run_admin_mapping_tests.sh`)
- [x] DB reflection checks added (coverage_name_map + audit_log verification)
- [x] Execution log documented (docs/admin/STEP_NEXT7_DELTA_SMOKE_LOG.md)
- [ ] Main branch commit + push (NEXT-7-δ)

**Next Steps (One-Command Execution):**
- Run tests: `./tools/test/run_admin_mapping_tests.sh`
- Or step-by-step:
  1. Start DB: `docker-compose -f docker-compose.test.yml up -d`
  2. Migrate: `./tools/db/apply_migrations_next7.sh`
  3. Test: `python -m pytest tests/test_admin_mapping_approve.py -v`
- Verify: All 7 tests pass (no skip/xfail)
- Cleanup: `docker-compose -f docker-compose.test.yml down`

---

### ✅ STEP NEXT-6: Clarify Panel + Deterministic Compiler + Debug Tab (Complete)
**Commit:** fecf858 | **Date:** 2025-12-26

**Summary:**
- Backend: Deterministic compiler module (rule-based, no LLM)
- Backend: `/compare/compile` endpoint (CompileInput → compiled ProposalCompareRequest)
- Backend: `/compare/clarify` endpoint (clarification detection)
- Frontend: ClarifyPanel component (selection UI for ambiguous queries)
- Frontend: DebugPanel component (compiler debug info, hidden by default)
- Frontend: Test page at `/compare-clarify-test`
- 21 automated tests (100% passing): determinism + endpoint + scenarios
- No LLM dependency verified (mock tests passing)

**Module Structure (Backend):**
```
apps/api/app/compiler/
├── __init__.py
├── version.py (rule version tracking: v1.0.0-next6)
├── rules.py (deterministic domain/keyword mapping)
├── schemas.py (CompileInput/Output, CompilerDebug)
└── compiler.py (compile_request, detect_clarification_needed)
```

**Component Structure (Frontend):**
```
apps/web/src/
├── components/
│   ├── clarify/
│   │   └── ClarifyPanel.tsx  # Selection UI (insurers/surgery/cancer/focus)
│   └── debug/
│       └── DebugPanel.tsx    # Debug info (toggle, hidden by default)
├── lib/clarify/
│   ├── types.ts              # TypeScript types
│   └── normalize.ts          # Selection → CompileInput
└── pages/
    └── compare-clarify-test.tsx  # Test page (/compare-clarify-test)
```

**Compiler Features:**
- **Deterministic**: Same input → same output (test-verified)
- **No LLM**: Rule-based only (no OpenAI/Anthropic calls)
- **Traceable**: decision_trace logs all applied rules
- **Versioned**: rule_version tracked (v1.0.0-next6)
- **Fast**: <10ms compilation time (no network calls)

**Clarification Triggers:**
1. Insurers < 2
2. Surgery method keywords detected (다빈치/로봇/복강경)
3. Cancer subtype keywords detected (제자리암/경계성종양/유사암)
4. Comparison focus unclear (amount/definition/condition)

**Debug Panel Policy:**
- **Default: Hidden** (toggle button to show)
- **Content**: rule_version, selected_slots, decision_trace, warnings, compiled_request JSON
- **Constitutional**: Fact-only, no recommendation/judgment

**Tests** (21/21 passing):
1. Compiler determinism (6 tests)
   - Same input → same output
   - Different inputs → different outputs
   - Rule version tracking
   - Decision trace reproducibility
2. Endpoint tests (10 tests)
   - `/compare/compile` schema validation
   - Options handling (surgery_method, cancer_subtypes, comparison_focus)
   - `/compare/clarify` detection logic
3. No LLM dependency (5 tests)
   - No OpenAI calls
   - No Anthropic calls
   - Fast execution (<100ms)
   - No external API calls
4. E2E scenarios (5 tests)
   - Scenario 1: 다빈치 수술비 (surgery_method selection)
   - Scenario 2: 경계성종양·제자리암 (cancer_subtypes selection)
   - Scenario 3: 암 진단비 (general comparison)
   - Determinism guarantee across scenarios
   - Debug info always present

**Documentation:**
- `docs/ui/STEP_NEXT6_CLARIFY_AND_DEBUG.md` (complete spec)

**Constitutional Compliance:**
- ✅ Fact-only (no recommendation)
- ✅ No inference (rule-based only)
- ✅ Presentation only (selection UI)
- ✅ Deterministic compiler (reproducible)
- ✅ Canonical coverage rule (신정원 통일코드)

### ✅ STEP NEXT-5: ViewModel Assembler + Frontend Renderer (Complete)
**Commit:** 0ee2373 | **Date:** 2025-12-26

**Summary:**
- Backend: ViewModel assembler (ProposalCompareResponse → ViewModel JSON)
- Backend: `/compare/view-model` endpoint with runtime schema validation
- Backend: 15 automated tests (100% passing)
- Frontend: 3-Block ChatGPT-style renderer (React/TypeScript)
- Frontend: 5 components (CompareViewModelRenderer + 4 blocks)
- Frontend: Test page at `/compare-test`
- Evidence reference integrity guaranteed
- Hard-ban phrase detection (0 violations)
- Debug section non-display enforced

**Module Structure (Backend):**
```
apps/api/app/view_model/
├── __init__.py
├── types.py (Pydantic models matching JSON Schema)
├── schema_loader.py (JSON Schema loader + validator)
└── assembler.py (assembler logic)
```

**Component Structure (Frontend):**
```
apps/web/src/
├── components/compare/
│   ├── CompareViewModelRenderer.tsx  # Entry (3-Block layout)
│   ├── ChatHeader.tsx                # BLOCK 0: User query
│   ├── CoverageSnapshot.tsx          # BLOCK 1: Per-insurer snapshot
│   ├── FactTable.tsx                 # BLOCK 2: Comparison table
│   └── EvidenceAccordion.tsx         # BLOCK 3: Collapsible evidence
├── lib/compare/
│   └── viewModelTypes.ts             # TypeScript types from JSON Schema
└── pages/
    └── compare-test.tsx              # Test page (/compare-test)
```

**Assembler Features:**
- **Conservative status mapping**: No new inference (existing data → StatusCode)
- **Deterministic**: Same input → same output (test-verified)
- **Amount formatting**: 원 → 만원 conversion with thousand separator
- **Evidence ID generation**: `ev_{insurer}_{doc_type}_{index}` (deterministic)
- **Stable sorting**: fact_table rows (insurer/coverage), evidence_panels (insurer/doc_type/id)
- **Ref integrity**: All evidence_ref_id resolve to evidence_panels[].id

**Status Mapping Rules** (Conservative, No Inference):
| Input | Output Status |
|-------|---------------|
| mapping_status=UNMAPPED | UNMAPPED |
| mapping_status=AMBIGUOUS | AMBIGUOUS |
| comparison_result=out_of_universe | OUT_OF_UNIVERSE |
| comparison_result=comparable + MAPPED | OK |
| comparison_result=comparable_with_gaps | MISSING_EVIDENCE (conservative) |
| comparison_result=non_comparable | OK (fact exists) |
| Otherwise | MISSING_EVIDENCE (conservative fallback) |

**Endpoint:**
- URL: `POST /compare/view-model`
- Request: `ProposalCompareRequest` (same as `/compare`)
- Response: ViewModel JSON (schema-validated)
- Validation: Runtime check against `compare_view_model.schema.json` (env-controlled, default ON)
- Flow: `/compare` logic → assemble ViewModel → validate → return JSON

**Tests** (15/15 passing):
1. Schema validation (JSON Schema Draft 2020-12 compliance)
2. Evidence ref_id integrity (all refs resolve)
3. No forbidden phrases (hard-ban enforced)
4. Schema version format (`next4.vX`)
5. Deterministic output (reproducibility)
6. Fact table columns fixed (6 columns, immutable order)
7. Fact table deterministic sort (insurer/coverage ASC)
8. UNMAPPED status mapping
9. OUT_OF_UNIVERSE handling (empty snapshot/rows/panels)
10. Policy evidence added to panels
11. Amount formatting (원 → 만원)
12. Debug section optional
13. Canonical coverage codes in debug only
14. Excerpt length constraints (min 25 chars)
15. Insurer codes uppercase (canonical format)

**Golden Samples** (Test Fixtures):
- `sample_comparable_response`: Scenario A (both MAPPED, normal flow)
- `sample_unmapped_response`: Scenario B (UNMAPPED coverage)
- `sample_out_of_universe_response`: OUT_OF_UNIVERSE edge case
- `sample_with_policy_evidence_response`: Scenario C (policy evidence)

**Schema Updates:**
- Allow `null` for optional fields: `bbox`, `source_meta`, `debug.*`
- Rationale: Pydantic emits `null` for unset optional fields

**Frontend Implementation:**
- **BLOCK 0: ChatHeader**: Displays user_query + normalized_query (no internal codes)
- **BLOCK 1: CoverageSnapshot**: Shows comparison_basis + per-insurer headline amounts/status
- **BLOCK 2: FactTable**: Fixed 6-column layout (immutable order), no frontend sorting
  - Columns: 보험사, 담보명(정규화), 보장금액, 지급 조건 요약, 보험기간, 비고
  - Payout conditions: bullet list (Korean label + value_text, no interpretation)
- **BLOCK 3: EvidenceAccordion**: Collapsible per-insurer groups (doc_type, page, excerpt as-is)
- **Test Page**: `/compare-test` (example selector + live API test button)
- **Edge Cases**: Handles UNMAPPED/OUT_OF_UNIVERSE/empty evidence without crash

**Constitutional Compliance:**
- ✅ Backend: Fact-only (status from existing data, no new inference)
- ✅ Backend: No Recommendation (0 forbidden phrases, test-enforced)
- ✅ Backend: Presentation Only (pure mapping/formatting, no business logic)
- ✅ Frontend: Fact-only (display ViewModel as-is, no modification)
- ✅ Frontend: No Recommendation (zero "better/worse/same/different" phrases)
- ✅ Frontend: Presentation Only (no sorting/filtering/scoring)
- ✅ Frontend: Debug Non-UI (debug section completely hidden)
- ✅ Canonical Coverage Rule: Internal codes in debug, UI uses normalized names
- ✅ Coverage Universe Lock: OUT_OF_UNIVERSE for non-proposal
- ✅ Evidence Rule: All amounts have evidence_ref_id
- ✅ Deterministic: Test-verified reproducibility

**DoD Achievement:**
- ✅ Backend: `/compare/view-model` endpoint schema-compliant
- ✅ Backend: Assembler validates against JSON Schema
- ✅ Backend: Hard-ban test passing (0 violations)
- ✅ Backend: Evidence ref_id integrity passing
- ✅ Backend: 15/15 tests passing
- ✅ Frontend: CompareViewModelRenderer renders schema-compliant ViewModel
- ✅ Frontend: 3-Block structure implemented (Header, Snapshot, FactTable, Evidence)
- ✅ Frontend: Debug section non-display enforced
- ✅ Frontend: Build passes (type-safe)
- ✅ Frontend: Test page functional with example data
- ✅ Documentation complete (`STEP_NEXT5_ADAPTER_AND_RENDERER.md` v2.0.0)

**Key Principle:**
- **Assembler = Adapter = Presentation Layer = No Inference**
- **Status from existing data only (conservative fallback to MISSING_EVIDENCE)**
- **Same input → same output (deterministic, test-verified)**

---

### ✅ STEP NEXT-4: ViewModel JSON Schema Contract
**Commit:** e19f3f1 | **Date:** 2025-12-26

**Summary:**
- JSON Schema Draft 2020-12 for UI ViewModel (presentation layer contract)
- 5 validated examples (cancer diagnosis, borderline tumor, robotic surgery, UNMAPPED, missing evidence)
- 16 automated tests enforcing constitutional compliance
- Forbidden phrase detection (hard ban on recommendations/judgments)
- Reference integrity validation (evidence_ref_id → evidence_panels[].id)

**Deliverables:**
1. `docs/ui/STEP_NEXT4_VIEWMODEL_SCHEMA.md` (19-section specification)
2. `docs/ui/compare_view_model.schema.json` (JSON Schema Draft 2020-12)
3. `docs/ui/compare_view_model.examples.json` (5 examples)
4. `tests/test_ui_viewmodel_schema.py` (16 validation tests)

**Schema Structure:**
```json
{
  "schema_version": "next4.v1",
  "generated_at": "ISO8601",
  "header": {...},          // BLOCK 0: User Query
  "snapshot": {...},        // BLOCK 1: Coverage Snapshot
  "fact_table": {...},      // BLOCK 2: Fact Table
  "evidence_panels": [...], // BLOCK 3: Evidence Accordion
  "debug": {...}            // Non-UI: Reproducibility
}
```

**Top-Level Fields:**
- `schema_version`: "next4.v1" (version strategy defined)
- `generated_at`: ISO 8601 timestamp
- `header`: User query (original + normalized)
- `snapshot`: Comparison basis + per-insurer headline amounts
- `fact_table`: Fixed 6 columns (보험사/담보명/보장금액/지급조건/보험기간/비고)
- `evidence_panels`: Document type + page + excerpt (25-400 chars)
- `debug`: Coverage codes, retrieval params (optional, MUST NOT display in UI)

**Enum Definitions:**
- Insurers: `SAMSUNG, HANWHA, LOTTE, MERITZ, KB, HYUNDAI, HEUNGKUK, DB`
- Status: `OK, MISSING_EVIDENCE, UNMAPPED, AMBIGUOUS, OUT_OF_UNIVERSE`
- Doc Types: `가입설계서, 약관, 상품요약서, 사업방법서`
- Slot Keys: `waiting_period, payment_frequency, diagnosis_definition, method_condition, exclusion_scope, payout_limit, disease_scope`

**Validation Tests (16 total, all passing):**
1. Schema is valid JSON Schema Draft 2020-12
2. All examples validate against schema
3. No forbidden phrases in examples (hard ban enforced)
4. Required top-level fields present
5. Schema version format compliance
6. Insurer enum compliance (snapshot + fact_table + evidence_panels)
7. Fact table columns fixed and ordered
8. Evidence reference integrity (all ref_ids resolve)
9. Slot key enum compliance
10. Status enum compliance (snapshot + fact_table)
11. Doc type enum compliance
12. Excerpt length constraints (25-400 chars)
13. Debug section optional
14. Constitutional compliance matrix
15. Minimum example count (≥4)
16. Required scenario coverage (cancer, borderline, robotic, unmapped)

**Example Scenarios:**
1. **Standard Cancer Diagnosis** (암 진단비): 2 insurers, normal flow
2. **Borderline Tumor** (경계성종양): Definition-based, disease_scope slot
3. **Robotic Surgery** (다빈치 수술비): Method-based, method_condition slot
4. **UNMAPPED Coverage** (신종수술비): Missing canonical code, edge case
5. **Missing Evidence** (심근경색증): Incomplete slot data, policy review needed

**Constitutional Compliance:**
- ✅ Fact-only: All amounts require evidence_ref_id
- ✅ No Recommendation: Forbidden phrases validated (hard ban)
- ✅ Presentation Only: No logic fields (score/rank/judgment)
- ✅ Canonical Coverage: coverage_title_normalized from coverage_standard
- ✅ Coverage Universe Lock: OUT_OF_UNIVERSE status for non-proposal coverages
- ✅ Evidence Rule: evidence_panels required, excerpt minLength=25
- ✅ Deterministic Output: Same input → same JSON structure

**Forbidden Expressions (Hard Ban, Test-Enforced):**
- ❌ "더 좋다", "유리하다", "불리하다"
- ❌ "추천", "권장", "선택하세요"
- ❌ "우수", "뛰어남", "최선"
- ❌ "동일함", "차이 없음"
- ❌ "사실상 같은 담보", "유사한 담보"
- ❌ "종합적으로", "결론적으로"

**Frontend/Backend Contract:**
- Backend: Generates JSON matching this schema
- Frontend: Renders JSON (no processing, display only)
- `debug` section: MUST NOT be displayed in UI
- Column order: Immutable (frontend cannot reorder)
- Reference integrity: All `evidence_ref_id` must resolve

**Version Strategy:**
- `next4.vX`: Breaking changes (add/remove required fields)
- `next4.vX.Y`: Non-breaking (add optional fields)
- Backwards compatibility: Frontend handles unknown optional fields

**DoD Achievement:**
- ✅ `compare_view_model.schema.json` exists (Draft 2020-12)
- ✅ 5 examples validate against schema
- ✅ Forbidden phrase test implemented (detects 15+ patterns)
- ✅ Reference integrity test implemented
- ✅ `debug` excluded from UI rendering contract
- ✅ 16/16 tests passing
- ✅ Constitutional compliance verified

**Next Steps:**
1. Backend API implementation: `/api/compare` ViewModel assembly
2. Frontend component development: 3-Block renderer (React/Vue)
3. Integration with STEP 3.x PRIME comparison results

**Key Principle:**
- **ViewModel = Presentation Layer Contract = Fact-Only = No Judgment**
- **Schema enforces constitutional compliance (automated validation)**
- **Same input → same output structure (deterministic)**

---

### ✅ STEP NEXT-3: UI Layout Specification (ChatGPT-Style MVP)
**Commit:** 1bacd1e | **Date:** 2025-12-26

**Summary:**
- Fixed 3-Block ChatGPT-style UI layout specification for insurance comparison MVP
- Fact-only presentation layer (absolutely no inference, judgment, or recommendations)
- Constitutional compliance enforced (prohibited phrases, canonical coverage rule)
- 8 concrete examples covering standard/edge/special cases

**3-Block Structure (Fixed):**
```
[BLOCK 0] User Query (Chat Header)
[BLOCK 1] Coverage Snapshot
[BLOCK 2] Fact Table (Coverage Comparison)
[BLOCK 3] Evidence Panels (Accordion)
```

**Constitutional Principles (Hard Enforced):**
1. **Fact-only**: All data from document evidence, no inference
2. **No Recommendation**: Absolutely no "better/recommended" language
3. **Presentation Layer Only**: No business logic in UI
4. **Canonical Coverage Rule**: Normalized coverage names in tables

**Block Definitions:**

**BLOCK 0 (User Query):**
- User question displayed exactly as asked (1 line)
- No rephrasing, no internal processing info

**BLOCK 1 (Coverage Snapshot):**
- Normalized coverage name (canonical)
- Insurer list + amounts
- NO comparative judgments ("동일함", "차이 없음" prohibited)

**BLOCK 2 (Fact Table):**
| 보험사 | 담보명(정규화) | 보장금액 | 지급 조건 요약 | 보험기간 | 비고 |

- Slot-based conditions only (waiting_period, payment_frequency, etc.)
- NO sentence rewriting or interpretation
- UNMAPPED/AMBIGUOUS tags in 비고 column

**BLOCK 3 (Evidence Panels):**
- Collapsible per-insurer accordion
- Document type + page + original text span (max 200 chars)
- NO rewriting, NO summarization, NO interpretation

**Special Comparison Cases:**

1. **경계성종양/제자리암/유사암** (Definition-based):
   | 보험사 | 질병 유형 | 보장 여부 | 지급 비율 | 정의 근거 |

2. **다빈치/로봇 수술비** (Method-based):
   | 보험사 | 수술 방식 | 보장 담보 | 금액 | 제한 조건 |

**Edge Cases Handled:**
- UNMAPPED coverage: Tag + "(UNMAPPED)" in 비고
- AMBIGUOUS mapping: Tag + "(AMBIGUOUS - 수동 매핑 필요)"
- Out of Universe: Separate message (no 3-Block rendering)
- Missing evidence: "(근거 없음)" in evidence panel

**Prohibited Expressions (Hard Ban):**
- ❌ "더 좋다", "유리하다", "불리하다"
- ❌ "추천", "권장"
- ❌ "우수", "뛰어남"
- ❌ "동일함", "차이 없음"
- ❌ "A사가 B사보다..."
- ❌ "종합적으로 볼 때..."

**Allowed Expressions (Fact-based):**
- ✅ "대기기간: 90일"
- ✅ "지급 횟수: 최초 1회"
- ✅ "제외 범위: 유사암, 갑상선암"
- ✅ "(약관 확인 필요)"
- ✅ "(UNMAPPED)", "(AMBIGUOUS)"

**Generated Files:**
- `docs/ui/STEP_NEXT3_UI_LAYOUT.md` (full specification with 11 sections)
- `docs/ui/STEP_NEXT3_UI_EXAMPLES.md` (8 concrete examples)

**Examples (8 scenarios):**
1. Standard cancer diagnosis (암 진단비)
2. Borderline tumor (경계성종양) - definition-based table
3. Robotic surgery (다빈치 수술비) - method-based table
4. UNMAPPED coverage (edge case)
5. Out of Universe (edge case)
6. AMBIGUOUS mapping (edge case)
7. Missing evidence (slot unknown)
8. Multiple coverage variants (same canonical)

**Data Flow:**
```
Backend (View Model JSON)
  ↓
Frontend (3-Block Renderer)
  ↓
User Display
```

**Frontend/Backend Separation:**
- Backend: Comparison logic, slot extraction, evidence retrieval, View Model assembly
- Frontend: Rendering only, accordion interaction, NO data processing

**Validation Checklist:**
- ✅ No judgment/recommendation phrases
- ✅ All amounts have evidence
- ✅ No rewriting of original text
- ✅ Canonical coverage names used
- ✅ Prohibited elements (opinion, icon, color) absent
- ✅ 3-Block structure strictly followed

**Constitutional Compliance:**
- ✅ Coverage Universe Lock: BLOCK 2 uses normalized names
- ✅ Document Priority: Evidence panels show doc_type hierarchy
- ✅ Deterministic Output: Same input → same structure
- ✅ No LLM Inference: All text from evidence or slots
- ✅ Presentation Layer Only: Zero business logic in UI

**DoD Achievement:**
- ✅ Fixed 3-Block structure defined
- ✅ 11-section specification document
- ✅ 8 concrete examples (standard + edge + special)
- ✅ Prohibited phrases list (hard ban)
- ✅ Frontend-ready (no ambiguity)
- ✅ Constitutional compliance matrix
- ✅ Ready for STEP NEXT-4 (JSON Schema definition)

**Next Steps:**
1. STEP NEXT-4: JSON Schema Definition (formalize View Model)
2. Backend API Implementation (/api/compare View Model assembly)
3. Frontend Component Development (React/Vue 3-block renderer)

**Key Principle:**
- **UI = View Model = Presentation Layer ONLY**
- **No inference, no judgment, no recommendation, ever.**
- **Same input → same output structure guaranteed.**

---

### ✅ STEP 4.2: Customer Response Enhancement (Structural UNMAPPED Handling)
**Commit:** 00b5c70 | **Date:** 2025-12-26

**Summary:**
- Enhanced STEP 4.0 customer responses with Structural Notice Block
- Made structural UNMAPPED understandable (not system failures)
- Provided honest explanations without inference or recommendations
- **No state changes**: PRIME results preserved, presentation only

**Key Achievement:**
- **Transformed "비교 불가" → "확인 필요"**
- Structural UNMAPPED = designed limitation, not system incompetence

**Message Templates (Fixed):**

| Type | Customer Message |
|------|------------------|
| **S1_SPLIT** | "세부 항목이 나뉘어 기재되어 있어 단순 비교하기 어렵습니다" |
| **S2_COMPOSITE** | "여러 보장 내용을 묶어 제공됩니다. 보장 범위가 보험사마다 다릅니다" |
| **S3_POLICY_ONLY** | "요약 정보만으로는 보장 범위 확정이 어려워 약관 확인 필요합니다" |

**Next Action Options (Non-Recommendations):**
```
□ 특정 하위 담보만 선택해서 보기
□ 가입설계서 상세 보장 내용 확인
□ 약관 기준으로 비교 요청
```

**Display Conditions:**
- PRIME state = `in_universe_with_gaps` OR
- mapping_status = `UNMAPPED` OR
- structural_type ∈ {S1_SPLIT, S2_COMPOSITE, S3_POLICY_ONLY}

**Response Structure (4 sections):**
1. Summary Header (STEP 4.0)
2. Comparison Table (STEP 4.0)
3. Insurer Explanation Blocks (STEP 4.0)
4. **Structural Notice Block** (STEP 4.2 NEW) ← Key Addition

**Generated Files:**
- `scripts/step42_customer_response_enhancer.py`
- `docs/customer_response_examples_step42.md`

**Constitutional Compliance:**
- ✅ PRIME results IMMUTABLE (STEP 3.11 untouched)
- ✅ Explanations IMMUTABLE (STEP 3.12 untouched)
- ✅ Pure presentation layer (no state changes)
- ✅ No forbidden phrases ("사실상 같다", "추천합니다" etc)
- ✅ No inference/recommendations
- ✅ No shinjeongwon code mentions in customer output
- ✅ Deterministic (same input → same output)

**Forbidden Expressions (Hard Ban):**
- ❌ "사실상 같은 담보"
- ❌ "유사한 담보"
- ❌ "일반적으로/보통은"
- ❌ "추천합니다/선택하세요"
- ❌ "더 나은/유리한"
- ❌ "통합하면/거의 동일"

**Allowed Expressions (Fact-based Only):**
- ✅ "세부 항목이 나뉘어 있습니다"
- ✅ "여러 보장을 묶어 제공합니다"
- ✅ "보장 범위가 다릅니다"
- ✅ "요약표 기준입니다"
- ✅ "확인이 필요합니다"

**DoD Achievement:**
- ✅ 100% of structural UNMAPPED cases show Structural Notice
- ✅ Zero forbidden phrases in customer output
- ✅ Zero PRIME state/mapping result changes
- ✅ Deterministic output (pure function)
- ✅ "System incompetence" perception eliminated

**Customer Perception Shift:**
- **Before**: "왜 비교가 안돼? 시스템이 이것도 못해?"
- **After**: "아, 담보 구성이 다르구나. 상세하게 볼 수 있네."

**Integration:**
```python
# STEP 4.0 → STEP 4.2 enhancement
enhanced = enhance_customer_response(base_response, comparison_results)

# No structural issues: enhanced == base (pass-through)
# Structural issues exist: enhanced = base + notice_block
```

---

### ✅ STEP 3.10-θ: Structural UNMAPPED Strategy (C3/C4/C7 Processing)
**Commit:** 9160027 | **Date:** 2025-12-26

**Summary:**
- Identified and classified 10 structural UNMAPPED cases (out of 19 total UNMAPPED)
- All structural cases assigned S1/S2/S3 types + NextActions
- Generated backlog for future detailed table / policy layer work
- **No state changes**: PRIME results preserved, no UNMAPPED → MAPPED conversion

**Structural Type Distribution:**

| Type | Count | Percentage | Description |
|------|-------|------------|-------------|
| **S1_SPLIT** | 5 | 50.0% | Subcategory split (C3) |
| **S2_COMPOSITE** | 5 | 50.0% | Composite coverage (C4) |
| **S3_POLICY_ONLY** | 0 | 0.0% | Policy-level only (C7) |
| **TOTAL** | 10 | 100.0% | |

**Per-Insurer Breakdown:**

| Insurer | Total | S1 | S2 | S3 |
|---------|-------|----|----|-----|
| HANWHA | 7 | 2 | 5 | 0 |
| KB | 2 | 2 | 0 | 0 |
| SAMSUNG | 1 | 1 | 0 | 0 |

**Group Key Success:**
- Generated: 10/10 (100.0%)
- All structural cases successfully labeled

**NextAction Distribution:**

| Action | Count | Description |
|--------|-------|-------------|
| A1_CREATE_GROUP_KEY | 10 | Labeling for comparison grouping |
| A2_REQUIRE_USER_DISAMBIGUATION | 10 | User query refinement needed |
| A3_DEFER_TO_DETAIL_TABLE | 5 | Detailed table parser (STEP 4.x) |
| A4_DEFER_TO_POLICY_LAYER | 0 | Policy document analysis |
| A5_MANUAL_REVIEW_QUEUE | 0 | Human structure definition |

**Remaining UNMAPPED Analysis:**
- Total UNMAPPED: 19 (from η-2)
- Structural (C3/C4/C7): 10 (52.6%) - **processed in θ**
- Non-structural: 9 (47.4%) - **true gaps / insurer-specific**

**Generated Files:**
- `data/step310_mapping/structural_unmapped/STRUCTURAL_UNMAPPED_CASES.csv`
- `data/step310_mapping/structural_unmapped/STRUCTURAL_UNMAPPED_SUMMARY.md`
- `data/step310_mapping/structural_unmapped/STRUCTURAL_BACKLOG.md`

**Script:**
- `scripts/step310_theta_structural_unmapped.py`

**Backlog for Future Steps:**
1. **High Priority**: A3 - Detailed table parser (enables S2_COMPOSITE resolution)
2. **Medium Priority**: A2 - Query refinement (improves UX for S1_SPLIT cases)
3. **Medium Priority**: A4 - Policy layer (for S3_POLICY_ONLY if any emerge)
4. **Low Priority**: A5 - Manual review (case-by-case)

**Constitutional Compliance:**
- ✅ No UNMAPPED → MAPPED conversion
- ✅ No shinjeongwon code inference
- ✅ No coverage consolidation
- ✅ No similarity/embedding/LLM
- ✅ PRIME state unchanged
- ✅ Backlog only (no actual policy reading)
- ✅ Group keys = labels only (not integration)

**DoD Achievement:**
- ✅ All C3/C4/C7 cases extracted from eta2 UNMAPPED
- ✅ All cases assigned structural_type (S1/S2/S3)
- ✅ All cases assigned next_actions (100%)
- ✅ STRUCTURAL_UNMAPPED_CASES.csv + 2 MD reports generated
- ✅ PRIME results preserved (non-destructive)
- ✅ Reproducibility guaranteed (deterministic classification)

**Key Insight:**
- Structural UNMAPPED (10/19) require **system enhancement**, not Excel additions
- Non-structural UNMAPPED (9/19) are **true coverage gaps** or insurer-specific unique products
- No further UNMAPPED→MAPPED conversions possible without detailed table parser

---

### ✅ STEP 3.10-η-2: Forced Remapping with Enhanced Excel (Reproducibility Locked)
**Commit:** 2769542 | **Date:** 2025-12-26

**Summary:**
- Forced re-execution of STEP 3.10-2 mapping logic
- Used enhanced Excel (`담보명mapping자료__inscd_patched_plus.xlsx`) as input
- Generated new mapping results with __eta2 suffix
- **Proved η enhancement effectiveness with numbers**

**Results (Numbers Only):**

| Status | ζ (Baseline) | η-2 (Enhanced) | Change |
|--------|--------------|----------------|--------|
| **MAPPED** | 259 (77.54%) | **315 (94.31%)** | **+56** |
| **UNMAPPED** | 75 (22.46%) | **19 (5.69%)** | **-56** |
| **AMBIGUOUS** | 0 (0.00%) | 0 (0.00%) | 0 |
| **TOTAL** | 334 | 334 | 0 |

**Key Metrics:**
- MAPPED improvement: **+56 entries** (116.7% of 48 Excel additions)
- UNMAPPED reduction: **-56 entries** (74.7% reduction)
- Final MAPPED ratio: **94.31%** (exceeds 85% target ✅)
- DB & LOTTE: **100% MAPPED** 🎉

**Per-Insurer Results:**
| Insurer | MAPPED | UNMAPPED | Ratio |
|---------|--------|----------|-------|
| DB | 62 | 0 | 100.0% ✅ |
| LOTTE | 70 | 0 | 100.0% ✅ |
| SAMSUNG | 40 | 1 | 97.6% |
| MERITZ | 32 | 2 | 94.1% |
| HYUNDAI | 25 | 2 | 92.6% |
| HEUNGKUK | 21 | 2 | 91.3% |
| KB | 35 | 5 | 87.5% |
| HANWHA | 30 | 7 | 81.1% |

**Generated Files:**
- New mapping CSV: `proposal_coverage_mapping_insurer_filtered__eta2.csv`
- Comparison report: `mapping_report_insurer_filtered__eta2.md`
- Reproducibility doc: `EXCEL_REPRODUCE_INSTRUCTIONS.md`

**Script:**
- `scripts/step310_eta2_forced_remapping.py`

**Reproducibility Lock:**
- ✅ Enhanced Excel regeneration path documented
- ✅ Complete reproduction instructions provided
- ✅ Same input → same output guaranteed

**Constitutional Compliance:**
- ✅ Mapping logic unchanged (STEP 3.10-2 as-is)
- ✅ Enhanced Excel as sole input
- ✅ No rule modifications
- ✅ Deterministic execution
- ✅ Numbers-only proof (no claims without data)

**DoD Achievement:**
- ✅ Enhanced Excel-based remapping complete
- ✅ Before/after metrics reported (numbers only)
- ✅ Excel reproducibility path fixed
- ✅ Reproducibility guaranteed
- ✅ UNMAPPED reduction proven (+56 MAPPED)
- ✅ 94.31% MAPPED ratio achieved (target: ≥85%)

**Effectiveness Proof:**
- 48 Excel rows added → 56 new MAPPED entries
- Conversion rate: 116.7% (some rows matched multiple proposals)
- Zero AMBIGUOUS maintained throughout

---

### ✅ STEP 3.10-η: Excel Enhancement - UNMAPPED Backlog Processing
**Commit:** cde40d8 | **Date:** 2025-12-26

**Summary:**
- Processed UNMAPPED backlog from STEP 3.10-γ
- Added 48 new mapping rows to Excel (qualified ADD targets)
- Deferred 19 structural cases to STEP 3.10-θ
- Generated enhanced Excel: `담보명mapping자료__inscd_patched_plus.xlsx`

**Processing Rules:**
- ✅ ADD_EXCEL_ROW: immediate processing (C1/C2/C6 causes only)
- ✅ ADD_EXCEL_ROW_WITH_NOTE: with annotation
- ❌ STRUCTURAL cases deferred (C3/C4/C7)

**Enhancement Results:**
- Total backlog items: 67
- Processed (added): 48 (71.6%)
- Deferred: 19 (28.4%)
- Processing rate: 71.6%

**Current Mapping Status:**
- MAPPED: 259 (77.54%)
- UNMAPPED: 75 (22.46%)
- AMBIGUOUS: 0 (0.00%) ✅

**Per-Insurer Additions:**
| Insurer | Added Rows |
|---------|------------|
| N01 (SAMSUNG) | 8 |
| N02 (HANWHA) | 2 |
| N03 (LOTTE) | 7 |
| N04 (MERITZ) | 11 |
| N05 (KB) | 7 |
| N06 (HYUNDAI) | 7 |
| N07 (HEUNGKUK) | 3 |
| N08 (DB) | 3 |

**Generated Files:**
- `data/담보명mapping자료__inscd_patched_plus.xlsx` (enhanced Excel)
- `data/step310_mapping/excel_enhancement/ENHANCEMENT_LOG.csv`
- `STEP310_ETA_EXCEL_ENHANCEMENT_REPORT.md`
- `STEP310_ETA_FINAL_METRICS_REPORT.md`

**Scripts:**
- `scripts/step310_eta_excel_enhancement.py`
- `scripts/step310_eta_simple_metrics.py`

**Constitution Compliance:**
- ✅ Single Source of Truth: Excel remains canonical mapping authority
- ✅ No LLM Inference: All mappings deterministic (Excel lookup only)
- ✅ Coverage Universe Lock: All proposals remain in universe
- ✅ Evidence Rule: All additions traceable to backlog analysis
- ❌ No coverage code inference
- ❌ No structural assumptions

**DoD Achievement:**
- ✅ ADD-qualified backlog 100% processed (48/48)
- ✅ STRUCTURAL cases 0% processed (deferred as intended: 19/19)
- ✅ Enhanced Excel generated
- ✅ Enhancement logs generated
- ⚠️ MAPPED ratio 77.54% < 85% target (expected - full pipeline re-run needed)
- ✅ AMBIGUOUS = 0 maintained
- ✅ Git commit complete (cde40d8)

**Next Steps:**
1. STEP 3.10-θ: Handle 19 deferred structural cases
2. Full pipeline re-run with enhanced Excel to measure actual MAPPED improvement
3. Admin UI for any remaining manual resolutions

---

### ✅ STEP 3.10-ζ: ins_cd Patched Excel + Re-run Complete
**Commits:** 2cecda1, efa43b2 | **Date:** 2025-12-26

**Summary:**
- ins_cd 자동 정합화 패치본 Excel 생성 (비파괴)
- STEP 3.10-2/β/γ 패치본 기준 재실행
- I3_MISMATCH_PIPELINE_VS_EXCEL: 6 → 0 ✅
- AMBIGUOUS mappings: 129 → 0 ✅

**Patch Results:**
- Original Excel preserved: `data/담보명mapping자료.xlsx` (read-only)
- Patched Excel generated: `data/담보명mapping자료__inscd_patched.xlsx`
- Total affected rows: 194/264 (73.5%)
- ins_cd corrections: 6 insurers (DB, KB, 메리츠, 삼성, 현대, 흥국)

**Validation:**
- ✅ ins_cd-only changes verified
- ✅ ins_cd uniqueness per insurer verified
- ✅ I3_MISMATCH_PIPELINE_VS_EXCEL = 0
- ✅ Row count preserved (264 rows)

**Re-run Results:**
1. **STEP 3.10-2** (Insurer-Filtered Mapping):
   - MAPPED: 259 (77.5%)
   - AMBIGUOUS: 0 (0.0%) ← 129 → 0 (100% reduction)
   - UNMAPPED: 75 (22.5%)

2. **STEP 3.10-β** (UNMAPPED Cause-Effect):
   - Total UNMAPPED analyzed: 75
   - Cause-effect classifications complete

3. **STEP 3.10-γ** (Excel Backlog):
   - Unique backlog items: 67
   - Per-insurer backlog CSVs generated

**Generated Files:**
- `data/담보명mapping자료__inscd_patched.xlsx`
- `data/step310_mapping/ins_cd_patch/PATCH_LOG.csv`
- `data/step310_mapping/ins_cd_patch/PATCH_SUMMARY.md`
- `data/step310_mapping/ins_cd_patch/VERIFICATION_REPORT.md`
- All STEP 3.10-2/β/γ reports regenerated

**Scripts:**
- `scripts/step310_zeta_patch_inscd.py`
- `scripts/step310_zeta_verify.py`
- `scripts/step310_2_insurer_filtered_mapping.py` (updated)
- `scripts/step310_beta_unmapped_analysis.py` (updated)

**Constitution Compliance:**
- ✅ Original Excel preserved (non-destructive)
- ✅ ins_cd-only changes (deterministic)
- ✅ Pipeline canonical ins_cd as ground truth
- ✅ Verification script confirms I3 = 0
- ❌ No coverage code inference
- ❌ No mapping logic changes

**DoD Achievement:**
- ✅ Patched Excel generated
- ✅ Patch logs generated
- ✅ I3 mismatch = 0 achieved
- ✅ STEP 3.10-2/β/γ re-run complete
- ✅ Git commits complete
- ✅ STATUS.md updated

---

### ✅ STEP 3.10-ε: ins_cd Consistency Audit
**Commit:** 9b08c86 | **Date:** 2025-12-25

**Summary:**
- 전 보험사 ins_cd 정합성 자동 감사 (3자 교차검증)
- Excel/Pipeline/Proposal 간 ins_cd 불일치 감지
- 6/8 보험사에서 mismatch 발견 (75% 불일치율)
- 감사 리포트만 생성 (수정 없음)

**Purpose:**
- Cross-validate ins_cd consistency across Excel/Pipeline/Proposal
- Detect mismatches, collisions, missing mappings
- Generate audit reports (NO fixes)

**3-Way Cross-Validation:**
1. **Excel**: 담보명mapping자료.xlsx (보험사명 → ins_cd)
2. **Pipeline**: INSURER_NAMES registry (INSURER → ins_cd)
3. **Proposal**: ALL_INSURERS_coverage_universe.csv (insurer existence)

**Audit Results:**
- Total insurers audited: 8
- Insurers OK: 2 (HANWHA, LOTTE)
- Insurers with issues: 6 (75%)

**Issue Breakdown:**
- **I3_MISMATCH_PIPELINE_VS_EXCEL**: 6 cases
  - DB: Pipeline N08 ≠ Excel N13
  - HEUNGKUK: Pipeline N07 ≠ Excel N05
  - HYUNDAI: Pipeline N06 ≠ Excel N09
  - KB: Pipeline N05 ≠ Excel N10
  - MERITZ: Pipeline N04 ≠ Excel N01
  - SAMSUNG: Pipeline N01 ≠ Excel N08

**Recommended Fix:**
- **Excel 수정 대상**: 6 insurers
- All recommended_fix_target = **EXCEL**
- 권장: Excel 담보명mapping자료.xlsx의 ins_cd 값을 Pipeline 기준으로 정정

**Generated Reports:**
1. CSV: `data/step310_mapping/ins_cd_audit/ins_cd_audit_table.csv`
   - Per-insurer audit results
2. MD: `data/step310_mapping/ins_cd_audit/INSCD_AUDIT_REPORT.md`
   - Summary + Top 5 critical issues + recommendations
3. JSON: `data/step310_mapping/ins_cd_audit/ins_cd_audit_findings.json`
   - Machine-readable findings

**Constitution Compliance:**
- ✅ 3-way cross-validation (deterministic)
- ✅ 7 fixed issue codes (I1-I7)
- ✅ Audit reports only (no modifications)
- ❌ No Excel/code modifications
- ❌ No ins_cd inference/auto-correction

**DoD:**
- ✅ All insurers (8) audited
- ✅ CSV/MD/JSON reports generated
- ✅ Issue classification 100% applied
- ✅ No Excel/code modifications
- ✅ Reproducible audit

**Next Step:**
- STEP 3.10-ζ: Excel ins_cd correction (based on audit findings)

---

### ✅ STEP 3.10-γ: Excel Backlog Generator
**Commit:** f076b87 | **Date:** 2025-12-25

**Summary:**
- Excel 보강 작업 목록 생성 (UNMAPPED → Backlog)
- 보험사별 backlog CSV (8개 파일)
- 수학적 우선순위 (occurrence_count DESC)
- 규칙 기반 recommended_action 분류

**Purpose:**
- Generate actionable Excel backlog for UNMAPPED coverages
- Per-insurer work lists (NO mapping changes)
- Prepare for STEP 3.10-δ (Excel enhancement)

**Processing Logic:**
1. Aggregate UNMAPPED by insurer + coverage_name_raw
2. Count occurrences
3. Classify recommended_action (rule-based)
4. Sort by priority (occurrence_count DESC)

**Recommended Action Classification (Rule-Based):**
- **ADD_EXCEL_ROW**: C1, C2, C6 포함 (단순 추가 가능)
- **STRUCTURAL_REVIEW**: C3, C4, C7 포함 (구조적 검토 필요)
- **ADD_EXCEL_ROW_WITH_NOTE**: 혼합 (추가 가능하나 주의 필요)

**Results:**
- Total backlog items: 157 (from 191 UNMAPPED rows)
- Per-insurer breakdown:
  - DB: 29 items (110 occurrences)
  - SAMSUNG: 37 items (37 occurrences)
  - LOTTE: 7 items (28 occurrences)
  - HYUNDAI: 27 items (27 occurrences)
  - HEUNGKUK: 23 items (23 occurrences)
  - MERITZ: 13 items (13 occurrences)
  - KB: 12 items (12 occurrences)
  - HANWHA: 9 items (9 occurrences)

**Generated Files:**
1. Per-insurer backlog CSVs: `data/step310_mapping/excel_backlog/backlog_{ins_cd}_{INSURER}.csv`
   - Schema: ins_cd, insurer_name, coverage_name_raw, occurrence_count, cause_codes, effect_codes, recommended_action, notes
2. Summary report: `data/step310_mapping/STEP310_GAMMA_EXCEL_BACKLOG_SUMMARY.md`
   - Per-insurer totals
   - Top 10 backlog per insurer
   - Expansion candidates vs structural review split
   - Expected impact (quantitative)

**Expected Impact:**
- ADD_EXCEL_ROW/WITH_NOTE: 157 items → Excel 보강으로 해소 가능
- STRUCTURAL_REVIEW: 9 items (별도 전략 필요)
- Excel 보강만으로 해소 가능: ~94.3%

**Constitution Compliance:**
- ✅ UNMAPPED → Backlog (no state change)
- ✅ Rule-based recommended_action (deterministic)
- ✅ Mathematical priority (occurrence count)
- ✅ NO UNMAPPED → MAPPED conversion
- ❌ No inference/semantic judgment
- ❌ No Excel modification

**DoD:**
- ✅ All UNMAPPED (191) → backlog items (157 unique)
- ✅ Per-insurer backlog CSVs (8 files)
- ✅ recommended_action 100% assigned
- ✅ No judgment/inference sentences
- ✅ Reproducible (same input → same backlog)
- ✅ Ready for STEP 3.10-δ

---

### ✅ STEP 3.10-β: UNMAPPED Cause-Effect Analysis
**Commit:** d42289f | **Date:** 2025-12-25

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


### ✅ STEP NEXT-10-β: ViewModel Assembler v2 + Example E2E Tests (Complete)
**Commit:** [pending] | **Date:** 2025-12-26

**Summary:**
- ViewModel Assembler v2 구현 (schema v2 필드 지원)
- Forbidden Phrase Guard 테스트 추가
- Example 1-4 E2E 테스트 추가
- 모든 테스트 통과 (12 passed)

**목적:**
- LOCKED ViewModel schema v2(Commit 1f85282)를 실제 런타임 산출물로 구현
- 추천/우열/해석/추론 문구 생성 차단 (테스트 기반)
- INCA DIO 요구사항(Example 1-4) E2E 검증

**주요 변경 사항:**

1. **ViewModel Types 확장 (schema v2)**
   - `FilterCriteria`: insurer_filter, disease_scope, slot_key, difference_detected
   - `SortMetadata`: sort_by, sort_order, limit (UI hint)
   - `VisualEmphasis`: min_value_style, max_value_style (UI hint)
   - `FactTableRow.highlight`: 차이 감지 셀 강조 (fact-only)
   - `FactTable.table_type`: default | ox_matrix

2. **Assembler v2 구현**
   - 파일: `apps/api/app/view_model/assembler.py`
   - v2 필드는 optional, 필요시에만 채움
   - schema_version = "next4.v2"
   - 기존 assembler 기능 유지 (non-breaking)

3. **Forbidden Phrase Guard**
   - 파일: `tests/test_next10_forbidden_phrases.py`
   - 정규식 기반 금지 표현 검증
   - 추천/우열/해석/추론 문구 감지
   - 도메인 용어 예외 처리 ("유사암" 허용)

4. **Example 1-4 E2E Tests**
   - 파일: `tests/test_next10_examples_e2e.py`
   - Example 1: 보험료 정렬 비교
   - Example 2: 보장한도 차이 감지
   - Example 3: 특정 보험사 비교
   - Example 4: 질병별 O/X 매트릭스
   - Schema v2 검증 + Forbidden Phrase Guard

**테스트 결과:**
```
tests/test_next10_examples_e2e.py: 5 passed
tests/test_next10_forbidden_phrases.py: 7 passed
Total: 12 passed, 32 warnings (pydantic deprecation)
```

**Constitutional Compliance:**
- ✅ Article II: Deterministic Compiler (assembler는 매핑만, 추론 금지)
- ✅ Article III: Evidence Rule (모든 값에 evidence_ref_id)
- ✅ 금지 사항 준수 (추천/우열/해석/추론 문구 생성 금지)
- ✅ Schema v2 준수 (JSON Schema validation)

**DoD (Definition of Done):**
- [x] Assembler가 schema v2 ViewModel을 실제로 생성
- [x] forbidden phrase 테스트가 통과
- [x] Example 1~4 E2E 테스트 통과
- [x] git commit + push 완료
- [x] STATUS.md에 NEXT-10-β 반영

**다음 단계:**
- UI/비교 구조 고정 후 보험료 기능 설계 (data/호출_api/ 연결)
- Query Parser 구현 (filter_criteria 자동 채우기)
- Comparison Engine 개선 (table_type 자동 선택)

---
