# inca-RAG-final Project Status

**Last Updated:** 2025-12-26
**Current Phase:** STEP NEXT-12A (E2E Lock with Playwright)
**Project Health:** ✅ ACTIVE

---

## Quick Overview

**inca-RAG-final** = Proposal-centered insurance comparison RAG system
**Repository:** [GitHub - inca-rag-final](https://github.com/jason-dio-so/inca-rag-final)

**Core Principles:**
- Proposal-centered (not policy-centered)
- Coverage Universe Lock (가입설계서 = SSOT)
- Deterministic extraction (no LLM inference)
- Evidence-based everything

**Key Documents:**
- [CLAUDE.md](CLAUDE.md) - Project Constitution
- [data/inca-dio.pdf](data/inca-dio.pdf) - Customer Requirements SSOT

---

## Latest Work (Last 7 Days)

### 2025-12-26

#### ✅ STEP NEXT-12A: Automated E2E Lock with Playwright
**Commit:** 4f3308f
**Summary:** Playwright 자동화 E2E 테스트 (Example 1-4, Forbidden phrases 검증)
**DoD:** ✅ Pass

**Key Changes:**
- Playwright setup (apps/web/playwright.config.ts)
- E2E test suite (apps/web/e2e/compare-live.spec.ts)
- 6 tests: Example 1-4 + Evidence + Error handling
- Forbidden phrases auto-check
- CI/CD ready

**Usage:**
```bash
cd apps/web && npm run test:e2e
```

---

#### ✅ STEP NEXT-12: Real API → UI E2E Lock
**Commit:** de845cf
**Summary:** ChatGPT 스타일 실시간 비교 UI (/compare-live)
**DoD:** ✅ Pass

**Key Changes:**
- ChatGPT style live UI (apps/web/src/pages/compare-live.tsx)
- Real API integration (POST /compare/view-model)
- E2E manual test checklist (docs/testing/E2E_MANUAL_TEST_CHECKLIST.md)
- Test data setup guide (docs/testing/TEST_DATA_SETUP.md)

**Usage:**
```bash
open http://localhost:3000/compare-live
```

---

#### ✅ STEP NEXT-11: Frontend Renderer v2 + Example Fixtures
**Commit:** 4f54125
**Summary:** ViewModel v2 렌더러 구현 + Example 1-4 픽스처
**DoD:** ✅ Pass

**Key Changes:**
- CompareViewModelRenderer.tsx (ViewModel v2 fields)
- O/X Matrix Table Renderer (table_type=ox_matrix)
- Example 1-4 fixtures (apps/web/src/fixtures/example-viewmodels.ts)
- Examples test page (http://localhost:3000/examples-test)

---

#### ✅ STEP NEXT-10B: ViewModel Assembler v2 + Example E2E Tests
**Commit:** c368be9
**Summary:** ViewModel 조립 로직 + Example 1-4 E2E 테스트
**DoD:** ✅ Pass

**Key Changes:**
- apps/api/app/view_model/assembler_v2.py
- apps/api/tests/e2e/test_examples_1_4.py
- Example 1-4 golden snapshots (docs/design/next-10/examples/)

---

#### ✅ STEP NEXT-10: ViewModel Schema v2 Lock
**Commit:** 91386bf
**Summary:** ViewModel v2 스키마 확정 (filter_criteria, sort_metadata, table_type)
**DoD:** ✅ Pass

**Key Changes:**
- docs/design/next-10/VIEW_MODEL_SCHEMA_V2.md
- Example 1-4 정의 (inca-dio.pdf 기반)
- Implementation plan

---

### 2025-12-25

#### ✅ STEP NEXT-9: Documentation Complete (INCA DIO Requirements Lock)
**Summary:** data/inca-dio.pdf 기반 요구사항 분석 완료
**DoD:** ✅ Pass

**Deliverables:**
- INCA_DIO_REQUIREMENTS.md (FAQ ①⑦, Example 14 분석)
- NEXT_STEPS.md (NEXT-10~13 roadmap)
- Evidence: inca-dio.pdf page 3-4

---

#### ✅ STEP NEXT-8B: CLAUDE.md Consistency Recovery
**Summary:** CLAUDE.md 정합성 회복 (본문 ↔ Decision Change Log 일치)
**DoD:** ✅ Pass

**Key Changes:**
- 금지 사항 재구조화 (15개 항목, UI/응답 레벨 추가)
- Deterministic Compiler 전 구간 확장
- Decision Change Log 추가 (2025-12-26 변경 7건)

---

#### ✅ STEP NEXT-8A: SSOT Entry Point Lock
**Summary:** CLAUDE.md = 유일한 실행 헌법, inca-dio.pdf = 요구사항 SSOT
**DoD:** ✅ Pass

**Key Changes:**
- 🔴 SSOT ENTRY POINT 섹션 추가
- data/호출_api/ 명시적 보류 (보험료 기능 단계 전까지)
- ChatGPT UI 목표 고정 (좌: 질의 / 우: 근거 패널)

---

### 2025-12-24 and Earlier

**Completed Phases:**
- ✅ STEP 5-A/B/C: FastAPI + Read-Only + Conditions Summary
- ✅ STEP 6-A/B: LLM Ingestion Design + Implementation
- ✅ STEP 6-C: Proposal Universe Lock (E2E Functional)
- ✅ STEP NEXT-3~7: UI Layout + ViewModel + Clarify Panel + Admin Mapping Workbench

**Details:** See [docs/status/STATUS-251201-251226.md](docs/status/STATUS-251201-251226.md)

---

## Current System State

**Branch:** main
**Backend:** FastAPI (apps/api/, port 8001)
**Frontend:** Next.js (apps/web/, port 3000)

**Key Modules:**
- `apps/api/app/` - FastAPI backend (/compare endpoint)
- `apps/web/src/` - Next.js frontend (ChatGPT-style UI)
- `apps/api/app/compiler/` - Deterministic compiler
- `apps/api/app/view_model/` - ViewModel assembler v2
- `apps/api/app/admin_mapping/` - Admin mapping workbench

**Test Pages:**
- http://localhost:3000/examples-test (Fixture-based)
- http://localhost:3000/compare-live (Real API-based)

**E2E Tests:**
```bash
cd apps/web && npm run test:e2e
```

---

## Next Steps

**Immediate:**
- Query Parser 구현 (filter_criteria 자동 채우기)
- Comparison Engine 개선 (table_type 자동 선택)

**After UI/비교 구조 고정:**
- 보험료 기능 설계 (data/호출_api/ 연결)

**Reference:**
- [NEXT_STEPS.md](docs/design/next-9/NEXT_STEPS.md)
- [inca-dio.pdf](data/inca-dio.pdf)

---

## Archive

**Detailed History:**
- [STATUS-251201-251226.md](docs/status/STATUS-251201-251226.md) - Full work log (Dec 1-26, 2025)

---

## Constitutional Compliance

All work follows [CLAUDE.md](CLAUDE.md) principles:
- ✅ No LLM inference for mappings
- ✅ Excel-only canonical coverage code
- ✅ Proposal = Universe SSOT
- ✅ Evidence-based everything
- ✅ No recommendation/judgment/interpretation in UI

**Decision Change Log:** See CLAUDE.md § Decision Change Log

---

**Document Status:** Active (Summary format since 2025-12-26)
