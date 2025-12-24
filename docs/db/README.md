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
| **erd_current.mermaid** | Entity-Relationship Diagram (1:1 with schema_current.sql) | ✅ CANONICAL |
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

## 🔐 Constitutional Principles (ENFORCED)

These principles from CLAUDE.md are **enforced at the database level**:

### 1. Coverage Universe Lock
- **Principle**: Only coverages in enrollment proposals (`proposal_coverage_universe`) can be compared
- **Enforcement**:
  - All comparisons MUST check universe existence
  - Out-of-universe queries return `out_of_universe` status
- **Tables**: `proposal_coverage_universe`, `proposal_coverage_mapped`, `proposal_coverage_slots`

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

**Last Updated**: 2025-12-24
**Baseline**: STEP 6-C (Proposal Universe Lock v1)
**Migration Version**: `migrations/step6c/001_proposal_universe_lock.sql`
