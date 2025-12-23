# Ingestion 설계 문서

## 개요

inca-RAG-final 프로젝트의 Ingestion 파이프라인 전체 설계 문서 모음입니다.

**목적:**
- 보험사 원본 PDF → 신정원 통일 담보 코드 기반 DB 스키마 변환
- 재현 가능하고, 확장 가능하며, 안전한 데이터 처리 파이프라인 구축

---

## 문서 목록

### 1. [overview.md](./overview.md) - 전체 개요
**내용:**
- Ingestion 파이프라인 9단계 (A~I) 소개
- 신정원 통일 담보 코드 정합 강제 원칙
- Synthetic chunk 정책
- 검증 & 리포트 전략

**대상 독자:** 전체 아키텍처 이해 필요한 개발자/운영자

---

### 2. [data_layout.md](./data_layout.md) - 데이터 레이아웃
**내용:**
- 디렉토리 구조 (`data/raw/`, `data/derived/`, `artifacts/`)
- 보험사 코드 표준 (SAMSUNG, HYUNDAI 등)
- 문서 타입 디렉토리 (terms, business, summary, proposal)
- 파일 명명 규칙 및 `file_hash` 산출

**대상 독자:** 데이터 관리자, 파일 시스템 설계자

---

### 3. [manifest_spec.md](./manifest_spec.md) - Manifest 스펙
**내용:**
- `docs_manifest.csv` 형식 정의
- 필수 컬럼 9개 (insurer_code ~ file_hash)
- 생성 방법 (Discover 단계 자동 생성 + 수동 보완)
- 검증 규칙 (필수 컬럼, 파일 존재, hash 형식)

**대상 독자:** Ingestion 담당 개발자

---

### 4. [pipeline.md](./pipeline.md) - 파이프라인 상세 설계
**내용:**
- 9단계 (Discover/Register/Parse/Chunk/Embed/Extract/Normalize/Synthetic/Validate) 정의
- 단계별 입출력/핵심 로직/실패 정책/Idempotency 키
- DB 테이블별 I/O 요약
- CLI Subcommand 매핑
- Synthetic chunk 생성 정책 (확정)

**대상 독자:** Ingestion 파이프라인 구현 개발자

---

### 5. [error_policy.md](./error_policy.md) - 오류 처리 정책
**내용:**
- 에러 등급 (FATAL/ERROR/WARN/INFO)
- 실패 케이스 대응표 (15개 필수 케이스)
- 금지 사항 (coverage_standard 자동 INSERT 금지 등)
- 에러 로그 형식 및 재실행 시 처리

**대상 독자:** Ingestion 파이프라인 구현/운영 담당자

---

### 6. [backfill_and_idempotency.md](./backfill_and_idempotency.md) - Backfill & Idempotency
**내용:**
- 단계별 Idempotency 전략 (UNIQUE 제약, 캐시, UPSERT)
- Backfill 시나리오 6종 (새 보험사 추가, 문서 버전 추가, 파서 개선 등)
- 최소 Backfill 원칙
- 안전한 재실행 순서 및 리포트 비교 방법

**대상 독자:** 운영 담당자, Backfill 작업 수행자

---

## 설계 핵심 원칙

### 1. 신정원 통일 담보 코드 정합
- `coverage_standard` 테이블은 **Report-only**
- Ingestion이 자동 INSERT/UPDATE 절대 금지
- 모든 담보 코드는 `coverage_standard.coverage_code` FK 기준
- 매핑 실패 시 UNMAPPED 리포트, 억지 매핑 금지

### 2. 원본 데이터 불변성
- `data/raw/` 디렉토리는 읽기 전용
- 원본 PDF 내용 변형 금지
- `file_hash` 기반 추적 (파일명 변경 허용)

### 3. Synthetic Chunk 정책
- **생성 대상 문서**: 가입설계서/상품요약서/사업방법서
- **생성 조건**: 1개 청크에 2개 이상 담보 포함
- **필수 필드**:
  - `is_synthetic=true`
  - `synthetic_source_chunk_id` NOT NULL
  - `meta.synthetic_type="split"`
  - `meta.synthetic_method="v1_6_3_beta_2_split"`
- **사용 제한**:
  - ❌ Compare/Retrieval axis (`WHERE is_synthetic=false`)
  - ✅ Amount Bridge (is_synthetic 무관)

### 4. Idempotency
- 동일 입력 → 동일 결과 보장
- UNIQUE 제약 3종:
  - `product(insurer_id, product_code)`
  - `document(product_id, document_type, file_hash)`
  - `coverage_alias(insurer_id, insurer_coverage_name)`
- 재실행 시 중복 방지 (ON CONFLICT DO NOTHING/UPDATE)

### 5. 최소 Backfill
- 가능한 한 DELETE 회피 (UPDATE/UPSERT 우선)
- Destructive 작업은 `--dangerously-reset` 플래그 필요
- 재실행 전 백업 필수

---

## 파이프라인 흐름도

```
┌─────────────┐
│  (A) Discover  │  data/raw/ 스캔 → manifest.csv 생성
└──────┬──────┘
       ▼
┌─────────────┐
│  (B) Register  │  insurer/product/document DB 등록
└──────┬──────┘
       ▼
┌─────────────┐
│   (C) Parse    │  PDF → text 추출
└──────┬──────┘
       ▼
┌─────────────┐
│   (D) Chunk    │  청크 생성 (is_synthetic=false)
└──────┬──────┘
       ▼
┌─────────────┐
│   (E) Embed    │  Embedding 생성 (vector)
└──────┬──────┘
       ▼
┌─────────────┐
│  (F) Extract   │  Entity 추출 (LLM)
└──────┬──────┘
       ▼
┌─────────────┐
│ (G) Normalize  │  담보 매핑 (coverage_alias)
└──────┬──────┘
       ▼
┌─────────────┐
│ (H) Synthetic  │  Mixed chunk 분해 (Amount Bridge 전용)
└──────┬──────┘
       ▼
┌─────────────┐
│ (I) Validate   │  검증 + 리포트 생성
└─────────────┘
```

---

## CLI 사용 예시

### 전체 파이프라인 실행
```bash
python -m tools.ingest.cli run-all
```

### 단계별 실행
```bash
# 1. 파일 스캔
python -m tools.ingest.cli discover

# 2. DB 메타데이터 등록
python -m tools.ingest.cli register

# 3. PDF 파싱
python -m tools.ingest.cli parse --doc-type terms

# 4. 청킹
python -m tools.ingest.cli chunk --strategy semantic

# 5. 임베딩
python -m tools.ingest.cli embed --batch-size 100

# 6. 엔티티 추출
python -m tools.ingest.cli extract --model gpt-4o

# 7. 담보 매핑
python -m tools.ingest.cli normalize

# 8. Synthetic chunk 생성
python -m tools.ingest.cli synthetic --doc-types proposal,summary

# 9. 검증
python -m tools.ingest.cli validate
```

### 보험사별 실행
```bash
python -m tools.ingest.cli run-all --insurer SAMSUNG
```

### Backfill (재실행)
```bash
# 특정 문서 재청킹
python -m tools.ingest.cli chunk --document-id 100 --dangerously-reset

# 보험사 전체 재실행
python -m tools.ingest.cli run-all --insurer SAMSUNG --dangerously-reset
```

---

## 금지 사항 (전체)

1. ❌ `coverage_standard` 자동 INSERT/UPDATE
2. ❌ `meta` JSONB로 필터링 (컬럼 기준만 허용)
3. ❌ 원본 PDF 내용 변형/재저장
4. ❌ 하드코딩 (보험사별 rule 확장 포인트 필수)
5. ❌ Synthetic chunk를 비교 축에 사용

---

## 검증 & 리포트

### 리포트 위치
```
artifacts/ingestion/<YYYYMMDD_HHMM>/
├── summary.json                      # 전체 통계
├── unmapped_coverages.csv            # UNMAPPED 담보 목록
├── synthetic_stats.json              # Synthetic chunk 통계
├── amount_context_distribution.json  # Amount context 분포
└── validation_errors.log             # 검증 오류
```

### 필수 검증 쿼리
```sql
-- 1. coverage_alias FK 위반
SELECT ca.insurer_coverage_name FROM coverage_alias ca
LEFT JOIN coverage_standard cs ON ca.coverage_id = cs.coverage_id
WHERE cs.coverage_id IS NULL;

-- 2. chunk_entity 미매핑 코드
SELECT DISTINCT ce.coverage_code FROM chunk_entity ce
LEFT JOIN coverage_standard cs ON ce.coverage_code = cs.coverage_code
WHERE ce.coverage_code IS NOT NULL AND cs.coverage_code IS NULL;

-- 3. Synthetic chunk 정책 위반
SELECT chunk_id FROM chunk
WHERE is_synthetic = true AND synthetic_source_chunk_id IS NULL;
```

---

## 다음 단계

Ingestion 설계 완료 후:
1. **STEP 4**: Backend API 설계 (Compare/Retrieval/Amount Bridge)
2. **STEP 5**: Frontend UI 설계
3. **STEP 6**: 구현 및 테스트

---

## 문서 버전

- **v1.0** (2025-01-23): 초기 설계 완료
- 변경 이력은 Git commit 참조

---

## 참조

- [DB 스키마 설계](../db/schema.sql)
- [ERD](../db/erd.md)
- [설계 의사결정](../db/design_decisions.md)
