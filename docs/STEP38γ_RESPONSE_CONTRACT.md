# STEP 3.8-γ Response Contract (고객 응답 계약)

**Date:** 2025-12-25
**Purpose:** 비교표 + 종합평가 + 추천 구조 정의

---

## 1. Response Contract Overview

고객이 요구한 응답 구조는 **3단 구조**:

```
┌─────────────────────────────────────┐
│  1. 비교 표 (Fact Table)            │  ← 사실만 (O/X/△/금액)
├─────────────────────────────────────┤
│  2. 종합 평가 (Rule-based Summary)  │  ← 사전 정의 규칙
├─────────────────────────────────────┤
│  3. 추천 (Conditional Guidance)     │  ← 조건 분기형
└─────────────────────────────────────┘
```

**절대 원칙:**
- ❌ 자연어 주관 평가 금지
- ❌ "A가 더 좋다" 식 판단 금지
- ✅ 구조화 데이터만 허용
- ✅ 근거(evidence) 필수

---

## 2. Part 1: 비교 표 (Fact Table)

### 2.1 구조 정의

```json
{
  "comparison_table": {
    "coverage_name": "일반암진단비",
    "canonical_coverage_code": "CANCER_DIAGNOSIS",
    "insurers": ["SAMSUNG", "MERITZ", "DB"],
    "axes": {
      "eligibility": {
        "SAMSUNG": {
          "value": "O",
          "evidence": {
            "document_id": "SAMSUNG_PROPOSAL_2024",
            "page": 3,
            "span_text": "일반암진단비 보장"
          }
        },
        "MERITZ": {
          "value": "O",
          "evidence": {...}
        },
        "DB": {
          "value": "O",
          "evidence": {...}
        }
      },
      "coverage_limit": {
        "SAMSUNG": {
          "value": 30000000,
          "display": "3,000만원",
          "evidence": {...}
        },
        "MERITZ": {
          "value": 30000000,
          "display": "3,000만원",
          "evidence": {...}
        },
        "DB": {
          "value": 60000000,
          "display": "6,000만원",
          "evidence": {...}
        }
      },
      "coverage_start": {
        "SAMSUNG": {
          "type": "waiting_period",
          "waiting_days": 90,
          "display": "보장개시일 90일 후",
          "evidence": {...}
        },
        "MERITZ": {
          "type": "waiting_period",
          "waiting_days": 90,
          "display": "보장개시일 90일 후",
          "evidence": {...}
        },
        "DB": {
          "type": "immediate",
          "waiting_days": 0,
          "display": "보장개시일부터",
          "evidence": {...}
        }
      },
      "exclusions": {
        "SAMSUNG": {
          "reduction_periods": [
            {
              "period": "1년",
              "rate": 0.5,
              "display": "1년 50% 감액"
            }
          ],
          "exclusion_diseases": ["유사암"],
          "evidence": {...}
        },
        "MERITZ": {
          "reduction_periods": [],
          "exclusion_diseases": ["유사암"],
          "evidence": {...}
        },
        "DB": {
          "reduction_periods": [],
          "exclusion_diseases": ["유사암"],
          "evidence": {...}
        }
      },
      "enrollment_condition": {
        "SAMSUNG": {
          "age_range": "20~60세",
          "coverage_period": "80세 만기",
          "payment_period": "20년납",
          "evidence": {...}
        },
        "MERITZ": {
          "age_range": "20~65세",
          "coverage_period": "80세 만기",
          "payment_period": "20년납",
          "evidence": {...}
        },
        "DB": {
          "age_range": "20~60세",
          "coverage_period": "80세 만기",
          "payment_period": "20년납",
          "evidence": {...}
        }
      }
    }
  }
}
```

### 2.2 Fact Table 규칙

**허용 값:**
- `eligibility`: "O" | "X" | "△" (조건 명시 필수)
- `coverage_limit`: integer (KRW) + display (formatted string)
- `coverage_start`: type + waiting_days + display
- `exclusions`: reduction_periods (array) + exclusion_diseases (array)
- `enrollment_condition`: structured object

**금지 표현:**
- ❌ "우수함", "부족함", "보통"
- ❌ "추천", "유리", "불리"
- ❌ 감정 표현 전부

**NULL 처리:**
- `null` = 정보 없음 (가입설계서에 명시 없음)
- `[]` = 명시적 없음 (예: "감액 없음")
- `0` = 명시적 0 (예: "보장개시일부터")

---

## 3. Part 2: 종합 평가 (Rule-based Summary)

### 3.1 구조 정의

```json
{
  "rule_based_summary": {
    "coverage_name": "일반암진단비",
    "evaluated_dimensions": [
      {
        "dimension": "coverage_amount",
        "rule": "max_amount_insurer",
        "result": {
          "insurer": "DB",
          "value": 60000000,
          "display": "6,000만원",
          "comparison": {
            "SAMSUNG": "50% 낮음",
            "MERITZ": "50% 낮음"
          }
        }
      },
      {
        "dimension": "coverage_start_speed",
        "rule": "shortest_waiting_period",
        "result": {
          "insurer": "DB",
          "waiting_days": 0,
          "display": "즉시 보장",
          "comparison": {
            "SAMSUNG": "90일 더 빠름",
            "MERITZ": "90일 더 빠름"
          }
        }
      },
      {
        "dimension": "reduction_burden",
        "rule": "no_reduction_insurer",
        "result": {
          "insurers": ["MERITZ", "DB"],
          "display": "감액 없음",
          "comparison": {
            "SAMSUNG": "1년 50% 감액 있음"
          }
        }
      },
      {
        "dimension": "enrollment_flexibility",
        "rule": "widest_age_range",
        "result": {
          "insurer": "MERITZ",
          "age_range": "20~65세",
          "display": "가입 가능 연령 최대",
          "comparison": {
            "SAMSUNG": "5년 좁음",
            "DB": "5년 좁음"
          }
        }
      }
    ],
    "prohibited_phrases_check": "PASS"
  }
}
```

### 3.2 Rule-based Evaluation Rules

**사전 정의 규칙 (Rule Registry):**

```yaml
rule_registry:
  coverage_amount:
    rule_id: "max_amount_insurer"
    logic: "SELECT insurer WHERE amount_value = MAX(amount_value)"
    output_template: "{insurer}: {display}"
    comparison_template: "{other_insurer}: {percentage}% 낮음/높음"

  coverage_start_speed:
    rule_id: "shortest_waiting_period"
    logic: "SELECT insurer WHERE waiting_days = MIN(waiting_days)"
    output_template: "{insurer}: {waiting_days}일 대기"
    comparison_template: "{other_insurer}: {days_diff}일 더 빠름/느림"

  reduction_burden:
    rule_id: "no_reduction_insurer"
    logic: "SELECT insurer WHERE reduction_periods = []"
    output_template: "{insurer}: 감액 없음"
    comparison_template: "{other_insurer}: {reduction_display}"

  enrollment_flexibility:
    rule_id: "widest_age_range"
    logic: "SELECT insurer WHERE (age_max - age_min) = MAX(...)"
    output_template: "{insurer}: {age_range}"
    comparison_template: "{other_insurer}: {years}년 좁음/넓음"
```

**금지 규칙:**
- ❌ LLM 기반 평가 생성
- ❌ 주관적 점수 부여 (예: "5점 만점에 4점")
- ❌ "우수", "양호", "부족" 같은 평가어
- ✅ 오직 수치 비교 + 사실 진술만

---

## 4. Part 3: 추천 (Conditional Guidance)

### 4.1 구조 정의

```json
{
  "conditional_guidance": {
    "coverage_name": "일반암진단비",
    "guidance_type": "conditional_branching",
    "conditions": [
      {
        "condition_id": "priority_coverage_amount",
        "condition_text": "보장금액을 우선하는 경우",
        "recommended_insurer": "DB",
        "reason": {
          "primary": "보장금액 6,000만원 (타사 대비 2배)",
          "secondary": "즉시 보장 (대기기간 없음)"
        },
        "evidence": {
          "coverage_limit": {...},
          "coverage_start": {...}
        }
      },
      {
        "condition_id": "priority_no_reduction",
        "condition_text": "감액 조건을 피하고 싶은 경우",
        "recommended_insurers": ["MERITZ", "DB"],
        "reason": {
          "primary": "감액 기간 없음",
          "comparison": "SAMSUNG은 1년 50% 감액 있음"
        },
        "evidence": {
          "exclusions": {...}
        }
      },
      {
        "condition_id": "priority_enrollment_age",
        "condition_text": "60세 이후 가입을 원하는 경우",
        "recommended_insurer": "MERITZ",
        "reason": {
          "primary": "최대 65세까지 가입 가능",
          "comparison": "SAMSUNG/DB는 60세까지만 가입 가능"
        },
        "evidence": {
          "enrollment_condition": {...}
        }
      },
      {
        "condition_id": "priority_premium",
        "condition_text": "보험료를 우선하는 경우",
        "premium_required": true,
        "recommended_insurer": null,
        "reason": {
          "unavailable": "보험료 정보 없음",
          "action": "보험료 API 연동 필요"
        }
      }
    ],
    "prohibited_guidance": [
      "A사가 가장 좋습니다",
      "B사를 추천합니다",
      "C사가 최선입니다"
    ],
    "prohibited_phrases_check": "PASS"
  }
}
```

### 4.2 Conditional Guidance Rules

**허용 패턴:**
```
IF {사용자 우선순위} THEN {보험사} BECAUSE {사실 근거}
```

**금지 패턴:**
```
❌ "{보험사}가 더 좋다"
❌ "{보험사}를 추천한다"
❌ "{보험사}가 최선이다"
```

**조건 분기 예시:**
```
✅ "보장금액 우선이면 DB (6,000만원)"
✅ "감액 조건 회피하려면 MERITZ 또는 DB"
✅ "60세 이후 가입 원하면 MERITZ (65세까지 가입 가능)"
```

---

## 5. Complete Response Example (통합 예시)

### Scenario 1: 3사 비교 성공 (보험료 포함)

**User Query:** "일반암진단비 비교해주세요 (30세 남성, 20년납 기준)"

**Response:**

```json
{
  "request_id": "req_20251225_001",
  "query": "일반암진단비",
  "insurers": ["SAMSUNG", "MERITZ", "DB"],
  "comparison_state": "comparable",
  "coverage": {
    "canonical_coverage_code": "CANCER_DIAGNOSIS",
    "mapping_status": "MAPPED"
  },

  "comparison_table": {
    "axes": {
      "eligibility": {
        "SAMSUNG": {"value": "O", "evidence": {...}},
        "MERITZ": {"value": "O", "evidence": {...}},
        "DB": {"value": "O", "evidence": {...}}
      },
      "coverage_limit": {
        "SAMSUNG": {"value": 30000000, "display": "3,000만원"},
        "MERITZ": {"value": 30000000, "display": "3,000만원"},
        "DB": {"value": 60000000, "display": "6,000만원"}
      },
      "coverage_start": {
        "SAMSUNG": {"waiting_days": 90, "display": "보장개시일 90일 후"},
        "MERITZ": {"waiting_days": 90, "display": "보장개시일 90일 후"},
        "DB": {"waiting_days": 0, "display": "보장개시일부터"}
      },
      "exclusions": {
        "SAMSUNG": {
          "reduction_periods": [{"period": "1년", "rate": 0.5}],
          "exclusion_diseases": ["유사암"]
        },
        "MERITZ": {
          "reduction_periods": [],
          "exclusion_diseases": ["유사암"]
        },
        "DB": {
          "reduction_periods": [],
          "exclusion_diseases": ["유사암"]
        }
      },
      "enrollment_condition": {
        "SAMSUNG": {"age_range": "20~60세"},
        "MERITZ": {"age_range": "20~65세"},
        "DB": {"age_range": "20~60세"}
      }
    }
  },

  "rule_based_summary": {
    "evaluated_dimensions": [
      {
        "dimension": "coverage_amount",
        "result": {
          "insurer": "DB",
          "value": 60000000,
          "comparison": {
            "SAMSUNG": "50% 낮음",
            "MERITZ": "50% 낮음"
          }
        }
      },
      {
        "dimension": "coverage_start_speed",
        "result": {
          "insurer": "DB",
          "waiting_days": 0,
          "comparison": {
            "SAMSUNG": "90일 더 빠름",
            "MERITZ": "90일 더 빠름"
          }
        }
      },
      {
        "dimension": "reduction_burden",
        "result": {
          "insurers": ["MERITZ", "DB"],
          "comparison": {
            "SAMSUNG": "1년 50% 감액 있음"
          }
        }
      },
      {
        "dimension": "premium",
        "result": {
          "SAMSUNG": {
            "monthly": 25000,
            "display": "월 25,000원",
            "conditions": {"age": 30, "gender": "M", "period": "20년납"}
          },
          "MERITZ": {
            "monthly": 27000,
            "display": "월 27,000원"
          },
          "DB": {
            "monthly": 45000,
            "display": "월 45,000원"
          }
        }
      }
    ]
  },

  "conditional_guidance": {
    "conditions": [
      {
        "condition_text": "보장금액을 우선하는 경우",
        "recommended_insurer": "DB",
        "reason": {
          "primary": "보장금액 6,000만원 (타사 대비 2배)",
          "secondary": "즉시 보장 (대기기간 없음)",
          "tradeoff": "보험료 월 45,000원 (타사 대비 1.7~1.8배)"
        }
      },
      {
        "condition_text": "보험료를 우선하는 경우",
        "recommended_insurer": "SAMSUNG",
        "reason": {
          "primary": "보험료 월 25,000원 (최저)",
          "tradeoff": "보장금액 3,000만원 (DB 대비 50%), 1년 50% 감액 있음"
        }
      },
      {
        "condition_text": "보험료와 보장의 균형을 원하는 경우",
        "recommended_insurer": "MERITZ",
        "reason": {
          "primary": "보험료 월 27,000원, 감액 없음",
          "tradeoff": "보장금액 3,000만원 (DB 대비 50%)"
        }
      }
    ]
  },

  "document_priority": ["PROPOSAL", "PRODUCT_SUMMARY", "BUSINESS_METHOD", "POLICY"],

  "evidence": {
    "proposal": [
      {
        "insurer": "SAMSUNG",
        "document_id": "SAMSUNG_PROPOSAL_2024",
        "page": 3,
        "span_text": "일반암진단비 3,000만원"
      },
      {...}
    ],
    "policy": [
      {
        "insurer": "SAMSUNG",
        "document_id": "SAMSUNG_POLICY_2024",
        "page": 12,
        "span_text": "유사암: 갑상선암(C73), 기타피부암(C44)"
      },
      {...}
    ]
  },

  "prohibited_phrases_check": "PASS"
}
```

---

### Scenario 2: 보험료 API 실패 (비교 지속)

**User Query:** "일반암진단비 비교해주세요"

**Response:**

```json
{
  "request_id": "req_20251225_002",
  "query": "일반암진단비",
  "insurers": ["SAMSUNG", "MERITZ", "DB"],
  "comparison_state": "comparable",

  "comparison_table": {
    // ... (Scenario 1과 동일)
  },

  "rule_based_summary": {
    "evaluated_dimensions": [
      // ... coverage_amount, coverage_start, reduction_burden (동일)
      {
        "dimension": "premium",
        "result": {
          "unavailable": true,
          "reason": "Premium API 연결 실패",
          "message": "보험료 정보를 가져올 수 없습니다."
        }
      }
    ]
  },

  "conditional_guidance": {
    "conditions": [
      {
        "condition_text": "보장금액을 우선하는 경우",
        "recommended_insurer": "DB",
        "reason": {...}
      },
      {
        "condition_text": "감액 조건을 피하고 싶은 경우",
        "recommended_insurers": ["MERITZ", "DB"],
        "reason": {...}
      },
      {
        "condition_text": "보험료를 우선하는 경우",
        "premium_required": true,
        "recommended_insurer": null,
        "reason": {
          "unavailable": "보험료 정보 없음",
          "action": "보험료는 별도 문의 필요"
        }
      }
    ]
  },

  "warnings": [
    {
      "type": "premium_unavailable",
      "message": "보험료 정보를 가져올 수 없어 보험료 기반 비교가 제외되었습니다."
    }
  ],

  "prohibited_phrases_check": "PASS"
}
```

---

### Scenario 3: 일부 보험사 out_of_universe

**User Query:** "특정희귀질환진단비 비교해주세요"

**Response:**

```json
{
  "request_id": "req_20251225_003",
  "query": "특정희귀질환진단비",
  "insurers": ["SAMSUNG", "MERITZ", "DB"],
  "comparison_state": "out_of_universe",

  "error": {
    "code": "partial_out_of_universe",
    "message": "일부 보험사에서 해당 담보를 찾을 수 없습니다.",
    "details": {
      "SAMSUNG": {
        "status": "out_of_universe",
        "reason": "가입설계서에 해당 담보 없음"
      },
      "MERITZ": {
        "status": "in_universe",
        "universe_id": "univ_meritz_001"
      },
      "DB": {
        "status": "out_of_universe",
        "reason": "가입설계서에 해당 담보 없음"
      }
    }
  },

  "comparison_allowed": false,
  "reason": "3사 중 1사만 가입설계서에 담보 존재 (비교 불가)",
  "suggestion": "가입설계서에 포함된 담보만 비교 가능합니다.",

  "prohibited_phrases_check": "PASS"
}
```

---

## 6. Premium Integration Strategy

### 6.1 Premium API 연동 방식

**API Call Timing:**
```
User Query
  ↓
Universe Lock Check
  ↓
Mapping Validation
  ↓
Comparison Table 생성
  ↓
[Premium API Call]  ← 여기서 호출 (병렬 가능)
  ↓
Rule-based Summary (보험료 포함/제외)
  ↓
Conditional Guidance 생성
```

**Premium API Request:**
```json
{
  "insurer": "SAMSUNG",
  "coverage_code": "CANCER_DIAGNOSIS",
  "conditions": {
    "age": 30,
    "gender": "M",
    "payment_period_years": 20,
    "coverage_period_years": 60
  }
}
```

**Premium API Response:**
```json
{
  "insurer": "SAMSUNG",
  "monthly_premium": 25000,
  "annual_premium": 300000,
  "total_premium": 6000000,
  "conditions_applied": {
    "age": 30,
    "gender": "M",
    "payment_period_years": 20
  }
}
```

### 6.2 Premium API 실패 처리

**Failure Scenarios:**
1. API 서버 다운
2. 타임아웃
3. 조건 불일치 (연령/기간 범위 초과)
4. 보험사별 API 미지원

**Handling Strategy:**
```python
def handle_premium_api_failure(error: Exception, insurer: str) -> dict:
    log_error(f"Premium API failed for {insurer}: {error}")

    return {
        "insurer": insurer,
        "premium_available": False,
        "premium_error": {
            "type": classify_error(error),  # "timeout" | "unsupported" | "invalid_condition"
            "message": "보험료 정보를 가져올 수 없습니다.",
            "fallback_action": "comparison_continues"
        }
    }
```

**Response Adjustment:**
- Rule-based Summary의 `premium` dimension은 `unavailable: true`
- Conditional Guidance에서 보험료 기반 조건은 `premium_required: true` + `recommended_insurer: null`
- `warnings` 배열에 보험료 미제공 경고 추가

**Critical Rule:**
```
Premium API 실패 → 비교 중단 ❌
Premium API 실패 → 보험료 제외하고 비교 지속 ✅
```

---

## 7. Validation Checklist (응답 검증)

모든 응답은 반환 전 다음 검증 통과 필요:

### 7.1 Structure Validation
- ✅ `comparison_table` 존재
- ✅ `rule_based_summary` 존재
- ✅ `conditional_guidance` 존재
- ✅ `document_priority` 고정 순서
- ✅ `evidence` 그룹화 (문서 유형별)

### 7.2 Content Validation
- ✅ 모든 O/X 판정에 evidence 존재
- ✅ 금액 단위 KRW 통일
- ✅ NULL vs [] vs 0 구분 명확
- ✅ Evidence에 document_id, page, span_text 필수

### 7.3 Prohibited Phrases Check
- ✅ "가장 좋다", "추천", "유리" 등 금지어 검출
- ✅ 조건 분기형 추천만 허용
- ✅ `prohibited_phrases_check: "PASS"` 필수

### 7.4 Premium Handling
- ✅ Premium API 실패 시 비교 지속
- ✅ 보험료 조건 명시 (age, gender, payment_period)
- ✅ 보험료 없어도 response 완성도 유지

---

## 8. Success Criteria (DoD)

### 8.1 응답 완전성
- ✅ 3단 구조 완비 (비교표 + 평가 + 추천)
- ✅ 모든 비교 축 포함 (5 axes)
- ✅ Evidence 완전 매핑

### 8.2 Constitutional Compliance
- ✅ 가입설계서 기준 (Universe Lock)
- ✅ 정직한 실패 (비교 불가 시 명시)
- ✅ 구조화 응답만 (자연어 요약 금지)
- ✅ 금지 표현 차단 (prohibited_phrases_check)

### 8.3 확장성
- ✅ 보험사 3개 → 8개 확장 시 구조 변경 없음
- ✅ Premium API 연동/미연동 모두 대응
- ✅ 일부 보험사 out_of_universe 처리

---

**End of Response Contract v1.0**
