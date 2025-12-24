-- ========================================
-- Migration: Step 6-C - Proposal Universe Lock
-- Purpose: Implement "가입설계서 담보만 비교" system
-- Constitution: v1.0 + Amendment v1.0.1 (Article VIII)
-- Slot Schema: v1.1.1
-- ========================================

-- ========================================
-- Tier 1: KCD-7 Code Master (from Article VIII)
-- ========================================
CREATE TABLE IF NOT EXISTS disease_code_master (
    code VARCHAR(10) PRIMARY KEY,
    version VARCHAR(20) NOT NULL DEFAULT 'KCD-7',
    name_ko TEXT,
    source VARCHAR(100) NOT NULL DEFAULT 'KCD-7 Official Distribution',
    active_flag BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_version CHECK (version = 'KCD-7')
);

CREATE INDEX IF NOT EXISTS idx_disease_code_active
ON disease_code_master(active_flag) WHERE active_flag = true;

COMMENT ON TABLE disease_code_master IS
'KCD-7 질병코드 사전 - 공식 배포본만 허용 (보험 의미 금지)';

COMMENT ON COLUMN disease_code_master.source IS
'KCD-7 official distribution dataset (정부/공식기관 배포본)';

-- ========================================
-- Tier 2: Disease Code Group (Insurance Concepts)
-- ========================================
CREATE TYPE member_type_enum AS ENUM ('CODE', 'RANGE');

CREATE TABLE IF NOT EXISTS disease_code_group (
    group_id VARCHAR(100) PRIMARY KEY,
    group_label VARCHAR(200) NOT NULL,
    insurer VARCHAR(50),  -- NULL only for medical/KCD classification groups
    version_tag VARCHAR(20) NOT NULL,
    basis_doc_id VARCHAR(200) NOT NULL,
    basis_page INT,
    basis_span TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_group_id_format CHECK (group_id ~ '^[A-Z_0-9]+$')
);

CREATE INDEX IF NOT EXISTS idx_group_insurer ON disease_code_group(insurer);
CREATE INDEX IF NOT EXISTS idx_group_label ON disease_code_group(group_label);

COMMENT ON TABLE disease_code_group IS
'보험 질병 개념 그룹 - 보험 실무 개념은 insurer별 그룹 원칙';

COMMENT ON COLUMN disease_code_group.insurer IS
'보험사별 그룹. NULL은 KCD 분류 자체(C00-C97 등) 의학적 범위에만 허용';

-- ========================================
-- Tier 2: Group Member (Group → Code Mapping)
-- ========================================
CREATE TABLE IF NOT EXISTS disease_code_group_member (
    id SERIAL PRIMARY KEY,
    group_id VARCHAR(100) NOT NULL REFERENCES disease_code_group(group_id) ON DELETE CASCADE,
    member_type member_type_enum NOT NULL,

    -- For member_type = CODE
    code VARCHAR(10) REFERENCES disease_code_master(code),

    -- For member_type = RANGE
    code_from VARCHAR(10) REFERENCES disease_code_master(code),
    code_to VARCHAR(10) REFERENCES disease_code_master(code),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_code_xor_range CHECK (
        (member_type = 'CODE' AND code IS NOT NULL AND code_from IS NULL AND code_to IS NULL)
        OR
        (member_type = 'RANGE' AND code IS NULL AND code_from IS NOT NULL AND code_to IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_member_group ON disease_code_group_member(group_id);
CREATE INDEX IF NOT EXISTS idx_member_code ON disease_code_group_member(code);

COMMENT ON TABLE disease_code_group_member IS
'그룹에 속한 KCD-7 코드들 (단일 코드 또는 범위)';

-- ========================================
-- Tier 3: Coverage Disease Scope
-- ========================================
CREATE TABLE IF NOT EXISTS coverage_disease_scope (
    id SERIAL PRIMARY KEY,
    canonical_coverage_code VARCHAR(50) NOT NULL,
    insurer VARCHAR(50) NOT NULL,
    proposal_id VARCHAR(200) NOT NULL,

    include_group_id VARCHAR(100) REFERENCES disease_code_group(group_id),
    exclude_group_id VARCHAR(100) REFERENCES disease_code_group(group_id),

    source_doc_id VARCHAR(200) NOT NULL,
    source_page INT,
    span_text TEXT,
    extraction_rule_id VARCHAR(100),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_include_required CHECK (include_group_id IS NOT NULL),
    CONSTRAINT uq_coverage_insurer_proposal UNIQUE (canonical_coverage_code, insurer, proposal_id)
);

CREATE INDEX IF NOT EXISTS idx_scope_coverage ON coverage_disease_scope(canonical_coverage_code);
CREATE INDEX IF NOT EXISTS idx_scope_insurer ON coverage_disease_scope(insurer);
CREATE INDEX IF NOT EXISTS idx_scope_include ON coverage_disease_scope(include_group_id);
CREATE INDEX IF NOT EXISTS idx_scope_exclude ON coverage_disease_scope(exclude_group_id);

COMMENT ON TABLE coverage_disease_scope IS
'담보별 질병 범위 (include/exclude 그룹 참조) - 약관 기반 확정값';

-- ========================================
-- Proposal Coverage Universe (신규)
-- Purpose: "가입설계서에 있는 담보만" Universe Lock
-- ========================================
CREATE TABLE proposal_coverage_universe (
    id SERIAL PRIMARY KEY,
    insurer VARCHAR(50) NOT NULL,
    proposal_id VARCHAR(200) NOT NULL,
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

    CONSTRAINT uq_universe_coverage UNIQUE (insurer, proposal_id, normalized_name),
    CONSTRAINT uq_content_hash UNIQUE (content_hash)
);

CREATE INDEX idx_universe_insurer ON proposal_coverage_universe(insurer);
CREATE INDEX idx_universe_proposal ON proposal_coverage_universe(proposal_id);
CREATE INDEX idx_universe_normalized ON proposal_coverage_universe(normalized_name);

COMMENT ON TABLE proposal_coverage_universe IS
'가입설계서 담보 Universe - 비교 대상의 절대 기준 (Coverage Universe Lock)';

COMMENT ON COLUMN proposal_coverage_universe.normalized_name IS
'전처리된 담보명 (공백/특수문자/괄호 통일) - 매칭용';

COMMENT ON COLUMN proposal_coverage_universe.content_hash IS
'SHA256(insurer||proposal_id||page||span_text) - 중복 삽입 방지';

-- ========================================
-- Proposal Coverage Mapped (신규)
-- Purpose: Universe → Canonical Code Mapping
-- ========================================
CREATE TYPE mapping_status_enum AS ENUM ('MAPPED', 'UNMAPPED', 'AMBIGUOUS');

CREATE TABLE proposal_coverage_mapped (
    id SERIAL PRIMARY KEY,
    universe_id INT NOT NULL REFERENCES proposal_coverage_universe(id) ON DELETE CASCADE,

    -- Mapping result (Slot Schema v1.1.1)
    canonical_coverage_code VARCHAR(50),  -- nullable
    mapping_status mapping_status_enum NOT NULL,

    -- Evidence
    mapping_evidence JSONB,  -- {lookup_key, matched_alias, source}

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_mapped_universe UNIQUE (universe_id),
    CONSTRAINT chk_mapped_requires_code CHECK (
        (mapping_status = 'MAPPED' AND canonical_coverage_code IS NOT NULL)
        OR
        (mapping_status IN ('UNMAPPED', 'AMBIGUOUS') AND canonical_coverage_code IS NULL)
    )
);

CREATE INDEX idx_mapped_canonical ON proposal_coverage_mapped(canonical_coverage_code);
CREATE INDEX idx_mapped_status ON proposal_coverage_mapped(mapping_status);

COMMENT ON TABLE proposal_coverage_mapped IS
'Universe 담보의 신정원 코드 매핑 결과 - Excel 기반만 허용';

COMMENT ON CONSTRAINT chk_mapped_requires_code ON proposal_coverage_mapped IS
'Slot Schema v1.1.1: MAPPED일 때만 canonical_coverage_code 필수';

-- ========================================
-- Proposal Coverage Slots (신규)
-- Purpose: Slot Schema v1.1.1 저장소
-- ========================================
CREATE TYPE event_type_enum AS ENUM ('diagnosis', 'surgery', 'hospitalization', 'treatment', 'death', 'unknown');
CREATE TYPE source_confidence_enum AS ENUM ('proposal_confirmed', 'policy_required', 'unknown');

CREATE TABLE proposal_coverage_slots (
    id SERIAL PRIMARY KEY,
    mapped_id INT NOT NULL REFERENCES proposal_coverage_mapped(id) ON DELETE CASCADE,

    -- Core slots
    event_type event_type_enum DEFAULT 'unknown',

    -- Disease scope
    disease_scope_raw TEXT,  -- 설계서 원문 (예: "유사암 제외")
    disease_scope_norm JSONB,  -- {include_group_id, exclude_group_id} or NULL

    -- Temporal conditions
    waiting_period_days INT,  -- NULL = unknown, 0 = none, >0 = days
    coverage_start_rule TEXT,
    reduction_periods JSONB,  -- NULL = unknown, [] = explicit none, [{...}] = periods

    -- Payout limit (consolidated v1.1.1)
    payout_limit JSONB,  -- {type, count, period} or NULL

    -- Special conditions
    treatment_method TEXT[],  -- ['robotic_surgery', 'chemotherapy', ...]
    hospitalization_exclusions JSONB,  -- NULL = unknown, [] = explicit none

    -- Renewal
    renewal_flag BOOLEAN DEFAULT false,
    renewal_period_years INT,
    renewal_max_age INT,

    -- Meta
    source_confidence source_confidence_enum NOT NULL,
    qualification_suffix TEXT,

    -- Evidence
    evidence JSONB NOT NULL,  -- {document_id, page, span, rule_id}

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_slots_mapped UNIQUE (mapped_id)
);

CREATE INDEX idx_slots_event_type ON proposal_coverage_slots(event_type);
CREATE INDEX idx_slots_confidence ON proposal_coverage_slots(source_confidence);

COMMENT ON TABLE proposal_coverage_slots IS
'가입설계서 기반 Slot 추출 결과 - Slot Schema v1.1.1 준수';

COMMENT ON COLUMN proposal_coverage_slots.disease_scope_norm IS
'그룹 참조 기반: {include_group_id, exclude_group_id} or NULL (약관 미처리 시)';

COMMENT ON COLUMN proposal_coverage_slots.payout_limit IS
'v1.1.1 통합 포맷: {type: once|multiple|unlimited, count: int, period: lifetime|per_year|...}';

-- ========================================
-- View: Full Coverage Pipeline
-- ========================================
CREATE OR REPLACE VIEW v_proposal_coverage_full AS
SELECT
    u.id AS universe_id,
    u.insurer,
    u.proposal_id,
    u.insurer_coverage_name,
    u.normalized_name,
    u.currency,
    u.amount_value,
    u.payout_amount_unit,

    m.canonical_coverage_code,
    m.mapping_status,
    m.mapping_evidence,

    s.event_type,
    s.disease_scope_raw,
    s.disease_scope_norm,
    s.waiting_period_days,
    s.reduction_periods,
    s.payout_limit,
    s.treatment_method,
    s.renewal_flag,
    s.renewal_period_years,
    s.source_confidence,
    s.qualification_suffix,

    u.source_page,
    u.span_text AS universe_span,
    s.evidence AS slot_evidence
FROM proposal_coverage_universe u
LEFT JOIN proposal_coverage_mapped m ON u.id = m.universe_id
LEFT JOIN proposal_coverage_slots s ON m.id = s.mapped_id;

COMMENT ON VIEW v_proposal_coverage_full IS
'전체 파이프라인 조회: Universe → Mapping → Slots';

-- ========================================
-- Indexes for comparison queries
-- ========================================
CREATE INDEX idx_full_insurer_canonical
ON proposal_coverage_mapped(canonical_coverage_code)
WHERE mapping_status = 'MAPPED';

CREATE INDEX idx_universe_insurer_normalized
ON proposal_coverage_universe(insurer, normalized_name);
