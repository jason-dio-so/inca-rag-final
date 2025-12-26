-- ========================================
-- V2 SSOT Minimal Seed Data
-- Purpose: Bootstrap v2 schema with minimal working dataset
-- Constitution: CLAUDE.md § Insurer/Product/Template SSOT
-- ========================================

SET search_path TO v2;

-- ========================================
-- 1. Insurer SSOT (8개 고정 enum)
-- ========================================

INSERT INTO v2.insurer (insurer_code, display_name, display_name_eng, is_active) VALUES
    ('SAMSUNG', '삼성화재', 'Samsung Fire & Marine Insurance', true),
    ('MERITZ', '메리츠화재', 'Meritz Fire & Marine Insurance', true),
    ('KB', 'KB손해보험', 'KB Insurance', true),
    ('HANA', '하나손해보험', 'Hana Insurance', true),
    ('DB', 'DB손해보험', 'DB Insurance', true),
    ('HANWHA', '한화손해보험', 'Hanwha General Insurance', true),
    ('LOTTE', '롯데손해보험', 'Lotte Insurance', true),
    ('HYUNDAI', '현대해상', 'Hyundai Marine & Fire Insurance', true)
ON CONFLICT (insurer_code) DO NOTHING;

-- ========================================
-- 2. Coverage Standard (신정원 통일 담보 코드 최소셋)
-- ========================================

INSERT INTO v2.coverage_standard (coverage_code, display_name, domain, coverage_type, priority, is_main) VALUES
    ('CA_DIAG_GENERAL', '암진단비(일반암)', '암', '진단', 1, true),
    ('CA_DIAG_SIMILAR', '암진단비(유사암)', '암', '진단', 10, false),
    ('BRAIN_HEMOR_DIAG', '뇌출혈진단비', '뇌', '진단', 1, true)
ON CONFLICT (coverage_code) DO NOTHING;

-- ========================================
-- 3. Product (최소 2개: SAMSUNG + MERITZ)
-- ========================================

INSERT INTO v2.product (product_id, insurer_code, internal_product_code, display_name, product_type, is_active) VALUES
    ('SAMSUNG_CANCER_2024', 'SAMSUNG', 'CANCER_2024', '무배당 내맘편한 암보험', '암보험', true),
    ('MERITZ_CANCER_2024', 'MERITZ', 'CANCER_2024', '(무)메리츠 암보험', '암보험', true)
ON CONFLICT (product_id) DO NOTHING;

-- ========================================
-- 4. Template (가입설계서 template 2개)
-- ========================================

-- SAMSUNG 가입설계서 template (v1.0, fingerprint = dummy hash)
INSERT INTO v2.template (
    template_id,
    product_id,
    template_type,
    version,
    fingerprint,
    effective_date
) VALUES (
    'SAMSUNG_CANCER_2024_proposal_202401_abc12345',
    'SAMSUNG_CANCER_2024',
    'proposal',
    '202401',
    'abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab', -- 64-char dummy SHA256
    '2024-01-01'
)
ON CONFLICT (template_id) DO NOTHING;

-- MERITZ 가입설계서 template (v1.0, fingerprint = dummy hash)
INSERT INTO v2.template (
    template_id,
    product_id,
    template_type,
    version,
    fingerprint,
    effective_date
) VALUES (
    'MERITZ_CANCER_2024_proposal_202401_def45678',
    'MERITZ_CANCER_2024',
    'proposal',
    '202401',
    'def4567890abcdef1234567890abcdef1234567890abcdef1234567890abcd', -- 64-char dummy SHA256
    '2024-01-01'
)
ON CONFLICT (template_id) DO NOTHING;

-- ========================================
-- 5. Document (가입설계서 문서 메타데이터 2개)
-- ========================================

INSERT INTO v2.document (
    document_id,
    template_id,
    file_path,
    file_hash,
    page_count,
    doc_type_priority
) VALUES (
    'SAMSUNG_CANCER_2024_proposal_202401_abc12345_11223344',
    'SAMSUNG_CANCER_2024_proposal_202401_abc12345',
    'data/proposals/samsung_cancer_2024_v1.pdf', -- placeholder
    '1122334455667788990011223344556677889900112233445566778899001122', -- 64-char dummy SHA256
    10,
    4 -- proposal = 4
)
ON CONFLICT (document_id) DO NOTHING;

INSERT INTO v2.document (
    document_id,
    template_id,
    file_path,
    file_hash,
    page_count,
    doc_type_priority
) VALUES (
    'MERITZ_CANCER_2024_proposal_202401_def45678_55667788',
    'MERITZ_CANCER_2024_proposal_202401_def45678',
    'data/proposals/meritz_cancer_2024_v1.pdf', -- placeholder
    '5566778899001122334455667788990011223344556677889900112233445566', -- 64-char dummy SHA256
    10,
    4 -- proposal = 4
)
ON CONFLICT (document_id) DO NOTHING;

-- ========================================
-- Validation Queries
-- ========================================

-- Row counts
DO $$
DECLARE
    insurer_count INT;
    coverage_count INT;
    product_count INT;
    template_count INT;
    document_count INT;
BEGIN
    SELECT COUNT(*) INTO insurer_count FROM v2.insurer;
    SELECT COUNT(*) INTO coverage_count FROM v2.coverage_standard;
    SELECT COUNT(*) INTO product_count FROM v2.product;
    SELECT COUNT(*) INTO template_count FROM v2.template;
    SELECT COUNT(*) INTO document_count FROM v2.document;

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'V2 SSOT Seed Data Applied';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Insurer count:          % (expected: 8)', insurer_count;
    RAISE NOTICE 'Coverage Standard count: % (expected: 3)', coverage_count;
    RAISE NOTICE 'Product count:          % (expected: 2)', product_count;
    RAISE NOTICE 'Template count:         % (expected: 2)', template_count;
    RAISE NOTICE 'Document count:         % (expected: 2)', document_count;
    RAISE NOTICE '============================================================';

    IF insurer_count <> 8 THEN
        RAISE WARNING 'Insurer count mismatch! Expected 8, got %', insurer_count;
    END IF;

    IF coverage_count < 3 THEN
        RAISE WARNING 'Coverage Standard count low! Expected at least 3, got %', coverage_count;
    END IF;

    IF product_count < 2 THEN
        RAISE WARNING 'Product count low! Expected at least 2, got %', product_count;
    END IF;

    IF template_count < 2 THEN
        RAISE WARNING 'Template count low! Expected at least 2, got %', template_count;
    END IF;

    IF document_count < 2 THEN
        RAISE WARNING 'Document count low! Expected at least 2, got %', document_count;
    END IF;
END $$;

-- Display sample data
SELECT '=== Insurers ===' AS section;
SELECT insurer_code, display_name, is_active FROM v2.insurer ORDER BY insurer_code;

SELECT '=== Coverage Standard ===' AS section;
SELECT coverage_code, display_name, domain, priority, is_main FROM v2.coverage_standard ORDER BY coverage_code;

SELECT '=== Products ===' AS section;
SELECT product_id, insurer_code, display_name, product_type FROM v2.product ORDER BY product_id;

SELECT '=== Templates ===' AS section;
SELECT template_id, product_id, template_type, version FROM v2.template ORDER BY template_id;

SELECT '=== Documents ===' AS section;
SELECT document_id, template_id, file_path, doc_type_priority FROM v2.document ORDER BY document_id;

RESET search_path;
