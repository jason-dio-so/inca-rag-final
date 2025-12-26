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
    insurer_code: str,
    insurer_coverage_name_raw: str
) -> tuple[Optional[str], Optional[dict]]:
    """
    Fetch comparison description from v2.proposal_coverage_detail (STEP NEXT-AF-FIX-2).

    IMPORTANT: Template + Insurer isolation - prevent cross-template/cross-insurer mixing.

    Args:
        conn: DB connection
        template_id: Template ID (for isolation)
        insurer_code: Insurer code (for additional isolation)
        insurer_coverage_name_raw: Raw coverage name (DB key, not normalized)

    Returns:
        (detail_text, source_metadata) or (None, None) if not found
    """
    cursor = conn.cursor()

    # AF-FIX-2: Match by template_id + insurer_coverage_name_raw
    # Additional safety: verify template belongs to same insurer
    # Prefer matched (coverage_id NOT NULL), fallback to unmatched within same template
    cursor.execute("""
        SELECT d.detail_text, d.source_page
        FROM v2.proposal_coverage_detail d
        JOIN v2.template t ON t.template_id = d.template_id
        JOIN v2.product p ON p.product_id = t.product_id
        WHERE d.template_id = %s
          AND p.insurer_code = %s
          AND d.insurer_coverage_name = %s
          AND d.source_doc_type = 'proposal_detail'
          AND d.extraction_method LIKE 'deterministic%%'
        ORDER BY (d.coverage_id IS NOT NULL) DESC, d.updated_at DESC
        LIMIT 1
    """, (template_id, insurer_code, insurer_coverage_name_raw))

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

        # Step 3.5: Enrich with comparison_description (STEP NEXT-AF-FIX-2)
        # Row-level matching with template_id + insurer_code isolation + raw coverage name
        if "fact_table" in view_model_dict and "rows" in view_model_dict["fact_table"]:
            # Build coverage metadata map (insurer → coverage_item)
            coverage_metadata = {}

            if compare_response.coverage_a:
                coverage_metadata[compare_response.coverage_a.insurer.upper()] = compare_response.coverage_a

            if compare_response.coverage_b:
                coverage_metadata[compare_response.coverage_b.insurer.upper()] = compare_response.coverage_b

            # Get template_id for each insurer (with insurer_code safety check)
            cursor = conn.cursor()
            template_ids = {}

            for insurer_upper, coverage_item in coverage_metadata.items():
                # AF-FIX-2: Get template_id with insurer_code verification
                cursor.execute("""
                    SELECT pc.template_id
                    FROM v2.proposal_coverage pc
                    JOIN v2.template t ON t.template_id = pc.template_id
                    JOIN v2.product p ON p.product_id = t.product_id
                    WHERE pc.insurer_coverage_name = %s
                      AND p.insurer_code = %s
                    ORDER BY pc.updated_at DESC
                    LIMIT 1
                """, (coverage_item.coverage_name_raw, coverage_item.insurer.upper()))

                result = cursor.fetchone()
                if result:
                    template_ids[insurer_upper] = result[0]

            cursor.close()

            # Enrich each row with comparison_description
            for row in view_model_dict["fact_table"]["rows"]:
                insurer = row.get("insurer")

                # Get coverage metadata for this row's insurer
                coverage_item = coverage_metadata.get(insurer)
                if not coverage_item:
                    continue

                # Get template_id for this insurer
                template_id = template_ids.get(insurer)
                if not template_id:
                    continue

                # AF-FIX-2: Use coverage_name_raw (DB key) instead of coverage_title_normalized (UI string)
                # The row's coverage_title_normalized might be canonical_coverage_code,
                # but we need to match by original insurer_coverage_name
                detail_text, source_meta = fetch_comparison_description(
                    conn,
                    template_id,
                    coverage_item.insurer.upper(),  # insurer_code
                    coverage_item.coverage_name_raw  # raw DB key, not normalized UI string
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
