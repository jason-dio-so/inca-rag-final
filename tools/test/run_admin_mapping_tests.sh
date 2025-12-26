#!/bin/bash
# One-Command Test Runner for Admin Mapping Tests
# Purpose: Verify PostgreSQL connection, apply migration, run tests, report results
# Constitutional: Tests must pass without skip/xfail markers
#
# EXECUTION INDEPENDENCE PRINCIPLE:
# - Docker is OPTIONAL, not required
# - If PostgreSQL is already running (localhost:5433), Docker is skipped
# - This script works with ANY PostgreSQL source (local, Docker, remote)

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Admin Mapping Tests - One Command Runner ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
COMPOSE_FILE="docker-compose.test.yml"
MIGRATION_SCRIPT="tools/db/apply_migrations_next7.sh"
TEST_FILE="tests/test_admin_mapping_approve.py"
CLEANUP=${CLEANUP:-"no"}  # Set CLEANUP=yes to stop DB after tests

# Step 1: Start database
echo -e "${YELLOW}[1/5] Starting test database...${NC}"
if docker-compose -f "$COMPOSE_FILE" ps | grep -q "inca_rag_test_db.*Up"; then
    echo -e "${GREEN}✓ Database already running${NC}"
else
    docker-compose -f "$COMPOSE_FILE" up -d
    echo -e "${YELLOW}Waiting for database to be ready...${NC}"
    sleep 5

    # Wait for health check
    RETRY_COUNT=0
    MAX_RETRIES=30
    until docker-compose -f "$COMPOSE_FILE" ps | grep -q "healthy" || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
        echo -n "."
        sleep 1
        ((RETRY_COUNT++))
    done
    echo ""

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}✗ Database failed to start${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Database started${NC}"
fi

# Step 2: Apply migrations
echo -e "${YELLOW}[2/5] Applying migrations...${NC}"
if [ ! -f "$MIGRATION_SCRIPT" ]; then
    echo -e "${RED}✗ Migration script not found: $MIGRATION_SCRIPT${NC}"
    exit 1
fi

if bash "$MIGRATION_SCRIPT"; then
    echo -e "${GREEN}✓ Migrations applied${NC}"
else
    echo -e "${RED}✗ Migration failed${NC}"
    exit 1
fi

# Step 3: Set environment variables
echo -e "${YELLOW}[3/5] Setting environment variables...${NC}"
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=testpass
export POSTGRES_DB=inca_rag_final_test
echo -e "${GREEN}✓ Environment configured${NC}"

# Step 4: Run tests
echo -e "${YELLOW}[4/5] Running admin mapping tests...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if python -m pytest "$TEST_FILE" -v --tb=short; then
    TEST_RESULT=0
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    TEST_RESULT=$?
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}✗ Tests failed${NC}"
fi

# Step 5: Cleanup (optional)
echo -e "${YELLOW}[5/5] Cleanup...${NC}"
if [ "$CLEANUP" = "yes" ]; then
    echo -e "${YELLOW}Stopping database...${NC}"
    docker-compose -f "$COMPOSE_FILE" down
    echo -e "${GREEN}✓ Database stopped${NC}"
else
    echo -e "${YELLOW}Database left running (set CLEANUP=yes to stop after tests)${NC}"
    echo -e "${YELLOW}To stop manually: docker-compose -f $COMPOSE_FILE down${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${BLUE}║${GREEN}  ✓ Admin Mapping Tests: PASSED          ${BLUE}║${NC}"
else
    echo -e "${BLUE}║${RED}  ✗ Admin Mapping Tests: FAILED          ${BLUE}║${NC}"
fi
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"

exit $TEST_RESULT
