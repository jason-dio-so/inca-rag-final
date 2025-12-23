# STEP 5-C Requirements Definition

**Document Status**: Design Phase (구현 금지)
**Date**: 2025-12-23
**Phase**: STEP 5-C (신규 기능 설계)

---

## 1. 목적 및 범위

### 1.1 목적

STEP 5-B에서 완성된 read-only API 인프라 위에 **보장 조건 요약(conditions_summary)** 기능을 추가한다.

### 1.2 범위

- **IN SCOPE**:
  - `/compare` 응답에 `conditions_summary` 필드 추가
  - Evidence snippet 기반 조건 요약 생성
  - LLM 사용 설계 (개념 수준)
  - OpenAPI 스키마 영향 분석

- **OUT OF SCOPE**:
  - 금액(amount) 요약/계산
  - 보험료(premium) 계산
  - 지급 가능 여부 판정
  - Coverage code 추천/추론
  - DB write 작업

### 1.3 원칙

이 단계는 **설계 문서 작성만** 수행하며, 코드 구현은 금지한다.

---

## 2. 기존 시스템 불변 조건 (Immutable Baseline)

STEP 5-B에서 완료·봉인된 상태이며 **절대 변경 불가**:

### 2.1 헌법적 원칙 (Constitutional Rules)

| 원칙 | 상태 | 검증 방법 |
|------|------|----------|
| Canonical Coverage Code | ✅ SEALED | coverage_standard.coverage_code 단일 진실 |
| Entity-based Filtering | ✅ SEALED | chunk_entity, amount_entity 사용 |
| Compare: is_synthetic=false | ✅ SEALED | SQL HARD RULE + string-level test |
| Amount Bridge: synthetic optional | ✅ SEALED | include_synthetic parameter |
| DB Read-Only | ✅ SEALED | BEGIN READ ONLY transaction |
| KRW ONLY | ✅ SEALED | No foreign currency logic |

### 2.2 기술적 제약

- **DB Access**: Read-only transactions only
- **SQL Templates**: Hard-coded filters (no runtime bypass)
- **Coverage Code**: API uses `coverage_code` (not `coverage_id`)
- **Currency**: Always KRW (amount_unit ignored)
- **Test Coverage**: 24/24 PASS must be maintained

### 2.3 금지된 패턴 (Forbidden Patterns)

다음은 STEP 5-C에서도 절대 금지:

- ❌ `coverage_id` in API parameters
- ❌ Synthetic chunks in compare axis
- ❌ DB INSERT/UPDATE/DELETE/DDL
- ❌ Foreign currency (USD/EUR/JPY/CNY)
- ❌ LLM-based coverage_code inference
- ❌ amount_unit branching logic

---

## 3. conditions_summary 정의

### 3.1 개념

**conditions_summary**는 보험 상품의 보장 조건을 사용자가 이해하기 쉽게 요약한 텍스트이다.

### 3.2 포함 내용 (예시)

- **면책기간**: "가입 후 90일 면책"
- **감액기간**: "2년 내 50% 감액 지급"
- **지급 조건**: "암 진단 확정 시 지급"
- **보장 개시**: "계약일 익일 0시부터"
- **특약/제외**: "피부암 제외", "유사암 20% 지급"

### 3.3 제외 내용 (명시적 금지)

- ❌ 금액 정보 (amount_value/amount_text) → amount_bridge axis 전용
- ❌ 보험료 계산 결과 → STEP 5-D 이후
- ❌ 지급 가능 여부 판정 → 법적 판단 불가
- ❌ Coverage code 추천 → canonical code 위반

### 3.4 데이터 타입

**Type**: `string | null`

**Nullability**: Optional (요약 생성 실패 시 null 허용)

**Encoding**: UTF-8 text

**Max Length**: 권장 2000자 이내

---

## 4. 데이터 입력 소스

### 4.1 Primary Source: Compare Evidence

**Source Query**: `apps/api/app/queries/compare.py::get_compare_evidence()`

```sql
SELECT
  c.chunk_id,
  c.content,        -- 요약 입력 소스
  d.document_type,  -- 우선순위 판단
  ...
FROM public.document d
JOIN public.chunk c ON c.document_id = d.document_id
JOIN public.chunk_entity ce ON ce.chunk_id = c.chunk_id
WHERE d.product_id = %(product_id)s
  AND ce.coverage_code = %(coverage_code)s
  AND c.is_synthetic = false  -- HARD RULE
ORDER BY d.doc_type_priority ASC
```

**Input Characteristics**:
- ✅ Already filtered by coverage_code
- ✅ Non-synthetic only (constitutional guarantee)
- ✅ Ordered by document priority (약관 > 사업방법서 > ...)
- ✅ Read-only query

### 4.2 Document Type Priority

Evidence는 이미 `doc_type_priority` 순으로 정렬됨:
1. 약관 (priority=1) - 최우선
2. 사업방법서 (priority=2)
3. 상품요약서 (priority=3)
4. 가입설계서 (priority=4)

**Strategy**: 우선순위 높은 문서의 evidence를 먼저 사용

### 4.3 Excluded Sources (금지)

다음 데이터는 입력으로 사용 금지:
- ❌ Synthetic chunks (`is_synthetic=true`)
- ❌ amount_entity data (amount_bridge 전용)
- ❌ coverage_alias (매핑 전용, 요약 아님)
- ❌ External web search results

### 4.4 Input Limit

**Max Evidence Count**: 5개 (상위 우선순위 기준)

**Rationale**:
- Token budget 관리
- 응답 속도 유지
- 핵심 조건만 요약

---

## 5. LLM 사용 설계 (개념 수준)

### 5.1 호출 시점

**Option A (권장)**: Query Parameter 기반
```json
POST /compare
{
  "options": {
    "include_conditions_summary": true  // default: false
  }
}
```

**Rationale**:
- 사용자가 명시적으로 요청할 때만 LLM 호출 (비용/속도)
- Default는 null (backward compatibility)

**Option B**: Always-on
- 모든 compare 요청에 자동 생성
- 응답 속도 영향 고려 필요

**권장**: **Option A** (opt-in 방식)

### 5.2 LLM 입력 구성

**Input Structure**:
```
Product: {product_name}
Coverage: {coverage_code} - {coverage_name}

Evidence from highest priority documents:
1. [약관] {snippet_1}
2. [사업방법서] {snippet_2}
...

Task: Summarize insurance coverage conditions in Korean.
Focus on: 면책기간, 감액기간, 지급조건, 보장개시시점, 특약사항
Exclude: 금액정보, 보험료, 지급가능여부 판정
```

**Token Budget**:
- Input: ~2000 tokens (evidence snippets)
- Output: ~500 tokens (요약문)
- Total: ~2500 tokens per request

### 5.3 LLM 출력 포맷

**Format**: Free-form Korean text

**Structure (권장)**:
```
면책기간: {내용}
감액기간: {내용}
지급조건: {내용}
보장개시: {내용}
특약사항: {내용}
```

**Alternative**: Unstructured paragraph (유연성)

### 5.4 LLM 실패 시 Fallback

**Failure Cases**:
- API timeout
- Token limit exceeded
- LLM API error
- Empty evidence

**Fallback Strategy**:
```python
try:
    conditions_summary = generate_summary(evidences)
except Exception:
    conditions_summary = None  # Graceful degradation
```

**Response Behavior**:
- ✅ 200 OK (실패해도 응답은 성공)
- ✅ `conditions_summary: null`
- ✅ `debug.notes`: "Conditions summary generation failed"

### 5.5 LLM 허용/금지 명확화

**LLM 허용 작업**:
- ✅ Evidence snippet 요약 (text summarization)
- ✅ 중복 제거 / 정리 (deduplication)
- ✅ 사용자 친화적 표현 (user-friendly wording)
- ✅ 구조화 (structuring)

**LLM 금지 작업**:
- ❌ Coverage code 추천/추론
- ❌ 금액 추출/계산 (amount_entity가 단일 진실)
- ❌ 지급 가능 여부 판정 (법적 판단)
- ❌ is_synthetic 관련 판단
- ❌ DB write 유도 (alias 생성 등)

---

## 6. OpenAPI 영향 분석

### 6.1 변경 필요 사항

#### CompareOptions Schema
```yaml
CompareOptions:
  type: object
  properties:
    include_conditions_summary:
      type: boolean
      default: false
      description: LLM 기반 보장 조건 요약 생성 여부
    max_evidence_for_summary:
      type: integer
      default: 5
      description: 요약에 사용할 최대 evidence 개수
```

#### CompareItem Schema
```yaml
CompareItem:
  type: object
  properties:
    product_id:
      type: integer
    coverage_code:
      type: string
    coverage_amount:
      type: number
    evidences:
      type: array
      items:
        $ref: "#/components/schemas/EvidenceItem"
    conditions_summary:        # NEW
      type: string
      nullable: true
      description: >
        보장 조건 요약 (면책기간, 감액기간, 지급조건 등).
        include_conditions_summary=true 시에만 생성.
        생성 실패 시 null.
```

### 6.2 Backward Compatibility

**Breaking Change 방지**:
- ✅ `conditions_summary`는 optional (nullable)
- ✅ Default는 null (기존 응답과 동일)
- ✅ Opt-in 방식 (include_conditions_summary=false가 default)

**Migration Path**:
- 기존 클라이언트: 영향 없음 (conditions_summary 무시)
- 신규 클라이언트: opt-in으로 활성화

### 6.3 OpenAPI Diff (초안)

```diff
# openapi/step5_openapi.yaml

CompareOptions:
  type: object
  properties:
    max_evidence:
      type: integer
      default: 5
+   include_conditions_summary:
+     type: boolean
+     default: false
+   max_evidence_for_summary:
+     type: integer
+     default: 5

CompareItem:
  type: object
  properties:
    product_id:
      type: integer
    coverage_code:
      type: string
    coverage_amount:
      type: number
    evidences:
      type: array
+   conditions_summary:
+     type: string
+     nullable: true
```

---

## 7. 금지 사항 (Forbidden List)

### 7.1 헌법 위반 (Constitutional Violations)

다음은 STEP 5-C에서도 절대 금지:

| 금지 항목 | 이유 | 검증 방법 |
|----------|------|----------|
| Synthetic chunks 사용 | Compare axis constitutional rule | SQL string test |
| coverage_id 사용 | Canonical coverage_code only | API schema validation |
| coverage_code 추론 | LLM forbidden zone | Code review |
| DB write 작업 | Read-only enforcement | Transaction test |
| 외화 지원 | KRW-only policy | Currency enum test |
| amount_unit 분기 | KRW-only enforcement | Integration test |

### 7.2 LLM 금지 영역 (LLM Forbidden Zone)

LLM은 다음을 절대 수행해서는 안 됨:

- ❌ **Coverage code inference**: "이 조건은 암진단특약(CANCER_DIAG)입니다" → 금지
- ❌ **Amount calculation**: "600만원 + 200만원 = 800만원" → 금지
- ❌ **Legal judgment**: "이 경우 지급 가능합니다" → 금지
- ❌ **Data correction**: "금액이 틀렸으므로 수정합니다" → 금지
- ❌ **Alias generation**: "이 담보명은 'X'로 매핑됩니다" → 금지

### 7.3 코드 변경 금지 (Immutable Code)

다음 파일은 STEP 5-C에서 변경 금지:

**Queries Layer** (SQL templates):
- `apps/api/app/queries/compare.py` - 조건 요약용 evidence 조회는 기존 쿼리 재사용
- `apps/api/app/queries/evidence.py` - amount_bridge 전용
- `apps/api/app/queries/products.py` - 상품 검색 전용

**DB Layer**:
- `apps/api/app/db.py` - Read-only transaction enforcement

**Policy Layer**:
- `apps/api/app/policy.py` - Axis validation

**Rationale**: 기존 검증된 코드 건드리지 않고 신규 기능만 추가

### 7.4 테스트 회귀 방지 (Test Regression Prevention)

**기존 테스트는 모두 PASS 유지**:
- Contract tests: 8/8
- Integration tests: 16/16
- Total: 24/24

**신규 테스트 추가 시**:
- ✅ conditions_summary=null일 때도 200 OK
- ✅ include_conditions_summary=false 시 null
- ✅ LLM 실패해도 응답 성공

---

## 8. STEP 5-D로 넘어가기 위한 전제 조건

### 8.1 STEP 5-C 완료 조건 (DoD)

| 조건 | 검증 방법 |
|------|----------|
| OpenAPI schema updated | Schema validation |
| conditions_summary field defined | Type checking |
| LLM integration implemented | Functional test |
| Backward compatibility maintained | Existing clients work |
| All tests pass | pytest -q |
| Documentation updated | STATUS.md + validation report |

### 8.2 STEP 5-D 진입 전제

**STEP 5-D (추정 범위)**: Premium calculation + advanced features

**진입 전제**:
1. ✅ STEP 5-C의 conditions_summary가 안정적으로 동작
2. ✅ LLM 비용/속도가 허용 범위 내
3. ✅ 헌법 위반 사례 0건
4. ✅ 기존 테스트 회귀 0건

### 8.3 미해결 결정 사항 (Open Questions)

다음은 구현 전 결정 필요:

1. **LLM Provider**:
   - OpenAI GPT-4?
   - Anthropic Claude?
   - Local model?

2. **Opt-in vs Always-on**:
   - Default false (권장)?
   - Default true?

3. **Caching Strategy**:
   - Product/coverage별 캐싱?
   - TTL?

4. **Rate Limiting**:
   - LLM API 호출 제한?
   - User quota?

**권장**: 이 질문들은 STEP 5-C **구현 단계**에서 답변

---

## 9. 요약 (Summary)

### 9.1 핵심 내용

- **목표**: Compare API에 조건 요약(conditions_summary) 추가
- **입력**: Compare evidence snippets (non-synthetic, 상위 5개)
- **처리**: LLM 기반 요약 (opt-in)
- **출력**: 한글 텍스트 요약 (nullable)
- **제약**: 헌법 위반 금지, 기존 코드 불변

### 9.2 설계 원칙

1. **Backward Compatible**: Optional field, opt-in activation
2. **Fail-Safe**: LLM 실패 시 null (응답은 200 OK)
3. **Constitutional**: 기존 헌법 절대 준수
4. **Minimal Change**: 신규 기능만 추가, 기존 코드 변경 최소화

### 9.3 다음 단계

**STEP 5-C 구현 단계**:
1. OpenAPI schema update
2. CompareOptions + CompareItem 수정
3. LLM integration layer 추가
4. Router에서 conditions_summary 생성
5. Integration test 추가
6. Documentation update

**예상 구현 파일**:
- `openapi/step5_openapi.yaml` (schema)
- `apps/api/app/schemas/compare.py` (Pydantic models)
- `apps/api/app/routers/compare.py` (LLM 호출)
- `apps/api/app/services/llm_summary.py` (NEW - LLM wrapper)
- `tests/integration/test_step5_conditions.py` (NEW)

---

## 10. 설계 승인 체크리스트

이 문서가 구현 가능 상태인지 확인:

- [x] conditions_summary 정의 명확
- [x] 데이터 소스 명시 (compare evidence)
- [x] LLM 사용 범위 명확 (허용/금지)
- [x] OpenAPI 영향 분석 완료
- [x] 헌법 위반 방지 명시
- [x] Backward compatibility 보장
- [x] 실패 시 fallback 전략 정의
- [x] 금지 사항 명시
- [x] DoD 정의

**Status**: ✅ 설계 완료 (구현 준비 완료)

---

**Document Version**: 1.0
**Last Updated**: 2025-12-23
**Next Phase**: STEP 5-C 구현 (별도 지시 대기)
