-- ========================================
-- Universe Lock Minimal Schema
-- Purpose: STEP 11 E2E verification (Docker fresh DB)
-- NO vector extension, NO chunk tables
-- Constitutional tables ONLY
-- ========================================
-- Source: Extracted from docs/db/schema_current.sql
-- Date: 2025-12-24
-- ========================================

-- ========================================
-- 기준/마스터 계층 (Canonical Layer)
-- ========================================

-- 보험사 마스터
CREATE TABLE IF NOT EXISTS insurer (
    insurer_id SERIAL PRIMARY KEY,
    insurer_code VARCHAR(50) UNIQUE NOT NULL,
    insurer_name VARCHAR(200) NOT NULL,
    insurer_name_eng VARCHAR(200),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE insurer IS '보험사 마스터 데이터';

-- 보험 상품
CREATE TABLE IF NOT EXISTS product (
    product_id SERIAL PRIMARY KEY,
    insurer_id INTEGER NOT NULL REFERENCES insurer(insurer_id) ON DELETE CASCADE,
    product_code VARCHAR(100) NOT NULL,
    product_name VARCHAR(300) NOT NULL,
    product_type VARCHAR(100),
    sale_start_date DATE,
    sale_end_date DATE,
    is_active BOOLEAN DEFAULT true,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(insurer_id, product_code)
);

COMMENT ON TABLE product IS '보험 상품 마스터';

-- ========================================
-- Coverage 계층
-- ========================================

-- 신정원 표준 담보 코드 (READ-ONLY)
CREATE TABLE IF NOT EXISTS coverage_standard (
    coverage_code VARCHAR(100) PRIMARY KEY,
    coverage_name VARCHAR(300) NOT NULL,
    coverage_category VARCHAR(100),
    coverage_type VARCHAR(100),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE coverage_standard IS '신정원 통일 담보 코드 (canonical) - 자동 INSERT 금지';

-- 담보 코드 별칭 (coverage_code에 대한 alias)
CREATE TABLE IF NOT EXISTS coverage_code_alias (
    alias_id SERIAL PRIMARY KEY,
    coverage_code VARCHAR(100) NOT NULL REFERENCES coverage_standard(coverage_code) ON DELETE CASCADE,
    alias_code VARCHAR(100) UNIQUE NOT NULL,
    alias_name VARCHAR(300),
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE coverage_code_alias IS '담보 코드 별칭 (다른 체계와의 매핑용)';

-- 담보명 별칭 (표준 담보명의 variation)
CREATE TABLE IF NOT EXISTS coverage_alias (
    alias_id SERIAL PRIMARY KEY,
    coverage_code VARCHAR(100) NOT NULL REFERENCES coverage_standard(coverage_code) ON DELETE CASCADE,
    alias_name VARCHAR(300) NOT NULL,
    normalized_name VARCHAR(300),
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coverage_code, alias_name, source)
);

COMMENT ON TABLE coverage_alias IS '담보명 별칭 테이블 (보험사별 variation)';

-- ========================================
-- 문서 계층
-- ========================================

-- 문서 유형 enum
DO $$ BEGIN
    CREATE TYPE doc_type_enum AS ENUM (
        'proposal',
        'policy',
        'product_summary',
        'business_method',
        'terms',
        'other'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 문서
CREATE TABLE IF NOT EXISTS document (
    document_id SERIAL PRIMARY KEY,
    insurer_id INTEGER REFERENCES insurer(insurer_id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES product(product_id) ON DELETE CASCADE,
    doc_type doc_type_enum NOT NULL,
    doc_name VARCHAR(500) NOT NULL,
    file_path TEXT,
    file_hash VARCHAR(64),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE document IS '원본 문서 메타데이터';

-- ========================================
-- STEP 6-C: Proposal Universe Lock
-- ========================================

-- Mapping status enum
DO $$ BEGIN
    CREATE TYPE mapping_status_enum AS ENUM ('MAPPED', 'UNMAPPED', 'AMBIGUOUS');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 가입설계서 담보 원본 (Universe Lock SSOT)
CREATE TABLE IF NOT EXISTS proposal_coverage_universe (
    id SERIAL PRIMARY KEY,
    insurer VARCHAR(100) NOT NULL,
    proposal_id VARCHAR(200) NOT NULL,
    coverage_name_raw VARCHAR(500) NOT NULL,
    amount_value NUMERIC(15, 2),
    currency VARCHAR(10) DEFAULT 'KRW',
    source_doc_id INTEGER REFERENCES document(document_id) ON DELETE CASCADE,
    source_page INTEGER,
    source_span_text TEXT,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(insurer, proposal_id, coverage_name_raw)
);

COMMENT ON TABLE proposal_coverage_universe IS 'Universe Lock: 가입설계서 담보 = 비교 가능 담보의 절대 기준';

-- 가입설계서 담보 → 신정원 매핑
CREATE TABLE IF NOT EXISTS proposal_coverage_mapped (
    id SERIAL PRIMARY KEY,
    universe_id INTEGER NOT NULL REFERENCES proposal_coverage_universe(id) ON DELETE CASCADE UNIQUE,
    mapping_status mapping_status_enum NOT NULL,
    canonical_coverage_code VARCHAR(100) REFERENCES coverage_standard(coverage_code) ON DELETE SET NULL,
    mapping_candidates JSONB DEFAULT '[]',
    mapping_method VARCHAR(100),
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE proposal_coverage_mapped IS 'Excel 기반 매핑 결과 (MAPPED/UNMAPPED/AMBIGUOUS)';

-- Slot Schema v1.1.1
CREATE TABLE IF NOT EXISTS proposal_coverage_slots (
    id SERIAL PRIMARY KEY,
    mapped_id INTEGER NOT NULL REFERENCES proposal_coverage_mapped(id) ON DELETE CASCADE UNIQUE,
    canonical_coverage_code VARCHAR(100) REFERENCES coverage_standard(coverage_code) ON DELETE SET NULL,
    disease_scope_raw TEXT,
    disease_scope_norm JSONB,
    payout_limit JSONB,
    currency VARCHAR(10),
    amount_value NUMERIC(15, 2),
    payout_amount_unit VARCHAR(50),
    source_confidence VARCHAR(50),
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE proposal_coverage_slots IS 'Slot Schema v1.1.1: 구조화된 담보 정보';
COMMENT ON COLUMN proposal_coverage_slots.disease_scope_norm IS '정규화된 질병 범위 (그룹 참조)';

-- ========================================
-- Disease Code 3-Tier Model (STEP 6-C)
-- ========================================

-- Tier 1: KCD-7 Official Codes
CREATE TABLE IF NOT EXISTS disease_code_master (
    code_id SERIAL PRIMARY KEY,
    kcd_code VARCHAR(20) UNIQUE NOT NULL,
    kcd_name_ko VARCHAR(500) NOT NULL,
    kcd_name_en VARCHAR(500),
    category VARCHAR(10),
    is_leaf BOOLEAN DEFAULT true,
    source VARCHAR(100) DEFAULT 'KCD-7 Official',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE disease_code_master IS 'Tier 1: KCD-7 공식 배포본 (의학적 분류)';

-- Tier 2: Insurance Concept Groups
CREATE TABLE IF NOT EXISTS disease_code_group (
    group_id SERIAL PRIMARY KEY,
    group_name VARCHAR(200) NOT NULL,
    group_type VARCHAR(100) NOT NULL,
    insurer VARCHAR(100),
    description TEXT,
    evidence_doc_id INTEGER REFERENCES document(document_id) ON DELETE SET NULL,
    evidence_page INTEGER,
    evidence_span_text TEXT,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_name, insurer)
);

COMMENT ON TABLE disease_code_group IS 'Tier 2: 보험 개념 그룹 (유사암, 소액암 등)';
COMMENT ON COLUMN disease_code_group.insurer IS 'NULL = 의학적 범위만 허용';

-- Group membership
CREATE TABLE IF NOT EXISTS disease_code_group_member (
    member_id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES disease_code_group(group_id) ON DELETE CASCADE,
    code_id INTEGER NOT NULL REFERENCES disease_code_master(code_id) ON DELETE CASCADE,
    is_include BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, code_id)
);

COMMENT ON TABLE disease_code_group_member IS 'Group membership (include/exclude)';

-- Tier 3: Coverage → Disease Scope
CREATE TABLE IF NOT EXISTS coverage_disease_scope (
    scope_id SERIAL PRIMARY KEY,
    coverage_code VARCHAR(100) NOT NULL REFERENCES coverage_standard(coverage_code) ON DELETE CASCADE,
    insurer VARCHAR(100) NOT NULL,
    include_group_id INTEGER REFERENCES disease_code_group(group_id) ON DELETE SET NULL,
    exclude_group_id INTEGER REFERENCES disease_code_group(group_id) ON DELETE SET NULL,
    evidence_doc_id INTEGER REFERENCES document(document_id) ON DELETE SET NULL,
    evidence_page INTEGER,
    evidence_span_text TEXT,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coverage_code, insurer)
);

COMMENT ON TABLE coverage_disease_scope IS 'Tier 3: 담보별 질병 범위 (약관 근거)';

-- ========================================
-- Indexes
-- ========================================

-- insurer
CREATE INDEX IF NOT EXISTS idx_insurer_code ON insurer(insurer_code);

-- product
CREATE INDEX IF NOT EXISTS idx_product_insurer ON product(insurer_id);
CREATE INDEX IF NOT EXISTS idx_product_code ON product(product_code);

-- document
CREATE INDEX IF NOT EXISTS idx_document_insurer ON document(insurer_id);
CREATE INDEX IF NOT EXISTS idx_document_product ON document(product_id);
CREATE INDEX IF NOT EXISTS idx_document_type ON document(doc_type);

-- proposal_coverage_universe
CREATE INDEX IF NOT EXISTS idx_universe_insurer_proposal ON proposal_coverage_universe(insurer, proposal_id);
CREATE INDEX IF NOT EXISTS idx_universe_coverage_name ON proposal_coverage_universe(coverage_name_raw);

-- proposal_coverage_mapped
CREATE INDEX IF NOT EXISTS idx_mapped_status ON proposal_coverage_mapped(mapping_status);
CREATE INDEX IF NOT EXISTS idx_mapped_canonical ON proposal_coverage_mapped(canonical_coverage_code);

-- proposal_coverage_slots
CREATE INDEX IF NOT EXISTS idx_slots_canonical ON proposal_coverage_slots(canonical_coverage_code);

-- disease_code_master
CREATE INDEX IF NOT EXISTS idx_disease_kcd_code ON disease_code_master(kcd_code);

-- disease_code_group
CREATE INDEX IF NOT EXISTS idx_disease_group_insurer ON disease_code_group(insurer);
CREATE INDEX IF NOT EXISTS idx_disease_group_type ON disease_code_group(group_type);

-- disease_code_group_member
CREATE INDEX IF NOT EXISTS idx_member_group ON disease_code_group_member(group_id);
CREATE INDEX IF NOT EXISTS idx_member_code ON disease_code_group_member(code_id);

-- coverage_disease_scope
CREATE INDEX IF NOT EXISTS idx_scope_coverage ON coverage_disease_scope(coverage_code);
CREATE INDEX IF NOT EXISTS idx_scope_insurer ON coverage_disease_scope(insurer);

-- ========================================
-- Triggers (updated_at)
-- ========================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_insurer_updated_at ON insurer;
CREATE TRIGGER update_insurer_updated_at BEFORE UPDATE ON insurer
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_product_updated_at ON product;
CREATE TRIGGER update_product_updated_at BEFORE UPDATE ON product
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_coverage_standard_updated_at ON coverage_standard;
CREATE TRIGGER update_coverage_standard_updated_at BEFORE UPDATE ON coverage_standard
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_document_updated_at ON document;
CREATE TRIGGER update_document_updated_at BEFORE UPDATE ON document
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- END OF SCHEMA
-- ========================================
