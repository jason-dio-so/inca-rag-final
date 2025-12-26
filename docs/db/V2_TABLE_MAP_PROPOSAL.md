# V2 Table Mapping: Proposal Extraction → v2 Schema

**Purpose**: 가입설계서 추출 파이프라인 → v2 테이블 매핑 규칙
**Constitution**: CLAUDE.md § 문서 우선순위 원칙 (가입설계서 = Universe SSOT)
**Schema**: docs/db/schema_v2.sql

---

## Extraction Pipeline Overview

```
[가입설계서 PDF]
    ↓
[1단계: Template 식별]
    ↓
[2단계: 앞 2장 테이블 추출] → v2.proposal_coverage
    ↓
[3단계: 담보명 정규화 + Excel 매핑] → v2.proposal_coverage_mapped
    ↓
[4단계: 상세 페이지 근거 추출] → v2.proposal_coverage_detail
    ↓
[5단계: Fallback 문서 연결] (사업방법서/요약서/약관)
```

---

## Stage 1: Template 식별 (Template ID Resolution)

### Input
- 가입설계서 PDF (`file_path`)
- 보험사 코드 (`insurer_code`)
- 상품 내부 코드 (`internal_product_code`)

### Process
1. **Product ID 해결**:
   ```sql
   product_id = v2.resolve_product_id(insurer_code, internal_product_code)
   -- 예: 'SAMSUNG_CANCER_2024'
   ```

2. **Template Fingerprint 생성**:
   - 앞 2장 테이블 구조 해시 (컬럼명 + 행 수 + 주요 필드)
   - SHA256(structure_json) → `fingerprint`

3. **Template ID 생성**:
   ```sql
   template_id = v2.resolve_template_id(
       product_id,
       'proposal',
       version, -- YYYYMM or 보험사 공식 버전
       fingerprint
   )
   -- 예: 'SAMSUNG_CANCER_2024_proposal_202401_a1b2c3d4'
   ```

4. **DB Insert**:
   - `v2.template`: 존재하지 않으면 INSERT
   - `v2.document`: 존재하지 않으면 INSERT

### Output Table
- `v2.template` (template_id, product_id, template_type='proposal', version, fingerprint)
- `v2.document` (document_id, template_id, file_path, file_hash)

### Fallback Rules
- Template 중복 시: 기존 template_id 재사용
- Version 미확인 시: `UNKNOWN` + fingerprint로 구분

---

## Stage 2: 앞 2장 테이블 추출 (Coverage Universe Extraction)

### Input
- 가입설계서 PDF (page 1~2)
- Template ID (from Stage 1)

### Extraction Target
**가입설계서 담보 테이블** (예시):

| 담보명 | 가입금액 | 보장내용 |
|--------|----------|----------|
| 암진단비(일반암) | 1억원 | 최초 1회 |
| 암진단비(유사암) | 1,000만원 | 최초 1회 |
| 뇌출혈진단비 | 5,000만원 | 최초 1회 |

### Extraction Rules (Deterministic)
1. **Table Detection**:
   - 정규식 패턴: `담보명` 컬럼 포함 테이블 감지
   - Page 1~2에서만 추출

2. **Row Extraction**:
   - 각 담보별 1 row = 1 coverage
   - Required fields:
     - `insurer_coverage_name`: 담보명 원문
     - `amount_value`: 가입금액 (숫자 추출)
     - `payout_amount_unit`: 지급 단위 (예: "최초 1회", "매회")
     - `source_page`: 페이지 번호
     - `span_text`: 테이블 행 원문

3. **Normalization**:
   - `normalized_name`: 공백 제거, 괄호 통일, 특수문자 제거
   - 예: "암진단비 (일반암)" → "암진단비일반암"

4. **Content Hash**:
   ```python
   content_hash = SHA256(template_id + page + span_text)
   ```

### Output Table
**v2.proposal_coverage**:
```sql
INSERT INTO v2.proposal_coverage (
    template_id,
    insurer_coverage_name,
    normalized_name,
    currency,
    amount_value,
    payout_amount_unit,
    source_page,
    span_text,
    content_hash
) VALUES (
    'SAMSUNG_CANCER_2024_proposal_202401_a1b2c3d4',
    '암진단비(일반암)',
    '암진단비일반암',
    'KRW',
    100000000,
    '최초 1회',
    1,
    '암진단비(일반암) | 1억원 | 최초 1회',
    'fa83b2...'
);
```

### Extraction Failure Handling
- 테이블 미감지: ERROR (가입설계서 필수)
- 금액 추출 실패: `amount_value = NULL`, `payout_amount_unit = 'unknown'`
- Page 3 이상에 테이블 존재 시: WARNING (검증 필요)

---

## Stage 3: 담보명 매핑 (Excel-based Mapping)

### Input
- `v2.proposal_coverage.normalized_name`
- `insurer_code` (from template → product → insurer)

### Mapping Source
**Excel SSOT**: `data/담보명mapping자료.xlsx`

### Mapping Process
1. **Excel Lookup**:
   ```sql
   SELECT canonical_coverage_code, mapping_status, mapping_evidence
   FROM v2.coverage_name_map
   WHERE insurer_code = {insurer_code}
     AND normalized_alias = {normalized_name}
   LIMIT 1;
   ```

2. **Mapping Status**:
   - `MAPPED`: Excel에서 단일 canonical_coverage_code 확정
   - `UNMAPPED`: Excel에 매칭 없음
   - `AMBIGUOUS`: 여러 canonical_coverage_code 후보 존재

3. **Fallback Rules**:
   - UNMAPPED → `canonical_coverage_code = NULL`, 비교 중단
   - AMBIGUOUS → `canonical_coverage_code = NULL`, 수동 해결 필요

### Output Table
**v2.proposal_coverage_mapped**:
```sql
INSERT INTO v2.proposal_coverage_mapped (
    coverage_id,
    canonical_coverage_code,
    mapping_status,
    mapping_evidence
) VALUES (
    123,
    'CA_DIAG_GENERAL',
    'MAPPED',
    '{"lookup_key": "암진단비일반암", "matched_alias": "암진단비(일반암)", "source": "data/담보명mapping자료.xlsx"}'
);
```

### Absolute Prohibition
- ❌ LLM/유사도 기반 매핑
- ❌ 추정/추론으로 canonical_coverage_code 생성
- ❌ Excel 외 출처 사용

---

## Stage 4: 상세 조건 추출 (Detail Extraction)

### Input
- 가입설계서 Page 3 이후 (상세 조건 페이지)
- `v2.proposal_coverage_mapped.canonical_coverage_code`

### Extraction Target
**담보별 상세 조건** (예시):
- 질병 범위: "유사암 5종 제외"
- 대기기간: "90일"
- 지급 한도: "평생 1회"
- 갱신 조건: "80세까지 자동갱신"

### Extraction Rules (Deterministic)
1. **Page Identification**:
   - canonical_coverage_code별 상세 페이지 탐색
   - Pattern: "{coverage_name}의 보장내용" 또는 "지급 조건"

2. **Field Extraction** (Regex + Table Lookup):
   - `disease_scope_raw`: 원문 그대로 (예: "유사암 제외")
   - `waiting_period_days`: 숫자 추출 (예: "90일" → 90)
   - `payout_limit`: JSON 구조화 (예: `{type: "once", count: 1, period: "lifetime"}`)
   - `treatment_method`: 배열 추출 (예: ["로봇수술", "항암치료"])

3. **Source Confidence**:
   - `proposal_confirmed`: 가입설계서에서 명확히 확인됨
   - `policy_required`: 가입설계서에 없음, 약관 확인 필요
   - `unknown`: 추출 실패

4. **Evidence Capture**:
   ```json
   {
     "document_id": "SAMSUNG_CANCER_2024_proposal_202401_a1b2c3d4_fa83b2ab",
     "page": 5,
     "span_text": "유사암(갑상선암, 기타피부암, 제자리암, 경계성종양, 전립선암) 제외",
     "rule_id": "disease_scope_extract_v1"
   }
   ```

### Output Table
**v2.proposal_coverage_detail**:
```sql
INSERT INTO v2.proposal_coverage_detail (
    mapped_id,
    event_type,
    disease_scope_raw,
    disease_scope_norm,
    waiting_period_days,
    payout_limit,
    source_confidence,
    evidence
) VALUES (
    456,
    'diagnosis',
    '유사암 제외',
    NULL, -- 약관 미처리 시 NULL
    90,
    '{"type": "once", "count": 1, "period": "lifetime"}',
    'proposal_confirmed',
    '{"document_id": "...", "page": 5, "span_text": "...", "rule_id": "disease_scope_extract_v1"}'
);
```

### Extraction Failure Handling
- Field 추출 실패 → NULL (unknown as first-class value)
- `source_confidence = 'unknown'` 명시
- Evidence는 항상 capture (실패 원인 추적용)

---

## Stage 5: Fallback 문서 연결 (Policy/Summary/Business Method)

### When to Use
- `source_confidence = 'policy_required'` (약관 확인 필요)
- `disease_scope_norm = NULL` (질병 범위 미확정)
- `payout_limit = NULL` (지급 한도 미확정)

### Fallback Document Priority
**Constitution § 문서 우선순위 원칙 (정보 검증/보강)**:
1. 약관 (doc_type_priority = 1)
2. 사업방법서 (doc_type_priority = 2)
3. 상품요약서 (doc_type_priority = 3)
4. 가입설계서 (doc_type_priority = 4) ← 이미 시도함

### Fallback Process
1. **Document Lookup**:
   ```sql
   SELECT d.document_id, d.file_path, d.doc_type_priority
   FROM v2.document d
   JOIN v2.template t ON d.template_id = t.template_id
   WHERE t.product_id = {product_id}
     AND d.doc_type_priority < 4 -- 가입설계서 제외
   ORDER BY d.doc_type_priority ASC
   LIMIT 1;
   ```

2. **Extraction Retry**:
   - 약관에서 동일 canonical_coverage_code 조건 탐색
   - 추출 성공 시:
     - `v2.proposal_coverage_detail` UPDATE
     - `source_confidence = 'policy_required'`
     - Evidence에 약관 document_id 기록

3. **Disease Scope Normalization**:
   - 약관에서 질병 범위 확정 시:
     - `disease_scope_norm = {include_group_id, exclude_group_id}`
     - `v2.disease_code_group` 참조 (3-tier model)

### Output Update
```sql
UPDATE v2.proposal_coverage_detail
SET
    disease_scope_norm = '{"include_group_id": "CANCER_GENERAL_V1", "exclude_group_id": "SIMILAR_CANCER_SAMSUNG_V1"}',
    source_confidence = 'policy_required',
    evidence = jsonb_set(evidence, '{fallback_doc_id}', '"SAMSUNG_CANCER_2024_policy_202401_b2c3d4e5_fb94c3bc"')
WHERE mapped_id = 456;
```

### Fallback Failure
- 모든 문서에서 추출 실패 → `disease_scope_norm = NULL` 유지
- 비교 시 `comparable_with_gaps` 상태 (약관 확인 필요)

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Template 식별                                                  │
│ v2.template ← product_id + version + fingerprint                │
│ v2.document ← template_id + file_path + file_hash               │
└───────────────────┬─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. 앞 2장 테이블 추출                                              │
│ v2.proposal_coverage ← insurer_coverage_name + amount + page   │
│ (Universe Lock 절대 기준)                                         │
└───────────────────┬─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Excel 매핑                                                     │
│ v2.proposal_coverage_mapped ← canonical_coverage_code (or NULL) │
│ (mapping_status: MAPPED/UNMAPPED/AMBIGUOUS)                     │
└───────────────────┬─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. 상세 조건 추출 (Page 3+)                                        │
│ v2.proposal_coverage_detail ← disease_scope + payout_limit +   │
│                                waiting_period + evidence        │
└───────────────────┬─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Fallback 문서 연결 (약관/사업방법서/요약서)                       │
│ v2.proposal_coverage_detail UPDATE ← disease_scope_norm +      │
│                                       source_confidence         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Error Handling Contract

| Error Type | Action | Output | Retry |
|------------|--------|--------|-------|
| Template 미식별 | FAIL | ERROR | No |
| 앞 2장 테이블 미감지 | FAIL | ERROR | No |
| 담보명 매핑 실패 (UNMAPPED) | CONTINUE | mapping_status=UNMAPPED | No |
| 상세 조건 추출 실패 | CONTINUE | NULL + source_confidence=unknown | Yes (Fallback 문서) |
| Fallback 문서 미존재 | CONTINUE | NULL 유지 | No |

---

## Validation Checklist

### Stage 1 Validation
- [ ] product_id가 `{insurer_code}_{internal_product_code}` 형식인가?
- [ ] template_id가 `{product_id}_{type}_{version}_{fingerprint[0:8]}` 형식인가?
- [ ] fingerprint가 64자 SHA256인가?

### Stage 2 Validation
- [ ] normalized_name이 공백/괄호/특수문자 제거되었는가?
- [ ] content_hash가 중복 없이 유일한가?
- [ ] source_page가 1~2 범위인가?

### Stage 3 Validation
- [ ] mapping_status가 MAPPED/UNMAPPED/AMBIGUOUS 중 하나인가?
- [ ] MAPPED 시 canonical_coverage_code IS NOT NULL인가?
- [ ] UNMAPPED/AMBIGUOUS 시 canonical_coverage_code IS NULL인가?

### Stage 4 Validation
- [ ] evidence JSONB가 document_id + page + span_text 포함하는가?
- [ ] disease_scope_norm이 NULL 또는 {include_group_id, exclude_group_id} 형식인가?
- [ ] payout_limit이 NULL 또는 {type, count, period} 형식인가?

### Stage 5 Validation
- [ ] source_confidence가 proposal_confirmed/policy_required/unknown 중 하나인가?
- [ ] Fallback 문서 사용 시 evidence에 fallback_doc_id 기록되었는가?

---

## Implementation Notes

### Required Scripts
1. `apps/api/scripts/extract_proposal_template.py` (Stage 1)
2. `apps/api/scripts/extract_proposal_coverage.py` (Stage 2)
3. `apps/api/scripts/map_coverage_excel.py` (Stage 3)
4. `apps/api/scripts/extract_proposal_detail.py` (Stage 4)
5. `apps/api/scripts/fallback_policy_extraction.py` (Stage 5)

### Dependencies
- `data/담보명mapping자료.xlsx` (SSOT for Stage 3)
- `v2.coverage_standard` (신정원 코드 사전)
- `v2.disease_code_group` (질병 범위 그룹)

### Monitoring
- Stage별 성공률 로그
- UNMAPPED/AMBIGUOUS 건수 추적
- Fallback 문서 활용 비율

---

## SSOT Compliance Checklist

### Insurer SSOT
- [ ] insurer_code가 8개 enum 중 하나인가?
- [ ] display_name이 UI 노출용으로 분리되었는가?

### Product SSOT
- [ ] product_id가 insurer_code + internal_product_code 규칙을 따르는가?
- [ ] display_name이 UI 노출용으로 분리되었는가?

### Template SSOT
- [ ] template_id가 product_id + type + version + fingerprint 규칙을 따르는가?
- [ ] fingerprint가 문서 구조 변경을 감지하는가?

### Coverage Mapping SSOT
- [ ] canonical_coverage_code가 Excel 단일 출처에서만 왔는가?
- [ ] LLM/유사도 추론을 사용하지 않았는가?

---

## Next Steps (Post-Implementation)

1. **Schema v2 Migration Script 작성**:
   - `migrations/step_next_z/001_create_v2_schema.sql`
   - Insurer 8개 enum seed
   - coverage_standard 초기 seed (기존 Excel 기반)

2. **Extraction Pipeline 구현**:
   - Stage 1~5 스크립트 개발
   - Smoke test 데이터 준비 (삼성/메리츠 가입설계서 1개씩)

3. **ViewModel 연결**:
   - `apps/api/app/view_model/` 모듈 v2 스키마 연결
   - Comparison API 엔드포인트 수정

4. **Legacy Freeze**:
   - public schema READ-ONLY 설정
   - Legacy 데이터 이관 계획 실행 (LEGACY_FREEZE_PLAN.md)
