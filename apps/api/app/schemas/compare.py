"""
Compare endpoint schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from .common import (
    Axis,
    Mode,
    ProductFilter,
    PremiumFilter,
    CoverageFilter,
    DebugBlock,
)


class CompareOptions(BaseModel):
    """Compare 축에서는 include_synthetic=true 금지"""
    include_evidence: bool = True
    include_synthetic: bool = False
    max_evidence_per_item: int = Field(5, ge=0, le=20)
    include_conditions_summary: bool = False

    class Config:
        extra = "forbid"


class CompareRequestFilter(BaseModel):
    product: Optional[ProductFilter] = None
    premium: Optional[PremiumFilter] = None
    coverage: Optional[CoverageFilter] = None

    class Config:
        extra = "forbid"


class CompareRequestTarget(BaseModel):
    product_ids: Optional[List[int]] = None

    class Config:
        extra = "forbid"


class CompareRequest(BaseModel):
    """
    Compare 요청 헌법:
    - axis는 반드시 "compare"
    - mode=premium 인 경우 filter.premium 필수(없으면 400)
    - options.include_synthetic=true 요청 금지(400)
    """
    axis: Axis
    mode: Mode
    filter: Optional[CompareRequestFilter] = None
    target: Optional[CompareRequestTarget] = None
    options: Optional[CompareOptions] = None

    class Config:
        extra = "forbid"


class EvidenceItem(BaseModel):
    """Compare 축에서는 is_synthetic 항상 false"""
    chunk_id: int
    document_id: Optional[int] = None
    page_number: Optional[int] = None
    is_synthetic: bool
    synthetic_source_chunk_id: Optional[int] = None
    snippet: str
    doc_type: Optional[str] = None

    class Config:
        extra = "forbid"


class CompareItem(BaseModel):
    rank: int
    insurer_code: str
    product_id: int
    product_name: str
    premium_amount: Optional[int] = None
    coverage_code: Optional[str] = None
    coverage_amount: Optional[int] = None
    conditions_summary: Optional[str] = None
    evidence: Optional[List[EvidenceItem]] = None

    class Config:
        extra = "forbid"


class UnmappedBlock(BaseModel):
    input_coverage_name: Optional[str] = None
    unmapped_names: Optional[List[str]] = None
    recommendations: Optional[Any] = None  # CoverageRecommendations

    class Config:
        extra = "forbid"


class CompareResponse(BaseModel):
    axis: Axis
    mode: Mode
    criteria: Optional[Dict[str, Any]] = None
    items: List[CompareItem]
    unmapped: Optional[UnmappedBlock] = None
    debug: Optional[DebugBlock] = None

    class Config:
        extra = "forbid"
