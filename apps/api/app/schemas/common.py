"""
Common schemas shared across all endpoints
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class Axis(str, Enum):
    """축(axis) 구분은 헌법"""
    compare = "compare"
    amount_bridge = "amount_bridge"


class Mode(str, Enum):
    """정렬/우선순위 모드"""
    premium = "premium"
    compensation = "compensation"


class SaleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ALL = "ALL"


class Gender(str, Enum):
    M = "M"
    F = "F"


class PaymentMethod(str, Enum):
    월납 = "월납"
    연납 = "연납"
    일시납 = "일시납"
    기타 = "기타"


class Currency(str, Enum):
    KRW = "KRW"


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class DebugHardRules(BaseModel):
    """E2E 테스트에서 검증 가능한 하드룰 체크 결과"""
    is_synthetic_filter_applied: Optional[bool] = None
    compare_axis_forbids_synthetic: Optional[bool] = None
    premium_mode_requires_premium_filter: Optional[bool] = None

    class Config:
        extra = "forbid"


class DebugBlock(BaseModel):
    hard_rules: Optional[DebugHardRules] = None
    notes: Optional[List[str]] = None

    class Config:
        extra = "forbid"


# Filters
class ProductFilter(BaseModel):
    insurer_codes: Optional[List[str]] = None
    product_query: Optional[str] = None
    product_type: Optional[str] = None
    sale_status: Optional[SaleStatus] = None

    class Config:
        extra = "forbid"


class PremiumFilter(BaseModel):
    """보험료 필터 - mode=premium 정렬/랭킹에는 필수"""
    age: int = Field(..., ge=0, le=120)
    gender: Gender
    payment_period_years: Optional[int] = Field(None, ge=0, le=100)
    coverage_period_to_age: Optional[int] = Field(None, ge=0, le=120)
    payment_method: Optional[PaymentMethod] = None

    class Config:
        extra = "forbid"


class CoverageRef(BaseModel):
    """담보 참조"""
    coverage_code: Optional[str] = None
    coverage_name: Optional[str] = None

    class Config:
        extra = "forbid"


class CoverageFilter(BaseModel):
    coverage: Optional[CoverageRef] = None
    min_coverage_amount: Optional[int] = Field(None, ge=0)
    max_coverage_amount: Optional[int] = Field(None, ge=0)
    disease_query: Optional[str] = None

    class Config:
        extra = "forbid"


class Paging(BaseModel):
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)

    class Config:
        extra = "forbid"
