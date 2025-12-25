# STEP 3.8-γ′ PRIME Response Contract

**Date:** 2025-12-25
**Version:** Prime (γ′)
**Purpose:** 가입설계서 행 기반 비교 응답 계약

---

## Response Structure (응답 구조)

### 기본 응답 (Default - 항상 포함)

```
┌─────────────────────────────────────┐
│  1. 비교표 (Fact Table)             │  ← 가입설계서 원문 데이터
├─────────────────────────────────────┤
│  2. 차이 요약 (Difference Summary)  │  ← 수치 차이만
└─────────────────────────────────────┘
```

### 추가 응답 (Optional - 사용자 요청 시에만)

```
┌─────────────────────────────────────┐
│  3. 조건별 답변 (Optional Guidance) │  ← 명시적 요청 시만
└─────────────────────────────────────┘
```

---

## Part 1: 비교표 (Fact Table)

### 구조

```json
{
  "comparison_table": {
    "coverage_query": "일반암진단비",
    "insurers": ["SAMSUNG", "MERITZ"],
    "SAMSUNG": {
      "state": "in_universe",
      "row_id": "SAMSUNG_PROPOSAL_2024_row_15",
      "coverage_name_raw": "일반암진단비(유사암제외)",
      "amount_raw": "3,000만원",
      "amount_value": 30000000,
      "period_raw": "80세 만기, 20년납",
      "renewal_flag": false,
      "evidence": {
        "document_id": "SAMSUNG_PROPOSAL_2024",
        "doc_type": "PROPOSAL",
        "page": 3,
        "row_id": "row_15"
      }
    },
    "MERITZ": {
      "state": "in_universe",
      "row_id": "MERITZ_PROPOSAL_2024_row_18",
      "coverage_name_raw": "일반암진단비(유사암5종제외)",
      "amount_raw": "3,000만원",
      "amount_value": 30000000,
      "period_raw": "80세 만기, 20년납",
      "renewal_flag": false,
      "evidence": {
        "document_id": "MERITZ_PROPOSAL_2024",
        "doc_type": "PROPOSAL",
        "page": 4,
        "row_id": "row_18"
      }
    }
  }
}
```

### 규칙

- ✅ 가입설계서 원문 그대로 (`coverage_name_raw`, `amount_raw`)
- ✅ 구조화 데이터 병기 (`amount_value`, regex 추출)
- ✅ Evidence = 가입설계서 행 정보
- ❌ 약관/요약서 인용 금지
- ❌ eligibility O/X/△ 판정 금지

---

## Part 2: 차이 요약 (Difference Summary)

### 구조

```json
{
  "difference_summary": {
    "coverage_query": "일반암진단비",
    "deltas": [
      {
        "dimension": "coverage_amount",
        "SAMSUNG": 30000000,
        "MERITZ": 30000000,
        "delta": 0,
        "summary": "동일 (3,000만원)"
      },
      {
        "dimension": "coverage_name",
        "SAMSUNG": "일반암진단비(유사암제외)",
        "MERITZ": "일반암진단비(유사암5종제외)",
        "delta": "담보명 차이 (유사암 vs 유사암5종)",
        "note": "가입설계서 원문 차이만 표시"
      },
      {
        "dimension": "renewal_type",
        "SAMSUNG": "비갱신형",
        "MERITZ": "비갱신형",
        "delta": "동일"
      }
    ],
    "prohibited_terms_check": "PASS"
  }
}
```

### 규칙

- ✅ 수치 차이만 제시 (금액, 기간, 연령)
- ✅ 사실 서술만 ("동일", "3,000만원 차이")
- ❌ "유리", "충분", "우수" 금지
- ❌ "평가", "점수" 금지

---

## Part 3: 조건별 답변 (Optional Guidance)

### 제공 조건

**다음 경우에만 생성:**
- 사용자가 "추천", "어떤 게 나은지" 명시적 질문
- 사용자가 우선순위 제시 ("보장금액 우선", "보험료 우선")

**기본 응답에 포함 ❌**

### 구조

```json
{
  "optional_guidance": {
    "note": "사용자 요청에 따른 조건별 답변",
    "user_question": "보장금액을 우선하는 경우 어디가 나은가요?",
    "conditions": [
      {
        "condition": "보장금액 우선",
        "response_insurer": null,
        "factual_basis": "SAMSUNG, MERITZ 동일 (3,000만원)",
        "conclusion": "보장금액 기준으로는 차이 없음"
      },
      {
        "condition": "담보 범위 우선",
        "response_insurer": null,
        "factual_basis": {
          "SAMSUNG": "유사암 제외",
          "MERITZ": "유사암5종 제외"
        },
        "conclusion": "가입설계서만으로는 유사암 정의 차이 불명확. 약관 확인 필요"
      }
    ]
  }
}
```

### 규칙

- ✅ 조건부 서술만 (`if-then`)
- ✅ 가입설계서 사실만 근거
- ❌ "A가 더 좋다" 금지
- ❌ "추천합니다" 금지

---

## Complete Examples

### Example 1: 기본 비교 (우선순위 질문 없음)

**User Query:** "일반암진단비 비교해주세요"

**Response:**

```json
{
  "request_id": "req_prime_001",
  "query": "일반암진단비",
  "insurers": ["SAMSUNG", "MERITZ"],
  "comparison_state": "in_universe_comparable",

  "comparison_table": {
    "SAMSUNG": {
      "state": "in_universe",
      "coverage_name_raw": "일반암진단비(유사암제외)",
      "amount_raw": "3,000만원",
      "amount_value": 30000000,
      "evidence": {
        "document_id": "SAMSUNG_PROPOSAL_2024",
        "doc_type": "PROPOSAL",
        "page": 3
      }
    },
    "MERITZ": {
      "state": "in_universe",
      "coverage_name_raw": "일반암진단비(유사암5종제외)",
      "amount_raw": "3,000만원",
      "amount_value": 30000000,
      "evidence": {
        "document_id": "MERITZ_PROPOSAL_2024",
        "doc_type": "PROPOSAL",
        "page": 4
      }
    }
  },

  "difference_summary": {
    "deltas": [
      {"dimension": "amount", "delta": 0, "summary": "동일 (3,000만원)"},
      {"dimension": "coverage_name", "delta": "유사암 vs 유사암5종", "note": "원문 차이"}
    ]
  },

  "optional_guidance": null,

  "document_sources": {
    "used": ["PROPOSAL"],
    "not_used": ["PRODUCT_SUMMARY", "BUSINESS_METHOD", "POLICY"]
  }
}
```

---

### Example 2: 담보 없음 (out_of_universe)

**User Query:** "특정희귀질환진단비 비교해주세요"

**Response:**

```json
{
  "request_id": "req_prime_002",
  "query": "특정희귀질환진단비",
  "insurers": ["SAMSUNG", "MERITZ"],
  "comparison_state": "out_of_universe",

  "error": {
    "code": "out_of_universe",
    "message": "해당 담보는 가입설계서에 존재하지 않아 비교 불가",
    "details": {
      "SAMSUNG": {
        "state": "out_of_universe",
        "reason": "가입설계서에 해당 담보 없음"
      },
      "MERITZ": {
        "state": "out_of_universe",
        "reason": "가입설계서에 해당 담보 없음"
      }
    }
  },

  "comparison_table": null,
  "difference_summary": null,
  "optional_guidance": null
}
```

---

### Example 3: 매핑 실패 (unmapped, 비교 지속)

**User Query:** "신규특약담보 비교해주세요"

**Response:**

```json
{
  "request_id": "req_prime_003",
  "query": "신규특약담보",
  "insurers": ["SAMSUNG", "MERITZ"],
  "comparison_state": "in_universe_unmapped",

  "comparison_table": {
    "SAMSUNG": {
      "state": "in_universe",
      "mapping_status": "UNMAPPED",
      "coverage_name_raw": "신규특약담보",
      "amount_raw": "500만원",
      "note": "Excel 매핑 실패. 원문 기반 비교 (정확도 낮음)"
    },
    "MERITZ": {
      "state": "in_universe",
      "mapping_status": "UNMAPPED",
      "coverage_name_raw": "신규특약담보(갱신형)",
      "amount_raw": "500만원"
    }
  },

  "difference_summary": {
    "deltas": [
      {"dimension": "amount", "delta": 0, "summary": "동일 (500만원)"},
      {"dimension": "renewal", "delta": "갱신형 여부 차이"}
    ],
    "note": "매핑 실패로 정확도 낮음. 원문 기반 비교만 가능"
  },

  "warnings": [
    {
      "type": "unmapped",
      "message": "담보명 매핑 실패. 원문 기반 비교 결과로 정확도가 낮을 수 있습니다."
    }
  ]
}
```

---

### Example 4: 우선순위 질문 포함

**User Query:** "일반암진단비 비교해주세요. 보장금액이 중요합니다."

**Response:**

```json
{
  "comparison_table": { /* 동일 */ },
  "difference_summary": { /* 동일 */ },

  "optional_guidance": {
    "note": "사용자 요청: 보장금액 우선",
    "user_question": "보장금액이 중요합니다",
    "conditions": [
      {
        "condition": "보장금액 우선",
        "response_insurer": null,
        "factual_basis": "SAMSUNG, MERITZ 동일 (3,000만원)",
        "conclusion": "보장금액 기준으로는 차이 없음"
      }
    ]
  }
}
```

---

## Validation Checklist

### Structure
- ✅ `comparison_table` 필수
- ✅ `difference_summary` 필수
- ✅ `optional_guidance` 기본 null
- ✅ `evidence.doc_type = "PROPOSAL"` 항상

### Content
- ✅ 가입설계서 원문 데이터만
- ✅ 수치 차이만 제시
- ✅ NULL 처리 명확
- ❌ 약관 인용 금지
- ❌ 주관 서술 금지
- ❌ eligibility 판정 금지

### Prohibited Terms
- ❌ "유리", "충분", "우수"
- ❌ "추천", "권장"
- ❌ "평가", "점수"
- ❌ "보통", "일반적으로"

---

## Success Criteria

- ✅ 가입설계서만으로 비교 완료
- ✅ 추천 Optional 분리
- ✅ eligibility 로직 제거
- ✅ 매핑 실패해도 비교 지속
- ✅ 금지 표현 차단

---

**End of PRIME Response Contract**
