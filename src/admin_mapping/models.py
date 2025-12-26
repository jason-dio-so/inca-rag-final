"""
Admin Mapping Workbench - Data Models
Constitutional: Canonical Coverage Rule - all coverage_code references must be 신정원 통일코드
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class DetectedStatus(str, Enum):
    """Detection status for mapping events"""
    UNMAPPED = "UNMAPPED"
    AMBIGUOUS = "AMBIGUOUS"


class EventState(str, Enum):
    """Resolution state for mapping events"""
    OPEN = "OPEN"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SNOOZED = "SNOOZED"


class ResolutionType(str, Enum):
    """Type of resolution action"""
    ALIAS = "ALIAS"
    NAME_MAP = "NAME_MAP"
    MANUAL_NOTE = "MANUAL_NOTE"


class AuditAction(str, Enum):
    """Admin audit action types"""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    SNOOZE = "SNOOZE"
    UPSERT_ALIAS = "UPSERT_ALIAS"
    UPSERT_NAME_MAP = "UPSERT_NAME_MAP"


class TargetType(str, Enum):
    """Audit target types"""
    EVENT = "EVENT"
    ALIAS = "ALIAS"
    NAME_MAP = "NAME_MAP"


# ============================================================================
# Request Models
# ============================================================================

class CreateMappingEventRequest(BaseModel):
    """Request to create a new mapping event"""
    insurer: str
    query_text: str
    normalized_query: Optional[str] = None
    raw_coverage_title: str
    detected_status: DetectedStatus
    candidate_coverage_codes: Optional[List[str]] = None
    evidence_ref_ids: Optional[List[str]] = None


class ApproveEventRequest(BaseModel):
    """Request to approve a mapping event
    Constitutional: coverage_code must be 신정원 통일코드 (canonical)
    """
    event_id: UUID
    coverage_code: str = Field(..., description="신정원 통일코드 (canonical coverage code)")
    resolution_type: ResolutionType
    note: Optional[str] = None
    actor: str = Field(..., description="Admin username or X-Admin-Actor header value")


class RejectEventRequest(BaseModel):
    """Request to reject a mapping event"""
    event_id: UUID
    note: Optional[str] = None
    actor: str


class SnoozeEventRequest(BaseModel):
    """Request to snooze a mapping event"""
    event_id: UUID
    note: Optional[str] = None
    actor: str


# ============================================================================
# Response Models
# ============================================================================

class MappingEventSummary(BaseModel):
    """Summary of a mapping event for queue view"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    insurer: str
    raw_coverage_title: str
    detected_status: DetectedStatus
    state: EventState
    candidate_count: int = 0


class MappingEventDetail(BaseModel):
    """Full details of a mapping event"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    insurer: str
    query_text: str
    normalized_query: Optional[str]
    raw_coverage_title: str
    detected_status: DetectedStatus
    candidate_coverage_codes: Optional[List[str]]
    evidence_ref_ids: Optional[List[str]]
    state: EventState
    resolved_coverage_code: Optional[str]
    resolution_type: Optional[ResolutionType]
    resolution_note: Optional[str]
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]


class AuditLogEntry(BaseModel):
    """Audit log entry"""
    id: UUID
    created_at: datetime
    actor: str
    action: AuditAction
    target_type: TargetType
    target_id: str
    before: Optional[dict]
    after: Optional[dict]
    evidence_ref_ids: Optional[List[str]]
    note: Optional[str]


class ApprovalResult(BaseModel):
    """Result of approval operation"""
    success: bool
    event_id: UUID
    resolved_coverage_code: str
    resolution_type: ResolutionType
    audit_log_id: UUID
    message: str


class MappingQueueResponse(BaseModel):
    """Response for mapping queue listing"""
    events: List[MappingEventSummary]
    total: int
    page: int
    page_size: int
