# Premium API Specification (Minimal - STEP 32)

**Status:** Minimal specification based on adapter expectations
**Source:** Derived from `apps/web/src/lib/api/premium/adapter.ts` and standard Korean insurance API patterns
**Note:** This is a placeholder until actual upstream API specifications (간편비교_api.txt, 한장비교_API.txt) are available.

---

## Constitutional Principle

**basePremium Source:** `data.monthlyPremSum` (ONLY)
- ❌ NO calculation from `data.cvrAmtArrLst`
- ❌ NO inference from policy documents
- ✅ ONLY use `monthlyPremSum` field from upstream response

---

## Common Response Structure

All Premium API endpoints return this structure:

### Success Response

```json
{
  "returnCode": "0000",
  "returnMsg": "정상처리",
  "data": {
    "insrCoCd": "001",
    "monthlyPremSum": 123620,
    "cvrAmtArrLst": [
      {
        "cvrNm": "암진단비",
        "cvrAmt": 50000000
      }
    ]
  }
}
```

### Error Response

```json
{
  "returnCode": "9999",
  "returnMsg": "시스템 오류",
  "data": null
}
```

### Field Definitions

- `returnCode`: "0000" = success, others = error
- `returnMsg`: Human-readable message (Korean)
- `data.insrCoCd`: Insurer code (string)
  - "001" = 삼성화재 (SAMSUNG)
  - "002" = 메리츠화재 (MERITZ)
  - "004" = KB손해보험 (KB)
  - "005" = 한화손해보험 (HANWHA)
  - "006" = 롯데손해보험 (LOTTE)
  - "007" = DB손해보험 (DB)
  - "008" = 흥국화재 (HEUNGKUK)
- `data.monthlyPremSum`: **basePremium source** (number, nullable)
- `data.cvrAmtArrLst`: Coverage array (for display only, NOT for premium calculation)

---

## Endpoint 1: Simple Compare (간편비교)

**Purpose:** Get premium for simple comparison scenarios

### Request

**Method:** POST
**Path:** TBD (placeholder: `/simple-compare`)
**Content-Type:** `application/json`

**Payload:**
```json
{
  "age": 30,
  "gender": "M",
  "coverages": ["암진단비", "뇌출혈진단비"]
}
```

**Fields (Placeholder - adjust to actual spec):**
- `age` (number): Insured person age
- `gender` (string): "M" or "F"
- `coverages` (array): Coverage names (Korean)

### Response

Returns common response structure (see above).

### Adapter Mapping

```typescript
{
  insurer: mapInsurerCode(data.insrCoCd),    // "001" → "SAMSUNG"
  coverageName: data.cvrAmtArrLst?.[0]?.cvrNm || "상품",
  basePremium: data.monthlyPremSum,           // SSOT for basePremium
  multiplier: null                             // Rarely provided
}
```

---

## Endpoint 2: Onepage Compare (한장비교)

**Purpose:** Get premium for single proposal comparison

### Request

**Method:** POST
**Path:** TBD (placeholder: `/onepage-compare`)
**Content-Type:** `application/json`

**Payload:**
```json
{
  "proposalId": "SAMSUNG_001"
}
```

**Fields (Placeholder - adjust to actual spec):**
- `proposalId` (string): Proposal identifier

### Response

Returns common response structure (see above).

### Adapter Mapping

Same as Simple Compare (see above).

---

## Integration Notes

### Current Implementation

1. **Proxy Routes:**
   - `apps/web/src/app/api/premium/simple-compare/route.ts`
   - `apps/web/src/app/api/premium/onepage-compare/route.ts`

2. **Adapter:**
   - `apps/web/src/lib/api/premium/adapter.ts`
   - `adaptPremiumResponse()` function

3. **Type Definitions:**
   - `apps/web/src/lib/api/premium/types.ts`
   - `UpstreamPremiumResponse` interface

### Environment Variables

```bash
PREMIUM_API_BASE_URL=https://api.example.com  # Replace with actual URL
PREMIUM_API_KEY=your_api_key_here             # Optional
```

### Upstream Paths

**Current placeholders (to be confirmed with actual spec):**
- Simple: `${PREMIUM_API_BASE_URL}/simple-compare`
- Onepage: `${PREMIUM_API_BASE_URL}/onepage-compare`

---

## TODO: Actual Specification Integration

**Action Required:**
1. Obtain actual upstream API specifications:
   - 간편비교_api.txt
   - 한장비교_API.txt

2. Update this document with:
   - Exact endpoint paths
   - Complete request field schemas (required/optional)
   - Sample requests/responses from actual spec
   - Authentication requirements
   - Error codes

3. Update implementation files:
   - `types.ts`: Request/response interfaces
   - `route.ts`: Upstream paths
   - `README.md`: Smoke test curl examples

---

**Last Updated:** 2025-12-25
**Status:** Placeholder (awaiting actual API specs)
**Adapter Dependency:** `monthlyPremSum` field is REQUIRED in upstream response
