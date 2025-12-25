# Premium API Specification (STEP 32-κ - Spec-Driven Lock)

**Status:** Confirmed from upstream specifications
**Source:**
- `docs/api/upstream/premium_simple_compare_spec.txt`
- `docs/api/upstream/premium_onepage_compare_spec.txt`

**Last Updated:** 2025-12-25

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

**Specification Lock:** This document is now the SSOT for Premium API integration.
