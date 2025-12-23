"""
/compare endpoint
"""
from fastapi import APIRouter, HTTPException
from ..schemas.compare import (
    CompareRequest,
    CompareResponse,
    CompareItem,
    EvidenceItem
)
from ..schemas.common import DebugHardRules, DebugBlock, Mode
from ..policy import enforce_compare_policy
from ..db import db_readonly_session
from ..queries.compare import (
    get_products_for_compare,
    get_compare_evidence,
    get_coverage_amount_for_product
)

router = APIRouter(tags=["Compare"])


@router.post("/compare", response_model=CompareResponse)
async def compare_products(request: CompareRequest):
    """
    상품 비교 (compare axis 전용)

    헌법:
    - axis는 반드시 "compare"
    - mode=premium 인 경우 filter.premium 필수
    - options.include_synthetic=true 금지 → POLICY_VIOLATION
    - 서버는 항상 is_synthetic=false 강제 (SQL WHERE clause)
    """
    # 헌법 강제 (400 발생 가능)
    enforce_compare_policy(request)

    # Extract parameters
    product_ids = None
    insurer_codes = None
    coverage_code = None

    if request.target:
        product_ids = request.target.product_ids

    if request.filter:
        if request.filter.product:
            insurer_codes = request.filter.product.insurer_codes
        if request.filter.coverage and request.filter.coverage.coverage:
            coverage_code = request.filter.coverage.coverage.coverage_code

    # Options
    include_evidence = True
    max_evidence = 5
    if request.options:
        include_evidence = request.options.include_evidence
        max_evidence = request.options.max_evidence_per_item

    # Query DB (read-only)
    try:
        with db_readonly_session() as conn:
            # Get products for comparison
            product_rows = get_products_for_compare(
                conn=conn,
                product_ids=product_ids,
                insurer_codes=insurer_codes,
                limit=10
            )

            # Build compare items
            items = []
            for rank, product_row in enumerate(product_rows, start=1):
                product_id = product_row["product_id"]

                # Get coverage amount if coverage_code provided
                coverage_amount = None
                if coverage_code:
                    coverage_amount = get_coverage_amount_for_product(
                        conn=conn,
                        product_id=product_id,
                        coverage_code=coverage_code
                    )

                # Get evidence (CONSTITUTIONAL: is_synthetic=false enforced in SQL)
                evidence_list = []
                if include_evidence:
                    evidence_rows = get_compare_evidence(
                        conn=conn,
                        product_id=product_id,
                        coverage_code=coverage_code,
                        limit=max_evidence
                    )
                    evidence_list = [
                        EvidenceItem(
                            chunk_id=row["chunk_id"],
                            document_id=row.get("document_id"),
                            page_number=row.get("page_number"),
                            is_synthetic=row["is_synthetic"],  # Always false from SQL
                            synthetic_source_chunk_id=row.get("synthetic_source_chunk_id"),
                            snippet=row["snippet"],
                            doc_type=row.get("doc_type")
                        )
                        for row in evidence_rows
                    ]

                items.append(CompareItem(
                    rank=rank,
                    insurer_code=product_row["insurer_code"],
                    product_id=product_id,
                    product_name=product_row["product_name"],
                    premium_amount=None,  # TODO: premium calculation
                    coverage_code=coverage_code,
                    coverage_amount=coverage_amount,
                    conditions_summary=None,  # TODO: conditions extraction
                    evidence=evidence_list if evidence_list else None
                ))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    debug_hard_rules = DebugHardRules(
        is_synthetic_filter_applied=True,
        compare_axis_forbids_synthetic=True,
        premium_mode_requires_premium_filter=(request.mode == Mode.premium)
    )

    return CompareResponse(
        axis=request.axis,
        mode=request.mode,
        items=items,
        debug=DebugBlock(
            hard_rules=debug_hard_rules,
            notes=[
                "DB read-only implementation",
                "is_synthetic=false enforced in SQL WHERE clause (see queries/compare.py)"
            ]
        )
    )
