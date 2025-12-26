"""
/compare/view-model endpoint - ViewModel Assembler

Converts ProposalCompareResponse to UI-ready ViewModel JSON.

Constitutional Principles:
- Fact-only (no inference)
- No recommendations/judgments
- Presentation layer only
- Schema-validated output
"""

import os
from fastapi import APIRouter, HTTPException, Depends
from psycopg2.extensions import connection as PGConnection
from typing import Dict, Any, Optional

from ..schemas.compare import ProposalCompareRequest, ProposalCoverageItem
from ..db import get_readonly_conn
from ..view_model.assembler import assemble_view_model
from ..view_model.schema_loader import load_schema, validate_view_model
from .compare import compare_proposals as base_compare_proposals


def fetch_comparison_description(
    conn: PGConnection,
    template_id: str,
    insurer_coverage_name: str
) -> tuple[Optional[str], Optional[dict]]:
    """
    Fetch comparison description from v2.proposal_coverage_detail (STEP NEXT-AF-FIX).

    IMPORTANT: Template isolation - only match within same template_id.

    Args:
        conn: DB connection
        template_id: Template ID (for isolation)
        insurer_coverage_name: Coverage name from row

    Returns:
        (detail_text, source_metadata) or (None, None) if not found
    """
    cursor = conn.cursor()

    # Match by template_id + insurer_coverage_name (template isolation)
    # Prefer matched (coverage_id NOT NULL), fallback to unmatched
    cursor.execute("""
        SELECT d.detail_text, d.source_page
        FROM v2.proposal_coverage_detail d
        WHERE d.template_id = %s
          AND d.insurer_coverage_name = %s
          AND d.extraction_method LIKE 'deterministic%%'
        ORDER BY (d.coverage_id IS NOT NULL) DESC, d.updated_at DESC
        LIMIT 1
    """, (template_id, insurer_coverage_name))

    row = cursor.fetchone()
    cursor.close()

    if row:
        detail_text, source_page = row
        source_meta = {"doc_type": "proposal_detail", "page": source_page}
        return detail_text, source_meta

    return None, None


router = APIRouter(tags=["ViewModel"])


# Runtime schema validation flag (env-controlled, default ON)
ENABLE_SCHEMA_VALIDATION = os.getenv("ENABLE_VIEW_MODEL_VALIDATION", "1") == "1"


@router.post("/compare/view-model")
async def compare_view_model(
    request: ProposalCompareRequest,
    conn: PGConnection = Depends(get_readonly_conn)
) -> Dict[str, Any]:
    """
    Compare proposals and return ViewModel JSON.

    This endpoint:
    1. Calls existing /compare logic (reuses compare_proposals)
    2. Assembles ViewModel from ProposalCompareResponse
    3. Validates against docs/ui/compare_view_model.schema.json
    4. Returns ViewModel JSON

    Constitutional Compliance:
    - No new business logic (adapter only)
    - Schema-validated output (fail-fast if invalid)
    - Deterministic assembly (same input → same output)

    Args:
        request: ProposalCompareRequest (same as /compare)
        conn: Read-only DB connection

    Returns:
        ViewModel JSON matching compare_view_model.schema.json

    Raises:
        HTTPException 500: If ViewModel assembly/validation fails
    """
    try:
        # Step 1: Get comparison result from existing /compare logic
        compare_response = await base_compare_proposals(request, conn)

        # Step 2: Assemble ViewModel
        view_model = assemble_view_model(compare_response, include_debug=True)

        # Step 3: Convert to dict
        view_model_dict = view_model.model_dump(mode="json")

        # Step 3.5: Enrich with comparison_description (STEP NEXT-AF-FIX)
        # Add comparison_description to fact_table rows (row-level matching with template_id isolation)
        if "fact_table" in view_model_dict and "rows" in view_model_dict["fact_table"]:
            # Get template_id for each coverage (need to query DB)
            template_ids = {}
            cursor = conn.cursor()

            # Get template_id for coverage_a
            if compare_response.coverage_a:
                cursor.execute("""
                    SELECT template_id FROM v2.proposal_coverage
                    WHERE insurer_coverage_name = %s LIMIT 1
                """, (compare_response.coverage_a.coverage_name_raw,))
                result = cursor.fetchone()
                if result:
                    template_ids[compare_response.coverage_a.insurer.upper()] = result[0]

            # Get template_id for coverage_b
            if compare_response.coverage_b:
                cursor.execute("""
                    SELECT template_id FROM v2.proposal_coverage
                    WHERE insurer_coverage_name = %s LIMIT 1
                """, (compare_response.coverage_b.coverage_name_raw,))
                result = cursor.fetchone()
                if result:
                    template_ids[compare_response.coverage_b.insurer.upper()] = result[0]

            cursor.close()

            # Enrich each row with comparison_description
            for row in view_model_dict["fact_table"]["rows"]:
                insurer = row.get("insurer")
                coverage_title = row.get("coverage_title_normalized")

                # Get template_id for this row's insurer
                template_id = template_ids.get(insurer)
                if not template_id:
                    continue

                # Fetch description using template_id + coverage_title (row-level matching)
                detail_text, source_meta = fetch_comparison_description(
                    conn,
                    template_id,
                    coverage_title  # This is the row's coverage name
                )

                if detail_text:
                    row["comparison_description"] = detail_text
                    row["comparison_description_source"] = source_meta

        # Step 4: Runtime schema validation (if enabled)
        if ENABLE_SCHEMA_VALIDATION:
            try:
                schema = load_schema()
                validate_view_model(view_model_dict, schema)
            except Exception as validation_error:
                # Schema validation failed → DATA_INSUFFICIENT
                raise HTTPException(
                    status_code=424,  # Failed Dependency
                    detail={
                        "error_code": "DATA_INSUFFICIENT",
                        "message": "ViewModel 생성에 필요한 근거/매핑 데이터가 부족합니다.",
                        "hints": [
                            "비교 가능한 데이터가 없거나 매핑되지 않았습니다.",
                            "docs/testing/TEST_DATA_SETUP.md를 확인하세요.",
                            f"Schema error: {str(validation_error)[:200]}"
                        ]
                    }
                )

        return view_model_dict

    except HTTPException:
        # Re-raise HTTP exceptions from base_compare_proposals
        raise
    except Exception as e:
        import psycopg2
        import logging
        import jsonschema

        logger = logging.getLogger(__name__)
        logger.error(f"ViewModel assembly error: {e}", exc_info=True)

        # Classify error type
        error_detail = str(e)
        error_code = "INTERNAL_ERROR"
        status_code = 500
        hints = []

        # 1. DB Connection Errors
        if isinstance(e, psycopg2.OperationalError):
            error_code = "DB_CONN_FAILED"
            status_code = 500
            if "password authentication failed" in error_detail:
                hints.append("DB_PASSWORD mismatch")
                hints.append("Run: python apps/api/scripts/db_doctor.py")
            elif "could not connect" in error_detail:
                hints.append("DB connection refused (check container)")
                hints.append("Run: docker ps | grep inca_pg")
            elif "does not exist" in error_detail:
                hints.append("Database name mismatch")
                hints.append("Expected: DB_NAME=inca_rag_final")

        # 2. Schema Validation Errors (Data Insufficient)
        elif isinstance(e, (jsonschema.ValidationError, ValueError)):
            error_code = "DATA_INSUFFICIENT"
            status_code = 424  # Failed Dependency
            error_detail = "ViewModel 생성에 필요한 근거/매핑 데이터가 부족합니다."
            hints.append("docs/testing/TEST_DATA_SETUP.md를 따라 최소 데이터셋을 준비하세요.")
            hints.append(f"Original error: {str(e)[:200]}")

        # 3. ViewModel Assembly Errors (likely data issue)
        elif "should be non-empty" in error_detail or "minItems" in error_detail:
            error_code = "DATA_INSUFFICIENT"
            status_code = 424
            error_detail = "ViewModel 생성에 필요한 근거/매핑 데이터가 부족합니다."
            hints.append("비교 가능한 데이터가 없거나 매핑되지 않았습니다.")
            hints.append("docs/testing/TEST_DATA_SETUP.md를 확인하세요.")

        # Build structured error response
        error_response = {
            "error_code": error_code,
            "message": error_detail,
        }
        if hints:
            error_response["hints"] = hints

        raise HTTPException(
            status_code=status_code,
            detail=error_response
        )
