# STEP 4-Validate 검증 보고서

**날짜**: 2025-12-23
**검증자**: Claude (Automated)
**판정**: ❌ **FAILED**

---

## 검증 환경

- 작업 루트: `/Users/cheollee/inca-RAG-final`
- DB: PostgreSQL 16 + pgvector (Docker)
- Schema: schema.sql + schema_v2_additions.sql (13 tables)
- coverage_standard 초기 상태: 0 rows

---

## 시나리오 실행 결과

### Scenario A: Full Pipeline 1회 실행
- **결과**: ⚠️ PARTIAL PASS
- **실행 명령**: `python -m apps.ingestion.cli_v2 run-all --manifest data/manifest/docs_manifest_sample.csv`
- **로그**: `/tmp/ingestion_run1.log`
- **발견 사항**:
  - Parse 단계: sample.pdf가 실제 PDF 아님 (ASCII text)
  - Workaround: derived/document_1.json 수동 생성
  - Chunk 단계: 정상 실행 (1 chunk 생성)
  - Embed/Extract: OpenAI API 키 없음 (정상 skip)
  - Normalize: coverage_standard 비어있음 (정상 skip)

### Scenario B: DB 상태 검증
- **결과**: ✅ PASS
- **검증 시각**: 1회 실행 직후

| 테이블 | Count | 기대값 | 판정 |
|--------|-------|--------|------|
| coverage_standard | 0 | 0 | ✅ |
| coverage_alias | 0 | 0 | ✅ |
| chunk | 1 | 1 | ✅ |
| amount_entity | 0 | 0 | ✅ |
| insurer | 1 | 1 | ✅ |
| product | 1 | 1 | ✅ |
| document | 1 | 1 | ✅ |

### Scenario C: Synthetic 정책 검증
- **결과**: ✅ PASS
- **검증 쿼리**:
```sql
SELECT
    'synthetic_without_source' as violation_type,
    COUNT(*) as count
FROM chunk
WHERE is_synthetic = true AND synthetic_source_chunk_id IS NULL
UNION ALL
SELECT
    'non_synthetic_with_source',
    COUNT(*)
FROM chunk
WHERE is_synthetic = false AND synthetic_source_chunk_id IS NOT NULL;
```
- **결과**:
  - synthetic_without_source: 0 ✅
  - non_synthetic_with_source: 0 ✅

### Scenario D: Idempotency 검증 (2회차 실행)
- **결과**: ❌ **FAIL (치명적)**
- **실행 명령**: `python -m apps.ingestion.cli_v2 chunk` (2nd run)
- **Row count 비교**:

| 테이블 | 1회차 | 2회차 | 기대값 | 판정 |
|--------|-------|-------|--------|------|
| insurer | 1 | 1 | 1 | ✅ |
| product | 1 | 1 | 1 | ✅ |
| document | 1 | 1 | 1 | ✅ |
| **chunk** | **1** | **2** | **1** | ❌ **FAIL** |

- **문제**: 동일한 content를 가진 chunk가 중복 생성됨

```
chunk_id | document_id | page_number | content_preview | is_synthetic
---------|-------------|-------------|-----------------|-------------
1        | 1           | 1           | 삼성 암플러스... | false
2        | 1           | 1           | 삼성 암플러스... | false
```

- **근본 원인**:
  - `schema.sql`의 `chunk` 테이블에 UNIQUE 제약 없음
  - `chunker.py`의 `ON CONFLICT DO NOTHING`이 작동하지 않음

### Scenario E: Validate 리포트 검증
- **결과**: ✅ PASS
- **리포트 경로**: `/Users/cheollee/inca-RAG-final/artifacts/ingestion/20251223_180450/`
- **파일 확인**:
  - `summary.json`: ✅ 존재
  - `unmapped_coverages.csv`: N/A (unmapped 없음)
- **리포트 내용**:
```json
{
  "timestamp": "20251223_180450",
  "document_stats": [...],
  "chunk_stats": {
    "original_chunks": 1,
    "synthetic_chunks": 0,
    "total_chunks": 1
  },
  "coverage_standard_violations": {
    "chunk_entity_invalid_codes": 0,
    "amount_entity_invalid_codes": 0,
    "coverage_alias_invalid_ids": 0
  },
  "synthetic_policy_violations": {
    "synthetic_without_source": 0,
    "non_synthetic_with_source": 0
  },
  "critical_violations": [],
  "validation_passed": true
}
```

---

## 운영 헌법 강제 확인 (Constitutional Checklist)

| 항목 | 판정 | 증거 |
|------|------|-----|
| coverage_standard 자동 INSERT 없음 | ✅ YES | coverage_standard count = 0 (불변) |
| FK 위반 발생 시 즉시 실패 | ✅ YES | FK 제약 존재 (schema.sql) |
| Synthetic chunk는 Amount Bridge 전용 | ✅ YES | 코드 분석 확인 |
| 필터링은 is_synthetic 컬럼만 사용 | ✅ YES | JSONB 필터링 없음 |
| meta JSONB 기반 필터링 없음 | ✅ YES | validator.py 검증 |
| **재실행 시 데이터 증가 없음** | ❌ **NO** | **chunk: 1 → 2 (실패)** |

---

## 최종 판정

### ❌ STEP 4-Validate: **실패 (FAILED)**

**실패 근거**:
- Idempotency 요구사항 미달성 (DoD 필수 조건)
- chunk 테이블 중복 INSERT 발생

### 수정 필요사항

#### 옵션 1: 스키마 수정 (권장)
`docs/db/schema.sql` 수정:

```sql
-- chunk 테이블에 UNIQUE 제약 추가
ALTER TABLE chunk ADD CONSTRAINT chunk_unique_content
    UNIQUE (document_id, page_number, content);
```

또는 content가 큰 경우:

```sql
-- Hash 기반 UNIQUE
ALTER TABLE chunk ADD COLUMN content_hash VARCHAR(64);
CREATE INDEX idx_chunk_content_hash ON chunk(content_hash);
ALTER TABLE chunk ADD CONSTRAINT chunk_unique_hash
    UNIQUE (document_id, page_number, content_hash);
```

#### 옵션 2: 코드 수정
`apps/ingestion/chunk/chunker.py`:

```python
def insert_chunk(conn: PGConnection, chunk: Chunk) -> int:
    """
    Insert chunk with explicit duplicate check.
    """
    # Check if chunk already exists
    with conn.cursor() as cur:
        cur.execute("""
            SELECT chunk_id FROM chunk
            WHERE document_id = %s
              AND page_number = %s
              AND content = %s
            LIMIT 1
        """, (chunk.document_id, chunk.page_number, chunk.content))

        existing = cur.fetchone()
        if existing:
            return existing[0]  # Return existing chunk_id

        # Insert new chunk
        cur.execute("""
            INSERT INTO chunk (...)
            VALUES (...)
            RETURNING chunk_id
        """, (...))
        return cur.fetchone()[0]
```

---

## 다음 조치

1. ✅ Idempotency 문제 해결 (스키마 또는 코드 수정)
2. ⏸️ STEP 4-Validate 재실행
3. ⏸️ 모든 DoD 조건 충족 확인
4. ⏸️ STEP 4 완료 선언
5. ❌ STEP 5 진행 금지 (DoD 미달성)

---

## 부록: 발견된 부수적 이슈

### 1. sample.pdf가 실제 PDF 아님
- **위치**: `data/raw/SAMSUNG/약관/sample.pdf`
- **실제 타입**: ASCII text
- **영향**: Parse 단계 실패
- **Workaround**: derived/document_1.json 수동 생성
- **권장 해결**: 실제 PDF 샘플 파일 준비

### 2. PyMuPDF (fitz) 의존성
- **영향**: Parse 단계 필수
- **해결**: `pip install PyMuPDF` 또는 대체 파서 구현

---

**작성 시각**: 2025-12-23 18:06
**다음 검증 예정**: Idempotency 수정 후 재실행
