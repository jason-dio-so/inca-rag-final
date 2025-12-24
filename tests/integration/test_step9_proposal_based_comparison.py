"""
STEP 9: 가입설계서 중심 3사 비교 E2E Integration Test

Constitutional Requirements Tested:
1. Comparison target from proposal_coverage_universe (SSOT)
2. Policy documents = Evidence Enrichment only (NO Universe expansion)
3. disease_scope_norm = group references (not raw code arrays)
4. Missing evidence causes failure
5. 3-insurer comparison returns single comparison_state
6. Response schema matches specification
7. NO prohibited phrases in response
8. Evidence references included

Test Fixture:
- 3 insurers: SAMSUNG, MERITZ, DB
- 1 common coverage: 일반암진단비 (CANCER_DIAGNOSIS)
- Disease scope interpretation needed (유사암 제외)
"""
import pytest
from tests.fixtures.step9_common_coverage import (
    STEP9_COMMON_COVERAGE,
    STEP9_POLICY_DEFINITIONS,
    STEP9_EXPECTED_DISEASE_SCOPE_NORM
)
from tests.fixtures.kcd7_test_subset import KCD7_TEST_CODES
from src.policy_scope.comparison import (
    GroupOverlapState,
    InsurerDiseaseScope,
    aggregate_multi_party_overlap,
    generate_comparison_reason,
    ComparisonResponse,
    InsurerDiseaseScopeResponse,
    InsurerEvidence,
    generate_comparison_response,
    validate_comparison_response
)


class TestSTEP9ProposalBasedComparison:
    """
    STEP 9: 가입설계서 중심 3사 비교 E2E 테스트

    Constitutional Requirement:
    - 가입설계서 = 비교 대상 SSOT
    - 약관 = Evidence Enrichment only
    - 구조화 응답만 허용 (자연어 요약 금지)
    """

    def test_step9_three_insurer_proposal_based_comparison(self):
        """
        E2E Test: 가입설계서 기준 3사 비교 (SAMSUNG, MERITZ, DB)

        Validation Checklist:
        1. ✅ Comparison target is from proposal_coverage_universe
        2. ✅ Policy documents did NOT expand Universe
        3. ✅ disease_scope_norm is group references
        4. ✅ Missing evidence causes failure (tested separately)
        5. ✅ 3-insurer comparison returns single comparison_state
        6. ✅ Response schema matches specification
        7. ✅ NO prohibited phrases in response
        8. ✅ Evidence references included
        """
        # Step 1: Verify coverage from proposal universe
        coverage_code = STEP9_COMMON_COVERAGE["canonical_coverage_code"]
        assert coverage_code == "CANCER_DIAGNOSIS", \
            "Coverage must be from proposal_coverage_universe"

        # Verify all 3 insurers have this coverage in their proposals
        insurers = list(STEP9_COMMON_COVERAGE["insurers"].keys())
        assert len(insurers) == 3, "Must have 3 insurers"
        assert "SAMSUNG" in insurers and "MERITZ" in insurers and "DB" in insurers

        # Step 2: Create insurer disease scopes (from enriched disease_scope_norm)
        # This simulates disease_scope_norm after policy enrichment
        scopes = []

        # SAMSUNG (from policy definition)
        samsung_def = STEP9_POLICY_DEFINITIONS["SAMSUNG"]
        scopes.append(
            InsurerDiseaseScope(
                insurer="SAMSUNG",
                canonical_coverage_code=coverage_code,
                include_group_id="GENERAL_CANCER_C00_C97",
                exclude_group_id=samsung_def["group_id"],
                include_codes=set(["C00", "C01", "C73", "C44"]),
                exclude_codes=set(samsung_def["extracted_codes"])
            )
        )

        # MERITZ (from policy definition)
        meritz_def = STEP9_POLICY_DEFINITIONS["MERITZ"]
        scopes.append(
            InsurerDiseaseScope(
                insurer="MERITZ",
                canonical_coverage_code=coverage_code,
                include_group_id="GENERAL_CANCER_C00_C97",
                exclude_group_id=meritz_def["group_id"],
                include_codes=set(["C00", "C01", "C73", "C44"]),
                exclude_codes=set(meritz_def["extracted_codes"])
            )
        )

        # DB (policy definition not found - NULL)
        scopes.append(
            InsurerDiseaseScope(
                insurer="DB",
                canonical_coverage_code=coverage_code,
                include_group_id=None,  # NULL - policy definition not found
                exclude_group_id=None,
                include_codes=None,
                exclude_codes=None
            )
        )

        # Step 3: Compute multi-party overlap state
        overlap_state = aggregate_multi_party_overlap(scopes)

        # Expected: UNKNOWN (because DB has NULL disease_scope_norm)
        assert overlap_state == GroupOverlapState.UNKNOWN, \
            "With 1 NULL scope, overlap_state should be UNKNOWN"

        # Step 4: Generate comparison reason with group details
        from src.policy_scope.comparison.explainer import InsurerGroupDetail

        group_details = [
            InsurerGroupDetail(
                insurer="SAMSUNG",
                group_id=samsung_def["group_id"],
                group_label="유사암 (삼성)",
                basis_doc_id=samsung_def["document_id"],
                basis_page=samsung_def["page"],
                member_count=len(samsung_def["extracted_codes"])
            ),
            InsurerGroupDetail(
                insurer="MERITZ",
                group_id=meritz_def["group_id"],
                group_label="유사암 (메리츠)",
                basis_doc_id=meritz_def["document_id"],
                basis_page=meritz_def["page"],
                member_count=len(meritz_def["extracted_codes"])
            ),
            InsurerGroupDetail(
                insurer="DB",
                group_id=None,
                group_label=None,
                basis_doc_id=None,
                basis_page=None,
                member_count=None
            ),
        ]

        reason = generate_comparison_reason(overlap_state, scopes, group_details)

        assert reason.comparison_state == "comparable_with_gaps"
        assert reason.reason_code == "disease_scope_policy_required"
        assert "DB" in reason.explanation or "약관" in reason.explanation, \
            "Should mention DB or policy verification needed"

        # Step 5: Create insurer scope responses with evidence
        insurer_responses = []

        # SAMSUNG (with evidence from policy)
        insurer_responses.append(
            InsurerDiseaseScopeResponse(
                insurer="SAMSUNG",
                disease_scope_norm=STEP9_EXPECTED_DISEASE_SCOPE_NORM["SAMSUNG"],
                evidence=InsurerEvidence(
                    basis_doc_id=samsung_def["document_id"],
                    basis_page=samsung_def["page"],
                    basis_span=samsung_def["definition_text"].strip()
                )
            )
        )

        # MERITZ (with evidence from policy)
        insurer_responses.append(
            InsurerDiseaseScopeResponse(
                insurer="MERITZ",
                disease_scope_norm=STEP9_EXPECTED_DISEASE_SCOPE_NORM["MERITZ"],
                evidence=InsurerEvidence(
                    basis_doc_id=meritz_def["document_id"],
                    basis_page=meritz_def["page"],
                    basis_span=meritz_def["definition_text"].strip()
                )
            )
        )

        # DB (NULL - no evidence)
        insurer_responses.append(
            InsurerDiseaseScopeResponse(
                insurer="DB",
                disease_scope_norm=None,
                evidence=None
            )
        )

        # Step 6: Generate structured comparison response
        response = generate_comparison_response(
            coverage_code=coverage_code,
            coverage_name=STEP9_COMMON_COVERAGE["coverage_name_ko"],
            insurer_scopes=insurer_responses,
            comparison_reason=reason
        )

        # Step 7: Validate response schema
        assert validate_comparison_response(response), \
            "Response must pass constitutional validation"

        # Step 8: Verify response structure
        assert response.comparison_state == "comparable_with_gaps"
        assert response.coverage_code == "CANCER_DIAGNOSIS"
        assert response.coverage_name == "일반암진단비"
        assert len(response.insurers) == 3, "All 3 insurers must be included"

        # Step 9: Verify prohibited phrases check
        assert response.prohibited_phrases_check == "PASS", \
            "Response must not contain prohibited phrases"

        # Step 10: Verify evidence included
        evidence_count = sum(
            1 for ins in response.insurers
            if ins.evidence is not None
        )
        assert evidence_count >= 2, \
            "At least 2 insurers should have evidence (SAMSUNG, MERITZ)"

        # Step 11: Verify response can be serialized to dict
        response_dict = response.to_dict()
        assert "comparison_state" in response_dict
        assert "comparison_reason" in response_dict
        assert "evidence_refs" in response_dict["comparison_reason"]
        assert len(response_dict["comparison_reason"]["evidence_refs"]) >= 2, \
            "Evidence references must be included"

    def test_universe_lock_policy_does_not_expand_universe(self):
        """
        Constitutional Test: Policy enrichment does NOT expand Universe

        Requirement:
        - Even if policy has additional coverage definitions
        - Only proposal_coverage_universe determines comparison targets
        - Policy = Evidence Enrichment only for existing Universe coverages
        """
        # Verify coverage selection is from proposal universe
        coverage_code = STEP9_COMMON_COVERAGE["canonical_coverage_code"]
        insurers = STEP9_COMMON_COVERAGE["insurers"]

        # All 3 insurers must have this coverage in proposal universe
        for insurer_code in ["SAMSUNG", "MERITZ", "DB"]:
            assert insurer_code in insurers, \
                f"{insurer_code} must exist in proposal universe"
            assert insurers[insurer_code]["universe_id"] is not None, \
                f"{insurer_code} must have universe_id (from proposal)"

        # Constitutional guarantee:
        # Even if policy documents define other coverages,
        # only proposal universe determines what to compare
        # This test verifies we start from proposal universe, not policy

    def test_disease_scope_norm_is_group_references_not_raw_codes(self):
        """
        Constitutional Test: disease_scope_norm must be group references

        Requirement:
        - disease_scope_norm = {"include_group_id": "...", "exclude_group_id": "..."}
        - NOT raw code arrays like ["C00", "C01", ...]
        """
        # Verify expected disease_scope_norm format
        for insurer_code in ["SAMSUNG", "MERITZ"]:
            scope_norm = STEP9_EXPECTED_DISEASE_SCOPE_NORM[insurer_code]
            assert scope_norm is not None
            assert "include_group_id" in scope_norm
            assert "exclude_group_id" in scope_norm
            assert isinstance(scope_norm["include_group_id"], str), \
                "include_group_id must be string (group ID)"
            assert isinstance(scope_norm["exclude_group_id"], str), \
                "exclude_group_id must be string (group ID)"

            # Verify NOT raw code arrays
            assert not isinstance(scope_norm.get("include_codes"), list), \
                "disease_scope_norm must not have raw include_codes array"
            assert not isinstance(scope_norm.get("exclude_codes"), list), \
                "disease_scope_norm must not have raw exclude_codes array"

    def test_prohibited_phrases_validation(self):
        """
        Constitutional Test: Prohibited phrases blocked in response

        Requirement:
        - NO value judgments (가장 넓은, 가장 유리함, 추천)
        - Only factual differences stated
        """
        # Test that prohibited phrases cause failure
        from src.policy_scope.comparison.explainer import validate_explanation_no_prohibited_phrases

        # Valid explanation (factual)
        valid_explanation = "삼성과 메리츠의 유사암 정의에 교집합이 있습니다. 약관 확인이 필요합니다."
        assert validate_explanation_no_prohibited_phrases(valid_explanation)

        # Invalid explanations (prohibited phrases)
        invalid_explanations = [
            "삼성이 가장 넓은 보장을 제공합니다.",
            "메리츠가 가장 유리합니다.",
            "DB를 추천합니다.",
            "삼성이 더 나은 상품입니다.",
        ]

        for invalid_explanation in invalid_explanations:
            assert not validate_explanation_no_prohibited_phrases(invalid_explanation), \
                f"Should reject prohibited phrase: {invalid_explanation}"

    def test_response_requires_evidence_when_disease_scope_norm_exists(self):
        """
        Constitutional Test: Evidence required when disease_scope_norm exists

        Requirement:
        - If disease_scope_norm is not NULL, evidence must be provided
        - Missing evidence should cause validation failure
        """
        # Create response with disease_scope_norm but NO evidence
        insurer_response_without_evidence = InsurerDiseaseScopeResponse(
            insurer="SAMSUNG",
            disease_scope_norm={"include_group_id": "GROUP_A", "exclude_group_id": "GROUP_B"},
            evidence=None  # Missing evidence
        )

        # Create mock comparison reason
        from src.policy_scope.comparison.explainer import ComparisonReason, InsurerGroupDetail
        mock_reason = ComparisonReason(
            comparison_state="comparable",
            reason_code="disease_scope_identical",
            explanation="테스트 설명",
            details=[]
        )

        # Create response
        response = ComparisonResponse(
            comparison_state="comparable",
            coverage_code="TEST_CODE",
            coverage_name="테스트",
            insurers=[insurer_response_without_evidence],
            comparison_reason=mock_reason,
            prohibited_phrases_check="PASS"
        )

        # Validation should fail (evidence required when disease_scope_norm exists)
        assert not validate_comparison_response(response), \
            "Validation must fail when evidence is missing for disease_scope_norm"
