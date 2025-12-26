"""
Type definitions for ViewModel.

These types match the JSON Schema defined in
docs/ui/compare_view_model.schema.json
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


# Enum types matching schema
InsurerCode = Literal["SAMSUNG", "HANWHA", "LOTTE", "MERITZ", "KB", "HYUNDAI", "HEUNGKUK", "DB"]
StatusCode = Literal["OK", "MISSING_EVIDENCE", "UNMAPPED", "AMBIGUOUS", "OUT_OF_UNIVERSE"]
DocType = Literal["가입설계서", "약관", "상품요약서", "사업방법서"]
SlotKey = Literal[
    "waiting_period",
    "payment_frequency",
    "diagnosis_definition",
    "method_condition",
    "exclusion_scope",
    "payout_limit",
    "disease_scope",
]


class AmountInfo(BaseModel):
    """Amount information with evidence reference."""
    amount_value: float
    amount_unit: Literal["만원"]
    display_text: str
    evidence_ref_id: Optional[str] = None


class Header(BaseModel):
    """BLOCK 0: User Query"""
    user_query: str
    normalized_query: Optional[str] = None


class InsurerSnapshot(BaseModel):
    """Per-insurer snapshot data."""
    insurer: InsurerCode
    headline_amount: Optional[AmountInfo] = None
    status: StatusCode


class FilterCriteria(BaseModel):
    """v2: Optional filter criteria (fact-only)"""
    insurer_filter: Optional[List[str]] = None
    disease_scope: Optional[List[str]] = None
    slot_key: Optional[str] = None
    difference_detected: Optional[bool] = None


class Snapshot(BaseModel):
    """BLOCK 1: Coverage Snapshot"""
    comparison_basis: str
    insurers: List[InsurerSnapshot]
    filter_criteria: Optional[FilterCriteria] = None


class PayoutCondition(BaseModel):
    """Slot-based payout condition."""
    slot_key: SlotKey
    value_text: str
    evidence_ref_id: Optional[str] = None


class ComparisonDescriptionSource(BaseModel):
    """Source metadata for comparison description (STEP NEXT-AF)."""
    doc_type: Literal["proposal_detail"]  # Always proposal_detail
    page: int


class FactTableRow(BaseModel):
    """Single row in fact table."""
    insurer: InsurerCode
    coverage_title_normalized: str
    benefit_amount: Optional[AmountInfo] = None
    payout_conditions: List[PayoutCondition] = Field(default_factory=list)
    term_text: Optional[str] = None
    note_text: Optional[str] = None
    row_status: StatusCode
    highlight: Optional[List[str]] = None  # v2: Cell keys to emphasize
    comparison_description: Optional[str] = None  # STEP NEXT-AF: Proposal detail text (NOT evidence)
    comparison_description_source: Optional[ComparisonDescriptionSource] = None  # STEP NEXT-AF: Source metadata


class SortMetadata(BaseModel):
    """v2: Optional sorting configuration (UI hint)"""
    sort_by: Optional[str] = None
    sort_order: Optional[Literal["asc", "desc"]] = None
    limit: Optional[int] = None


class VisualEmphasis(BaseModel):
    """v2: Optional visual styling for min/max values (UI hint only)"""
    min_value_style: Optional[Literal["blue", "green", "default"]] = None
    max_value_style: Optional[Literal["red", "orange", "default"]] = None


class FactTable(BaseModel):
    """BLOCK 2: Fact Table"""
    columns: List[str] = Field(
        default=["보험사", "담보명(정규화)", "보장금액", "지급 조건 요약", "보험기간", "비고"]
    )
    rows: List[FactTableRow]
    table_type: Literal["default", "ox_matrix"] = "default"  # v2: Table display mode
    sort_metadata: Optional[SortMetadata] = None  # v2: Sorting configuration
    visual_emphasis: Optional[VisualEmphasis] = None  # v2: Visual styling


class BBox(BaseModel):
    """PDF bounding box coordinates."""
    x: float
    y: float
    width: float
    height: float


class EvidencePanel(BaseModel):
    """Single evidence panel entry."""
    id: str
    insurer: InsurerCode
    doc_type: DocType
    doc_title: Optional[str] = None
    page: Union[str, int]
    excerpt: str = Field(min_length=25, max_length=400)
    bbox: Optional[BBox] = None
    source_meta: Optional[Dict[str, Any]] = None


class RetrievalInfo(BaseModel):
    """Retrieval parameters for debug."""
    topk: Optional[int] = None
    strategy: Optional[str] = None
    doc_priority: Optional[List[str]] = None


class Debug(BaseModel):
    """Non-UI debug/reproducibility section."""
    resolved_coverage_codes: Optional[List[str]] = None
    retrieval: Optional[RetrievalInfo] = None
    warnings: Optional[List[str]] = None
    execution_time_ms: Optional[float] = None


class ViewModel(BaseModel):
    """
    Complete ViewModel for UI presentation layer.

    This is the single source of truth for UI rendering.
    Backend generates this, frontend renders it without processing.
    """
    schema_version: str = Field(pattern=r"^next4\.v[0-9]+(\.[0-9]+)?$")
    generated_at: datetime
    header: Header
    snapshot: Snapshot
    fact_table: FactTable
    evidence_panels: List[EvidencePanel]
    debug: Optional[Debug] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
