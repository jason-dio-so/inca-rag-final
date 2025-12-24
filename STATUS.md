# inca-RAG-final Project Status

**Last Updated:** 2025-12-23
**Current Phase:** STEP 5-B Complete (γ release)

---

## Completed Steps

### ✅ STEP 5-A: OpenAPI Contract + FastAPI Skeleton
**Status:** COMPLETE
**Commit:** c102751
**Date:** 2025-12-23

**Deliverables:**
- OpenAPI 3.0.3 contract (`openapi/step5_openapi.yaml`)
- FastAPI skeleton with 3 endpoints
- Policy enforcement module (`apps/api/app/policy.py`)
- Contract tests (8/8 PASS)
- All tests DB-agnostic

**Key Files:**
- `openapi/step5_openapi.yaml`
- `apps/api/app/main.py`
- `apps/api/app/policy.py`
- `apps/api/app/schemas/*`
- `apps/api/app/routers/*`
- `tests/contract/test_step5_contract.py`

---

### ✅ STEP 5-B: DB Read-Only Implementation (α → β → γ → ε)
**Status:** COMPLETE AND SEALED (REAL DB ALIGNED)
**Final Commit:** [pending]
**Date:** 2025-12-23

#### α Release (Initial Implementation)
**Commit:** 17f27b5

**Deliverables:**
- DB read-only connection module
- Query layer with SQL templates
- Router integration with queries
- Read-only enforcement tests

#### β Release (Test Separation + Double Safety)
**Commit:** b7ea6f4

**Deliverables:**
- FastAPI dependency injection (`get_readonly_conn`)
- Contract tests DB-agnostic (dependency override)
- Integration tests separated (`tests/integration/`)
- Double safety for compare `is_synthetic`
- Strengthened BEGIN READ ONLY enforcement

#### γ Release (Final Validation + Guardrails)
**Commit:** e7e15e9

**Deliverables:**
- SQL template string-level assertion tests (4 new tests)
- Transaction hygiene enhancement (exception handling)
- Test command standardization (all 3 commands verified)
- Documentation updates (STEP5B_VALIDATE_REPORT.md)
- Constitutional guarantees sealed at 4 layers

#### ε Release (Entity-Based Coverage Filtering - FINAL)
**Commit:** [current]

**Deliverables:**
- All SQL queries aligned with actual PostgreSQL schema
- `public.product` / `public.product_coverage` / `public.coverage_standard`
- Coverage amount via `product_coverage` table
- **Entity-based evidence filtering**: `chunk_entity` + `amount_entity`
- Amount data from DB columns (no regex extraction)
- Coverage filtering via canonical `coverage_code` (신정원 통일 코드)
- Entity table assertions in integration tests
- Forbidden patterns (`product_master`, `coverage_id` params) enforced

**Key Features:**
1. **SQL Layer**: `is_synthetic=false` hard-coded, proven by string tests
2. **Router Layer**: Double safety hard-code for compare evidence
3. **Transaction Layer**: BEGIN READ ONLY with proper cleanup
4. **Policy Layer**: 400 errors for violations
5. **Schema Layer**: Real DB schema enforced by integration tests
6. **Entity Layer**: Coverage filtering via `chunk_entity`/`amount_entity`

**Test Coverage:**
- Contract tests: 8/8 PASS (DB-agnostic)
- Integration tests: 15/15 PASS (SQL validation + schema enforcement)
- Total: 23/23 PASS

**Test Commands:**
```bash
pytest tests/contract -q     # 8 passed
pytest tests/integration -q  # 15 passed
pytest -q                    # 23 passed
```

**Key Files:**
- `apps/api/app/db.py` (read-only connection + transaction hygiene)
- `apps/api/app/queries/*.py` (SQL templates with entity-based filtering)
- `apps/api/app/routers/*.py` (dependency injection + DB column mapping)
- `tests/contract/test_step5_contract.py` (8 contract tests, DB-agnostic)
- `tests/integration/test_step5_readonly.py` (15 integration tests + entity assertions)
- `docs/validation/STEP5B_VALIDATE_REPORT.md` (complete validation report)

---

## Current Status

### Constitutional Enforcement (4 Layers)

| Layer | Mechanism | Status |
|-------|-----------|--------|
| Policy | 400 errors for violations | ✅ SEALED |
| SQL Template | Hard-coded `is_synthetic=false` | ✅ PROVEN |
| Router | Double safety hard-code | ✅ SEALED |
| DB Transaction | BEGIN READ ONLY | ✅ SEALED |

### Forbidden Operations (All Blocked)

- ❌ Compare axis synthetic chunks → SQL hard-coded + router double safety
- ❌ coverage_standard auto-INSERT → Read-only connection + SELECT-only queries
- ❌ DB write operations → BEGIN READ ONLY transaction
- ❌ SQL bypass patterns → String-level tests prove no backdoors
- ❌ Foreign currencies → KRW ONLY policy enforced

### Currency Policy (FINAL)

- **System currency**: KRW ONLY
- **Foreign currencies**: NOT supported (USD/EUR/JPY/CNY all forbidden)
- **amount_unit**: Ignored for computation/branching/mapping
- **All API responses**: currency = "KRW"
- **Enforcement**: Integration test verifies KRW-only regardless of amount_unit value

**Rationale**: 대한민국 보험 도메인 전용 시스템. 모든 금액은 원화(KRW) 기준.

---

## Recent Steps

### ✅ STEP 5-C: Conditions Summary (Presentation-Only LLM)
**Status:** COMPLETE
**Commits:** 4498599 (implementation) + 029afa6 (hotfix)
**Date:** 2025-12-23

**Deliverables:**
- `conditions_summary` field for compare API (opt-in)
- LLM-based text summarization service (presentation-only)
- Constitutional compliance: non-synthetic evidence only
- Graceful degradation (null on failure)
- Integration tests (6 new tests)
- Hotfix: coverage_code optional for summary generation

**Key Features:**
1. **Opt-in Design**: `include_conditions_summary=false` (default)
2. **Presentation-Only**: LLM used for text summarization, not decision-making
3. **Constitutional**: Only uses non-synthetic evidence (SQL-enforced)
4. **Graceful Degradation**: Returns null on failure (200 OK)
5. **Coverage Code Optional**: Works with or without coverage_code filter

**Test Coverage:**
- Contract tests: 8/8 PASS
- Integration tests: 22/22 PASS (including 6 STEP 5-C tests)
- Total: 30/30 PASS

**Validation Evidence:**
- Hotfix validation report: `docs/validation/STEP5C_HOTFIX_029afa6.md`
- Server identity verification completed
- Runtime prerequisites documented

**Key Files:**
- `apps/api/app/services/conditions_summary_service.py`
- `apps/api/app/routers/compare.py` (conditions_summary integration)
- `apps/api/app/schemas/compare.py` (CompareOptions + CompareItem)
- `tests/integration/test_step5c_conditions.py`

---

## Next Steps

### STEP 6-A: LLM-Assisted Ingestion/Extraction (Design Only)
**Status:** IN PROGRESS (DESIGN PHASE)
**Estimated Completion:** 2025-12-23

**Scope:**
- Design document for LLM-assisted ingestion/extraction
- LLM as candidate generator only (not decision-maker)
- Candidate→Resolver→Confirmation pipeline
- Database schema for candidate storage
- Validation/verification strategy
- Test plan (5+ scenarios)
- Cost/performance estimation

**Constitutional Principles:**
- ✅ LLM proposes candidates only
- ✅ Code-based resolver validates and confirms
- ✅ coverage_standard auto-INSERT forbidden
- ✅ All entities use canonical coverage_code
- ✅ Compare-axis constitution unchanged (STEP 5 preserved)

**Deliverables:**
- `docs/step6/STEP6A_LLM_INGESTION_DESIGN.md`
- `docs/step6/diagrams/step6a_flow.mmd`
- STATUS.md update

**Prerequisites (All Met):**
- ✅ STEP 5 constitutional enforcement sealed
- ✅ Entity-based filtering operational (chunk_entity/amount_entity)
- ✅ Canonical coverage_code enforcement proven
- ✅ Read-only transactions validated

---

### STEP 6-B: LLM-Assisted Ingestion/Extraction (Implementation)
**Status:** NOT STARTED
**Estimated Start:** After STEP 6-A design approval

**Planned Features:**
1. LLM candidate generator (coverage entity extraction)
2. Coverage name→code resolver (rule-based)
3. Entity validator (FK/type/duplicate checks)
4. Candidate storage tables
5. Metrics/audit logging
6. Feature flag + configuration

**Prerequisites:**
- ✅ STEP 6-A design document approved
- ⏳ Database candidate tables created
- ⏳ LLM integration module implemented
- ⏳ Resolver logic validated

---

## Quick Reference

### Running the API
```bash
# Start server
uvicorn apps.api.app.main:app --reload --port 8000

# Health check
curl http://localhost:8000/health
```

### Running Tests
```bash
# Contract tests only (no DB needed)
pytest tests/contract -q

# Integration tests (with mocks)
pytest tests/integration -q

# All tests
pytest -q
```

### Project Structure
```
inca-RAG-final/
├── apps/
│   ├── api/          # STEP 5 API (FastAPI)
│   └── ingestion/    # Data ingestion (completed)
├── openapi/          # OpenAPI contracts
├── tests/
│   ├── contract/     # DB-agnostic policy tests
│   └── integration/  # DB-dependent implementation tests
└── docs/
    └── validation/   # Validation reports
```

---

## Recent Changes (γ Release)

### SQL Template String-Level Validation
- Added 4 new tests to prove SQL constitutional enforcement
- Tests verify SQL templates at STRING level, not just execution
- Proves `is_synthetic=false` is hard-coded, no bypass possible

### Transaction Hygiene
- Enhanced `db_readonly_session()` with proper exception handling
- Rollback on exception, clean close in finally block
- No interference with SELECT queries

### Documentation
- Updated STEP5B_VALIDATE_REPORT.md with γ changes
- Created STATUS.md (this file)
- All test commands verified and documented

---

## Team Notes

### For Developers
- Contract tests run without DB - use for quick validation
- Integration tests verify SQL enforcement - use for deep validation
- All routers use dependency injection - easy to mock for testing

### For QA
- Test commands standardized - see "Running Tests" above
- 18/18 tests must PASS before any commit
- Constitutional guarantees proven by string-level SQL tests

### For Operations
- API is read-only - no write operations possible
- BEGIN READ ONLY enforced at PostgreSQL level
- Any write attempt will fail immediately

---

**Project Status:** ✅ HEALTHY
**Next Milestone:** STEP 5-C (Premium + Conditions)
**Blockers:** None
