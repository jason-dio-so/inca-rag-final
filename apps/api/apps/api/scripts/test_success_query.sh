#!/bin/bash
# Success Query Test - Verify 200 response for minimal dataset
# Purpose: Confirm DATA_INSUFFICIENT → 200 transition after seed

set -e

API_URL="${API_URL:-http://127.0.0.1:8001}"
ENDPOINT="/compare/view-model"

echo "=========================================="
echo "Success Query Test"
echo "API: $API_URL"
echo "=========================================="
echo

# Success Query (based on existing data)
echo "Test: 일반암진단비 comparison (SAMSUNG vs MERITZ)"
echo "--------------------------------------"

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_URL$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{"query":"일반암진단비","insurers":["SAMSUNG","MERITZ"]}')

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_STATUS:")

if [ "$HTTP_STATUS" != "200" ]; then
  echo "❌ FAILED: Expected 200, got $HTTP_STATUS"
  echo "$BODY" | python3 -m json.tool || echo "$BODY"
  exit 1
fi

# Validate schema_version
SCHEMA_VERSION=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('schema_version', ''))")
if [ "$SCHEMA_VERSION" != "next4.v2" ]; then
  echo "❌ FAILED: Expected schema_version=next4.v2, got $SCHEMA_VERSION"
  exit 1
fi

# Validate fact_table rows >= 2
ROW_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('fact_table', {}).get('rows', [])))")
if [ "$ROW_COUNT" -lt 2 ]; then
  echo "❌ FAILED: Expected rows>=2, got $ROW_COUNT"
  exit 1
fi

# Validate evidence_panels >= 1
EVIDENCE_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('evidence_panels', [])))")
if [ "$EVIDENCE_COUNT" -lt 1 ]; then
  echo "❌ FAILED: Expected evidence>=1, got $EVIDENCE_COUNT"
  exit 1
fi

echo "✅ SUCCESS:"
echo "   HTTP: 200"
echo "   schema_version: $SCHEMA_VERSION"
echo "   fact_table rows: $ROW_COUNT"
echo "   evidence_panels: $EVIDENCE_COUNT"
echo

echo "=========================================="
echo "✅ Success query test passed"
echo "=========================================="
