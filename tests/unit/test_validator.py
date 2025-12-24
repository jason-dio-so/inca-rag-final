"""
STEP 6-B: Unit Tests for Validator Module

Constitutional Tests:
- Synthetic chunk rejection
- FK integrity enforcement
- Confidence thresholds
- Duplicate prevention
"""
import pytest
from unittest.mock import MagicMock, patch
from apps.api.app.ingest_llm.validator import CandidateValidator, ValidationResult
from apps.api.app.ingest_llm.models import EntityCandidate, ResolverResult


class TestCandidateValidator:
    """Unit tests for CandidateValidator"""

    @pytest.fixture
    def mock_conn(self):
        """Mock PostgreSQL connection"""
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cursor
        return conn, cursor

    @pytest.fixture
    def validator(self, mock_conn):
        """Create validator with mocked connection"""
        conn, _ = mock_conn
        return CandidateValidator(conn)

    @pytest.fixture
    def valid_candidate(self):
        """Valid candidate for testing"""
        return EntityCandidate(
            coverage_name_span="암진단비",
            entity_type="definition",
            confidence=0.95,
            text_offset=(0, 10)
        )

    # ========================================================================
    # Test 1: Constitutional Rule - Synthetic Chunk Rejection
    # ========================================================================

    def test_synthetic_chunk_rejected(self, validator, valid_candidate):
        """
        CONSTITUTIONAL TEST: is_synthetic=true MUST be rejected.

        This enforces compare-axis constitution (synthetic forbidden).
        """
        result = validator.validate_candidate(
            chunk_id=1,
            candidate=valid_candidate,
            is_synthetic=True  # SYNTHETIC
        )

        assert result.is_valid is False
        assert "synthetic" in result.reason.lower()
        assert "forbidden" in result.reason.lower()

    def test_non_synthetic_chunk_passes(self, validator, valid_candidate, mock_conn):
        """Non-synthetic chunk passes initial validation"""
        _, cursor = mock_conn

        # Mock chunk exists
        cursor.fetchone.return_value = (1,)

        result = validator.validate_candidate(
            chunk_id=1,
            candidate=valid_candidate,
            is_synthetic=False  # NON-SYNTHETIC
        )

        assert result.is_valid is True

    # ========================================================================
    # Test 2: FK Integrity - Chunk Existence
    # ========================================================================

    def test_chunk_not_found_rejected(self, validator, valid_candidate, mock_conn):
        """Candidate rejected if chunk_id doesn't exist (FK violation)"""
        _, cursor = mock_conn

        # Mock chunk does NOT exist
        cursor.fetchone.return_value = None

        result = validator.validate_candidate(
            chunk_id=999,  # Non-existent
            candidate=valid_candidate,
            is_synthetic=False
        )

        assert result.is_valid is False
        assert "chunk_id" in result.reason
        assert "not_found" in result.reason

    # ========================================================================
    # Test 3: Entity Type Validation
    # ========================================================================

    def test_invalid_entity_type_rejected(self, validator, mock_conn):
        """Invalid entity_type rejected by Pydantic (defense-in-depth)"""
        _, cursor = mock_conn
        cursor.fetchone.return_value = (1,)  # Chunk exists

        # Pydantic validates entity_type at model level (before validator)
        with pytest.raises(Exception) as exc_info:
            invalid_candidate = EntityCandidate(
                coverage_name_span="Test",
                entity_type="INVALID_TYPE",  # NOT in allowed list
                confidence=0.9
            )

        # Pydantic should raise ValidationError
        assert "entity_type" in str(exc_info.value).lower()

    @pytest.mark.parametrize("entity_type", [
        "definition",
        "condition",
        "exclusion",
        "amount",
        "benefit"
    ])
    def test_allowed_entity_types_pass(self, validator, entity_type, mock_conn):
        """All allowed entity types pass validation"""
        _, cursor = mock_conn
        cursor.fetchone.return_value = (1,)  # Chunk exists

        candidate = EntityCandidate(
            coverage_name_span="Test",
            entity_type=entity_type,
            confidence=0.9
        )

        result = validator.validate_candidate(
            chunk_id=1,
            candidate=candidate,
            is_synthetic=False
        )

        assert result.is_valid is True

    # ========================================================================
    # Test 4: Confidence Thresholds
    # ========================================================================

    @pytest.mark.parametrize("confidence,expected_valid", [
        (0.0, False),  # Too low (< 0.3 reject threshold)
        (0.2, False),  # Below reject threshold
        (0.29, False),  # Just below reject threshold
        (0.3, True),   # At reject threshold (passes but needs review)
        (0.5, True),   # Above reject, below review threshold
        (0.69, True),  # Just below review threshold
        (0.7, True),   # At review threshold
        (0.9, True),   # High confidence
        (1.0, True),   # Max confidence
    ])
    def test_confidence_thresholds(self, validator, confidence, expected_valid, mock_conn):
        """Confidence threshold enforcement"""
        _, cursor = mock_conn
        cursor.fetchone.return_value = (1,)  # Chunk exists

        candidate = EntityCandidate(
            coverage_name_span="Test",
            entity_type="definition",
            confidence=confidence
        )

        result = validator.validate_candidate(
            chunk_id=1,
            candidate=candidate,
            is_synthetic=False
        )

        assert result.is_valid == expected_valid

        if expected_valid and confidence < 0.7:
            # Should have warning for needs_review
            assert len(result.warnings) > 0
            assert "low_confidence" in result.warnings[0]

    def test_confidence_out_of_bounds_rejected(self, validator, mock_conn):
        """Confidence outside [0.0, 1.0] rejected by Pydantic (defense-in-depth)"""
        _, cursor = mock_conn
        cursor.fetchone.return_value = (1,)

        # Pydantic validates confidence bounds at model level
        with pytest.raises(Exception) as exc_info:
            candidate = EntityCandidate(
                coverage_name_span="Test",
                entity_type="definition",
                confidence=1.5  # Invalid (> 1.0)
            )

        # Pydantic should raise ValidationError
        assert "confidence" in str(exc_info.value).lower()

    # ========================================================================
    # Test 5: Coverage Name Validation
    # ========================================================================

    def test_empty_coverage_name_rejected(self, validator, mock_conn):
        """Empty coverage_name rejected by Pydantic (defense-in-depth)"""
        _, cursor = mock_conn
        cursor.fetchone.return_value = (1,)

        # Pydantic validates min_length at model level
        with pytest.raises(Exception) as exc_info:
            candidate = EntityCandidate(
                coverage_name_span="",  # EMPTY
                entity_type="definition",
                confidence=0.9
            )

        # Pydantic should raise ValidationError
        assert "coverage_name_span" in str(exc_info.value)

    def test_whitespace_only_coverage_name_rejected(self, validator, mock_conn):
        """Whitespace-only coverage_name rejected"""
        _, cursor = mock_conn
        cursor.fetchone.return_value = (1,)

        candidate = EntityCandidate(
            coverage_name_span="   ",  # WHITESPACE ONLY
            entity_type="definition",
            confidence=0.9
        )

        result = validator.validate_candidate(
            chunk_id=1,
            candidate=candidate,
            is_synthetic=False
        )

        assert result.is_valid is False
        assert "empty" in result.reason

    def test_too_long_coverage_name_rejected(self, validator, mock_conn):
        """Coverage name > 200 chars rejected by Pydantic (defense-in-depth)"""
        _, cursor = mock_conn
        cursor.fetchone.return_value = (1,)

        # Pydantic validates max_length at model level
        with pytest.raises(Exception) as exc_info:
            candidate = EntityCandidate(
                coverage_name_span="A" * 201,  # TOO LONG
                entity_type="definition",
                confidence=0.9
            )

        # Pydantic should raise ValidationError
        assert "coverage_name_span" in str(exc_info.value)

    # ========================================================================
    # Test 6: Resolver Result Validation (FK Enforcement)
    # ========================================================================

    def test_resolved_without_coverage_code_rejected(self, validator):
        """
        CONSTITUTIONAL TEST: status='resolved' requires coverage_code.
        Enforced at Pydantic level (defense-in-depth).
        """
        # Pydantic validates this at model creation
        with pytest.raises(Exception) as exc_info:
            result_obj = ResolverResult(
                status="resolved",
                resolved_coverage_code=None,  # MISSING - Pydantic catches this
                resolver_method="exact_alias"
            )

        # Pydantic should raise ValidationError
        assert "resolved_coverage_code" in str(exc_info.value)

    def test_resolved_with_nonexistent_coverage_code_rejected(self, validator, mock_conn):
        """
        CONSTITUTIONAL TEST: resolved coverage_code must exist in coverage_standard (FK).
        """
        _, cursor = mock_conn

        # Mock coverage_code does NOT exist
        cursor.fetchone.return_value = None

        result_obj = ResolverResult(
            status="resolved",
            resolved_coverage_code="FAKE_CODE_999",
            resolver_method="exact_alias"
        )

        validation = validator.validate_resolver_result(result_obj)

        assert validation.is_valid is False
        assert "FK_violation" in validation.reason
        assert "FAKE_CODE_999" in validation.reason

    def test_resolved_with_valid_coverage_code_passes(self, validator, mock_conn):
        """Valid coverage_code passes FK check"""
        _, cursor = mock_conn

        # Mock coverage_code EXISTS
        cursor.fetchone.return_value = (1,)

        result_obj = ResolverResult(
            status="resolved",
            resolved_coverage_code="A4200_1",
            resolver_method="exact_alias",
            resolver_confidence=1.0
        )

        validation = validator.validate_resolver_result(result_obj)

        assert validation.is_valid is True

    def test_needs_review_status_passes_without_fk_check(self, validator):
        """needs_review status doesn't require FK check"""
        result_obj = ResolverResult(
            status="needs_review",
            reason="ambiguous"
        )

        validation = validator.validate_resolver_result(result_obj)

        assert validation.is_valid is True

    def test_rejected_status_passes_without_fk_check(self, validator):
        """rejected status doesn't require FK check"""
        result_obj = ResolverResult(
            status="rejected",
            reason="no_match"
        )

        validation = validator.validate_resolver_result(result_obj)

        assert validation.is_valid is True

    # ========================================================================
    # Test 7: Duplicate Detection
    # ========================================================================

    def test_duplicate_in_candidates_detected(self, validator, mock_conn):
        """Duplicate in chunk_entity_candidate detected"""
        _, cursor = mock_conn

        # Mock: duplicate exists in candidates
        cursor.fetchone.side_effect = [(1,), None]  # Found in candidates, not in production

        is_duplicate = validator.check_duplicate(
            chunk_id=1,
            coverage_code="A4200_1",
            entity_type="definition"
        )

        assert is_duplicate is True

    def test_duplicate_in_production_detected(self, validator, mock_conn):
        """Duplicate in chunk_entity (production) detected"""
        _, cursor = mock_conn

        # Mock: not in candidates, but in production
        cursor.fetchone.side_effect = [None, (1,)]  # Not in candidates, found in production

        is_duplicate = validator.check_duplicate(
            chunk_id=1,
            coverage_code="A4200_1",
            entity_type="definition"
        )

        assert is_duplicate is True

    def test_no_duplicate_detected(self, validator, mock_conn):
        """No duplicate (new candidate)"""
        _, cursor = mock_conn

        # Mock: not found in either table
        cursor.fetchone.side_effect = [None, None]

        is_duplicate = validator.check_duplicate(
            chunk_id=1,
            coverage_code="A4200_1",
            entity_type="definition"
        )

        assert is_duplicate is False

    # ========================================================================
    # Test 8: Duplicate Merging
    # ========================================================================

    def test_merge_duplicates_keeps_highest_confidence(self, validator):
        """Duplicate merging keeps highest confidence candidate"""
        candidates = [
            (1, EntityCandidate(coverage_name_span="암진단비", entity_type="definition", confidence=0.7)),
            (1, EntityCandidate(coverage_name_span="암진단비", entity_type="definition", confidence=0.9)),  # HIGHEST
            (1, EntityCandidate(coverage_name_span="암진단비", entity_type="definition", confidence=0.8)),
        ]

        merged = validator.merge_duplicates(candidates)

        assert len(merged) == 1
        assert merged[0][1].confidence == 0.9

    def test_merge_duplicates_keeps_different_entity_types(self, validator):
        """Different entity_types are NOT duplicates"""
        candidates = [
            (1, EntityCandidate(coverage_name_span="암진단비", entity_type="definition", confidence=0.7)),
            (1, EntityCandidate(coverage_name_span="암진단비", entity_type="condition", confidence=0.8)),
        ]

        merged = validator.merge_duplicates(candidates)

        assert len(merged) == 2  # Both kept (different entity_type)

    # ========================================================================
    # Test 9: Status Determination Logic
    # ========================================================================

    @pytest.mark.parametrize("resolver_status,confidence,expected_status", [
        ("resolved", 0.95, "resolved"),  # High confidence + resolved → resolved
        ("resolved", 0.7, "resolved"),   # At threshold + resolved → resolved
        ("resolved", 0.69, "needs_review"),  # Below threshold → needs_review
        ("resolved", 0.5, "needs_review"),  # Low confidence → needs_review
        ("needs_review", 0.95, "needs_review"),  # Resolver says review → review
        ("rejected", 0.95, "rejected"),  # Resolver says rejected → rejected
    ])
    def test_status_determination(self, validator, resolver_status, confidence, expected_status):
        """Status determination based on resolver + confidence"""
        candidate = EntityCandidate(
            coverage_name_span="Test",
            entity_type="definition",
            confidence=confidence
        )

        resolver_result = ResolverResult(
            status=resolver_status,
            resolved_coverage_code="A4200_1" if resolver_status == "resolved" else None,
            resolver_method="exact_alias"
        )

        final_status = validator.determine_status(candidate, resolver_result)

        assert final_status == expected_status


# ========================================================================
# Integration-style Tests (with DB mocking)
# ========================================================================

class TestValidatorIntegration:
    """Integration-style tests for validator with full flow"""

    def test_full_validation_flow_success(self):
        """Complete validation flow: candidate + resolver result"""
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cursor

        # Mock: chunk exists, coverage exists, no duplicates
        cursor.fetchone.side_effect = [
            (1,),  # Chunk exists
            (1,),  # Coverage exists
            None,  # No duplicate in candidates
            None,  # No duplicate in production
        ]

        validator = CandidateValidator(conn)

        # Validate candidate
        candidate = EntityCandidate(
            coverage_name_span="암진단비",
            entity_type="definition",
            confidence=0.95
        )

        candidate_validation = validator.validate_candidate(
            chunk_id=1,
            candidate=candidate,
            is_synthetic=False
        )

        assert candidate_validation.is_valid is True

        # Validate resolver result
        resolver_result = ResolverResult(
            status="resolved",
            resolved_coverage_code="A4200_1",
            resolver_method="exact_alias",
            resolver_confidence=1.0
        )

        resolver_validation = validator.validate_resolver_result(resolver_result)

        assert resolver_validation.is_valid is True

        # Check duplicate
        is_duplicate = validator.check_duplicate(1, "A4200_1", "definition")

        assert is_duplicate is False

        # Final status
        final_status = validator.determine_status(candidate, resolver_result)

        assert final_status == "resolved"
