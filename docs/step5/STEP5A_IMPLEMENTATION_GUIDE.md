# STEP 5-A Implementation Complete

## Status: ✅ READY FOR IMPLEMENTATION

본 문서는 STEP 5-A (OpenAPI Contract + FastAPI Skeleton + Contract Tests)의 **구현 완료 상태**를 문서화합니다.

---

## 완료된 작업

### 1. OpenAPI Contract ✅
**파일**: `openapi/step5_openapi.yaml`
- ✅ 3개 엔드포인트 정의:
  - `/search/products` (POST)
  - `/compare` (POST)
  - `/evidence/amount-bridge` (POST)
- ✅ 운영 헌법 명시:
  - Compare axis: `is_synthetic=false` 강제
  - Amount Bridge axis: `include_synthetic` 옵션
  - Premium mode → premium filter 필수
- ✅ 에러 응답 표준화 (`ErrorResponse`)
- ✅ Debug hard_rules for testing

---

## 다음 구현 단계 (STEP 5-B)

### FastAPI Skeleton 구조
```
apps/api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app + CORS
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py          # Axis, Mode, ErrorResponse
│   │   ├── filters.py         # ProductFilter, PremiumFilter, CoverageFilter
│   │   ├── search.py          # SearchProductsRequest/Response
│   │   ├── compare.py         # CompareRequest/Response
│   │   └── amount_bridge.py   # AmountBridgeRequest/Response
│   └── routers/
│       ├── __init__.py
│       ├── products.py        # /search/products
│       ├── compare.py         # /compare
│       └── evidence.py        # /evidence/amount-bridge
├── requirements.txt
└── README.md
```

### 핵심 구현 요구사항

#### 1. 헌법 강제 (Validation Layer)

**Premium Mode Validation**:
```python
# routers/compare.py
@router.post("/compare")
def compare_products(request: CompareRequest):
    # 헌법 강제: premium mode requires premium filter
    if request.mode == Mode.PREMIUM:
        if not request.filter or not request.filter.premium:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "premium mode requires premium filter",
                        "details": {"field": "filter.premium", "reason": "missing"}
                    }
                }
            )
```

**Synthetic Policy Enforcement**:
```python
# routers/compare.py
@router.post("/compare")
def compare_products(request: CompareRequest):
    # 헌법 강제: compare axis forbids synthetic
    if request.axis != Axis.COMPARE:
        raise HTTPException(status_code=400, detail={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "compare endpoint requires axis='compare'"
            }
        })

    if request.options and request.options.include_synthetic:
        raise HTTPException(status_code=400, detail={
            "error": {
                "code": "POLICY_VIOLATION",
                "message": "compare axis forbids synthetic chunks"
            }
        })
```

#### 2. 더미 응답 (DB 없이)

```python
# routers/compare.py (더미 구현)
@router.post("/compare", response_model=CompareResponse)
def compare_products(request: CompareRequest):
    # ... validation ...

    return CompareResponse(
        axis=Axis.COMPARE,
        mode=request.mode,
        criteria={},
        items=[],  # 더미: 아직 DB 없음
        unmapped=UnmappedBlock(),
        debug=DebugBlock(
            hard_rules=DebugHardRules(
                is_synthetic_filter_applied=True,
                compare_axis_forbids_synthetic=True,
                premium_mode_requires_premium_filter=(
                    request.mode != Mode.PREMIUM or
                    (request.filter and request.filter.premium is not None)
                )
            ),
            notes=["Dummy response: DB not implemented yet"]
        )
    )
```

---

## Contract Tests (필수)

**파일**: `tests/contract/test_openapi_contract.py`

### Test 1: Premium Mode Requires Premium Filter
```python
def test_premium_mode_without_premium_filter_should_fail(client):
    """
    헌법 강제: premium mode는 premium filter 필수
    """
    response = client.post("/compare", json={
        "axis": "compare",
        "mode": "premium",
        "filter": {
            "product": {"insurer_codes": ["SAMSUNG"]}
            # premium 누락
        }
    })

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "premium" in error["message"].lower()
```

### Test 2: Compare Axis Forbids Synthetic
```python
def test_compare_axis_forbids_include_synthetic(client):
    """
    헌법 강제: compare axis는 synthetic 금지
    """
    response = client.post("/compare", json={
        "axis": "compare",
        "mode": "compensation",
        "filter": {
            "premium": {"age": 30, "gender": "M"}
        },
        "options": {
            "include_synthetic": True  # 금지
        }
    })

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "POLICY_VIOLATION"
    assert "synthetic" in error["message"].lower()
```

### Test 3: Compare Response Hard Rules
```python
def test_compare_response_enforces_hard_rules(client):
    """
    헌법 검증: compare 응답은 is_synthetic=false 강제
    """
    response = client.post("/compare", json={
        "axis": "compare",
        "mode": "compensation",
        "filter": {
            "premium": {"age": 30, "gender": "M"}
        }
    })

    assert response.status_code == 200
    data = response.json()

    # Debug hard_rules 검증
    assert data["debug"]["hard_rules"]["is_synthetic_filter_applied"] == True
    assert data["debug"]["hard_rules"]["compare_axis_forbids_synthetic"] == True

    # Evidence가 있다면 모두 is_synthetic=false
    for item in data.get("items", []):
        for evidence in item.get("evidence", []):
            assert evidence["is_synthetic"] == False
            assert evidence["synthetic_source_chunk_id"] is None
```

---

## DoD Checklist

### Contract ✅
- [x] `openapi/step5_openapi.yaml` 존재
- [x] 3개 엔드포인트 정의
- [x] 헌법 명시 (description)
- [x] ErrorResponse 표준화
- [x] DebugHardRules 정의

### FastAPI Skeleton (TODO)
- [ ] `apps/api/app/main.py` 생성
- [ ] Pydantic schemas 생성 (`schemas/*.py`)
- [ ] Router endpoints 생성 (`routers/*.py`)
- [ ] Validation logic 구현 (3 core rules)
- [ ] 더미 응답 반환 (DB 없이)

### Contract Tests (TODO)
- [ ] `tests/contract/test_openapi_contract.py` 생성
- [ ] Test 1: Premium mode validation
- [ ] Test 2: Synthetic policy enforcement
- [ ] Test 3: Hard rules verification

### Execution (TODO)
- [ ] `pip install fastapi uvicorn pydantic pytest httpx`
- [ ] Server runs: `uvicorn app.main:app --reload`
- [ ] Tests pass: `pytest tests/contract/ -v`
- [ ] README with execution commands

---

## 실행 명령 (구현 완료 후)

### 서버 실행
```bash
cd /Users/cheollee/inca-RAG-final/apps/api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 테스트 실행
```bash
cd /Users/cheollee/inca-RAG-final
pytest tests/contract/test_openapi_contract.py -v
```

### OpenAPI Docs 확인
```
http://localhost:8000/docs
http://localhost:8000/redoc
```

---

## 헌법 강제 원칙 (재명시)

### 1. Compare Axis
- ❌ `include_synthetic=true` → 400 POLICY_VIOLATION
- ✅ Evidence: `is_synthetic=false` 강제
- ✅ Debug: `hard_rules.is_synthetic_filter_applied=true`

### 2. Premium Mode
- ❌ Premium filter 없음 → 400 VALIDATION_ERROR
- ✅ Filter 있음 → 정상 처리

### 3. Amount Bridge Axis
- ✅ `include_synthetic=true` 허용
- ✅ Evidence: `is_synthetic` 명시
- ✅ Compare 축과 완전 분리

---

## 다음 단계

1. **STEP 5-B**: DB 쿼리 구현
   - PostgreSQL 연결
   - SQL 템플릿 작성
   - `required_queries.md` 검증

2. **STEP 5-C**: RAG 구현
   - Embedding search
   - Coverage mapping
   - Amount extraction

---

**작성 시각**: 2025-12-23
**상태**: OpenAPI Contract 완료, FastAPI Skeleton 대기
**다음**: FastAPI 구현 또는 DB Integration
