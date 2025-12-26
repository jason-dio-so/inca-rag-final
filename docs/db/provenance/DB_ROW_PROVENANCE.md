# DB Row Provenance Report

**Generated**: 2025-12-26
**Purpose**: DB row-level provenance audit (READ-ONLY)
**Target**: `inca_rag_final` database (port 5433)

---

## Executive Summary

**All DB rows were inserted in a single automated batch on 2025-12-24 23:21:58 UTC (±5 seconds).**

**Timing Evidence**:
- Volume created: `2025-12-24T23:21:53Z`
- First row inserted: `2025-12-24 23:21:58.649191` (insurer table)
- Last row inserted: `2025-12-24 23:21:58.658529` (proposal_coverage_mapped table)
- **Total duration**: ~9.3 seconds

**Conclusion**: All data seeded via **single automated script** during container initialization.

---

## Table Inventory

### Tables Present
Total: **13 tables**

**Core Schema**:
- `insurer` (3 rows)
- `product` (3 rows)
- `document` (3 rows)
- `coverage_standard` (3 rows)
- `coverage_alias` (4 rows)

**Proposal Universe (STEP 6-C)**:
- `proposal_coverage_universe` (5 rows)
- `proposal_coverage_mapped` (5 rows)
- `proposal_coverage_slots` (0 rows) ⚠️ Empty

**Disease Code (Article VIII)**:
- `disease_code_master` (0 rows) ⚠️ Empty
- `disease_code_group` (0 rows) ⚠️ Empty
- `disease_code_group_member` (0 rows) ⚠️ Empty
- `coverage_disease_scope` (0 rows) ⚠️ Empty

**Code Tables**:
- `coverage_code_alias` (unknown row count)

---

## Row-Level Provenance: Insertion Timeline

### 2025-12-24 23:21:58.649191 UTC
**Table**: `insurer` (3 rows)
- SAMSUNG (insurer_id=1)
- MERITZ (insurer_id=2)
- KB (insurer_id=3)

**Evidence**:
```sql
SELECT * FROM insurer ORDER BY insurer_id;
```
| insurer_id | insurer_code | insurer_name | created_at |
|------------|--------------|--------------|------------|
| 1 | SAMSUNG | 삼성화재 | 2025-12-24 23:21:58.649191 |
| 2 | MERITZ | 메리츠화재 | 2025-12-24 23:21:58.649191 |
| 3 | KB | KB손해보험 | 2025-12-24 23:21:58.649191 |

**Timing**: All 3 rows have **identical created_at** (microsecond precision)
**Interpretation**: Batch INSERT via script

---

### 2025-12-24 23:21:58.650020 UTC (+0.8s)
**Table**: `product` (3 rows)
- product_id=1: 삼성화재 암보험 2024 (insurer_id=1)
- product_id=2: 메리츠화재 암보험 2024 (insurer_id=2)
- product_id=3: KB손해보험 암보험 2024 (insurer_id=3)

**Evidence**:
```sql
SELECT * FROM product ORDER BY product_id;
```
| product_id | insurer_id | product_code | product_name | created_at |
|------------|------------|--------------|--------------|------------|
| 1 | 1 | CANCER_2024 | 삼성화재 암보험 2024 | 2025-12-24 23:21:58.65002 |
| 2 | 2 | CANCER_2024 | 메리츠화재 암보험 2024 | 2025-12-24 23:21:58.65002 |
| 3 | 3 | CANCER_2024 | KB손해보험 암보험 2024 | 2025-12-24 23:21:58.65002 |

**FK Integrity**: All `insurer_id` reference `insurer` table (FK constraint verified)

---

### 2025-12-24 23:21:58.651722 UTC (+1.7s)
**Table**: `document` (3 rows)
- document_id=1: 삼성화재 암보험 가입설계서 (product_id=1, doc_type=proposal)
- document_id=2: 메리츠화재 암보험 가입설계서 (product_id=2, doc_type=proposal)
- document_id=3: KB손해보험 암보험 가입설계서 (product_id=3, doc_type=proposal)

**Evidence**:
```sql
SELECT document_id, product_id, doc_type, doc_name, file_path, created_at FROM document;
```
| document_id | product_id | doc_type | doc_name | file_path | created_at |
|-------------|------------|----------|----------|-----------|------------|
| 1 | 1 | proposal | 삼성화재 암보험 가입설계서 | /seed/proposal_SAMSUNG_cancer_2024.pdf | 2025-12-24 23:21:58.651722 |
| 2 | 2 | proposal | 메리츠화재 암보험 가입설계서 | /seed/proposal_MERITZ_cancer_2024.pdf | 2025-12-24 23:21:58.651722 |
| 3 | 3 | proposal | KB손해보험 암보험 가입설계서 | /seed/proposal_KB_cancer_2024.pdf | 2025-12-24 23:21:58.651722 |

**File Paths**: All reference `/seed/` directory (seed data, not real files)
**Implication**: Document rows are **test fixtures**, not real file uploads

---

### 2025-12-24 23:21:58.652705 UTC (+3.5s)
**Table**: `coverage_standard` (3 rows)

**Evidence**:
```sql
SELECT 'coverage_standard' AS table, MIN(created_at), MAX(created_at), COUNT(*) FROM coverage_standard;
```
| table | min_created | max_created | count |
|-------|-------------|-------------|-------|
| coverage_standard | 2025-12-24 23:21:58.652705 | 2025-12-24 23:21:58.652705 | 3 |

**Interpretation**: All 3 rows inserted in single batch (identical timestamp)

---

### 2025-12-24 23:21:58.653029~653759 UTC (+3.8s~4.5s)
**Table**: `coverage_alias` (4 rows)

**Evidence**:
```sql
SELECT 'coverage_alias' AS table, MIN(created_at), MAX(created_at), COUNT(*) FROM coverage_alias;
```
| table | min_created | max_created | count |
|-------|-------------|-------------|-------|
| coverage_alias | 2025-12-24 23:21:58.653029 | 2025-12-24 23:21:58.653759 | 4 |

**Timing Spread**: 730 microseconds (0.73ms)
**Interpretation**: Sequential INSERT (row-by-row), not batch

---

### 2025-12-24 23:21:58.654004~656620 UTC (+4.8s~7.4s)
**Table**: `proposal_coverage_universe` (5 rows)

**Evidence**:
```sql
SELECT id, insurer, proposal_id, coverage_name_raw, amount_value, source_doc_id, source_page, created_at
FROM proposal_coverage_universe
ORDER BY id;
```

| id | insurer | proposal_id | coverage_name_raw | amount_value | source_doc_id | source_page | created_at |
|----|---------|-------------|-------------------|--------------|---------------|-------------|------------|
| 1 | SAMSUNG | PROP_SAMSUNG_001 | 일반암진단금 | 50000000.00 | 1 | 1 | 2025-12-24 23:21:58.654004 |
| 2 | SAMSUNG | PROP_SAMSUNG_001 | 유사암진단금 | 5000000.00 | 1 | 2 | 2025-12-24 23:21:58.655396 |
| 3 | MERITZ | PROP_MERITZ_001 | 암진단금(일반암) | 30000000.00 | 2 | 1 | 2025-12-24 23:21:58.65584 |
| 4 | KB | PROP_KB_001 | 일반암 진단비 | 40000000.00 | 3 | 1 | 2025-12-24 23:21:58.656234 |
| 5 | KB | PROP_KB_001 | 매핑안된담보 | 1000000.00 | 3 | 2 | 2025-12-24 23:21:58.65662 |

**Timing Spread**: 2.6 seconds (sequential INSERT)
**FK Integrity**: `source_doc_id` references `document` table (FK verified)
**Insurer Distribution**: SAMSUNG (2), MERITZ (1), KB (2)
**Proposal IDs**: PROP_SAMSUNG_001, PROP_MERITZ_001, PROP_KB_001

---

### 2025-12-24 23:21:58.656999~658529 UTC (+7.8s~9.3s)
**Table**: `proposal_coverage_mapped` (5 rows)

**Evidence**:
```sql
SELECT 'proposal_coverage_mapped' AS table, MIN(created_at), MAX(created_at), COUNT(*) FROM proposal_coverage_mapped;
```
| table | min_created | max_created | count |
|-------|-------------|-------------|-------|
| proposal_coverage_mapped | 2025-12-24 23:21:58.656999 | 2025-12-24 23:21:58.658529 | 5 |

**Timing Spread**: 1.5 seconds (sequential INSERT)
**Row Count Match**: 5 rows = 5 rows in `proposal_coverage_universe` (1:1 mapping)

---

## Source Document Traceability

### document.source_doc_id → document.document_id
All `proposal_coverage_universe.source_doc_id` values (1, 2, 3) reference valid `document` rows:

| source_doc_id | document.doc_name | document.file_path | insurer (derived) |
|---------------|-------------------|---------------------|-------------------|
| 1 | 삼성화재 암보험 가입설계서 | /seed/proposal_SAMSUNG_cancer_2024.pdf | SAMSUNG |
| 2 | 메리츠화재 암보험 가입설계서 | /seed/proposal_MERITZ_cancer_2024.pdf | MERITZ |
| 3 | KB손해보험 암보험 가입설계서 | /seed/proposal_KB_cancer_2024.pdf | KB |

**Conclusion**: All coverage data traces back to **3 seed proposal documents** (not real files)

---

## Insurer Distribution

### proposal_coverage_universe.insurer (VARCHAR field)

**Query**:
```sql
SELECT insurer, proposal_id, source_doc_id, COUNT(*) AS cnt
FROM proposal_coverage_universe
GROUP BY insurer, proposal_id, source_doc_id
ORDER BY cnt DESC, insurer, proposal_id;
```

**Result**:
| insurer | proposal_id | source_doc_id | cnt |
|---------|-------------|---------------|-----|
| KB | PROP_KB_001 | 3 | 2 |
| SAMSUNG | PROP_SAMSUNG_001 | 1 | 2 |
| MERITZ | PROP_MERITZ_001 | 2 | 1 |

**SSOT Violation**: `insurer` field is VARCHAR, not FK to `insurer.insurer_id`
**Implication**: String-based insurer (not SSOT compliant, see SSOT_VIOLATIONS.md)

---

## proposal_id vs product_id Mismatch

### SSOT Violation: proposal_id Used Instead of product_id

**Current State**:
- `proposal_coverage_universe.proposal_id`: `PROP_SAMSUNG_001`, `PROP_MERITZ_001`, `PROP_KB_001`
- No FK to `product` table
- `product_id` not present in `proposal_coverage_universe`

**Expected (SSOT Hard Rule)**:
- `product_id` should be FK to `product.product_id`
- `proposal_id` should be removed or demoted to metadata

**Evidence of Mismatch**:
```sql
-- proposal_coverage_universe has proposal_id (VARCHAR)
SELECT DISTINCT proposal_id FROM proposal_coverage_universe;
-- Result: PROP_SAMSUNG_001, PROP_MERITZ_001, PROP_KB_001

-- But product table has product_id (INTEGER PK)
SELECT product_id, product_name FROM product;
-- Result: 1, 2, 3 (삼성화재 암보험 2024, 메리츠화재 암보험 2024, KB손해보험 암보험 2024)
```

**Conclusion**: Current schema violates **Product SSOT** (see CLAUDE.md § Insurer/Product/Template SSOT)

---

## Empty Tables (Disease Code Schema)

### Article VIII Tables (All Empty)

**Query**:
```sql
SELECT COUNT(*) FROM disease_code_master;        -- Result: 0
SELECT COUNT(*) FROM disease_code_group;         -- Result: 0
SELECT COUNT(*) FROM disease_code_group_member;  -- Result: 0
SELECT COUNT(*) FROM coverage_disease_scope;     -- Result: 0
SELECT COUNT(*) FROM proposal_coverage_slots;    -- Result: 0
```

**Interpretation**:
- **Schema exists** (tables created via migrations)
- **No data loaded** (seed script did not populate these tables)
- Suggests: **Disease code pipeline not yet implemented** or **test data only focused on coverage mapping**

---

## Timeline Reconstruction

### Complete Insertion Sequence (9.3 seconds total)

| Δt (s) | Timestamp (UTC) | Table | Rows | Method |
|--------|-----------------|-------|------|--------|
| +0.0 | 23:21:58.649191 | insurer | 3 | Batch INSERT |
| +0.8 | 23:21:58.650020 | product | 3 | Batch INSERT |
| +1.7 | 23:21:58.651722 | document | 3 | Batch INSERT |
| +3.5 | 23:21:58.652705 | coverage_standard | 3 | Batch INSERT |
| +3.8 | 23:21:58.653029 | coverage_alias (start) | 4 | Sequential INSERT |
| +4.5 | 23:21:58.653759 | coverage_alias (end) | — | — |
| +4.8 | 23:21:58.654004 | proposal_coverage_universe (start) | 5 | Sequential INSERT |
| +7.4 | 23:21:58.656620 | proposal_coverage_universe (end) | — | — |
| +7.8 | 23:21:58.656999 | proposal_coverage_mapped (start) | 5 | Sequential INSERT |
| +9.3 | 23:21:58.658529 | proposal_coverage_mapped (end) | — | — |

**Insertion Pattern**:
- Core schema (insurer/product/document): **Batch INSERT** (identical timestamps)
- Coverage/proposal tables: **Sequential INSERT** (timestamp spread)

**Likely Seed Script Structure**:
```python
# 1. Core schema batch inserts (0-3.5s)
INSERT INTO insurer VALUES (...), (...), (...);
INSERT INTO product VALUES (...), (...), (...);
INSERT INTO document VALUES (...), (...), (...);
INSERT INTO coverage_standard VALUES (...), (...), (...);

# 2. Coverage aliases (3.8-4.5s)
for alias in coverage_aliases:
    INSERT INTO coverage_alias ...

# 3. Proposal universe (4.8-7.4s)
for coverage in proposal_coverages:
    INSERT INTO proposal_coverage_universe ...

# 4. Coverage mapping (7.8-9.3s)
for mapping in coverage_mappings:
    INSERT INTO proposal_coverage_mapped ...
```

---

## Data Characteristics

### Coverage Names (Raw)
- `일반암진단금` (SAMSUNG)
- `유사암진단금` (SAMSUNG)
- `암진단금(일반암)` (MERITZ)
- `일반암 진단비` (KB)
- `매핑안된담보` (KB) ⚠️ Test fixture for unmapped coverage

**Notable**: `매핑안된담보` = **Intentional unmapped test case** (for testing UNMAPPED state)

### Amount Distribution
- SAMSUNG: 50M (일반암), 5M (유사암)
- MERITZ: 30M (일반암)
- KB: 40M (일반암), 1M (매핑안된담보)

**Currency**: All `KRW` (Korean Won)

---

## SSOT Compliance Check

### Insurer SSOT
**Expected** (CLAUDE.md):
- `insurer_code` = enum (8개 고정)
- `proposal_coverage_universe.insurer` = FK to `insurer.insurer_id`

**Actual**:
- `insurer.insurer_code` = VARCHAR(50) (not enum) ⚠️
- `proposal_coverage_universe.insurer` = VARCHAR(50) (not FK) 🔴

**Status**: 🔴 **Violation** (see SSOT_VIOLATIONS.md § Category 1)

### Product SSOT
**Expected** (CLAUDE.md):
- `proposal_coverage_universe.product_id` = FK to `product.product_id`

**Actual**:
- `proposal_coverage_universe.proposal_id` = VARCHAR(200) (임시 식별자) 🔴
- No `product_id` field

**Status**: 🔴 **Violation** (see SSOT_VIOLATIONS.md § Category 2)

### Template SSOT
**Expected** (CLAUDE.md):
- `template_id` = insurer_code + product_id + version + fingerprint

**Actual**:
- No `template_id` field anywhere 🔴

**Status**: 🔴 **Violation** (see SSOT_VIOLATIONS.md § Category 4)

---

## Data Provenance Conclusion

### Evidence Summary
1. **All data inserted in single 9.3s automated batch** (2025-12-24 23:21:58 UTC)
2. **Source**: Seed script (not manual, not migration)
3. **Method**: Mix of batch INSERT (core schema) + sequential INSERT (proposal data)
4. **Volume-DB timeline**: Volume created 5s before first INSERT (automated init)

### Data Trustworthiness
- ✅ **Referential integrity**: All FKs valid (insurer → product → document → coverage)
- ⚠️ **Test fixtures**: File paths (`/seed/*.pdf`) are placeholders, not real files
- ⚠️ **Minimal dataset**: 3 insurers, 3 products, 5 coverages (E2E test scope)
- 🔴 **SSOT violations**: insurer VARCHAR, proposal_id usage, template_id missing

### Seed Script Location (Hypothesis)
Based on timing and structure, likely candidates:
- `docs/db/seed_step13_minimal.sql`
- `migrations/step6c/*` (if migration includes seed data)
- `apps/api/scripts/seed_*.py` (if Python script)

**Next Step**: Check repo for seed script execution around 2025-12-24 23:21 UTC

---

## Appendix: Raw Query Results

### Full Table Row Counts
```sql
SELECT
  'insurer' AS table, COUNT(*) AS cnt FROM insurer
UNION ALL
SELECT 'product' AS table, COUNT(*) AS cnt FROM product
UNION ALL
SELECT 'document' AS table, COUNT(*) AS cnt FROM document
UNION ALL
SELECT 'coverage_standard' AS table, COUNT(*) AS cnt FROM coverage_standard
UNION ALL
SELECT 'coverage_alias' AS table, COUNT(*) AS cnt FROM coverage_alias
UNION ALL
SELECT 'proposal_coverage_universe' AS table, COUNT(*) AS cnt FROM proposal_coverage_universe
UNION ALL
SELECT 'proposal_coverage_mapped' AS table, COUNT(*) AS cnt FROM proposal_coverage_mapped
UNION ALL
SELECT 'proposal_coverage_slots' AS table, COUNT(*) AS cnt FROM proposal_coverage_slots
UNION ALL
SELECT 'disease_code_master' AS table, COUNT(*) AS cnt FROM disease_code_master
UNION ALL
SELECT 'disease_code_group' AS table, COUNT(*) AS cnt FROM disease_code_group
UNION ALL
SELECT 'disease_code_group_member' AS table, COUNT(*) AS cnt FROM disease_code_group_member
UNION ALL
SELECT 'coverage_disease_scope' AS table, COUNT(*) AS cnt FROM coverage_disease_scope;
```

| table | cnt |
|-------|-----|
| insurer | 3 |
| product | 3 |
| document | 3 |
| coverage_standard | 3 |
| coverage_alias | 4 |
| proposal_coverage_universe | 5 |
| proposal_coverage_mapped | 5 |
| proposal_coverage_slots | 0 |
| disease_code_master | 0 |
| disease_code_group | 0 |
| disease_code_group_member | 0 |
| coverage_disease_scope | 0 |

---

**Report generated via READ-ONLY queries. No data modification performed.**
