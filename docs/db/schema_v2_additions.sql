-- ========================================
-- inca-RAG-final DB Schema v2 Additions
-- ========================================
-- STEP 2-EXT: 보험료 + 상품비교 확장
-- 기존 schema.sql 과 완전 호환 (ADD ONLY, DROP 금지)
-- ========================================

-- ========================================
-- 신규 테이블 (v2)
-- ========================================

-- 보험료 테이블
CREATE TABLE premium (
    premium_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    age INTEGER NOT NULL,
    gender VARCHAR(1) NOT NULL,
    payment_period INTEGER NOT NULL,
    coverage_period INTEGER NOT NULL,
    payment_method VARCHAR(20) DEFAULT '월납',
    premium_amount NUMERIC(12, 2) NOT NULL,
    effective_date DATE,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, age, gender, payment_period, coverage_period, payment_method)
);

COMMENT ON TABLE premium IS '보험료 테이블 (연령/성별/납입방식별)';
COMMENT ON COLUMN premium.age IS '가입 연령';
COMMENT ON COLUMN premium.gender IS '성별 (M/F)';
COMMENT ON COLUMN premium.payment_period IS '납입 기간 (년)';
COMMENT ON COLUMN premium.coverage_period IS '보장 기간 (년, 100=100세만기)';
COMMENT ON COLUMN premium.payment_method IS '납입 방식 (월납/연납/일시납)';
COMMENT ON COLUMN premium.premium_amount IS '보험료 (원)';
COMMENT ON COLUMN premium.effective_date IS '요율 적용 시작일';

-- 상품별 담보 보장 정보
CREATE TABLE product_coverage (
    product_coverage_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    coverage_id INTEGER NOT NULL REFERENCES coverage_standard(coverage_id) ON DELETE CASCADE,
    coverage_amount NUMERIC(15, 2) NOT NULL,
    coverage_limit_type VARCHAR(50),
    coverage_frequency VARCHAR(50),
    coverage_max_count INTEGER,
    effective_date DATE,
    coverage_details JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, coverage_id)
);

COMMENT ON TABLE product_coverage IS '상품별 담보 보장 금액 및 조건';
COMMENT ON COLUMN product_coverage.coverage_amount IS '보장 금액 (원)';
COMMENT ON COLUMN product_coverage.coverage_limit_type IS '보장 유형 (일시금/연금/실손 등)';
COMMENT ON COLUMN product_coverage.coverage_frequency IS '지급 빈도 (1회/연간/무제한 등)';
COMMENT ON COLUMN product_coverage.coverage_max_count IS '최대 지급 횟수';
COMMENT ON COLUMN product_coverage.effective_date IS '보장 시작일';

-- ========================================
-- 인덱스 (Index Strategy)
-- ========================================

-- premium
CREATE INDEX idx_premium_product ON premium(product_id);
CREATE INDEX idx_premium_age_gender ON premium(age, gender);
CREATE INDEX idx_premium_amount ON premium(premium_amount);
CREATE INDEX idx_premium_lookup ON premium(product_id, age, gender, payment_period, coverage_period);

-- product_coverage
CREATE INDEX idx_product_coverage_product ON product_coverage(product_id);
CREATE INDEX idx_product_coverage_coverage ON product_coverage(coverage_id);
CREATE INDEX idx_product_coverage_amount ON product_coverage(coverage_amount);

-- ========================================
-- 제약 조건 (Constraints)
-- ========================================

-- premium 제약
ALTER TABLE premium ADD CONSTRAINT chk_premium_age
    CHECK (age BETWEEN 0 AND 100);

ALTER TABLE premium ADD CONSTRAINT chk_premium_gender
    CHECK (gender IN ('M', 'F'));

ALTER TABLE premium ADD CONSTRAINT chk_premium_payment_period
    CHECK (payment_period > 0 AND payment_period <= 100);

ALTER TABLE premium ADD CONSTRAINT chk_premium_coverage_period
    CHECK (coverage_period > 0 AND coverage_period <= 100);

ALTER TABLE premium ADD CONSTRAINT chk_premium_amount
    CHECK (premium_amount >= 0);

ALTER TABLE premium ADD CONSTRAINT chk_premium_payment_method
    CHECK (payment_method IN ('월납', '연납', '일시납', '전기납'));

-- product_coverage 제약
ALTER TABLE product_coverage ADD CONSTRAINT chk_coverage_amount
    CHECK (coverage_amount >= 0);

ALTER TABLE product_coverage ADD CONSTRAINT chk_coverage_max_count
    CHECK (coverage_max_count IS NULL OR coverage_max_count > 0);

-- ========================================
-- 트리거 (Triggers)
-- ========================================

CREATE TRIGGER update_premium_updated_at BEFORE UPDATE ON premium
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_coverage_updated_at BEFORE UPDATE ON product_coverage
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- 뷰 (Views)
-- ========================================

-- 보험료 최저 상품 (연령/성별별)
CREATE OR REPLACE VIEW v_lowest_premium_by_age AS
SELECT
    age,
    gender,
    payment_period,
    coverage_period,
    product_id,
    MIN(premium_amount) as lowest_premium
FROM premium
GROUP BY age, gender, payment_period, coverage_period, product_id
ORDER BY age, gender, lowest_premium;

-- 상품별 담보 보장 요약
CREATE OR REPLACE VIEW v_product_coverage_summary AS
SELECT
    p.product_id,
    p.product_name,
    i.insurer_name,
    cs.coverage_name,
    cs.coverage_code,
    pc.coverage_amount,
    pc.coverage_limit_type,
    pc.coverage_frequency
FROM product_coverage pc
JOIN product p ON pc.product_id = p.product_id
JOIN insurer i ON p.insurer_id = i.insurer_id
JOIN coverage_standard cs ON pc.coverage_id = cs.coverage_id
ORDER BY i.insurer_name, p.product_name, cs.coverage_code;

-- 보험료 + 담보 통합 뷰
CREATE OR REPLACE VIEW v_product_comparison AS
SELECT
    p.product_id,
    p.product_name,
    i.insurer_name,
    pr.age,
    pr.gender,
    pr.premium_amount,
    cs.coverage_code,
    cs.coverage_name,
    pc.coverage_amount
FROM product p
JOIN insurer i ON p.insurer_id = i.insurer_id
LEFT JOIN premium pr ON p.product_id = pr.product_id
LEFT JOIN product_coverage pc ON p.product_id = pc.product_id
LEFT JOIN coverage_standard cs ON pc.coverage_id = cs.coverage_id
WHERE p.is_active = true;

-- ========================================
-- 유틸리티 함수 (Utility Functions)
-- ========================================

-- 특정 조건의 보험료 조회
CREATE OR REPLACE FUNCTION get_premium(
    p_product_id INTEGER,
    p_age INTEGER,
    p_gender VARCHAR,
    p_payment_period INTEGER,
    p_coverage_period INTEGER
)
RETURNS NUMERIC AS $$
    SELECT premium_amount
    FROM premium
    WHERE product_id = p_product_id
      AND age = p_age
      AND gender = p_gender
      AND payment_period = p_payment_period
      AND coverage_period = p_coverage_period
    LIMIT 1;
$$ LANGUAGE SQL STABLE;

-- 상품별 특정 담보 보장 금액 조회
CREATE OR REPLACE FUNCTION get_coverage_amount(
    p_product_id INTEGER,
    p_coverage_code VARCHAR
)
RETURNS NUMERIC AS $$
    SELECT pc.coverage_amount
    FROM product_coverage pc
    JOIN coverage_standard cs ON pc.coverage_id = cs.coverage_id
    WHERE pc.product_id = p_product_id
      AND cs.coverage_code = p_coverage_code
    LIMIT 1;
$$ LANGUAGE SQL STABLE;

-- ========================================
-- 검증 쿼리 (Validation Queries)
-- ========================================

-- 1. premium FK 무결성
COMMENT ON TABLE premium IS '
검증 쿼리:
SELECT COUNT(*) FROM premium pr
LEFT JOIN product p ON pr.product_id = p.product_id
WHERE p.product_id IS NULL;
-- 결과: 0 (FK 보장됨)
';

-- 2. product_coverage FK 무결성
COMMENT ON TABLE product_coverage IS '
검증 쿼리:
SELECT COUNT(*) FROM product_coverage pc
LEFT JOIN coverage_standard cs ON pc.coverage_id = cs.coverage_id
WHERE cs.coverage_id IS NULL;
-- 결과: 0 (신정원 코드 정합 보장됨)
';

-- ========================================
-- 마이그레이션 노트
-- ========================================

-- 기존 schema.sql 실행 후 본 파일 실행:
-- psql -d inca_rag_final -f docs/db/schema.sql
-- psql -d inca_rag_final -f docs/db/schema_v2_additions.sql

-- 또는 통합 스크립트:
-- cat docs/db/schema.sql docs/db/schema_v2_additions.sql | psql -d inca_rag_final

-- ========================================
-- 신정원 코드 정합 강제 (재명시)
-- ========================================

-- product_coverage.coverage_id는 반드시 coverage_standard.coverage_id FK
-- application-level에서 coverage_standard INSERT 절대 금지
-- UNMAPPED 담보는 coverage_alias + unmapped_log로만 관리

-- ========================================
-- Synthetic Chunk 오염 차단 (재명시)
-- ========================================

-- 비교 쿼리 예시 (필수 필터):
/*
SELECT c.content
FROM chunk c
JOIN document d ON c.document_id = d.document_id
JOIN product p ON d.product_id = p.product_id
WHERE p.product_id = ?
  AND c.is_synthetic = false;  -- 필수
*/

-- Amount Bridge (Synthetic 허용):
/*
SELECT ae.amount_value, c.content
FROM amount_entity ae
JOIN chunk c ON ae.chunk_id = c.chunk_id
WHERE ae.coverage_code = ?
  AND ae.context_type = 'payment';
-- is_synthetic 필터링 불필요
*/
