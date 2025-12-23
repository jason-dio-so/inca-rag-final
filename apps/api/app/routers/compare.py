"""
/compare endpoint
"""
from fastapi import APIRouter
from ..schemas.compare import CompareRequest, CompareResponse
from ..schemas.common import DebugHardRules, DebugBlock, Mode
from ..policy import enforce_compare_policy

router = APIRouter(tags=["Compare"])


@router.post("/compare", response_model=CompareResponse)
async def compare_products(request: CompareRequest):
    """
    상품 비교 (compare axis 전용)

    헌법:
    - axis는 반드시 "compare"
    - mode=premium 인 경우 filter.premium 필수
    - options.include_synthetic=true 금지 → POLICY_VIOLATION
    - 서버는 항상 is_synthetic=false 강제
    """
    # 헌법 강제 (400 발생 가능)
    enforce_compare_policy(request)

    # Dummy response (contract-only implementation)
    has_premium_filter = (
        request.filter is not None
        and request.filter.premium is not None
    )

    debug_hard_rules = DebugHardRules(
        is_synthetic_filter_applied=True,
        compare_axis_forbids_synthetic=True,
        premium_mode_requires_premium_filter=(request.mode == Mode.premium)
    )

    return CompareResponse(
        axis=request.axis,
        mode=request.mode,
        items=[],  # Skeleton: empty list
        debug=DebugBlock(
            hard_rules=debug_hard_rules,
            notes=[
                "Contract-only skeleton implementation",
                "is_synthetic=false filter is enforced in DB query (not implemented yet)"
            ]
        )
    )
