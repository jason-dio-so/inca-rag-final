"""
Pydantic schemas matching OpenAPI contract
"""
from .common import *
from .products import *
from .compare import *
from .evidence import *

__all__ = [
    # Common
    "Axis",
    "Mode",
    "SaleStatus",
    "Gender",
    "PaymentMethod",
    "Currency",
    "ErrorCode",
    "ErrorDetail",
    "ErrorResponse",
    "DebugHardRules",
    "DebugBlock",
    # Filters
    "ProductFilter",
    "PremiumFilter",
    "CoverageRef",
    "CoverageFilter",
    "Paging",
    # Products
    "SearchProductsRequest",
    "ProductSummary",
    "CoverageCandidate",
    "CoverageRecommendations",
    "SearchProductsResponse",
    # Compare
    "CompareOptions",
    "CompareRequest",
    "EvidenceItem",
    "CompareItem",
    "UnmappedBlock",
    "CompareResponse",
    # Evidence
    "AmountContextType",
    "AmountBridgeOptions",
    "AmountBridgeRequest",
    "AmountEvidence",
    "AmountBridgeResponse",
]
