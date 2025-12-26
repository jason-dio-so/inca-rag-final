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


class Snapshot(BaseModel):
    """BLOCK 1: Coverage Snapshot"""
    comparison_basis: str
    insurers: List[InsurerSnapshot]


class PayoutCondition(BaseModel):
    """Slot-based payout condition."""
    slot_key: SlotKey
    value_text: str
    evidence_ref_id: Optional[str] = None


class FactTableRow(BaseModel):
    """Single row in fact table."""
    insurer: InsurerCode
    coverage_title_normalized: str
    benefit_amount: Optional[AmountInfo] = None
    payout_conditions: List[PayoutCondition] = Field(default_factory=list)
    term_text: Optional[str] = None
    note_text: Optional[str] = None
    row_status: StatusCode


class FactTable(BaseModel):
    """BLOCK 2: Fact Table"""
    columns: List[str] = Field(
        default=["보험사", "담보명(정규화)", "보장금액", "지급 조건 요약", "보험기간", "비고"]
    )
    rows: List[FactTableRow]


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
