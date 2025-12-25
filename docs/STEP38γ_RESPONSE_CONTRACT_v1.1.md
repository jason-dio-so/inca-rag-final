# STEP 3.8-γ Response Contract v1.1 (고객 응답 계약)

**Date:** 2025-12-25
**Version:** 1.1
**Changes from v1.0:**
- Recommendation을 Optional로 강등 (기본 응답은 비교표+차이요약까지만)
- Rule-based Summary → Factual Deltas Summary (용어 변경, "평가" 금지)
- Document Priority 완화 적용 (PROPOSAL 필수, 나머지 선택)
- eligibility 축 수정 (X 제거, in_universe 기본)

---

## 1. Response Contract Overview

고객이 요구한 응답 구조는 **2단 기본 + 1단 선택** 구조:

```
┌─────────────────────────────────────┐
│  1. 비교 표 (Fact Table)            │  ← 사실만 (O/△/금액) [필수]
├─────────────────────────────────────┤
│  2. 차이 요약 (Factual Deltas)      │  ← 수치 차이만 [필수]
├─────────────────────────────────────┤
│  3. 조건별 답변 (Optional Guidance) │  ← 사용자 우선순위 질문 시에만 [선택]
└─────────────────────────────────────┘
```

**절대 원칙:**
- ❌ 자연어 주관 평가 금지
- ❌ "A가 더 좋다" 식 판단 금지
- ❌ "평가", "우수", "양호" 용어 금지
- ✅ 구조화 데이터만 허용
- ✅ 근거(evidence) 필수 (PROPOSAL 우선)

---

## 2. Part 1: 비교 표 (Fact Table) [필수]

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
          "note": "Universe 내 담보 (가입설계서에 존재)",
          "evidence": {
            "document_id": "SAMSUNG_PROPOSAL_2024",
            "doc_type": "PROPOSAL",
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
          "evidence": {
            "document_id": "SAMSUNG_PROPOSAL_2024",
            "doc_type": "PROPOSAL",
            "page": 3,
            "span_text": "일반암진단비 3,000만원"
          }
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
- `eligibility`: "O" | "△" (X는 out_of_universe로 처리)
  - Universe 내 담보는 기본 "O"
  - 조건부 보장만 "△" (조건 명시 필수)
- `coverage_limit`: integer (KRW) + display (formatted string)
- `coverage_start`: type + waiting_days + display
- `exclusions`: reduction_periods (array) + exclusion_diseases (array)
- `enrollment_condition`: structured object

**금지 표현:**
- ❌ "우수함", "부족함", "보통"
- ❌ "추천", "유리", "불리"
- ❌ 감정 표현 전부

**NULL 처리:**
- `null` = 정보 없음 (가입설계서에 명시 없음) → comparable_with_gaps
- `[]` = 명시적 없음 (예: "감액 없음")
- `0` = 명시적 0 (예: "보장개시일부터")

---

## 3. Part 2: 차이 요약 (Factual Deltas Summary) [필수]

### 3.1 구조 정의

```json
{
  "factual_deltas_summary": {
    "coverage_name": "일반암진단비",
    "deltas": [
      {
        "dimension": "coverage_amount",
        "delta_type": "numeric_comparison",
        "result": {
          "max_insurer": "DB",
          "max_value": 60000000,
          "max_display": "6,000만원",
          "deltas": {
            "SAMSUNG": {
              "value": 30000000,
              "diff_from_max": -30000000,
              "diff_display": "3,000만원 낮음"
            },
            "MERITZ": {
              "value": 30000000,
              "diff_from_max": -30000000,
              "diff_display": "3,000만원 낮음"
            }
          }
        }
      },
      {
        "dimension": "coverage_start_speed",
        "delta_type": "numeric_comparison",
        "result": {
          "min_waiting_insurer": "DB",
          "min_waiting_days": 0,
          "display": "즉시 보장",
          "deltas": {
            "SAMSUNG": {
              "waiting_days": 90,
              "diff_from_min": 90,
              "diff_display": "90일 더 느림"
            },
            "MERITZ": {
              "waiting_days": 90,
              "diff_from_min": 90,
              "diff_display": "90일 더 느림"
            }
          }
        }
      },
      {
        "dimension": "reduction_burden",
        "delta_type": "categorical_comparison",
        "result": {
          "no_reduction_insurers": ["MERITZ", "DB"],
          "reduction_insurers": {
            "SAMSUNG": "1년 50% 감액"
          }
        }
      },
      {
        "dimension": "enrollment_age_range",
        "delta_type": "numeric_comparison",
        "result": {
          "widest_insurer": "MERITZ",
          "age_range": "20~65세",
          "range_years": 45,
          "deltas": {
            "SAMSUNG": {
              "age_range": "20~60세",
              "range_years": 40,
              "diff_from_widest": -5,
              "diff_display": "5년 좁음"
            },
            "DB": {
              "age_range": "20~60세",
              "range_years": 40,
              "diff_from_widest": -5,
              "diff_display": "5년 좁음"
            }
          }
        }
      }
    ],
    "prohibited_terms_check": "PASS"
  }
}
```

### 3.2 Factual Deltas Rules

**용어 변경:**
- ❌ "Rule-based Summary", "종합 평가"
- ✅ "Factual Deltas Summary", "차이 요약"

**허용 표현:**
- ✅ 수치 차이만 (예: "3,000만원 낮음", "90일 더 느림")
- ✅ 사실 진술 (예: "감액 없음", "즉시 보장")

**금지 표현:**
- ❌ "우수", "양호", "부족", "최고", "최선"
- ❌ "평가", "점수", "등급"
- ❌ 주관적 판단 전부

**Delta Types:**
- `numeric_comparison`: 수치 비교 (금액, 일수, 연수)
- `categorical_comparison`: 범주 비교 (있음/없음)

---

## 4. Part 3: 조건별 답변 (Optional Guidance) [선택]

### 4.1 제공 조건

**조건별 답변은 다음 경우에만 제공:**
1. 사용자가 명시적으로 우선순위를 질문한 경우
   - 예: "보장금액을 우선하면 어디가 좋나요?"
   - 예: "보험료가 저렴한 곳을 알려주세요"
2. 기본 응답(비교표 + 차이요약)만으로 충분한 경우 제공 안 함

### 4.2 구조 정의

```json
{
  "optional_guidance": {
    "coverage_name": "일반암진단비",
    "guidance_type": "conditional_branching",
    "note": "사용자 우선순위 질문에 대한 조건별 답변",
    "conditions": [
      {
        "condition_id": "priority_coverage_amount",
        "user_question": "보장금액을 우선하는 경우",
        "response_insurer": "DB",
        "factual_basis": {
          "primary": "보장금액 6,000만원 (타사 대비 2배)",
          "secondary": "즉시 보장 (대기기간 0일)"
        },
        "tradeoff": "보험료 정보 없음 (비교 불가)",
        "evidence": {
          "coverage_limit": {...},
          "coverage_start": {...}
        }
      },
      {
        "condition_id": "priority_no_reduction",
        "user_question": "감액 조건을 피하고 싶은 경우",
        "response_insurers": ["MERITZ", "DB"],
        "factual_basis": {
          "primary": "감액 기간 없음"
        },
        "comparison_fact": "SAMSUNG은 1년 50% 감액",
        "evidence": {
          "exclusions": {...}
        }
      },
      {
        "condition_id": "priority_enrollment_age",
        "user_question": "60세 이후 가입을 원하는 경우",
        "response_insurer": "MERITZ",
        "factual_basis": {
          "primary": "최대 65세까지 가입 가능"
        },
        "comparison_fact": "SAMSUNG/DB는 60세까지만",
        "evidence": {
          "enrollment_condition": {...}
        }
      }
    ],
    "prohibited_guidance": [
      "A사가 가장 좋습니다",
      "B사를 추천합니다",
      "C사가 최선입니다"
    ],
    "prohibited_terms_check": "PASS"
  }
}
```

### 4.3 Optional Guidance Rules

**제공 원칙:**
- 사용자가 우선순위 질문을 한 경우에만 제공
- 기본 응답에는 포함하지 않음

**허용 패턴:**
```
IF {사용자 우선순위} THEN {보험사} BECAUSE {사실 근거} TRADEOFF {다른 축 차이}
```

**금지 패턴:**
```
❌ "{보험사}가 더 좋다"
❌ "{보험사}를 추천한다"
❌ "{보험사}가 최선이다"
❌ "{보험사}가 우수하다"
```

**조건 분기 예시:**
```
✅ "보장금액 우선이면 DB (6,000만원, 타사 대비 2배)"
✅ "감액 조건 회피하려면 MERITZ 또는 DB (감액 없음)"
✅ "60세 이후 가입 원하면 MERITZ (65세까지 가입 가능)"
```

---

## 5. Complete Response Example (통합 예시)

### Scenario 1: 기본 비교 (우선순위 질문 없음)

**User Query:** "일반암진단비 비교해주세요"

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
        "SAMSUNG": {"value": "O", "evidence": {"doc_type": "PROPOSAL", ...}},
        "MERITZ": {"value": "O", "evidence": {"doc_type": "PROPOSAL", ...}},
        "DB": {"value": "O", "evidence": {"doc_type": "PROPOSAL", ...}}
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
        "SAMSUNG": {"reduction_periods": [{"period": "1년", "rate": 0.5}]},
        "MERITZ": {"reduction_periods": []},
        "DB": {"reduction_periods": []}
      },
      "enrollment_condition": {
        "SAMSUNG": {"age_range": "20~60세"},
        "MERITZ": {"age_range": "20~65세"},
        "DB": {"age_range": "20~60세"}
      }
    }
  },

  "factual_deltas_summary": {
    "deltas": [
      {
        "dimension": "coverage_amount",
        "result": {
          "max_insurer": "DB",
          "max_value": 60000000,
          "deltas": {
            "SAMSUNG": {"diff_display": "3,000만원 낮음"},
            "MERITZ": {"diff_display": "3,000만원 낮음"}
          }
        }
      },
      {
        "dimension": "coverage_start_speed",
        "result": {
          "min_waiting_insurer": "DB",
          "min_waiting_days": 0,
          "deltas": {
            "SAMSUNG": {"diff_display": "90일 더 느림"},
            "MERITZ": {"diff_display": "90일 더 느림"}
          }
        }
      },
      {
        "dimension": "reduction_burden",
        "result": {
          "no_reduction_insurers": ["MERITZ", "DB"],
          "reduction_insurers": {"SAMSUNG": "1년 50% 감액"}
        }
      }
    ]
  },

  "optional_guidance": null,

  "document_priority": {
    "used": ["PROPOSAL"],
    "note": "PROPOSAL 근거만으로 비교 완료"
  },

  "evidence": {
    "PROPOSAL": [
      {
        "insurer": "SAMSUNG",
        "document_id": "SAMSUNG_PROPOSAL_2024",
        "page": 3,
        "span_text": "일반암진단비 3,000만원"
      },
      // ... MERITZ, DB
    ]
  },

  "prohibited_terms_check": "PASS"
}
```

---

### Scenario 2: 우선순위 질문 포함 비교

**User Query:** "일반암진단비 비교해주세요. 보장금액이 중요합니다."

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

  "factual_deltas_summary": {
    // ... (Scenario 1과 동일)
  },

  "optional_guidance": {
    "note": "사용자 우선순위 '보장금액 중요'에 대한 답변",
    "conditions": [
      {
        "condition_id": "priority_coverage_amount",
        "user_question": "보장금액을 우선하는 경우",
        "response_insurer": "DB",
        "factual_basis": {
          "primary": "보장금액 6,000만원 (타사 대비 2배)",
          "secondary": "즉시 보장 (대기기간 0일)"
        },
        "tradeoff": null,
        "evidence": {...}
      }
    ]
  },

  "document_priority": {
    "used": ["PROPOSAL"]
  },

  "prohibited_terms_check": "PASS"
}
```

---

### Scenario 3: Evidence 부족 (comparable_with_gaps)

**User Query:** "특정 담보 비교해주세요"

**Response:**

```json
{
  "request_id": "req_20251225_003",
  "query": "특정 담보",
  "insurers": ["SAMSUNG", "MERITZ"],
  "comparison_state": "comparable_with_gaps",

  "comparison_table": {
    "axes": {
      "eligibility": {
        "SAMSUNG": {"value": "O", "evidence": {...}},
        "MERITZ": {"value": "O", "evidence": {...}}
      },
      "coverage_limit": {
        "SAMSUNG": {"value": 30000000, "evidence": {...}},
        "MERITZ": {"value": null, "reason": "가입설계서에 금액 명시 없음"}
      },
      "coverage_start": {
        "SAMSUNG": {"waiting_days": null, "reason": "가입설계서에 보장개시 명시 없음"},
        "MERITZ": {"waiting_days": 0, "evidence": {...}}
      }
    }
  },

  "factual_deltas_summary": {
    "deltas": [
      {
        "dimension": "coverage_amount",
        "result": {
          "incomplete": true,
          "reason": "MERITZ 금액 정보 없음",
          "available_data": {
            "SAMSUNG": 30000000
          }
        }
      }
    ]
  },

  "gap_details": {
    "gap_slots": ["coverage_limit.MERITZ", "coverage_start.SAMSUNG"],
    "policy_verification_required": true,
    "message": "일부 정보 누락. 약관 확인 필요"
  },

  "optional_guidance": null,

  "document_priority": {
    "used": ["PROPOSAL"],
    "needed": ["POLICY"],
    "note": "PROPOSAL 근거 부족으로 POLICY 확인 필요"
  },

  "prohibited_terms_check": "PASS"
}
```

---

## 6. Premium Integration Strategy

### 6.1 Premium은 보조 정보 (비교 중단 금지)

**Premium API 실패 처리:**
```json
{
  "factual_deltas_summary": {
    "deltas": [
      // ... coverage_amount, coverage_start, reduction_burden
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

  "optional_guidance": {
    "conditions": [
      // ... 다른 조건들
      {
        "condition_id": "priority_premium",
        "user_question": "보험료를 우선하는 경우",
        "response_insurer": null,
        "factual_basis": {
          "unavailable": "보험료 정보 없음"
        },
        "action": "보험료는 별도 문의 필요"
      }
    ]
  },

  "warnings": [
    {
      "type": "premium_unavailable",
      "message": "보험료 정보를 가져올 수 없어 보험료 기반 비교가 제외되었습니다."
    }
  ]
}
```

**Critical Rule:**
```
Premium API 실패 → 비교 중단 ❌
Premium API 실패 → 보험료 제외하고 비교 지속 ✅
```

---

## 7. Validation Checklist (응답 검증)

### 7.1 Structure Validation
- ✅ `comparison_table` 존재
- ✅ `factual_deltas_summary` 존재
- ✅ `optional_guidance` = null (우선순위 질문 없으면) or object (있으면)
- ✅ `document_priority.used` 포함 (최소 PROPOSAL)
- ✅ `evidence` 그룹화 (문서 유형별, 존재하는 것만)

### 7.2 Content Validation
- ✅ 모든 O/△ 판정에 PROPOSAL evidence 존재
- ✅ 금액 단위 KRW 통일
- ✅ NULL vs [] vs 0 구분 명확
- ✅ Evidence에 document_id, doc_type="PROPOSAL", page, span_text 필수

### 7.3 Prohibited Terms Check
- ✅ "평가", "우수", "양호", "추천", "유리" 등 금지어 검출
- ✅ 조건 분기형만 허용 (optional_guidance)
- ✅ `prohibited_terms_check: "PASS"` 필수

### 7.4 Premium Handling
- ✅ Premium API 실패 시 비교 지속
- ✅ 보험료 조건 명시 (age, gender, payment_period) - 성공 시에만
- ✅ 보험료 없어도 response 완성도 유지

---

## 8. Success Criteria (DoD)

### 8.1 응답 완전성
- ✅ 2단 기본 구조 (비교표 + 차이요약)
- ✅ 1단 선택 구조 (조건별 답변 - 우선순위 질문 시에만)
- ✅ 모든 비교 축 포함 (5 axes)
- ✅ Evidence PROPOSAL 우선

### 8.2 Constitutional Compliance
- ✅ 가입설계서 기준 (Universe Lock)
- ✅ 정직한 실패 (비교 불가 시 명시, evidence 없으면 comparable_with_gaps)
- ✅ 구조화 응답만 (자연어 요약 금지)
- ✅ 금지 표현 차단 (prohibited_terms_check)
- ✅ Document Priority 완화 (PROPOSAL 필수, 나머지 선택)

### 8.3 확장성
- ✅ 보험사 3개 → 8개 확장 시 구조 변경 없음
- ✅ Premium API 연동/미연동 모두 대응
- ✅ 일부 보험사 evidence 부족 처리 (comparable_with_gaps)

---

**End of Response Contract v1.1**
