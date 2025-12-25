#!/bin/bash
# Premium Upstream curl Reproduction Script (STEP 33-β-2)
#
# Purpose: Test upstream API with/without browser headers
# Usage: bash apps/web/scripts/premium_upstream_curl.sh

set -e

BASE_URL="https://new-prod.greenlight.direct"
PARAMS="baseDt=20251225&birthday=19760101&customerNm=Hong&sex=1&age=50"

echo "======================================"
echo "Premium Upstream API curl Test"
echo "======================================"
echo ""

# Test 1: prInfo without headers
echo "[1] prInfo (No Headers)"
echo "URL: $BASE_URL/public/prdata/prInfo?$PARAMS"
echo "--------------------------------------"
curl -v "$BASE_URL/public/prdata/prInfo?$PARAMS" 2>&1 | head -30
echo ""
echo ""

# Test 2: prInfo with browser headers
echo "[2] prInfo (Browser Headers)"
echo "URL: $BASE_URL/public/prdata/prInfo?$PARAMS"
echo "--------------------------------------"
curl -v "$BASE_URL/public/prdata/prInfo?$PARAMS" \
  -H "Accept: application/json, text/plain, */*" \
  -H "Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7" \
  -H "Cache-Control: no-cache" \
  -H "Pragma: no-cache" \
  -H "Referer: $BASE_URL/" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36" \
  2>&1 | head -30
echo ""
echo ""

# Test 3: prDetail without headers
echo "[3] prDetail (No Headers)"
echo "URL: $BASE_URL/public/prdata/prDetail?$PARAMS"
echo "--------------------------------------"
curl -v "$BASE_URL/public/prdata/prDetail?$PARAMS" 2>&1 | head -30
echo ""
echo ""

# Test 4: prDetail with browser headers
echo "[4] prDetail (Browser Headers)"
echo "URL: $BASE_URL/public/prdata/prDetail?$PARAMS"
echo "--------------------------------------"
curl -v "$BASE_URL/public/prdata/prDetail?$PARAMS" \
  -H "Accept: application/json, text/plain, */*" \
  -H "Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7" \
  -H "Cache-Control: no-cache" \
  -H "Pragma: no-cache" \
  -H "Referer: $BASE_URL/" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36" \
  2>&1 | head -30
echo ""
echo ""

echo "======================================"
echo "Test Complete"
echo "======================================"
echo ""
echo "Check for:"
echo "  - HTTP status (200 vs 400)"
echo "  - Response headers (server, content-length, set-cookie, location)"
echo "  - Response body (JSON vs empty)"
echo "  - WAF/cloudflare headers (cf-*, x-*)"
