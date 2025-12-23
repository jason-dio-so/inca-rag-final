# Ingestion 파이프라인 상세 설계

## 개요

Ingestion 파이프라인은 9단계(A~I)로 구성되며, 각 단계는 명확한 입출력과 실패 정책을 갖는다.

**실행 순서:** Discover → Register → Parse → Chunk → Embed → Extract → Normalize → Synthetic → Validate

---

## 파이프라인 단계 정의

### (A) Discover: 파일 스캔 + file_hash 산출

| 항목 | 내용 |
|------|------|
| **목적** | `data/raw/` 디렉토리 스캔, 원본 PDF 목록 및 `file_hash` 산출 |
| **입력** | `data/raw/**/*.pdf` |
| **출력** | `data/manifest/docs_manifest.csv` |
| **핵심 로직** | 1. 디렉토리 재귀 스캔<br>2. SHA-256 해시 계산<br>3. Manifest CSV 생성 |
| **실패 시 처리** | FATAL - 파일 권한/해시 산출 실패 시 즉시 중단 |
| **Idempotency 키** | `file_hash` (동일 파일 재스캔 시 덮어쓰기) |

**DB 테이블 I/O:** 없음 (파일 시스템만)

---

### (B) Register: insurer/product/document upsert

| 항목 | 내용 |
|------|------|
| **목적** | Manifest 기반 보험사/상품/문서 메타데이터 DB 등록 |
| **입력** | `data/manifest/docs_manifest.csv` |
| **출력** | `insurer`, `product`, `document` 테이블 |
| **핵심 로직** | 1. insurer UPSERT (ON CONFLICT insurer_code)<br>2. product UPSERT (ON CONFLICT insurer_id, product_code)<br>3. document INSERT (ON CONFLICT product_id, document_type, file_hash DO NOTHING) |
| **실패 시 처리** | ERROR - UNIQUE 위반 시 해당 행 skip, 계속 진행 |
| **Idempotency 키** | `insurer.insurer_code`<br>`product(insurer_id, product_code)`<br>`document(product_id, document_type, file_hash)` |

**DB 테이블 I/O:**
```sql
-- INSERT/UPSERT
INSERT INTO insurer (insurer_code, insurer_name, ...)
ON CONFLICT (insurer_code) DO UPDATE SET insurer_name = EXCLUDED.insurer_name;

INSERT INTO product (insurer_id, product_code, product_name, ...)
ON CONFLICT (insurer_id, product_code) DO UPDATE SET product_name = EXCLUDED.product_name;

INSERT INTO document (product_id, document_type, file_path, file_hash, doc_type_priority, ...)
ON CONFLICT (product_id, document_type, file_hash) DO NOTHING;
```

**보장:**
- `insurer.insurer_code` UNIQUE
- `product(insurer_id, product_code)` UNIQUE
- `document(product_id, document_type, file_hash)` UNIQUE

---

### (C) Parse: PDF→text/pages

| 항목 | 내용 |
|------|------|
| **목적** | PDF 원본에서 텍스트 추출, 문서 타입별 파싱 전략 적용 |
| **입력** | `document` 테이블 (`file_path`) |
| **출력** | `data/derived/{insurer}/text/{file_hash}.txt` |
| **핵심 로직** | 1. PDF 라이브러리(PyMuPDF/pdfplumber) 로드<br>2. 페이지별 텍스트 추출<br>3. 문서 타입별 전처리 (약관: 목차 제거, 설계서: 표 추출 등)<br>4. UTF-8 텍스트 파일 저장 |
| **실패 시 처리** | ERROR - 파싱 실패 시 `document.meta` 에 `parse_error` flag, 계속 진행 |
| **Idempotency 키** | `file_hash` (동일 파일은 캐시 재사용) |

**DB 테이블 I/O:**
```sql
-- UPDATE
UPDATE document SET meta = meta || '{"parse_status": "success", "page_count": 120}'::jsonb
WHERE document_id = ?;
```

---

### (D) Chunk: 청크 생성 (원본만)

| 항목 | 내용 |
|------|------|
| **목적** | 텍스트를 검색 가능한 청크 단위로 분할 (원본만, `is_synthetic=false`) |
| **입력** | `data/derived/{insurer}/text/{file_hash}.txt` |
| **출력** | `chunk` 테이블 (is_synthetic=false) |
| **핵심 로직** | 1. 텍스트 로드<br>2. Chunking 전략 (fixed size / semantic / sentence-based)<br>3. `chunk.content` INSERT<br>4. `chunk.is_synthetic=false` 강제 |
| **실패 시 처리** | WARN - 빈 청크 생성 시 경고, 계속 진행 |
| **Idempotency 키** | `(document_id, page_number, chunk_index)` 또는 `content_hash` |

**DB 테이블 I/O:**
```sql
INSERT INTO chunk (document_id, page_number, content, is_synthetic, meta)
VALUES (?, ?, ?, false, '{}')
ON CONFLICT (document_id, page_number, chunk_index) DO NOTHING;
```

**중복 방지:**
- Option 1: `UNIQUE(document_id, page_number, chunk_index)` (추가 권장)
- Option 2: `content_hash` 기반 중복 제거 (application-level)

---

### (E) Embed: embedding 생성

| 항목 | 내용 |
|------|------|
| **목적** | 청크 텍스트를 벡터 임베딩으로 변환 |
| **입력** | `chunk.content` (WHERE embedding IS NULL) |
| **출력** | `chunk.embedding` (vector(1536)) |
| **핵심 로직** | 1. 임베딩 모델 로드 (OpenAI text-embedding-3-small 등)<br>2. Batch 단위 임베딩 생성<br>3. `chunk.embedding` UPDATE |
| **실패 시 처리** | WARN - API 실패 시 재시도 3회, 이후 embedding=NULL 유지 |
| **Idempotency 키** | `chunk_id` (embedding NULL인 경우만 생성) |

**DB 테이블 I/O:**
```sql
UPDATE chunk SET embedding = ?::vector(1536)
WHERE chunk_id = ? AND embedding IS NULL;
```

---

### (F) Extract: chunk_entity, amount_entity 추출

| 항목 | 내용 |
|------|------|
| **목적** | LLM 기반 엔티티 추출 (담보명, 금액, 질병, 수술 등) |
| **입력** | `chunk.content` |
| **출력** | `chunk_entity`, `amount_entity` |
| **핵심 로직** | 1. LLM Extraction (GPT-4o/Claude 등)<br>2. Structured output parsing<br>3. `chunk_entity` INSERT (entity_type, coverage_code, entity_value)<br>4. `amount_entity` INSERT (coverage_code, context_type, amount_value) |
| **실패 시 처리** | WARN - 추출 실패 시 빈 entity, 계속 진행 |
| **Idempotency 키** | `(chunk_id, entity_type, coverage_code)` 또는 전체 삭제 후 재생성 |

**DB 테이블 I/O:**
```sql
-- chunk_entity
INSERT INTO chunk_entity (chunk_id, entity_type, coverage_code, entity_value, extraction_method, confidence)
VALUES (?, 'coverage', ?, ?, 'llm_v1', 0.9)
ON CONFLICT (chunk_id, entity_type, coverage_code) DO UPDATE SET entity_value = EXCLUDED.entity_value;

-- amount_entity
INSERT INTO amount_entity (chunk_id, coverage_code, context_type, amount_value, amount_text, extraction_method, confidence)
VALUES (?, ?, 'payment', ?, ?, 'llm_v1', 0.85);
```

**FK 보장:**
- `chunk_entity.coverage_code` → `coverage_standard.coverage_code` (NULL 허용, 다음 단계에서 정규화)
- `amount_entity.coverage_code` → `coverage_standard.coverage_code` (NOT NULL)

---

### (G) Normalize: 담보명→신정원 코드 매핑

| 항목 | 내용 |
|------|------|
| **목적** | 보험사별 담보명을 신정원 통일 담보 코드로 매핑 (`coverage_alias` 생성) |
| **입력** | `chunk_entity` (entity_type='coverage') |
| **출력** | `coverage_alias` |
| **핵심 로직** | 1. 추출된 담보명 수집<br>2. Rule 기반 매핑 (coverage_mapping.csv 또는 규칙 엔진)<br>3. `coverage_standard` 존재 확인 (FK 검증)<br>4. `coverage_alias` INSERT (confidence=high/medium/low)<br>5. 매핑 실패 시 UNMAPPED 리포트 생성 |
| **실패 시 처리** | WARN - 매핑 실패 시 UNMAPPED 리포트, **억지 매핑 금지** |
| **Idempotency 키** | `(insurer_id, insurer_coverage_name)` UNIQUE |

**DB 테이블 I/O:**
```sql
-- coverage_alias INSERT (신정원 코드 존재 시만)
INSERT INTO coverage_alias (insurer_id, coverage_id, insurer_coverage_name, confidence, mapping_method)
SELECT ?, cs.coverage_id, ?, 'high', 'rule'
FROM coverage_standard cs
WHERE cs.coverage_code = ?
ON CONFLICT (insurer_id, insurer_coverage_name) DO UPDATE
SET coverage_id = EXCLUDED.coverage_id, confidence = EXCLUDED.confidence;

-- UNMAPPED 리포트 (coverage_standard 미존재)
INSERT INTO unmapped_coverages_log (insurer_id, coverage_name, frequency, last_seen)
VALUES (?, ?, 1, NOW())
ON CONFLICT (insurer_id, coverage_name) DO UPDATE
SET frequency = unmapped_coverages_log.frequency + 1, last_seen = NOW();
```

**절대 금지:**
```sql
-- ❌ 절대 금지
INSERT INTO coverage_standard (coverage_code, coverage_name, ...)
VALUES (?, ?, ...);
```

---

### (H) Synthetic: Mixed coverage chunk 분해

| 항목 | 내용 |
|------|------|
| **목적** | 1개 청크에 2개 이상 담보 포함 시 담보별 synthetic chunk 생성 (Amount Bridge 전용) |
| **입력** | `chunk` (is_synthetic=false, 2개 이상 coverage 포함) |
| **출력** | `chunk` (is_synthetic=true) |
| **핵심 로직** | 1. Mixed coverage 감지 (chunk_entity COUNT > 1)<br>2. LLM 기반 담보별 텍스트 분해<br>3. Synthetic chunk INSERT<br>4. 필수 필드 설정:<br>&nbsp;&nbsp;&nbsp;- `is_synthetic=true`<br>&nbsp;&nbsp;&nbsp;- `synthetic_source_chunk_id=원본 chunk_id`<br>&nbsp;&nbsp;&nbsp;- `meta.synthetic_type="split"`<br>&nbsp;&nbsp;&nbsp;- `meta.synthetic_method="v1_6_3_beta_2_split"`<br>&nbsp;&nbsp;&nbsp;- `meta.entities.coverage_code` 설정 |
| **실패 시 처리** | WARN - 생성 실패 시 원본 chunk 유지, 계속 진행 |
| **Idempotency 키** | `(synthetic_source_chunk_id, coverage_code)` |

**생성 대상 문서 타입:**
- 가입설계서 (proposal)
- 상품요약서 (summary)
- 사업방법서 (business)

**DB 테이블 I/O:**
```sql
INSERT INTO chunk (document_id, page_number, content, is_synthetic, synthetic_source_chunk_id, meta)
VALUES (?, ?, ?, true, ?, '{
  "synthetic_type": "split",
  "synthetic_method": "v1_6_3_beta_2_split",
  "entities": {"coverage_code": "CA_DIAG_GENERAL"}
}'::jsonb);
```

**제약 검증:**
```sql
-- CHECK constraint 자동 검증
CHECK (
  (is_synthetic = false AND synthetic_source_chunk_id IS NULL) OR
  (is_synthetic = true AND synthetic_source_chunk_id IS NOT NULL)
)
```

**사용 제한 (필수):**
```sql
-- ✅ Amount Bridge (허용)
SELECT ae.amount_value, c.content
FROM amount_entity ae
JOIN chunk c ON ae.chunk_id = c.chunk_id
WHERE ae.coverage_code = 'CA_DIAG_GENERAL'
  AND ae.context_type = 'payment';
-- is_synthetic 필터링 불필요

-- ❌ Compare/Retrieval (금지)
SELECT c.content
FROM chunk c
WHERE c.document_id IN (...)
  AND c.is_synthetic = false;  -- 필수 필터
```

---

### (I) Validate: 정합성 체크 + 리포트 생성

| 항목 | 내용 |
|------|------|
| **목적** | 전체 Ingestion 결과 검증, 리포트 생성 |
| **입력** | All tables |
| **출력** | `artifacts/ingestion/<YYYYMMDD_HHMM>/*.{json,csv,log}` |
| **핵심 로직** | 1. 문서/청크/엔티티 통계 수집<br>2. 신정원 코드 정합성 검증<br>3. Synthetic chunk 정책 준수 확인<br>4. UNMAPPED 담보 빈도 분석<br>5. Amount context 분포 분석<br>6. 리포트 파일 생성 |
| **실패 시 처리** | INFO - 검증만, 롤백 없음 |
| **Idempotency 키** | 실행 타임스탬프 (덮어쓰기 없음) |

**검증 쿼리:**
```sql
-- 1. coverage_alias FK 위반 검사
SELECT ca.insurer_coverage_name, ca.coverage_id
FROM coverage_alias ca
LEFT JOIN coverage_standard cs ON ca.coverage_id = cs.coverage_id
WHERE cs.coverage_id IS NULL;

-- 2. chunk_entity에 존재하는 coverage_code 중 표준 테이블 미존재
SELECT DISTINCT ce.coverage_code
FROM chunk_entity ce
LEFT JOIN coverage_standard cs ON ce.coverage_code = cs.coverage_code
WHERE ce.coverage_code IS NOT NULL AND cs.coverage_code IS NULL;

-- 3. amount_entity FK 위반 (NOT NULL이므로 삽입 시 실패해야 정상)
SELECT ae.coverage_code, COUNT(*)
FROM amount_entity ae
LEFT JOIN coverage_standard cs ON ae.coverage_code = cs.coverage_code
WHERE cs.coverage_code IS NULL
GROUP BY ae.coverage_code;

-- 4. Synthetic chunk 정책 위반
SELECT chunk_id FROM chunk
WHERE is_synthetic = true AND synthetic_source_chunk_id IS NULL;

SELECT chunk_id FROM chunk
WHERE is_synthetic = true AND NOT (meta ? 'synthetic_type');

-- 5. 보험사별 UNMAPPED top 10
SELECT insurer_id, coverage_name, frequency
FROM unmapped_coverages_log
ORDER BY frequency DESC
LIMIT 10;
```

**리포트 파일:**
```
artifacts/ingestion/20250123_1430/
├─ summary.json              # 전체 통계 (문서/청크/엔티티 수)
├─ unmapped_coverages.csv    # UNMAPPED 담보 목록 (빈도순)
├─ synthetic_stats.json      # Synthetic chunk 생성 통계
├─ amount_context_distribution.json  # payment/count/limit 비율
├─ coverage_alias_mapping.csv  # 보험사별 매핑 성공률
└─ validation_errors.log     # FK 위반, 정책 위반 목록
```

---

## DB 테이블별 I/O 요약

| 테이블 | INSERT 단계 | UPSERT 키 | FK 보장 | 비고 |
|--------|------------|-----------|---------|------|
| `insurer` | Register | `insurer_code` UNIQUE | - | |
| `product` | Register | `(insurer_id, product_code)` UNIQUE | → insurer | |
| `document` | Register | `(product_id, document_type, file_hash)` UNIQUE | → product | |
| `chunk` | Chunk, Synthetic | `(document_id, page_number, chunk_index)` 권장 | → document | is_synthetic 분리 |
| `chunk_entity` | Extract | `(chunk_id, entity_type, coverage_code)` 권장 | → chunk<br>→ coverage_standard (nullable) | Normalize 전 NULL 허용 |
| `amount_entity` | Extract | 재생성 전략 | → chunk<br>→ coverage_standard (NOT NULL) | |
| `coverage_alias` | Normalize | `(insurer_id, insurer_coverage_name)` UNIQUE | → insurer<br>→ coverage_standard | 자동 INSERT 허용 |

---

## CLI 매핑 (tools/ingest/cli.py)

### Subcommand 설계

```bash
# 전체 실행
python -m tools.ingest.cli run-all

# 단계별 실행
python -m tools.ingest.cli discover
python -m tools.ingest.cli register
python -m tools.ingest.cli parse --doc-type terms
python -m tools.ingest.cli chunk
python -m tools.ingest.cli embed --batch-size 100
python -m tools.ingest.cli extract --model gpt-4o
python -m tools.ingest.cli normalize
python -m tools.ingest.cli synthetic --doc-types proposal,summary
python -m tools.ingest.cli validate
```

### Subcommand 정의

| Subcommand | 설명 | 주요 옵션 | Artifacts |
|------------|------|-----------|-----------|
| `discover` | 파일 스캔, manifest 생성 | `--root-dir` | `data/manifest/docs_manifest.csv` |
| `register` | DB 메타데이터 등록 | `--manifest` | - |
| `parse` | PDF 텍스트 추출 | `--doc-type`, `--workers` | `data/derived/{insurer}/text/*.txt` |
| `chunk` | 청크 생성 | `--strategy`, `--size` | - |
| `embed` | 임베딩 생성 | `--model`, `--batch-size` | - |
| `extract` | 엔티티 추출 | `--model`, `--workers` | - |
| `normalize` | 담보 매핑 | `--mapping-file` | `artifacts/ingestion/{ts}/unmapped_coverages.csv` |
| `synthetic` | Synthetic chunk 생성 | `--doc-types`, `--method` | `artifacts/ingestion/{ts}/synthetic_stats.json` |
| `validate` | 검증 + 리포트 | `--output-dir` | `artifacts/ingestion/{ts}/*` |
| `run-all` | 전체 파이프라인 | `--skip-steps` | All artifacts |

### Artifacts 경로 규칙

```python
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
ARTIFACTS_ROOT = f"artifacts/ingestion/{TIMESTAMP}"

# 리포트 파일
SUMMARY_PATH = f"{ARTIFACTS_ROOT}/summary.json"
UNMAPPED_PATH = f"{ARTIFACTS_ROOT}/unmapped_coverages.csv"
SYNTHETIC_STATS_PATH = f"{ARTIFACTS_ROOT}/synthetic_stats.json"
AMOUNT_DIST_PATH = f"{ARTIFACTS_ROOT}/amount_context_distribution.json"
VALIDATION_LOG_PATH = f"{ARTIFACTS_ROOT}/validation_errors.log"

# 심볼릭 링크
LATEST_LINK = "artifacts/ingestion/latest"
os.symlink(ARTIFACTS_ROOT, LATEST_LINK)
```

---

## Synthetic Chunk 생성 정책 (확정)

### 생성 대상 문서 타입
- **가입설계서** (proposal)
- **상품요약서** (summary)
- **사업방법서** (business)

### 생성 조건
- 1개 원본 청크에 2개 이상 담보(`coverage_code`) 포함

### 필수 필드

| 필드 | 값 | 검증 |
|------|---|------|
| `is_synthetic` | `true` | NOT NULL CHECK |
| `synthetic_source_chunk_id` | 원본 chunk_id | NOT NULL, FK to chunk |
| `meta.synthetic_type` | `"split"` | JSONB 필수 |
| `meta.synthetic_method` | `"v1_6_3_beta_2_split"` | 버전 명시 |
| `meta.entities.coverage_code` | 해당 담보 코드 | 분해 근거 |

### 사용 제한 (강제)

**✅ 허용: Amount Bridge**
```sql
SELECT ae.amount_value, c.content
FROM amount_entity ae
JOIN chunk c ON ae.chunk_id = c.chunk_id
WHERE ae.coverage_code = ?;
-- is_synthetic 필터링 불필요
```

**❌ 금지: Compare/Retrieval Axis**
```sql
-- 비교 축 검색
SELECT c.* FROM chunk c
WHERE c.document_id = ?
  AND c.is_synthetic = false;  -- 필수

-- Policy 축 검색
SELECT c.* FROM chunk c
WHERE c.document_id = ?
  AND c.is_synthetic = false;  -- 필수
```

---

## 요약

| 단계 | 핵심 출력 | Idempotency 키 | 실패 정책 |
|------|----------|----------------|-----------|
| Discover | manifest.csv | file_hash | FATAL |
| Register | insurer/product/document | UNIQUE 제약 3종 | ERROR (skip) |
| Parse | text/*.txt | file_hash | ERROR (flag) |
| Chunk | chunk (is_synthetic=false) | (document_id, page, index) | WARN |
| Embed | chunk.embedding | chunk_id | WARN |
| Extract | chunk_entity, amount_entity | (chunk_id, type, code) | WARN |
| Normalize | coverage_alias | (insurer_id, coverage_name) | WARN |
| Synthetic | chunk (is_synthetic=true) | (source_chunk_id, coverage) | WARN |
| Validate | Reports | timestamp | INFO |

**핵심 원칙:**
- 신정원 코드 정합 강제 (coverage_standard 자동 INSERT 금지)
- Synthetic chunk는 Amount Bridge 전용
- 모든 단계 Idempotent 설계
