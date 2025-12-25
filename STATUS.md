# inca-RAG-final Project Status

**Last Updated:** 2025-12-25
**Current Phase:** Premium API Integration (STEP 32)
**Project Health:** ✅ HEALTHY

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

