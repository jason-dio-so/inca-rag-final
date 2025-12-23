-- ========================================
-- inca-RAG-final DB Schema (PostgreSQL)
-- ========================================
-- 보험 약관 비교 RAG 시스템
-- 신정원 통일 담보 코드 기반 설계
-- ========================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
-- Note: uuid-ossp는 현재 스키마에서 사용하지 않음 (향후 필요 시 활성화)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- 기준/마스터 계층 (Canonical Layer)
-- ========================================

-- 보험사 마스터
CREATE TABLE insurer (
    insurer_id SERIAL PRIMARY KEY,
    insurer_code VARCHAR(50) UNIQUE NOT NULL,
    insurer_name VARCHAR(200) NOT NULL,
    insurer_name_eng VARCHAR(200),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE insurer IS '보험사 마스터 데이터';
COMMENT ON COLUMN insurer.insurer_code IS '보험사 고유 코드 (예: SAMSUNG, HYUNDAI)';
COMMENT ON COLUMN insurer.is_active IS '활성 보험사 여부';

-- 보험 상품
CREATE TABLE product (
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
COMMENT ON COLUMN product.product_code IS '상품 코드 (보험사 내 UNIQUE)';
COMMENT ON COLUMN product.product_type IS '상품 유형 (암보험, 건강보험 등)';
COMMENT ON COLUMN product.meta IS '추가 메타 정보 (JSON)';

-- 신정원 통일 담보 코드 (CANONICAL)
CREATE TABLE coverage_standard (
    coverage_id SERIAL PRIMARY KEY,
    coverage_code VARCHAR(100) UNIQUE NOT NULL,
    coverage_name VARCHAR(300) NOT NULL,
    domain VARCHAR(100),
    coverage_type VARCHAR(100),
    priority INTEGER DEFAULT 999,
    is_main BOOLEAN DEFAULT false,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE coverage_standard IS '신정원 통일 담보 코드 (CANONICAL) - 자동 INSERT 금지';
COMMENT ON COLUMN coverage_standard.coverage_code IS '유일한 비교 기준 코드 (예: CA_DIAG_GENERAL)';
COMMENT ON COLUMN coverage_standard.domain IS '도메인 (암/뇌/심혈관/상해 등)';
COMMENT ON COLUMN coverage_standard.coverage_type IS '담보 유형 (진단/수술/입원/통원 등)';
COMMENT ON COLUMN coverage_standard.priority IS '도메인 내 우선순위 (메인담보=1, 숫자 작을수록 우선)';
COMMENT ON COLUMN coverage_standard.is_main IS '메인 담보 여부 (파생 담보와 구분)';

-- 보험 문서
CREATE TABLE document (
    document_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL,
    document_version VARCHAR(50),
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64),
    effective_date DATE,
    doc_type_priority INTEGER NOT NULL,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, document_type, file_hash)
);

COMMENT ON TABLE document IS '보험 문서 메타데이터';
COMMENT ON COLUMN document.document_type IS '문서 유형 (약관/사업방법서/요약서/설계서)';
COMMENT ON COLUMN document.doc_type_priority IS '문서 우선순위: 1=약관, 2=사업방법서, 3=상품요약서, 4=가입설계서';
COMMENT ON COLUMN document.file_hash IS 'SHA-256 파일 해시 (중복 방지)';

-- ========================================
-- 매핑/정규화 계층 (Normalization Layer)
-- ========================================

-- 보험사별 담보명 → 신정원 코드 매핑
CREATE TABLE coverage_alias (
    alias_id SERIAL PRIMARY KEY,
    insurer_id INTEGER NOT NULL REFERENCES insurer(insurer_id) ON DELETE CASCADE,
    coverage_id INTEGER NOT NULL REFERENCES coverage_standard(coverage_id) ON DELETE CASCADE,
    insurer_coverage_name VARCHAR(300) NOT NULL,
    insurer_coverage_code VARCHAR(100),
    confidence VARCHAR(20) DEFAULT 'medium',
    mapping_method VARCHAR(50) DEFAULT 'rule',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(insurer_id, insurer_coverage_name)
);

COMMENT ON TABLE coverage_alias IS '보험사별 담보명 → 신정원 코드 매핑 (자동 INSERT 허용)';
COMMENT ON COLUMN coverage_alias.insurer_coverage_name IS '보험사별 담보명 (예: "삼성화재 암진단금")';
COMMENT ON COLUMN coverage_alias.confidence IS '매핑 신뢰도 (high/medium/low)';
COMMENT ON COLUMN coverage_alias.mapping_method IS '매핑 방법 (manual/rule/llm)';

-- 레거시/변형 코드 매핑
CREATE TABLE coverage_code_alias (
    code_alias_id SERIAL PRIMARY KEY,
    coverage_id INTEGER NOT NULL REFERENCES coverage_standard(coverage_id) ON DELETE CASCADE,
    legacy_code VARCHAR(100) NOT NULL,
    code_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(legacy_code)
);

COMMENT ON TABLE coverage_code_alias IS '레거시/변형 코드 → 신정원 코드 매핑';
COMMENT ON COLUMN coverage_code_alias.legacy_code IS '레거시 또는 변형된 담보 코드';

-- 담보 세부 유형
CREATE TABLE coverage_subtype (
    subtype_id SERIAL PRIMARY KEY,
    coverage_id INTEGER NOT NULL REFERENCES coverage_standard(coverage_id) ON DELETE CASCADE,
    subtype_name VARCHAR(200) NOT NULL,
    subtype_code VARCHAR(100),
    rules JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE coverage_subtype IS '담보 세부 유형 (경계성종양, 제자리암, 유사암 등)';
COMMENT ON COLUMN coverage_subtype.rules IS '세부 유형 적용 규칙 (JSON)';

-- 담보 지급 조건
CREATE TABLE coverage_condition (
    condition_id SERIAL PRIMARY KEY,
    coverage_id INTEGER NOT NULL REFERENCES coverage_standard(coverage_id) ON DELETE CASCADE,
    condition_type VARCHAR(50) NOT NULL,
    condition_text TEXT,
    condition_rules JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE coverage_condition IS '담보 지급 조건, 감액, 면책 조건';
COMMENT ON COLUMN coverage_condition.condition_type IS '조건 유형 (지급/감액/면책)';
COMMENT ON COLUMN coverage_condition.condition_rules IS '조건 규칙 구조화 (JSON)';

-- ========================================
-- 문서/청크 계층 (Document & Chunk Layer)
-- ========================================

-- 청크 (RAG 기본 단위)
CREATE TABLE chunk (
    chunk_id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
    page_number INTEGER,
    content TEXT NOT NULL,
    embedding vector(1536),
    is_synthetic BOOLEAN NOT NULL DEFAULT false,
    synthetic_source_chunk_id INTEGER REFERENCES chunk(chunk_id) ON DELETE SET NULL,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE chunk IS '문서 분할 단위 (원본 + synthetic)';
COMMENT ON COLUMN chunk.content IS '청크 본문 (검색/비교 시 필터링: is_synthetic = false)';
COMMENT ON COLUMN chunk.is_synthetic IS '합성 청크 여부 (Amount Bridge 전용) - 필터 기준은 이 컬럼 사용, meta 아님';
COMMENT ON COLUMN chunk.synthetic_source_chunk_id IS '원본 청크 ID (synthetic인 경우)';
COMMENT ON COLUMN chunk.meta IS '메타 정보: synthetic_type, synthetic_method, entities 등 (참고용, 필터링 금지)';

-- ========================================
-- Extraction/Evidence 계층
-- ========================================

-- 청크 엔티티 (모든 추출 결과)
CREATE TABLE chunk_entity (
    entity_id SERIAL PRIMARY KEY,
    chunk_id INTEGER NOT NULL REFERENCES chunk(chunk_id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    coverage_code VARCHAR(100) REFERENCES coverage_standard(coverage_code) ON DELETE SET NULL,
    entity_value JSONB NOT NULL,
    extraction_method VARCHAR(50),
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE chunk_entity IS '청크에서 추출한 모든 엔티티 (coverage/amount/disease/surgery 등)';
COMMENT ON COLUMN chunk_entity.entity_type IS '엔티티 유형 (coverage/amount/disease/surgery 등)';
COMMENT ON COLUMN chunk_entity.entity_value IS '엔티티 값 (구조화 JSON)';

-- 금액 엔티티 (Amount Bridge 전용)
CREATE TABLE amount_entity (
    amount_id SERIAL PRIMARY KEY,
    chunk_id INTEGER NOT NULL REFERENCES chunk(chunk_id) ON DELETE CASCADE,
    coverage_code VARCHAR(100) NOT NULL REFERENCES coverage_standard(coverage_code) ON DELETE CASCADE,
    context_type VARCHAR(50) NOT NULL,
    amount_value NUMERIC(15, 2),
    amount_text VARCHAR(200),
    amount_unit VARCHAR(20),
    extraction_method VARCHAR(50),
    confidence FLOAT,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE amount_entity IS '금액 전용 구조화 테이블 (Amount Bridge)';
COMMENT ON COLUMN amount_entity.context_type IS '컨텍스트 유형 (payment/count/limit)';
COMMENT ON COLUMN amount_entity.amount_value IS '금액 숫자 (예: 5000000)';
COMMENT ON COLUMN amount_entity.amount_text IS '금액 원문 (예: "500만원")';

-- ========================================
-- 인덱스 (Index Strategy)
-- ========================================

-- insurer
CREATE INDEX idx_insurer_code ON insurer(insurer_code);
CREATE INDEX idx_insurer_active ON insurer(is_active);

-- product
CREATE INDEX idx_product_insurer ON product(insurer_id);
CREATE INDEX idx_product_type ON product(product_type);
CREATE INDEX idx_product_active ON product(is_active);

-- coverage_standard
CREATE INDEX idx_coverage_code ON coverage_standard(coverage_code);
CREATE INDEX idx_coverage_domain_priority ON coverage_standard(domain, priority);
CREATE INDEX idx_coverage_is_main ON coverage_standard(is_main);

-- document
CREATE INDEX idx_document_product ON document(product_id);
CREATE INDEX idx_document_type ON document(document_type);
CREATE INDEX idx_document_priority ON document(doc_type_priority);

-- coverage_alias
CREATE INDEX idx_alias_insurer_coverage ON coverage_alias(insurer_id, insurer_coverage_name);
CREATE INDEX idx_alias_coverage ON coverage_alias(coverage_id);

-- coverage_code_alias
CREATE INDEX idx_code_alias_legacy ON coverage_code_alias(legacy_code);

-- coverage_subtype
CREATE INDEX idx_subtype_coverage ON coverage_subtype(coverage_id);

-- coverage_condition
CREATE INDEX idx_condition_coverage ON coverage_condition(coverage_id);
CREATE INDEX idx_condition_type ON coverage_condition(condition_type);

-- chunk
CREATE INDEX idx_chunk_document ON chunk(document_id);
CREATE INDEX idx_chunk_synthetic ON chunk(is_synthetic);
CREATE INDEX idx_chunk_document_synthetic ON chunk(document_id, is_synthetic);
CREATE INDEX idx_chunk_source ON chunk(synthetic_source_chunk_id) WHERE synthetic_source_chunk_id IS NOT NULL;

-- ========================================
-- Vector search index (Optional - pgvector 버전 확인 필요)
-- ========================================
-- IVFFLAT: pgvector 0.3.0+ 지원, 대용량 데이터셋에 적합
-- 초기 데이터 적을 때는 인덱스 없이도 동작 가능
CREATE INDEX idx_chunk_embedding ON chunk USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- HNSW: pgvector 0.5.0+ 지원, 검색 성능 우수하나 인덱스 구축 시간 김
-- 운영 환경에서 IVFFLAT 성능 부족 시 HNSW로 교체 고려:
-- DROP INDEX IF EXISTS idx_chunk_embedding;
-- CREATE INDEX idx_chunk_embedding ON chunk USING hnsw (embedding vector_cosine_ops);

-- pgvector 버전 확인: SELECT * FROM pg_extension WHERE extname = 'vector';
-- 인덱스 생성 실패 시: 인덱스 없이도 vector search 동작 가능 (성능 저하)

-- chunk_entity
CREATE INDEX idx_entity_chunk ON chunk_entity(chunk_id);
CREATE INDEX idx_entity_coverage ON chunk_entity(coverage_code);
CREATE INDEX idx_entity_type ON chunk_entity(entity_type);

-- amount_entity
CREATE INDEX idx_amount_chunk ON amount_entity(chunk_id);
CREATE INDEX idx_amount_coverage ON amount_entity(coverage_code);
CREATE INDEX idx_amount_context ON amount_entity(context_type);
CREATE INDEX idx_amount_coverage_context ON amount_entity(coverage_code, context_type);

-- ========================================
-- 트리거 (Triggers)
-- ========================================

-- updated_at 자동 갱신
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_insurer_updated_at BEFORE UPDATE ON insurer
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_updated_at BEFORE UPDATE ON product
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_coverage_standard_updated_at BEFORE UPDATE ON coverage_standard
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_updated_at BEFORE UPDATE ON document
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_coverage_alias_updated_at BEFORE UPDATE ON coverage_alias
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chunk_updated_at BEFORE UPDATE ON chunk
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- 제약 조건 체크 (Constraints)
-- ========================================

-- doc_type_priority 값 제한 (1~4)
ALTER TABLE document ADD CONSTRAINT chk_doc_type_priority
    CHECK (doc_type_priority BETWEEN 1 AND 4);

-- confidence 값 제한
ALTER TABLE coverage_alias ADD CONSTRAINT chk_confidence
    CHECK (confidence IN ('high', 'medium', 'low'));

-- condition_type 값 제한
ALTER TABLE coverage_condition ADD CONSTRAINT chk_condition_type
    CHECK (condition_type IN ('지급', '감액', '면책'));

-- context_type 값 제한
ALTER TABLE amount_entity ADD CONSTRAINT chk_context_type
    CHECK (context_type IN ('payment', 'count', 'limit'));

-- synthetic chunk는 반드시 source_chunk_id 필요
ALTER TABLE chunk ADD CONSTRAINT chk_synthetic_source
    CHECK (
        (is_synthetic = false AND synthetic_source_chunk_id IS NULL) OR
        (is_synthetic = true AND synthetic_source_chunk_id IS NOT NULL)
    );

-- ========================================
-- 뷰 (Views)
-- ========================================

-- 보험사별 활성 상품 목록
CREATE OR REPLACE VIEW v_active_products AS
SELECT
    i.insurer_code,
    i.insurer_name,
    p.product_code,
    p.product_name,
    p.product_type,
    p.sale_start_date,
    p.sale_end_date
FROM product p
JOIN insurer i ON p.insurer_id = i.insurer_id
WHERE p.is_active = true AND i.is_active = true;

-- 담보별 보험사 매핑 현황
CREATE OR REPLACE VIEW v_coverage_mapping AS
SELECT
    cs.coverage_code,
    cs.coverage_name,
    cs.domain,
    i.insurer_name,
    ca.insurer_coverage_name,
    ca.confidence,
    ca.mapping_method
FROM coverage_alias ca
JOIN coverage_standard cs ON ca.coverage_id = cs.coverage_id
JOIN insurer i ON ca.insurer_id = i.insurer_id
ORDER BY cs.coverage_code, i.insurer_name;

-- 원본 청크만 (비교/검색용)
CREATE OR REPLACE VIEW v_original_chunks AS
SELECT
    c.chunk_id,
    c.document_id,
    c.page_number,
    c.content,
    c.embedding,
    c.meta,
    d.document_type,
    d.doc_type_priority,
    p.product_name,
    i.insurer_name
FROM chunk c
JOIN document d ON c.document_id = d.document_id
JOIN product p ON d.product_id = p.product_id
JOIN insurer i ON p.insurer_id = i.insurer_id
WHERE c.is_synthetic = false;

-- Synthetic 청크 (Amount Bridge용)
CREATE OR REPLACE VIEW v_synthetic_chunks AS
SELECT
    c.chunk_id,
    c.content,
    c.synthetic_source_chunk_id,
    c.meta->>'synthetic_type' AS synthetic_type,
    c.meta->>'synthetic_method' AS synthetic_method,
    c.meta->'entities'->>'coverage_code' AS coverage_code
FROM chunk c
WHERE c.is_synthetic = true;

-- ========================================
-- 유틸리티 함수 (Utility Functions)
-- ========================================

-- 담보 코드로 도메인 조회
CREATE OR REPLACE FUNCTION get_coverage_domain(p_coverage_code VARCHAR)
RETURNS VARCHAR AS $$
    SELECT domain FROM coverage_standard WHERE coverage_code = p_coverage_code;
$$ LANGUAGE SQL IMMUTABLE;

-- 보험사 담보명으로 신정원 코드 조회
CREATE OR REPLACE FUNCTION resolve_coverage_code(
    p_insurer_code VARCHAR,
    p_coverage_name VARCHAR
)
RETURNS VARCHAR AS $$
    SELECT cs.coverage_code
    FROM coverage_alias ca
    JOIN coverage_standard cs ON ca.coverage_id = cs.coverage_id
    JOIN insurer i ON ca.insurer_id = i.insurer_id
    WHERE i.insurer_code = p_insurer_code
      AND ca.insurer_coverage_name = p_coverage_name
    LIMIT 1;
$$ LANGUAGE SQL STABLE;

-- ========================================
-- 데이터베이스 설정
-- ========================================

-- 문자열 비교 대소문자 구분 설정
-- ALTER DATABASE inca_rag_final SET lc_collate = 'ko_KR.UTF-8';
-- ALTER DATABASE inca_rag_final SET lc_ctype = 'ko_KR.UTF-8';

COMMENT ON DATABASE CURRENT_DATABASE() IS 'inca-RAG-final: 보험 약관 비교 RAG 시스템 (신정원 통일 담보 코드 기반)';

-- ========================================
-- 권한 정책 (Security & Access Control)
-- ========================================
-- coverage_standard 자동 INSERT 금지 정책
-- 운영 환경에서는 애플리케이션 role에 INSERT 권한 제거
-- 예시:
-- CREATE ROLE app_ingestion;
-- GRANT SELECT ON coverage_standard TO app_ingestion;
-- GRANT INSERT, UPDATE, DELETE ON coverage_alias TO app_ingestion;
-- REVOKE INSERT ON coverage_standard FROM app_ingestion;
--
-- coverage_standard는 관리자만 수동으로 INSERT 가능
-- CREATE ROLE admin_role;
-- GRANT ALL ON coverage_standard TO admin_role;
