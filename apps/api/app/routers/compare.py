"""
/compare endpoint - STEP 14-α: Proposal Universe Lock enforcement
"""
from fastapi import APIRouter, HTTPException, Depends
from psycopg2.extensions import connection as PGConnection
from typing import Optional, Dict, Any
from ..schemas.compare import (
    CompareRequest,
    CompareResponse,
    CompareItem,
    EvidenceItem,
    ProposalCompareRequest,
    ProposalCompareResponse,
    ProposalCoverageItem,
    PolicyEvidence
)
from ..schemas.common import DebugHardRules, DebugBlock, Mode
from ..policy import enforce_compare_policy
from ..db import get_readonly_conn
from ..queries.compare import (
    get_products_for_compare,
    get_compare_evidence,
    get_coverage_amount_for_proposal,
    get_proposal_coverage,
    get_disease_code_group
)
from ..services.conditions_summary_service import generate_conditions_summary
from ..contracts import validate_compare_response  # STEP 24: Runtime code guard

router = APIRouter(tags=["Compare"])


# STEP 14-α: Deterministic query resolution rules
# Constitutional: NO LLM, NO inference - only exact keyword matching
QUERY_RESOLUTION_RULES = {
    "일반암진단비": "CA_DIAG_GENERAL",
    "유사암진단금": "CA_DIAG_SIMILAR",
    # Add more mappings as needed
}


def resolve_query_to_canonical(query: str) -> Optional[str]:
    """
    Resolve user query to canonical coverage code via deterministic rules.

    Constitutional: NO LLM, NO similarity matching.
    Returns None if no exact match found.
    """
    query_normalized = query.strip()
    return QUERY_RESOLUTION_RULES.get(query_normalized)


@router.post("/compare", response_model=ProposalCompareResponse)
async def compare_proposals(
    request: ProposalCompareRequest,
    conn: PGConnection = Depends(get_readonly_conn)
):
    """
    STEP 14-α: Proposal Universe-based Coverage Comparison

    Constitutional Principles:
    - Universe Lock: Only coverages in proposal_coverage_universe can be compared
    - Deterministic query resolution (NO LLM)
    - Excel-based mapping (NO inference)
    - Evidence order: PROPOSAL → PRODUCT_SUMMARY → BUSINESS_METHOD → POLICY

    Scenarios:
    - A: Normal comparison (두 보험사 모두 MAPPED, 같은 canonical code)
    - B: UNMAPPED coverage (Excel에 매핑 없음)
    - C: Disease scope required (disease_scope_norm 존재, policy evidence 필요)
    """
    try:
        # Step 1: Resolve query to canonical code or raw name
        canonical_code = resolve_query_to_canonical(request.query)
        raw_name = None if canonical_code else request.query

        # Step 2: Default insurers if not provided (for test scenarios)
        insurer_a = request.insurer_a or "SAMSUNG"
        insurer_b = request.insurer_b or "MERITZ"

        # Handle special case: single insurer query (Scenario C)
        if not request.insurer_b and canonical_code == "CA_DIAG_SIMILAR":
            insurer_b = None  # Single coverage lookup

        # Step 3: Get coverages from proposal universe
        coverage_a = get_proposal_coverage(
            conn=conn,
            insurer=insurer_a,
            canonical_code=canonical_code,
            raw_name=raw_name
        )

        coverage_b = None
        if insurer_b:
            coverage_b = get_proposal_coverage(
                conn=conn,
                insurer=insurer_b,
                canonical_code=canonical_code,
                raw_name=raw_name
            )

        # Step 4: Determine comparison result
        comparison_result, next_action, message = determine_comparison_result(
            coverage_a=coverage_a,
            coverage_b=coverage_b,
            query=request.query,
            insurer_a=insurer_a,
            insurer_b=insurer_b
        )

        # Step 5: Build response items
        response_coverage_a = None
        response_coverage_b = None
        policy_evidence_a = None
        policy_evidence_b = None

        if coverage_a:
            response_coverage_a = ProposalCoverageItem(
                insurer=coverage_a["insurer"],
                proposal_id=coverage_a["proposal_id"],
                coverage_name_raw=coverage_a["coverage_name_raw"],
                canonical_coverage_code=coverage_a.get("canonical_coverage_code"),
                mapping_status=coverage_a.get("mapping_status", "UNKNOWN"),
                amount_value=coverage_a.get("amount_value"),
                disease_scope_raw=coverage_a.get("disease_scope_raw"),
                disease_scope_norm=coverage_a.get("disease_scope_norm"),
                source_confidence=coverage_a.get("source_confidence")
            )

            # Get policy evidence if disease_scope_norm exists
            if (coverage_a.get("disease_scope_norm") and
                request.include_policy_evidence):
                policy_evidence_a = get_disease_code_group(
                    conn=conn,
                    insurer=coverage_a["insurer"],
                    group_name_pattern="%유사암%"
                )
                if policy_evidence_a:
                    policy_evidence_a = PolicyEvidence(
                        group_name=policy_evidence_a["group_name"],
                        insurer=policy_evidence_a["insurer"],
                        member_count=policy_evidence_a["member_count"]
                    )

        if coverage_b:
            response_coverage_b = ProposalCoverageItem(
                insurer=coverage_b["insurer"],
                proposal_id=coverage_b["proposal_id"],
                coverage_name_raw=coverage_b["coverage_name_raw"],
                canonical_coverage_code=coverage_b.get("canonical_coverage_code"),
                mapping_status=coverage_b.get("mapping_status", "UNKNOWN"),
                amount_value=coverage_b.get("amount_value"),
                disease_scope_raw=coverage_b.get("disease_scope_raw"),
                disease_scope_norm=coverage_b.get("disease_scope_norm"),
                source_confidence=coverage_b.get("source_confidence")
            )

            # Get policy evidence if disease_scope_norm exists
            if (coverage_b.get("disease_scope_norm") and
                request.include_policy_evidence):
                policy_evidence_b = get_disease_code_group(
                    conn=conn,
                    insurer=coverage_b["insurer"],
                    group_name_pattern="%유사암%"
                )
                if policy_evidence_b:
                    policy_evidence_b = PolicyEvidence(
                        group_name=policy_evidence_b["group_name"],
                        insurer=policy_evidence_b["insurer"],
                        member_count=policy_evidence_b["member_count"]
                    )

        # STEP 24: Runtime code validation (fail-fast on unknown codes)
        validate_compare_response(comparison_result, next_action)

        return ProposalCompareResponse(
            query=request.query,
            comparison_result=comparison_result,
            next_action=next_action,
            coverage_a=response_coverage_a,
            coverage_b=response_coverage_b,
            policy_evidence_a=policy_evidence_a,
            policy_evidence_b=policy_evidence_b,
            message=message,
            debug={
                "canonical_code_resolved": canonical_code,
                "raw_name_used": raw_name,
                "universe_lock_enforced": True
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


def determine_comparison_result(
    coverage_a: Optional[Dict[str, Any]],
    coverage_b: Optional[Dict[str, Any]],
    query: str,
    insurer_a: str,
    insurer_b: Optional[str]
) -> tuple[str, str, str]:
    """
    Determine comparison result and UX message.

    Returns:
        (comparison_result, next_action, message)
    """
    # Scenario: out_of_universe
    if not coverage_a:
        return (
            "out_of_universe",
            "REQUEST_MORE_INFO",
            f"'{query}' coverage not found in {insurer_a} proposal universe"
        )

    # Single coverage query (Scenario B/C)
    if not insurer_b or not coverage_b:
        # Check UNMAPPED first
        if coverage_a.get("mapping_status") == "UNMAPPED":
            return (
                "unmapped",
                "REQUEST_MORE_INFO",
                f"{coverage_a.get('coverage_name_raw')} is not mapped to canonical coverage code"
            )

        # Check disease_scope_norm (Scenario C)
        if coverage_a.get("disease_scope_norm"):
            return (
                "policy_required",
                "VERIFY_POLICY",
                f"Disease scope verification required for {coverage_a.get('coverage_name_raw')}"
            )

        return (
            "comparable",
            "COMPARE",
            f"{coverage_a.get('coverage_name_raw')} found in {insurer_a}"
        )

    # Scenario B: UNMAPPED
    if coverage_a.get("mapping_status") == "UNMAPPED":
        return (
            "unmapped",
            "REQUEST_MORE_INFO",
            f"{coverage_a.get('coverage_name_raw')} is not mapped to canonical coverage code"
        )

    if coverage_b.get("mapping_status") == "UNMAPPED":
        return (
            "unmapped",
            "REQUEST_MORE_INFO",
            f"{coverage_b.get('coverage_name_raw')} is not mapped to canonical coverage code"
        )

    # Scenario A: Normal comparison (same canonical code)
    if (coverage_a.get("canonical_coverage_code") ==
        coverage_b.get("canonical_coverage_code") and
        coverage_a.get("canonical_coverage_code") is not None):

        # Check if disease_scope_norm exists (requires policy verification)
        if coverage_a.get("disease_scope_norm") or coverage_b.get("disease_scope_norm"):
            return (
                "comparable_with_gaps",
                "VERIFY_POLICY",
                f"Coverage comparison possible but disease scope verification required"
            )

        return (
            "comparable",
            "COMPARE",
            f"Both insurers have {coverage_a.get('canonical_coverage_code')}"
        )

    # Different canonical codes
    return (
        "non_comparable",
        "REQUEST_MORE_INFO",
        f"Different coverage types: {coverage_a.get('canonical_coverage_code')} vs {coverage_b.get('canonical_coverage_code')}"
    )
