# STEP 3.8-γ′ PRIME Comparison Constitution (가입설계서 절대 SSOT 헌법)

**Date:** 2025-12-25
**Version:** Prime (γ′)
**Purpose:** 가입설계서 결과표 기반 비교 시스템의 최상위 원칙

---

## 전제 (Premise)

**모든 보험사의 가입설계서가 이미 존재한다.**

```
data/
  samsung/가입설계서/삼성_가입설계서_2511.pdf
  meritz/가입설계서/메리츠_가입설계서_2511.pdf
  db/가입설계서/DB_가입설계서(40세이하)_2511.pdf
  db/가입설계서/DB_가입설계서(41세이상)_2511.pdf
  kb/가입설계서/KB_가입설계서.pdf
  lotte/가입설계서/롯데_가입설계서(남)_2511.pdf
  lotte/가입설계서/롯데_가입설계서(여)_2511.pdf
  hanwha/가입설계서/한화_가입설계서_2511.pdf
  heungkuk/가입설계서/흥국_가입설계서_2511.pdf
  hyundai/가입설계서/현대_가입설계서_2511.pdf
```

**이 시스템은 "설계 문서 중심 비교"가 아니라**
**"가입설계서 결과표 기반 비교 시스템"이다.**

---

## 헌법 10조 (PRIME Constitution)

### Article I: Proposal Absolute SSOT (가입설계서 절대 단일 진실 출처)

**가입설계서는 결과 문서이며, 단일 진실 출처(SSOT)이다.**

```
비교 로직, 슬롯 채움, 판단 근거 = 가입설계서만 사용
```

**다른 문서의 역할:**
- ❌ 요약서/약관/사업방법서 → 비교 근거 사용 금지
- ⭕ 요약서/약관/사업방법서 → 사람 검증/사후 설명 참고용만 허용

**근거:**
- 가입설계서 = 고객이 실제로 가입하는 담보와 조건의 최종 결과물
- 약관 = 법적 정의 (비교 대상 아님)
- 상품요약서 = 일반 설명 (비교 대상 아님)

---

### Article II: Presence = Eligibility (존재 = 보장 가능)

**가입설계서에 담보가 존재하면 자동 in_universe**

```python
IF proposal_row exists:
    coverage_state = "in_universe"
    eligibility = "O"  # 자동
ELSE:
    coverage_state = "out_of_universe"
```

**금지:**
- ❌ eligibility O/X/△ 판정 로직
- ❌ regex 기반 "보장 가능" 판단
- ❌ 조건부 보장(△) 추론

**원칙:**
- 가입설계서에 담보가 있으면 = 보장 가능
- 가입설계서에 담보가 없으면 = 비교 불가

---

### Article III: No Inference Rule (추론 금지)

**가입설계서에 명시되지 않은 의미 해석, 보완 추론 금지**

**금지 행위:**
- ❌ "보통 ~하다"
- ❌ "일반적으로 ~"
- ❌ "유리합니다"
- ❌ 담보 의미 병합
- ❌ 금액·조건 추정
- ❌ 약관 정의로 가입설계서 보완

**허용:**
- ✅ 가입설계서에 명시된 문자열 그대로 추출
- ✅ 정규식 기반 구조화 (금액, 기간)
- ✅ NULL 처리 (정보 없음)

---

### Article IV: Honest Failure Priority (정직한 실패 우선)

**가입설계서에 정보가 없으면 정직한 실패**

```python
if proposal_data is None:
    # ❌ 다른 문서로 보완
    # ❌ 추정
    # ✅ 정직한 실패
    return {
        "value": None,
        "reason": "가입설계서에 정보 없음",
        "comparison_state": "comparable_with_gaps"
    }
```

**원칙:**
- 틀린 비교보다 "비교 불가" 명시가 우선
- 불확실성 투명화

---

### Article V: Row-Based Evidence (행 기반 근거)

**Evidence = 가입설계서 표의 1행(row)**

```json
{
  "evidence": {
    "document_id": "SAMSUNG_PROPOSAL_2024",
    "doc_type": "PROPOSAL",
    "page": 3,
    "row_id": "row_15",
    "coverage_name_raw": "일반암진단비(유사암제외)",
    "amount_raw": "3,000만원"
  }
}
```

**불필요:**
- ❌ chunk cross-check
- ❌ policy document 교차 검증
- ❌ span text 정합성 검사

**근거:**
- 가입설계서 1행 = 완전한 증거

---

### Article VI: No Mapping Requirement (매핑 선택)

**normalized_name / coverage_code 매핑 실패는 비교 실패 사유가 아니다**

```python
# REQUIRED
required_fields = [
    "insurer",
    "proposal_id",
    "coverage_row_id",
    "coverage_name_raw",  # 원문 그대로
    "amount_raw"
]

# OPTIONAL
optional_fields = [
    "normalized_name",     # 검색용
    "coverage_code",       # 분류용
    "disease_scope_norm"   # 약관 참조용
]
```

**비교 판정:**
- 매핑 성공 → 더 정확한 비교 가능
- 매핑 실패 → `unmapped` 상태 유지, 원문 기반 비교

---

### Article VII: Factual Comparison Only (사실 비교만)

**비교 = 사실 차이 제시만**

**기본 응답 (Default):**
1. 비교표 (Fact Table) - 가입설계서 원문 데이터
2. 차이 요약 (Difference Summary) - 수치 차이만

**추천 (Optional):**
- 기본 응답에 포함 ❌
- 사용자가 "추천", "어떤 게 나은지"를 명시적으로 요청한 경우에만 생성
- 추천은 조건부 서술만 허용 (`if–then`)

---

### Article VIII: No Document Hierarchy (문서 계층 금지)

**가입설계서 외 문서는 비교에 사용하지 않는다**

```
PROPOSAL (가입설계서)   → 비교 SSOT (Required)
PRODUCT_SUMMARY         → 사람 참조용만 (시스템 외부)
BUSINESS_METHOD         → 사람 참조용만 (시스템 외부)
POLICY                  → 사람 참조용만 (시스템 외부)
```

**구현 강제 규칙:**
```python
# 비교 로직 입력단 검증
if evidence.source_doc_type != "PROPOSAL":
    raise ValidationError("PROPOSAL 외 문서 사용 금지")

# 슬롯 채움 검증
for slot in comparison_result:
    if slot.evidence.doc_type != "PROPOSAL":
        raise ConstitutionalViolation(
            "Article VIII 위반: 비교 근거는 PROPOSAL만 허용"
        )
```

**명확한 금지:**
- ❌ 약관/요약서를 비교 로직 입력에 사용
- ❌ "약관에서 보완", "요약서 참조" 등 자동 병합
- ❌ Document Priority 개념 자체 (PROPOSAL 단독 사용)
- ⭕ 약관/요약서는 **사람이 수동 확인**하는 참고 문서

**완화 (v1.1과 차이):**
- v1.1: PROPOSAL 필수, 나머지 선택
- γ′: PROPOSAL만 사용, 나머지 **시스템 사용 금지**

---

### Article IX: Deterministic Processing (결정론적 처리)

**허용되는 추출 방법:**
- ✅ 표 구조 기반 row 파싱 (테이블 경계, 셀 위치)
- ✅ 컬럼 위치/헤더 기반 rule
- ✅ Regex 패턴 매칭
- ✅ 결정론적 문자열 변환

**처리 흐름:**

```
1. 가입설계서 원문 로드
   ↓
2. 표(row) 단위로 담보 추출 (표 구조 파싱)
   ↓
3. 원문 담보명 그대로 SSOT 저장
   ↓
4. 금액 / 기간 / 갱신 여부 구조화 (regex + rule)
   ↓
5. [OPTIONAL] 담보 매핑 (normalized_name, coverage_code)
   ↓
6. 비교 대상 교집합 생성 (원문 매칭 또는 coverage_code 매칭)
   ↓
7. 비교표 생성
   ↓
8. 차이 요약 생성
   ↓
9. [CONDITIONAL] 사용자 요청 시에만 If-Then 답변 생성
```

**금지:**
- ❌ LLM 기반 추론/보완
- ❌ 확률적 방법
- ❌ 약관 정의 병합
- ❌ 담보 의미 일반화
- ❌ 추정/가정 기반 슬롯 채우기

---

### Article X: Validation by Reality (현실 검증)

**검증 시나리오:**

**PASS:**
- ✅ KB/삼성/메리츠 가입설계서 표만으로 비교표 생성
- ✅ 담보 없음 → out_of_universe
- ✅ 매핑 실패 → unmapped 상태 유지

**FAIL:**
- ❌ 약관 문장 인용
- ❌ eligibility 판정 로직 사용
- ❌ 추천이 기본 응답에 포함됨
- ❌ "유리합니다" 같은 주관 서술
- ❌ 가입설계서에 없는 정보로 슬롯 채움

---

## Comparison States (비교 상태)

### γ′ (PRIME) 4-State System

**1. in_universe_comparable**
- 담보 존재 & 비교 가능
- 매핑 성공 또는 원문 매칭 가능
- 모든 핵심 정보 확보

**2. in_universe_unmapped**
- 담보 존재 & 매핑 실패
- 원문 기반 비교 지속 (정확도 낮음)
- ❌ 비교 불가 아님

**3. in_universe_with_gaps**
- 담보 존재 & 일부 정보 누락
- 제한적 비교 가능
- NULL 슬롯 명시

**4. out_of_universe**
- 담보 미존재
- 비교 불가

---

### v1.0/v1.1 (5-State) 호환성 매핑

| v1.0/v1.1 (5-State) | γ′ (4-State) | 비고 |
|---------------------|-------------|------|
| `comparable` | `in_universe_comparable` | 핵심 슬롯 모두 일치 |
| `comparable_with_gaps` | `in_universe_with_gaps` | 일부 슬롯 NULL |
| `non_comparable` | *(제거됨)* | γ′에서는 담보 존재 = 비교함 |
| `unmapped` | `in_universe_unmapped` | 매핑 실패, 원문 비교 |
| `out_of_universe` | `out_of_universe` | 담보 미존재 |

**변경 이유:**
- v1.1의 `non_comparable`은 설계상 모순
- 가입설계서에 있으면 항상 비교 가능 (정확도는 별개)
- γ′는 **존재 = 비교 가능** 원칙으로 단순화

---

## 금지 사항 (Hard Ban)

### 절대 금지 행위

1. ❌ **eligibility O/X/△ 판정 로직**
   - 가입설계서에 존재 = in_universe = 자동 보장 가능

2. ❌ **가입설계서 외 문서 기반 판단**
   - 약관, 상품요약서, 사업방법서로 비교 근거 생성 금지

3. ❌ **주관적 서술**
   - "유리합니다"
   - "추천드립니다"
   - "충분한 보장"
   - "보통 ~하다"

4. ❌ **담보 의미 병합 또는 일반화**
   - 원문 담보명 그대로 사용

5. ❌ **금액·조건 추정**
   - 가입설계서에 없으면 NULL

6. ❌ **추천 기본 포함**
   - 추천은 사용자 명시 요청 시에만

7. ❌ **Document Priority 강제**
   - PROPOSAL만 사용, 나머지 금지

8. ❌ **LLM 기반 매핑/추론**
   - regex 기반 구조화만 허용

---

## v1.0 → v1.1 → γ′ 변경 요약

### v1.0 (Initial)
- 3단 필수 (비교표 + 종합평가 + 추천)
- eligibility: O/X/△
- Document Priority: 4개 모두 필수
- Evidence: 교차 검증

### v1.1 (Refinement)
- 2단 기본 + 1단 선택
- eligibility: O/△ (X = out_of_universe)
- Document Priority: PROPOSAL 필수, 나머지 선택
- Evidence: PROPOSAL 우선

### γ′ (Prime - Current)
- 2단 기본 + 1단 선택 (유지)
- **eligibility 판정 로직 제거 (존재 = 보장 가능)**
- **Document: PROPOSAL만 사용 (나머지 금지)**
- **Evidence: 1행 = 완전한 증거**
- **매핑 선택 (unmapped ≠ 비교 실패)**
- **추론 전면 금지**

---

## 설계 근거 (Design Rationale)

### 왜 가입설계서만 사용하는가?

**가입설계서 = 결과 문서:**
- 모든 약관, 조건, 제약이 이미 반영된 최종 결과물
- 고객이 실제로 가입하는 담보와 조건

**약관 = 법적 정의:**
- 담보의 법적 의미 (비교 대상 아님)
- 가입설계서 생성의 입력 (이미 반영됨)

**비유:**
- 가입설계서 = 최종 견적서 (What you get)
- 약관 = 제품 매뉴얼 (How it works)

**비교 시스템은 "What you get"을 비교한다.**

---

### 왜 eligibility 판정을 제거하는가?

**존재 = 보장 가능:**
- 가입설계서에 담보가 있으면 = 가입 가능 = 보장 가능
- 보장 불가는 애초에 가입설계서에 없음

**O/X/△ 판정 = 불필요:**
- 가입설계서 = 이미 가입 가능한 담보만 포함
- 조건부 보장도 가입설계서에 명시

---

### 왜 매핑을 선택으로 하는가?

**매핑 = 분류/검색 보조:**
- 비교는 원문 기반으로도 가능
- 매핑 실패 = 정확도 하락 (비교 불가 아님)

**Unmapped ≠ Out of Universe:**
- Unmapped: 가입설계서에는 있으나 분류 안 됨 (비교 가능, 정확도 낮음)
- Out of Universe: 가입설계서에 없음 (비교 불가)

---

## 확장성 (Scalability)

**보험사 증가 (현재 8개 → 10개+):**
- ✅ 가입설계서만 추가하면 즉시 비교 가능
- ✅ 약관 파싱 불필요
- ✅ 문서 계층 불필요
- ✅ 매핑 실패해도 원문 비교 가능

**담보 증가:**
- ✅ 가입설계서 행 추가만으로 자동 지원
- ✅ 새로운 담보 = 새로운 행
- ✅ 매핑 나중에 추가 가능

---

## Implementation Guidance

### Proposal Row Schema (가입설계서 행 스키마)

```json
{
  "row_id": "SAMSUNG_PROPOSAL_2024_row_15",
  "insurer": "SAMSUNG",
  "proposal_id": "SAMSUNG_PROPOSAL_2024",
  "page": 3,

  // REQUIRED (원문)
  "coverage_name_raw": "일반암진단비(유사암제외)",
  "amount_raw": "3,000만원",
  "period_raw": "80세 만기",

  // OPTIONAL (구조화)
  "amount_value": 30000000,
  "coverage_period_years": 60,
  "payment_period_years": 20,
  "renewal_flag": false,

  // OPTIONAL (매핑)
  "normalized_name": "일반암진단비",
  "coverage_code": "CANCER_DIAGNOSIS",
  "mapping_status": "MAPPED",

  // OPTIONAL (약관 참조용 - 비교에 사용 금지)
  "disease_scope_norm": {
    "include_group_id": "GENERAL_CANCER_C00_C97",
    "exclude_group_id": "SIMILAR_CANCER_SAMSUNG_V1"
  }
}
```

### Comparison Logic (비교 로직)

```python
def compare_coverages(insurer_a, insurer_b, coverage_query):
    # Step 1: Load proposal rows
    rows_a = load_proposal_rows(insurer_a)
    rows_b = load_proposal_rows(insurer_b)

    # Step 2: Find matching coverage
    row_a = find_coverage(rows_a, coverage_query)  # 원문 매칭 or coverage_code 매칭
    row_b = find_coverage(rows_b, coverage_query)

    # Step 3: Universe Lock
    if row_a is None:
        return out_of_universe(insurer_a)
    if row_b is None:
        return out_of_universe(insurer_b)

    # Step 4: Compare (원문 데이터만 사용)
    return {
        "comparison_table": {
            insurer_a: extract_fact_table(row_a),  # 가입설계서 원문
            insurer_b: extract_fact_table(row_b)
        },
        "difference_summary": calculate_deltas(row_a, row_b),  # 수치 차이
        "optional_guidance": None  # 기본 null
    }
```

---

## Success Criteria (성공 기준)

### 구조적 성공
- ✅ 가입설계서 단독 비교 가능
- ✅ eligibility 로직 제거
- ✅ 추천 Optional 분리
- ✅ SSOT 원문 중심 재정렬

### 기능적 성공
- ✅ 8개 보험사 가입설계서 비교 작동
- ✅ 담보 없음 → out_of_universe
- ✅ 매핑 실패 → unmapped (비교 지속)
- ✅ 약관 문장 인용 없음

### Constitutional Compliance
- ✅ Proposal Absolute SSOT
- ✅ Presence = Eligibility
- ✅ No Inference Rule
- ✅ Honest Failure Priority
- ✅ Row-Based Evidence
- ✅ No Mapping Requirement
- ✅ Factual Comparison Only
- ✅ No Document Hierarchy
- ✅ Deterministic Processing
- ✅ Validation by Reality

---

**End of PRIME Comparison Constitution**
