# Manifest 스펙 정의

## 개요

`docs_manifest.csv`는 Ingestion 파이프라인의 **입력 정의서(Input Specification)**이며,
모든 원본 PDF 문서의 메타데이터를 정의한다.

**역할:**
1. **Discover 단계** 출력: 파일 스캔 결과
2. **Register 단계** 입력: DB INSERT 기준
3. **재현성 보장**: 동일 manifest → 동일 결과

---

## 파일 위치

```
data/manifest/docs_manifest.csv
```

---

## 파일 형식

- **형식**: CSV (UTF-8 with BOM)
- **구분자**: `,` (comma)
- **헤더**: 필수
- **인코딩**: UTF-8 (BOM 권장, Excel 호환성)

---

## 스키마 정의

### 필수 컬럼 (9개)

| 컬럼명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| `insurer_code` | VARCHAR(50) | ✅ | 보험사 코드 (대문자) | `SAMSUNG` |
| `insurer_name` | VARCHAR(200) | ✅ | 보험사명 | `삼성화재` |
| `product_code` | VARCHAR(100) | ✅ | 상품 코드 | `CANCER_PLUS_2024` |
| `product_name` | VARCHAR(300) | ✅ | 상품명 | `삼성화재 암플러스보험` |
| `product_type` | VARCHAR(100) | ❌ | 상품 유형 | `암보험` |
| `document_type` | VARCHAR(100) | ✅ | 문서 유형 | `약관` |
| `file_path` | TEXT | ✅ | 원본 파일 경로 (절대 또는 상대) | `data/raw/SAMSUNG/terms/cancer_plus_v1.pdf` |
| `file_hash` | VARCHAR(64) | ✅ | SHA-256 해시 | `a3f5e8d9c1b2...` |
| `effective_date` | DATE | ❌ | 효력 발생일 | `2024-01-01` |

### 선택 컬럼

| 컬럼명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `document_version` | VARCHAR(50) | 문서 버전 | `v1.2` |
| `sale_start_date` | DATE | 판매 시작일 | `2024-01-01` |
| `sale_end_date` | DATE | 판매 종료일 | `2025-12-31` |
| `notes` | TEXT | 비고 | `2024년 개정판` |

---

## 컬럼 상세 설명

### `insurer_code`
- **목적**: `insurer` 테이블 PK 조회
- **규칙**:
  - 대문자 (SAMSUNG, HYUNDAI 등)
  - `insurer.insurer_code` 와 동일
  - 신규 보험사는 `insurer` 테이블에 먼저 INSERT

### `product_code`
- **목적**: `product` 테이블 UNIQUE 키
- **규칙**:
  - 보험사 내 유일 (UNIQUE within insurer)
  - 영문/숫자/언더스코어 권장
  - 예: `CANCER_PLUS_2024`, `HEALTH_PREMIUM_2023`

### `document_type`
- **목적**: `doc_type_priority` 결정
- **허용 값**:
  - `약관` (priority=1)
  - `사업방법서` (priority=2)
  - `상품요약서` (priority=3)
  - `가입설계서` (priority=4)

### `file_path`
- **형식**: 절대 경로 또는 상대 경로
- **권장**: 프로젝트 루트 기준 상대 경로
- **예시**:
  ```
  data/raw/SAMSUNG/terms/cancer_plus_v1.pdf
  ```

### `file_hash`
- **알고리즘**: SHA-256 (hex digest)
- **용도**: 중복 방지, 무결성 검증
- **계산**:
  ```python
  import hashlib

  def compute_hash(file_path):
      sha256 = hashlib.sha256()
      with open(file_path, 'rb') as f:
          while chunk := f.read(8192):
              sha256.update(chunk)
      return sha256.hexdigest()
  ```

---

## 예시 manifest

```csv
insurer_code,insurer_name,product_code,product_name,product_type,document_type,file_path,file_hash,effective_date,document_version
SAMSUNG,삼성화재,CANCER_PLUS_2024,삼성화재 암플러스보험,암보험,약관,data/raw/SAMSUNG/terms/cancer_plus_v1.pdf,a3f5e8d9c1b2f4a6e9d7c3b1a5f8e4d2c9b6a3f1e8d5c2b9a6f3e1d8c5b2a9f6,2024-01-01,v1.0
SAMSUNG,삼성화재,CANCER_PLUS_2024,삼성화재 암플러스보험,암보험,사업방법서,data/raw/SAMSUNG/business/cancer_plus_business.pdf,b2c7a1f3e9d4b8a6f2c9e5d1b7a4f8e3d9c6b2a8f5e1d7c4b9a6f3e8d5c2b1a7,2024-01-01,
HYUNDAI,현대해상,HEALTH_PREMIUM,현대해상 프리미엄건강보험,건강보험,약관,data/raw/HYUNDAI/terms/health_premium_terms.pdf,c9f6e3d1b8a5f2e9d6c3b9a7f4e1d8c5b2a9f6e3d1b8a5f2e9d6c3b9a7f4e1,2023-06-01,v2.1
```

---

## 생성 방법

### (A) Discover 단계에서 자동 생성
```python
import os
import hashlib
import csv
from pathlib import Path

def generate_manifest(root_dir: str, output_path: str):
    """data/raw/ 스캔 후 manifest 생성"""
    rows = []

    for pdf_path in Path(root_dir).rglob("*.pdf"):
        # 경로 파싱
        parts = pdf_path.relative_to(root_dir).parts
        insurer_code = parts[0]  # SAMSUNG
        doc_type_dir = parts[1]  # terms

        # file_hash 계산
        file_hash = compute_file_hash(pdf_path)

        # 문서 타입 매핑
        doc_type_map = {
            "terms": "약관",
            "business": "사업방법서",
            "summary": "상품요약서",
            "proposal": "가입설계서"
        }
        document_type = doc_type_map.get(doc_type_dir, "기타")

        row = {
            "insurer_code": insurer_code,
            "insurer_name": "",  # 수동 입력 필요
            "product_code": "",  # 수동 입력 필요
            "product_name": "",
            "product_type": "",
            "document_type": document_type,
            "file_path": str(pdf_path),
            "file_hash": file_hash,
            "effective_date": "",
            "document_version": ""
        }
        rows.append(row)

    # CSV 작성
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writeheader()
        writer.writerows(rows)
```

### (B) 수동 보완
1. `insurer_name`, `product_code`, `product_name` 입력
2. `effective_date`, `document_version` 확인
3. 검증: 필수 컬럼 누락 확인

---

## 검증 규칙

### 필수 컬럼 검증
```python
REQUIRED_COLUMNS = [
    "insurer_code",
    "insurer_name",
    "product_code",
    "product_name",
    "document_type",
    "file_path",
    "file_hash"
]

def validate_manifest(manifest_path: str) -> list[str]:
    """Manifest 검증, 오류 목록 반환"""
    errors = []

    with open(manifest_path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        # 헤더 검증
        missing_cols = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")
            return errors

        # 행 검증
        for i, row in enumerate(reader, start=2):  # line 2부터
            for col in REQUIRED_COLUMNS:
                if not row.get(col, "").strip():
                    errors.append(f"Line {i}: {col} is empty")

            # file_path 존재 확인
            if not os.path.exists(row["file_path"]):
                errors.append(f"Line {i}: file not found: {row['file_path']}")

            # file_hash 검증
            if len(row["file_hash"]) != 64:
                errors.append(f"Line {i}: invalid file_hash length")

    return errors
```

---

## 중복 방지 정책

### 중복 정의
- **파일 중복**: 동일 `file_hash`
- **논리적 중복**: 동일 `(product_code, document_type, file_hash)`

### 처리 전략
```python
def check_duplicates(manifest_path: str):
    """중복 검사"""
    seen_hashes = set()
    seen_keys = set()

    with open(manifest_path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader, start=2):
            file_hash = row["file_hash"]
            key = (row["product_code"], row["document_type"], file_hash)

            if file_hash in seen_hashes:
                print(f"Line {i}: Duplicate file_hash: {file_hash}")

            if key in seen_keys:
                print(f"Line {i}: Duplicate (product, doc_type, hash): {key}")

            seen_hashes.add(file_hash)
            seen_keys.add(key)
```

---

## Register 단계 연동

### DB INSERT 로직
```sql
-- 1. insurer 조회/생성
INSERT INTO insurer (insurer_code, insurer_name)
VALUES (%(insurer_code)s, %(insurer_name)s)
ON CONFLICT (insurer_code) DO NOTHING
RETURNING insurer_id;

-- 2. product 조회/생성
INSERT INTO product (insurer_id, product_code, product_name, product_type)
VALUES (%(insurer_id)s, %(product_code)s, %(product_name)s, %(product_type)s)
ON CONFLICT (insurer_id, product_code) DO UPDATE
SET product_name = EXCLUDED.product_name
RETURNING product_id;

-- 3. document 조회/생성
INSERT INTO document (product_id, document_type, file_path, file_hash, doc_type_priority, effective_date)
VALUES (%(product_id)s, %(document_type)s, %(file_path)s, %(file_hash)s, %(doc_type_priority)s, %(effective_date)s)
ON CONFLICT (product_id, document_type, file_hash) DO NOTHING
RETURNING document_id;
```

---

## 증분 갱신 정책

### 신규 파일 추가
1. 기존 manifest 로드
2. `data/raw/` 재스캔
3. 신규 `file_hash` 추가
4. Manifest 재작성

### 파일 삭제 처리
- Manifest에서 제거 (물리 삭제)
- DB에서는 `is_active=false` (논리 삭제)

---

## 요약

| 항목 | 내용 |
|------|------|
| **위치** | `data/manifest/docs_manifest.csv` |
| **형식** | CSV (UTF-8 BOM) |
| **필수 컬럼** | 9개 (insurer_code ~ file_hash) |
| **중복 방지** | `file_hash` + `(product_code, document_type)` |
| **생성 방법** | Discover 단계 자동 생성 + 수동 보완 |
| **검증** | 필수 컬럼, 파일 존재, hash 형식 |

**핵심:**
- Manifest는 Ingestion 입력의 단일 진실 공급원
- `file_hash` 기반 추적으로 파일명 변경 허용
- 재현 가능성 보장
