# STEP 9: 가입설계서 중심 3사 비교 실전 고정

**Date:** 2025-12-24
**Base:** STEP 8 (feature/step8-multi-insurer-policy-scope)
**Purpose:** 가입설계서 기반 비교 시스템을 실전 비교 응답 수준까지 고정

---

## 0. Constitutional Requirement (절대 원칙)

### 가입설계서 중심 비교 Universe (SSOT)

**비교 대상 = 가입설계서에 있는 담보만**

1. **가입설계서 (Proposal)** → `proposal_coverage_universe` (비교 대상 SSOT)
   - 비교 가능 담보는 가입설계서에 있는 담보만
   - Universe Lock의 절대 기준
   - 약관/사업방법서는 Universe를 **확장하지 않음**

2. **약관 / 상품요약서 / 사업방법서** → Evidence Enrichment only
   - `disease_scope_norm` 채우기 (약관 정의 근거)
   - `coverage_condition` 보강
   - `exclusion_reason` 명시
   - **가입설계서 담보를 "해석"할 뿐, "선정"하지 않음**

### Why 약관을 보지만 약관 중심이 아닌가?

**문서 역할 분리:**
- 가입설계서: "무엇을 비교할 것인가" (What to compare)
- 약관: "어떻게 해석할 것인가" (How to interpret)

**비유:**
- 가입설계서 = 지도 (목적지 결정)
- 약관 = 나침반 (방향 해석)
- 지도 없이 나침반만으로는 목적지를 정할 수 없음

**STEP 9에서 약관의 역할:**
- 가입설계서에 "유사암 제외" 라고만 쓰여있을 때
- 약관에서 "유사암 = C73 갑상선암 + C44 피부암" 정의 확인
- **But, 약관에 다른 담보가 있어도 가입설계서에 없으면 비교 안 함**

---

## 1. Problem Statement

### Current State (STEP 8)
- Multi-insurer registry pattern working
- Multi-party overlap detection implemented
- Explainable reasons generated
- **But: No E2E comparison from proposal to response**

### STEP 9 Goal
- **가입설계서 기준 3사 비교를 E2E로 고정**
- 약관 기반 disease_scope_norm 보강 실전 적용
- 구조화 응답 스키마 고정
- 판단/추천 문구 완전 제거

---

## 2. Coverage Selection (공통 비교 축)

### Selection Criteria
1. ✅ 가입설계서에 3사 모두 존재
2. ✅ canonical coverage_code 동일
3. ✅ disease scope 해석이 필요한 담보 (유사암/소액암 계열)

### Selected Coverage (Example for STEP 9 MVP)

**Coverage Name:** 일반암진단비 (General Cancer Diagnosis)

| Insurer | Proposal Coverage Name | Canonical Code | Universe ID |
|---------|----------------------|----------------|-------------|
| SAMSUNG | 일반암진단비 | CANCER_DIAGNOSIS | (from proposal_coverage_universe) |
| MERITZ | 일반암진단비 | CANCER_DIAGNOSIS | (from proposal_coverage_universe) |
| DB | 일반암진단비 | CANCER_DIAGNOSIS | (from proposal_coverage_universe) |

**Disease Scope Interpretation Needed:**
- All 3 insurers exclude "유사암" (Similar Cancer)
- But each insurer defines "유사암" differently in 약관
- Need to extract disease_scope_norm from policy documents

---

## 3. Disease Scope Enrichment (약관 기반 Evidence Only)

### 3.1 Workflow

For each of 3 insurers:

1. **Extract from 약관** (deterministic regex)
   - Find "유사암의 정의" section
   - Extract disease codes (C73, C44, etc.)
   - Capture evidence span

2. **Create disease_code_group**
   - `group_id`: `SIMILAR_CANCER_{INSURER}_V1`
   - `insurer`: SAMSUNG / MERITZ / DB
   - `basis_doc_id`: Policy document ID
   - `basis_span`: Evidence text

3. **Add disease_code_group_member** (TEST ONLY subset)
   - KCD-7 codes: C73, C44 (minimum)
   - FK validation against disease_code_master

4. **Create coverage_disease_scope**
   - Links proposal coverage to disease groups
   - Evidence required (source_doc_id, page, span_text)

5. **Update proposal_coverage_slots.disease_scope_norm**
   ```json
   {
     "include_group_id": "GENERAL_CANCER_C00_C97",
     "exclude_group_id": "SIMILAR_CANCER_SAMSUNG_V1"
   }
   ```

### 3.2 Evidence Requirements (Mandatory)

**Every step must include:**
- `document_id`: Policy document identifier
- `page`: Page number
- `span_text`: Extracted text span

**Missing evidence → Immediate failure**

---

## 4. Comparison Logic (3-Insurer Simultaneous)

### 4.1 Multi-Party Overlap Detection

Using STEP 8 implementation:

```python
from src.policy_scope.comparison.overlap import (
    InsurerDiseaseScope,
    aggregate_multi_party_overlap
)

scopes = [
    InsurerDiseaseScope(insurer='SAMSUNG', ...),
    InsurerDiseaseScope(insurer='MERITZ', ...),
    InsurerDiseaseScope(insurer='DB', ...),
]

overlap_state = aggregate_multi_party_overlap(scopes)
# → FULL_MATCH | PARTIAL_OVERLAP | NO_OVERLAP | UNKNOWN
```

### 4.2 Comparison State Mapping

| Overlap State | Comparison State | Reason Code |
|--------------|------------------|-------------|
| FULL_MATCH | comparable | disease_scope_identical |
| PARTIAL_OVERLAP | comparable_with_gaps | disease_scope_partial_overlap |
| NO_OVERLAP | non_comparable | disease_scope_multi_insurer_conflict |
| UNKNOWN | comparable_with_gaps | disease_scope_policy_required |

---

## 5. Comparison Response Schema (구조화 응답 고정)

### 5.1 Response Structure

**자연어 요약이 아닌 구조화 응답만 허용**

```json
{
  "comparison_state": "comparable_with_gaps",
  "coverage_code": "CANCER_DIAGNOSIS",
  "coverage_name": "일반암진단비",
  "insurers": [
    {
      "insurer": "SAMSUNG",
      "disease_scope_norm": {
        "include_group_id": "GENERAL_CANCER_C00_C97",
        "exclude_group_id": "SIMILAR_CANCER_SAMSUNG_V1"
      },
      "evidence": {
        "basis_doc_id": "SAMSUNG_POLICY_2024",
        "basis_page": 12,
        "basis_span": "유사암이라 함은 갑상선암(C73), 기타피부암(C44)..."
      }
    },
    {
      "insurer": "MERITZ",
      "disease_scope_norm": {
        "include_group_id": "GENERAL_CANCER_C00_C97",
        "exclude_group_id": "SIMILAR_CANCER_MERITZ_V1"
      },
      "evidence": {
        "basis_doc_id": "MERITZ_POLICY_2024",
        "basis_page": 9,
        "basis_span": "유사암: 갑상선암(C73)..."
      }
    },
    {
      "insurer": "DB",
      "disease_scope_norm": null,
      "evidence": null
    }
  ],
  "comparison_reason": {
    "reason_code": "disease_scope_partial_overlap",
    "summary_ko": "삼성과 메리츠의 유사암 정의에 교집합이 있으나, DB의 정의는 약관에서 추출되지 않았습니다. 약관 확인이 필요합니다.",
    "evidence_refs": [
      {"insurer": "SAMSUNG", "doc_id": "SAMSUNG_POLICY_2024", "page": 12},
      {"insurer": "MERITZ", "doc_id": "MERITZ_POLICY_2024", "page": 9}
    ]
  },
  "prohibited_phrases_check": "PASS"
}
```

### 5.2 Prohibited Phrases (절대 금지)

**Response에 절대 포함 금지:**
- ❌ "가장 넓은 보장"
- ❌ "가장 유리함"
- ❌ "추천합니다"
- ❌ "더 나은 상품"
- ❌ Any value judgment or recommendation

**Only factual statements allowed:**
- ✅ "삼성과 메리츠는 유사암 정의에 교집합이 있습니다"
- ✅ "DB의 유사암 정의는 약관에서 추출되지 않았습니다"
- ✅ "약관 확인이 필요합니다"

---

## 6. Implementation Plan

### 6.1 Phase A: Coverage Selection & Preparation
1. Identify common coverage in 3 proposals
2. Document coverage details (canonical_code, universe_id)
3. Verify coverage exists in all 3 proposal_coverage_universe

### 6.2 Phase B: Disease Scope Enrichment
1. Extract 유사암 definitions from 3 policies (deterministic regex)
2. Create disease_code_group (3 groups, 1 per insurer)
3. Add disease_code_group_member (TEST ONLY KCD-7 subset)
4. Create coverage_disease_scope (3 scopes)
5. Update proposal_coverage_slots.disease_scope_norm (3 slots)

### 6.3 Phase C: Comparison Response Generation
1. Load disease scopes for 3 insurers
2. Compute multi-party overlap state
3. Generate structured response
4. Validate prohibited phrases
5. Include evidence references

---

## 7. Testing Requirements (Mandatory)

### 7.1 E2E Integration Test

**Test Name:** `test_step9_three_insurer_proposal_based_comparison`

**Validation Checklist:**
1. ✅ Comparison target is from proposal_coverage_universe
2. ✅ Policy documents did NOT expand Universe
3. ✅ disease_scope_norm is group references (not raw code arrays)
4. ✅ Missing evidence causes failure
5. ✅ 3-insurer comparison returns single comparison_state
6. ✅ Response schema matches specification
7. ✅ NO prohibited phrases in response
8. ✅ Evidence references included

### 7.2 Test Scenarios

**Scenario 1: FULL_MATCH (3 insurers identical)**
- All 3 insurers exclude same 유사암 codes
- Expected: comparable, disease_scope_identical

**Scenario 2: PARTIAL_OVERLAP (2 overlap, 1 differs)**
- Samsung and Meritz overlap on C73
- DB has different definition
- Expected: comparable_with_gaps, disease_scope_partial_overlap

**Scenario 3: UNKNOWN (1 insurer NULL)**
- Samsung and Meritz defined
- DB disease_scope_norm is NULL
- Expected: comparable_with_gaps, disease_scope_policy_required

---

## 8. Documentation Requirements

### 8.1 STATUS.md Update

**Add STEP 9 section:**
- Purpose
- Selected coverage
- Disease scope enrichment results
- Comparison response schema
- Test results
- Constitutional compliance checklist

### 8.2 Design Document (this file)

**Included:**
- ✅ Document hierarchy (가입설계서 → 약관)
- ✅ "Why 약관을 보지만 약관 중심이 아닌지" explanation
- ✅ Comparison response schema
- ✅ Prohibited phrases list
- ✅ Evidence requirements

---

## 9. Definition of Done

- ✅ 1 common coverage selected from 3 proposals
- ✅ Disease scope enrichment completed for 3 insurers
- ✅ Comparison response generated E2E
- ✅ Response schema fixed and validated
- ✅ NO prohibited phrases (validated)
- ✅ All tests PASS
- ✅ STATUS.md updated
- ✅ Committed and pushed to GitHub

---

## 10. Success Criteria

**Structural Integrity:**
- ✅ 가입설계서 = 비교 대상 SSOT (no Universe expansion from policy)
- ✅ 약관 = Evidence Enrichment only
- ✅ Comparison response is structured (not free-form text)

**Functional Completeness:**
- ✅ 3-insurer comparison works E2E
- ✅ Multi-party overlap detection returns single state
- ✅ Evidence included in all steps

**Constitutional Compliance:**
- ✅ NO value judgments or recommendations
- ✅ Only factual differences stated
- ✅ Prohibited phrases blocked and validated

---

## References

- STEP 7: Universe Lock + Policy Scope Pipeline v1
- STEP 8: Multi-Insurer Policy Scope Expansion
- CLAUDE.md: Constitutional requirements
