#!/bin/bash
# Migration Application Script for STEP NEXT-7
# Purpose: Apply admin_mapping workbench tables to test database
# Constitutional: Single source migration file, deterministic application

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== STEP NEXT-7 Migration Application ===${NC}"

# DB Connection parameters
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5433}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD:-testpass}"
DB_NAME="${POSTGRES_DB:-inca_rag_final_test}"

export PGPASSWORD="$DB_PASSWORD"

# Check if database is reachable
echo -e "${YELLOW}[1/4] Checking database connection...${NC}"
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
    echo -e "${RED}✗ Database not reachable at $DB_HOST:$DB_PORT${NC}"
    echo -e "${YELLOW}Hint: Start database with: docker-compose -f docker-compose.test.yml up -d${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Database connection OK${NC}"

# Apply migration
echo -e "${YELLOW}[2/4] Applying migration: step_next7_admin_mapping_workbench.sql${NC}"
MIGRATION_FILE="migrations/step_next7_admin_mapping_workbench.sql"

if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}✗ Migration file not found: $MIGRATION_FILE${NC}"
    exit 1
fi

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$MIGRATION_FILE" > /dev/null 2>&1
echo -e "${GREEN}✓ Migration applied${NC}"

# Verify tables created
echo -e "${YELLOW}[3/4] Verifying tables created...${NC}"
TABLES_QUERY="SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('mapping_event_queue', 'coverage_code_alias', 'coverage_name_map', 'admin_audit_log')
ORDER BY table_name;"

TABLES=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$TABLES_QUERY")

EXPECTED_TABLES=("admin_audit_log" "coverage_code_alias" "coverage_name_map" "mapping_event_queue")
CREATED_COUNT=0

for table in "${EXPECTED_TABLES[@]}"; do
    if echo "$TABLES" | grep -q "$table"; then
        echo -e "${GREEN}  ✓ $table${NC}"
        ((CREATED_COUNT++))
    else
        echo -e "${RED}  ✗ $table (MISSING)${NC}"
    fi
done

if [ $CREATED_COUNT -ne ${#EXPECTED_TABLES[@]} ]; then
    echo -e "${RED}✗ Migration verification failed: $CREATED_COUNT/${#EXPECTED_TABLES[@]} tables created${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All 4 tables verified${NC}"

# Check constraints
echo -e "${YELLOW}[4/4] Checking constraints...${NC}"
CONSTRAINTS_QUERY="SELECT constraint_name, table_name
FROM information_schema.table_constraints
WHERE table_name IN ('mapping_event_queue', 'coverage_code_alias', 'coverage_name_map')
AND constraint_type = 'UNIQUE'
ORDER BY table_name;"

CONSTRAINTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$CONSTRAINTS_QUERY")

if [ -n "$CONSTRAINTS" ]; then
    CONSTRAINT_COUNT=$(echo "$CONSTRAINTS" | grep -v '^$' | wc -l | tr -d ' ')
    echo -e "${GREEN}✓ Found $CONSTRAINT_COUNT UNIQUE constraints${NC}"
else
    echo -e "${YELLOW}⚠ No UNIQUE constraints found (may be OK if using partial index)${NC}"
fi

echo -e "${GREEN}=== Migration Complete ===${NC}"
echo -e "Database: ${DB_NAME}"
echo -e "Host: ${DB_HOST}:${DB_PORT}"
echo -e "Tables: mapping_event_queue, coverage_code_alias, coverage_name_map, admin_audit_log"
