# inca-RAG-final Project Status

**Last Updated:** 2025-12-26
**Current Phase:** STEP NEXT-AE (Coverage 조건/정의 Evidence 연결 완료)
**Project Health:** ✅ ACTIVE

---

## 🔒 STATUS 운영 규칙
- 본 파일은 **최근 7일 요약판**이다.
- 각 작업 완료 시 **최대 5~10줄만** 기록한다.
- 상세 이력은 `docs/status/` 하위 아카이브 문서를 참조한다.
- **본 파일은 SSOT가 아니다** (SSOT: CLAUDE.md, docs/CONTEXT_PACK.md, docs/CUSTOMER_UI_SPEC.md)

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

#### ✅ STEP NEXT-AE: Coverage 조건/정의 Evidence 연결 (본단계)
**Commit:** (pending)
**Summary:** Coverage별 조건/정의/증거 데이터 구조 완성. Universe → Mapping → Evidence E2E 연결 검증 완료.
**DoD:** ✅ Pass

**Deliverables:**
- migrations/step_next_ae/001_create_coverage_evidence.sql (v2.coverage_evidence 테이블)
- v2.coverage_evidence: 3 sample evidence records (CA_DIAG_GENERAL: definition, payment_condition, exclusion)

**Validation:**
- ✅ v2.coverage_evidence schema created (17 columns, 6 indexes, FK constraints)
- ✅ E2E connection: Universe (proposal_coverage) → Mapping (coverage_mapping) → Evidence (coverage_evidence)
- ✅ Sample evidence: CA_DIAG_GENERAL (1 coverage × 3 evidence types)

**Note:** Full policy extraction은 별도 STEP으로 진행 (본 단계는 schema + framework 완성)

---

#### ✅ STEP NEXT-AE-0: 신정원 통일코드 SSOT 로드 (Gate)
**Commit:** d6950ae
**Summary:** 신정원 통일코드 28개 로드 완료. v2.coverage_standard = SSOT 고정. AE 본단계 진입 가능.
**DoD:** ✅ Pass

**Deliverables:**
- apps/api/scripts/ae0_load_coverage_standard.py (Excel → DB loader + FK validator)
- v2.coverage_standard: 31 rows (28신정원 codes from Excel + 3 existing)

---

#### ✅ STEP NEXT-AD-FIX: 신정원 통일코드 강제 검증
**Commit:** 946e9c6
**Summary:** Universe → Coverage mapping은 반드시 신정원 통일코드로만 이루어진다. 임의 코드 제거 완료.
**DoD:** ✅ Pass

**Changes:**
- import_universe_mapping_xlsx.py: Rule 6 추가 (신정원 코드 검증 필수)
- smoke_v2.sh Test 7: 신정원 코드 기준 검증 (arbitrary code 감지)
- v2.coverage_mapping: 3 valid신정원 mappings (CA_DIAG_GENERAL, CA_DIAG_SIMILAR)

---

#### ✅ STEP NEXT-AD: Coverage Mapping (DB-First, XLSX Import)
**Commit:** e10b508
**Summary:** Universe → Canonical 매핑 (DB SSOT, XLSX I/O medium)
**DoD:** ✅ Pass (형식만, 내용은 NEXT-AD-FIX에서 수정)

**Deliverables:**
- v2.coverage_mapping table
- apps/api/scripts/export_universe_for_mapping.py
- apps/api/scripts/import_universe_mapping_xlsx.py
- smoke_v2.sh: Test 7 (Coverage Mapping validation)

---

#### ✅ STEP NEXT-AC: Universe Lock + Structure Contract (No Mapping)
**Commit:** fbbe28b
**Summary:** Universe 품질 고정 (SSOT 적격 행 분류) + 구조 계약 문서화
**DoD:** ✅ Pass

**Deliverables:**
- v2.proposal_coverage_universe_lock table (29 UNIVERSE_COVERAGE, 3 NON_UNIVERSE_META)
- apps/api/scripts/universe_lock_v2_stage1.py (deterministic classifier)
- docs/db/provenance/STRUCTURE_CONTRACT_SAMSUNG_2511.md
- docs/db/provenance/NEXT_AC_UNIVERSE_LOCK_REPORT.md

**Validation:**
- ✅ Universe Lock: 29 SSOT-eligible rows
- ✅ Raw data preserved (v2.proposal_coverage unchanged)
- ✅ Re-run idempotent (same classification)
- ✅ smoke_v2.sh PASSED
- ✅ Legacy public schema write: 0

---

#### ✅ STEP NEXT-AB (FINAL): v2 Proposal Ingestion Stage-1 (Structure-First)
**Commit:** 30be125
**Summary:** Structure-First Universe 추출 (pdfplumber 테이블 구조 기반)
**DoD:** ✅ Pass

**Deliverables:**
- apps/api/scripts/ingest_v2_proposal_stage1.py (structure-first rewrite)
- v2.template: +1 (Samsung proposal, extraction_method: structure_first_v1)
- v2.proposal_coverage: 32 rows (29 success, 3 partial)

**Validation:**
- ✅ v2.proposal_coverage: 32 rows (table structure extraction)
- ✅ Amount parsing: 29/32 success (3,000만원 → 30000000)
- ✅ Payout unit: 만원/원 구분 정상
- ✅ smoke_v2.sh PASSED
- ✅ Legacy public schema: 0 writes

**Constitutional Compliance:**
- ✅ PDF = Layout Document (not text)
- ✅ Table structure first, content second
- ✅ NO text keyword search
- ✅ NO LLM-based extraction
- ✅ NO normalization/mapping

---

#### ✅ STEP NEXT-AA-FIX: v2 Schema Idempotency + Smoke Hard Pass
**Commit:** (pending)
**Summary:** schema_v2.sql 완전 idempotent 보장 + smoke_v2.sh repo root 1회 통과
**DoD:** ✅ Pass

**Changes:**
- schema_v2.sql: CREATE IF NOT EXISTS (모든 TYPE/TABLE/INDEX/TRIGGER)
- ON_ERROR_STOP=1 2회 연속 실행 ERROR 0건
- smoke_v2.sh: repo root 기준 경로 수정 + 1회 완주 PASS

**Validation:**
- ✅ schema_v2.sql 재실행 idempotent (ERROR 0)
- ✅ smoke_v2.sh PASSED (5 tests, API test skipped)

---

#### ✅ STEP NEXT-AA: Apply v2 Schema + SSOT Seed + API Read Path Switch
**Commit:** (pending)
**Summary:** v2 schema 실제 DB 적용 + SSOT seed (8 insurer) + API search_path v2 전환
**DoD:** ✅ Pass

**Deliverables:**
- v2 schema applied to DB (13 tables)
- SSOT seed: 8 insurers, 2 products, 2 templates
- apps/api/app/db.py: search_path = v2, public (v2 우선)
- db_doctor.py: v2 schema 검증 추가
- smoke_v2.sh: v2 기본 검증 스크립트

**Validation:**
- ✅ v2.insurer: 8 rows (SAMSUNG, MERITZ, KB, HANA, DB, HANWHA, LOTTE, HYUNDAI)
- ✅ product_id SSOT format: {insurer_code}_{internal_product_code}
- ✅ API read path uses v2 schema priority

---

#### ✅ STEP NEXT-Z: New Schema v2 Bootstrap
**Commit:** (pending)
**Summary:** SSOT 기반 v2 schema 설계 완료 (insurer enum + product_id + template_id)
**DoD:** ✅ Pass

**Deliverables:**
- docs/db/schema_v2.sql (실행 가능 DDL, v2 schema 분리)
- docs/db/V2_TABLE_MAP_PROPOSAL.md (추출→테이블 매핑 규칙)
- docs/db/LEGACY_FREEZE_PLAN.md (public schema READ-ONLY 동결 계획)

**Key Changes:**
- DB 분리 전략: A안 (같은 DB 내 schema 분리, public vs v2)
- Legacy public schema: READ-ONLY audit trail 동결 (DROP 금지)
- v2 schema: insurer 8-enum, product_id (insurer+code), template_id (product+version+fingerprint)

---

#### ✅ STEP NEXT-Y: Provenance Audit + Route Alignment
**Commit:** (pending)
**Summary:** DB/Container/Repo 완전 provenance 분석 + SSOT 정합 결론
**DoD:** ✅ Pass

**Deliverables:**
- docs/db/provenance/DOCKER_PROVENANCE.md (Container/Volume/Env 증거)
- docs/db/provenance/DB_ROW_PROVENANCE.md (Row-level 시간순 분석)
- docs/db/provenance/REPO_EXECUTION_PROVENANCE.md (Git/Scripts/Seed 경로 추적)
- docs/db/ROUTE_ALIGNMENT_REPORT.md (SSOT 위배 판정 + 신규 스키마 권고)

**Key Findings:**
- 모든 DB 데이터 = E2E test fixtures (2025-12-24 23:21 UTC, seed_step13_minimal.sql)
- insurer VARCHAR / proposal_id / template_id 부재 → 구조적 SSOT 위반
- 권고: Option B (New Schema v2 재구축)

---

#### ✅ STEP NEXT-X: Insurer/Product/Template SSOT Lock
**Commit:** 2dbbde4
**Summary:** insurer(8개), product, template_id 헌법급 SSOT 고정
**DoD:** ✅ Pass

**Key Changes:**
- CLAUDE.md § Insurer/Product/Template SSOT (Hard Rule) 추가
- docs/db/SSOT_VIOLATIONS.md (위반 자산 목록화)
- Violations: insurer VARCHAR, proposal_id 사용, template_id 부재

---

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
