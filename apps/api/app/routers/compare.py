"""
/compare endpoint - AH-6: Cancer Canonical Decision Integration
"""
from fastapi import APIRouter, HTTPException, Depends
from psycopg2.extensions import connection as PGConnection
from typing import Optional, Dict, Any, List
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
from ..contracts import (
    validate_compare_response,  # STEP 24: Runtime code guard
    validate_ux_message_code,   # STEP 26: UX message code guard
)
from ..ah.compare_integration import CancerCompareIntegration
from ..ah.cancer_decision import CancerCanonicalDecision, DecisionStatus

router = APIRouter(tags=["Compare"])


@router.post("/compare", response_model=ProposalCompareResponse)
async def compare_proposals(
    request: ProposalCompareRequest,
    conn: PGConnection = Depends(get_readonly_conn)
):
    """
    AH-6: Cancer Canonical Decision Integration

    Constitutional Principles:
    - Universe Lock: Only coverages in proposal_coverage_universe can be compared
    - Cancer Canonical Decision: Query → Excel Alias → Policy Evidence → DECIDED/UNDECIDED
    - Compare execution ONLY uses DECIDED codes (UNDECIDED → empty set, "확정 불가")
    - No LLM/heuristic/fallback to recalled_candidates

    Flow:
    1. Query → CancerCompareIntegration → CancerCanonicalDecision per insurer
    2. DECIDED: Use decided_canonical_codes for comparison
    3. UNDECIDED: Return "약관 근거 부족으로 확정 불가" (NO comparison)
    """
    try:
        # Step 1: Get insurers list (support both legacy and new formats)
        if request.insurers:
            insurers = request.insurers
        else:
            insurers = [request.insurer_a or "SAMSUNG"]
            if request.insurer_b:
                insurers.append(request.insurer_b)

        # Step 2: Initialize Cancer Compare Integration
        cancer_integration = CancerCompareIntegration(conn=conn)

        # Step 3: Resolve cancer canonical decisions for all insurers
        compare_context = cancer_integration.resolve_compare_context(
            query=request.query,
            insurer_codes=insurers,
        )

        # Step 4: Check if we have any DECIDED codes
        all_decided = all(d.is_decided() for d in compare_context.decisions)
        any_decided = any(d.is_decided() for d in compare_context.decisions)

        # Step 5: Get canonical codes for comparison (DECIDED only)
        canonical_codes_for_compare = set()
        for decision in compare_context.decisions:
            # Constitutional Rule: ONLY DECIDED codes are used for comparison
            canonical_codes_for_compare.update(
                code.value for code in decision.get_canonical_codes_for_compare()
            )

        # If no DECIDED codes, we cannot compare
        if not canonical_codes_for_compare:
            # All UNDECIDED → return "확정 불가"
            return _build_undecided_response(
                request=request,
                compare_context=compare_context,
            )

        # Step 6: For backward compatibility, use first decided code
        canonical_code = list(canonical_codes_for_compare)[0] if canonical_codes_for_compare else None
        raw_name = None

        # Step 7: Get coverages from proposal universe
        insurer_a = insurers[0]
        insurer_b = insurers[1] if len(insurers) > 1 else None

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
        comparison_result, next_action, message, ux_message_code = determine_comparison_result(
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
                proposal_id=coverage_a.get("proposal_id", f"proposal_{coverage_a.get('coverage_id', 'unknown')}"),
                coverage_name_raw=coverage_a["coverage_name_raw"],
                canonical_coverage_code=coverage_a.get("canonical_coverage_code"),
                mapping_status=coverage_a.get("mapping_status", "UNKNOWN"),
                amount_value=coverage_a.get("amount_value"),
                disease_scope_raw=coverage_a.get("disease_scope_raw"),
                disease_scope_norm=coverage_a.get("disease_scope_norm"),
                source_confidence=coverage_a.get("source_confidence"),
                # STEP NEXT-AF-FIX-3: Row-level keys
                coverage_id=coverage_a.get("coverage_id"),
                template_id=coverage_a.get("template_id")
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
                proposal_id=coverage_b.get("proposal_id", f"proposal_{coverage_b.get('coverage_id', 'unknown')}"),
                coverage_name_raw=coverage_b["coverage_name_raw"],
                canonical_coverage_code=coverage_b.get("canonical_coverage_code"),
                mapping_status=coverage_b.get("mapping_status", "UNKNOWN"),
                amount_value=coverage_b.get("amount_value"),
                disease_scope_raw=coverage_b.get("disease_scope_raw"),
                disease_scope_norm=coverage_b.get("disease_scope_norm"),
                source_confidence=coverage_b.get("source_confidence"),
                # STEP NEXT-AF-FIX-3: Row-level keys
                coverage_id=coverage_b.get("coverage_id"),
                template_id=coverage_b.get("template_id")
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

        # STEP 26: UX message code validation (fail-fast on unknown codes)
        validate_ux_message_code(ux_message_code)

        # AH-6: Include cancer canonical decision context in debug
        return ProposalCompareResponse(
            query=request.query,
            comparison_result=comparison_result,
            next_action=next_action,
            coverage_a=response_coverage_a,
            coverage_b=response_coverage_b,
            policy_evidence_a=policy_evidence_a,
            policy_evidence_b=policy_evidence_b,
            message=message,
            ux_message_code=ux_message_code,
            debug={
                "canonical_code_resolved": canonical_code,
                "raw_name_used": raw_name,
                "universe_lock_enforced": True,
                "cancer_canonical_decision": compare_context.to_dict() if compare_context else None,
                "decided_codes_for_compare": list(canonical_codes_for_compare),
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
) -> tuple[str, str, str, str]:
    """
    Determine comparison result and UX message.

    Returns:
        (comparison_result, next_action, message, ux_message_code)
    """
    # Scenario: out_of_universe
    if not coverage_a:
        return (
            "out_of_universe",
            "REQUEST_MORE_INFO",
            f"'{query}' coverage not found in {insurer_a} proposal universe",
            "COVERAGE_NOT_IN_UNIVERSE"
        )

    # Single coverage query (Scenario B/C)
    if not insurer_b or not coverage_b:
        # Check UNMAPPED first
        if coverage_a.get("mapping_status") == "UNMAPPED":
            return (
                "unmapped",
                "REQUEST_MORE_INFO",
                f"{coverage_a.get('coverage_name_raw')} is not mapped to canonical coverage code",
                "COVERAGE_UNMAPPED"
            )

        # Check disease_scope_norm (Scenario C)
        if coverage_a.get("disease_scope_norm"):
            return (
                "policy_required",
                "VERIFY_POLICY",
                f"Disease scope verification required for {coverage_a.get('coverage_name_raw')}",
                "DISEASE_SCOPE_VERIFICATION_REQUIRED"
            )

        return (
            "comparable",
            "COMPARE",
            f"{coverage_a.get('coverage_name_raw')} found in {insurer_a}",
            "COVERAGE_FOUND_SINGLE_INSURER"
        )

    # Scenario B: UNMAPPED
    if coverage_a.get("mapping_status") == "UNMAPPED":
        return (
            "unmapped",
            "REQUEST_MORE_INFO",
            f"{coverage_a.get('coverage_name_raw')} is not mapped to canonical coverage code",
            "COVERAGE_UNMAPPED"
        )

    if coverage_b.get("mapping_status") == "UNMAPPED":
        return (
            "unmapped",
            "REQUEST_MORE_INFO",
            f"{coverage_b.get('coverage_name_raw')} is not mapped to canonical coverage code",
            "COVERAGE_UNMAPPED"
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
                f"Coverage comparison possible but disease scope verification required",
                "COVERAGE_COMPARABLE_WITH_GAPS"
            )

        return (
            "comparable",
            "COMPARE",
            f"Both insurers have {coverage_a.get('canonical_coverage_code')}",
            "COVERAGE_MATCH_COMPARABLE"
        )

    # Different canonical codes
    return (
        "non_comparable",
        "REQUEST_MORE_INFO",
        f"Different coverage types: {coverage_a.get('canonical_coverage_code')} vs {coverage_b.get('canonical_coverage_code')}",
        "COVERAGE_TYPE_MISMATCH"
    )


def _build_undecided_response(
    request: ProposalCompareRequest,
    compare_context: Any,  # CancerCompareContext
) -> ProposalCompareResponse:
    """
    Build response for UNDECIDED cancer canonical decision.

    Constitutional Rule (AH-6):
    - UNDECIDED → "약관 근거 부족으로 확정 불가"
    - NO comparison execution (empty canonical codes)
    - NO fallback to recalled_candidates
    - NO recommendations/inferences/alternatives

    Args:
        request: Original compare request
        compare_context: Cancer compare context with UNDECIDED decisions

    Returns:
        ProposalCompareResponse with UNDECIDED status
    """
    return ProposalCompareResponse(
        query=request.query,
        comparison_result="undecided",
        next_action="REQUEST_MORE_INFO",
        coverage_a=None,
        coverage_b=None,
        policy_evidence_a=None,
        policy_evidence_b=None,
        message="약관 근거 부족으로 담보 확정 불가",
        ux_message_code="CANCER_CANONICAL_UNDECIDED",
        debug={
            "cancer_canonical_decision": compare_context.to_dict(),
            "decided_count": compare_context.get_decided_count(),
            "undecided_count": compare_context.get_undecided_count(),
            "decided_rate": compare_context.get_decided_rate(),
            "reason": "All cancer canonical decisions are UNDECIDED (no policy evidence)",
        }
    )
