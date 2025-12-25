# STEP 3.8-γ Guardrail Rules (안전장치 규칙)

**Date:** 2025-12-25
**Purpose:** 가입설계서 담보 추출 실패를 막는 Guardrail 설계

---

## 1. Fail-Fast Rules (즉시 중단 규칙)

### Rule 1.1: Universe Lock Enforcement
**조건:** 가입설계서에 담보가 존재하지 않음
**시점:** 비교 시작 전 (최우선)
**Action:**
```python
if coverage not in proposal_coverage_universe:
    return {
        "error": "out_of_universe",
        "message": "해당 담보는 가입설계서에 존재하지 않아 비교할 수 없습니다.",
        "http_status": 400,
        "suggestion": "가입설계서에 포함된 담보만 비교 가능합니다."
    }
```
**근거:** Constitution 원칙 1 (Proposal SSOT)

---

### Rule 1.2: Mapping Validation
**조건:** Excel 매핑 실패 (UNMAPPED 또는 AMBIGUOUS)
**시점:** Universe Lock 확인 후
**Action:**
```python
if mapping_status in ['UNMAPPED', 'AMBIGUOUS']:
    return {
        "error": "unmapped",
        "message": "해당 담보명은 매핑되지 않았습니다.",
        "mapping_status": mapping_status,
        "http_status": 400,
        "suggestion": "담보명을 확인하거나 관리자에게 문의하세요."
    }
```
**근거:** Constitution 원칙 5 (Deterministic Extraction)

---

### Rule 1.3: Critical Slots Validation
**조건:** 핵심 축(eligibility, coverage_limit) 누락
**시점:** 매핑 확인 후
**Action:**
```python
critical_axes = ['eligibility', 'coverage_limit']
missing_axes = []

for axis in critical_axes:
    if coverage_data[axis] is None:
        missing_axes.append(axis)

if missing_axes:
    return {
        "error": "critical_data_missing",
        "message": "핵심 비교 정보가 가입설계서에 없습니다.",
        "missing_axes": missing_axes,
        "comparison_state": "comparable_with_gaps",
        "policy_verification_required": true
    }
```
**근거:** Constitution 원칙 2 (Honest Failure)

---

## 2. Integrity Check Rules (정합성 검증 규칙)

### Rule 2.1: Amount Unit Validation
**조건:** 금액 단위 검증
**시점:** 금액 추출 후
**Checks:**
```python
# Check 1: Currency
if currency != 'KRW':
    raise ValueError("KRW 외 통화 불허")

# Check 2: Range
if amount_value < 0:
    raise ValueError("음수 금액 불가")

if amount_value > 100_000_000_000:  # 1000억
    log_warning("1000억 초과 금액 의심 (재확인 필요)")
    require_manual_review = True
```
**근거:** SSOT Schema - integrity_checks.amount_validation

---

### Rule 2.2: O/X Evidence Requirement
**조건:** eligibility 판정 시 evidence 필수
**시점:** O/X 판정 생성 시
**Checks:**
```python
if eligibility_value in ['O', 'X', '△']:
    if evidence is None:
        return {
            "eligibility": None,
            "reason": "evidence_missing",
            "message": "가입설계서에 명시적 근거 없음"
        }

    if eligibility_value == '△' and condition_text is None:
        return {
            "eligibility": None,
            "reason": "condition_missing",
            "message": "조건부 판정은 조건 명시 필수"
        }
```
**근거:** Constitution 원칙 4 (Evidence Mandatory)

---

### Rule 2.3: Disease Scope Normalization Guard
**조건:** disease_scope_norm은 그룹 참조만 허용
**시점:** disease_scope_norm 생성/저장 시
**Checks:**
```python
if disease_scope_norm is not None:
    # Check 1: Must be group reference (not code array)
    if isinstance(disease_scope_norm, list):
        raise ValueError("disease_scope_norm은 코드 배열 금지. 그룹 참조만 허용")

    # Check 2: Must have policy evidence
    if evidence.doc_type != 'POLICY':
        raise ValueError("disease_scope_norm은 약관 근거 필수")

    # Check 3: Group ID must exist
    if not group_exists(disease_scope_norm.get('exclude_group_id')):
        raise ValueError("disease_code_group이 존재하지 않음")
```
**근거:** CLAUDE.md - disease_scope_norm 정책

---

## 3. Insurer Scalability Guards (보험사 확장 안정성)

### Rule 3.1: Confidence Score Threshold
**조건:** 보험사별 데이터 품질 검증
**시점:** 비교 시작 시
**Calculation:**
```python
def calculate_insurer_confidence(insurer: str) -> dict:
    # Metric 1: Mapping success rate
    total_coverages = count_proposal_coverages(insurer)
    mapped_coverages = count_mapped_coverages(insurer)
    mapping_success_rate = mapped_coverages / total_coverages

    # Metric 2: Evidence completeness
    coverages_with_evidence = count_coverages_with_evidence(insurer)
    evidence_completeness = coverages_with_evidence / total_coverages

    # Determine confidence level
    if mapping_success_rate >= 0.9 and evidence_completeness >= 0.8:
        level = "HIGH"
    elif mapping_success_rate >= 0.7 and evidence_completeness >= 0.6:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "insurer": insurer,
        "mapping_success_rate": mapping_success_rate,
        "evidence_completeness": evidence_completeness,
        "confidence_level": level
    }
```

**Action on LOW confidence:**
```python
if confidence_level == "LOW":
    warning = {
        "type": "low_confidence",
        "message": f"{insurer} 데이터 품질이 낮습니다 (매핑 성공률: {rate}%). 비교 결과가 불완전할 수 있습니다.",
        "allow_comparison": True  # 비교는 계속, 경고만 표시
    }
    add_warning_to_response(warning)
```
**근거:** SSOT Schema - insurer_scalability

---

### Rule 3.2: Multi-Insurer Gap Handling
**조건:** 3개 보험사 중 일부만 데이터 존재
**시점:** 3사 비교 시
**Checks:**
```python
def check_multi_insurer_gaps(insurers: List[str], coverage_query: str) -> dict:
    results = {}

    for insurer in insurers:
        coverage = get_from_universe(insurer, coverage_query)

        if coverage is None:
            results[insurer] = {
                "status": "out_of_universe",
                "allow_comparison": False
            }
        elif coverage.mapping_status != 'MAPPED':
            results[insurer] = {
                "status": "unmapped",
                "allow_comparison": False
            }
        else:
            results[insurer] = {
                "status": "ready",
                "allow_comparison": True
            }

    # Decision logic
    ready_count = sum(1 for r in results.values() if r['allow_comparison'])

    if ready_count == 0:
        return {
            "comparison_allowed": False,
            "reason": "no_insurer_ready",
            "message": "모든 보험사에서 비교 불가"
        }
    elif ready_count < len(insurers):
        return {
            "comparison_allowed": True,
            "warning": f"{ready_count}/{len(insurers)} 보험사만 비교 가능",
            "partial_comparison": True
        }
    else:
        return {
            "comparison_allowed": True,
            "full_comparison": True
        }
```

---

## 4. Premium Integration Guards (보험료 처리 안전장치)

### Rule 4.1: Premium API Failure Handling
**조건:** Premium API 실패 시
**시점:** 보험료 조회 시
**Action:**
```python
def handle_premium_failure(error: Exception) -> dict:
    # Log the error
    log_error(f"Premium API failed: {error}")

    # DO NOT stop comparison
    return {
        "premium_available": False,
        "premium_error": {
            "message": "보험료 정보를 가져올 수 없습니다.",
            "reason": str(error),
            "fallback_action": "comparison_continues"
        },
        "comparison_continues": True  # 비교는 계속
    }
```
**근거:** Constitution 원칙 7 (Premium as Auxiliary)

---

### Rule 4.2: Premium Condition Enforcement
**조건:** 보험료 제시 시 조건 필수
**시점:** 보험료 응답 생성 시
**Checks:**
```python
if premium_value is not None:
    required_conditions = ['age', 'gender', 'payment_period']

    for condition in required_conditions:
        if premium_conditions.get(condition) is None:
            raise ValueError(f"보험료 조건 누락: {condition}")

    return {
        "premium": premium_value,
        "conditions": {
            "age": premium_conditions['age'],
            "gender": premium_conditions['gender'],
            "payment_period": premium_conditions['payment_period']
        },
        "disclaimer": "위 조건 기준 보험료입니다. 실제 보험료는 다를 수 있습니다."
    }
```

---

## 5. Response Validation Guards (응답 검증 안전장치)

### Rule 5.1: Prohibited Phrases Validator
**조건:** 응답에 금지 표현 포함 검사
**시점:** 응답 생성 후, 반환 전
**Checks:**
```python
PROHIBITED_PHRASES = [
    "가장 넓은 보장",
    "가장 유리",
    "추천합니다",
    "더 나은 상품",
    "최고의",
    "베스트",
    # ... more patterns
]

def validate_prohibited_phrases(response_text: str) -> dict:
    violations = []

    for phrase in PROHIBITED_PHRASES:
        if phrase in response_text:
            violations.append(phrase)

    if violations:
        return {
            "validation": "FAIL",
            "violations": violations,
            "action": "block_response",
            "error": "응답에 금지된 표현이 포함되어 있습니다."
        }

    return {
        "validation": "PASS"
    }
```
**근거:** Constitution 원칙 8 (Structured Response Only)

---

### Rule 5.2: Evidence Order Validator
**조건:** 응답 내 문서 근거 순서 검증
**시점:** 응답 생성 후
**Checks:**
```python
REQUIRED_DOCUMENT_ORDER = [
    "PROPOSAL",
    "PRODUCT_SUMMARY",
    "BUSINESS_METHOD",
    "POLICY"
]

def validate_evidence_order(evidence_groups: dict) -> dict:
    actual_order = list(evidence_groups.keys())

    if actual_order != REQUIRED_DOCUMENT_ORDER:
        return {
            "validation": "FAIL",
            "expected_order": REQUIRED_DOCUMENT_ORDER,
            "actual_order": actual_order,
            "error": "문서 우선순위 순서 위반"
        }

    # Check: POLICY evidence only when necessary
    if evidence_groups.get('POLICY') and not is_policy_required():
        return {
            "validation": "WARNING",
            "message": "약관 근거가 불필요하게 포함되었습니다."
        }

    return {
        "validation": "PASS"
    }
```
**근거:** STEP 10 - Document Evidence Order

---

## 6. Comparison-Time Guardrails (비교 실행 시점 검증)

### Rule 6.1: Canonical Code Match Requirement
**조건:** 비교 대상 간 canonical_coverage_code 일치 필수
**시점:** 비교 시작 시
**Checks:**
```python
def validate_canonical_code_match(coverages: List[dict]) -> dict:
    codes = [c['canonical_coverage_code'] for c in coverages]
    unique_codes = set(codes)

    if len(unique_codes) > 1:
        return {
            "comparison_state": "non_comparable",
            "reason": "canonical_code_mismatch",
            "details": {
                "codes": dict(zip([c['insurer'] for c in coverages], codes))
            },
            "message": "담보 성격이 달라 비교 불가"
        }

    if None in codes:
        return {
            "comparison_state": "unmapped",
            "reason": "canonical_code_missing"
        }

    return {
        "validation": "PASS",
        "canonical_code": codes[0]
    }
```

---

### Rule 6.2: Slot Completeness Check
**조건:** 비교에 필요한 최소 슬롯 확인
**시점:** 비교 시작 시
**Checks:**
```python
MINIMUM_COMPARABLE_SLOTS = [
    'canonical_coverage_code',
    'event_type',
    'amount_value'
]

def check_slot_completeness(coverage: dict) -> dict:
    missing_slots = []
    gap_slots = []

    for slot in MINIMUM_COMPARABLE_SLOTS:
        if slot not in coverage or coverage[slot] is None:
            missing_slots.append(slot)

    # Check optional but important slots
    IMPORTANT_SLOTS = ['disease_scope_norm', 'payout_limit']
    for slot in IMPORTANT_SLOTS:
        if coverage.get(slot) is None:
            gap_slots.append(slot)

    if missing_slots:
        return {
            "completeness": "INSUFFICIENT",
            "comparison_state": "non_comparable",
            "missing_slots": missing_slots
        }

    if gap_slots:
        return {
            "completeness": "PARTIAL",
            "comparison_state": "comparable_with_gaps",
            "gap_slots": gap_slots,
            "policy_verification_required": True
        }

    return {
        "completeness": "COMPLETE",
        "comparison_state": "comparable"
    }
```

---

## 7. Logging & Monitoring Guards (로깅 및 모니터링)

### Rule 7.1: Extraction Failure Logging
**조건:** 담보 추출 실패 시
**시점:** 모든 추출 시도 시
**Action:**
```python
def log_extraction_failure(
    insurer: str,
    coverage_name: str,
    failure_type: str,
    details: dict
):
    log_entry = {
        "timestamp": now(),
        "insurer": insurer,
        "coverage_name": coverage_name,
        "failure_type": failure_type,  # "no_match", "ambiguous", "extraction_error"
        "details": details,
        "severity": determine_severity(failure_type)
    }

    # Write to monitoring system
    write_to_monitoring_log(log_entry)

    # Alert on critical failures
    if log_entry['severity'] == 'CRITICAL':
        send_alert(log_entry)
```

---

### Rule 7.2: Comparison Quality Metrics
**조건:** 비교 품질 추적
**시점:** 모든 비교 완료 시
**Metrics:**
```python
def track_comparison_quality(comparison_result: dict):
    metrics = {
        "timestamp": now(),
        "comparison_state": comparison_result['comparison_state'],
        "insurers_count": len(comparison_result['insurers']),
        "evidence_completeness": calculate_evidence_completeness(comparison_result),
        "slot_completeness": calculate_slot_completeness(comparison_result),
        "prohibited_phrases_check": comparison_result.get('prohibited_phrases_check'),
        "response_time_ms": comparison_result.get('response_time_ms')
    }

    # Track in time-series DB
    write_to_metrics_db(metrics)

    # Alert on quality degradation
    if metrics['evidence_completeness'] < 0.5:
        send_quality_alert(metrics)
```

---

## 8. Constitutional Violation Detector (헌법 위반 감지)

### Rule 8.1: Universe Lock Violation Detector
**조건:** 약관 기반 비교 대상 생성 감지
**시점:** 담보 선택 시
**Checks:**
```python
def detect_universe_lock_violation(coverage_source: str, coverage_id: str) -> dict:
    # Check: Coverage must come from proposal_coverage_universe
    if not is_from_proposal_universe(coverage_id):
        return {
            "violation": "CRITICAL",
            "rule": "Universe Lock (Constitution Article 1)",
            "message": "가입설계서 외 출처에서 비교 대상 생성 시도",
            "source": coverage_source,
            "action": "BLOCK_IMMEDIATELY"
        }

    return {"violation": None}
```

---

### Rule 8.2: LLM Inference Violation Detector
**조건:** LLM 기반 추론 감지
**시점:** coverage_code 매핑 시
**Checks:**
```python
def detect_llm_inference_violation(mapping_method: str) -> dict:
    ALLOWED_METHODS = [
        'excel_lookup',
        'regex_pattern',
        'table_reference'
    ]

    if mapping_method not in ALLOWED_METHODS:
        return {
            "violation": "CRITICAL",
            "rule": "Deterministic Extraction (Constitution Article 5)",
            "message": f"LLM/확률적 방법 사용 시도: {mapping_method}",
            "action": "BLOCK_IMMEDIATELY"
        }

    return {"violation": None}
```

---

## 9. Summary: Guardrail Execution Order

비교 시스템 실행 시 Guardrail 적용 순서:

```
1. Universe Lock Enforcement (Rule 1.1)
   ↓
2. Mapping Validation (Rule 1.2)
   ↓
3. Critical Slots Validation (Rule 1.3)
   ↓
4. Amount Unit Validation (Rule 2.1)
   ↓
5. O/X Evidence Requirement (Rule 2.2)
   ↓
6. Disease Scope Guard (Rule 2.3)
   ↓
7. Insurer Confidence Check (Rule 3.1)
   ↓
8. Multi-Insurer Gap Handling (Rule 3.2)
   ↓
9. Canonical Code Match (Rule 6.1)
   ↓
10. Slot Completeness Check (Rule 6.2)
    ↓
11. Premium API Handling (Rule 4.1)
    ↓
12. Prohibited Phrases Validation (Rule 5.1)
    ↓
13. Evidence Order Validation (Rule 5.2)
    ↓
14. Constitutional Violation Check (Rules 8.1, 8.2)
    ↓
15. Logging & Metrics (Rules 7.1, 7.2)
```

---

**End of Guardrail Rules v1.0**
