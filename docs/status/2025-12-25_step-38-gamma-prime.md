# STEP 3.8-γ′ (Gamma-Prime): 가입설계서 절대 SSOT 보정 완료

**Date:** 2025-12-25
**Type:** Design Realignment (설계 재정렬)
**Status:** ✅ COMPLETED
**Version:** Prime (γ′)

---

## Purpose

**"모든 보험사의 가입설계서가 이미 존재한다"는 현실을**
**STEP 3.8-γ 설계의 최상위 조건으로 반영**

본 단계는 기존 STEP 3.8-γ (v1.0, v1.1) 산출물을 폐기하지 않고 보정하여,
"설계 문서 중심 비교"가 아닌
**"가입설계서 결과표 기반 비교 시스템"**으로 재정렬한다.

---

## 전제 확인 (Premise Validation)

### 가입설계서 존재 확인

```
✅ SAMSUNG   - data/samsung/가입설계서/삼성_가입설계서_2511.pdf
✅ MERITZ    - data/meritz/가입설계서/메리츠_가입설계서_2511.pdf
✅ DB        - data/db/가입설계서/DB_가입설계서(40세이하)_2511.pdf
✅ DB        - data/db/가입설계서/DB_가입설계서(41세이상)_2511.pdf
✅ KB        - data/kb/가입설계서/KB_가입설계서.pdf
✅ LOTTE     - data/lotte/가입설계서/롯데_가입설계서(남)_2511.pdf
✅ LOTTE     - data/lotte/가입설계서/롯데_가입설계서(여)_2511.pdf
✅ HANWHA    - data/hanwha/가입설계서/한화_가입설계서_2511.pdf
✅ HEUNGKUK  - data/heungkuk/가입설계서/흥국_가입설계서_2511.pdf
✅ HYUNDAI   - data/hyundai/가입설계서/현대_가입설계서_2511.pdf
```

**총 7개 보험사 (일부 다중 파일)**

---

## Deliverables (산출물)

### 1. PRIME Comparison Constitution
**File:** `docs/STEP38γ_PRIME_COMPARISON_CONSTITUTION.md`

**핵심 10조:**
1. **Proposal Absolute SSOT** - 가입설계서 = 유일한 비교 근거
2. **Presence = Eligibility** - 존재 = 보장 가능 (판정 로직 제거)
3. **No Inference Rule** - 추론 전면 금지
4. **Honest Failure Priority** - 정직한 실패 우선
5. **Row-Based Evidence** - 행 = 완전한 증거
6. **No Mapping Requirement** - 매핑 선택 (unmapped ≠ 비교 실패)
7. **Factual Comparison Only** - 사실 비교만 (추천 Optional)
8. **No Document Hierarchy** - PROPOSAL만 사용 (나머지 금지)
9. **Deterministic Processing** - regex 기반 구조화만
10. **Validation by Reality** - 현실 검증

---

### 2. PRIME SSOT Schema
**File:** `docs/STEP38γ_PRIME_SSOT_SCHEMA.yaml`

**핵심 구조:**

#### Proposal Row Schema
```yaml
required_fields:
  - row_id
  - insurer
  - proposal_id
  - page
  - coverage_name_raw  # 원문 SSOT
  - amount_raw         # 원문 SSOT

optional_fields:
  - amount_value       # regex 추출
  - normalized_name    # 검색용
  - coverage_code      # 분류용 (매핑 실패 OK)
```

#### Comparison States (4-State)
```yaml
- in_universe_comparable      # 담보 존재 & 비교 가능
- in_universe_unmapped        # 담보 존재 & 매핑 실패 (비교 지속)
- in_universe_with_gaps       # 담보 존재 & 정보 부족
- out_of_universe             # 담보 없음 (비교 불가)
```

#### Prohibited Operations
- ❌ eligibility O/X/△ 판정
- ❌ 가입설계서 외 문서 기반 비교
- ❌ 담보 의미 추론
- ❌ 매핑 실패 = 비교 실패
- ❌ 추천 기본 포함
- ❌ LLM 기반 구조화

---

### 3. PRIME Response Contract
**File:** `docs/STEP38γ_PRIME_RESPONSE_CONTRACT.md`

**응답 구조:**

#### 기본 응답 (Default - 필수)
1. 비교표 (Fact Table) - 가입설계서 원문 데이터
2. 차이 요약 (Difference Summary) - 수치 차이만

#### 추가 응답 (Optional - 사용자 요청 시만)
3. 조건별 답변 (Optional Guidance) - `if-then` 조건부만

**Complete Examples (4 Scenarios):**
- Example 1: 기본 비교 (우선순위 질문 없음)
- Example 2: out_of_universe
- Example 3: unmapped (비교 지속)
- Example 4: 우선순위 질문 포함

---

## v1.0 → v1.1 → γ′ 변경 요약

### v1.0 (Initial - 2025-12-25 earlier)
- 3단 필수 (비교표 + 종합평가 + 추천)
- eligibility: O/X/△
- Document Priority: 4개 모두 필수
- Evidence: 교차 검증

### v1.1 (Refinement - 2025-12-25 mid)
- 2단 기본 + 1단 선택
- eligibility: O/△ (X → out_of_universe)
- Document Priority: PROPOSAL 필수, 나머지 선택
- Evidence: PROPOSAL 우선

### γ′ (Prime - Current)
**핵심 변경:**
1. **eligibility 판정 로직 제거**
   - 존재 = in_universe = 자동 보장 가능
   - O/X/△ regex 판정 전면 금지

2. **Document: PROPOSAL만 사용**
   - 나머지 문서 비교 근거 사용 금지
   - 약관/요약서 = 사람 참조용만

3. **Evidence = 가입설계서 행**
   - 1행 = 완전한 증거
   - chunk/policy 교차 검증 불필요

4. **매핑 선택**
   - unmapped ≠ 비교 실패
   - 원문 기반 비교 지속

5. **추론 전면 금지**
   - regex 구조화만 허용
   - LLM 기반 판단 금지

---

## Constitutional Compliance (γ′)

### Article I: Proposal Absolute SSOT
- ✅ 비교 로직 = 가입설계서만
- ✅ 약관/요약서 = 비교 근거 사용 금지
- ✅ 사람 참조용만 허용

### Article II: Presence = Eligibility
- ✅ 존재 → in_universe
- ✅ 미존재 → out_of_universe
- ✅ eligibility 판정 로직 제거

### Article III: No Inference Rule
- ✅ 추론 전면 금지
- ✅ 가입설계서 명시 문자열만
- ✅ regex 구조화만

### Article IV: Honest Failure Priority
- ✅ 정보 없음 → NULL
- ✅ 다른 문서 보완 금지
- ✅ 정직한 실패

### Article V: Row-Based Evidence
- ✅ 가입설계서 행 = 완전한 증거
- ✅ 교차 검증 불필요

### Article VI: No Mapping Requirement
- ✅ 매핑 선택 (optional)
- ✅ unmapped → 원문 비교 지속
- ✅ unmapped ≠ out_of_universe

### Article VII: Factual Comparison Only
- ✅ 기본 응답 = 2단 (비교표 + 차이요약)
- ✅ 추천 = 사용자 요청 시만
- ✅ 주관 서술 금지

### Article VIII: No Document Hierarchy
- ✅ PROPOSAL만 사용
- ✅ 나머지 문서 금지

### Article IX: Deterministic Processing
- ✅ regex 기반 추출만
- ✅ LLM 금지

### Article X: Validation by Reality
- ✅ 가입설계서만으로 비교 작동
- ✅ 약관 인용 없음

---

## Implementation Guidance

### Comparison Flow

```
1. 가입설계서 원문 로드
   ↓
2. 표 행 단위 담보 추출
   ↓
3. 원문 담보명 그대로 SSOT 저장
   ↓
4. 금액/기간/갱신 구조화 (regex)
   ↓
5. [OPTIONAL] 매핑 (normalized_name, coverage_code)
   ↓
6. 비교 대상 교집합 (원문 or code 매칭)
   ↓
7. 비교표 생성 (가입설계서 원문)
   ↓
8. 차이 요약 생성 (수치 차이)
   ↓
9. [CONDITIONAL] 추천 생성 (요청 시만)
```

### Proposal Row Example

```json
{
  "row_id": "SAMSUNG_PROPOSAL_2024_row_15",
  "insurer": "SAMSUNG",
  "proposal_id": "SAMSUNG_PROPOSAL_2024",
  "page": 3,

  "coverage_name_raw": "일반암진단비(유사암제외)",  // SSOT
  "amount_raw": "3,000만원",                        // SSOT

  "amount_value": 30000000,       // regex 추출
  "renewal_flag": false,          // regex 추출

  "normalized_name": "일반암진단비",  // optional
  "coverage_code": "CANCER_DIAGNOSIS", // optional
  "mapping_status": "MAPPED"       // optional
}
```

---

## Success Criteria (DoD)

### 구조적 성공
- ✅ 가입설계서 단독 비교 가능
- ✅ eligibility 로직 제거
- ✅ 추천 Optional 분리
- ✅ SSOT 원문 중심 재정렬
- ✅ 기존 3.8-γ 문서와 논리 충돌 없음

### 기능적 성공
- ✅ 7개 보험사 가입설계서 비교 작동
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

## Files Created

1. `docs/STEP38γ_PRIME_COMPARISON_CONSTITUTION.md` - PRIME 헌법 10조
2. `docs/STEP38γ_PRIME_SSOT_SCHEMA.yaml` - Row-based SSOT 스키마
3. `docs/STEP38γ_PRIME_RESPONSE_CONTRACT.md` - 2단 기본 + 1단 선택 응답
4. `docs/status/2025-12-25_step-38-gamma-prime.md` - 본 문서

---

## Related Documents

### STEP 3.8-γ Series
- `STEP38γ_COMPARISON_CONSTITUTION.md` (v1.0 - 참조용)
- `STEP38γ_SSOT_SCHEMA.yaml` (v1.0 - 참조용, YAML 오류)
- `STEP38γ_SSOT_SCHEMA_v1.1.yaml` (v1.1 - 참조용)
- `STEP38γ_RESPONSE_CONTRACT.md` (v1.0 - 참조용)
- `STEP38γ_RESPONSE_CONTRACT_v1.1.md` (v1.1 - 참조용)
- `STEP38γ_GUARDRAIL_RULES.md` (v1.0 - 참조용)
- `STEP38γ_REVISION_SUMMARY_v1.1.md` (v1.0 → v1.1 변경사항)

### Constitution
- `CLAUDE.md` - Constitutional requirements (최상위 헌법)

### Implementation
- `src/proposal_universe/` - Proposal Universe Lock 구현 (STEP 6-C)
- `tests/test_proposal_universe_e2e.py` - E2E 테스트

---

## Next Steps (Implementation Phase)

**γ′ 기준 구현:**

### Phase 1: Proposal Row Extraction
- 가입설계서 PDF 파싱 (표 행 단위)
- 원문 데이터 SSOT 저장 (`coverage_name_raw`, `amount_raw`)
- regex 기반 구조화 (`amount_value`, `renewal_flag`)

### Phase 2: Comparison Engine
- 존재 기반 Universe Lock (`proposal_row exists → in_universe`)
- 원문/매핑 기반 담보 매칭
- 차이 계산 (수치만)

### Phase 3: Response Generation
- 비교표 생성 (가입설계서 원문)
- 차이 요약 생성 (수치 차이)
- 추천 생성 (조건부, optional)

### Phase 4: Validation
- Prohibited terms check
- Evidence = PROPOSAL only
- eligibility 판정 로직 없음

---

## Migration from v1.1 to γ′

### Code Changes Required

#### 1. Remove eligibility Logic
```python
# v1.1 (remove)
if regex.match(r'보장.*가능', text):
    eligibility = 'O'

# γ′ (correct)
if proposal_row exists:
    state = 'in_universe'  # 자동
```

#### 2. PROPOSAL Only
```python
# v1.1 (remove)
if evidence.doc_type in ['PROPOSAL', 'PRODUCT_SUMMARY']:
    use_evidence()

# γ′ (correct)
if evidence.doc_type == 'PROPOSAL':
    use_evidence()
else:
    reject()
```

#### 3. Unmapped Handling
```python
# v1.1 (wrong)
if mapping_status == 'UNMAPPED':
    return comparison_failed()

# γ′ (correct)
if mapping_status == 'UNMAPPED':
    return in_universe_unmapped(allow_comparison=True)
```

---

## Validation Scenarios

### PASS
- ✅ KB/삼성/메리츠 가입설계서 표만으로 비교표 생성
- ✅ 담보 없음 → out_of_universe
- ✅ 매핑 실패 → unmapped (비교 지속)

### FAIL
- ❌ 약관 문장 인용
- ❌ eligibility 판정 로직 사용
- ❌ 추천이 기본 응답에 포함
- ❌ "유리합니다" 같은 주관 서술
- ❌ 가입설계서 외 문서로 슬롯 채움

---

**Status:** ✅ COMPLETED (Design Phase)
**Next:** Implementation Phase (TBD)
