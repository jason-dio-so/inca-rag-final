# Backfill & Idempotency 가이드

## 개요

Ingestion 파이프라인의 재실행, 증분 적재, Backfill 전략을 정의한다.

**핵심 원칙:**
1. **Idempotency**: 동일 입력 → 동일 결과
2. **최소 Backfill**: 필요한 데이터만 재생성
3. **추적 가능성**: 변경 이력 보존
4. **안전성**: Destructive 작업은 명시적 플래그 필요

---

## Idempotency 전략 (단계별)

### (A) Discover: file_hash 기반 동일성

**중복 방지 키:** `file_hash` (SHA-256)

```python
# Manifest 생성 시
existing_manifest = load_manifest("data/manifest/docs_manifest.csv")
existing_hashes = {row['file_hash']: row for row in existing_manifest}

for pdf_path in scan_pdfs("data/raw/"):
    file_hash = compute_file_hash(pdf_path)

    if file_hash in existing_hashes:
        # 동일 파일, 메타데이터 갱신
        update_manifest_row(file_hash, pdf_path)
    else:
        # 신규 파일, 추가
        add_manifest_row(file_hash, pdf_path)
```

**재실행 시:**
- 동일 `file_hash` → 기존 행 유지
- 파일명 변경 시 → `file_path` 갱신, `file_hash` 동일

---

### (B) Register: UNIQUE 제약 기반 upsert

**중복 방지 키:**
- `insurer.insurer_code` UNIQUE
- `product(insurer_id, product_code)` UNIQUE
- `document(product_id, document_type, file_hash)` UNIQUE

```sql
-- insurer: ON CONFLICT DO UPDATE
INSERT INTO insurer (insurer_code, insurer_name)
VALUES ('SAMSUNG', '삼성화재')
ON CONFLICT (insurer_code) DO UPDATE
SET insurer_name = EXCLUDED.insurer_name;

-- product: ON CONFLICT DO UPDATE
INSERT INTO product (insurer_id, product_code, product_name, ...)
VALUES (1, 'CANCER_PLUS_2024', '삼성화재 암플러스보험', ...)
ON CONFLICT (insurer_id, product_code) DO UPDATE
SET product_name = EXCLUDED.product_name, updated_at = NOW();

-- document: ON CONFLICT DO NOTHING (file_hash 동일하면 skip)
INSERT INTO document (product_id, document_type, file_path, file_hash, ...)
VALUES (10, '약관', 'data/raw/SAMSUNG/terms/cancer_plus.pdf', 'a3f5e8d9...', ...)
ON CONFLICT (product_id, document_type, file_hash) DO NOTHING;
```

**재실행 시:**
- 동일 `file_hash` → skip (idempotent)
- 파일 변경 시 (`file_hash` 다름) → 새 `document_id` 생성

---

### (C) Parse: file_hash 캐시

**중복 방지 키:** `file_hash`

```python
def parse_pdf_cached(file_path: str, file_hash: str) -> str:
    """캐시된 텍스트 반환, 없으면 파싱"""
    cache_path = f"data/derived/text/{file_hash}.txt"

    if os.path.exists(cache_path):
        logger.info(f"Using cached text for {file_hash}")
        return Path(cache_path).read_text(encoding='utf-8')

    # 파싱
    text = extract_text_from_pdf(file_path)
    Path(cache_path).write_text(text, encoding='utf-8')
    return text
```

**재실행 시:**
- 캐시 존재 → 재사용 (파싱 skip)
- 파싱 로직 변경 시 → 캐시 삭제 후 재실행

---

### (D) Chunk: (document_id, page_number, chunk_index)

**중복 방지 키 (권장):** `(document_id, page_number, chunk_index)`

```sql
-- 테이블 제약 추가 (권장)
ALTER TABLE chunk ADD CONSTRAINT uq_chunk_position
UNIQUE (document_id, page_number, chunk_index);

-- INSERT 시
INSERT INTO chunk (document_id, page_number, chunk_index, content, is_synthetic, ...)
VALUES (100, 1, 0, '텍스트...', false, ...)
ON CONFLICT (document_id, page_number, chunk_index) DO NOTHING;
```

**대안:** `content_hash` 기반 (application-level)
```python
content_hash = hashlib.sha256(chunk_text.encode()).hexdigest()[:16]

# DB 조회
existing = cur.execute("""
    SELECT chunk_id FROM chunk
    WHERE document_id = %s AND meta->>'content_hash' = %s
""", (document_id, content_hash)).fetchone()

if not existing:
    cur.execute("""
        INSERT INTO chunk (document_id, content, meta, ...)
        VALUES (%s, %s, %s::jsonb, ...)
    """, (document_id, chunk_text, {'content_hash': content_hash}, ...))
```

**재실행 시:**
- Chunking 규칙 변경 시 → `document_id` 기준 DELETE 후 재생성
- 동일 규칙 → UNIQUE 제약으로 skip

---

### (E) Embed: chunk_id 기반 NULL 체크

**중복 방지 키:** `chunk_id` (embedding IS NULL)

```sql
-- Embedding 미생성 청크만 처리
SELECT chunk_id, content
FROM chunk
WHERE embedding IS NULL;
```

```python
# Embedding 생성
for chunk_id, content in chunks:
    embedding = get_embedding(content)

    cur.execute("""
        UPDATE chunk SET embedding = %s::vector(1536)
        WHERE chunk_id = %s AND embedding IS NULL
    """, (embedding, chunk_id))
```

**재실행 시:**
- Embedding NULL → 재생성
- Embedding 존재 → skip

---

### (F) Extract: (chunk_id, entity_type, coverage_code)

**중복 방지 전략:**

**Option 1: DELETE 후 재생성** (권장)
```sql
-- 재실행 시 기존 entities 삭제
DELETE FROM chunk_entity WHERE chunk_id IN (SELECT chunk_id FROM chunk WHERE document_id = ?);
DELETE FROM amount_entity WHERE chunk_id IN (SELECT chunk_id FROM chunk WHERE document_id = ?);

-- 재추출
INSERT INTO chunk_entity (...) VALUES (...);
INSERT INTO amount_entity (...) VALUES (...);
```

**Option 2: UPSERT**
```sql
INSERT INTO chunk_entity (chunk_id, entity_type, coverage_code, entity_value, ...)
VALUES (?, ?, ?, ?, ...)
ON CONFLICT (chunk_id, entity_type, coverage_code) DO UPDATE
SET entity_value = EXCLUDED.entity_value, confidence = EXCLUDED.confidence;
```

**재실행 시:**
- Extraction 로직 변경 → document 단위 DELETE 후 재생성
- 동일 로직 → UPSERT로 중복 방지

---

### (G) Normalize: (insurer_id, insurer_coverage_name)

**중복 방지 키:** `(insurer_id, insurer_coverage_name)` UNIQUE

```sql
INSERT INTO coverage_alias (insurer_id, coverage_id, insurer_coverage_name, confidence, ...)
VALUES (1, 10, '암진단금', 'high', ...)
ON CONFLICT (insurer_id, insurer_coverage_name) DO UPDATE
SET coverage_id = EXCLUDED.coverage_id, confidence = EXCLUDED.confidence, updated_at = NOW();
```

**재실행 시:**
- 매핑 규칙 변경 → coverage_alias 전체 재생성 (또는 insurer별)
- 동일 규칙 → UPSERT로 최신 매핑 반영

---

### (H) Synthetic: (synthetic_source_chunk_id, coverage_code)

**중복 방지 전략:**

```python
# 기존 synthetic chunk 삭제
cur.execute("""
    DELETE FROM chunk
    WHERE is_synthetic = true
      AND synthetic_source_chunk_id IN (
        SELECT chunk_id FROM chunk WHERE document_id = ?
      )
""", (document_id,))

# 재생성
for source_chunk_id, coverage_code in mixed_chunks:
    synthetic_text = split_chunk_by_coverage(source_chunk_id, coverage_code)
    cur.execute("""
        INSERT INTO chunk (document_id, content, is_synthetic, synthetic_source_chunk_id, meta)
        VALUES (?, ?, true, ?, ?::jsonb)
    """, (document_id, synthetic_text, source_chunk_id, meta))
```

**재실행 시:**
- Synthetic 정책 변경 → document 단위 DELETE 후 재생성
- Meta normalization → UPDATE meta

---

## Backfill 시나리오 6종

### 1. 새 보험사 추가

**작업 흐름:**
```bash
# 1. 원본 파일 추가
cp -r /source/NEW_INSURER data/raw/

# 2. Discover (증분)
python -m tools.ingest.cli discover

# 3. Manifest 수동 보완 (insurer_name, product_code 등)
vim data/manifest/docs_manifest.csv

# 4. 전체 파이프라인 실행
python -m tools.ingest.cli run-all --insurers NEW_INSURER
```

**DB 영향:**
- `insurer` INSERT (신규)
- `product`, `document` INSERT (신규)
- 기존 데이터 영향 없음 (Idempotent)

---

### 2. 동일 보험사 신규 상품 추가

**작업 흐름:**
```bash
# 1. 원본 파일 추가
cp new_product.pdf data/raw/SAMSUNG/terms/

# 2. Discover
python -m tools.ingest.cli discover

# 3. Manifest 보완
# product_code, product_name 추가

# 4. 파이프라인 실행 (해당 상품만)
python -m tools.ingest.cli run-all --product SAMSUNG/NEW_PRODUCT
```

**DB 영향:**
- `product` INSERT (신규)
- `document`, `chunk`, ... INSERT (신규)
- 기존 SAMSUNG 상품 영향 없음

---

### 3. 동일 상품 문서 버전 추가

**작업 흐름:**
```bash
# 1. 신규 버전 PDF 추가
cp cancer_plus_v2.pdf data/raw/SAMSUNG/terms/

# 2. Discover
python -m tools.ingest.cli discover
# file_hash 변경 → 새 행 추가

# 3. Register
python -m tools.ingest.cli register
# document INSERT (file_hash 다름 → 새 document_id)

# 4. 나머지 파이프라인
python -m tools.ingest.cli run-all --document-id <new_document_id>
```

**DB 영향:**
- `document` INSERT (신규, file_hash 다름)
- 기존 v1 문서 유지
- `chunk`, `entities` 신규 생성 (document_id 별도)

**정리:**
- 구버전 삭제 필요 시 수동 DELETE
- `document.is_active=false` 설정 (권장)

---

### 4. 파서 개선으로 재파싱 필요

**작업 흐름:**
```bash
# 1. 파싱 캐시 삭제
rm -rf data/derived/SAMSUNG/text/*.txt

# 2. Parse 재실행
python -m tools.ingest.cli parse --insurer SAMSUNG

# 3. Chunk 재생성 (기존 삭제)
python -m tools.ingest.cli chunk --insurer SAMSUNG --force-recreate
```

**DB 영향:**
```sql
-- Chunk 삭제 (CASCADE로 entities도 삭제)
DELETE FROM chunk WHERE document_id IN (
    SELECT document_id FROM document d
    JOIN product p ON d.product_id = p.product_id
    WHERE p.insurer_id = (SELECT insurer_id FROM insurer WHERE insurer_code = 'SAMSUNG')
);

-- 재생성
-- Chunk, Embed, Extract 단계 재실행
```

**주의:** CASCADE DELETE로 `chunk_entity`, `amount_entity` 함께 삭제

---

### 5. Chunking 규칙 변경으로 재청킹

**작업 흐름:**
```bash
# 1. Chunk 삭제 (document 단위 또는 전체)
python -m tools.ingest.cli chunk --reset --document-id <id>

# 2. 재청킹
python -m tools.ingest.cli chunk --strategy new_strategy

# 3. Embed, Extract 재실행
python -m tools.ingest.cli embed
python -m tools.ingest.cli extract
```

**DB 영향:**
```sql
-- 특정 document의 chunk 삭제
DELETE FROM chunk WHERE document_id = ?;

-- 재생성
-- Chunk 단계부터 재실행
```

---

### 6. Synthetic 정책/메타 변경 (β-3 같은 normalization)

**시나리오:** `meta.synthetic_method` 를 `v1_6_3_beta_2_split` → `v1_6_3_beta_3_split` 로 변경

**작업 흐름:**

**Option 1: Meta UPDATE (비파괴)**
```sql
UPDATE chunk
SET meta = meta || '{"synthetic_method": "v1_6_3_beta_3_split"}'::jsonb
WHERE is_synthetic = true
  AND meta->>'synthetic_method' = 'v1_6_3_beta_2_split';
```

**Option 2: 재생성 (파괴)**
```bash
# 1. Synthetic chunk 삭제
python -m tools.ingest.cli synthetic --reset

# 2. 재생성
python -m tools.ingest.cli synthetic --method v1_6_3_beta_3_split
```

**DB 영향:**
```sql
-- 삭제
DELETE FROM chunk WHERE is_synthetic = true;

-- 재생성
-- Synthetic 단계 재실행
```

**권장:** Meta normalization은 UPDATE 사용 (재생성 불필요)

---

## 최소 Backfill 원칙

### 1. 가능한 한 DELETE 회피
- **UPDATE**: Meta 정보 변경, confidence 조정 등
- **INSERT ON CONFLICT**: UPSERT 활용
- **Soft Delete**: `is_active=false` 설정 (물리 삭제 지연)

### 2. 새 산출물 + 링크로 추적
```python
# ❌ 기존 chunk 삭제 후 재생성
DELETE FROM chunk WHERE document_id = ?;

# ✅ 새 버전 chunk 생성, 기존 유지
INSERT INTO chunk (document_id, content, meta)
VALUES (?, ?, '{"version": 2, "previous_chunk_id": 1234}'::jsonb);
```

### 3. Destructive 작업은 명시적 플래그
```bash
# ❌ 기본 동작으로 삭제 금지
python -m tools.ingest.cli chunk

# ✅ 명시적 플래그 필요
python -m tools.ingest.cli chunk --dangerously-reset
```

---

## 안전한 재실행 순서

### 전체 재실행 (보험사 단위)
```bash
# 1. 백업
pg_dump inca_rag_final > backup_$(date +%Y%m%d).sql

# 2. 삭제 (CASCADE)
DELETE FROM document WHERE product_id IN (
    SELECT product_id FROM product WHERE insurer_id = (
        SELECT insurer_id FROM insurer WHERE insurer_code = 'SAMSUNG'
    )
);

# 3. 파이프라인 재실행
python -m tools.ingest.cli run-all --insurer SAMSUNG
```

### 단계별 재실행 (document 단위)
```bash
# 1. 특정 단계 이후 삭제
DELETE FROM chunk WHERE document_id = 100;  # Chunk 이후 재실행

# 2. 해당 단계부터 재실행
python -m tools.ingest.cli chunk --document-id 100
python -m tools.ingest.cli embed --document-id 100
python -m tools.ingest.cli extract --document-id 100
```

---

## Artifacts 리포트 비교

### 재실행 전후 비교
```bash
# 1. 재실행 전 리포트
python -m tools.ingest.cli validate
# → artifacts/ingestion/20250123_1430/

# 2. Backfill 수행
python -m tools.ingest.cli chunk --insurer SAMSUNG --dangerously-reset
python -m tools.ingest.cli run-all --insurer SAMSUNG --start-from chunk

# 3. 재실행 후 리포트
python -m tools.ingest.cli validate
# → artifacts/ingestion/20250123_1630/

# 4. 비교
diff artifacts/ingestion/20250123_1430/summary.json \
     artifacts/ingestion/20250123_1630/summary.json
```

### 주요 비교 항목
| 항목 | Before | After | 판단 |
|------|--------|-------|------|
| 총 청크 수 | 10,000 | 10,200 | Chunking 규칙 변경 |
| UNMAPPED 건수 | 150 | 120 | 매핑 규칙 개선 |
| Synthetic 생성 수 | 500 | 520 | Mixed chunk 증가 |
| Amount context 분포 | payment: 70% | payment: 75% | 추출 정확도 향상 |

---

## Idempotency 검증 쿼리

### 1. 중복 document 확인
```sql
SELECT product_id, document_type, file_hash, COUNT(*)
FROM document
GROUP BY product_id, document_type, file_hash
HAVING COUNT(*) > 1;
-- 결과: 0 rows (정상)
```

### 2. 중복 chunk 확인 (content_hash 기준)
```sql
SELECT document_id, meta->>'content_hash', COUNT(*)
FROM chunk
WHERE meta ? 'content_hash'
GROUP BY document_id, meta->>'content_hash'
HAVING COUNT(*) > 1;
```

### 3. Synthetic chunk 정합성
```sql
-- source_chunk_id 유효성
SELECT c1.chunk_id, c1.synthetic_source_chunk_id
FROM chunk c1
LEFT JOIN chunk c2 ON c1.synthetic_source_chunk_id = c2.chunk_id
WHERE c1.is_synthetic = true AND c2.chunk_id IS NULL;
-- 결과: 0 rows (정상)
```

---

## 요약

| 시나리오 | 삭제 대상 | 재실행 단계 | Idempotency 보장 |
|---------|----------|------------|-----------------|
| 새 보험사 추가 | 없음 | Discover → Validate | UNIQUE 제약 |
| 신규 상품 추가 | 없음 | Discover → Validate | UNIQUE 제약 |
| 문서 버전 추가 | 없음 (file_hash 다름) | Register → Validate | UNIQUE (file_hash) |
| 파서 개선 | chunk (CASCADE) | Parse → Validate | file_hash 캐시 |
| Chunking 변경 | chunk (CASCADE) | Chunk → Validate | UNIQUE position 권장 |
| Synthetic 정책 변경 | chunk (is_synthetic=true) | Synthetic → Validate | DELETE 후 재생성 |

**핵심 원칙:**
- 최소 범위 Backfill (document/insurer 단위)
- Destructive 작업은 `--dangerously-reset` 필수
- 재실행 전 백업 필수
- Artifacts 리포트로 변경 검증
