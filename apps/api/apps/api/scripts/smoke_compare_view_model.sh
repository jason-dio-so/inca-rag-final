#!/bin/bash
# Smoke test for /compare/view-model endpoint
# Purpose: Verify request contract (no 422) before E2E tests

set -e

API_URL="${API_URL:-http://127.0.0.1:8001}"
ENDPOINT="/compare/view-model"

echo "=========================================="
echo "Smoke Test: /compare/view-model"
echo "API: $API_URL"
echo "=========================================="
echo

# Test 1: Minimal request (query only)
echo "Test 1: Minimal request (query only)"
echo "--------------------------------------"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_URL$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{"query": "암진단비 비교해줘"}')

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_STATUS:")

if [ "$HTTP_STATUS" == "422" ]; then
  echo "❌ Test 1 FAILED: Got 422 (schema validation failed)"
  echo "$BODY" | python3 -m json.tool || echo "$BODY"
  exit 1
else
  echo "✅ Test 1 PASSED: No 422 (status: $HTTP_STATUS)"
fi
echo

# Test 2: With insurers list
echo "Test 2: With insurers list"
echo "--------------------------------------"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_URL$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{"query": "암진단비 비교해줘", "insurers": ["SAMSUNG", "MERITZ"]}')

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_STATUS:")

if [ "$HTTP_STATUS" == "422" ]; then
  echo "❌ Test 2 FAILED: Got 422 (schema validation failed)"
  echo "$BODY" | python3 -m json.tool || echo "$BODY"
  exit 1
else
  echo "✅ Test 2 PASSED: No 422 (status: $HTTP_STATUS)"
fi
echo

# Test 3: Legacy format (insurer_a + insurer_b)
echo "Test 3: Legacy format (insurer_a + insurer_b)"
echo "--------------------------------------"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_URL$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{"query": "암진단비 비교해줘", "insurer_a": "SAMSUNG", "insurer_b": "MERITZ"}')

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_STATUS:")

if [ "$HTTP_STATUS" == "422" ]; then
  echo "❌ Test 3 FAILED: Got 422 (schema validation failed)"
  echo "$BODY" | python3 -m json.tool || echo "$BODY"
  exit 1
else
  echo "✅ Test 3 PASSED: No 422 (status: $HTTP_STATUS)"
fi
echo

echo "=========================================="
echo "✅ All smoke tests passed (no 422)"
echo "=========================================="
echo
echo "Note: 500/424 errors are OK for this test."
echo "We only verify request schema contract."
