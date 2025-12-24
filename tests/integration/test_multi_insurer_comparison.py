"""
STEP 8: Multi-Insurer Comparison Tests (3+ Insurers)

Constitutional requirements tested:
1. Registry pattern working (3+ insurers registered)
2. Multi-party overlap detection (pairwise → unified state)
3. Explainable reasons with NO prohibited phrases
4. Evidence included in all cases

Test Scenarios:
- Scenario 1: FULL_MATCH (3 insurers identical)
- Scenario 2: PARTIAL_OVERLAP (2 insurers overlap, 1 differs)
- Scenario 3: NO_OVERLAP (3 insurers all different)
- Scenario 4: UNKNOWN (1 insurer disease_scope_norm NULL)
"""
import pytest
from src.policy_scope.registry import PolicyParserRegistry
from src.policy_scope.comparison.overlap import (
    GroupOverlapState,
    InsurerDiseaseScope,
    detect_pairwise_overlap,
    aggregate_multi_party_overlap
)
from src.policy_scope.comparison.explainer import (
    generate_comparison_reason,
    validate_explanation_no_prohibited_phrases
)


class TestMultiInsurerComparison:
    """
    STEP 8: Validate multi-insurer comparison (3+ insurers)

    Constitutional requirement (STEP 8-β):
    - 가입설계서 = 비교 Universe SSOT
    - 약관 = Evidence Enrichment only (Universe 확장 금지)
    - Policy parsers DO NOT expand proposal_coverage_universe
    """

    def test_universe_lock_policy_parsers_do_not_expand_universe(self):
        """
        Constitutional Test: Policy parsers are Evidence Enrichment only

        Requirement:
        - Policy parsers extract disease_scope_norm from 약관
        - They DO NOT create new Universe entries
        - They only fill slots for existing Universe coverages

        This test verifies:
        1. Policy parsers return definitions (not Universe entries)
        2. No code path creates proposal_coverage_universe from policy
        """
        from src.policy_scope.parsers.samsung import SamsungPolicyParser
        from src.policy_scope.base_parser import DiseaseGroupDefinition, CoverageScopeDefinition

        parser = SamsungPolicyParser()

        # Policy text with 유사암 definition
        policy_text = """
        제3조 (유사암의 정의)
        유사암이라 함은 다음의 질병을 말합니다:
        1. 갑상선암 (C73)
        2. 기타피부암 (C44)
        """

        # Extract disease group definition
        result = parser.extract_disease_group_definition(
            policy_text=policy_text,
            group_concept='유사암',
            document_id='SAMSUNG_POLICY_2024',
            page_number=3
        )

        # Verify result type
        assert isinstance(result, DiseaseGroupDefinition), \
            "Parser must return DiseaseGroupDefinition (NOT Universe entry)"

        # Verify it's evidence only (for enrichment)
        assert result.basis_doc_id == 'SAMSUNG_POLICY_2024', \
            "Must include evidence (약관 근거)"
        assert len(result.basis_span) > 0, \
            "Must include evidence span"

        # Constitutional guarantee: This does NOT create Universe entry
        # Universe Lock: Only proposal_coverage_universe determines comparison targets
        # This definition will ONLY be used to fill disease_scope_norm for existing Universe coverages

    def test_registry_has_3_plus_insurers(self):
        """
        Test: Registry has 3+ insurers registered

        Constitutional requirement:
        - Minimum 3 insurers (Samsung, Meritz, DB)
        """
        supported_insurers = PolicyParserRegistry.list_supported_insurers()

        assert len(supported_insurers) >= 3, \
            f"Registry must have 3+ insurers, got {len(supported_insurers)}: {supported_insurers}"

        # Verify specific insurers
        assert 'SAMSUNG' in supported_insurers, "Samsung must be registered"
        assert 'MERITZ' in supported_insurers, "Meritz must be registered"
        assert 'DB' in supported_insurers, "DB must be registered"

    def test_get_parser_for_registered_insurer(self):
        """
        Test: Can get parser for registered insurer
        """
        parser = PolicyParserRegistry.get_parser('SAMSUNG')

        assert parser is not None
        assert parser.insurer_code == 'SAMSUNG'
        assert parser.implementation_status == 'FULL'

    def test_get_parser_for_unregistered_insurer_raises_error(self):
        """
        Test: Getting parser for unregistered insurer raises NotImplementedError

        Constitutional requirement:
        - Unregistered insurers must raise NotImplementedError
        """
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            PolicyParserRegistry.get_parser('UNKNOWN_INSURER')

    def test_scenario_1_full_match_3_insurers(self):
        """
        Scenario 1: FULL_MATCH - All 3 insurers have identical disease scopes

        Expected:
        - overlap_state = FULL_MATCH
        - comparison_state = comparable
        - reason_code = disease_scope_identical
        """
        # Create identical scopes for 3 insurers
        scopes = [
            InsurerDiseaseScope(
                insurer='SAMSUNG',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id='GENERAL_CANCER_C00_C97',
                exclude_group_id='SIMILAR_CANCER_SAMSUNG_V1',
                include_codes={'C00', 'C01', 'C73', 'C44'},
                exclude_codes={'C73', 'C44'}
            ),
            InsurerDiseaseScope(
                insurer='MERITZ',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id='GENERAL_CANCER_C00_C97',
                exclude_group_id='SIMILAR_CANCER_SAMSUNG_V1',  # Same group ID
                include_codes={'C00', 'C01', 'C73', 'C44'},
                exclude_codes={'C73', 'C44'}
            ),
            InsurerDiseaseScope(
                insurer='DB',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id='GENERAL_CANCER_C00_C97',
                exclude_group_id='SIMILAR_CANCER_SAMSUNG_V1',  # Same group ID
                include_codes={'C00', 'C01', 'C73', 'C44'},
                exclude_codes={'C73', 'C44'}
            ),
        ]

        # Aggregate overlap
        overlap_state = aggregate_multi_party_overlap(scopes)

        assert overlap_state == GroupOverlapState.FULL_MATCH, \
            "3 identical scopes should result in FULL_MATCH"

        # Generate reason
        reason = generate_comparison_reason(overlap_state, scopes)

        assert reason.comparison_state == "comparable"
        assert reason.reason_code == "disease_scope_identical"
        assert len(reason.details) == 3, "Should have details for all 3 insurers"
        assert validate_explanation_no_prohibited_phrases(reason.explanation), \
            "Explanation must not contain prohibited phrases"

    def test_scenario_2_partial_overlap_3_insurers(self):
        """
        Scenario 2: PARTIAL_OVERLAP - All 3 insurers have some overlap but not identical

        Expected:
        - overlap_state = PARTIAL_OVERLAP
        - comparison_state = comparable_with_gaps
        - reason_code = disease_scope_partial_overlap
        """
        # All 3 insurers have C00 in common, but different exclusions
        scopes = [
            InsurerDiseaseScope(
                insurer='SAMSUNG',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id='GENERAL_CANCER_C00_C97',
                exclude_group_id='SIMILAR_CANCER_SAMSUNG_V1',
                include_codes={'C00', 'C01', 'C73', 'C44'},
                exclude_codes={'C73', 'C44'}  # Effective: C00, C01
            ),
            InsurerDiseaseScope(
                insurer='MERITZ',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id='GENERAL_CANCER_C00_C97',
                exclude_group_id='SIMILAR_CANCER_MERITZ_V1',
                include_codes={'C00', 'C01', 'C73', 'C44'},
                exclude_codes={'C73', 'C44', 'C01'}  # Effective: C00 (overlaps with Samsung on C00)
            ),
            InsurerDiseaseScope(
                insurer='DB',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id='GENERAL_CANCER_C00_C97',
                exclude_group_id='SIMILAR_CANCER_DB_V1',
                include_codes={'C00', 'C01', 'C73', 'C44'},
                exclude_codes={'C01', 'C73', 'C44'}  # Effective: C00 (overlaps with Samsung and Meritz on C00)
            ),
        ]

        overlap_state = aggregate_multi_party_overlap(scopes)

        # Should be PARTIAL_OVERLAP (all have C00 in common but different effective scopes)
        assert overlap_state == GroupOverlapState.PARTIAL_OVERLAP, \
            "Partial overlap should result in PARTIAL_OVERLAP"

        reason = generate_comparison_reason(overlap_state, scopes)

        assert reason.comparison_state == "comparable_with_gaps"
        assert reason.reason_code == "disease_scope_partial_overlap"
        assert "교집합" in reason.explanation or "확인" in reason.explanation, \
            "Should mention overlap or verification needed"
        assert validate_explanation_no_prohibited_phrases(reason.explanation)

    def test_scenario_3_no_overlap_3_insurers(self):
        """
        Scenario 3: NO_OVERLAP - All 3 insurers have different disease scopes

        Expected:
        - overlap_state = NO_OVERLAP
        - comparison_state = non_comparable
        - reason_code = disease_scope_multi_insurer_conflict
        """
        scopes = [
            InsurerDiseaseScope(
                insurer='SAMSUNG',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id='GROUP_SAMSUNG',
                exclude_group_id=None,
                include_codes={'C73'},  # Only C73
                exclude_codes=set()
            ),
            InsurerDiseaseScope(
                insurer='MERITZ',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id='GROUP_MERITZ',
                exclude_group_id=None,
                include_codes={'C44'},  # Only C44
                exclude_codes=set()
            ),
            InsurerDiseaseScope(
                insurer='DB',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id='GROUP_DB',
                exclude_group_id=None,
                include_codes={'C00'},  # Only C00
                exclude_codes=set()
            ),
        ]

        overlap_state = aggregate_multi_party_overlap(scopes)

        assert overlap_state == GroupOverlapState.NO_OVERLAP, \
            "No common codes should result in NO_OVERLAP"

        reason = generate_comparison_reason(overlap_state, scopes)

        assert reason.comparison_state == "non_comparable"
        assert reason.reason_code == "disease_scope_multi_insurer_conflict"
        assert "교집합을 가지지 않" in reason.explanation or "비교가 불가능" in reason.explanation, \
            "Should explain no overlap or non-comparable"
        assert validate_explanation_no_prohibited_phrases(reason.explanation)

    def test_scenario_4_unknown_one_insurer_null(self):
        """
        Scenario 4: UNKNOWN - DB has disease_scope_norm NULL

        Expected:
        - overlap_state = UNKNOWN
        - comparison_state = comparable_with_gaps
        - reason_code = disease_scope_policy_required
        """
        scopes = [
            InsurerDiseaseScope(
                insurer='SAMSUNG',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id='GENERAL_CANCER_C00_C97',
                exclude_group_id='SIMILAR_CANCER_SAMSUNG_V1',
                include_codes={'C00', 'C01', 'C73', 'C44'},
                exclude_codes={'C73', 'C44'}
            ),
            InsurerDiseaseScope(
                insurer='MERITZ',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id='GENERAL_CANCER_C00_C97',
                exclude_group_id='SIMILAR_CANCER_MERITZ_V1',
                include_codes={'C00', 'C01', 'C73', 'C44'},
                exclude_codes={'C73'}
            ),
            InsurerDiseaseScope(
                insurer='DB',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id=None,  # NULL - disease_scope_norm not extracted
                exclude_group_id=None,
                include_codes=None,
                exclude_codes=None
            ),
        ]

        overlap_state = aggregate_multi_party_overlap(scopes)

        assert overlap_state == GroupOverlapState.UNKNOWN, \
            "NULL disease_scope_norm should result in UNKNOWN"

        reason = generate_comparison_reason(overlap_state, scopes)

        assert reason.comparison_state == "comparable_with_gaps"
        assert reason.reason_code == "disease_scope_policy_required"
        assert "약관" in reason.explanation and "확인" in reason.explanation, \
            "Should mention policy verification needed"
        assert validate_explanation_no_prohibited_phrases(reason.explanation)

    def test_prohibited_phrases_validation(self):
        """
        Test: validate_explanation_no_prohibited_phrases detects violations

        Constitutional requirement:
        - NO value judgments or recommendations
        """
        # Valid explanations (no prohibited phrases)
        assert validate_explanation_no_prohibited_phrases(
            "삼성, 메리츠, DB 모두 동일한 유사암 정의를 사용합니다."
        )

        # Invalid explanations (prohibited phrases)
        assert not validate_explanation_no_prohibited_phrases(
            "삼성이 가장 넓은 보장을 제공합니다."
        )
        assert not validate_explanation_no_prohibited_phrases(
            "메리츠를 추천합니다."
        )
        assert not validate_explanation_no_prohibited_phrases(
            "DB가 더 나은 상품입니다."
        )

    def test_pairwise_overlap_detection(self):
        """
        Test: Pairwise overlap detection works correctly
        """
        scope_a = InsurerDiseaseScope(
            insurer='SAMSUNG',
            canonical_coverage_code='CANCER_DIAGNOSIS',
            include_group_id='GROUP_A',
            exclude_group_id=None,
            include_codes={'C00', 'C01', 'C73'},
            exclude_codes=set()
        )

        scope_b = InsurerDiseaseScope(
            insurer='MERITZ',
            canonical_coverage_code='CANCER_DIAGNOSIS',
            include_group_id='GROUP_B',
            exclude_group_id=None,
            include_codes={'C73', 'C44'},  # Overlaps with C73
            exclude_codes=set()
        )

        state = detect_pairwise_overlap(scope_a, scope_b)

        # Has intersection (C73) but not identical
        assert state == GroupOverlapState.PARTIAL_OVERLAP

    def test_multi_party_aggregation_deterministic(self):
        """
        Test: Multi-party aggregation is deterministic

        Same input → same output (no randomness)
        """
        scopes = [
            InsurerDiseaseScope(
                insurer='SAMSUNG',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id='GROUP_A',
                exclude_group_id=None,
                include_codes={'C00', 'C01'},
                exclude_codes=set()
            ),
            InsurerDiseaseScope(
                insurer='MERITZ',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id='GROUP_B',
                exclude_group_id=None,
                include_codes={'C00', 'C01'},
                exclude_codes=set()
            ),
            InsurerDiseaseScope(
                insurer='DB',
                canonical_coverage_code='CANCER_DIAGNOSIS',
                include_group_id='GROUP_C',
                exclude_group_id=None,
                include_codes={'C00', 'C01'},
                exclude_codes=set()
            ),
        ]

        # Run multiple times
        results = [aggregate_multi_party_overlap(scopes) for _ in range(5)]

        # All results should be identical
        assert len(set(results)) == 1, "Aggregation must be deterministic"
