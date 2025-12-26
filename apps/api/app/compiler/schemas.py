"""
Compiler input/output schemas.

Constitutional Principles:
- Schema-validated input/output
- No inference in schema definitions
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CompileOptions(BaseModel):
    """
    Compile options (user selections).

    These are NOT inferred - they come from user selection in ClarifyPanel.
    """
    surgery_method: Optional[str] = Field(
        None,
        description="Surgery method: da_vinci | robot | laparoscopic | any"
    )
    cancer_subtypes: Optional[List[str]] = Field(
        None,
        description="Cancer subtypes: 제자리암 | 경계성종양 | 유사암 | 일반암"
    )
    comparison_focus: Optional[str] = Field(
        None,
        description="Comparison focus: amount | definition | condition"
    )

    class Config:
        extra = "forbid"


class CompileInput(BaseModel):
    """
    Input to deterministic compiler.

    Constitutional Compliance:
    - No LLM inference
    - All fields come from user selection (ClarifyPanel)
    """
    user_query: str = Field(..., description="Original user query")
    selected_insurers: List[str] = Field(
        ...,
        description="Selected insurers (e.g., ['SAMSUNG', 'MERITZ'])"
    )
    selected_comparison_basis: Optional[str] = Field(
        None,
        description="Selected coverage name (normalized) for comparison basis"
    )
    options: Optional[CompileOptions] = Field(
        None,
        description="User-selected options"
    )

    class Config:
        extra = "forbid"


class CompilerDebug(BaseModel):
    """
    Compiler debug information (for Debug tab).

    Constitutional Compliance:
    - Fact-only (no recommendation)
    - Presentation only
    - Reproducibility guaranteed
    """
    rule_version: str = Field(..., description="Compiler rule version")
    resolved_coverage_codes: Optional[List[str]] = Field(
        None,
        description="Resolved canonical coverage codes (신정원 통일코드)"
    )
    selected_slots: Dict[str, Any] = Field(
        {},
        description="Normalized user selections"
    )
    decision_trace: List[str] = Field(
        [],
        description="Decision trace (which rules were applied)"
    )
    warnings: List[str] = Field(
        [],
        description="Warnings (e.g., AMBIGUOUS mapping)"
    )

    class Config:
        extra = "forbid"


class CompileOutput(BaseModel):
    """
    Output from deterministic compiler.

    Constitutional Compliance:
    - compiled_request matches ProposalCompareRequest schema
    - compiler_debug for reproducibility
    """
    compiled_request: Dict[str, Any] = Field(
        ...,
        description="Compiled request (ProposalCompareRequest-compatible)"
    )
    compiler_debug: CompilerDebug = Field(
        ...,
        description="Debug information (for Debug tab)"
    )

    class Config:
        extra = "forbid"
