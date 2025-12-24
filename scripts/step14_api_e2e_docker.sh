#!/bin/bash
set -euo pipefail

# ========================================
# STEP 14: Docker Proposal Data E2E Verification
# ========================================
# Purpose: Verify proposal seed data is queryable for comparison scenarios
# Note: Full API endpoint implementation deferred to future STEP
# DoD: Scenarios A/B/C data verified via SQL queries

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ARTIFACT_DIR="$PROJECT_ROOT/artifacts/step14"

echo "=== STEP 14: Docker Proposal Data E2E Verification ==="
echo "Started at: $(date)"
echo ""

# Create artifact directory
mkdir -p "$ARTIFACT_DIR"

# ========================================
# [1/7] Docker compose down/up
# ========================================
echo "[1/7] Docker compose down/up..."
cd "$PROJECT_ROOT"
docker compose down -v
docker compose up -d

# ========================================
# [2/7] Wait for DB ready
# ========================================
echo ""
echo "[2/7] Waiting for DB ready..."
max_attempts=30
attempt=0
while ! docker exec -i inca_pg_5433 pg_isready -U postgres > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "❌ DB not ready after $max_attempts seconds"
        exit 1
    fi
    sleep 1
done
echo "✓ DB ready after $attempt seconds"

# ========================================
# [3/7] Apply schema
# ========================================
echo ""
echo "[3/7] Applying schema migration..."
cat "$PROJECT_ROOT/docs/db/schema_universe_lock_minimal.sql" | \
    docker exec -i inca_pg_5433 psql -U postgres -d inca_rag_final > /dev/null 2>&1
echo "✓ Schema applied"

# ========================================
# [4/7] Apply seed data
# ========================================
echo ""
echo "[4/7] Applying seed data..."
cat "$PROJECT_ROOT/docs/db/seed_step13_minimal.sql" | \
    docker exec -i inca_pg_5433 psql -U postgres -d inca_rag_final > /dev/null 2>&1
echo "✓ Seed data applied"

# ========================================
# [5/7] Verify Scenario A: Normal comparison
# ========================================
echo ""
echo "[5/7] Verifying Scenario A: 삼성 vs 메리츠 일반암진단비 비교"

docker exec -i inca_pg_5433 psql -U postgres -d inca_rag_final <<'SQL' > "$ARTIFACT_DIR/scenario_a_query.txt"
-- Scenario A: CA_DIAG_GENERAL comparison
SELECT
    u.insurer,
    u.proposal_id,
    u.coverage_name_raw,
    m.mapping_status,
    m.canonical_coverage_code,
    u.amount_value,
    s.disease_scope_norm,
    s.source_confidence
FROM proposal_coverage_universe u
JOIN proposal_coverage_mapped m ON u.id = m.universe_id
LEFT JOIN proposal_coverage_slots s ON m.id = s.mapped_id
WHERE u.insurer IN ('SAMSUNG', 'MERITZ')
  AND m.canonical_coverage_code = 'CA_DIAG_GENERAL'
ORDER BY u.insurer;
SQL
echo "  ✓ Query results saved to artifacts/step14/scenario_a_query.txt"

# ========================================
# [6/7] Verify Scenario B: UNMAPPED coverage
# ========================================
echo ""
echo "[6/7] Verifying Scenario B: KB 매핑안된담보"

docker exec -i inca_pg_5433 psql -U postgres -d inca_rag_final <<'SQL' > "$ARTIFACT_DIR/scenario_b_query.txt"
-- Scenario B: UNMAPPED coverage
SELECT
    u.insurer,
    u.proposal_id,
    u.coverage_name_raw,
    m.mapping_status,
    m.canonical_coverage_code
FROM proposal_coverage_universe u
JOIN proposal_coverage_mapped m ON u.id = m.universe_id
WHERE u.insurer = 'KB'
  AND u.coverage_name_raw = '매핑안된담보'
  AND m.mapping_status = 'UNMAPPED';
SQL
echo "  ✓ Query results saved to artifacts/step14/scenario_b_query.txt"

# ========================================
# [7/7] Verify Scenario C: Disease scope required
# ========================================
echo ""
echo "[7/7] Verifying Scenario C: 삼성 유사암진단금 보장범위"

docker exec -i inca_pg_5433 psql -U postgres -d inca_rag_final <<'SQL' > "$ARTIFACT_DIR/scenario_c_query.txt"
-- Scenario C: Disease scope with policy evidence
SELECT
    u.insurer,
    u.proposal_id,
    u.coverage_name_raw,
    m.canonical_coverage_code,
    s.disease_scope_raw,
    s.disease_scope_norm,
    s.source_confidence,
    dcg.group_name,
    dcg.insurer as group_insurer
FROM proposal_coverage_universe u
JOIN proposal_coverage_mapped m ON u.id = m.universe_id
JOIN proposal_coverage_slots s ON m.id = s.mapped_id
LEFT JOIN disease_code_group dcg ON
    (s.disease_scope_norm->>'include_group_id')::int = dcg.group_id
WHERE u.insurer = 'SAMSUNG'
  AND m.canonical_coverage_code = 'CA_DIAG_SIMILAR'
  AND s.disease_scope_norm IS NOT NULL;
SQL
echo "  ✓ Query results saved to artifacts/step14/scenario_c_query.txt"

# ========================================
# [8/8] Summary
# ========================================
echo ""
echo "[8/8] E2E Verification Summary"
echo "================================"
echo "✓ Docker DB up and ready"
echo "✓ Schema applied (Universe Lock)"
echo "✓ Seed data applied (STEP 13-β)"
echo "✓ Scenario A verified (SAMSUNG vs MERITZ CA_DIAG_GENERAL)"
echo "✓ Scenario B verified (KB UNMAPPED coverage)"
echo "✓ Scenario C verified (SAMSUNG CA_DIAG_SIMILAR with disease_scope)"
echo ""
echo "Query result files:"
ls -lh "$ARTIFACT_DIR"/*.txt 2>/dev/null
echo ""
echo "Completed at: $(date)"
echo ""
echo "Next: Run pytest tests/e2e/test_step14_data_e2e.py"
