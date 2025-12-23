# 필수 SQL 질의 예시 (ERD v2 검증 기준)

## 개요

본 문서는 STEP 2-EXT (운영 헌법을 ERD로 강제) 단계의 **Definition of Done** 기준이 되는 SQL 질의 10개를 정의한다.

**목적:**
- ERD v2가 "이 쿼리들이 실행 가능한 최소 구조"로 설계되도록 강제
- 비교/보험료/조건 필터링이 "데이터 모델 차원"에서 가능함을 증명
- "서비스 로직으로 처리"하는 설계를 차단

**원칙:**
- 모든 쿼리는 **표준 SQL (PostgreSQL)** 로 작성
- JOIN만으로 해결 불가능한 요구는 **ERD 설계 실패**
- Application-level 필터링이 필요한 설계는 **폐기**

---

## 필수 질의 10개

### 1. 보험료 우선 비교 (TOP N)

**요구사항:** 특정 조건(연령, 성별, 상품 유형)에서 보험료가 가장 저렴한 상품 TOP 5

```sql
-- 30세 남성 기준, 암보험, 보험료 최저 TOP 5
SELECT
    p.product_name,
    i.insurer_name,
    pr.premium_amount,
    pr.age,
    pr.gender,
    pr.payment_period,
    pr.coverage_period
FROM premium pr
JOIN product p ON pr.product_id = p.product_id
JOIN insurer i ON p.insurer_id = i.insurer_id
WHERE pr.age = 30
  AND pr.gender = 'M'
  AND p.product_type = '암보험'
  AND pr.payment_period = 20  -- 20년납
  AND pr.coverage_period = 100 -- 100세만기
ORDER BY pr.premium_amount ASC
LIMIT 5;
```

**검증 포인트:**
- `premium` 테이블 필수
- `age`, `gender`, `payment_period`, `coverage_period` 컬럼 필수
- FK: `premium.product_id` → `product.product_id`

---

### 2. 보상 우선 비교 (특정 담보 한도)

**요구사항:** 특정 담보(암진단금)의 보장 금액이 5000만원 이상인 상품, 보험료 낮은 순

```sql
-- 암진단금 5000만원 이상 상품, 보험료 낮은 순
SELECT
    p.product_name,
    i.insurer_name,
    cs.coverage_name,
    pc.coverage_amount,
    pr.premium_amount
FROM product_coverage pc
JOIN product p ON pc.product_id = p.product_id
JOIN insurer i ON p.insurer_id = i.insurer_id
JOIN coverage_standard cs ON pc.coverage_id = cs.coverage_id
LEFT JOIN premium pr ON pc.product_id = pr.product_id
    AND pr.age = 30
    AND pr.gender = 'M'
WHERE cs.coverage_code = 'CA_DIAG_GENERAL'
  AND pc.coverage_amount >= 50000000
ORDER BY pr.premium_amount ASC NULLS LAST;
```

**검증 포인트:**
- `product_coverage` 테이블 필수
- `coverage_amount` 컬럼 필수
- FK: `product_coverage.product_id` → `product.product_id`
- FK: `product_coverage.coverage_id` → `coverage_standard.coverage_id`

---

### 3. Synthetic 오염 차단 검증 (비교 축)

**요구사항:** 상품 비교 시 Synthetic chunk는 절대 포함되지 않음을 구조적으로 보장

```sql
-- 비교 축 검색: is_synthetic=false 필수 필터
SELECT
    c.chunk_id,
    c.content,
    d.document_type,
    c.is_synthetic
FROM chunk c
JOIN document d ON c.document_id = d.document_id
JOIN product p ON d.product_id = p.product_id
WHERE p.product_id = 100
  AND c.is_synthetic = false;  -- 필수 필터 (컬럼 레벨)
```

**검증 포인트:**
- `chunk.is_synthetic` BOOLEAN NOT NULL
- `meta` JSONB로 필터링 금지 (성능 저하)
- CHECK 제약: `(is_synthetic = false AND synthetic_source_chunk_id IS NULL) OR (is_synthetic = true AND synthetic_source_chunk_id IS NOT NULL)`

---

### 4. 제자리암 조건 비교 (Subtype/Condition)

**요구사항:** 제자리암 보장 조건이 다른 상품 비교 (subtype, 지급 조건)

```sql
-- 제자리암 subtype 및 지급 조건 비교
SELECT
    p.product_name,
    i.insurer_name,
    cs.coverage_name,
    st.subtype_name,
    st.subtype_code,
    cond.condition_type,
    cond.condition_text
FROM product p
JOIN insurer i ON p.insurer_id = i.insurer_id
JOIN product_coverage pc ON p.product_id = pc.product_id
JOIN coverage_standard cs ON pc.coverage_id = cs.coverage_id
LEFT JOIN coverage_subtype st ON cs.coverage_id = st.coverage_id
LEFT JOIN coverage_condition cond ON cs.coverage_id = cond.coverage_id
    AND cond.condition_type = '지급'
WHERE cs.coverage_code = 'CA_DIAG_CARCINOMA_IN_SITU'
ORDER BY i.insurer_name, p.product_name;
```

**검증 포인트:**
- `coverage_subtype` 테이블 (경계성종양, 제자리암 등)
- `coverage_condition` 테이블 (지급/감액/면책)
- FK: `coverage_subtype.coverage_id` → `coverage_standard.coverage_id`

---

### 5. 보험사 제한 비교 (삼성 vs 메리츠)

**요구사항:** 특정 보험사만 비교 (삼성화재, 메리츠화재), 암진단금 기준

```sql
-- 삼성화재 vs 메리츠화재, 암진단금 비교
SELECT
    i.insurer_name,
    p.product_name,
    pc.coverage_amount,
    pr.premium_amount
FROM product p
JOIN insurer i ON p.insurer_id = i.insurer_id
JOIN product_coverage pc ON p.product_id = pc.product_id
JOIN coverage_standard cs ON pc.coverage_id = cs.coverage_id
LEFT JOIN premium pr ON p.product_id = pr.product_id
    AND pr.age = 35
    AND pr.gender = 'F'
WHERE i.insurer_code IN ('SAMSUNG', 'MERITZ')
  AND cs.coverage_code = 'CA_DIAG_GENERAL'
ORDER BY i.insurer_name, pr.premium_amount;
```

**검증 포인트:**
- `insurer.insurer_code` UNIQUE
- FK 관계: `product` → `insurer`

---

### 6. 신정원 코드 FK 강제 검증

**요구사항:** 존재하지 않는 `coverage_code` 참조 시 INSERT 실패 (FK 위반)

```sql
-- ❌ 실패해야 정상 (coverage_standard에 없는 coverage_id)
INSERT INTO coverage_alias (insurer_id, coverage_id, insurer_coverage_name, confidence)
VALUES (1, 9999, '존재하지않는담보', 'high');
-- ERROR: insert or update on table "coverage_alias" violates foreign key constraint

-- ✅ 성공 (coverage_standard에 존재하는 coverage_id)
INSERT INTO coverage_alias (insurer_id, coverage_id, insurer_coverage_name, confidence)
SELECT 1, coverage_id, '정상담보', 'high'
FROM coverage_standard
WHERE coverage_code = 'CA_DIAG_GENERAL';
```

**검증 포인트:**
- FK: `coverage_alias.coverage_id` → `coverage_standard.coverage_id` (NOT NULL)
- FK: `product_coverage.coverage_id` → `coverage_standard.coverage_id` (NOT NULL)
- Application-level에서 `coverage_standard` INSERT 절대 금지

---

### 7. 연령대별 보험료 분포

**요구사항:** 특정 상품의 연령대별 보험료 추이 조회

```sql
-- 30~40세 연령대별 평균 보험료
SELECT
    pr.age,
    AVG(pr.premium_amount) as avg_premium,
    MIN(pr.premium_amount) as min_premium,
    MAX(pr.premium_amount) as max_premium,
    COUNT(*) as sample_count
FROM premium pr
WHERE pr.product_id = 100
  AND pr.age BETWEEN 30 AND 40
  AND pr.gender = 'M'
GROUP BY pr.age
ORDER BY pr.age;
```

**검증 포인트:**
- `premium` 테이블의 연령별 행 존재
- 집계 쿼리 가능

---

### 8. 담보별 한도 차이 (상품 간)

**요구사항:** 동일 담보(암직접입원비)에 대한 상품별 한도 차이 비교

```sql
-- 암직접입원비 담보, 상품별 한도 비교
SELECT
    p.product_name,
    i.insurer_name,
    cs.coverage_name,
    pc.coverage_amount,
    pc.coverage_limit_type,
    pc.coverage_frequency
FROM product_coverage pc
JOIN product p ON pc.product_id = p.product_id
JOIN insurer i ON p.insurer_id = i.insurer_id
JOIN coverage_standard cs ON pc.coverage_id = cs.coverage_id
WHERE cs.coverage_code = 'CA_HOSP_DIRECT'
ORDER BY pc.coverage_amount DESC;
```

**검증 포인트:**
- `product_coverage.coverage_amount` (금액)
- `product_coverage.coverage_limit_type` (일시금/연금 등) (선택)
- `product_coverage.coverage_frequency` (1회/연간 등) (선택)

---

### 9. Amount Bridge (Synthetic 포함 허용)

**요구사항:** 금액 증거 수집 시 Synthetic chunk 포함 허용 (Amount Bridge 전용)

```sql
-- 금액 증거 수집 (Synthetic 포함)
SELECT
    c.content,
    ae.amount_value,
    ae.amount_text,
    ae.context_type,
    c.is_synthetic,
    c.synthetic_source_chunk_id
FROM amount_entity ae
JOIN chunk c ON ae.chunk_id = c.chunk_id
WHERE ae.coverage_code = 'CA_DIAG_GENERAL'
  AND ae.context_type = 'payment'
ORDER BY ae.confidence DESC, ae.amount_value DESC;
-- is_synthetic 필터링 불필요 (Amount Bridge 전용)
```

**검증 포인트:**
- Synthetic chunk 포함 가능 (필터링 없음)
- `amount_entity.context_type` (payment/count/limit) 필수
- `amount_entity.coverage_code` FK → `coverage_standard.coverage_code`

---

### 10. 우선순위 기반 정렬 (보험료 vs 보상)

**요구사항:** 사용자 선택에 따라 보험료 우선 또는 보상 우선 정렬

```sql
-- 보험료 우선 vs 보상 우선 (ranking_mode 파라미터)
-- ranking_mode = 'premium' | 'coverage'

SELECT
    p.product_name,
    i.insurer_name,
    pr.premium_amount,
    pc.coverage_amount,
    CASE
        WHEN $1 = 'premium' THEN pr.premium_amount
        ELSE -pc.coverage_amount  -- 보상은 내림차순이므로 음수 변환
    END as sort_value
FROM product p
JOIN insurer i ON p.insurer_id = i.insurer_id
JOIN premium pr ON p.product_id = pr.product_id
JOIN product_coverage pc ON p.product_id = pc.product_id
WHERE pr.age = 30
  AND pr.gender = 'M'
  AND pc.coverage_id = (SELECT coverage_id FROM coverage_standard WHERE coverage_code = 'CA_DIAG_GENERAL')
ORDER BY sort_value ASC;
```

**검증 포인트:**
- 우선순위는 Application 파라미터로 전달
- 정렬은 SQL CASE로 처리 (데이터 모델 기반)
- "우선순위 룰"을 별도 테이블로 관리할 필요 없음 (over-engineering)

---

## 추가 검증 쿼리

### A. 중복 방지 검증

```sql
-- product_coverage UNIQUE 검증
SELECT product_id, coverage_id, COUNT(*)
FROM product_coverage
GROUP BY product_id, coverage_id
HAVING COUNT(*) > 1;
-- 결과: 0 rows (정상)
```

### B. Synthetic chunk 정책 위반 검증

```sql
-- Synthetic chunk에 source_chunk_id 누락 검사
SELECT chunk_id, is_synthetic, synthetic_source_chunk_id
FROM chunk
WHERE is_synthetic = true AND synthetic_source_chunk_id IS NULL;
-- 결과: 0 rows (정상, CHECK 제약으로 차단됨)
```

### C. coverage_standard 참조 무결성

```sql
-- amount_entity에 존재하지 않는 coverage_code
SELECT DISTINCT ae.coverage_code
FROM amount_entity ae
LEFT JOIN coverage_standard cs ON ae.coverage_code = cs.coverage_code
WHERE cs.coverage_code IS NULL;
-- 결과: 0 rows (정상, FK로 차단됨)
```

---

## ERD v2 필수 테이블 도출

위 쿼리를 기반으로 다음 테이블이 **필수**로 포함되어야 한다:

| 테이블 | 목적 | 관련 쿼리 |
|--------|------|----------|
| `premium` | 보험료 저장 (연령/성별/납입방식별) | Q1, Q2, Q7, Q10 |
| `product_coverage` | 상품별 담보 보장 금액/조건 | Q2, Q4, Q5, Q8, Q10 |
| `coverage_subtype` | 담보 세부 유형 (제자리암, 경계성종양 등) | Q4 |
| `coverage_condition` | 지급/감액/면책 조건 | Q4 |

**기존 테이블 (STEP 2):**
- `insurer`, `product`, `document`, `coverage_standard`, `coverage_alias`, `chunk`, `chunk_entity`, `amount_entity`

---

## Definition of Done (DoD)

ERD v2 설계가 완료되었다고 판단하는 기준:

- [ ] 위 10개 쿼리가 모두 **syntax error 없이 실행 가능**
- [ ] Q6 (FK 위반)이 **INSERT 실패**로 차단됨
- [ ] Q3 (Synthetic 필터)가 **컬럼 레벨**에서 처리됨 (meta JSONB 사용 안 함)
- [ ] `premium`, `product_coverage` 테이블 스키마 확정
- [ ] FK/UNIQUE 제약이 모든 관계에 명시됨
- [ ] `schema_v2.sql` 생성 완료 (기존 schema.sql과 호환, ADD ONLY)

---

## 금지 사항

다음 설계는 **즉시 폐기**:

1. ❌ "이 쿼리는 Application에서 처리합니다"
2. ❌ `meta` JSONB로 핵심 필터링 (Q3, Q9)
3. ❌ `coverage_standard` 우회 설계 (임시 코드 생성)
4. ❌ Synthetic chunk를 비교 축에 사용 가능한 구조
5. ❌ 보험료를 `product.meta` JSONB에 저장

---

## 다음 단계

1. ERD v2 설계 (이 쿼리들이 실행 가능한 최소 구조)
2. `schema_v2.sql` 생성 (기존 schema.sql + 신규 테이블 ADD)
3. PostgreSQL Docker 환경에서 쿼리 검증
4. `design_decisions.md` 보강 ("왜 보험료를 독립 테이블로?")
