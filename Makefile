.PHONY: help test test-contract test-integration test-unit step6b-verify-db

# Default target
help:
	@echo "inca-RAG-final Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  test                 - Run all tests (contract + integration + unit)"
	@echo "  test-contract        - Run contract tests only"
	@echo "  test-integration     - Run integration tests only"
	@echo "  test-unit            - Run unit tests only"
	@echo "  step6b-verify-db     - Verify STEP 6-B database migration (requires PostgreSQL)"
	@echo ""

# Test targets
test:
	pytest -q

test-contract:
	pytest tests/contract -q

test-integration:
	pytest tests/integration -q

test-unit:
	pytest tests/unit -q

# STEP 6-B DB verification
step6b-verify-db:
	@echo "==================================================================="
	@echo "STEP 6-B Phase 1: Database Migration Verification"
	@echo "==================================================================="
	@echo ""
	@echo "Prerequisites:"
	@echo "  - PostgreSQL running on localhost:5433"
	@echo "  - Database 'inca_rag_final' exists"
	@echo "  - Migration SQL applied"
	@echo ""
	@echo "Running verification script..."
	@echo ""
	@bash migrations/step6b/verify_migration.sh
	@echo ""
	@echo "==================================================================="
	@echo "If all checks passed, update docs/validation/STEP6B_PHASE1_VERIFICATION.md"
	@echo "with the output above and change status to COMPLETE."
	@echo "==================================================================="
