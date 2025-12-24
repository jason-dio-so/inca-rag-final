"""
STEP 6-B: Validator Module for Candidate Validation

Purpose: Validate LLM candidates before storage/resolution.

Constitutional Principles:
- Synthetic chunks REJECTED (is_synthetic=true forbidden)
- FK integrity enforced (coverage_code must exist in coverage_standard)
- Duplicate prevention
- Confidence-based gating
"""
from typing import Optional, List, Tuple
from psycopg2.extensions import connection as PGConnection
import logging
from .models import EntityCandidate, ResolverResult

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails (non-recoverable)"""
    pass


class ValidationResult:
    """
    Result of candidate validation.

    Attributes:
        is_valid: Whether validation passed
        reason: Reason for rejection (if not valid)
        warnings: Non-fatal issues (logged but not rejected)
    """

    def __init__(
        self,
        is_valid: bool,
        reason: Optional[str] = None,
        warnings: Optional[List[str]] = None
    ):
        self.is_valid = is_valid
        self.reason = reason
        self.warnings = warnings or []


class CandidateValidator:
    """
    Validator for LLM candidate entities.

    Constitutional Guarantees:
    - Synthetic chunks NEVER validated (compare-axis forbidden)
    - FK integrity verified before resolution
    - Confidence thresholds enforced
    """

    # Allowed entity types (from design doc)
    ALLOWED_ENTITY_TYPES = {
        "definition",
        "condition",
        "exclusion",
        "amount",
        "benefit"
    }

    # Confidence thresholds
    CONFIDENCE_MIN = 0.0
    CONFIDENCE_MAX = 1.0
    CONFIDENCE_REJECT_THRESHOLD = 0.3  # Below this → auto-reject
    CONFIDENCE_REVIEW_THRESHOLD = 0.7  # Below this → needs_review

    def __init__(self, conn: PGConnection):
        """
        Initialize validator with database connection.

        Args:
            conn: PostgreSQL connection (for FK checks)
        """
        self.conn = conn

    def validate_candidate(
        self,
        chunk_id: int,
        candidate: EntityCandidate,
        is_synthetic: bool = False
    ) -> ValidationResult:
        """
        Validate single LLM candidate.

        Args:
            chunk_id: Chunk ID (FK to chunk table)
            candidate: EntityCandidate from LLM
            is_synthetic: Whether chunk is synthetic (from chunk.is_synthetic)

        Returns:
            ValidationResult with pass/fail + reason

        Constitutional Rule 1: Synthetic chunks REJECTED
        """
        warnings = []

        # Rule 1: Synthetic chunks FORBIDDEN (constitutional)
        if is_synthetic:
            return ValidationResult(
                is_valid=False,
                reason="synthetic_chunk_forbidden_by_constitution"
            )

        # Rule 2: Chunk ID must exist (FK integrity)
        if not self._verify_chunk_exists(chunk_id):
            return ValidationResult(
                is_valid=False,
                reason=f"chunk_id_{chunk_id}_not_found"
            )

        # Rule 3: Entity type must be allowed
        if candidate.entity_type not in self.ALLOWED_ENTITY_TYPES:
            return ValidationResult(
                is_valid=False,
                reason=f"invalid_entity_type_{candidate.entity_type}"
            )

        # Rule 4: Confidence bounds check
        if not (self.CONFIDENCE_MIN <= candidate.confidence <= self.CONFIDENCE_MAX):
            return ValidationResult(
                is_valid=False,
                reason=f"confidence_out_of_bounds_{candidate.confidence}"
            )

        # Rule 5: Confidence threshold - auto-reject if too low
        if candidate.confidence < self.CONFIDENCE_REJECT_THRESHOLD:
            return ValidationResult(
                is_valid=False,
                reason=f"confidence_below_threshold_{candidate.confidence}<{self.CONFIDENCE_REJECT_THRESHOLD}"
            )

        # Rule 6: Coverage name not empty
        if not candidate.coverage_name_span or len(candidate.coverage_name_span.strip()) == 0:
            return ValidationResult(
                is_valid=False,
                reason="coverage_name_empty"
            )

        # Rule 7: Coverage name length check (prevent abuse)
        if len(candidate.coverage_name_span) > 200:
            return ValidationResult(
                is_valid=False,
                reason=f"coverage_name_too_long_{len(candidate.coverage_name_span)}_chars"
            )

        # Warning: Low confidence (needs review but not rejected)
        if candidate.confidence < self.CONFIDENCE_REVIEW_THRESHOLD:
            warnings.append(f"low_confidence_{candidate.confidence}<{self.CONFIDENCE_REVIEW_THRESHOLD}_needs_review")

        # All checks passed
        return ValidationResult(is_valid=True, warnings=warnings)

    def validate_resolver_result(
        self,
        result: ResolverResult
    ) -> ValidationResult:
        """
        Validate resolver result before storage.

        Args:
            result: ResolverResult from resolver

        Returns:
            ValidationResult

        Constitutional Rule: coverage_code must exist in coverage_standard (FK)
        """
        # If status is not resolved, no FK check needed
        if result.status != "resolved":
            return ValidationResult(is_valid=True)

        # Status=resolved requires coverage_code
        if not result.resolved_coverage_code:
            return ValidationResult(
                is_valid=False,
                reason="resolved_status_requires_coverage_code"
            )

        # FK Check: coverage_code must exist in coverage_standard
        if not self._verify_coverage_exists(result.resolved_coverage_code):
            return ValidationResult(
                is_valid=False,
                reason=f"coverage_code_{result.resolved_coverage_code}_not_in_coverage_standard_FK_violation"
            )

        return ValidationResult(is_valid=True)

    def check_duplicate(
        self,
        chunk_id: int,
        coverage_code: str,
        entity_type: str
    ) -> bool:
        """
        Check if candidate already exists (duplicate prevention).

        Args:
            chunk_id: Chunk ID
            coverage_code: Canonical coverage code
            entity_type: Entity type

        Returns:
            True if duplicate exists, False otherwise
        """
        try:
            with self.conn.cursor() as cur:
                # Check chunk_entity_candidate
                cur.execute("""
                    SELECT 1
                    FROM chunk_entity_candidate
                    WHERE chunk_id = %s
                      AND resolved_coverage_code = %s
                      AND resolved_entity_type = %s
                      AND resolver_status = 'resolved'
                    LIMIT 1
                """, (chunk_id, coverage_code, entity_type))

                if cur.fetchone():
                    return True  # Duplicate in candidates

                # Check production chunk_entity (already confirmed)
                cur.execute("""
                    SELECT 1
                    FROM chunk_entity
                    WHERE chunk_id = %s
                      AND coverage_code = %s
                      AND entity_type = %s
                    LIMIT 1
                """, (chunk_id, coverage_code, entity_type))

                if cur.fetchone():
                    return True  # Duplicate in production

                return False  # No duplicate

        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            # Err on side of caution: assume duplicate to prevent bad writes
            return True

    def merge_duplicates(
        self,
        candidates: List[Tuple[int, EntityCandidate]]
    ) -> List[Tuple[int, EntityCandidate]]:
        """
        Merge duplicate candidates (same chunk_id + coverage_name + entity_type).

        Strategy: Keep highest confidence candidate, drop others.

        Args:
            candidates: List of (chunk_id, EntityCandidate) tuples

        Returns:
            Deduplicated list
        """
        # Group by (chunk_id, coverage_name, entity_type)
        groups = {}
        for chunk_id, candidate in candidates:
            key = (chunk_id, candidate.coverage_name_span, candidate.entity_type)
            if key not in groups:
                groups[key] = []
            groups[key].append((chunk_id, candidate))

        # Keep highest confidence from each group
        deduplicated = []
        for group_candidates in groups.values():
            best = max(group_candidates, key=lambda x: x[1].confidence)
            deduplicated.append(best)

        dropped_count = len(candidates) - len(deduplicated)
        if dropped_count > 0:
            logger.info(f"Merged {dropped_count} duplicate candidates")

        return deduplicated

    def determine_status(
        self,
        candidate: EntityCandidate,
        resolver_result: ResolverResult
    ) -> str:
        """
        Determine final candidate status based on confidence + resolver result.

        Args:
            candidate: Original LLM candidate
            resolver_result: Resolver result

        Returns:
            Status string: 'resolved' | 'needs_review' | 'rejected'

        Logic:
        - resolver_result.status='resolved' + confidence >= 0.7 → 'resolved'
        - resolver_result.status='resolved' + confidence < 0.7 → 'needs_review'
        - resolver_result.status='needs_review' → 'needs_review'
        - resolver_result.status='rejected' → 'rejected'
        """
        if resolver_result.status == "rejected":
            return "rejected"

        if resolver_result.status == "needs_review":
            return "needs_review"

        # resolver_result.status == "resolved"
        if candidate.confidence >= self.CONFIDENCE_REVIEW_THRESHOLD:
            return "resolved"  # High confidence + resolved → ready
        else:
            return "needs_review"  # Low confidence → manual review needed

    def _verify_chunk_exists(self, chunk_id: int) -> bool:
        """
        Verify chunk exists in chunk table (FK check).

        Args:
            chunk_id: Chunk ID

        Returns:
            True if exists, False otherwise
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT 1
                    FROM chunk
                    WHERE chunk_id = %s
                """, (chunk_id,))

                return cur.fetchone() is not None

        except Exception as e:
            logger.error(f"Chunk existence check failed: {e}")
            return False

    def _verify_coverage_exists(self, coverage_code: str) -> bool:
        """
        Verify coverage_code exists in coverage_standard (FK check).

        Constitutional Guarantee: NO auto-INSERT (read-only check).

        Args:
            coverage_code: Canonical coverage code

        Returns:
            True if exists, False otherwise
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT 1
                    FROM coverage_standard
                    WHERE coverage_code = %s
                """, (coverage_code,))

                return cur.fetchone() is not None

        except Exception as e:
            logger.error(f"Coverage existence check failed: {e}")
            return False
