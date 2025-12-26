"""
Admin Mapping Workbench - Service Layer
Constitutional: Canonical Coverage Rule + Deterministic & Auditable
"""

import asyncpg
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID
import json

from .models import (
    CreateMappingEventRequest,
    ApproveEventRequest,
    RejectEventRequest,
    SnoozeEventRequest,
    MappingEventSummary,
    MappingEventDetail,
    AuditLogEntry,
    ApprovalResult,
    EventState,
    DetectedStatus,
    AuditAction,
    TargetType,
)


class ValidationError(Exception):
    """Validation error during approval process"""
    pass


class AdminMappingService:
    """
    Service for admin mapping workbench operations.

    Constitutional Requirements:
    1. Canonical Coverage Rule: All coverage_code must reference 신정원 통일코드
    2. Deterministic: No auto-approval, all actions explicit
    3. Auditable: All actions logged with before/after state
    4. Safe defaults: Conflict/ambiguity → reject (no auto-overwrite)
    """

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    # ========================================================================
    # Event Queue Management
    # ========================================================================

    async def create_or_update_event(
        self, request: CreateMappingEventRequest
    ) -> UUID:
        """
        Create new mapping event or update existing OPEN event.
        Constitutional: Deduplication - only one OPEN event per (insurer, raw_coverage_title, detected_status)
        """
        async with self.db_pool.acquire() as conn:
            # Check for existing OPEN event
            existing = await conn.fetchrow(
                """
                SELECT id FROM mapping_event_queue
                WHERE insurer = $1
                  AND raw_coverage_title = $2
                  AND detected_status = $3
                  AND state = 'OPEN'
                """,
                request.insurer,
                request.raw_coverage_title,
                request.detected_status.value,
            )

            candidate_codes_json = (
                json.dumps(request.candidate_coverage_codes)
                if request.candidate_coverage_codes
                else None
            )
            evidence_json = (
                json.dumps(request.evidence_ref_ids)
                if request.evidence_ref_ids
                else None
            )

            if existing:
                # Update existing event
                await conn.execute(
                    """
                    UPDATE mapping_event_queue
                    SET query_text = $1,
                        normalized_query = $2,
                        candidate_coverage_codes = $3,
                        evidence_ref_ids = $4,
                        updated_at = NOW()
                    WHERE id = $5
                    """,
                    request.query_text,
                    request.normalized_query,
                    candidate_codes_json,
                    evidence_json,
                    existing["id"],
                )
                return existing["id"]
            else:
                # Create new event
                row = await conn.fetchrow(
                    """
                    INSERT INTO mapping_event_queue (
                        insurer, query_text, normalized_query, raw_coverage_title,
                        detected_status, candidate_coverage_codes, evidence_ref_ids
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                    """,
                    request.insurer,
                    request.query_text,
                    request.normalized_query,
                    request.raw_coverage_title,
                    request.detected_status.value,
                    candidate_codes_json,
                    evidence_json,
                )
                return row["id"]

    async def get_queue(
        self,
        state: Optional[EventState] = None,
        insurer: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[MappingEventSummary], int]:
        """Get mapping event queue with pagination"""
        offset = (page - 1) * page_size

        async with self.db_pool.acquire() as conn:
            # Build query
            where_clauses = []
            params = []
            param_idx = 1

            if state:
                where_clauses.append(f"state = ${param_idx}")
                params.append(state.value)
                param_idx += 1

            if insurer:
                where_clauses.append(f"insurer = ${param_idx}")
                params.append(insurer)
                param_idx += 1

            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # Get total count
            count_row = await conn.fetchrow(
                f"SELECT COUNT(*) as total FROM mapping_event_queue {where_sql}",
                *params,
            )
            total = count_row["total"]

            # Get events
            rows = await conn.fetch(
                f"""
                SELECT
                    id, created_at, updated_at, insurer, raw_coverage_title,
                    detected_status, state,
                    COALESCE(jsonb_array_length(candidate_coverage_codes), 0) as candidate_count
                FROM mapping_event_queue
                {where_sql}
                ORDER BY created_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
                """,
                *params,
                page_size,
                offset,
            )

            events = [
                MappingEventSummary(
                    id=row["id"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    insurer=row["insurer"],
                    raw_coverage_title=row["raw_coverage_title"],
                    detected_status=DetectedStatus(row["detected_status"]),
                    state=EventState(row["state"]),
                    candidate_count=row["candidate_count"],
                )
                for row in rows
            ]

            return events, total

    async def get_event_detail(self, event_id: UUID) -> Optional[MappingEventDetail]:
        """Get full event details"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    id, created_at, updated_at, insurer, query_text, normalized_query,
                    raw_coverage_title, detected_status, candidate_coverage_codes,
                    evidence_ref_ids, state, resolved_coverage_code, resolution_type,
                    resolution_note, resolved_at, resolved_by
                FROM mapping_event_queue
                WHERE id = $1
                """,
                event_id,
            )

            if not row:
                return None

            return MappingEventDetail(
                id=row["id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                insurer=row["insurer"],
                query_text=row["query_text"],
                normalized_query=row["normalized_query"],
                raw_coverage_title=row["raw_coverage_title"],
                detected_status=DetectedStatus(row["detected_status"]),
                candidate_coverage_codes=(
                    json.loads(row["candidate_coverage_codes"])
                    if row["candidate_coverage_codes"]
                    else None
                ),
                evidence_ref_ids=(
                    json.loads(row["evidence_ref_ids"])
                    if row["evidence_ref_ids"]
                    else None
                ),
                state=EventState(row["state"]),
                resolved_coverage_code=row["resolved_coverage_code"],
                resolution_type=row["resolution_type"],
                resolution_note=row["resolution_note"],
                resolved_at=row["resolved_at"],
                resolved_by=row["resolved_by"],
            )

    # ========================================================================
    # Validation (Constitutional: Canonical Coverage Rule)
    # ========================================================================

    async def _validate_canonical_coverage_code(
        self, conn: asyncpg.Connection, coverage_code: str
    ) -> None:
        """
        Validate that coverage_code exists in canonical source (신정원 통일코드).
        Constitutional: Canonical Coverage Rule enforcement.

        Raises ValidationError if code does not exist.
        """
        # Check in coverage_standard table (신정원 canonical source)
        exists = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM coverage_standard
                WHERE coverage_code = $1
            )
            """,
            coverage_code,
        )

        if not exists:
            raise ValidationError(
                f"Coverage code '{coverage_code}' does not exist in canonical source (신정원 통일코드). "
                f"Constitutional violation: Canonical Coverage Rule."
            )

    async def _check_alias_conflict(
        self, conn: asyncpg.Connection, insurer: str, alias_text: str, coverage_code: str
    ) -> Optional[str]:
        """
        Check if alias already exists with different coverage_code.
        Constitutional: Safe defaults - reject conflicts.

        Returns conflicting coverage_code if exists, None otherwise.
        """
        existing = await conn.fetchrow(
            """
            SELECT coverage_code FROM coverage_code_alias
            WHERE insurer = $1 AND alias_text = $2
            """,
            insurer,
            alias_text,
        )

        if existing and existing["coverage_code"] != coverage_code:
            return existing["coverage_code"]

        return None

    async def _check_name_map_conflict(
        self, conn: asyncpg.Connection, insurer: str, raw_name: str, coverage_code: str
    ) -> Optional[str]:
        """
        Check if raw_name already exists with different coverage_code.
        Constitutional: Safe defaults - reject conflicts.

        Returns conflicting coverage_code if exists, None otherwise.
        """
        existing = await conn.fetchrow(
            """
            SELECT coverage_code FROM coverage_name_map
            WHERE insurer = $1 AND raw_name = $2
            """,
            insurer,
            raw_name,
        )

        if existing and existing["coverage_code"] != coverage_code:
            return existing["coverage_code"]

        return None

    # ========================================================================
    # Approval Transaction (Constitutional: Deterministic & Auditable)
    # ========================================================================

    async def approve_event(self, request: ApproveEventRequest) -> ApprovalResult:
        """
        Approve mapping event and persist to alias/name_map tables.

        Constitutional Requirements:
        1. Canonical Coverage Rule: Validate coverage_code against 신정원
        2. Safe defaults: Reject on conflict (no auto-overwrite)
        3. Auditable: Log before/after state
        4. Transactional: All-or-nothing

        Raises ValidationError on validation failure.
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # 1. Load event (must be OPEN)
                event = await conn.fetchrow(
                    """
                    SELECT * FROM mapping_event_queue
                    WHERE id = $1 AND state = 'OPEN'
                    FOR UPDATE
                    """,
                    request.event_id,
                )

                if not event:
                    raise ValidationError(
                        f"Event {request.event_id} not found or not in OPEN state"
                    )

                # 2. Validate canonical coverage code
                await self._validate_canonical_coverage_code(conn, request.coverage_code)

                # 3. Check conflicts based on resolution type
                if request.resolution_type.value == "ALIAS":
                    # Use normalized_query as alias_text (fallback to query_text)
                    alias_text = event["normalized_query"] or event["query_text"]
                    conflict_code = await self._check_alias_conflict(
                        conn, event["insurer"], alias_text, request.coverage_code
                    )
                    if conflict_code:
                        raise ValidationError(
                            f"Alias '{alias_text}' already mapped to different code '{conflict_code}'. "
                            f"Constitutional: Safe defaults - no auto-overwrite."
                        )

                elif request.resolution_type.value == "NAME_MAP":
                    conflict_code = await self._check_name_map_conflict(
                        conn, event["insurer"], event["raw_coverage_title"], request.coverage_code
                    )
                    if conflict_code:
                        raise ValidationError(
                            f"Raw name '{event['raw_coverage_title']}' already mapped to different code '{conflict_code}'. "
                            f"Constitutional: Safe defaults - no auto-overwrite."
                        )

                # 4. Capture before state for audit
                before_state = {
                    "state": event["state"],
                    "resolved_coverage_code": event["resolved_coverage_code"],
                    "resolution_type": event["resolution_type"],
                }

                # 5. Upsert to target table
                if request.resolution_type.value == "ALIAS":
                    alias_text = event["normalized_query"] or event["query_text"]
                    await conn.execute(
                        """
                        INSERT INTO coverage_code_alias (insurer, alias_text, coverage_code, created_by)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (insurer, alias_text)
                        DO UPDATE SET coverage_code = EXCLUDED.coverage_code, created_by = EXCLUDED.created_by
                        """,
                        event["insurer"],
                        alias_text,
                        request.coverage_code,
                        request.actor,
                    )

                elif request.resolution_type.value == "NAME_MAP":
                    # For NAME_MAP, use raw_coverage_title as both raw_name and normalized
                    await conn.execute(
                        """
                        INSERT INTO coverage_name_map (
                            insurer, raw_name, coverage_title_normalized, coverage_code, created_by
                        ) VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (insurer, raw_name)
                        DO UPDATE SET
                            coverage_title_normalized = EXCLUDED.coverage_title_normalized,
                            coverage_code = EXCLUDED.coverage_code,
                            created_by = EXCLUDED.created_by
                        """,
                        event["insurer"],
                        event["raw_coverage_title"],
                        event["raw_coverage_title"],  # Use raw as normalized for now
                        request.coverage_code,
                        request.actor,
                    )

                # 6. Update event state
                await conn.execute(
                    """
                    UPDATE mapping_event_queue
                    SET state = 'APPROVED',
                        resolved_coverage_code = $1,
                        resolution_type = $2,
                        resolution_note = $3,
                        resolved_at = NOW(),
                        resolved_by = $4
                    WHERE id = $5
                    """,
                    request.coverage_code,
                    request.resolution_type.value,
                    request.note,
                    request.actor,
                    request.event_id,
                )

                # 7. Capture after state
                after_state = {
                    "state": "APPROVED",
                    "resolved_coverage_code": request.coverage_code,
                    "resolution_type": request.resolution_type.value,
                }

                # 8. Create audit log
                audit_row = await conn.fetchrow(
                    """
                    INSERT INTO admin_audit_log (
                        actor, action, target_type, target_id,
                        before, after, evidence_ref_ids, note
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                    """,
                    request.actor,
                    AuditAction.APPROVE.value,
                    TargetType.EVENT.value,
                    str(request.event_id),
                    json.dumps(before_state),
                    json.dumps(after_state),
                    event["evidence_ref_ids"],
                    request.note,
                )

                return ApprovalResult(
                    success=True,
                    event_id=request.event_id,
                    resolved_coverage_code=request.coverage_code,
                    resolution_type=request.resolution_type,
                    audit_log_id=audit_row["id"],
                    message=f"Event approved and {request.resolution_type.value} mapping created",
                )

    # ========================================================================
    # Reject / Snooze (Constitutional: Auditable)
    # ========================================================================

    async def reject_event(self, request: RejectEventRequest) -> UUID:
        """Reject mapping event with audit log"""
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Load event
                event = await conn.fetchrow(
                    """
                    SELECT state FROM mapping_event_queue
                    WHERE id = $1
                    FOR UPDATE
                    """,
                    request.event_id,
                )

                if not event:
                    raise ValidationError(f"Event {request.event_id} not found")

                before_state = {"state": event["state"]}

                # Update event
                await conn.execute(
                    """
                    UPDATE mapping_event_queue
                    SET state = 'REJECTED',
                        resolution_note = $1,
                        resolved_at = NOW(),
                        resolved_by = $2
                    WHERE id = $3
                    """,
                    request.note,
                    request.actor,
                    request.event_id,
                )

                after_state = {"state": "REJECTED"}

                # Audit log
                audit_row = await conn.fetchrow(
                    """
                    INSERT INTO admin_audit_log (
                        actor, action, target_type, target_id, before, after, note
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                    """,
                    request.actor,
                    AuditAction.REJECT.value,
                    TargetType.EVENT.value,
                    str(request.event_id),
                    json.dumps(before_state),
                    json.dumps(after_state),
                    request.note,
                )

                return audit_row["id"]

    async def snooze_event(self, request: SnoozeEventRequest) -> UUID:
        """Snooze mapping event with audit log"""
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Load event
                event = await conn.fetchrow(
                    """
                    SELECT state FROM mapping_event_queue
                    WHERE id = $1
                    FOR UPDATE
                    """,
                    request.event_id,
                )

                if not event:
                    raise ValidationError(f"Event {request.event_id} not found")

                before_state = {"state": event["state"]}

                # Update event
                await conn.execute(
                    """
                    UPDATE mapping_event_queue
                    SET state = 'SNOOZED',
                        resolution_note = $1,
                        resolved_at = NOW(),
                        resolved_by = $2
                    WHERE id = $3
                    """,
                    request.note,
                    request.actor,
                    request.event_id,
                )

                after_state = {"state": "SNOOZED"}

                # Audit log
                audit_row = await conn.fetchrow(
                    """
                    INSERT INTO admin_audit_log (
                        actor, action, target_type, target_id, before, after, note
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                    """,
                    request.actor,
                    AuditAction.SNOOZE.value,
                    TargetType.EVENT.value,
                    str(request.event_id),
                    json.dumps(before_state),
                    json.dumps(after_state),
                    request.note,
                )

                return audit_row["id"]

    # ========================================================================
    # Audit Log Query
    # ========================================================================

    async def get_audit_logs(
        self,
        target_type: Optional[TargetType] = None,
        target_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLogEntry]:
        """Get audit logs with optional filtering"""
        async with self.db_pool.acquire() as conn:
            where_clauses = []
            params = []
            param_idx = 1

            if target_type:
                where_clauses.append(f"target_type = ${param_idx}")
                params.append(target_type.value)
                param_idx += 1

            if target_id:
                where_clauses.append(f"target_id = ${param_idx}")
                params.append(target_id)
                param_idx += 1

            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            rows = await conn.fetch(
                f"""
                SELECT
                    id, created_at, actor, action, target_type, target_id,
                    before, after, evidence_ref_ids, note
                FROM admin_audit_log
                {where_sql}
                ORDER BY created_at DESC
                LIMIT ${param_idx}
                """,
                *params,
                limit,
            )

            return [
                AuditLogEntry(
                    id=row["id"],
                    created_at=row["created_at"],
                    actor=row["actor"],
                    action=AuditAction(row["action"]),
                    target_type=TargetType(row["target_type"]),
                    target_id=row["target_id"],
                    before=json.loads(row["before"]) if row["before"] else None,
                    after=json.loads(row["after"]) if row["after"] else None,
                    evidence_ref_ids=(
                        json.loads(row["evidence_ref_ids"])
                        if row["evidence_ref_ids"]
                        else None
                    ),
                    note=row["note"],
                )
                for row in rows
            ]
