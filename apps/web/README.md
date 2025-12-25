# inca-RAG Web Frontend (STEP 28)

Contract-driven Frontend MVP based on Backend Contract (STEP 14-26) and UI Contract (STEP 27).

## Quick Start

### Development Mode (Mock Data)

```bash
cd apps/web
export DEV_MOCK_MODE=1
npm install
npm run dev
```

Visit: http://localhost:3000

### Production Mode (Real API)

```bash
cd apps/web
export DEV_MOCK_MODE=0
export API_BASE_URL=http://localhost:8000
npm install
npm run dev
```

## Features

### Contract-driven Architecture

- **SSOT**: `src/contracts/uiStateMap.ts` (from STEP 27)
- **View Resolver**: Automatically renders View based on Backend Contract state
- **Graceful Degradation**: Unknown states → FALLBACK_STATE (no errors)

### 5 View Components

1. **ComparableView**: `comparable:COMPARE:COVERAGE_MATCH_COMPARABLE`
2. **UnmappedView**: `unmapped:REQUEST_MORE_INFO:COVERAGE_UNMAPPED`
3. **PolicyRequiredView**: `policy_required:VERIFY_POLICY:DISEASE_SCOPE_VERIFICATION_REQUIRED`
4. **OutOfUniverseView**: `out_of_universe:REQUEST_MORE_INFO:COVERAGE_NOT_IN_UNIVERSE`
5. **UnknownStateView**: FALLBACK_STATE (Contract Drift)

### DEV_MOCK_MODE

- Scenario Switcher: Test all golden snapshots (A, B, C, D, E, UNKNOWN)
- No API calls required
- Instant scenario switching

### ChatGPT-style Layout

- **Left Panel**: Input/Search form
- **Right Panel**: Contract-driven Result view
- Responsive design

## Project Structure

```
apps/web/
├── src/
│   ├── components/
│   │   ├── views/            # 5 View components
│   │   ├── ui/               # UI primitives (Card, Button)
│   │   ├── ViewRenderer.tsx  # Contract-driven renderer
│   │   └── ScenarioSwitcher.tsx  # DEV mode tool
│   ├── contracts/
│   │   └── uiStateMap.ts     # SSOT (from STEP 27)
│   ├── lib/
│   │   ├── api/
│   │   │   └── compareClient.ts  # API client + mock
│   │   └── viewResolver.ts   # View resolution logic
│   ├── pages/
│   │   ├── index.tsx         # Main compare page
│   │   └── _app.tsx          # Next.js app
│   └── styles/
│       └── globals.css       # Tailwind CSS
├── package.json
├── tsconfig.json
└── next.config.js
```

## Environment Variables

- `DEV_MOCK_MODE`: `1` = Use golden snapshots, `0` = Real API
- `API_BASE_URL`: Backend API URL (default: `http://localhost:8000`)

## Limitations (inca-rag Dependency)

The following features require full inca-rag data pipeline:

- **Policy Document Viewer**: Document storage not in inca-RAG-final
- **All Insurers**: Only 3 insurers (SAMSUNG, MERITZ, KB) in seed data
- **Full Coverage Universe**: Limited proposal coverage in seed

These are handled as **placeholders** with "데이터 준비 중" messages.

## Constitutional Guarantees

- ✅ Backend Contract immutable (STEP 14-26)
- ✅ UI Contract SSOT (STEP 27 `uiStateMap.ts`)
- ✅ Unknown states → Graceful degradation
- ✅ No errors for valid contract states
- ✅ Data absence ≠ system error

## Testing Scenarios

### Scenario A (Comparable)
- Query: "일반암진단비"
- Insurers: SAMSUNG vs MERITZ
- Expected: ComparableView with amount comparison

### Scenario B (Unmapped)
- Query: "매핑안된담보"
- Expected: UnmappedView with retry CTA

### Scenario C (Policy Required)
- Query: "유사암진단금"
- Expected: PolicyRequiredView with evidence

### Scenario E (Out of Universe)
- Query: "다빈치 수술비"
- Expected: OutOfUniverseView with search again CTA

### Unknown State
- Scenario: UNKNOWN
- Expected: UnknownStateView with debug info

## Design Principles

- **Backend defines contract, Frontend adapts**
- **States = contract, Text = UX freedom**
- **Unknown states = graceful degradation**
- **Data absence ≠ system error**

---

## Premium API Integration (STEP 32+)

### Environment Variables

Required for premium comparison features:

```bash
# Premium API Configuration
PREMIUM_API_BASE_URL=https://api.premium-service.example.com
PREMIUM_API_KEY=your_api_key_here  # Optional, if authentication required
```

### Smoke Test (Reproducibility)

#### 1. Setup

Create `.env.local` in `apps/web/`:

```bash
# apps/web/.env.local
PREMIUM_API_BASE_URL=https://api.premium-service.example.com
PREMIUM_API_KEY=your_api_key_here
DEV_MOCK_MODE=0  # Use real API
```

#### 2. Start Development Server

```bash
cd apps/web
pnpm install
pnpm dev
```

Server starts at: http://localhost:3000

#### 3. Test Premium Proxy Endpoints

**Specification:** [docs/api/premium_api_spec.md](../../docs/api/premium_api_spec.md) (SSOT)
**Status:** ✅ Locked to upstream specifications

**Simple Compare (간편비교):**

```bash
curl -X POST http://localhost:3000/api/premium/simple-compare \
  -H "Content-Type: application/json" \
  -d '{
    "baseDt": "20251126",
    "birthday": "19760101",
    "customerNm": "홍길동",
    "sex": "1",
    "age": "50"
  }'
```

**Request Fields (All Required):**
- `baseDt`: Base date (YYYYMMDD format)
- `birthday`: Birthday (YYYYMMDD format)
- `customerNm`: Customer name
- `sex`: Gender ("1"=Male, "2"=Female)
- `age`: Age (string)

**Route Implementation:**
- File: `src/app/api/premium/simple-compare/route.ts`
- Upstream: GET `https://new-prod.greenlight.direct/public/prdata/prInfo`
- basePremium source: `outPrList[].monthlyPrem` (spec-confirmed)
- **Note:** Our proxy accepts POST (JSON body), converts to GET (query params) for upstream

Expected success response (from proxy):
```json
{
  "ok": true,
  "items": [
    {
      "insurer": "SAMSUNG",
      "coverageName": "암진단비",
      "basePremium": 123620,
      "multiplier": null
    }
  ]
}
```

Expected failure response (from proxy):
```json
{
  "ok": false,
  "reason": "UPSTREAM_ERROR",
  "message": "Upstream returned 500",
  "items": []
}
```

**Onepage Compare (한장비교):**

```bash
curl -X POST http://localhost:3000/api/premium/onepage-compare \
  -H "Content-Type: application/json" \
  -d '{
    "baseDt": "20251126",
    "birthday": "19760101",
    "customerNm": "홍길동",
    "sex": "1",
    "age": "50"
  }'
```

**Request Fields (All Required):**
- `baseDt`: Base date (YYYYMMDD format)
- `birthday`: Birthday (YYYYMMDD format)
- `customerNm`: Customer name
- `sex`: Gender ("1"=Male, "2"=Female)
- `age`: Age (string)

**Route Implementation:**
- File: `src/app/api/premium/onepage-compare/route.ts`
- Upstream: GET `https://new-prod.greenlight.direct/public/prdata/prDetail`
- basePremium source: `prProdLineCondOutIns[].monthlyPremSum` (spec-confirmed)
- **Note:** Our proxy accepts POST (JSON body), converts to GET (query params) for upstream

**Expected Response:** Same proxy contract as simple-compare

**Response Structure Differences:**
- prInfo (simple): Multiple insurers in flat `outPrList[]` array
- prDetail (onepage): Nested structure via `prProdLineCondOutSearchDiv[].prProdLineCondOutIns[]`
- Adapter handles both structures automatically via runtime shape detection

#### 4. Verification Checklist

- ✅ `ok: true` → `items[].basePremium` contains numeric values
- ✅ `ok: false` → `reason` and `message` fields present
- ✅ UI shows premium cards (not blank screen) even on failure
- ✅ PARTIAL/MISSING states explicitly rendered
- ✅ `/compare` endpoints still work (regression lock)

### Constitutional Guarantees (Premium)

- ✅ basePremium from spec fields ONLY:
  - prInfo: `outPrList[].monthlyPrem`
  - prDetail: `prProdLineCondOutIns[].monthlyPremSum`
  - NO calculation/inference from `cvrAmtArrLst` ❌
- ✅ Coverage name unmapped → graceful PARTIAL (not error)
- ✅ Premium failures isolated (doesn't affect /compare)
- ✅ No fake proposalId generation
- ✅ Explicit failure rendering (never blank screens)

### Mock Mode (Development)

For local testing without Premium API:

```bash
export DEV_MOCK_MODE=1
pnpm dev
```

Mock scenarios available (see `src/lib/api/mocks/priceScenarios.ts`):
- `A_PRICE_READY`: All insurers have premium data
- `A_PRICE_PARTIAL`: Mixed READY/PARTIAL/MISSING states
- `PRICE_COMPARISON`: KB vs SAMSUNG comparison

### Troubleshooting

**Issue:** Blank premium screen
**Solution:** Check browser console → verify `convertProxyResponseToCards()` returns cards even for failures

**Issue:** `basePremium` showing incorrect values
**Solution:** Verify upstream API returns `monthlyPremSum` field correctly

**Issue:** Coverage name mapping errors
**Solution:** This is NORMAL → system shows PARTIAL status (graceful degradation)

### Implementation Notes

- **API Specification:** [docs/api/premium_api_spec.md](../../docs/api/premium_api_spec.md) (SSOT - Spec-Driven Lock)
- Premium bridge: `src/lib/api/premium/bridge.ts`
- Proxy routes: `src/app/api/premium/*/route.ts`
- Type definitions: `src/lib/api/premium/types.ts`
- Adapter (basePremium mapping): `src/lib/api/premium/adapter.ts`
- Multiplier table: `src/lib/premium/multipliers.ts` (STEP 31-α)

For detailed implementation history, see:
- [docs/status/2025-12-25_step-32-delta.md](../../docs/status/2025-12-25_step-32-delta.md)
- [docs/status/2025-12-25_step-32.md](../../docs/status/2025-12-25_step-32.md)
- [docs/status/2025-12-25_step-31-alpha.md](../../docs/status/2025-12-25_step-31-alpha.md)
