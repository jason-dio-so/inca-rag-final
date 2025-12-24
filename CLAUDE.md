# inca-RAG-final - 보험 약관 비교 RAG 시스템 (운영 설계)

> 본 문서는 Claude가 수행하는 모든 작업의 **최상위 규칙(헌법)** 이다.

---

## 작업 디렉토리 규칙 (절대)

### 신규 루트 디렉토리
- **`inca-RAG-final/`** 에서만 작업
- 기존 `inca-rag/` 는 **읽기 전용 레퍼런스**
  - ❌ 수정 금지
  - ❌ 실행 금지
  - ✅ 구조·정책·이력 참고만 허용

### 보험사 원본 데이터
- `inca-RAG-final/data/` 하위로 copy
- 원본 내용 절대 변경 금지

---

## 신정원 통일 담보 코드 원칙 (절대)

### 절대 기준
**신정원 통일 담보 코드(canonical coverage_code)** 만이 유일한 기준이다.

- coverage_code는 신정원 테이블(`coverage_standard`)에 정합해야 한다
- 임의 담보 코드 생성 금지
- ingestion / extraction / compare / UI 전 구간 동일 코드 사용

### Coverage 매핑 정책 (STEP 6-C 확정)

**단일 출처 원칙 (Single Source of Truth)**:
- **Excel 파일 (`data/담보명mapping자료.xlsx`)** 만이 유일한 매핑 출처
- LLM/유사도/추론을 통한 매핑 절대 금지
- 매핑 결과는 3가지 상태로만 표현:
  - `MAPPED`: Excel에서 단일 canonical code 확정
  - `UNMAPPED`: Excel에 매칭 없음
  - `AMBIGUOUS`: 여러 canonical code 후보 존재 (수동 해결 필요)

**매핑 프로세스**:
1. 가입설계서 담보명 → 정규화 (공백/괄호 통일)
2. 정규화 담보명 → Excel lookup
3. `coverage_alias` → `canonical_coverage_code` 해결
4. UNMAPPED 시 비교 중단 (추정 금지)

**Coverage Universe Lock**:
- 비교 가능 담보 = **가입설계서에 있는 담보만**
- 가입설계서에 없는 담보 질의 → `out_of_universe` (비교 불가)
- 약관/사업방법서 담보는 비교 대상 아님 (Universe 외부)

**테이블 구조** (STEP 6-C):
1. **proposal_coverage_universe**
   - 가입설계서 담보 원본 저장
   - Universe Lock의 절대 기준

2. **proposal_coverage_mapped**
   - universe → canonical_coverage_code 매핑 결과
   - mapping_status 필수 (MAPPED/UNMAPPED/AMBIGUOUS)
   - canonical_coverage_code nullable (MAPPED일 때만 필수)

3. **coverage_standard** (기존)
   - 신정원 canonical 사전
   - **READ-ONLY**
   - 자동 INSERT 절대 금지

---

## Synthetic Chunk 정책 (확정)

### 정의
Mixed Coverage Chunk를 담보별로 분해한 보조 데이터

### 사용 범위
- ✅ **Amount Bridge 전용**
- ❌ compare_axis
- ❌ policy_axis
- ❌ coverage 추천

### Meta 스키마 (V1.6.3-β-3 기준)
```json
{
  "is_synthetic": true,
  "synthetic_type": "split",
  "synthetic_method": "v1_6_3_beta_2_split",
  "entities": {
    "coverage_code": "...",
    "amount": {
      "amount_value": 6000000,
      "amount_text": "600만원",
      "method": "v1_6_3_beta_2_split",
      "confidence": "high"
    }
  }
}
```

### 필터 규칙
compare / retrieval 단계에서 반드시 `is_synthetic = false` 필터 적용

### Synthetic Chunk와 Coverage Universe Lock의 관계

**Synthetic Chunk는 Coverage Universe를 확장하지 않는다.**

**절대 금지 사항**:
- ❌ Synthetic Chunk는 `proposal_coverage_universe`에 INSERT되지 않는다
- ❌ Synthetic Chunk는 비교 대상 판단에 절대 사용되지 않는다
- ❌ Synthetic으로 분해된 담보를 Universe에 추가
- ❌ Synthetic 기반 금액 비교 (Amount Bridge 외)

**원칙**:
- Coverage Universe Lock 판단은 **항상 원본 가입설계서 기준**이다
- Synthetic Chunk는 **Amount Bridge 목적 외 사용을 금지**한다
- 비교 가능 여부 확인 시 Synthetic Chunk 절대 참조 금지

**예시 (금지)**:
```python
# ❌ 금지: Synthetic chunk로 Universe 확장
if chunk.meta.get("is_synthetic") == True:
    # Universe에 추가하려는 시도
    insert_into_proposal_coverage_universe(chunk)  # 절대 금지!

# ❌ 금지: Synthetic 기반 비교 판단
if coverage_query not in universe:
    # Synthetic에서 찾으려는 시도
    check_in_synthetic_chunks(coverage_query)  # 절대 금지!
```

**예시 (허용)**:
```python
# ✅ 허용: Amount Bridge만
if need_amount_context:
    # Amount 보강 목적으로만 사용
    amount_bridge = get_from_synthetic_chunks(coverage_code, filters={"is_synthetic": True})
```

---

## GitHub 저장소 규칙 (절대)

### Single Source of Truth
본 프로젝트의 **유일한 기준 저장소**는 **GitHub `inca-rag-final` repository**이다.

### 작업 순서 (필수)
모든 작업은 다음 순서를 반드시 따른다:

1. `inca-RAG-final/` 디렉토리에서 작업
2. 로컬 Git commit
3. **GitHub `inca-rag-final`로 push**
4. 커밋 해시를 작업 결과에 명시

### Push 필수
- Push되지 않은 작업은 **완료로 간주하지 않는다**
- Claude는 작업 완료 시 항상 다음 정보를 출력해야 한다:
  - branch
  - commit hash
  - push 여부

### 기존 저장소
- 기존 `inca-rag` repository는 **참조용(read-only)**
- 어떠한 코드/문서도 추가·수정하지 않는다

---

## Slot Schema v1.1.1 (Authoritative Definition)

본 섹션은 Slot Schema v1.1.1의 **단일 기준(Single Source of Truth)** 이다.
다른 문단의 Slot 설명이 본 섹션과 충돌할 경우, **본 섹션을 우선한다**.

### 필수 슬롯 정의

| 슬롯명 | 타입 | Required | Default | 설명 |
|--------|------|----------|---------|------|
| **canonical_coverage_code** | string \| null | ❌ No | null | 신정원 통일 담보 코드<br>• mapping_status=MAPPED일 때만 필수<br>• mapping_status=UNMAPPED/AMBIGUOUS일 때 null |
| **mapping_status** | enum | ✅ Yes | - | MAPPED \| UNMAPPED \| AMBIGUOUS<br>• 항상 필수<br>• Excel 매핑 결과 상태 |
| **event_type** | enum | ❌ No | unknown | diagnosis \| surgery \| hospitalization \| treatment \| death \| unknown |
| **disease_scope_raw** | string | ❌ No | null | 가입설계서 원문 그대로<br>• 예: "유사암 제외", "5종"<br>• source_confidence=proposal_confirmed |
| **disease_scope_norm** | object \| null | ❌ No | null | **그룹 참조 기반**<br>• `{include_group_id, exclude_group_id}`<br>• NULL = 약관 미처리<br>• source_confidence≥policy_required<br>• ❌ 코드 배열 JSON 금지 |
| **waiting_period_days** | int \| null | ❌ No | null | • null = unknown<br>• 0 = explicit none<br>• >0 = 대기일수 |
| **coverage_start_rule** | string \| null | ❌ No | null | "보장개시일", "계약일" 등 |
| **reduction_periods** | array \| null | ❌ No | null | • null = unknown<br>• [] = explicit none<br>• [{from_days, to_days, rate, condition}] |
| **payout_limit** | object \| null | ❌ No | null | **통합 객체** (v1.1.1)<br>• `{type, count, period}`<br>• type: once \| multiple \| unlimited<br>• count: int \| null<br>• period: lifetime \| per_year \| per_diagnosis \| null |
| **currency** | string | ✅ Yes | KRW | 통화 (현재 KRW 고정) |
| **amount_value** | int \| null | ❌ No | null | 보장금액 (원 단위)<br>• null = unknown<br>• 0 = not applicable<br>• >0 = 원 단위 금액 |
| **payout_amount_unit** | enum | ❌ No | unknown | lump_sum \| daily \| per_event \| percentage \| unknown |
| **treatment_method** | array | ❌ No | [] | ['robotic_surgery', 'chemotherapy', ...] |
| **hospitalization_exclusions** | array \| null | ❌ No | null | • null = unknown<br>• [] = explicit none<br>• ['외래', '통원'] |
| **renewal_flag** | boolean | ❌ No | false | 갱신형 여부 |
| **renewal_period_years** | int \| null | ❌ No | null | 갱신 주기 (년) |
| **renewal_max_age** | int \| null | ❌ No | null | 갱신 최대 연령 |
| **source_confidence** | enum | ✅ Yes | - | proposal_confirmed \| policy_required \| unknown |
| **qualification_suffix** | string \| null | ❌ No | null | 설계서 괄호 내 한정어<br>• "유사암제외", "1년50%", "갱신형" 등 |

### Unknown 처리 원칙 (1급 값)

**Unknown은 "값이 없음"이 아니라 "아직 알 수 없음"을 의미한다.**

| 타입 | Unknown | Explicit None | 예시 |
|------|---------|---------------|------|
| **Scalar (int)** | `null` | `0` | waiting_period_days<br>• null = 정보 없음<br>• 0 = "보장개시일부터" 명시 |
| **Array** | `null` | `[]` | reduction_periods<br>• null = 감액 조항 정보 없음<br>• [] = "감액 없음" 명시 |
| **Enum** | `"unknown"` | N/A | payout_amount_unit<br>• "unknown" = 단위 정보 없음 |
| **Object** | `null` | N/A | payout_limit<br>• null = 횟수 제한 정보 없음 |

**절대 금지**:
- ❌ `null`을 기본값으로 치환 (예: `null` → `unlimited`)
- ❌ `unknown`을 추정/유추로 채우기
- ❌ `[]`를 `null`과 동일하게 처리

### Evidence 필수 필드

**모든 확정값(source_confidence=proposal_confirmed/policy_required)은 Evidence를 가져야 한다.**

```json
{
  "evidence": {
    "document_id": "samsung_proposal_2511",
    "page": 3,
    "span_text": "암 진단비(유사암 제외) 3,000만원 보장개시일 90일 후",
    "extraction_rule": "slot_extractor_v1_1_1"
  }
}
```

**필수 필드**:
- `document_id`: 문서 식별자 (insurer + doc_type + filename)
- `page`: 페이지 번호 (1-indexed)
- `span_text`: 추출 근거 원문
- `extraction_rule`: 추출 규칙 ID (traceability)

### Validation Rules

**MAPPED 검증**:
```python
if mapping_status == "MAPPED":
    assert canonical_coverage_code is not None
elif mapping_status in ["UNMAPPED", "AMBIGUOUS"]:
    assert canonical_coverage_code is None
```

**disease_scope_norm 검증**:
```python
if disease_scope_norm is not None:
    assert "include_group_id" in disease_scope_norm
    assert source_confidence in ["policy_required", "unknown"]
    # ❌ disease_scope_norm = {included: [...], excluded: [...]} 금지
```

**payout_limit 검증**:
```python
if payout_limit is not None:
    assert "type" in payout_limit
    assert payout_limit["type"] in ["once", "multiple", "unlimited"]
    # ❌ payout_limit_type/value/unit 분산 저장 금지
```

---

## 질병코드 (KCD-7) 원칙 (STEP 6-C 신규)

### KCD-7 Single Source of Truth
**KCD-7 공식 배포본**만이 유일한 질병코드 출처이다.

- 출처: 통계청 KCD-7 (한국표준질병·사인분류) 공식 배포 데이터셋
- 보험사 문서(가입설계서/약관)는 **코드 출처 아님**
- 보험사 문서는 "어떤 코드를 포함/제외하는지"의 **근거(Evidence)** 로만 사용

### 보험 개념 vs 질병코드 분리

**보험 실무 개념**은 질병코드가 **아니다**:
- "유사암 5종", "소액암", "제자리암·경계성종양" = 보험 개념 집합
- 반드시 `disease_code_group` 계층으로 분리
- 보험사별로 정의가 다를 수 있음 (예: 삼성 유사암 ≠ 메리츠 유사암)

**3-tier 데이터 모델** (Constitution v1.0 Amendment):
1. **disease_code_master** (Tier 1)
   - KCD-7 코드 사전 (C00, C73, D09 등)
   - 의학적 분류만 저장 (보험 의미 금지)
   - source = "KCD-7 Official Distribution"

2. **disease_code_group** (Tier 2)
   - 보험 개념 그룹 (유사암, 소액암 등)
   - `insurer` 필드로 보험사별 분리
   - `insurer=NULL`은 **의학적 범위(C00-C97 등)에만** 허용
   - 약관 근거(Evidence) 필수

3. **coverage_disease_scope** (Tier 3)
   - 담보별 질병 범위 정의
   - `include_group_id` / `exclude_group_id` 참조
   - 가입설계서 + 약관 근거 연결

### Slot Schema v1.1.1 (disease_scope)

**disease_scope_raw**:
- 가입설계서 원문 그대로 (예: "유사암 제외", "5종")
- source_confidence = `proposal_confirmed`

**disease_scope_norm**:
- 약관 기반 그룹 참조 (예: `{include_group_id: "CANCER_GENERAL_V1", exclude_group_id: "SIMILAR_CANCER_SAMSUNG_V1"}`)
- source_confidence = `policy_required` (최소)
- NULL = 약관 미처리 상태

### disease_code_group 공통 정의 제한 (강화)

**insurer = NULL 허용 대상**:
- **순수 의학 분류 범위만 가능**
- 예시:
  - ✅ C00-C97 (악성신생물 전체)
  - ✅ D05-D09 (제자리암종 - KCD 분류 자체)
  - ✅ D37-D48 (행동양식 불명 신생물 - KCD 분류 자체)

**insurer = NULL 절대 금지 대상**:
- ❌ 유사암
- ❌ 소액암
- ❌ 재진단암
- ❌ 일반암 (유사암 제외)
- ❌ 제자리암·경계성종양 (보험 약관 정의)
- ❌ 보험 약관에서 정의된 모든 보험 실무 개념

**분리 원칙**:
- 동일 명칭이라도 보험사별 정의가 다르면 **반드시 insurer별 group으로 분리**한다
- 예: 삼성 유사암 ≠ 메리츠 유사암
  - `SIMILAR_CANCER_SAMSUNG_V1` (insurer='Samsung')
  - `SIMILAR_CANCER_MERITZ_V1` (insurer='Meritz')

**절대 금지 개념**:
- ❌ "공통 유사암" 그룹 생성
- ❌ "공통 소액암" 그룹 생성
- ❌ 보험 실무 개념의 insurer=NULL 승격

**허용 사례 (의학 분류)**:
```sql
-- ✅ 허용: KCD 분류 자체
INSERT INTO disease_code_group (group_id, insurer, ...)
VALUES ('CANCER_GENERAL_V1', NULL, ...);  -- C00-C97

-- ❌ 금지: 보험 개념
INSERT INTO disease_code_group (group_id, insurer, ...)
VALUES ('SIMILAR_CANCER_COMMON_V1', NULL, ...);  -- 유사암은 보험 개념
```

### 절대 금지
- ❌ 보험사 문서에서 KCD 코드 생성/추론 (LLM 포함)
- ❌ disease_scope_norm을 코드 배열 JSON으로만 끝내기 (반드시 그룹 참조)
- ❌ insurer=NULL을 보험 실무 개념에 사용 (의학적 KCD 범위만 허용)
- ❌ 동일 명칭 보험 개념을 공통 그룹으로 통합

---

## 금지 사항 (절대)

1. ❌ 기존 inca-rag 코드 복붙 구현
2. ❌ 임시 로직으로 문제 회피
3. ❌ 신정원 코드 우회
4. ❌ synthetic chunk를 비교 결과에 노출
5. ❌ 문서 없는 구현
6. ❌ LLM 기반 coverage_code 추론/매핑
7. ❌ 의미 규칙 코드 하드코딩 (YAML/테이블로 외부화)
8. ❌ 가입설계서에 없는 담보 비교 (Universe Lock 위반)
9. ❌ KCD-7 코드를 보험사 문서에서 생성
10. ❌ disease_scope_norm 추정/자동생성 (약관 근거 필수)

---

## 설계 원칙

### Coverage Universe Lock (STEP 6-C 확정)

**비교 가능 담보 = 가입설계서 담보만**:
- 시스템은 가입설계서(`proposal_coverage_universe`)를 **절대 기준**으로 한다
- 비교 요청 시 반드시 Universe 존재 여부 확인
- Universe에 없으면 → `out_of_universe` (비교 중단, 추정 금지)
- 약관/사업방법서 담보는 참조용 (비교 대상 아님)

**5-State 비교 시스템**:
1. `comparable` - 모든 핵심 슬롯 일치, 갭 없음
2. `comparable_with_gaps` - canonical code 동일, 일부 슬롯 NULL (약관 확인 필요)
3. `non_comparable` - canonical code 다름 또는 호환 불가
4. `unmapped` - Universe에 있으나 Excel 매핑 실패
5. `out_of_universe` - 가입설계서에 없음 (Universe Lock 위반)

### Slot Schema v1.1.1 (STEP 6-C)

**필수 원칙**:
- `mapping_status` = required (MAPPED|UNMAPPED|AMBIGUOUS)
- `canonical_coverage_code` = nullable (MAPPED일 때만 필수)
- unknown은 1급 값 (`null` ≠ `[]` ≠ `0`)
- Evidence 필수 (document_id, page, span_text)

**주요 슬롯**:
- `disease_scope_raw`: 설계서 원문 (String)
- `disease_scope_norm`: 그룹 참조 (Object or NULL)
- `payout_limit`: 통합 객체 `{type, count, period}`
- `currency` / `amount_value` / `payout_amount_unit`: 분리
- `source_confidence`: proposal_confirmed | policy_required | unknown

### 의미 규칙 외부화
- coverage_code ↔ 담보명 / alias (**Excel 기반**)
- coverage_code → domain (암/뇌/심혈관 등)
- domain → 대표 담보 우선순위
- 질의 키워드 → domain 매핑
- 문서 우선순위 (doc_type_priority)

위 규칙은 테이블 또는 설정 파일(YAML)로 관리

### Domain 강제 원칙
- 질의에서 domain 판별 시, 대표 담보는 해당 domain만
- 다른 domain 담보는 대표/연관 모두 ❌

### 메인 담보 우선 원칙
- 동일 domain 내에서 "메인 담보" 우선 선택
- 파생 담보(유사암, 재진단암 등)는 연관 담보로만 노출

### 문서 우선순위 원칙 (용도별)
**비교 Universe** (STEP 6-C):
- 가입설계서만 (Universe Lock)

**정보 검증/보강**:
- 약관 > 사업방법서 > 상품요약서 > 가입설계서
- 이 우선순위도 설정으로 관리

### 결정론적 추출 원칙 (Deterministic Compiler)
**LLM/확률적 방법 금지 영역**:
- ❌ coverage_code 매핑 (Excel만)
- ❌ disease_scope_norm 생성 (약관 + 그룹 참조만)
- ❌ KCD-7 코드 생성 (공식 배포본만)
- ❌ canonical code 추론

**규칙 기반 추출만 허용**:
- ✅ 정규식(regex) 패턴 매칭
- ✅ 결정론적 파싱 로직
- ✅ 테이블/YAML 기반 룰
- ✅ Evidence 기반 추출 (document span 참조)

---

## Git 반영 원칙

- 모든 작업은 반드시 git에 반영
- 커밋 메시지 형식:
  - `feat:` - 새 기능
  - `fix:` - 버그 수정
  - `docs:` - 문서만
  - `refactor:` - 리팩토링
  - `data:` - 데이터 변경

---

## STATUS.md 업데이트 원칙

- 모든 작업 완료 시 STATUS.md 업데이트 (대문자 주의)
- 포함 내용:
  - 수행한 작업명
  - 작업 요약
  - 완료 여부
  - 주요 변경 사항
  - 관련 커밋 해시
  - Constitutional 원칙 준수 여부
  - DoD(Definition of Done) 달성 여부

---

## Constitution v1.0 + Amendment v1.0.1 요약

### Article I: Coverage Universe Lock
- 신정원 통일 담보 코드 = 유일한 기준
- Excel = canonical code 단일 출처
- 가입설계서 = 비교 Universe 단일 출처

### Article II: Deterministic Compiler Principle
- LLM/확률적 추론 금지 (coverage mapping, disease_scope_norm)
- 규칙 기반 추출만 허용 (regex, table, YAML)
- Evidence 필수 (document span reference)

### Article III: Evidence Rule
- 모든 확정값은 document_id, page, span_text 필수
- source_confidence 명시 (proposal_confirmed | policy_required | unknown)

### Article VIII: Disease Code Authority & Group Normalization
- KCD-7 공식 배포본 = 유일한 질병코드 출처
- 보험 개념 ≠ 질병코드 (3-tier 분리)
- insurer=NULL은 의학적 범위만 허용

### Slot Schema v1.1.1
- mapping_status required, canonical_coverage_code nullable
- disease_scope split (raw + norm)
- payout_limit consolidated
- unknown as first-class value

### Comparison States (5-State)
1. comparable
2. comparable_with_gaps
3. non_comparable
4. unmapped
5. out_of_universe

---

## 현행 시스템 상태 (2025-12-24)

**완료된 단계**:
- ✅ STEP 5-A/B/C: FastAPI + Read-Only + Conditions Summary
- ✅ STEP 6-A/B: LLM Ingestion Design + Implementation
- ✅ STEP 6-C: Proposal Universe Lock (E2E Functional)

**현재 브랜치**: `feature/proposal-universe-lock-v1`

**핵심 모듈**:
- `src/proposal_universe/` (parser, mapper, extractor, compare, pipeline)
- `migrations/step6c/` (3-tier disease code schema + universe tables)
- `tests/test_proposal_universe_e2e.py` (Scenarios A/B/C/D)

**다음 작업 예정**:
1. 약관 파이프라인 (disease_scope_norm 채우기)
2. Admin UI (AMBIGUOUS 매핑 수동 해결)
3. Disease code group 관리 인터페이스

---

## 본 문서는 프로젝트 헌법(Constitution)으로 간주한다
## 본 문서에 위배되는 구현은 허용되지 않는다

