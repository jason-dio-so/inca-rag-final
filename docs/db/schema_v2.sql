-- ========================================
-- Schema v2: SSOT-based Proposal-first Architecture
-- Constitution: CLAUDE.md § Insurer/Product/Template SSOT
-- Target: PostgreSQL 17+ (same DB, separate schema)
-- ========================================
-- Purpose: "새 술은 새 포대" 원칙에 따라 SSOT 기반 신규 스키마 구축
-- Legacy: public schema는 audit-only로 동결
-- ========================================

CREATE SCHEMA IF NOT EXISTS v2;
SET search_path TO v2;

-- ========================================
-- Tier 1: SSOT Master Tables
-- ========================================

-- Insurer SSOT (8개 고정 enum)
CREATE TYPE v2.insurer_code_enum AS ENUM (
    'SAMSUNG',
    'MERITZ',
    'KB',
    'HANA',
    'DB',
    'HANWHA',
    'LOTTE',
    'HYUNDAI'
);

CREATE TABLE v2.insurer (
    insurer_code v2.insurer_code_enum PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    display_name_eng VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT true,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE v2.insurer IS
'보험사 SSOT - insurer_code (8개 enum) + display_name 분리 원칙';

COMMENT ON COLUMN v2.insurer.insurer_code IS
'유일키 - 8개 고정 enum (SAMSUNG, MERITZ, KB, HANA, DB, HANWHA, LOTTE, HYUNDAI)';

COMMENT ON COLUMN v2.insurer.display_name IS
'UI 노출 이름 (예: "삼성화재", "메리츠화재")';

-- Product SSOT (insurer_code + internal_product_code = PK)
CREATE TABLE v2.product (
    product_id VARCHAR(200) PRIMARY KEY,
    insurer_code v2.insurer_code_enum NOT NULL REFERENCES v2.insurer(insurer_code) ON DELETE CASCADE,
    internal_product_code VARCHAR(100) NOT NULL,
    display_name VARCHAR(300) NOT NULL,
    product_type VARCHAR(100),
    sale_start_date DATE,
    sale_end_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_product_code UNIQUE (insurer_code, internal_product_code),
    CONSTRAINT chk_product_id_format CHECK (product_id = insurer_code::TEXT || '_' || internal_product_code)
);

COMMENT ON TABLE v2.product IS
'상품 SSOT - product_id = insurer_code + internal_product_code 규칙 강제';

COMMENT ON COLUMN v2.product.product_id IS
'유일키 = {insurer_code}_{internal_product_code} (예: SAMSUNG_CANCER_2024)';

COMMENT ON COLUMN v2.product.display_name IS
'UI 노출 상품명 (예: "무배당 내맘편한 암보험")';

-- Template SSOT (insurer_code + product_id + version + fingerprint)
CREATE TABLE v2.template (
    template_id VARCHAR(300) PRIMARY KEY,
    product_id VARCHAR(200) NOT NULL REFERENCES v2.product(product_id) ON DELETE CASCADE,
    template_type VARCHAR(50) NOT NULL, -- proposal/policy/summary/business_method
    version VARCHAR(50) NOT NULL, -- YYYYMM or 보험사 공식 버전
    fingerprint VARCHAR(64) NOT NULL, -- SHA256(structure + key fields)
    effective_date DATE,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_template_version UNIQUE (product_id, template_type, version, fingerprint),
    CONSTRAINT chk_template_id_format CHECK (
        template_id = product_id || '_' || template_type || '_' || version || '_' || LEFT(fingerprint, 8)
    ),
    CONSTRAINT chk_template_type CHECK (template_type IN ('proposal', 'policy', 'summary', 'business_method'))
);

COMMENT ON TABLE v2.template IS
'템플릿 SSOT - template_id = product_id + type + version + fingerprint(short) 규칙 강제';

COMMENT ON COLUMN v2.template.fingerprint IS
'문서 구조/양식 변경 감지 해시 (SHA256, full 64-char stored)';

COMMENT ON COLUMN v2.template.template_id IS
'유일키 = {product_id}_{template_type}_{version}_{fingerprint[0:8]}';

-- Document (template_id FK 필수)
CREATE TABLE v2.document (
    document_id VARCHAR(300) PRIMARY KEY,
    template_id VARCHAR(300) NOT NULL REFERENCES v2.template(template_id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64) NOT NULL, -- SHA256(full file content)
    page_count INT,
    doc_type_priority INT NOT NULL, -- 1=policy, 2=business_method, 3=summary, 4=proposal
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_document_file UNIQUE (template_id, file_hash),
    CONSTRAINT chk_document_id_format CHECK (
        document_id = template_id || '_' || LEFT(file_hash, 8)
    ),
    CONSTRAINT chk_doc_type_priority CHECK (doc_type_priority BETWEEN 1 AND 4)
);

COMMENT ON TABLE v2.document IS
'문서 메타데이터 - template_id FK 필수, file_hash로 중복 방지';

COMMENT ON COLUMN v2.document.doc_type_priority IS
'문서 우선순위 (Constitution 문서 우선순위 원칙): 1=약관, 2=사업방법서, 3=상품요약서, 4=가입설계서';

-- ========================================
-- Tier 2: Coverage Standard (신정원 통일 담보 코드)
-- ========================================

CREATE TABLE v2.coverage_standard (
    coverage_code VARCHAR(100) PRIMARY KEY,
    display_name VARCHAR(300) NOT NULL,
    domain VARCHAR(100),
    coverage_type VARCHAR(100),
    priority INT NOT NULL DEFAULT 999,
    is_main BOOLEAN NOT NULL DEFAULT false,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE v2.coverage_standard IS
'신정원 통일 담보 코드 (CANONICAL) - READ-ONLY, 자동 INSERT 절대 금지';

COMMENT ON COLUMN v2.coverage_standard.coverage_code IS
'유일한 비교 기준 코드 (예: CA_DIAG_GENERAL)';

COMMENT ON COLUMN v2.coverage_standard.domain IS
'도메인 (암/뇌/심혈관/상해 등) - 외부화 규칙 필요';

COMMENT ON COLUMN v2.coverage_standard.priority IS
'도메인 내 우선순위 (메인담보=1, 숫자 작을수록 우선) - 외부화 규칙 필요';

COMMENT ON COLUMN v2.coverage_standard.is_main IS
'메인 담보 여부 (파생 담보와 구분) - 외부화 규칙 필요';

-- Coverage Name Mapping (Excel 기반)
CREATE TABLE v2.coverage_name_map (
    map_id SERIAL PRIMARY KEY,
    insurer_code v2.insurer_code_enum NOT NULL REFERENCES v2.insurer(insurer_code) ON DELETE CASCADE,
    coverage_alias TEXT NOT NULL, -- 가입설계서 담보명 (정규화 전)
    normalized_alias TEXT NOT NULL, -- 정규화 담보명 (매칭용)
    canonical_coverage_code VARCHAR(100) REFERENCES v2.coverage_standard(coverage_code) ON DELETE SET NULL,
    mapping_status VARCHAR(20) NOT NULL, -- MAPPED / UNMAPPED / AMBIGUOUS
    mapping_source VARCHAR(100) NOT NULL DEFAULT 'data/담보명mapping자료.xlsx',
    mapping_evidence JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_insurer_alias UNIQUE (insurer_code, normalized_alias),
    CONSTRAINT chk_mapping_status CHECK (mapping_status IN ('MAPPED', 'UNMAPPED', 'AMBIGUOUS')),
    CONSTRAINT chk_mapped_requires_code CHECK (
        (mapping_status = 'MAPPED' AND canonical_coverage_code IS NOT NULL)
        OR
        (mapping_status IN ('UNMAPPED', 'AMBIGUOUS') AND canonical_coverage_code IS NULL)
    )
);

COMMENT ON TABLE v2.coverage_name_map IS
'담보명 매핑 - Excel 단일 출처 원칙, LLM/유사도 추론 절대 금지';

COMMENT ON COLUMN v2.coverage_name_map.mapping_source IS
'매핑 출처 - data/담보명mapping자료.xlsx 고정';

-- ========================================
-- Tier 3: Proposal-first Coverage Pipeline
-- ========================================

-- Proposal Coverage (가입설계서 앞 2장 테이블 추출 결과)
CREATE TABLE v2.proposal_coverage (
    coverage_id SERIAL PRIMARY KEY,
    template_id VARCHAR(300) NOT NULL REFERENCES v2.template(template_id) ON DELETE CASCADE,
    insurer_coverage_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,

    -- Amount info (Slot Schema v1.1.1)
    currency VARCHAR(10) DEFAULT 'KRW',
    amount_value BIGINT,
    payout_amount_unit VARCHAR(50) DEFAULT 'unknown',

    -- Evidence (required)
    source_page INT NOT NULL,
    span_text TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_coverage_hash UNIQUE (template_id, content_hash),
    CONSTRAINT chk_template_type_proposal CHECK (
        (SELECT template_type FROM v2.template WHERE template_id = v2.proposal_coverage.template_id) = 'proposal'
    )
);

COMMENT ON TABLE v2.proposal_coverage IS
'가입설계서 담보 Universe - 비교 대상의 절대 기준 (Coverage Universe Lock)';

COMMENT ON COLUMN v2.proposal_coverage.normalized_name IS
'정규화 담보명 (공백/괄호/특수문자 통일) - coverage_name_map 매칭용';

COMMENT ON COLUMN v2.proposal_coverage.content_hash IS
'SHA256(template_id||page||span_text) - 중복 삽입 방지';

-- Proposal Coverage Mapped (Universe → Canonical Code Mapping)
CREATE TYPE v2.mapping_status_enum AS ENUM ('MAPPED', 'UNMAPPED', 'AMBIGUOUS');

CREATE TABLE v2.proposal_coverage_mapped (
    mapped_id SERIAL PRIMARY KEY,
    coverage_id INT NOT NULL REFERENCES v2.proposal_coverage(coverage_id) ON DELETE CASCADE,

    -- Mapping result (Slot Schema v1.1.1)
    canonical_coverage_code VARCHAR(100) REFERENCES v2.coverage_standard(coverage_code) ON DELETE SET NULL,
    mapping_status v2.mapping_status_enum NOT NULL,

    -- Evidence
    mapping_evidence JSONB, -- {lookup_key, matched_alias, source}

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_mapped_coverage UNIQUE (coverage_id),
    CONSTRAINT chk_mapped_requires_code CHECK (
        (mapping_status = 'MAPPED' AND canonical_coverage_code IS NOT NULL)
        OR
        (mapping_status IN ('UNMAPPED', 'AMBIGUOUS') AND canonical_coverage_code IS NULL)
    )
);

COMMENT ON TABLE v2.proposal_coverage_mapped IS
'Universe 담보의 신정원 코드 매핑 결과 - Excel 기반만 허용';

-- Proposal Coverage Detail (상세 페이지 근거/조건/정의 추출 결과)
CREATE TYPE v2.event_type_enum AS ENUM ('diagnosis', 'surgery', 'hospitalization', 'treatment', 'death', 'unknown');
CREATE TYPE v2.source_confidence_enum AS ENUM ('proposal_confirmed', 'policy_required', 'unknown');

CREATE TABLE v2.proposal_coverage_detail (
    detail_id SERIAL PRIMARY KEY,
    mapped_id INT NOT NULL REFERENCES v2.proposal_coverage_mapped(mapped_id) ON DELETE CASCADE,

    -- Core slots
    event_type v2.event_type_enum DEFAULT 'unknown',

    -- Disease scope
    disease_scope_raw TEXT, -- 설계서 원문 (예: "유사암 제외")
    disease_scope_norm JSONB, -- {include_group_id, exclude_group_id} or NULL

    -- Temporal conditions
    waiting_period_days INT, -- NULL = unknown, 0 = none, >0 = days
    coverage_start_rule TEXT,
    reduction_periods JSONB, -- NULL = unknown, [] = explicit none

    -- Payout limit (consolidated v1.1.1)
    payout_limit JSONB, -- {type, count, period} or NULL

    -- Special conditions
    treatment_method TEXT[],
    hospitalization_exclusions JSONB,

    -- Renewal
    renewal_flag BOOLEAN DEFAULT false,
    renewal_period_years INT,
    renewal_max_age INT,

    -- Meta
    source_confidence v2.source_confidence_enum NOT NULL,
    qualification_suffix TEXT,

    -- Evidence (required)
    evidence JSONB NOT NULL, -- {document_id, page, span_text, rule_id}

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_detail_mapped UNIQUE (mapped_id)
);

COMMENT ON TABLE v2.proposal_coverage_detail IS
'가입설계서 기반 Slot 추출 결과 - Slot Schema v1.1.1 준수';

COMMENT ON COLUMN v2.proposal_coverage_detail.disease_scope_norm IS
'그룹 참조 기반: {include_group_id, exclude_group_id} or NULL (약관 미처리 시)';

COMMENT ON COLUMN v2.proposal_coverage_detail.payout_limit IS
'v1.1.1 통합 포맷: {type: once|multiple|unlimited, count: int, period: lifetime|per_year|...}';

-- ========================================
-- Tier 4: KCD-7 Disease Code (3-tier model)
-- ========================================

CREATE TABLE v2.disease_code_master (
    code VARCHAR(10) PRIMARY KEY,
    version VARCHAR(20) NOT NULL DEFAULT 'KCD-7',
    name_ko TEXT,
    source VARCHAR(100) NOT NULL DEFAULT 'KCD-7 Official Distribution',
    active_flag BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_version CHECK (version = 'KCD-7')
);

COMMENT ON TABLE v2.disease_code_master IS
'KCD-7 질병코드 사전 - 공식 배포본만 허용 (보험 의미 금지)';

CREATE TYPE v2.member_type_enum AS ENUM ('CODE', 'RANGE');

CREATE TABLE v2.disease_code_group (
    group_id VARCHAR(100) PRIMARY KEY,
    group_label VARCHAR(200) NOT NULL,
    insurer_code v2.insurer_code_enum REFERENCES v2.insurer(insurer_code) ON DELETE CASCADE,
    version_tag VARCHAR(20) NOT NULL,
    basis_doc_id VARCHAR(300) NOT NULL,
    basis_page INT,
    basis_span TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_group_id_format CHECK (group_id ~ '^[A-Z_0-9]+$')
);

COMMENT ON TABLE v2.disease_code_group IS
'보험 질병 개념 그룹 - insurer별 그룹 원칙 (insurer=NULL은 의학적 범위만)';

COMMENT ON COLUMN v2.disease_code_group.insurer_code IS
'보험사별 그룹. NULL은 KCD 분류 자체(C00-C97 등) 의학적 범위에만 허용';

CREATE TABLE v2.disease_code_group_member (
    member_id SERIAL PRIMARY KEY,
    group_id VARCHAR(100) NOT NULL REFERENCES v2.disease_code_group(group_id) ON DELETE CASCADE,
    member_type v2.member_type_enum NOT NULL,

    -- For member_type = CODE
    code VARCHAR(10) REFERENCES v2.disease_code_master(code),

    -- For member_type = RANGE
    code_from VARCHAR(10) REFERENCES v2.disease_code_master(code),
    code_to VARCHAR(10) REFERENCES v2.disease_code_master(code),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_code_xor_range CHECK (
        (member_type = 'CODE' AND code IS NOT NULL AND code_from IS NULL AND code_to IS NULL)
        OR
        (member_type = 'RANGE' AND code IS NULL AND code_from IS NOT NULL AND code_to IS NOT NULL)
    )
);

COMMENT ON TABLE v2.disease_code_group_member IS
'그룹에 속한 KCD-7 코드들 (단일 코드 또는 범위)';

-- ========================================
-- Tier 5: Evidence Chunk (향후 RAG 대비)
-- ========================================

CREATE TABLE v2.evidence_chunk (
    chunk_id SERIAL PRIMARY KEY,
    document_id VARCHAR(300) NOT NULL REFERENCES v2.document(document_id) ON DELETE CASCADE,
    page_number INT,
    chunk_index INT NOT NULL, -- 페이지 내 순서
    content TEXT NOT NULL,
    embedding vector(1536), -- pgvector extension 필요
    is_synthetic BOOLEAN NOT NULL DEFAULT false,
    synthetic_source_chunk_id INT REFERENCES v2.evidence_chunk(chunk_id) ON DELETE SET NULL,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_chunk_index UNIQUE (document_id, page_number, chunk_index),
    CONSTRAINT chk_synthetic_source CHECK (
        (is_synthetic = false AND synthetic_source_chunk_id IS NULL)
        OR
        (is_synthetic = true AND synthetic_source_chunk_id IS NOT NULL)
    )
);

COMMENT ON TABLE v2.evidence_chunk IS
'문서 chunk 저장 (향후 Vector RAG 대비) - is_synthetic 필터 기준';

COMMENT ON COLUMN v2.evidence_chunk.is_synthetic IS
'합성 chunk 여부 - Amount Bridge 전용, 비교/검색 시 필터링 필수';

-- ========================================
-- Indexes
-- ========================================

-- insurer
CREATE INDEX idx_v2_insurer_active ON v2.insurer(is_active) WHERE is_active = true;

-- product
CREATE INDEX idx_v2_product_insurer ON v2.product(insurer_code);
CREATE INDEX idx_v2_product_type ON v2.product(product_type);
CREATE INDEX idx_v2_product_active ON v2.product(is_active) WHERE is_active = true;

-- template
CREATE INDEX idx_v2_template_product ON v2.template(product_id);
CREATE INDEX idx_v2_template_type ON v2.template(template_type);

-- document
CREATE INDEX idx_v2_document_template ON v2.document(template_id);
CREATE INDEX idx_v2_document_priority ON v2.document(doc_type_priority);

-- coverage_standard
CREATE INDEX idx_v2_coverage_domain ON v2.coverage_standard(domain);
CREATE INDEX idx_v2_coverage_priority ON v2.coverage_standard(domain, priority);
CREATE INDEX idx_v2_coverage_main ON v2.coverage_standard(is_main) WHERE is_main = true;

-- coverage_name_map
CREATE INDEX idx_v2_map_insurer ON v2.coverage_name_map(insurer_code);
CREATE INDEX idx_v2_map_canonical ON v2.coverage_name_map(canonical_coverage_code);
CREATE INDEX idx_v2_map_status ON v2.coverage_name_map(mapping_status);

-- proposal_coverage
CREATE INDEX idx_v2_coverage_template ON v2.proposal_coverage(template_id);
CREATE INDEX idx_v2_coverage_normalized ON v2.proposal_coverage(normalized_name);

-- proposal_coverage_mapped
CREATE INDEX idx_v2_mapped_canonical ON v2.proposal_coverage_mapped(canonical_coverage_code);
CREATE INDEX idx_v2_mapped_status ON v2.proposal_coverage_mapped(mapping_status);

-- proposal_coverage_detail
CREATE INDEX idx_v2_detail_event ON v2.proposal_coverage_detail(event_type);
CREATE INDEX idx_v2_detail_confidence ON v2.proposal_coverage_detail(source_confidence);

-- disease_code_group
CREATE INDEX idx_v2_group_insurer ON v2.disease_code_group(insurer_code);

-- disease_code_group_member
CREATE INDEX idx_v2_member_group ON v2.disease_code_group_member(group_id);
CREATE INDEX idx_v2_member_code ON v2.disease_code_group_member(code);

-- evidence_chunk
CREATE INDEX idx_v2_chunk_document ON v2.evidence_chunk(document_id);
CREATE INDEX idx_v2_chunk_synthetic ON v2.evidence_chunk(is_synthetic);
CREATE INDEX idx_v2_chunk_page ON v2.evidence_chunk(document_id, page_number);

-- ========================================
-- Triggers (updated_at auto-update)
-- ========================================

CREATE OR REPLACE FUNCTION v2.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_insurer_updated_at BEFORE UPDATE ON v2.insurer
    FOR EACH ROW EXECUTE FUNCTION v2.update_updated_at_column();

CREATE TRIGGER update_product_updated_at BEFORE UPDATE ON v2.product
    FOR EACH ROW EXECUTE FUNCTION v2.update_updated_at_column();

CREATE TRIGGER update_template_updated_at BEFORE UPDATE ON v2.template
    FOR EACH ROW EXECUTE FUNCTION v2.update_updated_at_column();

CREATE TRIGGER update_document_updated_at BEFORE UPDATE ON v2.document
    FOR EACH ROW EXECUTE FUNCTION v2.update_updated_at_column();

CREATE TRIGGER update_coverage_standard_updated_at BEFORE UPDATE ON v2.coverage_standard
    FOR EACH ROW EXECUTE FUNCTION v2.update_updated_at_column();

CREATE TRIGGER update_coverage_name_map_updated_at BEFORE UPDATE ON v2.coverage_name_map
    FOR EACH ROW EXECUTE FUNCTION v2.update_updated_at_column();

-- ========================================
-- Views
-- ========================================

-- Full Pipeline View (Universe → Mapping → Detail)
CREATE OR REPLACE VIEW v2.v_proposal_coverage_full AS
SELECT
    c.coverage_id,
    t.product_id,
    p.insurer_code,
    p.display_name AS product_display_name,
    c.insurer_coverage_name,
    c.normalized_name,
    c.currency,
    c.amount_value,
    c.payout_amount_unit,
    c.source_page,
    c.span_text AS coverage_span,

    m.canonical_coverage_code,
    m.mapping_status,
    m.mapping_evidence,

    d.event_type,
    d.disease_scope_raw,
    d.disease_scope_norm,
    d.waiting_period_days,
    d.reduction_periods,
    d.payout_limit,
    d.treatment_method,
    d.renewal_flag,
    d.renewal_period_years,
    d.source_confidence,
    d.qualification_suffix,
    d.evidence AS detail_evidence
FROM v2.proposal_coverage c
JOIN v2.template t ON c.template_id = t.template_id
JOIN v2.product p ON t.product_id = p.product_id
LEFT JOIN v2.proposal_coverage_mapped m ON c.coverage_id = m.coverage_id
LEFT JOIN v2.proposal_coverage_detail d ON m.mapped_id = d.mapped_id;

COMMENT ON VIEW v2.v_proposal_coverage_full IS
'전체 파이프라인 조회: Proposal Coverage → Mapping → Detail (SSOT 기반)';

-- Active Products
CREATE OR REPLACE VIEW v2.v_active_products AS
SELECT
    i.insurer_code,
    i.display_name AS insurer_name,
    p.product_id,
    p.display_name AS product_name,
    p.product_type,
    p.sale_start_date,
    p.sale_end_date
FROM v2.product p
JOIN v2.insurer i ON p.insurer_code = i.insurer_code
WHERE p.is_active = true AND i.is_active = true;

-- Coverage Mapping Summary
CREATE OR REPLACE VIEW v2.v_coverage_mapping_summary AS
SELECT
    m.insurer_code,
    i.display_name AS insurer_name,
    m.canonical_coverage_code,
    cs.display_name AS coverage_name,
    COUNT(DISTINCT m.coverage_alias) AS alias_count,
    m.mapping_status
FROM v2.coverage_name_map m
JOIN v2.insurer i ON m.insurer_code = i.insurer_code
LEFT JOIN v2.coverage_standard cs ON m.canonical_coverage_code = cs.coverage_code
GROUP BY m.insurer_code, i.display_name, m.canonical_coverage_code, cs.display_name, m.mapping_status;

-- Original Chunks Only (비교/검색용)
CREATE OR REPLACE VIEW v2.v_original_chunks AS
SELECT
    c.chunk_id,
    c.document_id,
    c.page_number,
    c.chunk_index,
    c.content,
    c.embedding,
    c.meta,
    d.template_id,
    t.product_id,
    p.insurer_code
FROM v2.evidence_chunk c
JOIN v2.document d ON c.document_id = d.document_id
JOIN v2.template t ON d.template_id = t.template_id
JOIN v2.product p ON t.product_id = p.product_id
WHERE c.is_synthetic = false;

-- ========================================
-- Utility Functions
-- ========================================

-- Resolve product_id from insurer_code + internal_product_code
CREATE OR REPLACE FUNCTION v2.resolve_product_id(
    p_insurer_code TEXT,
    p_internal_product_code TEXT
)
RETURNS VARCHAR(200) AS $$
BEGIN
    RETURN p_insurer_code || '_' || p_internal_product_code;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Resolve template_id from product_id + type + version + fingerprint
CREATE OR REPLACE FUNCTION v2.resolve_template_id(
    p_product_id TEXT,
    p_template_type TEXT,
    p_version TEXT,
    p_fingerprint TEXT
)
RETURNS VARCHAR(300) AS $$
BEGIN
    RETURN p_product_id || '_' || p_template_type || '_' || p_version || '_' || LEFT(p_fingerprint, 8);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Get coverage domain
CREATE OR REPLACE FUNCTION v2.get_coverage_domain(p_coverage_code VARCHAR)
RETURNS VARCHAR AS $$
    SELECT domain FROM v2.coverage_standard WHERE coverage_code = p_coverage_code;
$$ LANGUAGE SQL STABLE;

-- ========================================
-- Security / Access Control (운영 환경 권장)
-- ========================================

-- coverage_standard는 READ-ONLY (app role은 SELECT만)
-- 예시:
-- CREATE ROLE app_ingestion_v2;
-- GRANT USAGE ON SCHEMA v2 TO app_ingestion_v2;
-- GRANT SELECT ON v2.coverage_standard TO app_ingestion_v2;
-- GRANT ALL ON v2.coverage_name_map TO app_ingestion_v2;
-- GRANT ALL ON v2.proposal_coverage, v2.proposal_coverage_mapped, v2.proposal_coverage_detail TO app_ingestion_v2;
-- REVOKE INSERT, UPDATE, DELETE ON v2.coverage_standard FROM app_ingestion_v2;

-- ========================================
-- Migration Notes
-- ========================================
-- 1. Legacy public schema는 audit-only로 동결 (DROP 금지)
-- 2. v2 schema는 신규 ingestion부터 사용
-- 3. 기존 데이터 이관은 LEGACY_FREEZE_PLAN.md 참조
-- 4. insurer 8개 enum은 수동 INSERT 필요 (seed script)
-- 5. coverage_standard는 기존 Excel 기반으로 초기 seed

RESET search_path;
