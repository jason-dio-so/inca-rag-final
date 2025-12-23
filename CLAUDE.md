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

### Coverage 매핑 정책
1. **coverage_alias**
   - 보험사별 담보명 → 신정원 코드 매핑
   - 자동 INSERT 허용
   - 신뢰 가능한 매핑 근거

2. **coverage_standard**
   - 신정원 canonical 사전
   - **report-only**
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

## 금지 사항 (절대)

1. ❌ 기존 inca-rag 코드 복붙 구현
2. ❌ 임시 로직으로 문제 회피
3. ❌ 신정원 코드 우회
4. ❌ synthetic chunk를 비교 결과에 노출
5. ❌ 문서 없는 구현
6. ❌ LLM 기반 coverage_code 추론
7. ❌ 의미 규칙 코드 하드코딩 (YAML/테이블로 외부화)

---

## 설계 원칙

### 의미 규칙 외부화
- coverage_code ↔ 담보명 / alias
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

### 문서 우선순위 원칙
- 약관 > 사업방법서 > 상품요약서 > 가입설계서
- 이 우선순위도 설정으로 관리

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

## status.md 업데이트 원칙

- 모든 작업 완료 시 status.md 업데이트
- 포함 내용:
  - 수행한 작업명
  - 작업 요약
  - 완료 여부
  - 주요 변경 사항
  - 관련 커밋 해시

---

## 본 문서는 프로젝트 헌법(Constitution)으로 간주한다
## 본 문서에 위배되는 구현은 허용되지 않는다
