"""
/evidence/amount-bridge endpoint
"""
from fastapi import APIRouter, HTTPException, Depends
from psycopg2.extensions import connection as PGConnection
from ..schemas.evidence import (
    AmountBridgeRequest,
    AmountBridgeResponse,
    AmountEvidence,
    AmountContextType
)
from ..schemas.common import DebugHardRules, DebugBlock, Currency
from ..policy import enforce_amount_bridge_policy
from ..db import get_readonly_conn
from ..queries.evidence import get_amount_bridge_evidence as query_amount_evidence

router = APIRouter(prefix="/evidence", tags=["Evidence"])


@router.post("/amount-bridge", response_model=AmountBridgeResponse)
async def get_amount_bridge_evidence(
    request: AmountBridgeRequest,
    conn: PGConnection = Depends(get_readonly_conn)
):
    """
    금액 증거 수집 (amount_bridge axis 전용)

    헌법:
    - axis는 반드시 "amount_bridge"
    - include_synthetic=true 허용 (옵션) - 이 축에서만 허용!
    - compare 축과 완전 분리
    - Read-only DB access
    """
    # 헌법 강제 (400 발생 가능)
    enforce_amount_bridge_policy(request)

    # Extract parameters
    include_synthetic = True
    max_evidence = 20
    if request.options:
        include_synthetic = request.options.include_synthetic
        max_evidence = request.options.max_evidence

    # Query DB (read-only)
    try:
        evidence_rows = query_amount_evidence(
            conn=conn,
            coverage_code=request.coverage_code,
            insurer_codes=request.insurer_codes,
            include_synthetic=include_synthetic,
            limit=max_evidence
        )

        # Convert to schema using DB-sourced amount fields
        evidences = []
        for row in evidence_rows:
            # Map amount_unit to Currency enum (KRW default)
            currency = Currency.KRW
            amount_unit = row.get("amount_unit", "").upper()
            if amount_unit in ["USD", "EUR", "JPY", "CNY"]:
                currency = Currency[amount_unit]

            # Use context_type from DB (validated by CHECK constraint)
            context_type = AmountContextType(row["context_type"])

            evidences.append(
                AmountEvidence(
                    chunk_id=row["chunk_id"],
                    is_synthetic=row["is_synthetic"],
                    synthetic_source_chunk_id=row.get("synthetic_source_chunk_id"),
                    amount_value=int(row["amount_value"]) if row.get("amount_value") else 0,
                    currency=currency,
                    amount_text=row.get("amount_text", ""),
                    context_type=context_type,
                    snippet=row.get("snippet", ""),
                    insurer_code=row.get("insurer_code"),
                    product_id=row.get("product_id"),
                    product_name=row.get("product_name"),
                    document_id=row.get("document_id"),
                    page_number=row.get("page_number")
                )
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    debug_hard_rules = DebugHardRules(
        is_synthetic_filter_applied=not include_synthetic
    )

    return AmountBridgeResponse(
        axis=request.axis,
        coverage_code=request.coverage_code,
        evidences=evidences,
        debug=DebugBlock(
            hard_rules=debug_hard_rules,
            notes=[
                "DB read-only implementation",
                f"include_synthetic={include_synthetic} (allowed in amount_bridge axis)",
                "SQL template controls is_synthetic filtering (see queries/evidence.py)",
                "Amount data from amount_entity table (신정원 통일 코드)"
            ]
        )
    )
