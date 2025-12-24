-- ========================================
-- STEP 13: Proposal-Based Minimal Seed Data
-- Purpose: Enable Docker E2E comparison with Constitutional compliance
-- ========================================
-- Requirements:
-- - 3 insurers: SAMSUNG, MERITZ, KB
-- - Proposal-based Universe Lock (SSOT)
-- - MAPPED + UNMAPPED coverage states
-- - disease_scope_norm NULL + NOT NULL states
-- - Evidence required (proposal mandatory, policy conditional)
-- ========================================

-- Clean existing data (idempotent)
TRUNCATE TABLE coverage_disease_scope CASCADE;
TRUNCATE TABLE proposal_coverage_slots CASCADE;
TRUNCATE TABLE proposal_coverage_mapped CASCADE;
TRUNCATE TABLE proposal_coverage_universe CASCADE;
TRUNCATE TABLE disease_code_group_member CASCADE;
TRUNCATE TABLE disease_code_group CASCADE;
TRUNCATE TABLE disease_code_master CASCADE;
TRUNCATE TABLE coverage_alias CASCADE;
TRUNCATE TABLE coverage_code_alias CASCADE;
TRUNCATE TABLE coverage_standard CASCADE;
TRUNCATE TABLE document CASCADE;
TRUNCATE TABLE product CASCADE;
TRUNCATE TABLE insurer CASCADE;

-- ========================================
-- 1. Insurers (3 required)
-- ========================================
INSERT INTO insurer (insurer_code, insurer_name, insurer_name_eng, is_active) VALUES
('SAMSUNG', '삼성화재', 'Samsung Fire & Marine Insurance', true),
('MERITZ', '메리츠화재', 'Meritz Fire & Marine Insurance', true),
('KB', 'KB손해보험', 'KB Insurance', true);

-- ========================================
-- 2. Products (1 per insurer)
-- ========================================
INSERT INTO product (insurer_id, product_code, product_name, product_type, is_active)
SELECT i.insurer_id, 'CANCER_2024', i.insurer_name || ' 암보험 2024', '암보험', true
FROM insurer i
WHERE i.insurer_code IN ('SAMSUNG', 'MERITZ', 'KB');

-- ========================================
-- 3. Documents (Proposals)
-- ========================================
INSERT INTO document (product_id, doc_type, doc_name, file_path)
SELECT
    p.product_id,
    'proposal'::doc_type_enum,
    i.insurer_name || ' 암보험 가입설계서',
    '/seed/proposal_' || i.insurer_code || '_cancer_2024.pdf'
FROM product p
JOIN insurer i ON p.insurer_id = i.insurer_id
WHERE i.insurer_code IN ('SAMSUNG', 'MERITZ', 'KB');

-- ========================================
-- 4. Coverage Standard (Canonical Codes)
-- ========================================
INSERT INTO coverage_standard (coverage_code, coverage_name, coverage_category, coverage_type) VALUES
('CA_DIAG_GENERAL', '일반암진단비', '암보험', 'diagnosis'),
('CA_DIAG_SIMILAR', '유사암진단비', '암보험', 'diagnosis'),
('UNMAPPED_TEST', '매핑 테스트용 담보', '기타', 'diagnosis');

-- ========================================
-- 5. Coverage Alias (Excel mapping simulation)
-- ========================================
-- SAMSUNG aliases
INSERT INTO coverage_alias (coverage_code, alias_name, normalized_name, source)
VALUES
('CA_DIAG_GENERAL', '일반암진단금', '일반암진단금', 'excel_seed'),
('CA_DIAG_SIMILAR', '유사암진단금', '유사암진단금', 'excel_seed');

-- MERITZ aliases
INSERT INTO coverage_alias (coverage_code, alias_name, normalized_name, source)
VALUES
('CA_DIAG_GENERAL', '암진단금(일반암)', '암진단금일반암', 'excel_seed');

-- KB aliases
INSERT INTO coverage_alias (coverage_code, alias_name, normalized_name, source)
VALUES
('CA_DIAG_GENERAL', '일반암 진단비', '일반암진단비', 'excel_seed');

-- ========================================
-- 6. Proposal Coverage Universe (SSOT)
-- ========================================

-- SAMSUNG: 일반암진단금 (MAPPED)
INSERT INTO proposal_coverage_universe (
    insurer, proposal_id, coverage_name_raw,
    currency, amount_value,
    source_doc_id, source_page, source_span_text
) SELECT
    'SAMSUNG',
    'PROP_SAMSUNG_001',
    '일반암진단금',
    'KRW',
    50000000,
    d.document_id,
    1,
    '일반암 진단시 5,000만원 지급'
FROM document d
JOIN product p ON d.product_id = p.product_id
JOIN insurer i ON p.insurer_id = i.insurer_id
WHERE i.insurer_code = 'SAMSUNG' AND d.doc_type = 'proposal';

-- SAMSUNG: 유사암진단금 (MAPPED, will have disease_scope_norm)
INSERT INTO proposal_coverage_universe (
    insurer, proposal_id, coverage_name_raw,
    currency, amount_value,
    source_doc_id, source_page, source_span_text
) SELECT
    'SAMSUNG',
    'PROP_SAMSUNG_001',
    '유사암진단금',
    'KRW',
    5000000,
    d.document_id,
    2,
    '유사암 진단시 500만원 지급 (갑상선암, 제자리암, 경계성종양)'
FROM document d
JOIN product p ON d.product_id = p.product_id
JOIN insurer i ON p.insurer_id = i.insurer_id
WHERE i.insurer_code = 'SAMSUNG' AND d.doc_type = 'proposal';

-- MERITZ: 암진단금(일반암) (MAPPED)
INSERT INTO proposal_coverage_universe (
    insurer, proposal_id, coverage_name_raw,
    currency, amount_value,
    source_doc_id, source_page, source_span_text
) SELECT
    'MERITZ',
    'PROP_MERITZ_001',
    '암진단금(일반암)',
    'KRW',
    30000000,
    d.document_id,
    1,
    '일반암 진단시 3,000만원 지급'
FROM document d
JOIN product p ON d.product_id = p.product_id
JOIN insurer i ON p.insurer_id = i.insurer_id
WHERE i.insurer_code = 'MERITZ' AND d.doc_type = 'proposal';

-- KB: 일반암 진단비 (MAPPED)
INSERT INTO proposal_coverage_universe (
    insurer, proposal_id, coverage_name_raw,
    currency, amount_value,
    source_doc_id, source_page, source_span_text
) SELECT
    'KB',
    'PROP_KB_001',
    '일반암 진단비',
    'KRW',
    40000000,
    d.document_id,
    1,
    '일반암 진단시 4,000만원 지급'
FROM document d
JOIN product p ON d.product_id = p.product_id
JOIN insurer i ON p.insurer_id = i.insurer_id
WHERE i.insurer_code = 'KB' AND d.doc_type = 'proposal';

-- KB: 매핑안된담보 (UNMAPPED - for UX testing)
INSERT INTO proposal_coverage_universe (
    insurer, proposal_id, coverage_name_raw,
    currency, amount_value,
    source_doc_id, source_page, source_span_text
) SELECT
    'KB',
    'PROP_KB_001',
    '매핑안된담보',
    'KRW',
    1000000,
    d.document_id,
    2,
    '매핑안된 담보 예시'
FROM document d
JOIN product p ON d.product_id = p.product_id
JOIN insurer i ON p.insurer_id = i.insurer_id
WHERE i.insurer_code = 'KB' AND d.doc_type = 'proposal';

-- ========================================
-- 7. Proposal Coverage Mapped
-- ========================================

-- SAMSUNG 일반암진단금 (MAPPED)
INSERT INTO proposal_coverage_mapped (
    universe_id,
    canonical_coverage_code,
    mapping_status,
    mapping_method,
    confidence
) SELECT
    u.id,
    'CA_DIAG_GENERAL',
    'MAPPED'::mapping_status_enum,
    'excel_lookup',
    1.0
FROM proposal_coverage_universe u
WHERE u.insurer = 'SAMSUNG' AND u.coverage_name_raw = '일반암진단금';

-- SAMSUNG 유사암진단금 (MAPPED)
INSERT INTO proposal_coverage_mapped (
    universe_id,
    canonical_coverage_code,
    mapping_status,
    mapping_method,
    confidence
) SELECT
    u.id,
    'CA_DIAG_SIMILAR',
    'MAPPED'::mapping_status_enum,
    'excel_lookup',
    1.0
FROM proposal_coverage_universe u
WHERE u.insurer = 'SAMSUNG' AND u.coverage_name_raw = '유사암진단금';

-- MERITZ 암진단금(일반암) (MAPPED)
INSERT INTO proposal_coverage_mapped (
    universe_id,
    canonical_coverage_code,
    mapping_status,
    mapping_method,
    confidence
) SELECT
    u.id,
    'CA_DIAG_GENERAL',
    'MAPPED'::mapping_status_enum,
    'excel_lookup',
    1.0
FROM proposal_coverage_universe u
WHERE u.insurer = 'MERITZ' AND u.coverage_name_raw = '암진단금(일반암)';

-- KB 일반암 진단비 (MAPPED)
INSERT INTO proposal_coverage_mapped (
    universe_id,
    canonical_coverage_code,
    mapping_status,
    mapping_method,
    confidence
) SELECT
    u.id,
    'CA_DIAG_GENERAL',
    'MAPPED'::mapping_status_enum,
    'excel_lookup',
    1.0
FROM proposal_coverage_universe u
WHERE u.insurer = 'KB' AND u.coverage_name_raw = '일반암 진단비';

-- KB 매핑안된담보 (UNMAPPED)
INSERT INTO proposal_coverage_mapped (
    universe_id,
    canonical_coverage_code,
    mapping_status,
    mapping_method
) SELECT
    u.id,
    NULL,
    'UNMAPPED'::mapping_status_enum,
    'excel_lookup_failed'
FROM proposal_coverage_universe u
WHERE u.insurer = 'KB' AND u.coverage_name_raw = '매핑안된담보';

-- ========================================
-- 8. Proposal Coverage Slots
-- ========================================

-- SAMSUNG 일반암진단금 (disease_scope_norm = NULL)
INSERT INTO proposal_coverage_slots (
    mapped_id,
    canonical_coverage_code,
    disease_scope_raw,
    disease_scope_norm,
    payout_limit,
    currency,
    amount_value,
    payout_amount_unit,
    source_confidence,
    meta
) SELECT
    m.id,
    'CA_DIAG_GENERAL',
    '일반암',
    NULL,
    '{"type": "once", "count": 1, "period": "lifetime"}'::jsonb,
    'KRW',
    50000000,
    'once',
    'proposal_confirmed',
    jsonb_build_object(
        'evidence', jsonb_build_object(
            'document_id', u.source_doc_id,
            'page', 1,
            'span', '일반암 진단시 5,000만원 지급'
        )
    )
FROM proposal_coverage_mapped m
JOIN proposal_coverage_universe u ON m.universe_id = u.id
WHERE u.insurer = 'SAMSUNG' AND u.coverage_name_raw = '일반암진단금';

-- SAMSUNG 유사암진단금 (disease_scope_norm = NOT NULL)
INSERT INTO proposal_coverage_slots (
    mapped_id,
    canonical_coverage_code,
    disease_scope_raw,
    disease_scope_norm,
    payout_limit,
    currency,
    amount_value,
    payout_amount_unit,
    source_confidence,
    meta
) SELECT
    m.id,
    'CA_DIAG_SIMILAR',
    '유사암 (갑상선암, 제자리암, 경계성종양)',
    '{"include_group_id": 1, "exclude_group_id": null}'::jsonb,
    '{"type": "once", "count": 1, "period": "lifetime"}'::jsonb,
    'KRW',
    5000000,
    'once',
    'policy_required',
    jsonb_build_object(
        'evidence', jsonb_build_object(
            'document_id', u.source_doc_id,
            'page', 2,
            'span', '유사암 진단시 500만원 지급 (갑상선암, 제자리암, 경계성종양)'
        )
    )
FROM proposal_coverage_mapped m
JOIN proposal_coverage_universe u ON m.universe_id = u.id
WHERE u.insurer = 'SAMSUNG' AND u.coverage_name_raw = '유사암진단금';

-- MERITZ 암진단금(일반암) (disease_scope_norm = NULL)
INSERT INTO proposal_coverage_slots (
    mapped_id,
    canonical_coverage_code,
    disease_scope_raw,
    disease_scope_norm,
    payout_limit,
    currency,
    amount_value,
    payout_amount_unit,
    source_confidence,
    meta
) SELECT
    m.id,
    'CA_DIAG_GENERAL',
    '일반암',
    NULL,
    '{"type": "once", "count": 1, "period": "lifetime"}'::jsonb,
    'KRW',
    30000000,
    'once',
    'proposal_confirmed',
    jsonb_build_object(
        'evidence', jsonb_build_object(
            'document_id', u.source_doc_id,
            'page', 1,
            'span', '일반암 진단시 3,000만원 지급'
        )
    )
FROM proposal_coverage_mapped m
JOIN proposal_coverage_universe u ON m.universe_id = u.id
WHERE u.insurer = 'MERITZ' AND u.coverage_name_raw = '암진단금(일반암)';

-- KB 일반암 진단비 (disease_scope_norm = NULL)
INSERT INTO proposal_coverage_slots (
    mapped_id,
    canonical_coverage_code,
    disease_scope_raw,
    disease_scope_norm,
    payout_limit,
    currency,
    amount_value,
    payout_amount_unit,
    source_confidence,
    meta
) SELECT
    m.id,
    'CA_DIAG_GENERAL',
    '일반암',
    NULL,
    '{"type": "once", "count": 1, "period": "lifetime"}'::jsonb,
    'KRW',
    40000000,
    'once',
    'proposal_confirmed',
    jsonb_build_object(
        'evidence', jsonb_build_object(
            'document_id', u.source_doc_id,
            'page', 1,
            'span', '일반암 진단시 4,000만원 지급'
        )
    )
FROM proposal_coverage_mapped m
JOIN proposal_coverage_universe u ON m.universe_id = u.id
WHERE u.insurer = 'KB' AND u.coverage_name_raw = '일반암 진단비';

-- ========================================
-- 9. KCD-7 Disease Codes (for disease_scope_norm reference)
-- ========================================
INSERT INTO disease_code_master (kcd_code, kcd_name_ko, category, source) VALUES
('C00', '입술의 악성 신생물', 'C00-C97', 'KCD-7 Official'),
('C73', '갑상선의 악성 신생물', 'C00-C97', 'KCD-7 Official'),
('C44', '피부의 악성 신생물', 'C00-C97', 'KCD-7 Official'),
('D05', '유방의 제자리암종', 'D00-D09', 'KCD-7 Official'),
('D09', '기타 및 상세불명 부위의 제자리암종', 'D00-D09', 'KCD-7 Official'),
('D37', '구강 및 소화기관의 행동양식 불명 또는 미상의 신생물', 'D37-D48', 'KCD-7 Official'),
('D48', '기타 및 상세불명 부위의 행동양식 불명 또는 미상의 신생물', 'D37-D48', 'KCD-7 Official'),
('C97', '독립된 (원발성) 여러 부위의 악성 신생물', 'C00-C97', 'KCD-7 Official');

-- ========================================
-- 10. Disease Code Group (for SAMSUNG similar cancer)
-- ========================================
INSERT INTO disease_code_group (
    group_name,
    group_type,
    insurer,
    description,
    evidence_page,
    evidence_span_text
) VALUES (
    '삼성 유사암 (Seed)',
    'similar_cancer',
    'SAMSUNG',
    '유사암: 갑상선암(C73), 피부암(C44), 제자리암(D05-D09), 경계성종양(D37-D48)',
    10,
    '유사암: 갑상선암(C73), 피부암(C44), 제자리암(D05-D09), 경계성종양(D37-D48)'
);

-- ========================================
-- 11. Disease Code Group Members
-- ========================================
INSERT INTO disease_code_group_member (group_id, code_id, is_include)
SELECT
    1,
    code_id,
    true
FROM disease_code_master
WHERE kcd_code IN ('C73', 'C44', 'D05', 'D09', 'D37', 'D48');

-- ========================================
-- 12. Coverage Disease Scope (Policy evidence)
-- ========================================
INSERT INTO coverage_disease_scope (
    coverage_code,
    insurer,
    include_group_id,
    exclude_group_id,
    evidence_page,
    evidence_span_text
) VALUES (
    'CA_DIAG_SIMILAR',
    'SAMSUNG',
    1,
    NULL,
    10,
    '유사암: 갑상선암(C73), 피부암(C44), 제자리암(D05-D09), 경계성종양(D37-D48)'
);

-- ========================================
-- Verification Queries
-- ========================================
-- Run these to verify seed data:
-- SELECT COUNT(*) FROM insurer; -- Should be 3
-- SELECT COUNT(*) FROM proposal_coverage_universe; -- Should be 5
-- SELECT mapping_status, COUNT(*) FROM proposal_coverage_mapped GROUP BY mapping_status; -- Should show MAPPED and UNMAPPED
-- SELECT COUNT(*) FROM proposal_coverage_slots WHERE disease_scope_norm IS NULL; -- Should be >= 1
-- SELECT COUNT(*) FROM proposal_coverage_slots WHERE disease_scope_norm IS NOT NULL; -- Should be >= 1

