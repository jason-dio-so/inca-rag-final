"""
Admin Mapping Integration
Helper functions to populate mapping_event_queue from compare/clarify flows
"""

import asyncpg
from typing import Optional, List
from .service import AdminMappingService
from .models import CreateMappingEventRequest, DetectedStatus


async def maybe_create_unmapped_event(
    db_pool: asyncpg.Pool,
    insurer: str,
    query_text: str,
    raw_coverage_title: str,
    mapping_status: str,
    normalized_query: Optional[str] = None,
    candidate_coverage_codes: Optional[List[str]] = None,
    evidence_ref_ids: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Create UNMAPPED/AMBIGUOUS event if applicable.

    Constitutional: Only create events for UNMAPPED or AMBIGUOUS status.
    This function is called from compare endpoints when such status is detected.

    Returns:
        event_id (str) if event created/updated, None otherwise
    """
    # Only create events for UNMAPPED or AMBIGUOUS
    if mapping_status not in ["UNMAPPED", "AMBIGUOUS"]:
        return None

    detected_status = (
        DetectedStatus.UNMAPPED if mapping_status == "UNMAPPED"
        else DetectedStatus.AMBIGUOUS
    )

    service = AdminMappingService(db_pool)

    request = CreateMappingEventRequest(
        insurer=insurer,
        query_text=query_text,
        normalized_query=normalized_query,
        raw_coverage_title=raw_coverage_title,
        detected_status=detected_status,
        candidate_coverage_codes=candidate_coverage_codes,
        evidence_ref_ids=evidence_ref_ids,
    )

    event_id = await service.create_or_update_event(request)
    return str(event_id)


async def maybe_create_unmapped_event_from_compare(
    db_pool: asyncpg.Pool,
    insurer: str,
    query: str,
    coverage_data: dict,
) -> Optional[str]:
    """
    Convenience wrapper for compare endpoint integration.

    Args:
        db_pool: Database connection pool
        insurer: Insurance company code
        query: User query text
        coverage_data: Coverage data from proposal_coverage_mapped (dict with keys: mapping_status, coverage_name_raw, etc.)

    Returns:
        event_id if created, None otherwise
    """
    mapping_status = coverage_data.get("mapping_status")
    if mapping_status not in ["UNMAPPED", "AMBIGUOUS"]:
        return None

    # Extract candidate codes if AMBIGUOUS
    candidate_codes = None
    if mapping_status == "AMBIGUOUS":
        # AMBIGUOUS means multiple candidate codes exist
        # In current implementation, we don't have candidate codes in coverage_data
        # This would be populated from Excel mapping lookup in future enhancement
        candidate_codes = []

    return await maybe_create_unmapped_event(
        db_pool=db_pool,
        insurer=insurer,
        query_text=query,
        raw_coverage_title=coverage_data.get("coverage_name_raw", ""),
        mapping_status=mapping_status,
        normalized_query=None,  # Can be populated from query normalization if available
        candidate_coverage_codes=candidate_codes,
        evidence_ref_ids=None,  # Can be populated from evidence blocks if available
    )
