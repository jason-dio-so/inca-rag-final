# Ingestion Pipeline - STEP 3-Validate

## Overview

Minimal ingestion skeleton for validating STEP 3 design.

**Scope:**
- ✅ Discover: File scanning + SHA-256 hash calculation
- ✅ Register: DB UPSERT (insurer/product/document)

**NOT included:**
- ❌ PDF parsing
- ❌ Chunk/Embed/Extract/Normalize/Synthetic

## Prerequisites

1. PostgreSQL running with schema applied:
   ```bash
   docker run --name postgres_inca_test \
     -e POSTGRES_PASSWORD=testpass \
     -e POSTGRES_DB=inca_rag_final_test \
     -p 5433:5432 -d pgvector/pgvector:pg16

   # Apply schema
   psql -h localhost -p 5433 -U postgres -d inca_rag_final_test \
     -f docs/db/schema.sql
   psql -h localhost -p 5433 -U postgres -d inca_rag_final_test \
     -f docs/db/schema_v2_additions.sql
   ```

2. Python dependencies:
   ```bash
   pip install psycopg2-binary
   ```

## Usage

### Basic execution

```bash
cd /Users/cheollee/inca-RAG-final

python -m apps.ingestion.cli \
  --manifest data/manifest/docs_manifest_sample.csv \
  --dry-run false
```

### Dry run (skip DB writes)

```bash
python -m apps.ingestion.cli \
  --manifest data/manifest/docs_manifest_sample.csv \
  --dry-run true
```

### Custom base path

```bash
python -m apps.ingestion.cli \
  --manifest data/manifest/docs_manifest_sample.csv \
  --base-path /Users/cheollee/inca-RAG-final \
  --dry-run false
```

## Environment Variables

- `POSTGRES_HOST` (default: localhost)
- `POSTGRES_PORT` (default: 5433)
- `POSTGRES_DB` (default: inca_rag_final_test)
- `POSTGRES_USER` (default: postgres)
- `POSTGRES_PASSWORD` (default: testpass)

## Verification Queries

After running ingestion, verify with:

```sql
-- Check insurer
SELECT * FROM insurer WHERE insurer_code = 'SAMSUNG';

-- Check product
SELECT * FROM product WHERE product_code = 'SAM-CA-001';

-- Check document
SELECT d.document_type, d.file_hash
FROM document d
JOIN product p ON d.product_id = p.product_id
WHERE p.product_code = 'SAM-CA-001';

-- Count rows
SELECT 'insurer' as table_name, COUNT(*) FROM insurer
UNION ALL
SELECT 'product', COUNT(*) FROM product
UNION ALL
SELECT 'document', COUNT(*) FROM document;
```

## Idempotency Test

Run the CLI twice and verify row counts don't change:

```bash
# First run
python -m apps.ingestion.cli \
  --manifest data/manifest/docs_manifest_sample.csv

# Second run (should not create duplicates)
python -m apps.ingestion.cli \
  --manifest data/manifest/docs_manifest_sample.csv

# Verify counts are identical
psql -h localhost -p 5433 -U postgres -d inca_rag_final_test \
  -c "SELECT COUNT(*) FROM insurer; SELECT COUNT(*) FROM product; SELECT COUNT(*) FROM document;"
```

## Design Principles

1. **Idempotency**: ON CONFLICT DO UPDATE ensures re-runs don't create duplicates
2. **신정원 코드 정합**: This validation does NOT touch `coverage_standard` or `coverage_alias`
3. **Synthetic 정책**: This validation does NOT touch `chunk` table
4. **File hash tracking**: SHA-256 hash calculated for all files
5. **UPSERT-based**: No DELETE operations, only INSERT/UPDATE

## File Structure

```
apps/ingestion/
├── __init__.py           # Package metadata
├── cli.py                # Entry point
├── discover.py           # File scanning + hash
├── register.py           # DB UPSERT logic
├── models.py             # Data models
├── db.py                 # DB connection/transaction
└── README.md             # This file
```

## Next Steps (NOT in STEP 3-Validate)

- STEP 4: Implement Parse/Chunk/Embed/Extract/Normalize/Synthetic
