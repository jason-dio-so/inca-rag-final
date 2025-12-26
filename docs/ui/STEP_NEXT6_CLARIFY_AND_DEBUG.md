# STEP NEXT-6: 질문 정제(선택 유도) UI + Deterministic Compiler Debug 탭

## 0. Constitutional Principles (헌법)

본 문서의 모든 구현은 다음 원칙을 준수한다:

1. **Fact-only**: UI는 사실/선택지/상태만 표시
2. **No Recommendation / No Inference**: "추천/우열/동일/차이 없음" 등 판단 문구 생성 금지
3. **Presentation Only**: 질문 정제 UI는 선택 유도만 수행
4. **Deterministic Compiler**: 최종 실행 쿼리는 규칙 기반 컴파일러가 생성하고 재현 가능한 로그 남김
5. **Canonical Coverage Rule**: coverage_code는 신정원 통일코드 정합

---

## 1. 목적

STEP NEXT-5에서 완성된 E2E(ViewModel API → 3-Block Renderer) 위에:

1. 사용자가 모호한 질문을 했을 때 **질문 정제(선택 유도) UI**로 "비교 기준을 확정"
2. 확정된 선택값으로 백엔드가 생성한 **deterministic CompareRequest/Compiler 로그를 Debug 탭으로 제공(기본 숨김)**

---

## 2. 아키텍처

### 2.1. Frontend Flow

```
User Query Input
      ↓
Check Clarification (/compare/clarify)
      ↓
[Clarification Needed?]
      ↓ Yes
ClarifyPanel (Selection UI)
      ↓ User Confirms
Compile Request (/compare/compile)
      ↓
Call ViewModel API (/compare/view-model)
      ↓
Render Result + Debug Panel (toggle)
```

### 2.2. Backend Flow

```
/compare/clarify
   → detect_clarification_needed()
   → Rule-based detection (no LLM)
   → Return: { clarification_needed, required_selections }

/compare/compile
   → compile_request(CompileInput)
   → Apply deterministic rules
   → Return: { compiled_request, compiler_debug }

/compare/view-model
   → Existing ViewModel assembler
   → Return: ViewModel JSON
```

---

## 3. Clarification Trigger Conditions

ClarifyPanel은 다음 조건에서 표시된다:

1. **보험사(Insurer)가 2개 미만**: 최소 2개 필요
2. **담보가 복수 후보로 매핑됨(AMBIGUOUS)**: 사용자가 하나를 선택해야 함
3. **특수 케이스 키워드 감지**:
   - 수술 방식: `다빈치`, `로봇`, `복강경` → `surgery_method` 선택 필요
   - 암 subtype: `제자리암`, `경계성종양`, `유사암` → `cancer_subtypes` 선택 필요
4. **비교 타입 불명확**: `comparison_focus` (amount/definition/condition) 선택 필요

---

## 4. Clarify Panel 선택지

### 4.1. 보험사 선택 (Insurers)
- 표시: 체크박스 (멀티 선택)
- 옵션: SAMSUNG, MERITZ, HANWHA, HYUNDAI, HEUNGKUK
- 최소 요구: 2개

### 4.2. 수술 방식 (Surgery Method)
- 표시: 라디오 버튼 (단일 선택)
- 옵션: `da_vinci`, `robot`, `laparoscopic`, `any`
- Trigger: "다빈치", "로봇", "복강경" 키워드 감지 시

### 4.3. 암 Subtype (Cancer Subtypes)
- 표시: 체크박스 (멀티 선택)
- 옵션: `제자리암`, `경계성종양`, `유사암`, `일반암`
- Trigger: 복수 암 subtype 키워드 감지 시

### 4.4. 비교 초점 (Comparison Focus)
- 표시: 라디오 버튼 (단일 선택)
- 옵션: `amount` (금액), `definition` (정의), `condition` (조건)
- Trigger: 비교 타입이 불명확할 때

---

## 5. Compiler Input/Output Schemas

### 5.1. CompileInput

```typescript
{
  user_query: string;
  selected_insurers: string[];
  selected_comparison_basis?: string;
  options?: {
    surgery_method?: "da_vinci" | "robot" | "laparoscopic" | "any";
    cancer_subtypes?: ("제자리암" | "경계성종양" | "유사암" | "일반암")[];
    comparison_focus?: "amount" | "definition" | "condition";
  };
}
```

### 5.2. CompileOutput

```typescript
{
  compiled_request: {
    query: string;
    insurer_a?: string;
    insurer_b?: string;
    include_policy_evidence: boolean;
  };
  compiler_debug: {
    rule_version: string;
    resolved_coverage_codes?: string[];
    selected_slots: Record<string, any>;
    decision_trace: string[];
    warnings: string[];
  };
}
```

---

## 6. Debug Panel 정책

### 6.1. 기본 상태
- **기본 숨김 (Hidden by default)**
- 토글 버튼으로만 표시/숨김

### 6.2. 표시 내용
1. **Compiler Debug**:
   - `rule_version`: 컴파일러 규칙 버전
   - `resolved_coverage_codes`: 신정원 통일코드 (디버그 전용)
   - `selected_slots`: 정규화된 선택값
   - `decision_trace`: 적용된 규칙 로그
   - `warnings`: 경고 메시지

2. **Compiled Request**:
   - ProposalCompareRequest JSON (pretty print)

### 6.3. 금지 사항 (Debug 탭에서도 적용)
- ❌ "추천/우열/동일/차이 없음" 등 평가성 텍스트
- ❌ LLM 생성 텍스트
- ✅ 사실/로그/상태만 표시

---

## 7. Deterministic Compiler Rules

### 7.1. Coverage Domain Mapping
```python
COVERAGE_DOMAIN_RULES = {
    "암진단비": "cancer",
    "일반암진단비": "cancer",
    "유사암진단비": "cancer",
    "수술비": "surgery",
    "뇌출혈진단비": "brain",
    "급성심근경색진단비": "heart",
}
```

### 7.2. Surgery Method Detection
```python
SURGERY_METHOD_KEYWORDS = {
    "da_vinci": ["다빈치", "da vinci"],
    "robot": ["로봇", "robot"],
    "laparoscopic": ["복강경", "laparoscopic"],
}
```

### 7.3. Cancer Subtype Detection
```python
CANCER_SUBTYPE_KEYWORDS = {
    "제자리암": ["제자리암", "carcinoma in situ"],
    "경계성종양": ["경계성종양", "경계성", "borderline"],
    "유사암": ["유사암", "similar cancer"],
    "일반암": ["일반암", "general cancer"],
}
```

### 7.4. Determinism Guarantee
- 동일한 입력 → 동일한 출력
- 결정 추적(decision trace) 재현 가능
- 규칙 버전 명시 (`v1.0.0-next6`)

---

## 8. 테스트 시나리오 (필수 통과)

### Scenario 1: 다빈치 수술비
```
Query: "다빈치 수술비를 삼성과 현대 비교"
Trigger: surgery_method 선택 필요
Selection: surgery_method = "da_vinci"
Expected: Compiled request with surgery_method in selected_slots
```

### Scenario 2: 경계성종양·제자리암
```
Query: "경계성 종양·제자리암을 한화와 흥국 비교"
Trigger: cancer_subtypes 선택 필요
Selection: cancer_subtypes = ["경계성종양", "제자리암"]
Expected: Compiled request with cancer_subtypes in selected_slots
```

### Scenario 3: 일반 암 진단비
```
Query: "암 진단비 비교"
Trigger: insurers 선택 필요 (또는 comparison basis)
Selection: insurers = ["SAMSUNG", "MERITZ"], basis = "일반암진단비"
Expected: Compiled request with correct insurer_a/insurer_b and query
```

---

## 9. 구현 파일 목록

### Backend
- `apps/api/app/compiler/version.py` - 버전 관리
- `apps/api/app/compiler/rules.py` - 결정론적 규칙
- `apps/api/app/compiler/schemas.py` - Input/Output 스키마
- `apps/api/app/compiler/compiler.py` - 컴파일러 로직
- `apps/api/app/routers/compile.py` - `/compare/compile`, `/compare/clarify` 엔드포인트

### Frontend
- `apps/web/src/lib/clarify/types.ts` - TypeScript 타입
- `apps/web/src/lib/clarify/normalize.ts` - 선택값 정규화
- `apps/web/src/components/clarify/ClarifyPanel.tsx` - 선택 UI
- `apps/web/src/components/debug/DebugPanel.tsx` - 디버그 탭 (토글)
- `apps/web/src/pages/compare-clarify-test.tsx` - 테스트 페이지

### Tests
- `tests/test_compiler_determinism.py` - 결정론 보장 테스트
- `tests/test_compile_endpoint.py` - 엔드포인트 스키마 테스트
- `tests/test_no_llm_dependency.py` - LLM 의존성 없음 검증
- `tests/test_step_next6_scenarios.py` - 3개 필수 시나리오 E2E

---

## 10. 금지 사항 (Hard Ban)

1. ❌ 추천/우열/동일/차이 없음/결론적으로/종합의견 등 평가성 텍스트 생성
2. ❌ LLM 호출로 CompareRequest 생성
3. ❌ Debug 정보의 기본 노출 (반드시 토글)
4. ❌ 임의성/확률적 매핑 (같은 입력 → 다른 출력)
5. ❌ Canonical coverage code 추론/생성 (Excel 단일 출처만)

---

## 11. Definition of Done (DoD)

- [x] Clarify Panel이 Trigger 조건에서만 나타남
- [x] 선택값으로 deterministic compiler가 compiled_request 생성
- [x] Debug 탭 기본 숨김 + 토글 시 JSON 표시
- [x] 3개 시나리오 E2E 동작 확인
- [x] 테스트: determinism + endpoint smoke 통과
- [x] 문서/STATUS 업데이트 + main 커밋/푸시

---

## 12. 향후 확장 가능성

### 12.1. Admin UI Integration
- AMBIGUOUS 매핑 수동 해결 UI
- Disease code group 관리 인터페이스

### 12.2. Advanced Clarification
- 담보 조합 (coverage combinations) 선택
- 가입 연령/기간 조건 선택

### 12.3. Compiler Rule Management
- YAML 기반 규칙 외부화
- 버전별 규칙 롤백 지원

---

## 13. Commit Hash

초기 구현: (작성 중)
문서화 완료: (작성 중)

---

**Constitutional Compliance**: ✅ Verified
- Fact-only: ✅
- No Recommendation: ✅
- Presentation Only: ✅
- Deterministic Compiler: ✅
- No LLM Dependency: ✅
