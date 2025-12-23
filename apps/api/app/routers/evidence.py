"""
/evidence/amount-bridge endpoint
"""
from fastapi import APIRouter
from ..schemas.evidence import AmountBridgeRequest, AmountBridgeResponse
from ..schemas.common import DebugHardRules, DebugBlock
from ..policy import enforce_amount_bridge_policy

router = APIRouter(prefix="/evidence", tags=["Evidence"])


@router.post("/amount-bridge", response_model=AmountBridgeResponse)
async def get_amount_bridge_evidence(request: AmountBridgeRequest):
    """
    금액 증거 수집 (amount_bridge axis 전용)

    헌법:
    - axis는 반드시 "amount_bridge"
    - include_synthetic=true 허용 (옵션)
    - compare 축과 완전 분리
    """
    # 헌법 강제 (400 발생 가능)
    enforce_amount_bridge_policy(request)

    # Dummy response (contract-only implementation)
    include_synthetic = (
        request.options.include_synthetic
        if request.options
        else True
    )

    debug_hard_rules = DebugHardRules(
        is_synthetic_filter_applied=not include_synthetic
    )

    return AmountBridgeResponse(
        axis=request.axis,
        coverage_code=request.coverage_code,
        evidences=[],  # Skeleton: empty list
        debug=DebugBlock(
            hard_rules=debug_hard_rules,
            notes=[
                "Contract-only skeleton implementation",
                f"include_synthetic={include_synthetic} (allowed in amount_bridge axis)"
            ]
        )
    )
