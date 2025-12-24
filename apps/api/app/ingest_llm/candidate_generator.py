"""
STEP 6-B: Candidate Generator - LLM + Resolver Integration

Constitutional Guarantees:
- LLM proposes candidates (coverage_name_span + confidence)
- Resolver validates and maps to canonical coverage_code
- Validator enforces FK integrity (coverage_code must exist)
- NO auto-INSERT into coverage_standard
- NO auto-confirm to production (chunk_entity)

Flow:
1. LLM extracts coverage_name_span from chunk text
2. Resolver maps coverage_name_span → canonical coverage_code (신정원 통일코드)
3. Validator checks FK integrity + synthetic rejection
4. Repository stores as candidate (NOT production entity)
"""
import logging
from typing import List, Optional
from psycopg2.extensions import connection as PGConnection

from .llm_client import LLMClientProtocol, ChunkInput
from .resolver import CoverageResolver
from .validator import CandidateValidator, ValidationResult
from .repository import CandidateRepository
from .models import (
    LLMCandidateResponse,
    EntityCandidate,
    ResolverResult
)

logger = logging.getLogger(__name__)


class CandidateGenerationResult:
    """
    Result of candidate generation for a single chunk.

    Tracks:
    - LLM proposals
    - Resolver decisions
    - Validation outcomes
    - Final storage status
    """

    def __init__(self, chunk_id: int):
        self.chunk_id = chunk_id
        self.llm_proposals: List[EntityCandidate] = []
        self.resolved_candidates: List[dict] = []  # Candidates with resolved coverage_code
        self.validation_failures: List[dict] = []  # Rejected candidates
        self.stored_candidate_ids: List[int] = []  # DB candidate_id list

    @property
    def total_proposals(self) -> int:
        """Total LLM proposals"""
        return len(self.llm_proposals)

    @property
    def total_resolved(self) -> int:
        """Total resolved candidates"""
        return len(self.resolved_candidates)

    @property
    def total_stored(self) -> int:
        """Total stored in repository"""
        return len(self.stored_candidate_ids)


class CandidateGenerator:
    """
    Candidate Generator - Orchestrates LLM + Resolver + Validator.

    Constitutional Guarantees:
    - LLM proposes, Resolver validates, Validator enforces
    - NO auto-INSERT into coverage_standard
    - NO auto-confirm to production
    - Synthetic chunks REJECTED
    """

    def __init__(
        self,
        conn: PGConnection,
        llm_client: LLMClientProtocol
    ):
        """
        Initialize candidate generator.

        Args:
            conn: PostgreSQL connection (read-only for FK checks)
            llm_client: LLM client (real or fake)
        """
        self.conn = conn
        self.llm_client = llm_client

        # Initialize components
        self.resolver = CoverageResolver(conn)
        self.validator = CandidateValidator(conn)
        self.repository = CandidateRepository(conn)

        logger.info("CandidateGenerator initialized")

    def generate_and_store_candidates(
        self,
        chunks: List[ChunkInput],
        *,
        request_id: str,
        skip_llm: bool = False
    ) -> List[CandidateGenerationResult]:
        """
        Generate and store candidates for chunk batch.

        Flow:
        1. LLM proposes candidates (or skip if flag set)
        2. Resolver maps coverage_name → canonical code
        3. Validator checks FK integrity + synthetic rejection
        4. Repository stores validated candidates

        Args:
            chunks: List of chunks to process
            request_id: Unique request ID for logging
            skip_llm: If True, skip LLM call (rule-only mode)

        Returns:
            List of CandidateGenerationResult (1 per chunk)
        """
        logger.info(
            f"[{request_id}] generate_and_store_candidates: "
            f"chunks={len(chunks)}, skip_llm={skip_llm}"
        )

        results: List[CandidateGenerationResult] = []

        # Step 1: LLM proposal (batch)
        if skip_llm:
            logger.info(f"[{request_id}] LLM SKIPPED (rule-only mode)")
            llm_responses = [LLMCandidateResponse(candidates=[]) for _ in chunks]
        else:
            llm_responses = self.llm_client.generate_candidates(
                chunks,
                request_id=request_id
            )

        # Step 2-4: Process each chunk's candidates
        for chunk_input, llm_response in zip(chunks, llm_responses):
            result = self._process_chunk_candidates(
                chunk_input=chunk_input,
                llm_response=llm_response,
                request_id=request_id
            )
            results.append(result)

        logger.info(
            f"[{request_id}] generate_and_store_candidates: completed {len(results)} chunks"
        )
        return results

    def _process_chunk_candidates(
        self,
        chunk_input: ChunkInput,
        llm_response: LLMCandidateResponse,
        request_id: str
    ) -> CandidateGenerationResult:
        """
        Process candidates for a single chunk.

        Steps:
        1. Resolver: coverage_name → canonical code
        2. Validator: FK check + synthetic rejection
        3. Repository: store validated candidates

        Args:
            chunk_input: Chunk metadata
            llm_response: LLM proposals
            request_id: Request ID for logging

        Returns:
            CandidateGenerationResult
        """
        result = CandidateGenerationResult(chunk_id=chunk_input.chunk_id)
        result.llm_proposals = llm_response.candidates

        logger.debug(
            f"[{request_id}] Processing chunk_id={chunk_input.chunk_id}: "
            f"{len(llm_response.candidates)} proposals"
        )

        for llm_candidate in llm_response.candidates:
            try:
                # Step 1: Resolver - coverage_name → canonical code
                resolver_result = self.resolver.resolve_coverage_name(
                    llm_candidate.coverage_name_span
                )

                logger.debug(
                    f"[{request_id}] Resolver: chunk_id={chunk_input.chunk_id}, "
                    f"name={llm_candidate.coverage_name_span}, "
                    f"status={resolver_result.status}, "
                    f"code={resolver_result.resolved_coverage_code}"
                )

                # Skip if resolver rejected
                if resolver_result.status == "rejected":
                    result.validation_failures.append({
                        "coverage_name_span": llm_candidate.coverage_name_span,
                        "reason": f"Resolver rejected: {resolver_result.reason}"
                    })
                    continue

                # Build candidate data
                candidate_data = {
                    "chunk_id": chunk_input.chunk_id,
                    "coverage_name_raw": llm_candidate.coverage_name_span,
                    "entity_type_proposed": llm_candidate.entity_type,
                    "confidence": llm_candidate.confidence,
                    "resolved_coverage_code": resolver_result.resolved_coverage_code,
                    "resolver_status": resolver_result.status,
                    "resolver_method": resolver_result.resolver_method,
                    "content": chunk_input.content  # For content-hash deduplication
                }

                # Step 2: Validator - FK + synthetic + duplicate checks
                validation = self.validator.validate_candidate(
                    chunk_id=chunk_input.chunk_id,
                    coverage_name_raw=llm_candidate.coverage_name_span,
                    entity_type_proposed=llm_candidate.entity_type,
                    confidence=llm_candidate.confidence,
                    resolved_coverage_code=resolver_result.resolved_coverage_code,
                    resolver_status=resolver_result.status
                )

                if not validation.is_valid:
                    result.validation_failures.append({
                        "coverage_name_span": llm_candidate.coverage_name_span,
                        "reason": f"Validator rejected: {validation.reason}"
                    })
                    logger.debug(
                        f"[{request_id}] Validator REJECTED: chunk_id={chunk_input.chunk_id}, "
                        f"reason={validation.reason}"
                    )
                    continue

                # Step 3: Repository - store validated candidate
                content_hash = self.repository.compute_content_hash(chunk_input.content)
                candidate_data["content_hash"] = content_hash

                candidate_id = self.repository.insert_candidate(**candidate_data)

                result.resolved_candidates.append(candidate_data)
                result.stored_candidate_ids.append(candidate_id)

                logger.info(
                    f"[{request_id}] Candidate STORED: candidate_id={candidate_id}, "
                    f"chunk_id={chunk_input.chunk_id}, "
                    f"coverage_code={resolver_result.resolved_coverage_code}, "
                    f"status={resolver_result.status}"
                )

            except Exception as e:
                # Log error but continue with next candidate
                logger.error(
                    f"[{request_id}] Failed to process candidate: "
                    f"chunk_id={chunk_input.chunk_id}, "
                    f"coverage_name={llm_candidate.coverage_name_span}, "
                    f"error={e}",
                    exc_info=True
                )
                result.validation_failures.append({
                    "coverage_name_span": llm_candidate.coverage_name_span,
                    "reason": f"Processing error: {str(e)}"
                })

        logger.debug(
            f"[{request_id}] Chunk processed: chunk_id={chunk_input.chunk_id}, "
            f"proposals={result.total_proposals}, "
            f"resolved={result.total_resolved}, "
            f"stored={result.total_stored}, "
            f"failures={len(result.validation_failures)}"
        )

        return result
