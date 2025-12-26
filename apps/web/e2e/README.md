# E2E Tests with Playwright

**Purpose:** Automated E2E validation of Real API → ViewModel → UI flow

**Coverage:** Example 1-4 from docs/customer/INCA_DIO_REQUIREMENTS.md

**Schema:** next4.v2

**Date:** 2025-12-26

---

## Quick Start

### Prerequisites

1. **Backend API running:**
   ```bash
   cd apps/api
   uvicorn app.main:app --port 8001
   ```

2. **Test data loaded:**
   - Verify database has coverage data for Example 1-4
   - See: docs/testing/TEST_DATA_SETUP.md

### Run Tests

```bash
# From apps/web directory
cd apps/web

# Run all E2E tests (headless)
npm run test:e2e

# Run with UI mode (interactive)
npm run test:e2e:ui

# Run with headed browser (visible)
npm run test:e2e:headed
```

**Note:** Frontend (port 3000) is automatically started by Playwright via `webServer` config.

---

## Test Suite

### Test File
- `e2e/compare-live.spec.ts`

### Test Cases

1. **Example 1: Premium Sorting**
   - Query: "가장 저렴한 보험료 정렬순으로 4개만 비교해줘"
   - Validates: ViewModel rendering, FactTable, forbidden phrases

2. **Example 2: Condition Difference**
   - Query: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
   - Validates: Filter criteria, highlighting, forbidden phrases

3. **Example 3: Specific Insurers**
   - Query: "삼성화재, 메리츠화재의 암진단비를 비교해줘"
   - Validates: Insurer filtering, forbidden phrases

4. **Example 4: O/X Matrix**
   - Query: "제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 상품 비교해줘"
   - Validates: O/X matrix rendering, forbidden phrases

5. **Evidence Panel Interaction**
   - Click insurer accordion → expand → collapse
   - Validates: Evidence panel rendering, click interaction

6. **Error Handling**
   - Simulate API error (500)
   - Validates: Error message display, no crash

---

## Configuration

### Playwright Config (`playwright.config.ts`)

```typescript
{
  testDir: './e2e',
  fullyParallel: false,  // Serial execution
  workers: 1,            // Single worker

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  }
}
```

### Key Settings

- **Serial execution:** Prevents API conflicts
- **Single worker:** Avoids port conflicts
- **Auto-start frontend:** `webServer` handles Next.js dev server
- **Timeout:** 120s for dev server startup

---

## Constitutional Compliance

### Forbidden Phrases Detection

Tests automatically check for forbidden phrases:
- ❌ "추천", "권장", "선택하세요" (recommendation)
- ❌ "더 좋다", "유리하다", "불리하다" (judgment)
- ❌ "사실상", "유사", "비슷" (interpretation - except "유사암")
- ❌ "종합적으로", "판단", "평가" (inference)

**Test fails if forbidden phrases detected in UI.**

### Allowed Expressions

- ✅ "다릅니다", "같습니다" (difference/sameness)
- ✅ "보장", "미보장", "O", "X" (coverage facts)
- ✅ "정렬", "최저", "최고" (sorting - NO judgment)
- ✅ "약관 확인 필요" (evidence requirement)

---

## Test Data Requirements

### Minimum Data for Example 1-4

**Example 1:** 4+ coverages with `amount_value`

**Example 2:** 2+ coverages with different `payout_limit`

**Example 3:** SAMSUNG + MERITZ "암진단비" coverages

**Example 4:** SAMSUNG + MERITZ disease-based coverages (제자리암/경계성종양)

**Verification:**
```bash
# Run test data verification script
python tools/verify_test_data.py
```

See: `docs/testing/TEST_DATA_SETUP.md`

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd apps/web
          npm ci
          npx playwright install --with-deps chromium

      - name: Start Backend API
        run: |
          cd apps/api
          uvicorn app.main:app --port 8001 &
          sleep 5

      - name: Run E2E tests
        run: |
          cd apps/web
          npm run test:e2e

      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: apps/web/playwright-report/
```

---

## Troubleshooting

### Tests Fail: "timeout waiting for page"

**Cause:** Backend API not running or slow

**Solution:**
```bash
# Ensure backend is running on port 8001
curl http://localhost:8001/health

# Check backend logs
cd apps/api
uvicorn app.main:app --port 8001 --reload
```

### Tests Fail: "forbidden phrase detected"

**Cause:** Backend returned judgment/recommendation text

**Solution:**
- Check backend ViewModel assembler
- Verify no LLM-generated text in response
- Review Constitutional compliance (CLAUDE.md)

### Tests Fail: "element not found"

**Cause:** Backend returned UNMAPPED/OUT_OF_UNIVERSE

**Solution:**
- Verify test data exists (see TEST_DATA_SETUP.md)
- Check coverage mapping (Excel)
- Review proposal_coverage_universe table

### Frontend port 3000 already in use

**Cause:** Dev server already running

**Solution:**
```bash
# Kill existing process
lsof -ti:3000 | xargs kill -9

# Or use reuseExistingServer (default in config)
```

---

## Development Workflow

### Adding New Tests

1. Create new test in `e2e/compare-live.spec.ts`
2. Follow existing pattern (click button → verify rendering)
3. Add forbidden phrase check
4. Run locally: `npm run test:e2e:headed`
5. Verify pass before commit

### Debugging Tests

```bash
# UI mode (interactive)
npm run test:e2e:ui

# Headed mode (visible browser)
npm run test:e2e:headed

# Debug mode
npx playwright test --debug

# Show report
npx playwright show-report
```

### Updating Snapshots

If UI changes are intentional:
```bash
# Update visual snapshots (if using)
npx playwright test --update-snapshots
```

---

## Performance

### Expected Execution Time

- Single test: ~5-10s
- Full suite (6 tests): ~30-60s
- CI execution: ~60-120s (including setup)

### Optimization

- Use `reuseExistingServer: true` for local dev
- Run serially (workers: 1) to avoid conflicts
- Cache Playwright browsers in CI

---

## Notes

**Real API Only:**
- Tests use actual /compare endpoint
- NO mocking/MSW/fixtures
- Deterministic: same query → same ViewModel

**Data Requirements:**
- Tests assume Example 1-4 data exists in database
- See TEST_DATA_SETUP.md for minimum data requirements

**Constitutional Compliance:**
- All tests validate forbidden phrases
- Tests fail if recommendation/judgment detected

**Future Enhancements:**
- Visual regression testing
- Accessibility testing (a11y)
- Performance testing (Lighthouse)
- Cross-browser testing (Firefox, Safari)

---

**Last Updated:** 2025-12-26

**Maintainer:** inca-rag-final team
