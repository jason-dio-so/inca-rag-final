# Premium API Specification (STEP 32-κ - Spec-Driven Lock)

**Status:** ⚠️ Spec/Access Requirement Mismatch Suspected - Customer Clarification Pending
**Source:**
- `docs/api/upstream/premium_simple_compare_spec.txt`
- `docs/api/upstream/premium_onepage_compare_spec.txt`

**Last Updated:** 2025-12-25
**Clarification Request:** `docs/api/premium_api_customer_clarification.md`

---

## Constitutional Principle

**basePremium Source (SSOT):**
- Simple Compare: `outPrList[].monthlyPrem`
- Onepage Compare: `prProdLineCondOutIns[].monthlyPremSum`

**Rules:**
- ❌ NO calculation from `cvrAmtArrLst`
- ❌ NO inference from policy documents
- ✅ ONLY use the specified monthly premium field

---

## API 1: Simple Compare (간편비교)

### Endpoint

**URL:** `https://new-prod.greenlight.direct/public/prdata/prInfo`
**Method:** `GET`
**Purpose:** Get premium list for simple comparison

### Request Parameters (Query String)

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `baseDt` | string | Yes | Base date (YYYYMMDD) | "20251126" |
| `birthday` | string | Yes | Birthday (YYYYMMDD) | "19760101" |
| `customerNm` | string | Yes | Customer name | "홍길동" |
| `sex` | string | Yes | Gender ("1"=M, "2"=F) | "1" |
| `age` | string | Yes | Age | "50" |

### Response Schema

```typescript
{
  customerSeq: number,
  customerIpSeq: number,
  compPlanId: number,
  outPrList: Array<{
    prProdLineCd: string,      // Product line code
    insCd: string,              // Insurer code (e.g., "N01", "N02")
    insNm: string,              // Insurer name
    prCd: string,               // Product code
    prNm: string,               // Product name
    prScore: number,            // Product score
    newDispYn: string,          // New display flag
    monthlyPrem: number,        // ★ basePremium source
    updateDt: string,           // Update date
    updatingYn: string          // Updating flag
  }>
}
```

### basePremium Mapping

```typescript
basePremium = response.outPrList[index].monthlyPrem
insurer = mapInsurerCode(response.outPrList[index].insCd)
coverageName = response.outPrList[index].prNm  // Product name
```

### Insurer Code Mapping

| `insCd` | Insurer Name | Our Code |
|---------|--------------|----------|
| N01 | 메리츠화재 | MERITZ |
| N02 | 한화손보 | HANWHA |
| N03 | 롯데손보 | LOTTE |
| N05 | 흥국화재 | HEUNGKUK |
| N08 | 삼성화재 | SAMSUNG |
| N09 | 현대해상 | HYUNDAI |
| N10 | KB손보 | KB |
| N13 | DB손보 | DB |

---

## API 2: Onepage Compare (한장비교)

### Endpoint

**URL:** `https://new-prod.greenlight.direct/public/prdata/prDetail`
**Method:** `GET`
**Purpose:** Get detailed premium for single proposal

### Request Parameters (Query String)

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `baseDt` | string | Yes | Base date (YYYYMMDD) | "20251126" |
| `birthday` | string | Yes | Birthday (YYYYMMDD) | "19760101" |
| `customerNm` | string | Yes | Customer name | "홍길동" |
| `sex` | string | Yes | Gender ("1"=M, "2"=F) | "1" |
| `age` | string | Yes | Age | "50" |

### Response Schema

```typescript
{
  calSubSeq: number,
  prProdLineCd: string,
  prProdLineNm: string,
  disSearchDiv: string | null,
  baseDate: string,
  nm: string | null,
  age: number,
  sex: string,
  prProdLineCondOutSearchDiv: Array<{
    searchDiv: string,
    prProdLineCondOutIns: Array<{
      insCd: string,              // Insurer code
      insNm: string,              // Insurer name
      prCd: string,               // Product code
      prNm: string,               // Product name
      insTrm: string,             // Insurance term
      pyTrm: string,              // Payment term
      rnwCycle: string,           // Renewal cycle
      prodType: string,           // Product type
      updateDt: string,           // Update date
      recommYn: string | null,    // Recommend flag
      monthlyPremSum: number,     // ★ basePremium source
      cvrAmtArrLst: Array<{       // Coverage list (for display ONLY)
        cvrDiv: string,
        dispOrder: number,
        cvrCd: string,
        cvrNm: string,
        creCvrCd: string,
        accAmt: number,
        accAmtNm: string,
        monthlyPrem: number,      // Individual coverage premium
        amtDispYn: string
      }>
    }>
  }>
}
```

### basePremium Mapping

```typescript
const ins = response.prProdLineCondOutSearchDiv[0].prProdLineCondOutIns[index]
basePremium = ins.monthlyPremSum  // ★ SSOT
insurer = mapInsurerCode(ins.insCd)
coverageName = ins.prNm  // Product name
// cvrAmtArrLst is for display only (NOT for premium calculation)
```

---

## Integration Notes

### 1. Our Proxy Adapter Mapping

File: `apps/web/src/lib/api/premium/adapter.ts`

**Simple Compare:**
```typescript
{
  insurer: mapInsurerCode(item.insCd),           // "N01" → "MERITZ"
  coverageName: item.prNm,                       // Product name
  basePremium: item.monthlyPrem,                 // ★ SSOT
  multiplier: null                                // Not provided
}
```

**Onepage Compare:**
```typescript
{
  insurer: mapInsurerCode(item.insCd),           // "N01" → "MERITZ"
  coverageName: item.prNm,                       // Product name
  basePremium: item.monthlyPremSum,              // ★ SSOT
  multiplier: null                                // Not provided
}
```

### 2. Authentication

**No API key required** - Public endpoints

### 3. Error Handling

Response does not include explicit error codes. Check:
- HTTP status code
- Response structure validity
- Presence of expected fields

---

## Environment Variables

```bash
# .env.local
PREMIUM_API_BASE_URL=https://new-prod.greenlight.direct
```

---

## Constitutional Guarantees

1. **basePremium = monthlyPrem OR monthlyPremSum** (ONLY)
2. **NO calculation** from cvrAmtArrLst
3. **Coverage name mismatch** → PARTIAL status (not error)
4. **GET method** (not POST) - pass params as query string
5. **Public API** - no authentication required

---

## Adapter Update Notes

**CRITICAL CHANGES NEEDED:**

1. **Method:** POST → GET
2. **Body → Query:** Request payload becomes query string parameters
3. **Field mapping:**
   - Simple: `monthlyPrem` (not `monthlyPremSum`)
   - Onepage: `monthlyPremSum`
4. **Response path:**
   - Simple: `outPrList[]`
   - Onepage: `prProdLineCondOutSearchDiv[].prProdLineCondOutIns[]`

---

## Implementation Status (STEP 32-λ-2 - Truth Lock)

**Last Updated:** 2025-12-25
**Status:** Spec-confirmed, Fixture-tested (offline), Live verification PENDING

### A. Spec-Confirmed (SSOT)

Structures documented in official specification files.

**Source:** `docs/api/upstream/premium_*_spec.txt` + this document (SSOT)

**prInfo (Simple Compare) - SSOT § API 1:**
- Response structure: Top-level `{ customerSeq, outPrList: [...], compPlanId }`
- basePremium field path: `outPrList[].monthlyPrem`
- Insurer code field: `insCd` (format: N01-N13)
- Method: GET with query parameters

**prDetail (Onepage Compare) - SSOT § API 2:**
- Response structure: Top-level `{ prProdLineCondOutSearchDiv: [...] }`
- basePremium field path: `prProdLineCondOutSearchDiv[].prProdLineCondOutIns[].monthlyPremSum`
- Coverage array: `cvrAmtArrLst[]` (present but NOT used for basePremium)
- Method: GET with query parameters

**Constitutional Rule:**
- ❌ NO calculation from `cvrAmtArrLst`
- ✅ ONLY use documented premium field

### B. Fixture-Tested (Offline)

Adapter behavior tested against SSOT-based fixtures without network dependency.

**Test Method:** Network-independent smoke test
**Execution:** `node apps/web/scripts/premium_adapter_smoke.mjs`
**Status:** Does NOT confirm live API behavior

**Fixtures Created:** 3
- `upstream_prInfo_sample.json` - Based on SSOT § API 1
- `upstream_prDetail_sample.json` - Based on SSOT § API 2
- `upstream_wrapped_sample.json` - Defensive wrapper case

**Test Scenarios:** 5
1. prInfo: basePremium extraction from `monthlyPrem`
2. prDetail: basePremium extraction from `monthlyPremSum`
3. Wrapped response: `{ returnCode, data }` handling
4. Null/undefined: Edge case handling
5. Error response: `returnCode !== "0000"` handling

**Test Assertions:**
- Adapter extracts from correct field paths per SSOT
- Unknown insurer codes handled gracefully
- `cvrAmtArrLst` NOT used for basePremium
- Wrapped/unwrapped responses both handled

**Limitation:** Fixtures are synthetic based on spec documentation, not captured from live API.

### C. Live-Observed (2025-12-25)

**Status:** ⚠️ SPEC/ACCESS MISMATCH - Customer Clarification Required

**Observation Date:** 2025-12-25 07:43 GMT
**Test Methods:** Next.js proxy, curl, browser DevTools

**Actual Upstream Behavior:**
- HTTP Status: 400 Bad Request
- Response Headers:
  - `Server: nginx`
  - `Content-Type: application/json`
  - `Content-Length: 0`
- Response Body: (empty)

**URLs Tested:**
```
https://new-prod.greenlight.direct/public/prdata/prInfo?baseDt=20251225&birthday=19760101&customerNm=Hong&sex=1&age=50
https://new-prod.greenlight.direct/public/prdata/prDetail?baseDt=20251225&birthday=19760101&customerNm=Hong&sex=1&age=50
```

**Variations Tested (all returned same 400):**
- customerNm: Korean (홍길동), ASCII (Hong), omitted
- Headers: default, browser-parity (User-Agent, Referer, Accept-Language)
- All parameter combinations

**Observed Facts:**
- nginx returns 400 before reaching application layer
- No error message in response body
- No authentication challenge headers (WWW-Authenticate, Set-Cookie)
- No redirect or location headers

**Conclusion:**
Spec indicates "Public API - no authentication required", but actual behavior suggests:
- Authentication/authorization required (not documented)
- Additional required parameters (not in spec)
- Incorrect base URL or environment
- IP whitelist or access restrictions

**Next Step:**
Customer clarification required. See: `docs/api/premium_api_customer_clarification.md`

**Integration Status:** BLOCKED pending customer response with correct access method.

### D. Defensive Handling (Not in SSOT)

Adapter handles structures NOT documented in SSOT for safety.

**Wrapped Response:** `{ returnCode, returnMsg, data }`
- SSOT status: NOT documented (spec shows top-level response)
- Adapter behavior: Unwraps `data` field if present, else uses top-level
- Live observation: PENDING (not confirmed via actual API call)
- Justification: Defensive programming for potential API changes

**Error Response:** `{ returnCode: "XXXX", returnMsg: "..." }`
- SSOT status: NOT documented (error format unspecified)
- Adapter behavior: Returns `ok: false, reason: UPSTREAM_ERROR`
- Live observation: PENDING

**Principle:** Adapter handles both documented and potential undocumented structures defensively.

---

**Specification Lock:** This document is now the SSOT for Premium API integration.
