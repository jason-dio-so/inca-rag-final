"""
STEP 9: Common Coverage Fixture (3-Insurer Proposal Universe)

Purpose: Test fixture representing common coverage across 3 insurers

Constitutional Requirement:
- Coverage selected from proposal_coverage_universe (SSOT)
- Canonical coverage_code identical across 3 insurers
- Disease scope interpretation needed (유사암 제외)
"""

# Selected Coverage: 일반암진단비 (General Cancer Diagnosis)
# Canonical Code: CANCER_DIAGNOSIS
# All 3 insurers have this in their proposals

STEP9_COMMON_COVERAGE = {
    "canonical_coverage_code": "CANCER_DIAGNOSIS",
    "coverage_name_ko": "일반암진단비",
    "insurers": {
        "SAMSUNG": {
            "proposal_coverage_name": "일반암진단비",
            "universe_id": "SAMSUNG_CANCER_DIAG_001",  # Mock ID
            "disease_scope_raw": "유사암 제외",  # From proposal
            "amount_value": 30000000,  # 3000만원
        },
        "MERITZ": {
            "proposal_coverage_name": "일반암진단비",
            "universe_id": "MERITZ_CANCER_DIAG_001",  # Mock ID
            "disease_scope_raw": "유사암 제외",  # From proposal
            "amount_value": 30000000,  # 3000만원
        },
        "DB": {
            "proposal_coverage_name": "일반암진단비",
            "universe_id": "DB_CANCER_DIAG_001",  # Mock ID
            "disease_scope_raw": "유사암 제외",  # From proposal
            "amount_value": 30000000,  # 3000만원
        },
    },
    "requires_policy_interpretation": True,  # Need 약관 for disease_scope_norm
}

# Policy Definitions (약관 근거) - Mock for testing
STEP9_POLICY_DEFINITIONS = {
    "SAMSUNG": {
        "document_id": "SAMSUNG_POLICY_2024",
        "page": 12,
        "definition_text": """
        제3조 (유사암의 정의 및 진단확정)
        "유사암"이라 함은 다음의 질병을 말합니다:
        1. 갑상선암 (C73)
        2. 기타피부암 (C44)
        """,
        "extracted_codes": ["C73", "C44"],
        "group_id": "SIMILAR_CANCER_SAMSUNG_V1",
    },
    "MERITZ": {
        "document_id": "MERITZ_POLICY_2024",
        "page": 9,
        "definition_text": """
        제5조 (유사암의 정의)
        유사암: 갑상선암(C73), 기타피부암(C44)
        """,
        "extracted_codes": ["C73", "C44"],
        "group_id": "SIMILAR_CANCER_MERITZ_V1",
    },
    "DB": {
        "document_id": "DB_POLICY_2024",
        "page": None,  # Not found (for UNKNOWN scenario testing)
        "definition_text": None,
        "extracted_codes": [],
        "group_id": None,
    },
}

# Expected disease_scope_norm after enrichment
STEP9_EXPECTED_DISEASE_SCOPE_NORM = {
    "SAMSUNG": {
        "include_group_id": "GENERAL_CANCER_C00_C97",
        "exclude_group_id": "SIMILAR_CANCER_SAMSUNG_V1",
    },
    "MERITZ": {
        "include_group_id": "GENERAL_CANCER_C00_C97",
        "exclude_group_id": "SIMILAR_CANCER_MERITZ_V1",
    },
    "DB": None,  # NULL - policy definition not found
}
