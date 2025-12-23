# 데이터 레이아웃 설계

## 개요

inca-RAG-final 프로젝트의 데이터 디렉토리 구조 및 파일 명명 규칙을 정의한다.

**핵심 원칙:**
1. **원본 데이터 불변성**: `data/raw/` 는 읽기 전용
2. **보험사 자료는 새 디렉토리에 copy**: 기존 저장소 수정 금지
3. **file_hash 기반 추적**: 파일명 변경 가능, 내용 변조 불가
4. **재현 가능성**: 동일 입력 → 동일 출력 보장

---

## 디렉토리 구조

```
inca-RAG-final/
├─ data/
│  ├─ raw/                        # 원본 PDF (읽기 전용)
│  │  ├─ SAMSUNG/                 # 보험사 코드 (대문자)
│  │  │  ├─ terms/                # 약관
│  │  │  │  ├─ product_A_terms_v1.pdf
│  │  │  │  └─ product_B_terms_v2.pdf
│  │  │  ├─ business/             # 사업방법서
│  │  │  ├─ summary/              # 상품요약서
│  │  │  └─ proposal/             # 가입설계서
│  │  ├─ HYUNDAI/
│  │  ├─ KB/
│  │  └─ ...
│  │
│  ├─ derived/                    # 중간 산출물
│  │  ├─ SAMSUNG/
│  │  │  ├─ text/                 # 추출된 텍스트
│  │  │  │  ├─ <file_hash>.txt
│  │  │  │  └─ ...
│  │  │  └─ pages/                # 페이지별 텍스트 (선택)
│  │  │     ├─ <file_hash>/
│  │  │     │  ├─ page_001.txt
│  │  │     │  └─ page_002.txt
│  │  ├─ HYUNDAI/
│  │  └─ ...
│  │
│  └─ manifest/                   # 메타데이터
│     ├─ docs_manifest.csv        # 전체 문서 manifest
│     └─ coverage_mapping.csv     # 담보 매핑 (선택)
│
├─ artifacts/                     # 파이프라인 산출물
│  └─ ingestion/
│     ├─ 20250123_1430/           # 실행 타임스탬프
│     │  ├─ summary.json
│     │  ├─ unmapped_coverages.csv
│     │  ├─ synthetic_stats.json
│     │  └─ validation_errors.log
│     └─ latest -> 20250123_1430/ # 심볼릭 링크
│
└─ docs/
   └─ ingestion/                  # 설계 문서
```

---

## 보험사 코드 표준

### 코드 규칙
- **대문자** (SAMSUNG, HYUNDAI, KB 등)
- `insurer.insurer_code` 와 동일
- 디렉토리명 = `insurer_code`

### 표준 보험사 코드 목록
| 보험사명 | insurer_code | 디렉토리 |
|----------|--------------|----------|
| 삼성화재 | SAMSUNG | `data/raw/SAMSUNG/` |
| 현대해상 | HYUNDAI | `data/raw/HYUNDAI/` |
| KB손해보험 | KB | `data/raw/KB/` |
| DB손해보험 | DB | `data/raw/DB/` |
| 메리츠화재 | MERITZ | `data/raw/MERITZ/` |

---

## 문서 타입 디렉토리

### 표준 문서 타입
| 문서 타입 | 디렉토리명 | doc_type_priority |
|-----------|-----------|-------------------|
| 약관 | `terms/` | 1 (최우선) |
| 사업방법서 | `business/` | 2 |
| 상품요약서 | `summary/` | 3 |
| 가입설계서 | `proposal/` | 4 |

### 디렉토리 매핑
```python
DOC_TYPE_MAP = {
    "terms": "약관",
    "business": "사업방법서",
    "summary": "상품요약서",
    "proposal": "가입설계서"
}

DOC_TYPE_PRIORITY = {
    "약관": 1,
    "사업방법서": 2,
    "상품요약서": 3,
    "가입설계서": 4
}
```

---

## 파일 명명 규칙

### 원본 PDF (data/raw/)
**규칙:** 자유 형식 허용, 단 `file_hash` 로 추적

**권장 패턴:**
```
{product_code}_{doc_type}_{version}.pdf
```

**예시:**
```
data/raw/SAMSUNG/terms/
├─ cancer_plus_terms_v1_2023.pdf
├─ cancer_plus_terms_v2_2024.pdf
└─ health_premium_terms_v1.pdf
```

### 중간 산출물 (data/derived/)
**규칙:** `{file_hash}.txt` (SHA-256 해시 기준)

**예시:**
```
data/derived/SAMSUNG/text/
├─ a3f5e8d9c1b2...4f6.txt
└─ b2c7a1f3e9d4...8a2.txt
```

### Manifest (data/manifest/)
**형식:** CSV (UTF-8 BOM)

**파일명:**
- `docs_manifest.csv` - 전체 문서 목록
- `coverage_mapping.csv` - 담보 매핑 (선택)

---

## 원본 데이터 Copy 정책

### 기존 저장소에서 Copy
```bash
# 기존 inca-rag 저장소 (읽기 전용)
SOURCE=/path/to/inca-rag/data/insurers/

# 신규 inca-RAG-final 저장소 (작업 디렉토리)
TARGET=/Users/cheollee/inca-RAG-final/data/raw/

# Copy (내용 변경 금지)
rsync -av --checksum $SOURCE/ $TARGET/
```

### Copy 후 검증
1. 파일 개수 확인
2. `file_hash` 산출 (SHA-256)
3. Manifest 생성

---

## file_hash 산출 규칙

### 알고리즘
- **SHA-256** (hex digest)
- 파일 내용 기준 (메타데이터 제외)

### Python 예시
```python
import hashlib

def compute_file_hash(file_path: str) -> str:
    """SHA-256 file hash 산출"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()
```

### 사용 목적
1. **중복 방지**: 동일 파일 재처리 방지
2. **추적성**: 파일명 변경 시에도 원본 추적
3. **무결성**: 파일 변조 감지

---

## 중간 산출물 관리

### 텍스트 추출 (data/derived/{insurer}/text/)
- **파일명**: `{file_hash}.txt`
- **인코딩**: UTF-8
- **내용**: PDF 전체 텍스트 (페이지 구분 포함)

### 페이지별 텍스트 (선택)
```
data/derived/SAMSUNG/pages/{file_hash}/
├─ page_001.txt
├─ page_002.txt
└─ page_003.txt
```

### 정리 정책
- **유지 기간**: 30일 (설정 가능)
- **재생성**: `file_hash` 기준 캐시 확인 후 재사용
- **삭제**: 최종 DB INSERT 완료 후 선택적 삭제

---

## Manifest 생성 시점

### (A) Discover 단계
1. `data/raw/` 디렉토리 스캔
2. 각 PDF 파일 `file_hash` 산출
3. `docs_manifest.csv` 생성

### Manifest 갱신 정책
- **전체 스캔**: 초기 실행 시
- **증분 스캔**: 신규 파일만 추가
- **검증**: `file_hash` 기준 중복 제거

---

## 디렉토리 권한

### 읽기 전용
- `data/raw/` - 원본 PDF (수정 금지)

### 읽기/쓰기
- `data/derived/` - 중간 산출물
- `data/manifest/` - Manifest
- `artifacts/` - 리포트

### 권장 설정
```bash
# 원본 보호
chmod -R 444 data/raw/

# 작업 디렉토리
chmod -R 755 data/derived/
chmod -R 755 artifacts/
```

---

## 디렉토리 초기화 스크립트

```bash
#!/bin/bash
# scripts/init_data_dirs.sh

BASE_DIR="$(pwd)/data"

# 디렉토리 생성
mkdir -p "$BASE_DIR/raw"
mkdir -p "$BASE_DIR/derived"
mkdir -p "$BASE_DIR/manifest"
mkdir -p "$(pwd)/artifacts/ingestion"

# 보험사별 하위 디렉토리 (예시)
INSURERS=("SAMSUNG" "HYUNDAI" "KB" "DB" "MERITZ")
DOC_TYPES=("terms" "business" "summary" "proposal")

for insurer in "${INSURERS[@]}"; do
    # raw 디렉토리
    for doc_type in "${DOC_TYPES[@]}"; do
        mkdir -p "$BASE_DIR/raw/$insurer/$doc_type"
    done

    # derived 디렉토리
    mkdir -p "$BASE_DIR/derived/$insurer/text"
    mkdir -p "$BASE_DIR/derived/$insurer/pages"
done

echo "Data directories initialized."
```

---

## 요약

| 디렉토리 | 용도 | 권한 | 재현성 |
|----------|------|------|--------|
| `data/raw/` | 원본 PDF | 읽기 전용 | 불변 |
| `data/derived/` | 중간 산출물 | 읽기/쓰기 | 캐시 (재생성 가능) |
| `data/manifest/` | Manifest | 읽기/쓰기 | 재생성 가능 |
| `artifacts/` | 리포트 | 읽기/쓰기 | 실행별 생성 |

**핵심:**
- 원본 PDF는 `file_hash` 로 추적
- 중간 산출물은 재생성 가능
- Manifest는 단일 진실 공급원(Single Source of Truth)
