# DB 설계 의사결정 문서 (Design Decisions)

## 개요

본 문서는 inca-RAG-final DB 스키마 설계 시 내린 핵심 의사결정과 그 이유를 명시한다.

---

## 1. 왜 coverage_standard를 분리했는가?

### 결정
`coverage_standard` 테이블을 독립된 마스터 테이블로 분리하고, **신정원 통일 담보 코드**를 유일한 비교 기준으로 설정

### 이유

#### 1.1 보험사 간 담보명 비일관성 문제
- 동일 담보를 보험사마다 다른 이름으로 표기
  - 삼성화재: "암진단금"
  - 현대해상: "암 진단비"
  - KB손해보험: "암진단자금"
- 이름 기반 비교는 불가능 → **코드 기반 정규화 필수**

#### 1.2 비교 로직의 단순화
- `coverage_standard.coverage_code` 기준으로 비교하면:
  - 보험사 추가 시 비교 로직 수정 불필요
  - 담보 추가 시 코드만 추가하면 자동 대응
  - LLM 기반 추론 최소화 (룰 기반 매핑 우선)

#### 1.3 데이터 무결성 보장
- coverage_standard는 **Report-only**
  - 자동 INSERT 금지
  - 수동 검증 후 추가
  - 담보 코드의 유일성 보장

#### 1.4 도메인 중심 설계
- `domain` (암/뇌/심혈관/상해 등) 컬럼을 통해:
  - 질의 시 domain 필터링
  - domain별 대표 담보 우선순위 관리
  - 크로스 도메인 비교 방지

### 대안 분석
| 대안 | 문제점 |
|------|--------|
| 보험사별 테이블 분리 | 보험사 추가마다 스키마 변경 필요 |
| 담보명 기반 비교 | 문자열 유사도 의존 → 불안정 |
| LLM 기반 실시간 매핑 | 비용, 지연시간, 일관성 문제 |

---

## 2. 왜 coverage_alias가 ingestion 단계에 필요한가?

### 결정
Ingestion 시점에 보험사 담보명을 자동으로 `coverage_alias`에 매핑

### 이유

#### 2.1 실시간 매핑의 비효율성
- Compare 단계에서 담보명 → 코드 매핑 시:
  - 매번 LLM 호출 필요
  - 응답 시간 증가
  - 비용 증가

#### 2.2 매핑 일관성 보장
- Ingestion 시 한 번 매핑 → 이후 재사용
- 동일 담보명은 항상 동일 coverage_code 반환
- 매핑 이력 추적 가능 (confidence, mapping_method)

#### 2.3 신뢰도 기반 필터링
```sql
-- Ingestion 시
INSERT INTO coverage_alias (insurer_id, coverage_id, insurer_coverage_name, confidence)
VALUES (1, 10, '암진단금', 'high');

-- Compare 시
SELECT coverage_code
FROM coverage_alias ca
JOIN coverage_standard cs ON ca.coverage_id = cs.coverage_id
WHERE ca.insurer_coverage_name = '암진단금'
  AND ca.confidence IN ('high', 'medium');
```

#### 2.4 점진적 개선 가능
- 초기: rule 기반 매핑
- 검증 후: confidence 상향
- 오류 발견 시: 수동 수정 및 재학습

### 매핑 전략
| 단계 | 방법 | Confidence |
|------|------|------------|
| 1 | 정확히 일치하는 담보명 | high |
| 2 | 규칙 기반 패턴 매칭 | medium |
| 3 | LLM 기반 유사도 | low → 검증 후 상향 |

---

## 3. 왜 synthetic chunk를 chunk 테이블에 두는가?

### 결정
Synthetic chunk를 별도 테이블로 분리하지 않고, `chunk` 테이블 내 `is_synthetic` flag로 구분

### 이유

#### 3.1 데이터 일관성
- 원본 chunk와 synthetic chunk 모두 동일한 스키마
  - chunk_text
  - embedding
  - meta (JSONB)
- 공통 처리 로직 적용 가능

#### 3.2 Amount Bridge 효율성
```sql
-- Amount Bridge 쿼리 (synthetic 포함)
SELECT ae.amount_value, c.chunk_text
FROM amount_entity ae
JOIN chunk c ON ae.chunk_id = c.chunk_id
WHERE ae.coverage_code = 'CA_DIAG_GENERAL'
  AND ae.context_type = 'payment'
-- is_synthetic 필터링 불필요
```

#### 3.3 명확한 필터링
- **Compare/Retrieval**: `WHERE is_synthetic = false`
- **Amount Bridge**: `is_synthetic` 무관
- 코드 레벨에서 명확한 분기 처리

#### 3.4 원본 추적 가능
- `synthetic_source_chunk_id` FK로 원본 chunk 참조
- 자기참조(self-referencing) 관계
- 원본 삭제 시 synthetic도 자동 정리 (CASCADE 고려)

### Meta 표준화
```json
{
  "is_synthetic": true,
  "synthetic_type": "split",
  "synthetic_method": "v1_6_3_beta_2_split",
  "synthetic_source_chunk_id": 1234,
  "entities": {
    "coverage_code": "CA_DIAG_GENERAL",
    "amount": {
      "amount_value": 5000000,
      "amount_text": "500만원",
      "confidence": "high"
    }
  }
}
```

### 대안 분석
| 대안 | 문제점 |
|------|--------|
| 별도 synthetic_chunk 테이블 | 스키마 중복, JOIN 복잡도 증가 |
| Meta에만 표시 (flag 없음) | WHERE 절에서 JSONB 쿼리 성능 저하 |
| 별도 amount_chunk 테이블 | Amount Bridge 외 다른 용도 확장 불가 |

---

## 4. 왜 amount를 meta/entity 구조로 설계했는가?

### 결정
금액 정보를 두 가지 방식으로 저장:
1. `chunk.meta` (JSONB) - 청크 수준 메타데이터
2. `amount_entity` 테이블 - 구조화된 금액 전용 테이블

### 이유

#### 4.1 Meta (JSONB)의 역할
- 청크 생성 시점의 컨텍스트 보존
- Synthetic chunk의 경우 원본 정보 유지
- 유연한 스키마 (향후 필드 추가 용이)

```json
// chunk.meta 예시
{
  "entities": {
    "coverage_code": "CA_DIAG_GENERAL",
    "amount": {
      "amount_value": 5000000,
      "amount_text": "500만원",
      "method": "v1_6_3_beta_2_split",
      "confidence": "high"
    }
  }
}
```

#### 4.2 amount_entity 테이블의 역할
- **구조화된 쿼리 성능**
  - JSONB 쿼리보다 B-tree 인덱스가 빠름
  - `coverage_code`, `context_type` 필터링 최적화
- **Amount Bridge 전용 설계**
  - payment vs count context 명확히 분리
  - 금액 범위 검색 (`amount_value BETWEEN`)
  - 집계 쿼리 효율성 (`AVG(amount_value)`)

#### 4.3 Context Type 분리 (중요)
```sql
CREATE TABLE amount_entity (
    context_type VARCHAR(50) NOT NULL, -- payment/count/limit
    ...
);
```

**문제 사례 (V1.6.x):**
- "암진단금 500만원, 연 1회 한도"
- "500만원"이 payment인지 count인지 불명확

**해결책:**
```sql
-- Payment context
INSERT INTO amount_entity (coverage_code, context_type, amount_value, amount_text)
VALUES ('CA_DIAG_GENERAL', 'payment', 5000000, '500만원');

-- Count context
INSERT INTO amount_entity (coverage_code, context_type, amount_value, amount_text)
VALUES ('CA_DIAG_GENERAL', 'count', 1, '연 1회');
```

#### 4.4 원문 보존의 중요성
- `amount_text`: "500만원", "5백만원", "5,000,000원"
- 비교 결과 표시 시 사용자에게 원문 그대로 제공
- 추출 오류 디버깅 시 필수

### Amount Bridge 쿼리 예시
```sql
-- 담보별 평균 지급 금액
SELECT
    coverage_code,
    AVG(amount_value) as avg_amount,
    COUNT(*) as sample_count
FROM amount_entity
WHERE context_type = 'payment'
GROUP BY coverage_code;

-- 특정 담보의 금액 증거 수집
SELECT
    c.chunk_text,
    ae.amount_value,
    ae.amount_text,
    ae.confidence
FROM amount_entity ae
JOIN chunk c ON ae.chunk_id = c.chunk_id
WHERE ae.coverage_code = 'CA_DIAG_GENERAL'
  AND ae.context_type = 'payment'
ORDER BY ae.confidence DESC;
```

---

## 5. 기존 V1.6.x 문제를 DB 설계로 어떻게 예방하는가?

### V1.6.x 주요 문제점
1. **임시 담보 코드 생성** → coverage_standard 오염
2. **Mixed coverage chunk 처리 불명확** → 비교 결과 오류
3. **금액 컨텍스트 혼동** → Amount Bridge 신뢰도 저하
4. **보험사별 코드 분기** → 확장성 저하
5. **Synthetic chunk 남용** → 비교 왜곡

### DB 설계 예방 메커니즘

#### 5.1 임시 담보 코드 생성 방지
**DB 제약:**
```sql
-- coverage_standard는 수동 INSERT만 허용
-- 애플리케이션 레벨에서 자동 INSERT 권한 제거
GRANT SELECT ON coverage_standard TO app_user;
REVOKE INSERT ON coverage_standard FROM app_user;
```

**프로세스:**
1. Ingestion 중 미등록 담보 발견 → `coverage_alias` 임시 저장
2. 관리자 검토 → `coverage_standard` 수동 추가
3. 재처리 → 정식 매핑 완료

#### 5.2 Mixed Coverage Chunk 명확한 처리
**원본 보존:**
```sql
-- 원본 chunk (mixed)
INSERT INTO chunk (chunk_text, is_synthetic)
VALUES ('암 500만원, 뇌출혈 300만원', false);

-- Synthetic chunk (분해)
INSERT INTO chunk (chunk_text, is_synthetic, synthetic_source_chunk_id, meta)
VALUES
  ('암 500만원', true, 1234, '{"synthetic_type": "split", ...}'),
  ('뇌출혈 300만원', true, 1234, '{"synthetic_type": "split", ...}');
```

**비교 시 필터:**
```sql
-- Compare/Retrieval에서 원본만 사용
SELECT * FROM chunk WHERE is_synthetic = false;
```

#### 5.3 금액 컨텍스트 분리
**제약:**
```sql
ALTER TABLE amount_entity ADD CONSTRAINT chk_context_type
    CHECK (context_type IN ('payment', 'count', 'limit'));
```

**쿼리 분리:**
```sql
-- Payment 금액만
SELECT * FROM amount_entity WHERE context_type = 'payment';

-- Count 금액만
SELECT * FROM amount_entity WHERE context_type = 'count';
```

#### 5.4 보험사 확장성
**스키마 불변:**
- 보험사 추가: `insurer` INSERT
- 상품 추가: `product` INSERT
- 담보 매핑: `coverage_alias` 자동 생성

**테이블 컬럼 분기 제거:**
```sql
-- ❌ 잘못된 설계 (V1.6.x)
-- ALTER TABLE coverage ADD COLUMN samsung_code VARCHAR(100);
-- ALTER TABLE coverage ADD COLUMN hyundai_code VARCHAR(100);

-- ✅ 올바른 설계 (V2.0)
-- coverage_alias 테이블로 N:M 관계 표현
```

#### 5.5 Synthetic Chunk 사용 제한
**View 제공:**
```sql
-- 원본 청크만 (비교/검색용)
CREATE VIEW v_original_chunks AS
SELECT * FROM chunk WHERE is_synthetic = false;

-- Application은 view 사용 강제
```

**명확한 문서화:**
- `schema.sql` COMMENT
- `erd.md` 사용 제한 명시
- API 레벨에서 필터링 강제

---

## 6. 추가 설계 결정

### 6.1 JSONB vs 별도 테이블
**결정:** Meta 정보는 JSONB, 구조화된 엔티티는 별도 테이블

| 데이터 유형 | 저장 방식 | 이유 |
|------------|----------|------|
| 청크 메타 정보 | chunk.meta (JSONB) | 유연성, 버전별 차이 수용 |
| 담보 엔티티 | chunk_entity | 쿼리 성능, FK 무결성 |
| 금액 엔티티 | amount_entity | 집계 쿼리, 인덱스 효율 |

### 6.2 Vector Index 선택
**결정:** IVFFLAT (초기) → HNSW (운영)

```sql
-- 초기 (데이터 적을 때)
CREATE INDEX idx_chunk_embedding ON chunk
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 운영 (데이터 많을 때, PostgreSQL 16+)
CREATE INDEX idx_chunk_embedding ON chunk
USING hnsw (embedding vector_cosine_ops);
```

### 6.3 문서 우선순위 정책
**결정:** `doc_type_priority` 컬럼으로 명시적 우선순위 관리

```sql
doc_type_priority:
  1 = 약관 (최우선)
  2 = 사업방법서
  3 = 상품요약서
  4 = 가입설계서
```

**활용:**
```sql
-- 담보 정보 조회 시 우선순위 높은 문서 우선
SELECT c.chunk_text
FROM chunk c
JOIN document d ON c.document_id = d.document_id
WHERE c.coverage_code = 'CA_DIAG_GENERAL'
ORDER BY d.doc_type_priority ASC
LIMIT 1;
```

### 6.4 Soft Delete vs Hard Delete
**결정:** Hard Delete (CASCADE) + 이력 테이블 별도 관리

```sql
-- 보험사 삭제 시 연관 데이터 자동 삭제
ON DELETE CASCADE

-- 필요 시 이력 테이블 추가
CREATE TABLE insurer_history AS SELECT * FROM insurer WHERE false;
```

---

## 7. 향후 확장 고려 사항

### 7.1 보험 계약 정보
```sql
-- 추후 추가 가능
CREATE TABLE policy (
    policy_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES product(product_id),
    policyholder_id INTEGER,
    policy_number VARCHAR(100),
    ...
);
```

### 7.2 사용자 질의 이력
```sql
CREATE TABLE query_history (
    query_id SERIAL PRIMARY KEY,
    user_id INTEGER,
    query_text TEXT,
    selected_coverages TEXT[],
    response JSONB,
    created_at TIMESTAMP
);
```

### 7.3 비교 결과 캐싱
```sql
CREATE TABLE comparison_cache (
    cache_id SERIAL PRIMARY KEY,
    coverage_codes TEXT[],
    insurer_ids INTEGER[],
    result JSONB,
    created_at TIMESTAMP,
    expires_at TIMESTAMP
);
```

---

## 8. 운영 적용 시 필수 확인 사항

### 8.0 DDL 적용 원칙 (필수)
**절대 원칙:** `schema.sql`은 빈 PostgreSQL 데이터베이스에 단일 실행으로 오류 없이 적용 가능해야 한다.

**환경 의존 요소 분리:**
- pgvector 인덱스 (IVFFLAT/HNSW)는 선택 실행으로 주석 처리
- 데이터베이스명 의존 구문은 주석 처리
- 환경별 설정(권한, collation 등)은 선택 적용

**검증 방법:**
```bash
# Docker 환경에서 검증
docker run --name postgres_test -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_DB=inca_rag_final_test -d pgvector/pgvector:pg16

docker exec -i postgres_test psql -U postgres -d inca_rag_final_test < schema.sql

# 테이블 생성 확인
docker exec postgres_test psql -U postgres -d inca_rag_final_test -c "\dt"
```

### 8.1 is_synthetic 필터링 규칙 (강제)
**절대 규칙:** 필터링은 `chunk.is_synthetic` 컬럼 기준, `meta` JSONB 필드 사용 금지

```sql
-- ✅ 올바른 필터링 (Compare/Retrieval)
SELECT * FROM chunk WHERE is_synthetic = false;

-- ❌ 잘못된 필터링 (성능 저하)
SELECT * FROM chunk WHERE meta->>'is_synthetic' = 'false';
```

**이유:**
- B-tree 인덱스 활용 가능 (컬럼)
- JSONB 쿼리는 인덱스 효율 저하
- meta는 참고용, 필터링 금지

### 8.2 컬럼명 표준: `content` (not `chunk_text`)
기존 코드베이스 호환성을 위해 청크 본문 컬럼명은 **`content`**로 확정

```python
# ✅ 표준
chunk.content

# ❌ 비표준
chunk.chunk_text
```

### 8.3 UNIQUE 제약 조건
```sql
-- product: 보험사 내 상품 코드 중복 방지
UNIQUE(insurer_id, product_code)

-- document: 동일 상품의 동일 문서 중복 방지
UNIQUE(product_id, document_type, file_hash)

-- coverage_alias: 보험사별 담보명 중복 방지
UNIQUE(insurer_id, insurer_coverage_name)
```

---

## 9. 왜 보험료를 독립 테이블로 설계했는가? (v2 확장)

### 결정
`premium` 테이블을 별도로 분리하고, 연령/성별/납입방식별 보험료를 구조화

### 이유

#### 9.1 보험료는 담보와 동일한 복잡성을 갖는다
- 동일 상품이라도:
  - 30세 남성 vs 40세 여성 → 보험료 다름
  - 20년납 vs 전기납 → 보험료 다름
  - 100세만기 vs 80세만기 → 보험료 다름

#### 9.2 `product.meta` JSONB 저장의 문제점
```json
// ❌ 잘못된 설계
{
  "premium": {
    "30M_20_100": 50000,
    "30F_20_100": 45000,
    ...
  }
}
```
- SQL 집계 불가능 (`MIN(premium_amount)` 등)
- 인덱스 불가능 (성능 저하)
- 연령대별 분포 분석 불가능

#### 9.3 비교 쿼리가 SQL 레벨에서 가능해야 한다
```sql
-- ✅ 보험료 최저 TOP 5 (SQL만으로 가능)
SELECT product_name, premium_amount
FROM premium pr
JOIN product p ON pr.product_id = p.product_id
WHERE age = 30 AND gender = 'M'
ORDER BY premium_amount ASC
LIMIT 5;
```

#### 9.4 UNIQUE 제약으로 중복 방지
```sql
UNIQUE(product_id, age, gender, payment_period, coverage_period, payment_method)
```
- 동일 조건의 보험료 중복 삽입 방지
- Idempotent ingestion 보장

### 대안 분석
| 대안 | 문제점 |
|------|--------|
| product.meta JSONB | SQL 집계 불가, 인덱스 불가 |
| product.premium_amount (단일 컬럼) | 연령/성별별 다른 보험료 표현 불가 |
| 별도 서비스에서 계산 | 데이터 일관성 보장 불가, 재현 불가 |

---

## 10. 왜 비교 우선순위를 데이터 모델에 반영했는가? (v2 확장)

### 결정
비교 우선순위(보험료 우선 vs 보상 우선)를 **쿼리 파라미터 + SQL CASE**로 처리

### 이유

#### 10.1 "우선순위는 사용자 선택"이다
- 고정된 순위가 아니라 런타임 파라미터
- 별도 `ranking_rule` 테이블은 over-engineering

#### 10.2 SQL CASE로 충분히 표현 가능
```sql
SELECT product_name,
       CASE WHEN $1 = 'premium' THEN premium_amount
            ELSE -coverage_amount END as sort_value
FROM ...
ORDER BY sort_value ASC;
```

#### 10.3 데이터 모델이 "비교 가능성"을 보장
- `premium` 테이블: 보험료 비교 가능
- `product_coverage` 테이블: 보상 금액 비교 가능
- 우선순위는 Application이 결정, 데이터는 중립

### 대안 분석
| 대안 | 문제점 |
|------|--------|
| ranking_rule 테이블 | 고정된 순위, 유연성 저하 |
| Application에서만 처리 | SQL 집계/필터 불가능 |
| View로 고정 | 사용자 선택 불가 |

---

## 11. product_coverage 테이블의 필요성 (v2 확장)

### 결정
상품별 담보 보장 금액을 `product_coverage` 테이블로 명시적 관리

### 이유

#### 11.1 "상품 × 담보" 관계는 N:M이다
- 1개 상품 → 여러 담보
- 1개 담보 → 여러 상품

#### 11.2 보장 금액은 상품마다 다르다
- 삼성화재 암플러스: 암진단금 5000만원
- 현대해상 프리미엄: 암진단금 3000만원
- 동일 담보(`CA_DIAG_GENERAL`)이지만 금액 다름

#### 11.3 비교 쿼리의 핵심 테이블
```sql
-- 암진단금 5000만원 이상 상품
SELECT product_name, coverage_amount
FROM product_coverage pc
JOIN coverage_standard cs ON pc.coverage_id = cs.coverage_id
WHERE cs.coverage_code = 'CA_DIAG_GENERAL'
  AND pc.coverage_amount >= 50000000;
```

#### 11.4 FK로 신정원 코드 정합 강제
```sql
coverage_id INTEGER NOT NULL REFERENCES coverage_standard(coverage_id)
```
- 존재하지 않는 담보 코드 → INSERT 실패
- Application-level 검증 불필요

### UNIQUE 제약
```sql
UNIQUE(product_id, coverage_id)
```
- 동일 상품에 동일 담보 중복 방지

---

## 요약

| 질문 | 답변 |
|------|------|
| **왜 coverage_standard를 분리?** | 보험사 간 담보명 비일관성 해결, 코드 기반 정규화, 비교 로직 단순화 |
| **왜 coverage_alias가 ingestion에 필요?** | 실시간 매핑 비효율 제거, 일관성 보장, 신뢰도 기반 필터링 |
| **왜 synthetic chunk를 chunk에?** | 스키마 일관성, Amount Bridge 효율성, 명확한 필터링 |
| **왜 amount를 meta/entity 구조로?** | Meta는 유연성, Entity는 쿼리 성능, Context 분리로 정확도 향상 |
| **V1.6.x 문제 예방법?** | DB 제약, 권한 분리, View 강제, 명확한 문서화 |
| **is_synthetic 필터링 규칙?** | `chunk.is_synthetic` 컬럼 사용, meta JSONB 사용 금지 |
| **청크 본문 컬럼명?** | `content` (기존 코드 호환성) |
| **왜 보험료를 독립 테이블로?** (v2) | SQL 집계 가능, 인덱스 활용, 연령/성별별 구조화 |
| **비교 우선순위 처리?** (v2) | 쿼리 파라미터 + SQL CASE, 데이터 모델은 중립 유지 |
| **product_coverage 필요성?** (v2) | 상품×담보 N:M 관계, FK로 신정원 코드 정합 강제 |

**핵심 원칙:**
1. 신정원 코드 중심 (coverage_standard)
2. Synthetic chunk 명확한 분리 (is_synthetic flag)
3. Amount Bridge 전용 설계 (amount_entity + context_type)
4. 확장 가능한 스키마 (보험사/문서/담보 추가 시 데이터만 변경)
5. **필터링은 컬럼 기준, meta는 참고용**
6. **비교는 데이터 모델이 강제, 서비스는 조합만** (v2)
