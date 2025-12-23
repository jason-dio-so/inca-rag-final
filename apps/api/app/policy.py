"""
운영 헌법(Hard Rules) 강제 모듈

본 모듈은 STEP 5 운영 헌법을 400 에러로 강제한다.
"""
from fastapi import HTTPException
from .schemas.common import ErrorCode, ErrorDetail, ErrorResponse, Axis, Mode
from .schemas.products import SearchProductsRequest
from .schemas.compare import CompareRequest
from .schemas.evidence import AmountBridgeRequest


def validate_premium_mode_requires_premium_filter(
    mode: Mode | None,
    has_premium_filter: bool,
    endpoint: str
) -> None:
    """
    Rule A: premium mode requires premium filter
    mode=premium인 경우 premium 필터 없으면 400
    """
    if mode == Mode.premium and not has_premium_filter:
        error_response = ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.VALIDATION_ERROR,
                message=f"{endpoint}: premium mode requires premium filter",
                details={
                    "rule": "premium_mode_requires_premium_filter",
                    "mode": mode.value,
                    "has_premium_filter": has_premium_filter,
                }
            )
        )
        raise HTTPException(
            status_code=400,
            detail=error_response.model_dump()["error"]
        )


def validate_compare_axis_only(axis: Axis) -> None:
    """
    Rule B: compare axis만 허용
    axis가 "compare"가 아니면 400
    """
    if axis != Axis.compare:
        error_response = ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.VALIDATION_ERROR,
                message="Compare endpoint requires axis='compare'",
                details={
                    "rule": "compare_axis_only",
                    "provided_axis": axis.value,
                    "expected_axis": "compare",
                }
            )
        )
        raise HTTPException(
            status_code=400,
            detail=error_response.model_dump()["error"]
        )


def validate_compare_forbids_synthetic(include_synthetic: bool) -> None:
    """
    Rule B-2: compare axis는 synthetic 금지
    options.include_synthetic=true면 400
    """
    if include_synthetic:
        error_response = ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.POLICY_VIOLATION,
                message="Compare axis forbids synthetic chunks (include_synthetic must be false)",
                details={
                    "rule": "compare_axis_forbids_synthetic",
                    "include_synthetic": include_synthetic,
                }
            )
        )
        raise HTTPException(
            status_code=400,
            detail=error_response.model_dump()["error"]
        )


def validate_amount_bridge_axis_only(axis: Axis) -> None:
    """
    Rule C: amount_bridge axis만 허용
    axis가 "amount_bridge"가 아니면 400
    """
    if axis != Axis.amount_bridge:
        error_response = ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.VALIDATION_ERROR,
                message="Amount Bridge endpoint requires axis='amount_bridge'",
                details={
                    "rule": "amount_bridge_axis_only",
                    "provided_axis": axis.value,
                    "expected_axis": "amount_bridge",
                }
            )
        )
        raise HTTPException(
            status_code=400,
            detail=error_response.model_dump()["error"]
        )


def enforce_search_products_policy(request: SearchProductsRequest) -> None:
    """
    /search/products 헌법 강제
    - sort.mode=premium 인 경우 premium 필터 필수
    """
    mode = request.sort.mode if request.sort else None
    has_premium_filter = (
        request.filter is not None
        and request.filter.premium is not None
    )

    if mode:
        validate_premium_mode_requires_premium_filter(
            mode=mode,
            has_premium_filter=has_premium_filter,
            endpoint="/search/products"
        )


def enforce_compare_policy(request: CompareRequest) -> None:
    """
    /compare 헌법 강제
    - axis는 반드시 "compare"
    - mode=premium 인 경우 filter.premium 필수
    - options.include_synthetic=true 금지
    """
    # Rule B: axis must be "compare"
    validate_compare_axis_only(request.axis)

    # Rule A: premium mode requires premium filter
    has_premium_filter = (
        request.filter is not None
        and request.filter.premium is not None
    )
    validate_premium_mode_requires_premium_filter(
        mode=request.mode,
        has_premium_filter=has_premium_filter,
        endpoint="/compare"
    )

    # Rule B-2: compare forbids synthetic
    include_synthetic = (
        request.options.include_synthetic
        if request.options
        else False
    )
    validate_compare_forbids_synthetic(include_synthetic)


def enforce_amount_bridge_policy(request: AmountBridgeRequest) -> None:
    """
    /evidence/amount-bridge 헌법 강제
    - axis는 반드시 "amount_bridge"
    """
    # Rule C: axis must be "amount_bridge"
    validate_amount_bridge_axis_only(request.axis)
