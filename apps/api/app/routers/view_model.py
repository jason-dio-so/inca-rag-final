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
from typing import Dict, Any

from ..schemas.compare import ProposalCompareRequest
from ..db import get_readonly_conn
from ..view_model.assembler import assemble_view_model
from ..view_model.schema_loader import load_schema, validate_view_model
from .compare import compare_proposals as base_compare_proposals


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

        # Step 4: Runtime schema validation (if enabled)
        if ENABLE_SCHEMA_VALIDATION:
            try:
                schema = load_schema()
                validate_view_model(view_model_dict, schema)
            except Exception as validation_error:
                # Fail-fast: Schema validation failure is a critical error
                raise HTTPException(
                    status_code=500,
                    detail=f"ViewModel schema validation failed: {str(validation_error)}"
                )

        return view_model_dict

    except HTTPException:
        # Re-raise HTTP exceptions from base_compare_proposals
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ViewModel assembly error: {str(e)}"
        )
