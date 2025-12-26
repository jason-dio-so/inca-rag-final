# Test Data Setup for E2E Tests

**Purpose:** Minimal dataset to support Example 1-4 E2E tests

**Schema:** ViewModel v2 (next4.v2)

**Date:** 2025-12-26

---

## Current State

### Existing Data
- **data/담보명mapping자료.xlsx**: Coverage mapping (canonical codes)
- **data/가입설계서/**: Proposal documents (existing insurers)
- **Database tables:**
  - `proposal_coverage_universe`: Proposal coverage SSOT
  - `proposal_coverage_mapped`: Mapped coverages
  - `coverage_standard`: Shinjungwon canonical coverage codes

### Data Availability Check

Run the following to verify existing data supports Example 1-4:

```sql
-- Example 1: Premium sorting (requires coverage with amounts)
SELECT insurer, coverage_name_raw, amount_value
FROM proposal_coverage_universe
WHERE amount_value IS NOT NULL
ORDER BY amount_value ASC
LIMIT 4;

-- Example 2: Payout limit differences (requires payout_limit slot)
SELECT insurer, coverage_name_raw, payout_limit
FROM proposal_coverage_mapped
WHERE canonical_coverage_code LIKE '%CANCER_HOSP%';

-- Example 3: Specific insurers (SAMSUNG, MERITZ)
SELECT insurer, coverage_name_raw
FROM proposal_coverage_universe
WHERE insurer IN ('SAMSUNG', 'MERITZ')
  AND coverage_name_raw LIKE '%암진단비%';

-- Example 4: Disease-based coverage (제자리암, 경계성종양)
SELECT insurer, coverage_name_raw, disease_scope_raw
FROM proposal_coverage_mapped
WHERE disease_scope_raw LIKE '%제자리암%'
   OR disease_scope_raw LIKE '%경계성종양%';
```

---

## Minimal Data Requirements

### Example 1: Premium Sorting
**Required:**
- 4+ coverages with `amount_value` populated
- Diverse `amount_value` (for sorting demonstration)

**Columns:**
- `proposal_coverage_universe.amount_value` (NOT NULL)

**Test Query:**
```
"가장 저렴한 보험료 정렬순으로 4개만 비교해줘"
```

**Expected:**
- `sort_metadata.sort_by` = "amount_value" or similar
- `sort_metadata.sort_order` = "asc"
- `sort_metadata.limit` = 4

---

### Example 2: Condition Difference
**Required:**
- 2+ coverages with same `canonical_coverage_code`
- Different `payout_limit` values (e.g., "1~120일" vs "1~180일")

**Columns:**
- `proposal_coverage_mapped.payout_limit` (different values)

**Test Query:**
```
"암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
```

**Expected:**
- `filter_criteria.slot_key` = "payout_limit"
- `filter_criteria.difference_detected` = true
- `rows[].highlight` contains "payout_limit"

---

### Example 3: Specific Insurers
**Required:**
- Coverage "암진단비" in both SAMSUNG and MERITZ
- `mapping_status` = "MAPPED"

**Columns:**
- `proposal_coverage_universe.insurer` = "SAMSUNG", "MERITZ"
- `proposal_coverage_universe.coverage_name_raw` = "암진단비"

**Test Query:**
```
"삼성화재, 메리츠화재의 암진단비를 비교해줘"
```

**Expected:**
- `filter_criteria.insurer_filter` = ["SAMSUNG", "MERITZ"]
- `snapshot.insurers` only contains SAMSUNG, MERITZ

---

### Example 4: Disease-based O/X Matrix
**Required:**
- Coverages with `disease_scope_raw` = "제자리암, 경계성종양"
- Multiple coverage types (진단비, 수술비, etc.) for matrix
- SAMSUNG and MERITZ insurers

**Columns:**
- `proposal_coverage_mapped.disease_scope_raw` (contains disease names)
- Multiple coverages per insurer

**Test Query:**
```
"제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 상품 비교해줘"
```

**Expected:**
- `table_type` = "ox_matrix"
- `filter_criteria.disease_scope` = ["제자리암", "경계성종양"]
- O/X/— values in table

---

## Data Loading Strategy

### Option 1: Use Existing Data (Preferred)
If existing data in `data/가입설계서/` already covers Example 1-4:
- Run ingestion pipeline: `python apps/api/app/ingestion/run_ingestion.py`
- Verify data with SQL queries above
- No additional data needed

### Option 2: Add Minimal Test Data
If existing data doesn't cover examples:
- Create `data/test/` directory
- Add minimal test fixtures (CSV or JSON)
- Load into database via test script

**Test Data Structure:**
```json
{
  "test_coverages": [
    {
      "insurer": "SAMSUNG",
      "coverage_name_raw": "암진단비",
      "canonical_coverage_code": "CRE_CVR_CANCER_DIAG",
      "mapping_status": "MAPPED",
      "amount_value": 30000000,
      "disease_scope_raw": "유사암 제외"
    },
    {
      "insurer": "MERITZ",
      "coverage_name_raw": "암진단비",
      "canonical_coverage_code": "CRE_CVR_CANCER_DIAG",
      "mapping_status": "MAPPED",
      "amount_value": 20000000,
      "disease_scope_raw": "유사암 제외"
    }
  ]
}
```

### Option 3: Mock Data (Development Only)
- Mock `/compare` endpoint responses for testing
- Use Example 1-4 fixtures from `apps/web/src/fixtures/example-viewmodels.ts`
- **NOT recommended for E2E** (bypasses real data flow)

---

## Data Verification Script

Create a script to verify test data readiness:

```python
# tools/verify_test_data.py

import psycopg2
from typing import Dict, List

def check_example1_data(conn) -> bool:
    """Example 1: Premium sorting - needs 4+ coverages with amounts"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM proposal_coverage_universe
        WHERE amount_value IS NOT NULL
    """)
    count = cursor.fetchone()[0]
    print(f"Example 1: {count} coverages with amount_value")
    return count >= 4

def check_example2_data(conn) -> bool:
    """Example 2: Payout limit differences"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(DISTINCT payout_limit)
        FROM proposal_coverage_mapped
        WHERE canonical_coverage_code LIKE '%CANCER_HOSP%'
          AND payout_limit IS NOT NULL
    """)
    count = cursor.fetchone()[0]
    print(f"Example 2: {count} distinct payout_limits for CANCER_HOSP")
    return count >= 2

def check_example3_data(conn) -> bool:
    """Example 3: SAMSUNG + MERITZ 암진단비"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM proposal_coverage_universe
        WHERE insurer IN ('SAMSUNG', 'MERITZ')
          AND coverage_name_raw LIKE '%암진단비%'
    """)
    count = cursor.fetchone()[0]
    print(f"Example 3: {count} 암진단비 coverages (SAMSUNG/MERITZ)")
    return count >= 2

def check_example4_data(conn) -> bool:
    """Example 4: Disease-based coverage"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM proposal_coverage_mapped
        WHERE (disease_scope_raw LIKE '%제자리암%'
           OR disease_scope_raw LIKE '%경계성종양%')
          AND insurer IN ('SAMSUNG', 'MERITZ')
    """)
    count = cursor.fetchone()[0]
    print(f"Example 4: {count} disease-based coverages")
    return count >= 2

def main():
    conn = psycopg2.connect(
        host="localhost",
        database="inca_rag",
        user="postgres",
        password="postgres"
    )

    results = {
        "Example 1": check_example1_data(conn),
        "Example 2": check_example2_data(conn),
        "Example 3": check_example3_data(conn),
        "Example 4": check_example4_data(conn),
    }

    print("\n=== Test Data Verification ===")
    for example, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{example}: {status}")

    all_passed = all(results.values())
    if all_passed:
        print("\n✅ All examples have sufficient test data")
    else:
        print("\n❌ Some examples need additional test data")

    conn.close()

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python tools/verify_test_data.py
```

---

## Data Integrity Checks

Before running E2E tests, verify:

### Coverage Universe Lock
```sql
-- All mapped coverages must exist in universe
SELECT COUNT(*) FROM proposal_coverage_mapped m
LEFT JOIN proposal_coverage_universe u
  ON m.proposal_id = u.proposal_id
 AND m.insurer = u.insurer
WHERE u.proposal_id IS NULL;
-- Should return 0
```

### Mapping Status
```sql
-- Check mapping status distribution
SELECT mapping_status, COUNT(*)
FROM proposal_coverage_mapped
GROUP BY mapping_status;
-- Should show MAPPED, UNMAPPED, AMBIGUOUS counts
```

### Canonical Codes
```sql
-- Verify canonical codes resolve to coverage_standard
SELECT m.canonical_coverage_code, COUNT(*)
FROM proposal_coverage_mapped m
LEFT JOIN coverage_standard s
  ON m.canonical_coverage_code = s.cre_cvr_cd
WHERE m.mapping_status = 'MAPPED'
  AND s.cre_cvr_cd IS NULL
GROUP BY m.canonical_coverage_code;
-- Should return 0 (all canonical codes exist)
```

---

## Notes

**Constitutional Compliance:**
- Test data must follow single source of truth (Excel mapping)
- NO LLM-generated mappings
- NO manual overrides without Excel update

**Data Freshness:**
- Re-run ingestion if Excel mapping changes
- Verify database state before E2E tests

**Future:**
- Automate test data seeding (pytest fixtures)
- Add data cleanup script (restore to baseline)
- Version test data snapshots (git)

---

**Status:** ⏳ PENDING (verify existing data first)

**Next Steps:**
1. Run verification script
2. If data insufficient, add minimal test fixtures
3. Document actual test data location
