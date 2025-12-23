"""
Product search schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from .common import (
    ProductFilter,
    PremiumFilter,
    CoverageFilter,
    Paging,
    Mode,
    SaleStatus,
    DebugBlock,
)


class SortOptions(BaseModel):
    mode: Optional[Mode] = None
    direction: Optional[str] = Field("asc", pattern="^(asc|desc)$")

    class Config:
        extra = "forbid"


class SearchProductsRequestFilter(BaseModel):
    product: Optional[ProductFilter] = None
    premium: Optional[PremiumFilter] = None
    coverage: Optional[CoverageFilter] = None

    class Config:
        extra = "forbid"


class SearchProductsRequest(BaseModel):
    """상품 검색 - sort.mode=premium 인 경우 premium 필터 없으면 400"""
    filter: Optional[SearchProductsRequestFilter] = None
    sort: Optional[SortOptions] = None
    paging: Optional[Paging] = None

    class Config:
        extra = "forbid"


class ProductSummary(BaseModel):
    product_id: int
    insurer_code: str
    product_code: str
    product_name: str
    product_type: Optional[str] = None
    sale_status: Optional[SaleStatus] = None
    premium_amount: Optional[int] = None

    class Config:
        extra = "forbid"


class CoverageCandidate(BaseModel):
    coverage_code: str
    score: float = Field(..., ge=0, le=1)
    reason: Optional[str] = None

    class Config:
        extra = "forbid"


class CoverageRecommendations(BaseModel):
    input_coverage_name: str
    candidates: List[CoverageCandidate]
    next_action: str

    class Config:
        extra = "forbid"


class SearchProductsResponse(BaseModel):
    items: List[ProductSummary]
    recommendations: Optional[CoverageRecommendations] = None
    debug: Optional[DebugBlock] = None

    class Config:
        extra = "forbid"
