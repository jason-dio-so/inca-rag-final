# Ingestion 오류 처리 정책

## 개요

Ingestion 파이프라인의 오류 처리 원칙과 단계별 실패 케이스 대응 전략을 정의한다.

**핵심 원칙:**
1. **명확한 에러 등급**: FATAL/ERROR/WARN/INFO
2. **격리 가능성**: 단일 문서 실패가 전체를 중단하지 않음
3. **추적 가능성**: 모든 에러는 로그 + 리포트로 기록
4. **재현 가능성**: 실패 원인 재현 가능한 정보 보존

---

## 에러 등급 정의

### FATAL (즉시 중단)
- **정의**: 파이프라인 전체 무결성을 위협하는 오류
- **대응**: 즉시 중단, 롤백 고려
- **예시**:
  - DB 연결 실패 (Register 이후 단계)
  - Manifest 스키마 파손
  - `coverage_standard` 테이블 손상
  - 필수 권한 부족 (파일 시스템, DB)

### ERROR (단계/문서 실패, 다음 진행)
- **정의**: 특정 문서 또는 청크 단위 실패
- **대응**: 해당 문서 skip, 에러 로그 기록, 다음 문서 진행
- **예시**:
  - PDF 파싱 실패 (손상된 파일)
  - UNIQUE 제약 위반 (중복 document)
  - LLM API 실패 (Extract 단계)

### WARN (결과 남기고 진행)
- **정의**: 비정상이지만 치명적이지 않은 상황
- **대응**: 경고 로그 + 리포트, 처리 계속
- **예시**:
  - 빈 청크 생성
  - Embedding NULL (API 실패 후 재시도 소진)
  - UNMAPPED 담보명 발견
  - Synthetic chunk 생성 실패

### INFO (참고)
- **정의**: 정상 동작 로그
- **대응**: 로그만 기록
- **예시**:
  - 파일 스캔 진행 상황
  - DB upsert 성공
  - 리포트 생성 완료

---

## 기본 에러 처리 정책

### Discover/Register 단계
- **스키마/Manifest 파손**: FATAL
- **파일 권한 문제**: FATAL (일부 파일 skip 불가)
- **UNIQUE 제약 위반**: ERROR (해당 행 skip)

### Parse 단계
- **개별 PDF 파싱 실패**: ERROR (문서 단위 격리 가능)
- **타임아웃**: ERROR (대용량 파일)
- **인코딩 오류**: ERROR (텍스트 복구 불가)

### Extract/Normalize 단계
- **LLM API 실패**: ERROR → WARN (재시도 후)
- **UNMAPPED 담보**: WARN (리포트 생성, 억지 매핑 금지)
- **FK 위반 시도**: ERROR (coverage_standard 미존재)

### Synthetic 단계
- **생성 실패**: WARN (원본 chunk 유지)
- **정책 위반**: ERROR (source_chunk_id 누락 등)

---

## 실패 케이스 대응표 (12개 필수)

| # | 단계 | 실패 케이스 | 감지 방법 | 처리 | 리포트/로그 | 재실행 영향 |
|---|------|------------|-----------|------|-------------|------------|
| 1 | Discover | 파일 해시 산출 실패 | `hashlib.sha256()` 예외 | FATAL | `error.log`: "Failed to compute hash for {file_path}" | 전체 재실행 필요 |
| 2 | Discover | 파일 권한 문제 | `PermissionError` | FATAL | `error.log`: "Permission denied: {file_path}" | 권한 수정 후 재실행 |
| 3 | Register | Manifest 중복 | CSV 동일 `file_hash` 2회 | WARN | `unmapped.csv`: 중복 행 기록 | Idempotent (skip) |
| 4 | Register | Manifest 필수 컬럼 누락 | CSV 헤더 검증 | FATAL | `error.log`: "Missing required column: {col}" | Manifest 수정 후 재실행 |
| 5 | Register | document UNIQUE 충돌 | `IntegrityError` (product_id, document_type, file_hash) | ERROR (skip) | `error.log`: "Duplicate document: {product_code}/{doc_type}/{file_hash}" | Idempotent (ON CONFLICT DO NOTHING) |
| 6 | Embed | pgvector 미설치 | `CREATE EXTENSION vector` 실패 | FATAL | `error.log`: "pgvector extension not installed" | pgvector 설치 후 재실행 |
| 7 | Embed | Embedding 컬럼 NULL | API 실패, 재시도 소진 | WARN | `warn.log`: "Embedding failed for chunk_id={id}, left NULL" | 재실행 시 NULL만 재생성 |
| 8 | Normalize | coverage_standard 미존재 코드 참조 | `SELECT` 결과 empty | WARN | `unmapped_coverages.csv`: {insurer, coverage_name, frequency} | UNMAPPED 리포트, 억지 매핑 금지 |
| 9 | Normalize | coverage_alias 억지 매핑 시도 | Application-level 검증 | ERROR (차단) | `error.log`: "Attempted to create coverage_alias without valid coverage_id" | **금지 동작** |
| 10 | Synthetic | source_chunk_id 누락 | `CHECK` 제약 위반 | ERROR | `error.log`: "Synthetic chunk missing source_chunk_id: {chunk_id}" | 정책 위반, 수정 후 재실행 |
| 11 | Extract | count-context/limit-context 오추출 징후 | `amount_entity.context_type='count'` 이상치 | WARN | `amount_context_distribution.json`: 이상 비율 표시 | 리포트만, 데이터 유지 |
| 12 | Parse | 대용량 PDF 파싱 타임아웃 | `timeout` 설정 초과 | ERROR (skip) | `error.log`: "Parsing timeout for {file_path} (>{timeout}s)" | 해당 문서 제외, 나머지 진행 |
| 13 | Parse | 인코딩/텍스트 추출 공백 | 추출된 텍스트 length=0 | WARN | `warn.log`: "Empty text extracted from {file_path}" | 문서 flag, 수동 검토 |
| 14 | Register | 문서 타입 오분류 | `document_type` not in allowed values | ERROR | `error.log`: "Invalid document_type: {type}" | Manifest 수정 필요 |
| 15 | All | DB 연결 실패 | `psycopg2.OperationalError` | FATAL | `error.log`: "Database connection failed" | DB 복구 후 재실행 |

---

## 케이스별 상세 처리

### 1. 파일 해시 산출 실패
```python
try:
    file_hash = compute_file_hash(file_path)
except (IOError, PermissionError) as e:
    logger.fatal(f"Failed to compute hash for {file_path}: {e}")
    sys.exit(1)
```

### 2. document UNIQUE 충돌
```python
try:
    cur.execute("""
        INSERT INTO document (product_id, document_type, file_hash, ...)
        VALUES (%s, %s, %s, ...)
        ON CONFLICT (product_id, document_type, file_hash) DO NOTHING
        RETURNING document_id
    """, (product_id, document_type, file_hash, ...))
    result = cur.fetchone()
    if not result:
        logger.info(f"Document already exists, skipped: {product_code}/{document_type}")
except Exception as e:
    logger.error(f"Failed to insert document: {e}")
```

### 3. pgvector 미설치
```python
try:
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
except psycopg2.Error as e:
    logger.fatal("pgvector extension not available. Install with: apt install postgresql-16-pgvector")
    sys.exit(1)
```

### 4. coverage_standard 미존재 코드 참조
```python
# Normalize 단계
for coverage_name in extracted_coverages:
    coverage_code = resolve_coverage_code(coverage_name, mapping_rules)

    # 신정원 코드 존재 확인
    cur.execute("SELECT coverage_id FROM coverage_standard WHERE coverage_code = %s", (coverage_code,))
    result = cur.fetchone()

    if result:
        # ✅ coverage_alias INSERT
        cur.execute("""
            INSERT INTO coverage_alias (insurer_id, coverage_id, insurer_coverage_name, confidence)
            VALUES (%s, %s, %s, 'high')
            ON CONFLICT (insurer_id, insurer_coverage_name) DO NOTHING
        """, (insurer_id, result['coverage_id'], coverage_name))
    else:
        # ❌ UNMAPPED 리포트
        logger.warn(f"UNMAPPED: {coverage_name} → {coverage_code} (coverage_standard not found)")
        unmapped_log.append({
            "insurer_id": insurer_id,
            "coverage_name": coverage_name,
            "attempted_code": coverage_code,
            "timestamp": datetime.now()
        })
```

### 5. coverage_alias 억지 매핑 차단
```python
# ❌ 절대 금지
def create_coverage_standard_if_not_exists(coverage_code, coverage_name):
    """이 함수는 존재하면 안 됨"""
    raise NotImplementedError("coverage_standard 자동 INSERT 금지")

# ✅ 올바른 처리
def safe_create_coverage_alias(insurer_id, coverage_name, coverage_code):
    """coverage_standard 존재 확인 후 alias 생성"""
    if not coverage_exists(coverage_code):
        logger.error(f"Attempted to create coverage_alias without valid coverage_id: {coverage_code}")
        return False  # 생성 차단

    # 정상 생성
    insert_coverage_alias(insurer_id, coverage_code, coverage_name)
    return True
```

### 6. Synthetic chunk source_chunk_id 누락
```python
try:
    cur.execute("""
        INSERT INTO chunk (document_id, content, is_synthetic, synthetic_source_chunk_id, meta)
        VALUES (%s, %s, true, %s, %s)
    """, (document_id, synthetic_content, source_chunk_id, meta))
except psycopg2.IntegrityError as e:
    if "chk_synthetic_source" in str(e):
        logger.error(f"Synthetic chunk missing source_chunk_id: {e}")
        # 정책 위반, 생성 중단
```

### 7. count-context 오추출 징후
```python
# Validate 단계
cur.execute("""
    SELECT context_type, COUNT(*) as cnt
    FROM amount_entity
    GROUP BY context_type
""")
distribution = {row['context_type']: row['cnt'] for row in cur.fetchall()}

# 이상 비율 감지
if distribution.get('count', 0) > distribution.get('payment', 0):
    logger.warn("Anomaly: count context > payment context. Review extraction logic.")

# 리포트에 기록
with open(f"{artifacts_dir}/amount_context_distribution.json", 'w') as f:
    json.dump(distribution, f, indent=2)
```

### 8. 대용량 PDF 파싱 타임아웃
```python
import signal

def parse_pdf_with_timeout(file_path, timeout=300):
    """PDF 파싱 (최대 5분)"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Parsing timeout for {file_path}")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    try:
        text = extract_text_from_pdf(file_path)
        signal.alarm(0)  # 타이머 취소
        return text
    except TimeoutError as e:
        logger.error(str(e))
        return None
```

---

## 금지 사항 (재명시)

### 1. coverage_standard 자동 INSERT/UPDATE 금지
```python
# ❌ 절대 금지
INSERT INTO coverage_standard (coverage_code, coverage_name, ...)
VALUES (?, ?, ...);

UPDATE coverage_standard SET coverage_name = ?
WHERE coverage_code = ?;
```

**이유:** 신정원 코드는 수동 검증 필수, 자동 생성 시 코드 충돌/오매핑 위험

### 2. meta JSONB로 필터링 금지
```sql
-- ❌ 금지 (성능 저하)
SELECT * FROM chunk WHERE meta->>'is_synthetic' = 'false';

-- ✅ 허용 (인덱스 활용)
SELECT * FROM chunk WHERE is_synthetic = false;
```

**이유:** JSONB 쿼리는 B-tree 인덱스 사용 불가, 성능 저하

### 3. 원본 PDF 변형 금지
```python
# ❌ 금지
# PDF 파일 압축/재저장
pdf_doc.save(file_path, deflate=True)

# PDF 워터마크 추가
add_watermark(file_path)
```

**이유:** `file_hash` 변경 → 추적 불가능, 원본 무결성 훼손

### 4. 억지 매핑 금지
```python
# ❌ 금지
if coverage_code not in coverage_standard:
    # "비슷한" 코드로 강제 매핑
    coverage_code = find_similar_code(coverage_code)  # 위험
    insert_coverage_alias(...)

# ✅ 허용
if coverage_code not in coverage_standard:
    # UNMAPPED 리포트
    log_unmapped(coverage_name, coverage_code)
```

---

## 에러 로그 형식

### error.log
```
2025-01-23 14:30:15 [FATAL] Database connection failed: connection refused (host=localhost, port=5432)
2025-01-23 14:35:22 [ERROR] Failed to parse PDF: data/raw/SAMSUNG/terms/corrupted.pdf (InvalidPDFException)
2025-01-23 14:40:10 [ERROR] Duplicate document skipped: CANCER_PLUS_2024/약관/a3f5e8d9c1b2...
```

### warn.log
```
2025-01-23 14:42:05 [WARN] UNMAPPED coverage: "암진단자금" → "CA_DIAG_FUND" (coverage_standard not found)
2025-01-23 14:45:30 [WARN] Empty text extracted from: data/raw/HYUNDAI/summary/blank_page.pdf
2025-01-23 14:50:12 [WARN] Embedding failed for chunk_id=12345, left NULL (API timeout after 3 retries)
```

---

## 재실행 시 에러 처리

### Idempotent 에러
- **UNIQUE 제약 위반**: ON CONFLICT DO NOTHING → skip, 에러 아님
- **file_hash 중복**: 재스캔 시 덮어쓰기 → 정상

### Non-Idempotent 에러
- **LLM API 실패**: 재실행 시 재시도
- **타임아웃**: 설정 조정 후 재실행

---

## 요약

| 에러 등급 | 대응 | 재실행 | 예시 |
|----------|------|--------|------|
| FATAL | 즉시 중단 | 원인 제거 후 전체 재실행 | DB 연결 실패, Manifest 파손 |
| ERROR | 해당 문서 skip | 실패 문서만 재실행 가능 | PDF 파싱 실패, UNIQUE 충돌 |
| WARN | 경고 로그 | 리포트 검토 후 선택적 수정 | UNMAPPED, 빈 청크 |
| INFO | 로그만 | - | 진행 상황 |

**핵심 원칙:**
- 격리 가능한 에러는 전체 중단하지 않음
- 모든 에러는 추적 가능하게 로그/리포트
- 금지 동작은 Application-level에서 차단
