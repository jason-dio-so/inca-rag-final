# STEP 3.8-γ 비교 시스템 헌법 (Comparison Constitution)

**Date:** 2025-12-25
**Purpose:** 가입설계서 기반 담보 비교의 절대 원칙 (10 Core Principles)

---

## 비교 시스템 10대 원칙

### 1. 가입설계서 단일 진실 출처 원칙 (Proposal SSOT)
**비교 대상은 가입설계서에 명시된 담보만 허용한다.**
- 가입설계서에 없는 담보 → 즉시 비교 차단 (`out_of_universe`)
- 약관/상품요약서/사업방법서는 비교 대상을 확장하지 않는다
- Universe Lock = `proposal_coverage_universe` 테이블

### 2. 정직한 실패 원칙 (Honest Failure)
**틀린 비교보다 "비교 불가"가 우선이다.**
- 담보 누락 가능성 → 비교 거부
- 핵심 축(eligibility, coverage_limit) 누락 → 비교 거부
- Evidence 없는 O/X 판정 → 비교 거부

### 3. 비교 축 고정 원칙 (Fixed Comparison Axes)
**고객이 정의한 5개 비교 축만 사용한다.**
```yaml
comparison_axes:
  eligibility:        # 보장 가능 여부 (O/X/조건부)
  coverage_limit:     # 보장한도 (금액)
  coverage_start:     # 보장개시
  exclusions:         # 면책/감액 조건
  enrollment_condition: # 가입조건 (나이/기간/납입)
```
- v1 비교에서 이 외 축 사용 금지
- 보험사 증가(3→8개)에도 축 변경 금지

### 4. Evidence 필수 원칙 (Evidence Mandatory)
**모든 비교 판정은 가입설계서 근거(evidence)를 포함해야 한다.**
```json
{
  "document_id": "SAMSUNG_PROPOSAL_2024",
  "page": 3,
  "span_text": "암진단비 3,000만원",
  "source_confidence": "proposal_confirmed"
}
```
- Evidence 없는 값 → NULL 처리
- NULL 값으로 O/X 판정 금지

### 5. 결정론적 추출 원칙 (Deterministic Extraction)
**LLM/확률적 추론 금지 영역:**
- ❌ coverage_code 매핑 (Excel만 허용)
- ❌ disease_scope_norm 생성 (약관 + 그룹 참조만)
- ❌ 금액 단위 추정 (정규식만 허용)
- ❌ O/X 판정 추론 (명시적 표현만 허용)

**허용 방법:**
- ✅ 정규식(regex) 패턴 매칭
- ✅ 테이블/YAML 기반 룰
- ✅ 명시적 텍스트 매칭

### 6. 5-State 비교 시스템 (5-State Comparison)
**비교 결과는 5가지 상태만 허용한다.**
```python
comparison_state:
  - comparable                # 모든 핵심 축 일치
  - comparable_with_gaps      # 일부 축 NULL (약관 확인 필요)
  - non_comparable            # 담보 성격 다름
  - unmapped                  # Excel 매핑 실패
  - out_of_universe           # 가입설계서에 없음
```

### 7. 보험료 보조 원칙 (Premium as Auxiliary)
**보험료는 비교 축이 아니라 보조 판단 요소이다.**
- 보험료는 반드시 조건(나이/성별/납입기간)과 함께 제시
- Premium API 실패 시:
  - 비교 중단 ❌
  - 보험료 제외하고 비교 지속 ✅
  - 사용자에게 "보험료 정보 없음" 명시

### 8. 응답 구조화 원칙 (Structured Response Only)
**자연어 요약/추천 금지. 구조화 응답만 허용.**

**응답 3단 구조:**
1. **비교 표 (Fact Table)** - O/X/△/금액만
2. **종합 평가 (Rule-based)** - 사전 정의 규칙 조합
3. **조건 분기형 추천** - "A가 더 좋다" ❌ / "보장금액 우선이면 A" ✅

**금지 표현:**
- ❌ "가장 넓은 보장"
- ❌ "가장 유리함"
- ❌ "추천합니다"
- ❌ Any value judgment

### 9. 문서 우선순위 원칙 (Document Priority)
**비교 출처 문서 우선순위 (고정):**
```
1. 가입설계서 (Proposal)      → 비교 대상 결정
2. 상품요약서 (Summary)        → 개요 설명
3. 사업방법서 (Business Rules) → 실무 제약
4. 약관 (Policy)              → 법적 해석 (최후)
```
- 약관은 "어떻게 해석할 것인가"만 담당
- "무엇을 비교할 것인가"는 가입설계서만 결정

### 10. Fail-Fast 검증 원칙 (Fail-Fast Validation)
**비교 시작 전 필수 검증:**
```python
# Step 1: Universe Lock
if coverage not in proposal_coverage_universe:
    return out_of_universe  # 즉시 중단

# Step 2: Mapping Validation
if mapping_status != 'MAPPED':
    return unmapped  # 즉시 중단

# Step 3: Critical Slots
if canonical_coverage_code is None:
    return non_comparable  # 즉시 중단
```

---

## 헌법 위반 행위 (Constitutional Violations)

다음 행위는 절대 금지:
1. ❌ 약관을 기준으로 비교 대상 생성/확장
2. ❌ 가입설계서 없이 비교 시작
3. ❌ LLM으로 coverage_code 추론/매핑
4. ❌ Evidence 없는 O/X 판정
5. ❌ 임의 비교 축 추가
6. ❌ 자연어 추천 문구 생성
7. ❌ 보험료 API 실패 시 비교 중단
8. ❌ 문서 우선순위 역전 (약관 먼저)
9. ❌ out_of_universe 오류 무시/추정
10. ❌ 불확실성 은폐 ("보통은~", "일반적으로~")

---

## 설계 결정 근거 (Design Rationale)

### 왜 가입설계서가 SSOT인가?
- 가입설계서 = 고객이 실제로 가입하는 담보 리스트
- 약관 = 담보의 법적 정의 (비교 대상 선정 아님)
- **비유:** 가입설계서 = 지도(목적지) / 약관 = 나침반(방향)

### 왜 정직한 실패인가?
- 잘못된 비교 = 고객 손해
- 비교 불가 명시 = 고객 신뢰 유지
- 불확실성 투명화 = 법적 리스크 최소화

### 왜 구조화 응답만 허용하는가?
- 자연어 요약 = 판단/추천으로 오인
- 구조화 응답 = 근거 추적 가능
- Fact Table = 법적 방어 가능

---

## 확장 안정성 (Scalability Guarantee)

**보험사 3개 → 8개 확장 시:**
- ✅ 비교 축 변경 없음 (5 axes 고정)
- ✅ Comparison States 변경 없음 (5 states 고정)
- ✅ Document Priority 변경 없음
- ✅ Evidence Schema 변경 없음

**단, 보험사별로 필요:**
- Excel 매핑 데이터 추가 (per insurer)
- Disease code group 추가 (per insurer)
- Proposal ingestion (per insurer)

---

**End of Constitution v1.0**
