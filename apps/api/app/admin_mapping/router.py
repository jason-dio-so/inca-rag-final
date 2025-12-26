"""
Admin Mapping Workbench - FastAPI Router
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from uuid import UUID

from .models import (
    CreateMappingEventRequest,
    ApproveEventRequest,
    RejectEventRequest,
    SnoozeEventRequest,
    MappingQueueResponse,
    MappingEventDetail,
    ApprovalResult,
    EventState,
)
from .service import AdminMappingService, ValidationError
from ..db import get_db_pool
import asyncpg


router = APIRouter(prefix="/admin/mapping", tags=["admin-mapping"])


def get_admin_service(db_pool: asyncpg.Pool = Depends(get_db_pool)) -> AdminMappingService:
    """Dependency injection for AdminMappingService"""
    return AdminMappingService(db_pool)


def get_admin_actor(x_admin_actor: Optional[str] = Header(None)) -> str:
    """
    Extract admin actor from header.
    Constitutional: Simple authentication for now (can be upgraded to full auth later).
    """
    if not x_admin_actor:
        # Default to 'system' if no header (for testing/development)
        return "system"
    return x_admin_actor


# ============================================================================
# Event Queue Endpoints
# ============================================================================

@router.get("/events", response_model=MappingQueueResponse)
async def get_mapping_queue(
    state: Optional[EventState] = None,
    insurer: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    service: AdminMappingService = Depends(get_admin_service),
):
    """
    Get mapping event queue with pagination.

    Query Parameters:
    - state: Filter by event state (OPEN, APPROVED, REJECTED, SNOOZED)
    - insurer: Filter by insurer
    - page: Page number (1-indexed)
    - page_size: Items per page
    """
    events, total = await service.get_queue(
        state=state, insurer=insurer, page=page, page_size=page_size
    )

    return MappingQueueResponse(
        events=events, total=total, page=page, page_size=page_size
    )


@router.get("/events/{event_id}", response_model=MappingEventDetail)
async def get_event_detail(
    event_id: UUID,
    service: AdminMappingService = Depends(get_admin_service),
):
    """
    Get full event details including candidates and evidence.
    """
    event = await service.get_event_detail(event_id)

    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    return event


# ============================================================================
# Resolution Actions
# ============================================================================

@router.post("/approve", response_model=ApprovalResult)
async def approve_event(
    request: ApproveEventRequest,
    service: AdminMappingService = Depends(get_admin_service),
):
    """
    Approve mapping event and persist to coverage_code_alias or coverage_name_map.

    Constitutional Requirements:
    - coverage_code must be valid 신정원 통일코드
    - No conflicts allowed (safe defaults)
    - All actions audited

    Raises:
    - 400: Validation error (invalid code, conflict, etc.)
    - 404: Event not found or not in OPEN state
    """
    try:
        result = await service.approve_event(request)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reject")
async def reject_event(
    request: RejectEventRequest,
    service: AdminMappingService = Depends(get_admin_service),
):
    """
    Reject mapping event with optional note.
    """
    try:
        audit_log_id = await service.reject_event(request)
        return {
            "success": True,
            "event_id": request.event_id,
            "audit_log_id": audit_log_id,
            "message": "Event rejected",
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/snooze")
async def snooze_event(
    request: SnoozeEventRequest,
    service: AdminMappingService = Depends(get_admin_service),
):
    """
    Snooze mapping event with optional note.
    """
    try:
        audit_log_id = await service.snooze_event(request)
        return {
            "success": True,
            "event_id": request.event_id,
            "audit_log_id": audit_log_id,
            "message": "Event snoozed",
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Internal Event Creation (called from compare/clarify flow)
# ============================================================================

@router.post("/events", status_code=201)
async def create_mapping_event(
    request: CreateMappingEventRequest,
    service: AdminMappingService = Depends(get_admin_service),
):
    """
    Create or update mapping event (internal use from compare/clarify flow).

    Constitutional: Deduplication - only one OPEN event per (insurer, raw_coverage_title, detected_status).
    """
    event_id = await service.create_or_update_event(request)
    return {"event_id": event_id, "message": "Event created or updated"}
