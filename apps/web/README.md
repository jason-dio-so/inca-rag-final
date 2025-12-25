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
