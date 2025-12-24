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

## 문서 우선순위 원칙 (절대)

### 문서 우선순위 – 절대 규칙

**본 시스템은 약관 중심 시스템이 아니다.**

비교 대상은 오직 가입설계서에서만 정의되며,
상품요약서·사업방법서·약관은 이미 선택된 담보의 의미를 보강하는 보조 문서이다.
약관은 최후의 법적 근거일 뿐, 비교의 출발점이 아니다.

#### 1. 가입설계서 (Proposal)
- **비교 대상(coverage universe)의 유일한 기준 (SSOT)**
- 가입설계서에 존재하지 않는 담보는 비교 대상이 될 수 없다
- Universe Lock의 기준 문서
- **역할:** 무엇을 비교할 것인가 (What to compare)

#### 2. 상품요약서 (Product Summary)
- 고객 관점의 1차 해석 문서
- 담보의 개요, 주요 조건, 예외를 설명
- 법적 판단 근거가 아님
- **역할:** 담보의 일반적 설명 제공

#### 3. 사업방법서 (Business Rules / Method)
- 설계 가능성 및 운영 기준 문서
- 담보 조합, 연령, 기간, 지급 구조의 실무적 근거
- 약관 이전 단계의 제도 문서
- **역할:** 실무 제약 조건 명시

#### 4. 약관 (Policy)
- **최종 법적 판단 근거 문서**
- 분쟁/정의/면책 판단 시에만 사용
- **비교 대상을 결정하거나 확장하지 않는다**
- **역할:** 어떻게 해석할 것인가 (How to interpret)

### 명시적 금지 사항

다음 행위는 헌법 위반이다:

- ❌ 약관을 기준으로 비교 대상을 생성하거나 확장하는 행위
- ❌ 약관 정의만으로 담보 비교를 시작하는 행위
- ❌ 가입설계서보다 약관을 상위 문서로 취급하는 서술
- ❌ "가장 정확한 문서이므로 약관 기준"과 같은 암묵적 우선순위 부여
- ❌ 약관에만 있는 담보를 비교 대상에 포함
- ❌ "policy-first", "약관 중심", "약관 기준 비교"와 같은 표현 사용

### 문서 역할 비유

- **가입설계서 = 지도** (목적지 결정)
- **상품요약서 = 안내서** (개요 설명)
- **사업방법서 = 운영 매뉴얼** (실무 규칙)
- **약관 = 나침반** (방향 해석)

**지도 없이 나침반만으로는 목적지를 정할 수 없다.**

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

※ `coverage_alias`, `canonical_coverage_code`는 시스템 논리 모델의 필드명이며,
   Excel 파일의 실제 컬럼명과 동일함을 전제하지 않는다.

### Excel 스키마 현실 정합성 (Runtime Verified)

- 실제 매핑 Excel 파일은 `data/담보명mapping자료.xlsx` 이다.
- 런타임 검증(Commit 71d363e) 결과, 실제 컬럼 구조는 다음과 같다:
  - 가입설계서 담보명(alias) 컬럼: `담보명(가입설계서)`
  - canonical coverage code 컬럼: `cre_cvr_cd`
  - 보조 컬럼: `ins_cd`, `보험사명`, `신정원코드명`

- 본 문서에서 사용하는 `coverage_alias`, `canonical_coverage_code`는 **개념적 명칭**이며,
  실제 Excel 컬럼명과 1:1로 동일함을 의미하지 않는다.

- 구현 원칙:
  - Excel 컬럼명은 코드에 하드코딩하지 않는다.
  - 다음 "컬럼 매핑 구성"을 통해 연결한다:
    - alias_column = `담보명(가입설계서)`
    - canonical_code_column = `cre_cvr_cd`

- 단일 출처 원칙 유지:
  - canonical coverage code는 **오직 Excel에서만** 온다.
  - LLM/유사도/추론 기반 매핑은 어떤 경우에도 금지한다.

- canonical code 개수 및 alias 개수는 Excel 파일 로드 시점에 산출되며,
  시스템은 해당 값을 런타임 로그 및 검증 리포트에 기록한다.
- 헌법은 숫자를 고정하지 않고, "Excel 단일 출처"만을 고정한다.

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

### 절대 금지
- ❌ 보험사 문서에서 KCD 코드 생성/추론 (LLM 포함)
- ❌ disease_scope_norm을 코드 배열 JSON으로만 끝내기 (반드시 그룹 참조)
- ❌ insurer=NULL을 보험 실무 개념에 남발 (의학적 범위만 허용)

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

