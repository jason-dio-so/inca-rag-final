"""
Amount Bridge evidence schemas
"""
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from .common import Axis, Currency, DebugBlock


class AmountContextType(str, Enum):
    payment = "payment"
    limit = "limit"
    count = "count"
    other = "other"


class AmountBridgeOptions(BaseModel):
    """Amount Bridge 축에서는 synthetic 허용"""
    include_synthetic: bool = True
    max_evidence: int = Field(20, ge=1, le=100)

    class Config:
        extra = "forbid"


class AmountBridgeRequest(BaseModel):
    """
    Amount Bridge 요청 헌법:
    - axis는 반드시 "amount_bridge"
    - coverage_code 필수
    """
    axis: Axis
    coverage_code: str
    insurer_codes: Optional[List[str]] = None
    options: Optional[AmountBridgeOptions] = None

    class Config:
        extra = "forbid"


class AmountEvidence(BaseModel):
    chunk_id: int
    is_synthetic: bool
    synthetic_source_chunk_id: Optional[int] = None
    amount_value: int = Field(..., ge=0)
    currency: Optional[Currency] = Currency.KRW
    amount_text: str
    context_type: AmountContextType
    snippet: str
    insurer_code: Optional[str] = None
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    document_id: Optional[int] = None
    page_number: Optional[int] = None

    class Config:
        extra = "forbid"


class AmountBridgeResponse(BaseModel):
    axis: Axis
    coverage_code: str
    evidences: List[AmountEvidence]
    debug: Optional[DebugBlock] = None

    class Config:
        extra = "forbid"
