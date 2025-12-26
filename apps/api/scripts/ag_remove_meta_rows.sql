-- ============================================
-- STEP NEXT-AG: Remove meta rows from proposal_coverage
-- Purpose: Clean up non-coverage metadata rows (headers, customer info, etc.)
-- Constitutional: Deterministic cleanup with audit trail
-- ============================================

-- Meta Row Identification Rules (Deterministic):
-- 1. Keyword-based (Korean)
--    - "통합고객", "보험나이변경일", "보험나이", "고객", "피보험자", "계약자"
--    - "주계약", "선택계약", "특약", "계약정보", "가입내용", "가입내역"
--    - "담보명", "보장내용", "가입금액", "보험기간", "납입기간" (table headers)
-- 2. Pattern-based
--    - Empty amount_value AND descriptive text only
--    - Row type already marked as META_HEADER

BEGIN;

-- Step 1: Identify meta rows (read-only check first)
DO $$
DECLARE
    meta_row_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO meta_row_count
    FROM v2.proposal_coverage
    WHERE
        -- Pattern 1: Customer/contract metadata
        insurer_coverage_name ~ '(통합고객|보험나이변경일|보험나이|고객|피보험자|계약자)'
        OR insurer_coverage_name ~ '(주계약|선택계약|특약|계약정보|가입내용|가입내역)'
        -- Pattern 2: Table headers
        OR insurer_coverage_name ~ '^(담보명|보장내용|가입금액|보험기간|납입기간)'
        -- Pattern 3: Empty amount + parenthetical description
        OR (amount_value IS NULL AND insurer_coverage_name ~ '\(.*:\s*.*\)')
        -- Pattern 4: Specific known meta row
        OR insurer_coverage_name LIKE '%보험나이변경일%';

    RAISE NOTICE 'Found % meta row(s) to remove', meta_row_count;

    IF meta_row_count = 0 THEN
        RAISE NOTICE 'No meta rows found - skip cleanup';
    END IF;
END $$;

-- Step 2: Delete meta rows (CASCADE will handle foreign keys)
-- Keep audit trail by logging before delete
CREATE TEMP TABLE meta_rows_to_delete AS
SELECT
    pc.coverage_id,
    pc.template_id,
    pc.insurer_coverage_name,
    pc.amount_value,
    CASE
        WHEN pc.insurer_coverage_name ~ '(통합고객|보험나이변경일|보험나이|고객|피보험자|계약자)' THEN 'customer_metadata'
        WHEN pc.insurer_coverage_name ~ '(주계약|선택계약|특약|계약정보|가입내용|가입내역)' THEN 'contract_metadata'
        WHEN pc.insurer_coverage_name ~ '^(담보명|보장내용|가입금액|보험기간|납입기간)' THEN 'table_header'
        WHEN pc.amount_value IS NULL AND pc.insurer_coverage_name ~ '\(.*:\s*.*\)' THEN 'empty_amount_description'
        ELSE 'other_meta'
    END AS meta_category
FROM v2.proposal_coverage pc
WHERE
    pc.insurer_coverage_name ~ '(통합고객|보험나이변경일|보험나이|고객|피보험자|계약자)'
    OR pc.insurer_coverage_name ~ '(주계약|선택계약|특약|계약정보|가입내용|가입내역)'
    OR pc.insurer_coverage_name ~ '^(담보명|보장내용|가입금액|보험기간|납입기간)'
    OR (pc.amount_value IS NULL AND pc.insurer_coverage_name ~ '\(.*:\s*.*\)')
    OR pc.insurer_coverage_name LIKE '%보험나이변경일%';

-- Log audit trail
RAISE NOTICE 'Meta rows to delete:';
SELECT coverage_id, insurer_coverage_name, meta_category FROM meta_rows_to_delete;

-- Delete meta rows (CASCADE will clean up foreign key references)
DELETE FROM v2.proposal_coverage
WHERE coverage_id IN (SELECT coverage_id FROM meta_rows_to_delete);

-- Verify deletion
DO $$
DECLARE
    deleted_count INTEGER;
    remaining_meta_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO deleted_count FROM meta_rows_to_delete;

    SELECT COUNT(*) INTO remaining_meta_count
    FROM v2.proposal_coverage pc
    WHERE
        pc.insurer_coverage_name ~ '(통합고객|보험나이변경일|보험나이|고객|피보험자|계약자)'
        OR pc.insurer_coverage_name ~ '(주계약|선택계약|특약|계약정보|가입내용|가입내역)'
        OR pc.insurer_coverage_name ~ '^(담보명|보장내용|가입금액|보험기간|납입기간)'
        OR (pc.amount_value IS NULL AND pc.insurer_coverage_name ~ '\(.*:\s*.*\)')
        OR pc.insurer_coverage_name LIKE '%보험나이변경일%';

    RAISE NOTICE 'Deleted % meta row(s)', deleted_count;
    RAISE NOTICE 'Remaining meta rows: %', remaining_meta_count;

    IF remaining_meta_count > 0 THEN
        RAISE WARNING 'Still found % meta rows after cleanup', remaining_meta_count;
    END IF;
END $$;

COMMIT;

-- ============================================
-- Verification Query
-- ============================================

-- Should return 0 rows
SELECT
    pc.coverage_id,
    pc.insurer_coverage_name,
    pc.amount_value,
    CASE
        WHEN pc.insurer_coverage_name ~ '(통합고객|보험나이변경일)' THEN 'SHOULD_NOT_EXIST'
        ELSE 'OK'
    END AS status
FROM v2.proposal_coverage pc
WHERE
    pc.insurer_coverage_name ~ '(통합고객|보험나이변경일|보험나이|고객|피보험자|계약자)'
    OR pc.insurer_coverage_name ~ '(주계약|선택계약|특약|계약정보|가입내용|가입내역)'
    OR pc.insurer_coverage_name ~ '^(담보명|보장내용|가입금액|보험기간|납입기간)'
    OR (pc.amount_value IS NULL AND pc.insurer_coverage_name ~ '\(.*:\s*.*\)')
    OR pc.insurer_coverage_name LIKE '%보험나이변경일%';

-- Expected result: 0 rows (all meta rows removed)
