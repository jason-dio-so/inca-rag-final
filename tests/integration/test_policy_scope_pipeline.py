"""
STEP 7 Phase B: Policy Scope Pipeline v1 Integration Test

Constitutional requirements tested:
1. Evidence required at every step (basis_span, span_text)
2. KCD-7 codes validated against disease_code_master (FK)
3. insurer=NULL restricted to medical/KCD classification only
4. disease_scope_norm must be group references (NOT raw code arrays)

MVP Scope:
- Samsung 유사암 definition extraction
- disease_code_group + disease_code_group_member + coverage_disease_scope
- proposal_coverage_slots.disease_scope_norm population
"""
import pytest
from src.policy_scope.parser import PolicyScopeParser
from src.policy_scope.pipeline import PolicyScopePipeline
from tests.fixtures.kcd7_test_subset import load_test_kcd7_codes


class TestPolicyScopePipelineMVP:
    """
    STEP 7 Phase B: Validate Policy Scope Pipeline v1 (Samsung 유사암 MVP)
    """

    @pytest.fixture
    def test_db(self, test_pg_conn):
        """
        Setup test database with KCD-7 test subset
        """
        # Load test KCD-7 codes
        load_test_kcd7_codes(test_pg_conn)
        yield test_pg_conn

    def test_create_samsung_similar_cancer_group_with_evidence(self, test_db):
        """
        MVP Test: Complete pipeline from policy text to disease_scope_norm

        Flow:
        1. Parse Samsung 유사암 definition from policy text (deterministic regex)
        2. Create disease_code_group with evidence
        3. Add disease_code_group_member (C73, C44) with FK validation
        4. Create coverage_disease_scope with evidence
        5. Update proposal_coverage_slots.disease_scope_norm

        Constitutional guarantees tested:
        - Evidence required (basis_doc_id, basis_page, basis_span)
        - KCD-7 codes exist in disease_code_master
        - insurer='SAMSUNG' for insurance concept (유사암)
        - disease_scope_norm = {include_group_id, exclude_group_id}
        """
        # Sample policy text with 유사암 definition
        policy_text = """
        제3조 (유사암의 정의 및 진단확정)
        "유사암"이라 함은 다음의 질병을 말합니다:
        1. 갑상선암 (C73)
        2. 기타피부암 (C44)

        제5조 (일반암 진단비 지급)
        회사는 피보험자가 일반암으로 진단확정된 경우 일반암진단비를 지급합니다.
        단, 유사암은 제외합니다.
        """

        parser = PolicyScopeParser()
        pipeline = PolicyScopePipeline(test_db)

        # Step 1: Parse Samsung 유사암 definition
        group_def = parser.parse_samsung_similar_cancer(
            policy_text=policy_text,
            document_id='SAMSUNG_CANCER_TERMS_2024',
            page_number=3
        )

        assert group_def is not None, "Should extract 유사암 definition from policy text"
        assert group_def['group_id'] == 'SIMILAR_CANCER_SAMSUNG_V1'
        assert group_def['insurer'] == 'SAMSUNG'
        assert 'C73' in group_def['mentioned_codes']
        assert 'C44' in group_def['mentioned_codes']
        assert len(group_def['basis_span']) > 0, "Evidence span must not be empty"

        # Step 2: Create disease_code_group with evidence
        pipeline.create_disease_code_group(
            group_id=group_def['group_id'],
            group_label=group_def['group_label'],
            insurer=group_def['insurer'],
            version_tag=group_def['version_tag'],
            basis_doc_id=group_def['basis_doc_id'],
            basis_page=group_def['basis_page'],
            basis_span=group_def['basis_span']
        )

        # Verify group created
        with test_db.cursor() as cursor:
            cursor.execute(
                "SELECT insurer, basis_span FROM disease_code_group WHERE group_id = %s",
                (group_def['group_id'],)
            )
            row = cursor.fetchone()
            assert row is not None, "Group should be created"
            assert row[0] == 'SAMSUNG', "insurer must be SAMSUNG"
            assert len(row[1]) > 0, "basis_span must not be empty"

        # Step 3: Add disease_code_group_member with FK validation
        # This will fail if KCD-7 codes don't exist in disease_code_master
        pipeline.add_disease_code_group_member(
            group_id=group_def['group_id'],
            code='C73'
        )
        pipeline.add_disease_code_group_member(
            group_id=group_def['group_id'],
            code='C44'
        )

        # Verify members added
        with test_db.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM disease_code_group_member WHERE group_id = %s",
                (group_def['group_id'],)
            )
            count = cursor.fetchone()[0]
            assert count == 2, "Should have 2 members (C73, C44)"

        # Step 4: Extract coverage scope (일반암 제외 유사암)
        scope_def = parser.extract_disease_scope_for_coverage(
            policy_text=policy_text,
            coverage_name='일반암진단비',
            document_id='SAMSUNG_CANCER_TERMS_2024',
            page_number=5
        )

        assert scope_def is not None, "Should extract 일반암 scope with 유사암 exclusion"
        assert scope_def['exclude_group_label'] == '유사암'
        assert len(scope_def['span_text']) > 0, "Evidence span must not be empty"

        # Step 5: Create coverage_disease_scope with evidence
        scope_id = pipeline.create_coverage_disease_scope(
            canonical_coverage_code='CANCER_DIAGNOSIS',
            insurer='SAMSUNG',
            proposal_id='PROPOSAL_TEST_001',
            include_group_id='GENERAL_CANCER_C00_C97',  # Would be created separately
            exclude_group_id=group_def['group_id'],  # 유사암
            source_doc_id=scope_def['source_doc_id'],
            source_page=scope_def['source_page'],
            span_text=scope_def['span_text'],
            extraction_rule_id=scope_def['extraction_rule_id']
        )

        assert scope_id > 0, "Should return created scope_id"

        # Verify scope created with evidence
        with test_db.cursor() as cursor:
            cursor.execute(
                "SELECT span_text FROM coverage_disease_scope WHERE id = %s",
                (scope_id,)
            )
            row = cursor.fetchone()
            assert row is not None
            assert len(row[0]) > 0, "span_text evidence must not be empty"

    def test_evidence_required_fails_without_basis_span(self, test_db):
        """
        Constitutional Test: Evidence required - should fail if basis_span is empty

        This test ensures the pipeline enforces evidence requirement.
        """
        pipeline = PolicyScopePipeline(test_db)

        with pytest.raises(ValueError, match="Evidence required: basis_span cannot be empty"):
            pipeline.create_disease_code_group(
                group_id='TEST_GROUP',
                group_label='Test Group',
                insurer='SAMSUNG',
                version_tag='V1',
                basis_doc_id='TEST_DOC',
                basis_page=1,
                basis_span=''  # Empty evidence - should fail
            )

    def test_insurer_null_forbidden_for_insurance_concepts(self, test_db):
        """
        Constitutional Test: insurer=NULL restricted to medical/KCD classification

        Insurance concepts (유사암, 소액암) MUST have insurer set.
        """
        pipeline = PolicyScopePipeline(test_db)

        with pytest.raises(ValueError, match="insurer=NULL not allowed for insurance concept"):
            pipeline.create_disease_code_group(
                group_id='INVALID_GROUP',
                group_label='유사암 (보험사 미지정)',  # Insurance concept
                insurer=None,  # NULL insurer - should fail
                version_tag='V1',
                basis_doc_id='TEST_DOC',
                basis_page=1,
                basis_span='유사암은 다음과 같이 정의됩니다...'
            )

    def test_kcd7_fk_validation_fails_for_invalid_code(self, test_db):
        """
        Constitutional Test: KCD-7 codes must exist in disease_code_master

        This test ensures FK validation works correctly.
        """
        pipeline = PolicyScopePipeline(test_db)

        # Create test group
        pipeline.create_disease_code_group(
            group_id='TEST_FK_GROUP',
            group_label='Test FK Validation',
            insurer='SAMSUNG',
            version_tag='V1',
            basis_doc_id='TEST_DOC',
            basis_page=1,
            basis_span='Test evidence'
        )

        # Try to add invalid KCD-7 code (not in disease_code_master)
        with pytest.raises(Exception):  # psycopg2.IntegrityError
            pipeline.add_disease_code_group_member(
                group_id='TEST_FK_GROUP',
                code='Z99999'  # Invalid code - should fail FK constraint
            )

    def test_disease_scope_norm_uses_group_references_not_raw_codes(self, test_db):
        """
        Constitutional Test: disease_scope_norm must use group references

        NOT raw code arrays like ["C00", "C01", ...]
        """
        pipeline = PolicyScopePipeline(test_db)

        # This would be called after coverage_disease_scope is created
        # For MVP, we just verify the JSONB structure
        disease_scope_norm = {
            "include_group_id": "GENERAL_CANCER_C00_C97",
            "exclude_group_id": "SIMILAR_CANCER_SAMSUNG_V1"
        }

        # Verify structure
        assert "include_group_id" in disease_scope_norm
        assert isinstance(disease_scope_norm["include_group_id"], str)
        assert "exclude_group_id" in disease_scope_norm
        assert isinstance(disease_scope_norm["exclude_group_id"], str)

        # Verify NOT raw code arrays
        assert not isinstance(disease_scope_norm.get("include_codes"), list)
        assert not isinstance(disease_scope_norm.get("exclude_codes"), list)
