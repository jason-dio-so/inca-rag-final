# STEP 4-Validate 검증 보고서 (Fix + Re-validation)

**날짜**: 2025-12-23
**검증자**: Claude (Automated)
**판정**: ✅ **PASSED**

---

## 수정 사항 (Fix Applied)

### Fix 1: Schema - content_hash 컬럼 추가
**파일**: `docs/db/schema_v2_additions.sql`

```sql
-- Add content_hash column for idempotency
ALTER TABLE chunk ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);

-- Add UNIQUE constraint
ALTER TABLE chunk ADD CONSTRAINT chunk_unique_hash
    UNIQUE (document_id, page_number, content_hash);
```

### Fix 2: Code - content_hash 계산 및 사용
**파일**: `apps/ingestion/chunk/chunker.py`

- `Chunk.__init__`: content_hash 자동 계산 (SHA-256)
- `insert_chunk`: ON CONFLICT (document_id, page_number, content_hash) DO NOTHING

### Fix 3: Real PDF 생성
**파일**: `tools/make_sample_pdf.py` (신규)

- Minimal valid PDF structure 생성
- PyMuPDF로 읽기 가능한 형식

---

## 검증 환경

- 작업 루트: `/Users/cheollee/inca-RAG-final`
- DB: PostgreSQL 16 + pgvector (Docker)
- Schema: schema.sql + schema_v2_additions.sql (content_hash 추가)
- coverage_standard 초기 상태: 0 rows
- Sample PDF: Real PDF (1 page, 569 bytes)

---

## 시나리오 실행 결과

### Scenario A: Full Pipeline 1회 실행
- **결과**: ✅ PASS
- **실행 명령**: `python -m apps.ingestion.cli_v2 run-all --manifest data/manifest/docs_manifest_sample.csv`
- **로그**: `/tmp/ingestion_run1_fixed.log`
- **결과**:
  - Parse: ✅ 성공 (Real PDF)
  - Chunk: ✅ 1 chunk 생성
  - Embed/Extract: ⚠️ Skip (API key 없음, 정상)
  - Normalize: ⚠️ Skip (coverage_standard 비어있음, 정상)

### Scenario B: DB 상태 검증
- **결과**: ✅ PASS
- **검증 시각**: 1회 실행 직후

| 테이블 | Count | 기대값 | 판정 |
|--------|-------|--------|------|
| coverage_standard | 0 | 0 | ✅ |
| chunk | 1 | 1 | ✅ |
| insurer | 1 | 1 | ✅ |
| product | 1 | 1 | ✅ |
| document | 1 | 1 | ✅ |

### Scenario C: Synthetic 정책 검증
- **결과**: ✅ PASS
- **검증 쿼리 결과**:
  - synthetic_without_source: 0 ✅
  - non_synthetic_with_source: 0 ✅

### Scenario D: Idempotency 검증 (2회차 실행) ⭐ **핵심 검증**
- **결과**: ✅ **PASS**
- **실행 명령**: `python -m apps.ingestion.cli_v2 run-all --manifest data/manifest/docs_manifest_sample.csv` (2nd run)
- **Row count 비교**:

| 테이블 | 1회차 | 2회차 | 기대값 | 판정 |
|--------|-------|-------|--------|------|
| insurer | 1 | 1 | 1 | ✅ |
| product | 1 | 1 | 1 | ✅ |
| document | 1 | 1 | 1 | ✅ |
| **chunk** | **1** | **1** | **1** | ✅ **PASS** |

- **중복 검증**:
```sql
SELECT document_id, page_number, content_hash, COUNT(*)
FROM chunk
GROUP BY document_id, page_number, content_hash
HAVING COUNT(*) > 1;
-- Result: 0 rows (no duplicates) ✅
```

### Scenario E: Validate 리포트 검증
- **결과**: ✅ PASS
- **리포트 경로**: `/Users/cheollee/inca-RAG-final/artifacts/ingestion/20251223_181913/`
- **파일 확인**:
  - `summary.json`: ✅ 존재
- **리포트 내용**:
```json
{
  "timestamp": "20251223_181913",
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
| ✅ coverage_standard 자동 INSERT 없음 | **YES** | coverage_standard count = 0 (불변) |
| ✅ FK 위반 발생 시 즉시 실패 | **YES** | FK 제약 존재 (schema.sql) |
| ✅ Synthetic chunk는 Amount Bridge 전용 | **YES** | 코드 분석 확인 |
| ✅ 필터링은 is_synthetic 컬럼만 사용 | **YES** | JSONB 필터링 없음 |
| ✅ meta JSONB 기반 필터링 없음 | **YES** | validator.py 검증 |
| ✅ **재실행 시 데이터 증가 없음** | **YES** | **chunk: 1 (1회) → 1 (2회) ✅** |

---

## 최종 판정

### ✅ STEP 4-Validate: **통과 (PASSED)**

**통과 근거**:
- ✅ Idempotency 요구사항 달성 (DoD 필수 조건)
- ✅ chunk 테이블 중복 방지 (UNIQUE constraint)
- ✅ ON CONFLICT 정상 작동
- ✅ coverage_standard 불변
- ✅ Synthetic 정책 준수
- ✅ Parse 단계 정상화 (Real PDF)

---

## DoD (Definition of Done) 체크리스트

- ✅ Full pipeline 실행 1회 성공
- ✅ **동일 입력 2회 실행 시 idempotent** → **달성** ⭐
- ✅ coverage_standard = 0 유지
- ✅ Synthetic 정책 위반 0건
- ✅ Validate 리포트 생성 확인
- ✅ Git 커밋 & push

---

## 수정 방식 분석

### 왜 UNIQUE constraint가 효과적인가?

#### Before (실패):
```python
# ON CONFLICT DO NOTHING (but no UNIQUE constraint)
# → Conflict never detected → Always INSERT → Duplicates
```

#### After (성공):
```sql
-- Schema
ALTER TABLE chunk ADD CONSTRAINT chunk_unique_hash
    UNIQUE (document_id, page_number, content_hash);

-- Code
INSERT INTO chunk (..., content_hash, ...)
VALUES (..., SHA256(content), ...)
ON CONFLICT (document_id, page_number, content_hash) DO NOTHING;
```

**동작 방식**:
1. 2회차 실행 시 동일한 content → 동일한 content_hash
2. UNIQUE constraint가 conflict 감지
3. ON CONFLICT DO NOTHING 실행 → INSERT 생략
4. 기존 chunk_id 조회 → 반환

**헌법 준수**:
- ✅ DB가 중복 방지 강제 (코드가 아님)
- ✅ 병렬 실행에도 안전 (UNIQUE constraint)
- ✅ 재실행에도 안전 (Idempotent)

---

## 성능 영향 분석

### Index 추가:
```sql
-- UNIQUE constraint automatically creates index
CREATE UNIQUE INDEX chunk_unique_hash ON chunk (document_id, page_number, content_hash);
```

**영향**:
- ✅ INSERT 시 중복 검사 (O(log n), B-tree)
- ✅ SELECT 성능 향상 (content_hash 기반 조회)
- ⚠️ 추가 저장 공간 (64 bytes per chunk)

**트레이드오프**: Acceptable (Idempotency가 우선)

---

## 다음 조치

1. ✅ STEP 4 완료 선언
2. ⏸️ STEP 5 진행 가능 (DoD 달성)

---

## 교훈 (Lessons Learned)

### 1. "헌법은 DB가 강제한다"
코드에서 SELECT로 중복을 막는 것은 불충분하다.
UNIQUE constraint + ON CONFLICT가 진정한 idempotency 보장.

### 2. Hash 기반 UNIQUE가 Content UNIQUE보다 우수
- content가 길면 UNIQUE constraint 비효율
- Hash (64 bytes)는 일정 크기 + 빠른 비교

### 3. ADD-ONLY 원칙 유지 가능
`schema_v2_additions.sql`에 ALTER TABLE로 추가 → 기존 v1 호환 유지

---

**작성 시각**: 2025-12-23 18:20
**판정**: ✅ STEP 4-Validate PASSED
**다음 단계**: STEP 5 진행 가능
