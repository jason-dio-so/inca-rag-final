# Ingestion Pipeline - Full Implementation (STEP 4)

## Overview

Complete ingestion pipeline from PDF → DB with 9 stages:

| Stage | Purpose | Output |
|-------|---------|--------|
| Discover | File scanning + hash | Manifest with SHA-256 |
| Register | DB metadata | insurer, product, document |
| Parse | PDF → text | data/derived/*.json |
| Chunk | Text → chunks | chunk (is_synthetic=false) |
| Embed | Embedding generation | chunk.embedding |
| Extract | Entity + amount | chunk_entity, amount_entity |
| Normalize | Coverage mapping | coverage_alias |
| Synthetic | Mixed chunk splitting | chunk (is_synthetic=true) |
| Validate | Report generation | artifacts/ingestion/<timestamp>/ |

## Prerequisites

### 1. PostgreSQL with schema
```bash
# Start PostgreSQL (if not running)
docker start postgres_inca_test

# Verify schema applied
docker exec postgres_inca_test psql -U postgres -d inca_rag_final_test \
  -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"
```

### 2. Python dependencies
```bash
pip install psycopg2-binary PyMuPDF openai
```

### 3. Environment variables
```bash
export OPENAI_API_KEY="sk-..."  # Required for Embed/Extract/Synthetic
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5433"
export POSTGRES_DB="inca_rag_final_test"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="testpass"
```

## Usage

### Full Pipeline

```bash
python -m apps.ingestion.cli_v2 run-all \
  --manifest data/manifest/docs_manifest_sample.csv
```

### Stage-by-Stage

```bash
# 1. Discover + Register
python -m apps.ingestion.cli_v2 discover --manifest data/manifest/docs_manifest_sample.csv
python -m apps.ingestion.cli_v2 register --manifest data/manifest/docs_manifest_sample.csv

# 2. Parse
python -m apps.ingestion.cli_v2 parse

# 3. Chunk
python -m apps.ingestion.cli_v2 chunk --chunk-size 1000

# 4. Embed (requires OPENAI_API_KEY)
python -m apps.ingestion.cli_v2 embed --batch-size 100

# 5. Extract (requires OPENAI_API_KEY)
python -m apps.ingestion.cli_v2 extract --limit 10

# 6. Normalize
python -m apps.ingestion.cli_v2 normalize

# 7. Synthetic (requires OPENAI_API_KEY)
python -m apps.ingestion.cli_v2 synthetic --limit 5

# 8. Validate
python -m apps.ingestion.cli_v2 validate
```

### Insurer-Specific

```bash
python -m apps.ingestion.cli_v2 run-all \
  --manifest data/manifest/docs_manifest.csv \
  --insurer SAMSUNG
```

## Data Flow

```
data/raw/SAMSUNG/약관/sample.pdf
  ↓ Parse
data/derived/document_1.json
  ↓ Chunk
chunk table (is_synthetic=false, page_number, content)
  ↓ Embed
chunk table (embedding vector[1536])
  ↓ Extract
chunk_entity (coverage_name, NULL coverage_code)
amount_entity (amount_value, NULL coverage_code)
  ↓ Normalize
coverage_alias (insurer_id, coverage_id FK)
chunk_entity (coverage_code FK updated)
amount_entity (coverage_code FK updated)
  ↓ Synthetic
chunk table (is_synthetic=true, synthetic_source_chunk_id)
  ↓ Validate
artifacts/ingestion/<timestamp>/summary.json
```

## Critical Design Principles

### 1. coverage_standard is Sacred

```python
# ❌ NEVER
cur.execute("INSERT INTO coverage_standard ...")

# ✅ ALWAYS
cur.execute("""
    INSERT INTO coverage_alias (insurer_id, coverage_id, ...)
    VALUES (%s, %s, ...)
""", (insurer_id, coverage_id))  # coverage_id must exist in coverage_standard
```

### 2. Synthetic Chunk Policy

```python
# ✅ Create synthetic chunk
meta = {
    "synthetic_type": "split",
    "synthetic_method": "v1_6_3_beta_2_split",
    "entities": {"coverage_code": "CA_DIAG_GENERAL"}
}

cur.execute("""
    INSERT INTO chunk (document_id, page_number, content, is_synthetic,
                      synthetic_source_chunk_id, meta)
    VALUES (%s, %s, %s, true, %s, %s)
""", (doc_id, page_num, content, source_chunk_id, json.dumps(meta)))

# ❌ NEVER use synthetic chunks for comparison
# WHERE clause MUST filter:
WHERE c.is_synthetic = false  # For compare/retrieval
```

### 3. Filtering by Columns, Not JSONB

```python
# ✅ Correct
WHERE c.is_synthetic = false

# ❌ Wrong (performance issue)
WHERE c.meta->>'synthetic_type' IS NULL
```

### 4. Idempotency via ON CONFLICT

```python
# ✅ Idempotent INSERT
cur.execute("""
    INSERT INTO chunk (document_id, page_number, content, is_synthetic, ...)
    VALUES (%s, %s, %s, %s, ...)
    ON CONFLICT DO NOTHING
""")
```

## DoD (Definition of Done) Checklist

- [ ] Parse → Chunk → Embed → Extract pipeline works
- [ ] coverage_standard unchanged (zero new rows)
- [ ] Synthetic policy: zero violations (CHECK constraint enforced)
- [ ] UNMAPPED coverage report generated
- [ ] Validation report shows:
  - [ ] Document stats by insurer/type
  - [ ] Chunk stats (original vs synthetic)
  - [ ] Mapping success rate
  - [ ] Zero FK violations
- [ ] Idempotency: 2nd run doesn't create duplicates
- [ ] Git commit + GitHub push

## Validation Report

After running `validate`, check:

```bash
cat artifacts/ingestion/<timestamp>/summary.json
```

Expected structure:
```json
{
  "timestamp": "20251223_180000",
  "document_stats": [...],
  "chunk_stats": {
    "original_chunks": 10,
    "synthetic_chunks": 2,
    "total_chunks": 12
  },
  "alias_stats": {
    "total_entities": 15,
    "mapped": 12,
    "unmapped": 3,
    "success_rate": 80.0
  },
  "unmapped_coverages": [
    {"coverage_name": "특수암진단금", "count": 3}
  ],
  "coverage_standard_violations": {
    "chunk_entity_invalid_codes": 0,
    "amount_entity_invalid_codes": 0,
    "coverage_alias_invalid_ids": 0
  },
  "synthetic_policy_violations": {
    "synthetic_without_source": 0,
    "non_synthetic_with_source": 0
  },
  "critical_violations": [],
  "validation_passed": true
}
```

## Troubleshooting

### Error: "PyMuPDF not found"
```bash
pip install PyMuPDF
```

### Error: "OPENAI_API_KEY not set"
```bash
export OPENAI_API_KEY="sk-..."
```

### Error: "FK violation: coverage_standard"
This is **expected** if coverage_standard is empty.

Solution:
1. Seed coverage_standard with canonical codes (manual step)
2. Or: Skip Normalize stage for initial validation

### Error: "Parsed document not found"
Run Parse stage before Chunk:
```bash
python -m apps.ingestion.cli_v2 parse
python -m apps.ingestion.cli_v2 chunk
```

## Next Steps (NOT in STEP 4)

- STEP 5: Backend API (Compare/Retrieval/Amount Bridge)
- STEP 6: Frontend UI
- STEP 7: coverage_standard seeding process
- STEP 8: Production deployment

## File Structure

```
apps/ingestion/
├── __init__.py
├── cli.py                    # Old CLI (Discover/Register only)
├── cli_v2.py                 # New CLI (Full pipeline)
├── db.py                     # DB connection/transaction
├── discover.py               # File scan + hash
├── models.py                 # Data models
├── register.py               # DB UPSERT (insurer/product/document)
├── parse/
│   ├── __init__.py
│   └── parser.py             # PDF → text
├── chunk/
│   ├── __init__.py
│   └── chunker.py            # Text → chunks
├── embed/
│   ├── __init__.py
│   └── embedder.py           # OpenAI embeddings
├── extract/
│   ├── __init__.py
│   └── extractor.py          # LLM entity/amount extraction
├── normalize/
│   ├── __init__.py
│   └── normalizer.py         # coverage_alias mapping
├── synthetic/
│   ├── __init__.py
│   └── generator.py          # Mixed chunk splitting
└── validate/
    ├── __init__.py
    └── validator.py          # Report generation
```

## Constitutional Principles (Do Not Violate)

1. ❌ Never INSERT into coverage_standard
2. ❌ Never use synthetic chunks for comparison
3. ❌ Never filter by meta JSONB (use columns)
4. ❌ Never modify schema.sql / schema_v2_additions.sql
5. ✅ Always use ON CONFLICT for idempotency
6. ✅ Always enforce FK constraints (fail is correct behavior)
7. ✅ Always generate UNMAPPED report (not suppress errors)

"코드가 아니라 DB가 헌법이다."
