# Ingestion 설계 개요

## 목적

inca-RAG-final 프로젝트의 Ingestion 파이프라인은 보험사 원본 문서(PDF)를 신정원 통일 담보 코드 기반 DB 스키마로 변환하는 전체 프로세스를 정의한다.

**핵심 원칙:**
1. **신정원 통일 담보 코드(`coverage_standard`)가 유일한 기준**
2. **원본 데이터 불변성**: PDF 내용 변경 금지, `file_hash` 기반 추적
3. **Synthetic chunk는 Amount Bridge 전용**, 비교 축 제외
4. **재실행 가능성(Idempotency)**: 동일 입력에 동일 결과 보장

---

## Ingestion 파이프라인 9단계

```
┌─────────────────────────────────────────────────────────────┐
│ (A) Discover: 파일 스캔 + file_hash 산출                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ (B) Register: insurer/product/document upsert               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ (C) Parse: PDF→text/pages (문서 타입별 전략)                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ (D) Chunk: 청크 생성 (원본만, is_synthetic=false)           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ (E) Embed: embedding 생성 (chunk.embedding)                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ (F) Extract: chunk_entity, amount_entity 추출               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ (G) Normalize: 담보명→신정원 코드 매핑 (coverage_alias)     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ (H) Synthetic: Mixed coverage chunk 분해 (정책 준수)        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ (I) Validate: 정합성 체크 + 리포트 생성                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 데이터 흐름 요약

| 단계 | 입력 | 출력 | 실패 정책 |
|------|------|------|-----------|
| Discover | `data/raw/**/*.pdf` | `manifest.csv` | Skip 불가 파일 |
| Register | `manifest.csv` | `insurer`, `product`, `document` | UNIQUE 위반 시 skip |
| Parse | PDF 파일 | `data/derived/{insurer}/text/*.txt` | 파싱 실패 시 flag |
| Chunk | Text | `chunk` (is_synthetic=false) | 계속 진행 |
| Embed | `chunk.content` | `chunk.embedding` | 재시도 후 null 허용 |
| Extract | `chunk.content` | `chunk_entity`, `amount_entity` | 계속 진행 |
| Normalize | `chunk_entity` | `coverage_alias` | Unmapped 리포트 |
| Synthetic | `chunk` (mixed) | `chunk` (is_synthetic=true) | 생성 실패 시 원본 유지 |
| Validate | All tables | Reports | 검증만, 롤백 없음 |

---

## 신정원 통일 담보 코드 정합 강제

### 절대 규칙
- `coverage_standard` 테이블은 **Report-only**
- Ingestion이 자동 INSERT 절대 금지
- 모든 담보 코드는 `coverage_standard.coverage_code` FK 기준

### coverage_alias 자동 생성 정책
```python
# ✅ 허용
if coverage_code in coverage_standard:
    INSERT INTO coverage_alias (insurer_id, coverage_id, insurer_coverage_name, confidence)

# ❌ 금지
if coverage_name not in coverage_standard:
    INSERT INTO coverage_standard (coverage_code, coverage_name)  # 절대 금지
```

### Unmapped 처리
- 매핑 실패 시: **UNMAPPED 리포트**로 기록
- 억지 매핑 금지
- 인간 검토 후 `coverage_standard` 수동 추가 → 재실행

---

## Synthetic Chunk 정책

### 생성 조건
- **Mixed coverage chunk** 발견 시 (1개 청크에 2개 이상 담보)
- 문서 타입: 가입설계서/상품요약서/사업방법서

### 생성 규칙
```python
# 원본 chunk 유지
original_chunk = {
    "chunk_id": 1234,
    "content": "암 500만원, 뇌출혈 300만원",
    "is_synthetic": False,
    "meta": {}
}

# Synthetic chunk 생성
synthetic_chunks = [
    {
        "content": "암 500만원",
        "is_synthetic": True,
        "synthetic_source_chunk_id": 1234,
        "meta": {
            "synthetic_type": "split",
            "synthetic_method": "v1_6_3_beta_2_split",
            "entities": {"coverage_code": "CA_DIAG_GENERAL"}
        }
    },
    {
        "content": "뇌출혈 300만원",
        "is_synthetic": True,
        "synthetic_source_chunk_id": 1234,
        "meta": {
            "synthetic_type": "split",
            "synthetic_method": "v1_6_3_beta_2_split",
            "entities": {"coverage_code": "CVD_HEMORRHAGE"}
        }
    }
]
```

### 사용 제한
- ❌ **Compare/Retrieval axis**: `WHERE is_synthetic = false`
- ✅ **Amount Bridge**: `is_synthetic` 무관

---

## 검증 & 리포트

### 출력 위치
```
artifacts/ingestion/<YYYYMMDD_HHMM>/
├── summary.json
├── unmapped_coverages.csv
├── synthetic_stats.json
├── amount_context_distribution.json
└── validation_errors.log
```

### 필수 리포트
1. **문서 통계**: 보험사×문서타입별 문서/페이지/청크 수
2. **매핑 성공률**: 보험사별 coverage_alias 매핑률
3. **Unmapped 목록**: 빈도 높은 순 top 100
4. **Synthetic 통계**: 생성 수, reject_reason 분포
5. **Amount context 분포**: payment/count/limit 비율

---

## 금지 사항

1. ❌ `coverage_standard` 자동 INSERT/UPDATE
2. ❌ `meta` JSONB로 필터링 (컬럼 기준만 허용)
3. ❌ 원본 PDF 내용 변형/재저장
4. ❌ 하드코딩 (보험사별 rule 확장 포인트 필수)
5. ❌ Synthetic chunk를 비교 축에 사용

---

## 재실행 가능성 (Idempotency)

### 중복 방지 키
- `document`: UNIQUE(product_id, document_type, file_hash)
- `chunk`: document_id + content hash (또는 page_number + offset)
- `coverage_alias`: UNIQUE(insurer_id, insurer_coverage_name)

### 재실행 시나리오
1. **전체 재실행**: 기존 데이터 유지, 신규만 추가
2. **특정 보험사 재실행**: `WHERE insurer_id = ?` DELETE 후 재생성
3. **특정 문서 재실행**: `file_hash` 기준 document_id 찾아 CASCADE DELETE

---

## 다음 문서

- [데이터 레이아웃](./data_layout.md) - 디렉토리 구조 및 파일 명명 규칙
- [Manifest 스펙](./manifest_spec.md) - docs_manifest.csv 형식 정의
- [파이프라인 상세](./pipeline.md) - 9단계별 입출력/로직 설명
- [오류 정책](./error_policy.md) - 단계별 실패 처리 전략
- [Backfill & Idempotency](./backfill_and_idempotency.md) - 재실행 상세 가이드
