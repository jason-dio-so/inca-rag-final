"""
/compare/compile endpoint - Deterministic Compiler

Constitutional Principles:
- No LLM, no inference
- Rule-based compilation only
- Returns compiled request + debug info
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from ..compiler import (
    compile_request,
    detect_clarification_needed,
    CompileInput,
    CompileOutput,
)


class ClarifyRequest(BaseModel):
    """Request body for /compare/clarify endpoint."""
    query: str
    insurers: Optional[List[str]] = None


router = APIRouter(tags=["Compiler"])


@router.post("/compare/compile")
async def compile_compare_request(input_data: CompileInput) -> CompileOutput:
    """
    Compile user selections into ProposalCompareRequest.

    Constitutional Compliance:
    - Deterministic (same input → same output)
    - No LLM inference
    - Rule-based only
    - Returns debug info for reproducibility

    Args:
        input_data: CompileInput with user selections

    Returns:
        CompileOutput with compiled_request and compiler_debug

    Raises:
        HTTPException 400: If compilation fails due to invalid input
        HTTPException 500: If internal compilation error
    """
    try:
        result = compile_request(input_data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Compilation failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal compilation error: {str(e)}"
        )


@router.post("/compare/clarify")
async def check_clarification_needed(request: ClarifyRequest) -> Dict[str, Any]:
    """
    Check if clarification is needed for the query.

    Constitutional Compliance:
    - Deterministic rule-based detection
    - No LLM inference
    - Returns structured clarification requirements

    Args:
        request: ClarifyRequest with query and optional insurers

    Returns:
        Dict with clarification_needed flag and required_selections
    """
    try:
        result = detect_clarification_needed(request.query, request.insurers)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Clarification detection error: {str(e)}"
        )
