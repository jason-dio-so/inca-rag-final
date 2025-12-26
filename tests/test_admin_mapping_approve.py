"""
Test: Admin Mapping Approval Flow
Constitutional: Canonical Coverage Rule enforcement

NOTE: These tests require a running PostgreSQL database with the admin_mapping tables.
Run migration first: migrations/step_next7_admin_mapping_workbench.sql
"""

import pytest
import pytest_asyncio
import asyncpg
import os
from apps.api.app.admin_mapping.service import AdminMappingService, ValidationError
from apps.api.app.admin_mapping.models import (
    CreateMappingEventRequest,
    ApproveEventRequest,
    RejectEventRequest,
    SnoozeEventRequest,
    DetectedStatus,
    ResolutionType,
    EventState,
)


# Test configuration
TEST_DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5433")),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "testpass"),
    "database": os.getenv("POSTGRES_DB", "inca_rag_final_test"),
}


@pytest_asyncio.fixture
async def db_pool():
    """Create test database pool"""
    pool = await asyncpg.create_pool(**TEST_DB_CONFIG)
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def admin_service(db_pool):
    """Create admin service instance"""
    return AdminMappingService(db_pool)


@pytest_asyncio.fixture
async def clean_tables(db_pool):
    """Clean test tables before each test"""
    async with db_pool.acquire() as conn:
        # Clean in reverse dependency order
        await conn.execute("DELETE FROM admin_audit_log WHERE target_type = 'EVENT'")
        await conn.execute("DELETE FROM mapping_event_queue WHERE insurer IN ('SAMSUNG', 'MERITZ', 'TEST_INSURER')")
        await conn.execute("DELETE FROM coverage_code_alias WHERE insurer IN ('SAMSUNG', 'MERITZ', 'TEST_INSURER')")
        await conn.execute("DELETE FROM coverage_name_map WHERE insurer IN ('SAMSUNG', 'MERITZ', 'TEST_INSURER')")


@pytest_asyncio.fixture
async def sample_event(admin_service: AdminMappingService, clean_tables):
    """Create sample UNMAPPED event for testing"""
    request = CreateMappingEventRequest(
        insurer="SAMSUNG",
        query_text="일반암진단비",
        normalized_query="일반암진단비",
        raw_coverage_title="일반암 진단비",
        detected_status=DetectedStatus.UNMAPPED,
        candidate_coverage_codes=["CA_DIAG_GENERAL"],
        evidence_ref_ids=None,
    )
    event_id = await admin_service.create_or_update_event(request)
    return event_id


@pytest_asyncio.fixture
async def ensure_canonical_code(db_pool):
    """Ensure canonical code exists in coverage_standard"""
    async with db_pool.acquire() as conn:
        # Insert test canonical code if not exists
        await conn.execute(
            """
            INSERT INTO coverage_standard (coverage_code, coverage_name)
            VALUES ($1, $2)
            ON CONFLICT (coverage_code) DO NOTHING
            """,
            "CA_DIAG_GENERAL",
            "일반암진단비",
        )


@pytest.mark.asyncio
async def test_create_event(admin_service: AdminMappingService, clean_tables):
    """
    Test: Create UNMAPPED event
    """
    request = CreateMappingEventRequest(
        insurer="TEST_INSURER",
        query_text="test query",
        raw_coverage_title="test coverage",
        detected_status=DetectedStatus.UNMAPPED,
    )

    event_id = await admin_service.create_or_update_event(request)
    assert event_id is not None

    # Verify event exists
    event = await admin_service.get_event_detail(event_id)
    assert event is not None
    assert event.insurer == "TEST_INSURER"
    assert event.state == EventState.OPEN


@pytest.mark.asyncio
async def test_approve_event_success(
    admin_service: AdminMappingService,
    sample_event,
    ensure_canonical_code,
):
    """
    Test: Successful approval creates NAME_MAP and updates event state
    Constitutional: Canonical Coverage Rule - code must exist
    """
    # Approve event
    request = ApproveEventRequest(
        event_id=sample_event,
        coverage_code="CA_DIAG_GENERAL",
        resolution_type=ResolutionType.NAME_MAP,
        note="Test approval",
        actor="test_admin",
    )

    result = await admin_service.approve_event(request)

    # Assertions
    assert result.success is True
    assert result.resolved_coverage_code == "CA_DIAG_GENERAL"
    assert result.resolution_type == ResolutionType.NAME_MAP
    assert result.audit_log_id is not None

    # Verify event state updated
    event = await admin_service.get_event_detail(sample_event)
    assert event is not None
    assert event.state == EventState.APPROVED
    assert event.resolved_coverage_code == "CA_DIAG_GENERAL"
    assert event.resolved_by == "test_admin"


@pytest.mark.asyncio
async def test_approve_event_invalid_code(
    admin_service: AdminMappingService,
    sample_event,
):
    """
    Test: Approval fails if coverage_code does not exist in canonical source
    Constitutional: Canonical Coverage Rule violation
    """
    request = ApproveEventRequest(
        event_id=sample_event,
        coverage_code="INVALID_CODE_12345",
        resolution_type=ResolutionType.NAME_MAP,
        note="Test invalid code",
        actor="test_admin",
    )

    with pytest.raises(ValidationError) as exc_info:
        await admin_service.approve_event(request)

    assert "does not exist in canonical source" in str(exc_info.value)
    assert "Constitutional violation" in str(exc_info.value)


@pytest.mark.asyncio
async def test_reject_event(
    admin_service: AdminMappingService,
    sample_event,
):
    """
    Test: Reject event updates state and creates audit log
    """
    request = RejectEventRequest(
        event_id=sample_event,
        note="Test rejection",
        actor="test_admin",
    )

    audit_id = await admin_service.reject_event(request)
    assert audit_id is not None

    # Verify state
    event = await admin_service.get_event_detail(sample_event)
    assert event.state == EventState.REJECTED
    assert event.resolution_note == "Test rejection"


@pytest.mark.asyncio
async def test_snooze_event(
    admin_service: AdminMappingService,
    sample_event,
):
    """
    Test: Snooze event updates state and creates audit log
    """
    request = SnoozeEventRequest(
        event_id=sample_event,
        note="Test snooze",
        actor="test_admin",
    )

    audit_id = await admin_service.snooze_event(request)
    assert audit_id is not None

    # Verify state
    event = await admin_service.get_event_detail(sample_event)
    assert event.state == EventState.SNOOZED
    assert event.resolution_note == "Test snooze"


@pytest.mark.asyncio
async def test_deduplication(admin_service: AdminMappingService, clean_tables):
    """
    Test: Only one OPEN event per (insurer, raw_coverage_title, detected_status)
    Constitutional: Deduplication requirement
    """
    request = CreateMappingEventRequest(
        insurer="MERITZ",
        query_text="유사암진단금",
        raw_coverage_title="유사암 진단금",
        detected_status=DetectedStatus.UNMAPPED,
    )

    # Create first event
    event_id_1 = await admin_service.create_or_update_event(request)

    # Create duplicate event (should update, not create)
    event_id_2 = await admin_service.create_or_update_event(request)

    assert event_id_1 == event_id_2

    # Verify only one OPEN event exists
    events, total = await admin_service.get_queue(state=EventState.OPEN)
    meritz_events = [e for e in events if e.insurer == "MERITZ" and e.raw_coverage_title == "유사암 진단금"]
    assert len(meritz_events) == 1
