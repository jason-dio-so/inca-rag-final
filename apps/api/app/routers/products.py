"""
/search/products endpoint
"""
from fastapi import APIRouter, HTTPException, Depends
from psycopg2.extensions import connection as PGConnection
from ..schemas.products import (
    SearchProductsRequest,
    SearchProductsResponse,
    ProductSummary,
    CoverageRecommendations,
    CoverageCandidate
)
from ..schemas.common import DebugHardRules, DebugBlock, Mode
from ..policy import enforce_search_products_policy
from ..db import get_readonly_conn
from ..queries.products import search_products as query_search_products
from ..queries.products import get_coverage_recommendations

router = APIRouter(prefix="/search", tags=["Products"])


@router.post("/products", response_model=SearchProductsResponse)
async def search_products(
    request: SearchProductsRequest,
    conn: PGConnection = Depends(get_readonly_conn)
):
    """
    상품 검색

    헌법:
    - sort.mode=premium 인 경우 premium 필터 없으면 400
    - Read-only DB access
    """
    # 헌법 강제
    enforce_search_products_policy(request)

    # Extract request parameters
    mode = request.sort.mode if request.sort else None
    has_premium_filter = (
        request.filter is not None
        and request.filter.premium is not None
    )

    # Filter parameters
    insurer_codes = None
    product_query = None
    sale_status = None
    if request.filter:
        if request.filter.product:
            insurer_codes = request.filter.product.insurer_codes
            product_query = request.filter.product.product_query
            sale_status = request.filter.product.sale_status.value if request.filter.product.sale_status else None

    # Paging
    limit = request.paging.limit if request.paging else 20
    offset = request.paging.offset if request.paging else 0

    # Coverage recommendations (if coverage_name provided but no coverage_code)
    recommendations = None
    if request.filter and request.filter.coverage:
        coverage_ref = request.filter.coverage.coverage
        if coverage_ref and coverage_ref.coverage_name and not coverage_ref.coverage_code:
            # Get recommendations from DB (no auto-INSERT)
            try:
                candidates_rows = get_coverage_recommendations(conn, coverage_ref.coverage_name)
                if candidates_rows:
                    candidates = [
                        CoverageCandidate(
                            coverage_code=row["coverage_code"],
                            score=float(row.get("score", 0.8)),
                            reason=f"Matched alias: {row.get('canonical_name', '')}"
                        )
                        for row in candidates_rows
                    ]
                    recommendations = CoverageRecommendations(
                        input_coverage_name=coverage_ref.coverage_name,
                        candidates=candidates,
                        next_action="사용자가 coverage_code 선택 후 재호출"
                    )
            except Exception:
                # If DB query fails, return empty recommendations
                pass

    # Query products from DB
    try:
        product_rows = query_search_products(
            conn=conn,
            insurer_codes=insurer_codes,
            product_query=product_query,
            sale_status=sale_status,
            limit=limit,
            offset=offset
        )

        # Convert to schema
        items = [
            ProductSummary(
                product_id=row["product_id"],
                insurer_code=row["insurer_code"],
                product_code=row["product_code"],
                product_name=row["product_name"],
                product_type=row.get("product_type"),
                sale_status=row.get("sale_status"),
                premium_amount=None  # TODO: premium calculation if filter provided
            )
            for row in product_rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    debug_hard_rules = DebugHardRules(
        premium_mode_requires_premium_filter=(mode == Mode.premium)
    )

    return SearchProductsResponse(
        items=items,
        recommendations=recommendations,
        debug=DebugBlock(
            hard_rules=debug_hard_rules,
            notes=["DB read-only implementation"]
        )
    )
