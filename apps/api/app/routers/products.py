"""
/search/products endpoint
"""
from fastapi import APIRouter
from ..schemas.products import SearchProductsRequest, SearchProductsResponse
from ..schemas.common import DebugHardRules, DebugBlock, Mode
from ..policy import enforce_search_products_policy

router = APIRouter(prefix="/search", tags=["Products"])


@router.post("/products", response_model=SearchProductsResponse)
async def search_products(request: SearchProductsRequest):
    """
    상품 검색

    헌법:
    - sort.mode=premium 인 경우 premium 필터 없으면 400
    """
    # 헌법 강제
    enforce_search_products_policy(request)

    # Dummy response (contract-only implementation)
    mode = request.sort.mode if request.sort else None
    has_premium_filter = (
        request.filter is not None
        and request.filter.premium is not None
    )

    debug_hard_rules = DebugHardRules(
        premium_mode_requires_premium_filter=(mode == Mode.premium)
    )

    return SearchProductsResponse(
        items=[],  # Skeleton: empty list
        debug=DebugBlock(
            hard_rules=debug_hard_rules,
            notes=["Contract-only skeleton implementation"]
        )
    )
