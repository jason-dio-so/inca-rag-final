# STEP 6-B Phase 3: DB Realization Evidence

**Date**: 2025-12-24
**Status**: ✅ COMPLETE
**Scope**: Database实体化 + Excel-based canonical coverage_standard initialization + Migration verification

---

## Constitutional Principles Applied

1. **Canonical Coverage Code (신정원 통일 담보 코드)**
   - Source: `data/담보명mapping자료.xlsx` (ONLY)
   - Schema: `coverage_id SERIAL PRIMARY KEY`, `coverage_code TEXT UNIQUE NOT NULL`
   - All FKs reference `coverage_code` (canonical key)
   - ❌ NO data from `inca-rag` DB
   - ❌ NO LLM-based inference

2. **pgvector Exclusion**
   - Phase 3 minimal scope: NO embedding/vector
   - `000_base_schema.sql` excludes `CREATE EXTENSION vector`
   - chunk.embedding column removed

3. **LLM Pipeline Prohibition**
   - Candidate tables created
   - ❌ NO automatic confirm
   - Phase 3 stops at candidate storage verification

---

## Execution Order

### STEP 3-1: Docker Compose (Postgres 5433)

```bash
$ docker compose up -d
 Container inca_pg_5433  Created
 Container inca_pg_5433  Started

$ docker compose ps
NAME           IMAGE                COMMAND                  SERVICE    CREATED          STATUS
inca_pg_5433   postgres:15-alpine   "docker-entrypoint.s…"   postgres   13 seconds ago   Up 13 seconds (healthy)

$ lsof -nP -iTCP:5433 -sTCP:LISTEN
COMMAND    PID     USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
com.docke 4650 cheollee  176u  IPv6 0x7e1c71a9480fe054      0t0  TCP *:5433 (LISTEN)
```

**Result**: ✅ PASS

---

### STEP 3-2: Base Schema Creation

```bash
$ export PGPASSWORD=postgres
$ psql -h localhost -p 5433 -U postgres -d inca_rag_final -f migrations/step6b/000_base_schema.sql

CREATE TABLE  # coverage_standard
CREATE TABLE  # coverage_alias
CREATE TABLE  # insurer
CREATE TABLE  # product
CREATE TABLE  # document
CREATE TABLE  # chunk
CREATE INDEX (x6)
```

**Schema Verification**:

```sql
\d coverage_standard

 Column        | Type          | Nullable | Default
---------------|---------------|----------|------------------
 coverage_id   | integer       | not null | nextval('...')
 coverage_code | text          | not null |
 coverage_name | text          | not null |
 domain        | varchar(100)  |          |
 coverage_type | varchar(100)  |          |
 priority      | integer       |          | 999
 is_main       | boolean       |          | false
 meta          | jsonb         |          | '{}'::jsonb
 created_at    | timestamp     |          | CURRENT_TIMESTAMP
 updated_at    | timestamp     |          | CURRENT_TIMESTAMP

Indexes:
    "coverage_standard_pkey" PRIMARY KEY (coverage_id)
    "coverage_standard_coverage_code_key" UNIQUE (coverage_code)
```

**Result**: ✅ PASS

---

### STEP 3-3: Excel-Based Coverage Initialization

**Data Source**:
```
data/담보명mapping자료.xlsx
- Sheet: Sheet1
- Columns: ins_cd, 보험사명, cre_cvr_cd, 신정원코드명, 담보명(가입설계서)
- Canonical codes: 28
- Aliases: 264
```

**Execution**:
```bash
$ python3 scripts/init_coverage_standard.py

🚀 Initializing coverage_standard from data/담보명mapping자료.xlsx
📖 Loaded 28 canonical codes, 264 aliases
✅ Tables verified: coverage_standard, coverage_alias
✅ Upserted 28 canonical coverage codes
✅ Inserted 264 coverage aliases

📊 Verification:
   coverage_standard: 28 records
   coverage_alias: 264 records

   Sample coverage_standard:
      A1100: 질병사망
      A1300: 상해사망
      A3300_1: 상해후유장해(3-100%)
      A4101: 뇌혈관질환진단비
      A4102: 뇌출혈진단비
```

**DB Verification**:
```sql
SELECT COUNT(*) FROM coverage_standard;
-- 28

SELECT coverage_code, coverage_name FROM coverage_standard ORDER BY coverage_code LIMIT 10;
-- A1100   | 질병사망
-- A1300   | 상해사망
-- A3300_1 | 상해후유장해(3-100%)
-- A4101   | 뇌혈관질환진단비
-- A4102   | 뇌출혈진단비
-- A4103   | 뇌졸중진단비
-- A4104_1 | 심장질환진단비
-- A4105   | 허혈성심장질환진단비
-- A4200_1 | 암진단비(유사암제외)
-- A4209   | 고액암진단비
```

**Result**: ✅ PASS (28 canonical codes match Excel exactly)

---

### STEP 3-4: STEP 6-B Candidate Tables Migration

```bash
$ psql -h localhost -p 5433 -U postgres -d inca_rag_final \
    -f migrations/step6b/001_create_candidate_tables.sql

CREATE TABLE  # chunk_entity_candidate
CREATE TABLE  # amount_entity_candidate
CREATE VIEW   # candidate_metrics
CREATE FUNCTION  # confirm_candidate_to_entity()
CREATE FUNCTION  # verify_candidate_coverage_code_fk()
CREATE TRIGGER   # trg_verify_coverage_code_fk
```

**Tables Created**:
```
 public | amount_entity_candidate | table
 public | chunk                   | table
 public | chunk_entity_candidate  | table
 public | coverage_alias          | table
 public | coverage_standard       | table
 public | document                | table
 public | insurer                 | table
 public | product                 | table

Views:
 public | candidate_metrics       | view
```

**Result**: ✅ PASS

---

### STEP 3-5: Migration Verification

```bash
$ bash migrations/step6b/verify_migration.sh

===================================================================
STEP 6-B Phase 1 Migration Verification
===================================================================
Database: inca_rag_final @ localhost:5433

1. Verifying chunk_entity_candidate table... ✅
2. Verifying amount_entity_candidate table... ✅
3. Verifying candidate_metrics view... ✅
4. Verifying confirm_candidate_to_entity() function... ✅
5. Checking indexes on chunk_entity_candidate... ✅
   - chunk_entity_candidate_pkey (PRIMARY)
   - idx_chunk_entity_candidate_chunk
   - idx_chunk_entity_candidate_status
   - idx_chunk_entity_candidate_created
   - idx_chunk_entity_candidate_hash
   - idx_chunk_entity_candidate_resolved_code
   - idx_chunk_entity_candidate_unique (UNIQUE on chunk_id, resolved_coverage_code WHERE resolved)

6. Checking constraints... ✅
   - confidence CHECK (0 <= confidence <= 1)
   - valid_resolver_status (pending/resolved/rejected/needs_review)
   - valid_entity_type_proposed (definition/condition/exclusion/amount/benefit)
   - resolved_code_required (resolver_status='resolved' => coverage_code NOT NULL)
   - FK: chunk_id -> chunk(chunk_id) CASCADE

7. Verifying row counts... ✅
   - chunk_entity_candidate: 0
   - amount_entity_candidate: 0
```

**Result**: ✅ PASS (All verification checks succeeded)

---

## Final State Verification

**Table Counts**:
```sql
SELECT
  'coverage_standard' as table_name, COUNT(*) FROM coverage_standard
UNION ALL
SELECT 'coverage_alias', COUNT(*) FROM coverage_alias
UNION ALL
SELECT 'chunk_entity_candidate', COUNT(*) FROM chunk_entity_candidate
UNION ALL
SELECT 'amount_entity_candidate', COUNT(*) FROM amount_entity_candidate;

-- Result:
--  coverage_standard       | 28
--  coverage_alias          | 264
--  chunk_entity_candidate  | 0
--  amount_entity_candidate | 0
```

**Coverage Standard Integrity**:
```sql
-- All aliases reference valid coverage_code
SELECT COUNT(*) FROM coverage_alias ca
WHERE NOT EXISTS (
  SELECT 1 FROM coverage_standard cs WHERE cs.coverage_code = ca.coverage_code
);
-- 0 (no orphaned aliases)

-- Canonical key constraint
SELECT COUNT(*) FROM coverage_standard WHERE coverage_code IS NULL;
-- 0
```

---

## DoD Checklist

- [x] docker compose ps → postgres healthy
- [x] lsof → port 5433 LISTEN
- [x] scripts/init_coverage_standard.py → SUCCESS
- [x] coverage_standard: 28 records (exact match with Excel)
- [x] coverage_alias: 264 records
- [x] chunk_entity_candidate table exists
- [x] amount_entity_candidate table exists
- [x] candidate_metrics view exists
- [x] confirm_candidate_to_entity() function exists
- [x] FK: chunk_entity_candidate.chunk_id -> chunk.chunk_id
- [x] Trigger: trg_verify_coverage_code_fk (coverage_code FK verification)
- [x] make step6b-verify-db → PASS

---

## Key Files

- **Migration**: `migrations/step6b/000_base_schema.sql`
- **Migration**: `migrations/step6b/001_create_candidate_tables.sql`
- **Initialization**: `scripts/init_coverage_standard.py`
- **Verification**: `migrations/step6b/verify_migration.sh`
- **Docker**: `docker-compose.yml`
- **Data Source**: `data/담보명mapping자료.xlsx`

---

## Next Steps

STEP 6-B Phase 4: Minimal E2E Test
- Ingest 1 PDF (보험사 선택)
- Run Orchestrator (LLM pipeline)
- Verify chunk_entity_candidate INSERT
- ❌ NO confirm call (prohibition maintained)

---

**Phase 3 Status**: ✅ COMPLETE
**Verified By**: Claude Code
**Evidence**: All verification outputs above
