# ERD 설명 - inca-RAG-final DB 스키마

## 개요

본 문서는 보험 약관 비교 RAG 시스템의 데이터베이스 스키마를 설명한다.

**핵심 원칙:**
- 신정원 통일 담보 코드(`coverage_standard.coverage_code`)가 유일한 비교 기준
- Synthetic chunk는 Amount Bridge 전용 보조 데이터
- 보험사 추가 시 스키마 변경 없이 데이터만 추가

---

## 테이블 계층 구조

```
┌─────────────────────────────────────────────────────────┐
│            기준/마스터 계층 (Canonical Layer)             │
│  - insurer, product, document, coverage_standard        │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│         매핑/정규화 계층 (Normalization Layer)           │
│  - coverage_alias, coverage_code_alias                  │
│  - coverage_subtype, coverage_condition                 │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│       문서/청크 계층 (Document & Chunk Layer)            │
│  - chunk (embedding + meta)                             │
│  - is_synthetic flag 포함                               │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│      Extraction/Evidence 계층                           │
│  - chunk_entity (모든 엔티티 추출 결과)                  │
│  - amount_entity (금액 전용 구조화)                      │
└─────────────────────────────────────────────────────────┘
```

---

## 테이블별 역할 요약

### 1. 기준/마스터 계층

#### `insurer`
- **역할**: 보험사 마스터 데이터
- **주요 컬럼**:
  - `insurer_code`: 보험사 고유 코드 (UNIQUE)
  - `insurer_name`: 보험사명
- **특징**: 보험사 추가 시 이 테이블만 INSERT

#### `product`
- **역할**: 보험 상품 마스터
- **주요 컬럼**:
  - `product_code`: 상품 코드 (보험사 내 UNIQUE)
  - `product_type`: 암보험, 건강보험 등
  - `sale_start_date`, `sale_end_date`: 판매 기간
- **관계**: `insurer` 1:N

#### `document`
- **역할**: 보험 문서 메타데이터
- **주요 컬럼**:
  - `document_type`: 약관/사업방법서/요약서/설계서
  - `doc_type_priority`: 문서 우선순위
    - 1 = 약관 (최우선)
    - 2 = 사업방법서
    - 3 = 상품요약서
    - 4 = 가입설계서
  - `file_path`, `file_hash`: 원본 파일 추적
- **관계**: `product` 1:N
- **특징**: 동일 상품의 여러 문서 버전 지원

#### `coverage_standard` ⭐
- **역할**: 신정원 통일 담보 코드 (CANONICAL)
- **주요 컬럼**:
  - `coverage_code`: **유일한 비교 기준 코드** (UNIQUE)
  - `coverage_name`: 표준 담보명
  - `domain`: 암/뇌/심혈관/상해 등
  - `coverage_type`: 진단/수술/입원/통원
  - `priority`: 도메인 내 우선순위 (메인담보=1)
  - `is_main`: 메인 담보 여부
- **특징**:
  - **Report-only**: 자동 INSERT 절대 금지
  - 모든 비교/검색은 이 코드 기준

---

### 2. 매핑/정규화 계층

#### `coverage_alias`
- **역할**: 보험사별 담보명 → 신정원 코드 매핑
- **주요 컬럼**:
  - `insurer_coverage_name`: "삼성화재 암진단금"
  - `coverage_code`: → `coverage_standard.coverage_code`
  - `confidence`: 매핑 신뢰도 (high/medium/low)
  - `mapping_method`: manual/rule/llm
- **관계**: `insurer` N:1, `coverage_standard` N:1
- **특징**: Ingestion 시 자동 INSERT 허용 (신뢰 기준 충족 시)

#### `coverage_code_alias`
- **역할**: 레거시/변형 코드 매핑
- **예시**: `"암진단_구"` → `"CA_DIAG_GENERAL"`
- **특징**: 과거 버전 코드 호환성 지원

#### `coverage_subtype`
- **역할**: 담보 세부 유형
- **예시**:
  - 암진단금 → {일반암, 유사암, 소액암, 경계성종양}
  - 뇌출혈 → {뇌출혈, 뇌경색}
- **특징**: 비교 시 subtype 레벨까지 일치 검증

#### `coverage_condition`
- **역할**: 지급 조건, 감액, 면책 조건
- **주요 컬럼**:
  - `condition_type`: 지급/감액/면책
  - `condition_rules`: JSONB 구조화 조건
- **특징**: 비교 결과에 조건 차이 표시 시 활용

---

### 3. 문서/청크 계층

#### `chunk`
- **역할**: 문서 분할 단위 (RAG 기본 단위)
- **주요 컬럼**:
  - `chunk_text`: 청크 본문
  - `embedding`: pgvector (1536d 등)
  - `is_synthetic`: 합성 청크 여부 ⭐
  - `synthetic_source_chunk_id`: 원본 청크 ID
  - `meta`: JSONB (synthetic_type, synthetic_method, entities 등)
- **관계**: `document` 1:N, 자기참조 (synthetic)

**Synthetic Chunk 규칙:**
```json
{
  "is_synthetic": true,
  "synthetic_type": "split",
  "synthetic_method": "v1_6_3_beta_2_split",
  "synthetic_source_chunk_id": 1234,
  "entities": {
    "coverage_code": "CA_DIAG_GENERAL",
    "amount": { ... }
  }
}
```

**필터 규칙:**
- Compare/Retrieval: `WHERE is_synthetic = false`
- Amount Bridge: `is_synthetic` 무관

---

### 4. Extraction/Evidence 계층

#### `chunk_entity`
- **역할**: 청크에서 추출한 모든 엔티티
- **주요 컬럼**:
  - `entity_type`: coverage/amount/disease/surgery 등
  - `coverage_code`: → `coverage_standard.coverage_code`
  - `entity_value`: JSONB (구조화된 엔티티 값)
  - `confidence`: 추출 신뢰도
- **관계**: `chunk` 1:N, `coverage_standard` N:1

#### `amount_entity` ⭐
- **역할**: 금액 전용 구조화 테이블
- **주요 컬럼**:
  - `coverage_code`: 담보 코드
  - `context_type`: payment/count/limit
  - `amount_value`: 숫자 (5000000)
  - `amount_text`: 원문 ("500만원")
  - `amount_unit`: 원/만원 등
  - `confidence`: 추출 신뢰도
- **특징**:
  - Amount Bridge 전용
  - Payment context vs Count context 명확히 분리
  - Synthetic chunk 포함 모든 chunk 대상

---

## 핵심 FK 관계 설명

### 1. 보험사 → 상품 → 문서 → 청크
```
insurer (1) ──> (N) product (1) ──> (N) document (1) ──> (N) chunk
```

### 2. 신정원 코드 중심 매핑
```
coverage_standard (1) ──> (N) coverage_alias
                     (1) ──> (N) coverage_code_alias
                     (1) ──> (N) coverage_subtype
                     (1) ──> (N) coverage_condition
```

### 3. 청크 → 엔티티 추출
```
chunk (1) ──> (N) chunk_entity
      (1) ──> (N) amount_entity
```

### 4. Synthetic Chunk 자기참조
```
chunk (original) ──spawns──> chunk (synthetic)
  ↑                              ↓
  └─────synthetic_source_chunk_id
```

---

## 데이터 흐름 (Ingestion → Retrieval → Compare)

### Ingestion 단계
1. `insurer`, `product`, `document` INSERT
2. PDF → `chunk` (원본만, is_synthetic=false)
3. LLM Extraction → `chunk_entity`, `amount_entity`
4. 담보명 인식 → `coverage_alias` 자동 INSERT (confidence ≥ medium)
5. Mixed coverage chunk 분해 → synthetic chunk 생성
   - `is_synthetic=true`
   - `synthetic_source_chunk_id` 설정

### Retrieval 단계
1. 사용자 질의 → domain 판별
2. `coverage_standard` 에서 대표 담보 선택
3. Vector search on `chunk` **WHERE is_synthetic=false**
4. 검색된 chunk → `chunk_entity` JOIN → coverage_code 확인

### Compare 단계
1. 선택된 coverage_code로 `chunk` 필터링 (is_synthetic=false)
2. `coverage_alias` 통해 보험사별 매핑 확인
3. `amount_entity` 에서 금액 증거 수집
   - **Synthetic chunk 포함** (Amount Bridge)
4. `coverage_condition` 통해 조건 차이 표시

---

## 인덱스 전략 (schema.sql 반영)

| 테이블 | 컬럼 | 인덱스 유형 | 이유 |
|--------|------|-------------|------|
| `chunk` | `embedding` | IVFFLAT/HNSW | Vector search 성능 |
| `chunk` | `document_id, is_synthetic` | B-tree | Retrieval 필터링 |
| `chunk_entity` | `coverage_code` | B-tree | Coverage 기반 검색 |
| `amount_entity` | `coverage_code, context_type` | B-tree | Amount Bridge |
| `coverage_alias` | `insurer_id, insurer_coverage_name` | B-tree | 담보명 → 코드 매핑 |
| `coverage_standard` | `coverage_code` | UNIQUE | PK 대체 가능 |
| `coverage_standard` | `domain, priority` | B-tree | Domain 기반 정렬 |

---

## Synthetic Chunk 특수 처리

### 생성 시점
- Ingestion 단계에서 Mixed coverage chunk 발견 시
- 원본 chunk는 유지, synthetic chunk 추가 생성

### DB 표현
```sql
-- 원본 chunk
INSERT INTO chunk (document_id, chunk_text, is_synthetic, meta)
VALUES (101, '암 500만원, 뇌출혈 300만원', false, '{}');
-- chunk_id = 1234

-- Synthetic chunk (암)
INSERT INTO chunk (document_id, chunk_text, is_synthetic, synthetic_source_chunk_id, meta)
VALUES (101, '암 500만원', true, 1234, '{
  "synthetic_type": "split",
  "synthetic_method": "v1_6_3_beta_2_split",
  "entities": {"coverage_code": "CA_DIAG_GENERAL"}
}');

-- Synthetic chunk (뇌출혈)
INSERT INTO chunk (document_id, chunk_text, is_synthetic, synthetic_source_chunk_id, meta)
VALUES (101, '뇌출혈 300만원', true, 1234, '{
  "synthetic_type": "split",
  "synthetic_method": "v1_6_3_beta_2_split",
  "entities": {"coverage_code": "CVD_HEMORRHAGE"}
}');
```

### 사용 제한
- ❌ Compare axis retrieval
- ❌ Policy axis retrieval
- ❌ Coverage recommendation
- ✅ Amount Bridge (금액 증거 수집)

---

## 확장성 보장

### 보험사 추가 시
1. `insurer` INSERT
2. `product`, `document`, `chunk` 추가
3. `coverage_alias` 자동 생성 (ingestion)
→ **스키마 변경 없음**

### 문서 유형 추가 시
1. `document.document_type` 새 값 사용
2. `doc_type_priority` 우선순위 설정
→ **스키마 변경 없음**

### 담보 추가 시
1. `coverage_standard` INSERT (수동)
2. `coverage_alias` 자동 생성 (ingestion)
→ **스키마 변경 없음**

---

## 요약

- **신정원 코드 중심**: 모든 비교는 `coverage_standard.coverage_code` 기준
- **Synthetic chunk 명확한 분리**: `is_synthetic` flag + meta 표준화
- **Amount Bridge 지원**: `amount_entity` + synthetic chunk 활용
- **확장성**: 보험사/문서/담보 추가 시 데이터만 추가, 스키마 불변
