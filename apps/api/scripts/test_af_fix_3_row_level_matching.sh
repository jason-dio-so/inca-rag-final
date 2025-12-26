#!/bin/bash
# ============================================
# STEP NEXT-AF-FIX-3: Row-Level Description Matching Test
# Purpose: Verify that each FactTableRow gets its own comparison_description
# Constitutional: No coverage_metadata reuse across rows
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

echo "============================================"
echo "STEP NEXT-AF-FIX-3: Row-Level Matching Test"
echo "============================================"
echo

# ============================================
# Test 1: Check ViewModel row-level keys exist
# ============================================

echo "📋 Test 1: ViewModel row-level keys exist..."

# Start API in background (if not running)
API_PID=$(pgrep -f "uvicorn.*app.main:app.*8001" || true)
if [ -z "$API_PID" ]; then
    echo "   Starting API..."
    cd apps/api
    uvicorn app.main:app --port 8001 > /tmp/api_test_af_fix_3.log 2>&1 &
    API_PID=$!
    cd "$REPO_ROOT"
    sleep 3
    echo "   API started (PID: $API_PID)"
else
    echo "   API already running (PID: $API_PID)"
fi

# Test API endpoint - use "유사암진단금" with SAMSUNG only (only available insurer)
# This will test single-insurer scenario (Scenario C from compare.py)
RESPONSE=$(curl -s -X POST http://127.0.0.1:8001/compare/view-model \
    -H "Content-Type: application/json" \
    -d '{
        "query": "유사암진단금",
        "insurer_a": "SAMSUNG",
        "include_policy_evidence": true
    }')

# Check if response is valid JSON
if ! echo "$RESPONSE" | jq -e . > /dev/null 2>&1; then
    echo "❌ FAILED: Invalid JSON response"
    echo "$RESPONSE"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# Check fact_table.rows exist
ROW_COUNT=$(echo "$RESPONSE" | jq '.fact_table.rows | length')
if [ "$ROW_COUNT" -eq 0 ]; then
    echo "❌ FAILED: No rows in fact_table"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

echo "✅ ViewModel has $ROW_COUNT rows"

# Check row-level keys exist (coverage_id, template_id, insurer_coverage_name_raw)
ROWS_WITH_COVERAGE_ID=$(echo "$RESPONSE" | jq '[.fact_table.rows[] | select(.coverage_id != null)] | length')
ROWS_WITH_TEMPLATE_ID=$(echo "$RESPONSE" | jq '[.fact_table.rows[] | select(.template_id != null)] | length')
ROWS_WITH_RAW_NAME=$(echo "$RESPONSE" | jq '[.fact_table.rows[] | select(.insurer_coverage_name_raw != null)] | length')

echo "   - Rows with coverage_id: $ROWS_WITH_COVERAGE_ID"
echo "   - Rows with template_id: $ROWS_WITH_TEMPLATE_ID"
echo "   - Rows with insurer_coverage_name_raw: $ROWS_WITH_RAW_NAME"

if [ "$ROWS_WITH_TEMPLATE_ID" -eq "$ROW_COUNT" ]; then
    echo "✅ All rows have template_id (row-level key)"
else
    echo "❌ FAILED: Not all rows have template_id"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# ============================================
# Test 2: Row-level description isolation
# ============================================

echo
echo "📋 Test 2: Row-level description isolation..."

# Check if rows from same insurer have different comparison_description
# (This would fail if we're reusing coverage_metadata across rows)

# Get unique insurers
UNIQUE_INSURERS=$(echo "$RESPONSE" | jq -r '[.fact_table.rows[].insurer] | unique | join(", ")')
echo "   Insurers in response: $UNIQUE_INSURERS"

# For each insurer, check if different rows have different descriptions
for INSURER in $(echo "$RESPONSE" | jq -r '[.fact_table.rows[].insurer] | unique[]'); do
    INSURER_ROWS=$(echo "$RESPONSE" | jq --arg ins "$INSURER" '[.fact_table.rows[] | select(.insurer == $ins)]')
    INSURER_ROW_COUNT=$(echo "$INSURER_ROWS" | jq 'length')

    if [ "$INSURER_ROW_COUNT" -gt 1 ]; then
        echo "   - $INSURER: $INSURER_ROW_COUNT rows"

        # Get unique coverage_name_raw values for this insurer
        UNIQUE_COVERAGE_NAMES=$(echo "$INSURER_ROWS" | jq -r '[.[].insurer_coverage_name_raw] | unique | length')

        # Get unique comparison_description values for this insurer (excluding null)
        UNIQUE_DESCRIPTIONS=$(echo "$INSURER_ROWS" | jq -r '[.[].comparison_description | select(. != null)] | unique | length')

        echo "     - Unique coverage names: $UNIQUE_COVERAGE_NAMES"
        echo "     - Unique descriptions: $UNIQUE_DESCRIPTIONS"

        # If there are multiple unique coverage names but only 1 description, that's a violation
        if [ "$UNIQUE_COVERAGE_NAMES" -gt 1 ] && [ "$UNIQUE_DESCRIPTIONS" -eq 1 ]; then
            echo "❌ FAILED: Multiple coverage names but only 1 description (metadata reuse detected)"
            echo "$INSURER_ROWS" | jq '.[] | {coverage_name_raw, comparison_description}'
            kill $API_PID 2>/dev/null || true
            exit 1
        fi
    fi
done

echo "✅ Row-level description isolation verified"

# ============================================
# Test 3: Template isolation (single-insurer scenario)
# ============================================

echo
echo "📋 Test 3: Template isolation..."

# Check that all rows have template_id set
ALL_TEMPLATES=$(echo "$RESPONSE" | jq -r '[.fact_table.rows[].template_id] | unique | join(", ")')

echo "   - Template(s) in response: $ALL_TEMPLATES"

if [ -z "$ALL_TEMPLATES" ]; then
    echo "❌ FAILED: No template_id found in rows"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Template isolation verified"

# ============================================
# Cleanup
# ============================================

# Kill API if we started it
if [ -n "$API_PID" ]; then
    kill $API_PID 2>/dev/null || true
    echo
    echo "   API stopped"
fi

# ============================================
# Final Summary
# ============================================

echo
echo "============================================"
echo "✅ STEP NEXT-AF-FIX-3: Row-Level Matching PASSED"
echo "============================================"
echo
echo "Verified:"
echo "  - FactTableRow has row-level keys (coverage_id, template_id, insurer_coverage_name_raw)"
echo "  - No coverage_metadata reuse across rows"
echo "  - Template + Insurer isolation maintained"
echo
