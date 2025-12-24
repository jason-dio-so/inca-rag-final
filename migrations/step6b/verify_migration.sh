#!/bin/bash
# STEP 6-B Phase 1 Migration Verification Script
# Purpose: Verify candidate tables and functions are properly created

set -e

# Configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5433}
DB_NAME=${DB_NAME:-inca_rag_final}
DB_USER=${DB_USER:-postgres}

echo "==================================================================="
echo "STEP 6-B Phase 1 Migration Verification"
echo "==================================================================="
echo "Database: $DB_NAME @ $DB_HOST:$DB_PORT"
echo ""

# Function to run psql command
run_psql() {
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$1"
}

echo "1. Verifying chunk_entity_candidate table..."
echo "-------------------------------------------------------------------"
run_psql "\d chunk_entity_candidate"
echo ""

echo "2. Verifying amount_entity_candidate table..."
echo "-------------------------------------------------------------------"
run_psql "\d amount_entity_candidate"
echo ""

echo "3. Verifying candidate_metrics view..."
echo "-------------------------------------------------------------------"
run_psql "\d+ candidate_metrics"
echo ""

echo "4. Verifying confirm_candidate_to_entity() function..."
echo "-------------------------------------------------------------------"
run_psql "\df+ confirm_candidate_to_entity"
echo ""

echo "5. Checking indexes on chunk_entity_candidate..."
echo "-------------------------------------------------------------------"
run_psql "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'chunk_entity_candidate';"
echo ""

echo "6. Checking constraints on chunk_entity_candidate..."
echo "-------------------------------------------------------------------"
run_psql "SELECT conname, contype, pg_get_constraintdef(oid) AS definition FROM pg_constraint WHERE conrelid = 'chunk_entity_candidate'::regclass;"
echo ""

echo "7. Verifying row counts (should be 0 for new migration)..."
echo "-------------------------------------------------------------------"
run_psql "SELECT COUNT(*) AS chunk_entity_candidate_count FROM chunk_entity_candidate;"
run_psql "SELECT COUNT(*) AS amount_entity_candidate_count FROM amount_entity_candidate;"
echo ""

echo "==================================================================="
echo "Verification Complete"
echo "==================================================================="
echo ""
echo "If all commands succeeded, Phase 1 migration is properly applied."
echo "Save this output to docs/validation/STEP6B_MIGRATION_EVIDENCE.txt"
