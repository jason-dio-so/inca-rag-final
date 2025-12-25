# STEP 3.8-γ v1.0 → v1.1 Revision Summary

**Date:** 2025-12-25
**Revision:** 8가지 핵심 개선사항 반영

---

## 개선사항 목록

### 1. Document Priority 완화
**변경 전 (v1.0):**
- 4개 문서 타입 모두 고정 순서 강제
- Evidence 출력 시 4개 모두 포함 강제

**변경 후 (v1.1):**
- PROPOSAL만 필수, 나머지 선택
- 존재하는 문서만 순서대로 출력
- PROPOSAL 근거만으로 비교 가능하면 다른 문서 불필요

**근거:**
- 가입설계서 기반 비교 시스템의 본질에 충실
- 불필요한 문서 참조 최소화

---

### 2. Response Contract 구조 변경
**변경 전 (v1.0):**
- 3단 구조 (비교표 + 종합평가 + 추천) 모두 필수

**변경 후 (v1.1):**
- 2단 기본 (비교표 + 차이요약) 필수
- 1단 선택 (조건별 답변) - 사용자 우선순위 질문 시에만

**근거:**
- 기본 응답은 사실 비교까지만
- 추천은 명시적 질문에 대한 조건 분기 답변으로 격하

---

### 3. eligibility 축 재정의
**변경 전 (v1.0):**
- O / X / △ 3가지 값
- X = 보장 안됨

**변경 후 (v1.1):**
- O / △ 2가지 값만
- X는 out_of_universe로 처리
- Universe 내 담보는 기본 eligibility = 'O'

**근거:**
- 가입설계서에 담보가 있으면 기본적으로 보장 가능
- 보장 불가(X)는 애초에 가입설계서에 없음 (= out_of_universe)

---

### 4. evidence_order_validator 수정
**변경 전 (v1.0):**
- 4개 문서 타입 순서 고정 검증
- 순서 위반 시 FAIL

**변경 후 (v1.1):**
- 존재하는 문서만 순서대로 검증
- rule: "include_only_if_exists"
- PROPOSAL만 required: true

**근거:**
- Document Priority 완화에 따른 검증 로직 수정

---

### 5. fail_fast step_5 모순 수정
**변경 전 (v1.0):**
```yaml
step_5_evidence_check:
  check: "evidence.document_id IS NOT NULL"
  fail_action:
    log_warning: true
    continue_comparison: true  # ← 모순: evidence 없어도 계속?
```

**변경 후 (v1.1):**
```yaml
step_5_evidence_check:
  description: "PROPOSAL 근거 존재 확인"
  check: "evidence.doc_type = 'PROPOSAL' AND evidence.document_id IS NOT NULL"
  fail_action:
    state: "comparable_with_gaps"
    set_affected_axis_to_null: true
    policy_verification_required: true
    message: "가입설계서 근거 부족 (해당 축 NULL 처리)"
```

**근거:**
- Evidence 없으면 해당 축 NULL + comparable_with_gaps 처리
- "경고만 하고 계속"은 정직한 실패 원칙 위반

---

### 6. normalized_name required 제거
**변경 전 (v1.0):**
```yaml
required_fields:
  - universe_id
  - insurer
  - insurer_coverage_name
  - normalized_name  # ← required
```

**변경 후 (v1.1):**
```yaml
required_fields:
  - universe_id
  - insurer
  - insurer_coverage_name  # 원문 담보명 (SSOT)
  - mapping_status
  - canonical_coverage_code

optional_fields:
  - normalized_name  # 검색용, required 아님
```

**근거:**
- 원문 담보명(insurer_coverage_name)이 SSOT
- normalized_name은 검색 보조 필드일 뿐

---

### 7. LOW confidence 처리 강화
**변경 전 (v1.0):**
```yaml
low_confidence_message:
  action: "display_warning"
  allow_comparison: true  # 경고만, 제한 없음
```

**변경 후 (v1.1):**
```yaml
low_confidence_policy:
  action: "partial_comparison_restriction"
  rules:
    - if: "confidence_level = 'LOW'"
      then:
        display_warning: true
        restrict_comparison: true
        restriction_detail: "해당 보험사는 비교표에 포함하되, 차이요약/조건별답변에서 제외"
```

**근거:**
- LOW 품질 데이터로 "평가/추천" 생성은 위험
- 비교표는 표시하되, 요약/답변에서는 제외

---

### 8. Rule-based Summary 용어/역할 축소
**변경 전 (v1.0):**
- 명칭: "Rule-based Summary", "종합평가"
- 역할: 4개 dimension "평가"

**변경 후 (v1.1):**
- 명칭: "Factual Deltas Summary", "차이요약"
- 역할: 수치 차이 사실만 제시
- 금지: "평가", "우수", "양호", "점수" 등 평가 용어 전부

**근거:**
- "평가"는 주관적 판단으로 오인 가능
- "차이 요약"은 객관적 사실 진술

---

## 변경 파일 목록

### 신규 파일 (v1.1)
1. `STEP38γ_SSOT_SCHEMA_v1.1.yaml` - YAML 오류 수정 + 8가지 개선
2. `STEP38γ_RESPONSE_CONTRACT_v1.1.md` - 2단 기본 + 1단 선택 구조
3. `STEP38γ_REVISION_SUMMARY_v1.1.md` - 본 문서

### 기존 파일 (v1.0 - 참조용 유지)
- `STEP38γ_COMPARISON_CONSTITUTION.md` - 헌법 문서 (v1.0 유지)
- `STEP38γ_GUARDRAIL_RULES.md` - Guardrail 규칙 (v1.0 유지, 차후 v1.1 반영 예정)
- `STEP38γ_SSOT_SCHEMA.yaml` - v1.0 (YAML 오류 있음, 참조만)
- `STEP38γ_RESPONSE_CONTRACT.md` - v1.0 (3단 필수 구조, 참조만)

---

## Constitutional Compliance (v1.1)

### 변경 없음 (유지)
- ✅ Proposal SSOT (가입설계서 단일 진실 출처)
- ✅ Honest Failure (정직한 실패 우선)
- ✅ Fixed Comparison Axes (5 axes 고정)
- ✅ Deterministic Extraction (LLM 금지)
- ✅ 5-State Comparison System
- ✅ Premium as Auxiliary (API 실패 시 비교 지속)
- ✅ Fail-Fast Validation

### 강화/명확화
- ✅ Evidence Mandatory (PROPOSAL 필수, 나머지 선택으로 명확화)
- ✅ Structured Response Only (평가 용어 금지 강화)
- ✅ Document Priority (완화: PROPOSAL 필수, 나머지 선택)

---

## Migration Guide (v1.0 → v1.1)

### 구현 시 주의사항

#### 1. Evidence 처리
```python
# v1.0 (잘못된 예)
if evidence is None:
    log_warning("Evidence missing")
    continue  # ← 경고만 하고 계속

# v1.1 (올바른 예)
if evidence is None or evidence.doc_type != 'PROPOSAL':
    axis_value = None
    comparison_state = 'comparable_with_gaps'
    gap_slots.append(axis_name)
```

#### 2. Response 구조
```python
# v1.0 (잘못된 예)
response = {
    "comparison_table": {...},
    "rule_based_summary": {...},  # 항상 포함
    "conditional_guidance": {...}  # 항상 포함
}

# v1.1 (올바른 예)
response = {
    "comparison_table": {...},  # 필수
    "factual_deltas_summary": {...},  # 필수 (용어 변경)
    "optional_guidance": user_asked_priority ? {...} : null  # 조건부
}
```

#### 3. Confidence Level 처리
```python
# v1.0 (잘못된 예)
if confidence == 'LOW':
    display_warning("Low quality data")
    # 비교는 계속 (제한 없음)

# v1.1 (올바른 예)
if confidence == 'LOW':
    display_warning("Low quality data")
    include_in_fact_table = True  # 비교표는 포함
    include_in_deltas_summary = False  # 차이요약에서 제외
    include_in_optional_guidance = False  # 조건별답변에서 제외
```

---

## Next Steps

### v1.1 적용 대상
1. Constitution 문서 업데이트 (v1.1 원칙 반영)
2. Guardrail Rules 업데이트 (v1.1 검증 로직 반영)
3. Implementation Guide 작성 (v1.1 기준)

### v1.0 처리
- 참조용으로 유지 (삭제하지 않음)
- v1.1과 비교하여 변경사항 확인 용도

---

**End of Revision Summary v1.1**
