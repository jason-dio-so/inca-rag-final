#!/usr/bin/env bash
# STEP 14-α: Docker API E2E Compare Endpoint Verification
# Purpose: Fresh DB → Schema → Seed → API → HTTP /compare → JSON response verification

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ARTIFACT_DIR="$PROJECT_ROOT/artifacts/step14"

echo "========================================="
echo "STEP 14-α Docker API E2E - Compare Endpoint"
echo "========================================="
echo ""

# [1/9] Cleanup previous runs
echo "[1/9] Cleaning up previous Docker containers..."
cd "$PROJECT_ROOT"
docker compose -f docker-compose.step14.yml down -v || true
rm -rf "$ARTIFACT_DIR"
mkdir -p "$ARTIFACT_DIR"

# [2/9] Start PostgreSQL
echo "[2/9] Starting PostgreSQL container..."
docker compose -f docker-compose.step14.yml up -d postgres
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Verify PostgreSQL is ready
for i in {1..30}; do
    if docker exec inca_pg_step14 pg_isready -U postgres > /dev/null 2>&1; then
        echo "PostgreSQL is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "ERROR: PostgreSQL failed to start after 30 seconds"
        exit 1
    fi
    echo "Waiting for PostgreSQL... ($i/30)"
    sleep 1
done

# [3/9] Apply schema
echo "[3/9] Applying schema (schema_universe_lock_minimal.sql)..."
docker exec -i inca_pg_step14 psql -U postgres -d inca_rag_final < \
    "$PROJECT_ROOT/docs/db/schema_universe_lock_minimal.sql"

# [4/9] Apply seed data
echo "[4/9] Applying seed data (seed_step13_minimal.sql)..."
docker exec -i inca_pg_step14 psql -U postgres -d inca_rag_final < \
    "$PROJECT_ROOT/docs/db/seed_step13_minimal.sql"

# [5/9] Start API container
echo "[5/9] Starting API container..."
docker compose -f docker-compose.step14.yml up -d api
echo "Waiting for API to be ready..."
sleep 10

# Verify API is ready
API_URL="http://localhost:8000"
for i in {1..60}; do
    if curl -sf "$API_URL/health" > /dev/null 2>&1; then
        echo "API is ready!"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "ERROR: API failed to start after 60 seconds"
        docker compose -f docker-compose.step14.yml logs api
        exit 1
    fi
    echo "Waiting for API... ($i/60)"
    sleep 1
done

# [6/9] Scenario A: Normal comparison (삼성 vs 메리츠 일반암진단비)
echo "[6/9] Testing Scenario A: Normal comparison (일반암진단비)..."
curl -X POST "$API_URL/compare" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "일반암진단비",
        "insurer_a": "SAMSUNG",
        "insurer_b": "MERITZ",
        "include_policy_evidence": false
    }' \
    -o "$ARTIFACT_DIR/scenario_a.json" \
    -w "\nHTTP Status: %{http_code}\n"

echo "Scenario A response saved to: $ARTIFACT_DIR/scenario_a.json"
cat "$ARTIFACT_DIR/scenario_a.json" | python3 -m json.tool

# [7/9] Scenario B: UNMAPPED coverage (KB 매핑안된담보)
echo ""
echo "[7/9] Testing Scenario B: UNMAPPED coverage (매핑안된담보)..."
curl -X POST "$API_URL/compare" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "매핑안된담보",
        "insurer_a": "KB",
        "insurer_b": null,
        "include_policy_evidence": false
    }' \
    -o "$ARTIFACT_DIR/scenario_b.json" \
    -w "\nHTTP Status: %{http_code}\n"

echo "Scenario B response saved to: $ARTIFACT_DIR/scenario_b.json"
cat "$ARTIFACT_DIR/scenario_b.json" | python3 -m json.tool

# [8/9] Scenario C: Disease scope required (삼성 유사암진단금)
echo ""
echo "[8/9] Testing Scenario C: Disease scope required (유사암진단금)..."
curl -X POST "$API_URL/compare" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "유사암진단금",
        "insurer_a": "SAMSUNG",
        "insurer_b": null,
        "include_policy_evidence": true
    }' \
    -o "$ARTIFACT_DIR/scenario_c.json" \
    -w "\nHTTP Status: %{http_code}\n"

echo "Scenario C response saved to: $ARTIFACT_DIR/scenario_c.json"
cat "$ARTIFACT_DIR/scenario_c.json" | python3 -m json.tool

# [9/9] Summary
echo ""
echo "========================================="
echo "STEP 14-α E2E Complete ✅"
echo "========================================="
echo ""
echo "Artifacts saved to: $ARTIFACT_DIR"
echo "  - scenario_a.json (Normal comparison)"
echo "  - scenario_b.json (UNMAPPED)"
echo "  - scenario_c.json (Disease scope)"
echo ""
echo "Next: Run pytest E2E tests"
echo "  E2E_DOCKER=1 python -m pytest tests/e2e/test_step14_api_compare_e2e.py -v"
echo ""
