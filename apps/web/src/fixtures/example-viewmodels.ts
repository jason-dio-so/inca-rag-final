/**
 * Example 1-4 ViewModel Fixtures
 * Based on: docs/customer/INCA_DIO_REQUIREMENTS.md
 *
 * Purpose: UI rendering validation for INCA DIO examples
 * Usage: Manual testing, Storybook, Playwright E2E tests
 *
 * Constitutional Compliance:
 * - All ViewModels are fact-only
 * - NO recommendation/judgment/interpretation text
 * - Schema v2 compliant (next4.v2)
 */

import type { CompareViewModel } from "@/lib/compare/viewModelTypes";

/**
 * Example 1: Premium Sorting
 * Input: "가장 저렴한 보험료 정렬순으로 4개만 비교해줘"
 * Expected: sort_metadata, visual_emphasis
 */
export const example1PremiumSorting: CompareViewModel = {
  schema_version: "next4.v2",
  generated_at: "2025-12-26T00:00:00Z",
  header: {
    user_query: "가장 저렴한 보험료 정렬순으로 4개만 비교해줘",
  },
  snapshot: {
    comparison_basis: "통합보험",
    insurers: [
      {
        insurer: "SAMSUNG",
        headline_amount: {
          amount_value: 3000,
          amount_unit: "만원",
          display_text: "3,000만원",
        },
        status: "OK",
      },
      {
        insurer: "MERITZ",
        headline_amount: {
          amount_value: 2500,
          amount_unit: "만원",
          display_text: "2,500만원",
        },
        status: "OK",
      },
    ],
    filter_criteria: {
      slot_key: "월납보험료",
    },
  },
  fact_table: {
    columns: [
      "보험사",
      "담보명(정규화)",
      "보장금액",
      "지급 조건 요약",
      "보험기간",
      "비고",
    ],
    rows: [
      {
        insurer: "MERITZ",
        coverage_title_normalized: "통합보험",
        benefit_amount: {
          amount_value: 2500,
          amount_unit: "만원",
          display_text: "2,500만원",
        },
        payout_conditions: [],
        term_text: "100세 만기",
        note_text: null,
        row_status: "OK",
      },
      {
        insurer: "SAMSUNG",
        coverage_title_normalized: "통합보험",
        benefit_amount: {
          amount_value: 3000,
          amount_unit: "만원",
          display_text: "3,000만원",
        },
        payout_conditions: [],
        term_text: "100세 만기",
        note_text: null,
        row_status: "OK",
      },
    ],
    table_type: "default",
    sort_metadata: {
      sort_by: "총납입보험료_일반",
      sort_order: "asc",
      limit: 4,
    },
    visual_emphasis: {
      min_value_style: "blue",
      max_value_style: "red",
    },
  },
  evidence_panels: [],
};

/**
 * Example 2: Condition Difference Detection
 * Input: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
 * Expected: filter_criteria.difference_detected, rows[].highlight
 */
export const example2ConditionDifference: CompareViewModel = {
  schema_version: "next4.v2",
  generated_at: "2025-12-26T00:00:00Z",
  header: {
    user_query: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘",
  },
  snapshot: {
    comparison_basis: "암직접입원비",
    insurers: [
      {
        insurer: "SAMSUNG",
        headline_amount: {
          amount_value: 5,
          amount_unit: "만원",
          display_text: "5만원 (일당)",
        },
        status: "OK",
      },
      {
        insurer: "MERITZ",
        headline_amount: {
          amount_value: 5,
          amount_unit: "만원",
          display_text: "5만원 (일당)",
        },
        status: "OK",
      },
    ],
    filter_criteria: {
      slot_key: "payout_limit",
      difference_detected: true,
    },
  },
  fact_table: {
    columns: [
      "보험사",
      "담보명(정규화)",
      "보장금액",
      "지급 조건 요약",
      "보험기간",
      "비고",
    ],
    rows: [
      {
        insurer: "SAMSUNG",
        coverage_title_normalized: "암직접입원비",
        benefit_amount: {
          amount_value: 5,
          amount_unit: "만원",
          display_text: "5만원",
        },
        payout_conditions: [
          {
            slot_key: "payout_limit",
            value_text: "1~120일",
          },
        ],
        term_text: "100세 만기",
        note_text: null,
        row_status: "OK",
        highlight: ["payout_limit"],
      },
      {
        insurer: "MERITZ",
        coverage_title_normalized: "암직접입원비",
        benefit_amount: {
          amount_value: 5,
          amount_unit: "만원",
          display_text: "5만원",
        },
        payout_conditions: [
          {
            slot_key: "payout_limit",
            value_text: "1~180일",
          },
        ],
        term_text: "100세 만기",
        note_text: null,
        row_status: "OK",
      },
    ],
    table_type: "default",
  },
  evidence_panels: [
    {
      id: "ev_samsung_001",
      insurer: "SAMSUNG",
      doc_type: "가입설계서",
      page: 3,
      excerpt: "암직접입원비 1~120일 한도로 지급 (일당 5만원)",
    },
    {
      id: "ev_meritz_001",
      insurer: "MERITZ",
      doc_type: "가입설계서",
      page: 4,
      excerpt: "암직접입원비 1~180일 한도로 지급 (일당 5만원)",
    },
  ],
};

/**
 * Example 3: Specific Insurers Comparison
 * Input: "삼성화재, 메리츠화재의 암진단비를 비교해줘"
 * Expected: filter_criteria.insurer_filter
 */
export const example3SpecificInsurers: CompareViewModel = {
  schema_version: "next4.v2",
  generated_at: "2025-12-26T00:00:00Z",
  header: {
    user_query: "삼성화재, 메리츠화재의 암진단비를 비교해줘",
  },
  snapshot: {
    comparison_basis: "암진단비",
    insurers: [
      {
        insurer: "SAMSUNG",
        headline_amount: {
          amount_value: 3000,
          amount_unit: "만원",
          display_text: "3,000만원",
        },
        status: "OK",
      },
      {
        insurer: "MERITZ",
        headline_amount: {
          amount_value: 2000,
          amount_unit: "만원",
          display_text: "2,000만원",
        },
        status: "OK",
      },
    ],
    filter_criteria: {
      insurer_filter: ["SAMSUNG", "MERITZ"],
    },
  },
  fact_table: {
    columns: [
      "보험사",
      "담보명(정규화)",
      "보장금액",
      "지급 조건 요약",
      "보험기간",
      "비고",
    ],
    rows: [
      {
        insurer: "SAMSUNG",
        coverage_title_normalized: "암진단비",
        benefit_amount: {
          amount_value: 3000,
          amount_unit: "만원",
          display_text: "3,000만원",
        },
        payout_conditions: [
          {
            slot_key: "disease_scope",
            value_text: "유사암 제외",
          },
          {
            slot_key: "payment_frequency",
            value_text: "최초 1회",
          },
        ],
        term_text: "100세 만기",
        note_text: null,
        row_status: "OK",
      },
      {
        insurer: "MERITZ",
        coverage_title_normalized: "암진단비",
        benefit_amount: {
          amount_value: 2000,
          amount_unit: "만원",
          display_text: "2,000만원",
        },
        payout_conditions: [
          {
            slot_key: "disease_scope",
            value_text: "유사암 제외",
          },
          {
            slot_key: "payment_frequency",
            value_text: "최초 1회",
          },
        ],
        term_text: "100세 만기",
        note_text: null,
        row_status: "OK",
      },
    ],
    table_type: "default",
  },
  evidence_panels: [
    {
      id: "ev_samsung_001",
      insurer: "SAMSUNG",
      doc_type: "가입설계서",
      page: 2,
      excerpt: "암진단비 3,000만원 (최초 1회 한, 90일 대기기간, 유사암 제외)",
    },
    {
      id: "ev_meritz_001",
      insurer: "MERITZ",
      doc_type: "가입설계서",
      page: 3,
      excerpt: "암진단비 2,000만원 (최초 1회 한, 유사암 제외)",
    },
  ],
};

/**
 * Example 4: Disease-based O/X Matrix
 * Input: "제자리암, 경계성종양 보장내용에 따라 A사, B사 상품 비교해줘"
 * Expected: table_type = "ox_matrix", filter_criteria.disease_scope
 */
export const example4OXMatrix: CompareViewModel = {
  schema_version: "next4.v2",
  generated_at: "2025-12-26T00:00:00Z",
  header: {
    user_query: "제자리암, 경계성종양 보장내용에 따라 A사, B사 상품 비교해줘",
  },
  snapshot: {
    comparison_basis: "제자리암, 경계성종양 보장내용",
    insurers: [
      {
        insurer: "SAMSUNG",
        headline_amount: {
          amount_value: 600,
          amount_unit: "만원",
          display_text: "600만원",
        },
        status: "OK",
      },
      {
        insurer: "MERITZ",
        headline_amount: {
          amount_value: 500,
          amount_unit: "만원",
          display_text: "500만원",
        },
        status: "OK",
      },
    ],
    filter_criteria: {
      disease_scope: ["제자리암", "경계성종양"],
      insurer_filter: ["SAMSUNG", "MERITZ"],
    },
  },
  fact_table: {
    columns: [
      "보험사",
      "담보명(정규화)",
      "보장금액",
      "지급 조건 요약",
      "보험기간",
      "비고",
    ],
    rows: [
      {
        insurer: "SAMSUNG",
        coverage_title_normalized: "제자리암 진단비",
        benefit_amount: {
          amount_value: 600,
          amount_unit: "만원",
          display_text: "600만원",
        },
        payout_conditions: [
          {
            slot_key: "disease_scope",
            value_text: "제자리암, 경계성종양",
          },
        ],
        term_text: "100세 만기",
        note_text: null,
        row_status: "OK",
      },
      {
        insurer: "MERITZ",
        coverage_title_normalized: "제자리암 진단비",
        benefit_amount: {
          amount_value: 500,
          amount_unit: "만원",
          display_text: "500만원",
        },
        payout_conditions: [
          {
            slot_key: "disease_scope",
            value_text: "제자리암, 경계성종양",
          },
        ],
        term_text: "100세 만기",
        note_text: null,
        row_status: "OK",
      },
    ],
    table_type: "ox_matrix",
  },
  evidence_panels: [
    {
      id: "ev_samsung_001",
      insurer: "SAMSUNG",
      doc_type: "약관",
      page: 12,
      excerpt: "제자리암 진단비: 600만원 지급 (경계성종양 포함)",
    },
    {
      id: "ev_meritz_001",
      insurer: "MERITZ",
      doc_type: "약관",
      page: 15,
      excerpt: "제자리암 진단비: 500만원 지급 (경계성종양 포함)",
    },
  ],
};
