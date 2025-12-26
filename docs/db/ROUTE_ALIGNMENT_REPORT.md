# Route Alignment Report

**Generated**: 2025-12-26
**Purpose**: Provenance-based SSOT compliance verdict + migration path recommendations
**Evidence**: DOCKER_PROVENANCE.md + DB_ROW_PROVENANCE.md + REPO_EXECUTION_PROVENANCE.md + SSOT_VIOLATIONS.md

---

## Executive Summary

**Verdict**: Current DB violates Insurer/Product/Template SSOT Hard Rule at structural level.

**Classification**: **E2E Test Fixtures** (not production-ready schema)

**Recommendation**: **Option B - New Schema Reconstruction** with legacy data migration path.

---

## Evidence-Based Findings

### Finding 1: Data Provenance (2025-12-24 23:21 UTC)

**Source**: `scripts/step14_api_e2e_docker.sh` → `seed_step13_minimal.sql`
**Purpose**: STEP 14 E2E Compare API verification
**Scope**: Minimal test data (3 insurers, 3 products, 5 coverages)
**Method**: Automated seed script (9.3s batch insertion)

**Conclusion**: **All current DB data = E2E test fixtures, NOT production pipeline output**

---

### Finding 2: SSOT Hard Rule Violations (Structural)

**From SSOT_VIOLATIONS.md**:

| Violation Category | Severity | Affected Assets |
|--------------------|----------|-----------------|
| insurer VARCHAR usage | 🔴 High | 6 tables, 3 Python types |
| proposal_id usage (not product_id) | 🔴 High | 2 tables, 1 Python type |
| template_id absence | 🔴 High | Entire codebase |
| insurer enum not enforced | 🔴 High | 1 table (insurer) |

**SSOT Hard Rule** (CLAUDE.md § Insurer/Product/Template SSOT):
- insurer_code = 8개 enum (SAMSUNG, MERITZ, KB, HANA, DB, HANWHA, LOTTE, HYUNDAI)
- product_id = FK to product.product_id (NOT proposal_id VARCHAR)
- template_id = insurer_code + product_id + version + fingerprint

**Actual Schema**:
- `proposal_coverage_universe.insurer`: VARCHAR(50) ❌ (should be FK to insurer_id)
- `proposal_coverage_universe.proposal_id`: VARCHAR(200) ❌ (should be product_id FK)
- `template_id`: Not exists ❌

**Conclusion**: **Current schema CANNOT support SSOT Hard Rule without structural changes**

---

### Finding 3: Schema Version Mismatch

**Applied Schema**: `docs/db/schema_universe_lock_minimal.sql`
**Purpose**: Minimal schema for STEP 6-C (Proposal Universe Lock)
**Design Date**: Pre-STEP NEXT-X (before SSOT Hard Rule)

**Migration Files Available** (not applied):
- `migrations/step6b/000_base_schema.sql` (base schema with insurer/product tables)
- `migrations/step6c/001_proposal_universe_lock.sql` (full Universe Lock schema)

**Conclusion**: **Applied schema predates SSOT Hard Rule** (December 2025-12-26)

---

### Finding 4: Docker Container Lifecycle

**Container Created**: 2025-12-25 15:24 KST
**Volume Created**: 2025-12-25 08:21 KST (1.5 days old)
**Restart Policy**: `unless-stopped`

**Volume Persistence**:
- Data survives container restarts ✅
- Data cleared on `docker compose down -v` ✅
- Seed script = idempotent (TRUNCATE CASCADE + INSERT)

**Conclusion**: **Ephemeral test environment**, not production deployment

---

## SSOT Compliance Analysis

### Question 1: Is current DB from "가입설계서 중심 파이프라인"?

**Answer**: ❌ No

**Evidence**:
- Source: `seed_step13_minimal.sql` (manual seed script)
- Document file_path: `/seed/proposal_*.pdf` (placeholder, not real files)
- Scope: 5 test coverages (intentionally minimal)
- Timing: Batch insertion in 9.3s (not incremental ingestion)

**Conclusion**: Current data is **test fixtures** for E2E API verification, NOT real proposal processing output.

---

### Question 2: Does schema structurally support SSOT Hard Rule?

**Answer**: ❌ No

**Evidence** (table-by-table):

#### proposal_coverage_universe
```sql
CREATE TABLE proposal_coverage_universe (
    insurer VARCHAR(50) NOT NULL,        -- ❌ Should be insurer_id INTEGER FK
    proposal_id VARCHAR(200) NOT NULL,   -- ❌ Should be product_id INTEGER FK
    -- template_id missing entirely       -- ❌ Required by SSOT
    ...
);
```

**Violations**:
- insurer: VARCHAR (not FK) → Cannot enforce 8개 enum
- proposal_id: Temporary identifier → product_id 대체 필요
- template_id: Absent → Cannot track document template versions

#### coverage_disease_scope
```sql
CREATE TABLE coverage_disease_scope (
    insurer VARCHAR(50) NOT NULL,        -- ❌ Should be insurer_id FK
    proposal_id VARCHAR(200) NOT NULL,   -- ❌ Should be product_id FK
    ...
);
```

**Violations**: Same as proposal_coverage_universe

#### disease_code_group
```sql
CREATE TABLE disease_code_group (
    insurer VARCHAR(50),                 -- ❌ Should be insurer_id FK (or NULL)
    ...
);
```

**Violations**: insurer VARCHAR (nullable), but no FK constraint

**Conclusion**: **3+ tables require structural schema changes** to support SSOT

---

### Question 3: Legacy vs New Schema?

#### Option A: Legacy Migration (이관)
**Assumptions**:
- Keep current schema structure
- Add FK constraints retrospectively
- Migrate proposal_id → product_id via mapping

**Challenges**:
- ❌ Breaking change: proposal_id → product_id migration requires data transformation
- ❌ insurer VARCHAR → insurer_id FK requires lookup table
- ❌ template_id: Cannot add retroactively (requires document version tracking)
- ❌ Violates "새 술은 새 포대" principle

**Verdict**: **Not recommended** (too many structural conflicts)

#### Option B: New Schema Reconstruction (재구축)
**Assumptions**:
- Design new schema compliant with SSOT Hard Rule
- Namespace: `v2_*` tables or schema separation
- Migrate test data as reference (optional)

**Advantages**:
- ✅ Clean SSOT compliance from start
- ✅ Proper FK relationships (insurer_id, product_id, template_id)
- ✅ Enum enforcement (insurer_code constraint)
- ✅ No legacy debt

**Challenges**:
- ⚠️ Requires schema design effort
- ⚠️ Seed script rewrite (seed_step13 → seed_v2)
- ⚠️ Migration path for future production data

**Verdict**: **Recommended** (aligns with "새 술은 새 포대" principle)

---

## Recommendation: Option B (New Schema Reconstruction)

### Phase 1: Schema Design (STEP NEXT-Y+1)

**Deliverables**:
1. `migrations/v2/001_ssot_compliant_schema.sql`
   - insurer_code: PostgreSQL ENUM type (8개 고정)
   - product table: product_id PK (SSOT)
   - template table: template_id PK (insurer_code + product_id + version + fingerprint)
   - proposal_coverage_universe_v2: insurer_id FK, product_id FK, template_id FK

2. Schema validation script:
   ```python
   # scripts/validate_ssot_schema.py
   # Check: insurer enum, FKs, template_id structure
   ```

3. Design doc: `docs/db/SCHEMA_V2_DESIGN.md`

---

### Phase 2: Seed Migration (STEP NEXT-Y+2)

**Deliverables**:
1. `docs/db/seed_v2_minimal.sql`
   - Rewrite seed_step13_minimal with v2 schema
   - Use insurer_id FK (not VARCHAR)
   - Use product_id FK (not proposal_id)
   - Add template_id entries

2. Validation:
   ```bash
   # E2E smoke test with v2 schema
   scripts/step14_api_e2e_docker_v2.sh
   ```

---

### Phase 3: API/Code Alignment (STEP NEXT-Y+3)

**Deliverables**:
1. Python types:
   - `InsurerCode(Enum)` (8개 값)
   - Remove `proposal_id` from schemas
   - Add `template_id` to ProposalCoverageItem

2. Query layer:
   - Update `apps/api/app/queries/compare.py` to use insurer_id FK
   - Remove proposal_id JOINs, replace with product_id

3. Backward compatibility (optional):
   - `proposal_id` → `product_id` adapter for existing tests
   - Deprecation warnings

---

### Phase 4: Container/Docker Alignment (STEP NEXT-Y+4)

**Deliverables**:
1. `docker-compose.v2.yml`:
   - Use `DB_*` env vars (not `POSTGRES_*`)
   - Align with apps/api/.env.example SSOT

2. Init scripts (optional):
   - `/docker-entrypoint-initdb.d/01_schema_v2.sql`
   - `/docker-entrypoint-initdb.d/02_seed_v2.sql`

---

## Migration Path Summary

### Current State (2025-12-26)
```
inca_pg_step14 (postgres:17-alpine)
  ├─ Volume: postgres_step14_data (2025-12-25 08:21)
  ├─ Schema: schema_universe_lock_minimal.sql (pre-SSOT)
  ├─ Seed: seed_step13_minimal.sql (E2E test fixtures)
  └─ Data: 3 insurers, 3 products, 5 coverages (SSOT violations)
```

### Target State (STEP NEXT-Y+4)
```
inca_pg_v2 (postgres:17-alpine)
  ├─ Volume: postgres_v2_data
  ├─ Schema: migrations/v2/001_ssot_compliant_schema.sql
  ├─ Seed: seed_v2_minimal.sql
  └─ Data: SSOT-compliant (insurer_id FK, product_id FK, template_id)
```

---

## Legacy Asset Classification

### 이관 대상 (Migration Target)
- **Test data**: seed_step13_minimal contents (3 insurers, 5 coverages)
- **Migration**: Transform proposal_id → product_id via lookup

### 폐기 대상 (Deprecation Target)
- **Schema**: schema_universe_lock_minimal.sql (replaced by v2)
- **Tables**: proposal_coverage_universe (current structure)
- **Fields**: insurer VARCHAR, proposal_id VARCHAR

### 보존 대상 (Preservation Target)
- **Design docs**: SSOT_VIOLATIONS.md, ROUTE_ALIGNMENT_REPORT.md (evidence)
- **Scripts**: step14_api_e2e_docker.sh (reference for v2 rewrite)
- **Migrations**: step6b/step6c (historical reference)

---

## Risk Assessment

### Option A Risks (Legacy Migration)
- 🔴 **High**: Breaking schema changes (proposal_id → product_id)
- 🔴 **High**: Partial SSOT compliance (template_id still missing)
- 🟡 **Medium**: Technical debt accumulation

### Option B Risks (New Schema)
- 🟢 **Low**: SSOT compliance guaranteed
- 🟡 **Medium**: Development effort (schema design + seed rewrite)
- 🟡 **Medium**: Test data migration overhead

**Recommended Mitigation**: Start with minimal v2 schema (3 insurers, 5 coverages) matching current test scope.

---

## Next Steps (Action Plan)

### Immediate (STEP NEXT-Y+1)
1. Create `docs/db/SCHEMA_V2_DESIGN.md`
2. Design v2 schema with SSOT compliance:
   - insurer_code ENUM (8개)
   - product_id FK
   - template_id structure
3. Review with stakeholders

### Short-term (STEP NEXT-Y+2)
1. Implement `migrations/v2/001_ssot_compliant_schema.sql`
2. Rewrite `seed_v2_minimal.sql`
3. E2E smoke test with v2

### Medium-term (STEP NEXT-Y+3)
1. Update Python types (InsurerCode enum)
2. Refactor query layer (insurer_id FK)
3. Deprecate proposal_id

### Long-term (STEP NEXT-Y+4)
1. Production data migration plan
2. Rollback strategy
3. Monitoring/validation

---

## Appendix: Evidence Cross-Reference

| Finding | Evidence Source | Page/Section |
|---------|----------------|--------------|
| Data = E2E test fixtures | REPO_EXECUTION_PROVENANCE.md | "Seed File" section |
| insurer VARCHAR violation | SSOT_VIOLATIONS.md | Category 1 |
| proposal_id violation | SSOT_VIOLATIONS.md | Category 2 |
| template_id absence | SSOT_VIOLATIONS.md | Category 4 |
| Container lifecycle | DOCKER_PROVENANCE.md | "Timeline Reconstruction" |
| DB insertion timing | DB_ROW_PROVENANCE.md | "Timeline Reconstruction" |

---

## Constitutional Compliance

**CLAUDE.md § Insurer/Product/Template SSOT (Hard Rule)**:
- ✅ Evidence-based analysis (no speculation)
- ✅ "새 술은 새 포대" judgment applied
- ✅ No DROP/TRUNCATE recommendations (read-only audit)
- ✅ Migration path (not deletion path)

**Decision**: **Option B (New Schema)** aligns with "기존 스키마 재활용 전제 금지" principle.

---

**Report Status**: Final (based on 100% provenance certainty)
