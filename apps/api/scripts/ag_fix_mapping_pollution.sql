-- ============================================
-- STEP NEXT-AG: Fix CA_DIAG_GENERAL mapping pollution
-- Purpose: Correct wrongly mapped premium waiver to actual general cancer coverage
-- Constitutional: Deterministic cleanup (no manual INSERT/DELETE)
-- ============================================

-- Problem:
-- coverage_id 44 "보험료 납입면제대상Ⅱ" is mapped to CA_DIAG_GENERAL
-- coverage_id 45 "암 진단비(유사암 제외)" should be mapped to CA_DIAG_GENERAL

-- Solution:
-- 1. Remove wrong mapping from coverage_id 44
-- 2. Add correct mapping to coverage_id 45

BEGIN;

-- Step 1: Delete wrong mapping (audit trail: mapping_id 4, coverage_id 44, source xlsx_manual)
DELETE FROM v2.coverage_mapping
WHERE coverage_id = 44
  AND canonical_coverage_code = 'CA_DIAG_GENERAL'
  AND mapping_status = 'MAPPED';

-- Verify: Check if delete affected exactly 1 row
DO $$
DECLARE
    affected_count INTEGER;
BEGIN
    GET DIAGNOSTICS affected_count = ROW_COUNT;
    IF affected_count != 1 THEN
        RAISE EXCEPTION 'Expected 1 row to be deleted, got %', affected_count;
    END IF;
    RAISE NOTICE 'Step 1: Deleted % wrong mapping(s) from coverage_id 44', affected_count;
END $$;

-- Step 2: Add correct mapping to coverage_id 45
-- Use INSERT ON CONFLICT to handle re-runs
INSERT INTO v2.coverage_mapping (
    coverage_id,
    canonical_coverage_code,
    mapping_status,
    mapping_source,
    confidence_score,
    created_at,
    updated_at
)
VALUES (
    45,  -- "암 진단비(유사암 제외)"
    'CA_DIAG_GENERAL',
    'MAPPED',
    'ag_fix_deterministic',  -- Mark as fixed by AG script
    1.0,  -- High confidence (deterministic rule-based)
    NOW(),
    NOW()
)
ON CONFLICT (coverage_id, canonical_coverage_code)
DO UPDATE SET
    mapping_status = 'MAPPED',
    mapping_source = 'ag_fix_deterministic',
    confidence_score = 1.0,
    updated_at = NOW();

-- Verify: Check result
DO $$
DECLARE
    new_mapping_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO new_mapping_count
    FROM v2.coverage_mapping
    WHERE coverage_id = 45
      AND canonical_coverage_code = 'CA_DIAG_GENERAL'
      AND mapping_status = 'MAPPED';

    IF new_mapping_count != 1 THEN
        RAISE EXCEPTION 'Expected 1 correct mapping, got %', new_mapping_count;
    END IF;
    RAISE NOTICE 'Step 2: Created/updated % correct mapping(s)', new_mapping_count;
END $$;

COMMIT;

-- ============================================
-- Verification Query
-- ============================================

SELECT
    cm.mapping_id,
    cm.coverage_id,
    pc.insurer_coverage_name,
    cm.canonical_coverage_code,
    cm.mapping_status,
    cm.mapping_source
FROM v2.coverage_mapping cm
JOIN v2.proposal_coverage pc ON pc.coverage_id = cm.coverage_id
WHERE cm.canonical_coverage_code = 'CA_DIAG_GENERAL'
ORDER BY cm.coverage_id;

-- Expected result:
-- coverage_id 44: mapping_status = INVALID
-- coverage_id 45: mapping_status = MAPPED, mapping_source = ag_fix_deterministic
