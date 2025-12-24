# Database Documentation (Canonical)

> **Single Source of Truth for inca-RAG-final Database Schema**

This directory contains the **canonical database documentation** for the inca-RAG-final project.

All database-related work MUST reference these documents as the definitive specification.

---

## 📌 Source of Truth

The ultimate database baseline is defined by:

1. **Migration Files**: `migrations/step6c/*`
2. **Canonical Schema**: `schema_current.sql` (this directory)

**Priority Order**:
- migrations/* (executed SQL) > schema_current.sql (documentation) > ERD (visualization)

If there is ANY discrepancy between documents and migration SQL, **migration SQL is always correct**.

---

## 📂 Current Documentation Files

| File | Purpose | Status |
|------|---------|--------|
| **schema_current.sql** | Full canonical schema (all tables, indexes, constraints) | ✅ CANONICAL |
| **schema_universe_lock_minimal.sql** | Minimal Universe Lock schema (Docker E2E, no vector/chunk) | ✅ E2E DEPLOY |
| **erd_current.mermaid** | Entity-Relationship Diagram (1:1 with schema_current.sql) | ✅ CANONICAL |
| **schema_inventory.md** | Table classification by architectural status (ACTIVE/ARCHIVED) | ✅ INVENTORY |
| **table_usage_report.md** | Code usage analysis for each table | ✅ ANALYSIS |
| **design_decisions.md** | Why certain design choices were made | ✅ REFERENCE |

### schema_current.sql

- **Purpose**: Complete PostgreSQL schema definition
- **Baseline**: STEP 6-C (Proposal Universe Lock)
- **Scope**:
  - Baseline tables (insurer, product, coverage_standard, document, chunk, entities)
  - STEP 6-C tables (disease code 3-tier, proposal universe lock, slot schema v1.1.1)
- **Usage**: Apply to fresh DB or use as reference for migrations

**Key Principles**:
- `coverage_standard` = **READ-ONLY** (no auto-INSERT)
- `proposal_coverage_universe` = **Universe Lock** (comparison absolute baseline)
- 3-Tier Disease Code Model: `disease_code_master` → `disease_code_group` → `coverage_disease_scope`
- Slot Schema v1.1.1: `proposal_coverage_slots` with 20 slots
- Evidence required at every level (document_id, page, span_text)

### schema_universe_lock_minimal.sql (STEP 11)

- **Purpose**: Idempotent Universe Lock schema for Docker E2E testing
- **Scope**: Constitutional tables ONLY (no vector extension, no chunk/RAG tables)
- **Tables Included**:
  - Core: `insurer`, `product`, `document`
  - Coverage: `coverage_standard`, `coverage_alias`, `coverage_code_alias`
  - Universe Lock: `proposal_coverage_universe`, `proposal_coverage_mapped`, `proposal_coverage_slots`
  - Disease 3-Tier: `disease_code_master`, `disease_code_group`, `disease_code_group_member`, `coverage_disease_scope`
- **Idempotency**:
  - All tables use `CREATE TABLE IF NOT EXISTS`
  - Enums use `DO $$ BEGIN ... EXCEPTION WHEN duplicate_object` blocks
  - Triggers use `DROP TRIGGER IF EXISTS` before `CREATE TRIGGER`
- **Usage**: `cat schema_universe_lock_minimal.sql | psql ...` (0 errors guaranteed)
- **E2E Script**: `scripts/step11_e2e_docker.sh` applies this schema automatically

**Strictness Policy (STEP 11)**:
- Schema apply errors are **NEVER ignored**
- Script fails immediately if ERROR count > 0
- `set -euo pipefail` enforced
- All output logged to `artifacts/step11/e2e_run.log`

### seed_step13_minimal.sql (STEP 13)

- **Purpose**: Minimal seed data for Docker E2E testing with Constitutional compliance
- **Scope**: Proposal-based comparison data for 3 insurers (SAMSUNG, MERITZ, KB)
- **Data Coverage**:
  - Core: 3 insurers, 3 products, 3 proposal documents
  - Coverage Canonical: CA_DIAG_GENERAL, CA_DIAG_SIMILAR, UNMAPPED_TEST
  - Universe Lock: 5 records (4 MAPPED + 1 UNMAPPED)
  - Disease Codes: 8 KCD-7 codes + 1 group + 6 members
- **Usage**:
  ```bash
  cat docs/db/seed_step13_minimal.sql | docker exec -i inca_pg_5433 psql -U postgres -d inca_rag_final
  ```
- **Idempotency**: Uses TRUNCATE CASCADE at the top for clean re-execution
- **Verification**: `python -m pytest tests/e2e/test_step13_seed_smoke.py` (14 tests)

**Determinism Policy (STEP 13-β)**:
- ❌ **PROHIBITED**: Hardcoded `group_id` values (e.g., `1`, `2`)
- ✅ **REQUIRED**: Dynamic `group_id` resolution via SELECT subquery
- **Pattern**:
  ```sql
  -- CORRECT: Dynamic resolution
  (SELECT group_id FROM disease_code_group
   WHERE group_name = '삼성 유사암 (Seed)' AND insurer = 'SAMSUNG'
   LIMIT 1)

  -- INCORRECT: Hardcoded
  1  -- ❌ FORBIDDEN
  ```
- **Applies to**:
  - `proposal_coverage_slots.disease_scope_norm->>'include_group_id'`
  - `disease_code_group_member.group_id`
  - `coverage_disease_scope.include_group_id`

**Regression Guards**:
- `test_disease_scope_norm_group_id_fk_valid`: Validates FK integrity for slots
- `test_coverage_disease_scope_group_id_fk_valid`: Validates FK integrity for scope

**Seed Dependencies**:
- Requires `schema_universe_lock_minimal.sql` to be applied first
- Compatible with Docker PostgreSQL 17

### STEP 14: Proposal Data E2E Verification (2025-12-25)

- **Purpose**: Verify proposal seed data supports comparison scenarios
- **Script**: `scripts/step14_api_e2e_docker.sh`
- **Tests**: `tests/e2e/test_step14_data_e2e.py` (13/13 PASS)
- **Scenarios**:
  - A: Normal comparison (SAMSUNG vs MERITZ CA_DIAG_GENERAL)
  - B: UNMAPPED coverage (KB 매핑안된담보)
  - C: Disease scope required (SAMSUNG CA_DIAG_SIMILAR)
- **Verification Method**: SQL queries against seeded database
- **Output**: Query result files in `artifacts/step14/`

**E2E Flow**:
```
Docker DB
  ↓
schema_universe_lock_minimal.sql
  ↓
seed_step13_minimal.sql
  ↓
SQL Queries (Scenarios A/B/C)
  ↓
Verification Tests (13/13 PASS)
```

**Constitutional Validation**:
- ✅ Universe Lock: All comparisons from `proposal_coverage_universe`
- ✅ No `product_coverage` table (product-based comparison prohibited)
- ✅ Excel-based mapping (MAPPED/UNMAPPED states)
- ✅ disease_scope_norm uses group references

**Future Work**:
- Proposal-based API endpoint implementation
- Full UX contract compliance in API responses

### erd_current.mermaid

- **Purpose**: Visual representation of database schema
- **Alignment**: 100% synchronized with schema_current.sql
- **Features**:
  - Shows all tables, columns, relationships
  - Includes STEP 6-C Proposal Universe Lock tables
  - Highlights constitutional constraints (READ-ONLY, Universe Lock)

**To view**:
- Use GitHub/GitLab's built-in Mermaid renderer
- Or use [Mermaid Live Editor](https://mermaid.live/)
- Or VS Code extension: "Markdown Preview Mermaid Support"

### design_decisions.md

- **Purpose**: Rationale behind schema design choices
- **Coverage**: Why certain tables exist, why certain constraints are enforced
- **Status**: Reference document (not schema definition)

---

## 📦 Archive Directory

The `archive/` directory contains **historical documents** that are **NOT part of the current system definition**.

These files are kept for reference and historical context only:

```
archive/
├── erd_v2.mermaid          # Previous ERD iteration
├── erd.mermaid             # Original ERD
├── erd.md                  # Text-based ERD (obsolete)
├── schema.sql              # Baseline schema (pre-STEP 6-C)
├── schema_v2_additions.sql # Intermediate additions (superseded)
└── required_queries.md     # Query requirements (design phase)
```

**⚠️ WARNING**: Do NOT reference `archive/*` files for implementation or migration work.

---

## 🏗️ Architecture Principle: Proposal-Centered Comparison

### Design Shift (Historical Context)

**Previous Design (Archived)**:
- 약관/상품 중심 비교 (Product-centered comparison)
- `product_coverage` table as primary comparison axis
- Assumed "모든 상품을 대상으로 담보 비교"

**Current Design (STEP 6-C)**:
- **가입설계서 담보 중심 비교 (Proposal Universe Lock)**
- `proposal_coverage_universe` as **comparison SSOT**
- Universe Lock principle: "Only coverages in enrollment proposals can be compared"

### Role Clarification

| Entity | Previous Role | Current Role |
|--------|---------------|--------------|
| **product** | Primary comparison axis | **Context Axis ONLY** |
| **policy/terms** | Comparison source | **Evidence source for enrichment** |
| **proposal** | N/A | **Comparison SSOT (Universe Lock)** |

**Key Insight**: Products provide context (insurer, document grouping), but comparisons happen at **proposal coverage** level.

---

## 🔐 Constitutional Principles (ENFORCED)

These principles from CLAUDE.md are **enforced at the database level**:

### 1. Coverage Universe Lock ⭐ **CORE PRINCIPLE**
- **Principle**: Only coverages in enrollment proposals (`proposal_coverage_universe`) can be compared
- **Enforcement**:
  - All comparisons MUST check universe existence first
  - Out-of-universe queries return `out_of_universe` status
  - No product-centered comparison allowed
- **Tables**: `proposal_coverage_universe`, `proposal_coverage_mapped`, `proposal_coverage_slots`
- **Comparison Flow**:
  ```
  1. proposal_coverage_universe (설계서 담보 원본)
     ↓
  2. proposal_coverage_mapped (Excel 기반 매핑)
     ↓
  3. proposal_coverage_slots (Slot Schema v1.1.1)
     ↓
  4. 5-State Comparison System
  ```

### 2. Canonical Coverage Code (READ-ONLY)
- **Principle**: `coverage_standard` is single source of truth, no auto-INSERT allowed
- **Enforcement**:
  - Application role has NO INSERT permission on `coverage_standard`
  - Only admin role can manually INSERT canonical codes
- **Table**: `coverage_standard`

### 3. Excel-Based Mapping
- **Principle**: Coverage name → canonical code mapping comes ONLY from Excel (`data/담보명mapping자료.xlsx`)
- **Enforcement**:
  - Mapping status required: MAPPED | UNMAPPED | AMBIGUOUS
  - No LLM/similarity/inference for mapping
- **Tables**: `proposal_coverage_mapped`
- **Constraint**: `chk_mapped_requires_code` (MAPPED ↔ code NOT NULL)

### 4. KCD-7 Disease Code Authority
- **Principle**: KCD-7 official distribution is single source for disease codes
- **Enforcement**:
  - `disease_code_master` source must be "KCD-7 Official Distribution"
  - Insurance concepts (유사암, 소액암) go to `disease_code_group` (NOT disease_code_master)
  - `insurer=NULL` groups restricted to medical/KCD classification only
- **Tables**: `disease_code_master`, `disease_code_group`, `disease_code_group_member`

### 5. Evidence Required
- **Principle**: All confirmed values must have document span references
- **Enforcement**:
  - `proposal_coverage_universe`: `source_page`, `span_text` NOT NULL
  - `proposal_coverage_slots`: `evidence` JSONB NOT NULL
  - `disease_code_group`: `basis_doc_id`, `basis_span` required
- **Tables**: All tables with extracted data

### 6. Slot Schema v1.1.1
- **Principle**: Structured coverage data with 20 slots
- **Enforcement**:
  - `mapping_status` = required (enum)
  - `canonical_coverage_code` = nullable (MAPPED only)
  - `disease_scope_norm` = NULL until policy processed
  - `source_confidence` = proposal_confirmed | policy_required | unknown
- **Table**: `proposal_coverage_slots`

---

## 🚀 Quick Start

### Viewing the Schema

```bash
# View full schema
cat docs/db/schema_current.sql

# View ERD (requires Mermaid support)
# Open erd_current.mermaid in GitHub or VS Code
```

### Applying to New Database

```bash
# 1. Create database
createdb inca_rag_final

# 2. Apply schema
psql inca_rag_final < docs/db/schema_current.sql

# 3. Apply STEP 6-C migration (if not already included)
psql inca_rag_final < migrations/step6c/001_proposal_universe_lock.sql
```

### Verifying Schema

```bash
# Check table count
psql inca_rag_final -c "\dt"

# Verify STEP 6-C tables
psql inca_rag_final -c "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'proposal_%' OR tablename LIKE 'disease_%';"

# Check constraints
psql inca_rag_final -c "\d proposal_coverage_mapped"
```

---

## 📋 Table Summary (STEP 6-C Baseline)

### Comparison Architecture Summary

**Primary Comparison Axis**: `proposal_coverage_universe` → `proposal_coverage_mapped` → `proposal_coverage_slots`

**Context Axis**: `insurer`, `product`, `document` (provide metadata, NOT comparison dimension)

**Evidence Enrichment**: `chunk`, `chunk_entity`, `amount_entity`, policy documents (약관)

**5-State Comparison System**:
1. `comparable` - All critical slots match
2. `comparable_with_gaps` - Same canonical code, some slots NULL (policy_required)
3. `non_comparable` - Different canonical codes or incompatible
4. `unmapped` - Universe에 있으나 Excel 매핑 실패
5. `out_of_universe` - 가입설계서에 없음 (Universe Lock violation)

---

### Canonical Layer (6 tables)
- `insurer` - 보험사 마스터
- `product` - 보험 상품
- `coverage_standard` - 신정원 통일 담보 코드 **(READ-ONLY)**
- `document` - 보험 문서 메타데이터
- `coverage_alias` - 보험사별 담보명 매핑
- `coverage_code_alias`, `coverage_subtype`, `coverage_condition` - 매핑/조건 보조 테이블

### Document & Chunk Layer (3 tables)
- `chunk` - RAG 청크 (원본 + synthetic)
- `chunk_entity` - 추출 엔티티
- `amount_entity` - 금액 엔티티 (Amount Bridge)

### STEP 6-C: Proposal Universe Lock (7 tables)
- `disease_code_master` - KCD-7 질병코드 사전 **(Tier 1)**
- `disease_code_group` - 보험 질병 개념 그룹 **(Tier 2)**
- `disease_code_group_member` - 그룹 멤버 **(Tier 2)**
- `coverage_disease_scope` - 담보별 질병 범위 **(Tier 3)**
- `proposal_coverage_universe` - 가입설계서 담보 Universe **(Universe Lock 기준)**
- `proposal_coverage_mapped` - Universe → Canonical 매핑
- `proposal_coverage_slots` - Slot Schema v1.1.1 저장소

### Views (4 views)
- `v_active_products` - 활성 상품 목록
- `v_coverage_mapping` - 담보 매핑 현황
- `v_original_chunks` - 원본 청크 (is_synthetic=false)
- `v_proposal_coverage_full` - Universe → Mapping → Slots 전체 파이프라인

**Total**: ~20 tables + 4 views

---

## 🔄 Migration Workflow

When adding new database features:

1. **Create migration file**: `migrations/stepN/XXX_description.sql`
2. **Apply to dev database**: Test thoroughly
3. **Update schema_current.sql**: Reflect changes (full schema rewrite if needed)
4. **Update erd_current.mermaid**: Keep 1:1 sync with schema
5. **Document in design_decisions.md**: Explain WHY (if significant change)
6. **Commit all changes together**: Migration + docs in single atomic commit

**⚠️ NEVER**:
- Modify `schema_current.sql` without corresponding migration
- Create "schema_v3.sql" or version-suffixed files (use git history for versions)
- Leave `archive/*` files in main `docs/db/` directory

---

## 🛡️ Security & Access Control

### Read-Only Enforcement

**coverage_standard** is constitutionally READ-ONLY:

```sql
-- Application role (example)
CREATE ROLE app_ingestion;
GRANT SELECT ON coverage_standard TO app_ingestion;
GRANT INSERT, UPDATE, DELETE ON coverage_alias TO app_ingestion;
REVOKE INSERT ON coverage_standard FROM app_ingestion;

-- Admin role (manual INSERT only)
CREATE ROLE admin_role;
GRANT ALL ON coverage_standard TO admin_role;
```

### Synthetic Chunk Filtering

**Constitutional requirement**: Compare/retrieval MUST filter `is_synthetic=false`

```sql
-- CORRECT: Hard-coded is_synthetic filter
SELECT * FROM chunk WHERE is_synthetic = false;

-- INCORRECT: Using meta field
SELECT * FROM chunk WHERE meta->>'is_synthetic' = 'false';
```

---

## 📖 Related Documentation

- **CLAUDE.md**: Project constitution (top-level rules)
- **STATUS.md**: Current project status and completed steps
- **migrations/step6c/001_proposal_universe_lock.sql**: STEP 6-C migration SQL
- **docs/step6/**: STEP 6 (LLM Ingestion + Universe Lock) design docs

---

## ❓ FAQ

**Q: Why is there no `schema_v2.sql` or `schema_v3.sql`?**
A: We use **single canonical schema** principle. Version history is tracked via git, not filename suffixes.

**Q: Can I modify tables directly in the database?**
A: No. All changes MUST go through migration files. Direct SQL modifications will be lost on schema refresh.

**Q: What if `schema_current.sql` conflicts with migration files?**
A: Migration files are source of truth. Update `schema_current.sql` to match.

**Q: Why is `coverage_standard` READ-ONLY?**
A: Constitutional guarantee. Prevents accidental auto-INSERT of unmapped canonical codes. Manual admin approval required.

**Q: What's the difference between `disease_code_master` and `disease_code_group`?**
A:
- `disease_code_master` = KCD-7 official codes (medical facts)
- `disease_code_group` = Insurance business concepts (유사암, 소액암 - insurer-specific)

**Q: Can I delete files in `archive/`?**
A: No. Keep for historical reference. They consume minimal space and provide context for design evolution.

---

**Last Updated**: 2025-12-25
**Baseline**: STEP 6-C (Proposal Universe Lock v1)
**Migration Version**: `migrations/step6c/001_proposal_universe_lock.sql`
**Seed Data**: STEP 13-β (Deterministic seed with dynamic group_id resolution)
