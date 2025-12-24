"""
STEP 6-B: Repository Layer for Candidate Storage

Purpose: CRUD operations for chunk_entity_candidate and amount_entity_candidate.

Constitutional Principles:
- Store candidates only (NO auto-confirm to production)
- Content-hash based deduplication
- Atomic transactions
- Audit trail preservation
"""
import hashlib
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from psycopg2.extensions import connection as PGConnection
from psycopg2 import sql
from .models import EntityCandidate, ResolverResult

logger = logging.getLogger(__name__)


class CandidateRepository:
    """
    Repository for managing LLM candidate entities.

    Constitutional Guarantee:
    - Candidates stored in separate tables (NOT production chunk_entity)
    - Confirmation to production is MANUAL ONLY (not in this repository)
    """

    def __init__(self, conn: PGConnection):
        """
        Initialize repository with database connection.

        Args:
            conn: PostgreSQL connection
        """
        self.conn = conn

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """
        Compute SHA-256 hash of chunk content for deduplication.

        Args:
            content: Chunk text content

        Returns:
            64-character hex string (SHA-256)
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def insert_candidate(
        self,
        chunk_id: int,
        candidate: EntityCandidate,
        llm_metadata: Dict[str, Any],
        content_hash: Optional[str] = None,
        prefilter_passed: bool = True
    ) -> Optional[int]:
        """
        Insert LLM candidate into chunk_entity_candidate table.

        Args:
            chunk_id: Chunk ID (FK to chunk table)
            candidate: EntityCandidate from LLM
            llm_metadata: LLM call metadata (model, tokens, prompt_version, response_raw)
            content_hash: SHA-256 of chunk.content (for deduplication)
            prefilter_passed: Whether passed prefilter

        Returns:
            candidate_id if inserted, None if duplicate (content_hash match)

        Constitutional Guarantee:
        - Only inserts into candidate table (NOT chunk_entity)
        - Duplicate prevention via content_hash
        """
        try:
            with self.conn.cursor() as cur:
                # Check for duplicate via content_hash (if provided)
                if content_hash:
                    cur.execute("""
                        SELECT candidate_id
                        FROM chunk_entity_candidate
                        WHERE content_hash = %s
                          AND coverage_name_raw = %s
                          AND entity_type_proposed = %s
                        LIMIT 1
                    """, (content_hash, candidate.coverage_name_span, candidate.entity_type))

                    row = cur.fetchone()
                    if row:
                        logger.info(f"Duplicate candidate found (content_hash={content_hash[:16]}...), skipping insert")
                        return None  # Duplicate

                # Insert new candidate
                cur.execute("""
                    INSERT INTO chunk_entity_candidate (
                        chunk_id,
                        coverage_name_raw,
                        entity_type_proposed,
                        text_offset,
                        confidence,
                        llm_model,
                        llm_prompt_version,
                        llm_response_raw,
                        llm_tokens_used,
                        llm_called_at,
                        content_hash,
                        prefilter_passed,
                        resolver_status,
                        created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, NOW()
                    )
                    RETURNING candidate_id
                """, (
                    chunk_id,
                    candidate.coverage_name_span,
                    candidate.entity_type,
                    list(candidate.text_offset) if candidate.text_offset else None,
                    candidate.confidence,
                    llm_metadata.get('llm_model'),
                    llm_metadata.get('llm_prompt_version'),
                    llm_metadata.get('llm_response_raw'),  # JSONB
                    llm_metadata.get('llm_tokens_used'),
                    llm_metadata.get('llm_called_at', datetime.now()),
                    content_hash,
                    prefilter_passed,
                    'pending'  # Initial status
                ))

                candidate_id = cur.fetchone()[0]
                self.conn.commit()
                logger.info(f"Inserted candidate {candidate_id} for chunk {chunk_id}")
                return candidate_id

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to insert candidate: {e}")
            raise

    def update_resolver_result(
        self,
        candidate_id: int,
        result: ResolverResult,
        resolver_version: Optional[str] = None
    ) -> bool:
        """
        Update candidate with resolver result.

        Args:
            candidate_id: Candidate ID
            result: ResolverResult from resolver
            resolver_version: Code version that resolved (for audit)

        Returns:
            True if updated, False if candidate not found
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE chunk_entity_candidate
                    SET
                        resolver_status = %s,
                        resolver_reason = %s,
                        resolved_coverage_code = %s,
                        resolved_entity_type = %s,
                        resolver_method = %s,
                        resolver_confidence = %s,
                        resolver_version = %s,
                        resolved_at = CASE WHEN %s = 'resolved' THEN NOW() ELSE NULL END,
                        updated_at = NOW()
                    WHERE candidate_id = %s
                """, (
                    result.status,
                    result.reason,
                    result.resolved_coverage_code,
                    result.resolved_entity_type,
                    result.resolver_method,
                    result.resolver_confidence,
                    resolver_version,
                    result.status,  # For CASE WHEN
                    candidate_id
                ))

                updated = cur.rowcount > 0
                self.conn.commit()

                if updated:
                    logger.info(f"Updated candidate {candidate_id} with resolver status: {result.status}")
                else:
                    logger.warning(f"Candidate {candidate_id} not found for resolver update")

                return updated

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to update resolver result: {e}")
            raise

    def get_pending_candidates(
        self,
        limit: int = 100,
        chunk_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch candidates with resolver_status='pending'.

        Args:
            limit: Max candidates to fetch
            chunk_ids: Optional filter by chunk IDs

        Returns:
            List of candidate dicts
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                    SELECT
                        candidate_id,
                        chunk_id,
                        coverage_name_raw,
                        entity_type_proposed,
                        confidence,
                        llm_model,
                        content_hash,
                        created_at
                    FROM chunk_entity_candidate
                    WHERE resolver_status = 'pending'
                """

                params = []
                if chunk_ids:
                    query += " AND chunk_id = ANY(%s)"
                    params.append(chunk_ids)

                query += " ORDER BY created_at ASC LIMIT %s"
                params.append(limit)

                cur.execute(query, params)

                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

        except Exception as e:
            logger.error(f"Failed to fetch pending candidates: {e}")
            raise

    def get_candidate_by_id(self, candidate_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch single candidate by ID.

        Args:
            candidate_id: Candidate ID

        Returns:
            Candidate dict or None if not found
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT *
                    FROM chunk_entity_candidate
                    WHERE candidate_id = %s
                """, (candidate_id,))

                row = cur.fetchone()
                if row:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, row))
                return None

        except Exception as e:
            logger.error(f"Failed to fetch candidate {candidate_id}: {e}")
            raise

    def get_metrics(self, start_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get candidate generation and resolution metrics.

        Args:
            start_date: Optional filter by created_at >= start_date

        Returns:
            Dict with metrics (total_candidates, resolved_count, etc.)
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                    SELECT
                        COUNT(*) AS total_candidates,
                        COUNT(CASE WHEN resolver_status = 'resolved' THEN 1 END) AS resolved_count,
                        COUNT(CASE WHEN resolver_status = 'rejected' THEN 1 END) AS rejected_count,
                        COUNT(CASE WHEN resolver_status = 'needs_review' THEN 1 END) AS needs_review_count,
                        COUNT(CASE WHEN resolver_status = 'pending' THEN 1 END) AS pending_count,
                        COALESCE(SUM(llm_tokens_used), 0) AS total_tokens,
                        AVG(confidence) AS avg_confidence,
                        COUNT(DISTINCT chunk_id) AS unique_chunks,
                        COUNT(DISTINCT resolved_coverage_code) AS unique_coverages
                    FROM chunk_entity_candidate
                """

                params = []
                if start_date:
                    query += " WHERE created_at >= %s"
                    params.append(start_date)

                cur.execute(query, params)

                row = cur.fetchone()
                columns = [desc[0] for desc in cur.description]
                metrics = dict(zip(columns, row))

                # Calculate derived metrics
                total = metrics['total_candidates'] or 0
                resolved = metrics['resolved_count'] or 0
                metrics['resolution_rate'] = (resolved / total) if total > 0 else 0.0

                # Estimate cost (based on design doc: ~$0.00725 per chunk with gpt-4-turbo)
                # Adjust for gpt-4.1-mini: ~$0.0015 per chunk (estimated)
                tokens = metrics['total_tokens'] or 0
                # Assuming: 425 input tokens + 100 output tokens per call
                # gpt-4.1-mini: $0.00015/1K input, $0.0006/1K output
                input_cost = (tokens * 0.8 / 1000) * 0.00015  # 80% input
                output_cost = (tokens * 0.2 / 1000) * 0.0006  # 20% output
                metrics['estimated_cost_usd'] = input_cost + output_cost

                return metrics

        except Exception as e:
            logger.error(f"Failed to fetch metrics: {e}")
            raise

    def delete_candidate(self, candidate_id: int) -> bool:
        """
        Delete candidate (for testing/cleanup only).

        Constitutional Note:
        - Production code should NOT delete candidates (audit trail)
        - This method is for testing/admin cleanup only
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM chunk_entity_candidate
                    WHERE candidate_id = %s
                """, (candidate_id,))

                deleted = cur.rowcount > 0
                self.conn.commit()
                return deleted

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to delete candidate {candidate_id}: {e}")
            raise
