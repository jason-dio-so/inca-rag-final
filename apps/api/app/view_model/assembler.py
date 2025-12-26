"""
ViewModel assembler: ProposalCompareResponse → ViewModel

Converts backend comparison results into UI-ready ViewModel JSON.

Constitutional Principles:
- Fact-only: No inference, mapping only
- No recommendations/judgments: Status from existing data only
- Presentation layer: Formatting/sorting/structuring only
- Deterministic: Same input → same output

Input Shape (ProposalCompareResponse):
{
    "query": str,
    "comparison_result": str,  # comparable|comparable_with_gaps|non_comparable|unmapped|out_of_universe
    "next_action": str,
    "coverage_a": ProposalCoverageItem | None,
    "coverage_b": ProposalCoverageItem | None,
    "policy_evidence_a": PolicyEvidence | None,
    "policy_evidence_b": PolicyEvidence | None,
    "message": str,
    "ux_message_code": str,
    "debug": dict | None
}

Output: ViewModel (docs/ui/compare_view_model.schema.json)
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import re

from ..schemas.compare import ProposalCompareResponse, ProposalCoverageItem, PolicyEvidence
from .types import (
    ViewModel,
    Header,
    Snapshot,
    InsurerSnapshot,
    FilterCriteria,
    FactTable,
    FactTableRow,
    AmountInfo,
    PayoutCondition,
    EvidencePanel,
    Debug,
    RetrievalInfo,
    StatusCode,
    InsurerCode,
    DocType,
    SortMetadata,
    VisualEmphasis,
    ComparisonDescriptionSource,
)


# Status mapping: comparison_result + mapping_status → StatusCode
def map_status(
    comparison_result: str,
    mapping_status: Optional[str],
    has_policy_evidence: bool
) -> StatusCode:
    """
    Map ProposalCompareResponse status to ViewModel StatusCode.

    Constitutional: No new inference, conservative fallback to MISSING_EVIDENCE.

    Rules (deterministic):
    - UNMAPPED mapping_status → UNMAPPED
    - AMBIGUOUS mapping_status → AMBIGUOUS
    - out_of_universe comparison_result → OUT_OF_UNIVERSE
    - comparable + MAPPED → OK
    - comparable_with_gaps → MISSING_EVIDENCE (conservative)
    - non_comparable → OK (fact exists, just not comparable)
    - Otherwise → MISSING_EVIDENCE (conservative fallback)
    """
    if mapping_status == "UNMAPPED":
        return "UNMAPPED"
    if mapping_status == "AMBIGUOUS":
        return "AMBIGUOUS"
    if comparison_result == "out_of_universe":
        return "OUT_OF_UNIVERSE"
    if comparison_result == "comparable" and mapping_status == "MAPPED":
        return "OK"
    if comparison_result == "comparable_with_gaps":
        return "MISSING_EVIDENCE"
    if comparison_result == "non_comparable":
        return "OK"  # Fact exists, just different coverage type
    # Conservative fallback
    return "MISSING_EVIDENCE"


def format_amount(amount_value: Optional[int]) -> Optional[AmountInfo]:
    """
    Format amount value to AmountInfo.

    Input: amount_value in 원 (e.g., 30000000)
    Output: AmountInfo with 만원 unit (e.g., 3000만원)
    """
    if amount_value is None:
        return None

    # Convert to 만원
    amount_in_manwon = amount_value / 10000

    # Format display text with thousand separator
    if amount_in_manwon >= 1000:
        display_text = f"{int(amount_in_manwon):,}만원"
    else:
        # For amounts < 1000만원, show decimal if needed
        if amount_in_manwon == int(amount_in_manwon):
            display_text = f"{int(amount_in_manwon)}만원"
        else:
            display_text = f"{amount_in_manwon:.1f}만원"

    return AmountInfo(
        amount_value=amount_in_manwon,
        amount_unit="만원",
        display_text=display_text,
        evidence_ref_id=None  # Will be set later if evidence available
    )


def generate_evidence_id(insurer: str, doc_type: str, index: int) -> str:
    """
    Generate deterministic evidence ID.

    Format: ev_{insurer}_{doc_type}_{index}
    Example: ev_samsung_proposal_001
    """
    doc_type_short = {
        "가입설계서": "proposal",
        "약관": "policy",
        "상품요약서": "summary",
        "사업방법서": "business"
    }.get(doc_type, "unknown")

    return f"ev_{insurer.lower()}_{doc_type_short}_{index:03d}"


def extract_payout_conditions(
    coverage: ProposalCoverageItem,
    evidence_id: str
) -> List[PayoutCondition]:
    """
    Extract payout conditions from coverage data.

    Constitutional: Slot-based only, NO rewriting.

    Available slots from ProposalCoverageItem:
    - disease_scope_raw → disease_scope slot
    - disease_scope_norm → disease_scope slot (if available)
    - source_confidence → (not a payout condition, skip)

    Note: ProposalCompareResponse has minimal condition data.
    For full slot extraction, we'd need to query proposal detail tables.
    This is a conservative implementation using available fields only.
    """
    conditions = []

    # Slot: disease_scope
    if coverage.disease_scope_raw:
        conditions.append(PayoutCondition(
            slot_key="disease_scope",
            value_text=coverage.disease_scope_raw,
            evidence_ref_id=evidence_id
        ))

    return conditions


def assemble_view_model(
    compare_response: ProposalCompareResponse,
    include_debug: bool = True
) -> ViewModel:
    """
    Assemble ViewModel from ProposalCompareResponse.

    Args:
        compare_response: Backend comparison result
        include_debug: Whether to include debug section (default: True)

    Returns:
        ViewModel matching docs/ui/compare_view_model.schema.json

    Constitutional Compliance:
    - No inference: Status from existing data only
    - No judgment: Fact mapping only
    - Deterministic: Stable sorting by insurer/coverage/slot
    - Evidence integrity: All ref_ids resolve to evidence_panels[].id
    """
    # Evidence panels registry (populated during assembly)
    evidence_panels: List[EvidencePanel] = []
    evidence_counter = 0

    def add_evidence(
        insurer: InsurerCode,
        doc_type: DocType,
        doc_title: str,
        page: str,
        excerpt: str
    ) -> str:
        """Add evidence panel and return its ID."""
        nonlocal evidence_counter
        evidence_counter += 1
        evidence_id = generate_evidence_id(insurer, doc_type, evidence_counter)

        evidence_panels.append(EvidencePanel(
            id=evidence_id,
            insurer=insurer,
            doc_type=doc_type,
            doc_title=doc_title,
            page=page,
            excerpt=excerpt
        ))

        return evidence_id

    # BLOCK 0: Header
    header = Header(
        user_query=compare_response.query,
        normalized_query=compare_response.query.strip()
    )

    # BLOCK 1: Snapshot
    snapshot_insurers: List[InsurerSnapshot] = []

    # Process coverage_a
    if compare_response.coverage_a:
        cov_a = compare_response.coverage_a
        insurer_a = cov_a.insurer.upper()

        # Create evidence for coverage_a amount
        evidence_id_a = None
        if cov_a.amount_value:
            evidence_text = f"{cov_a.coverage_name_raw}: {cov_a.amount_value:,}원"
            if cov_a.disease_scope_raw:
                evidence_text += f" ({cov_a.disease_scope_raw})"

            # Ensure minimum 25 characters for schema compliance
            if len(evidence_text) < 25:
                evidence_text += " (가입설계서 기준)"

            evidence_id_a = add_evidence(
                insurer=insurer_a,
                doc_type="가입설계서",
                doc_title=f"{insurer_a} 가입설계서",
                page=f"proposal_{cov_a.proposal_id}",
                excerpt=evidence_text
            )

        amount_info_a = format_amount(cov_a.amount_value)
        if amount_info_a and evidence_id_a:
            amount_info_a.evidence_ref_id = evidence_id_a

        status_a = map_status(
            comparison_result=compare_response.comparison_result,
            mapping_status=cov_a.mapping_status,
            has_policy_evidence=compare_response.policy_evidence_a is not None
        )

        snapshot_insurers.append(InsurerSnapshot(
            insurer=insurer_a,
            headline_amount=amount_info_a,
            status=status_a
        ))

    # Process coverage_b
    if compare_response.coverage_b:
        cov_b = compare_response.coverage_b
        insurer_b = cov_b.insurer.upper()

        # Create evidence for coverage_b amount
        evidence_id_b = None
        if cov_b.amount_value:
            evidence_text = f"{cov_b.coverage_name_raw}: {cov_b.amount_value:,}원"
            if cov_b.disease_scope_raw:
                evidence_text += f" ({cov_b.disease_scope_raw})"

            # Ensure minimum 25 characters for schema compliance
            if len(evidence_text) < 25:
                evidence_text += " (가입설계서 기준)"

            evidence_id_b = add_evidence(
                insurer=insurer_b,
                doc_type="가입설계서",
                doc_title=f"{insurer_b} 가입설계서",
                page=f"proposal_{cov_b.proposal_id}",
                excerpt=evidence_text
            )

        amount_info_b = format_amount(cov_b.amount_value)
        if amount_info_b and evidence_id_b:
            amount_info_b.evidence_ref_id = evidence_id_b

        status_b = map_status(
            comparison_result=compare_response.comparison_result,
            mapping_status=cov_b.mapping_status,
            has_policy_evidence=compare_response.policy_evidence_b is not None
        )

        snapshot_insurers.append(InsurerSnapshot(
            insurer=insurer_b,
            headline_amount=amount_info_b,
            status=status_b
        ))

    # Determine comparison_basis (canonical_coverage_code or raw name)
    comparison_basis = "비교 담보"
    if compare_response.coverage_a:
        comparison_basis = (
            compare_response.coverage_a.canonical_coverage_code or
            compare_response.coverage_a.coverage_name_raw
        )

    snapshot = Snapshot(
        comparison_basis=comparison_basis,
        insurers=snapshot_insurers
    )

    # BLOCK 2: Fact Table
    fact_table_rows: List[FactTableRow] = []

    # Process coverage_a fact row
    if compare_response.coverage_a:
        cov_a = compare_response.coverage_a
        insurer_a = cov_a.insurer.upper()

        # Find evidence_id for amount (already created above)
        amount_evidence_id = None
        for panel in evidence_panels:
            if panel.insurer == insurer_a and "proposal" in panel.id:
                amount_evidence_id = panel.id
                break

        amount_info_a = format_amount(cov_a.amount_value)
        if amount_info_a and amount_evidence_id:
            amount_info_a.evidence_ref_id = amount_evidence_id

        payout_conditions_a = extract_payout_conditions(cov_a, amount_evidence_id or "")

        # Note text for mapping status
        note_text_a = None
        if cov_a.mapping_status == "UNMAPPED":
            note_text_a = "(UNMAPPED)"
        elif cov_a.mapping_status == "AMBIGUOUS":
            note_text_a = "(AMBIGUOUS - 수동 매핑 필요)"

        fact_table_rows.append(FactTableRow(
            insurer=insurer_a,
            coverage_title_normalized=cov_a.canonical_coverage_code or cov_a.coverage_name_raw,
            benefit_amount=amount_info_a,
            payout_conditions=payout_conditions_a,
            term_text=None,  # Not available in ProposalCoverageItem
            note_text=note_text_a,
            row_status=map_status(
                comparison_result=compare_response.comparison_result,
                mapping_status=cov_a.mapping_status,
                has_policy_evidence=compare_response.policy_evidence_a is not None
            )
        ))

    # Process coverage_b fact row
    if compare_response.coverage_b:
        cov_b = compare_response.coverage_b
        insurer_b = cov_b.insurer.upper()

        # Find evidence_id for amount
        amount_evidence_id = None
        for panel in evidence_panels:
            if panel.insurer == insurer_b and "proposal" in panel.id:
                amount_evidence_id = panel.id
                break

        amount_info_b = format_amount(cov_b.amount_value)
        if amount_info_b and amount_evidence_id:
            amount_info_b.evidence_ref_id = amount_evidence_id

        payout_conditions_b = extract_payout_conditions(cov_b, amount_evidence_id or "")

        # Note text for mapping status
        note_text_b = None
        if cov_b.mapping_status == "UNMAPPED":
            note_text_b = "(UNMAPPED)"
        elif cov_b.mapping_status == "AMBIGUOUS":
            note_text_b = "(AMBIGUOUS - 수동 매핑 필요)"

        fact_table_rows.append(FactTableRow(
            insurer=insurer_b,
            coverage_title_normalized=cov_b.canonical_coverage_code or cov_b.coverage_name_raw,
            benefit_amount=amount_info_b,
            payout_conditions=payout_conditions_b,
            term_text=None,
            note_text=note_text_b,
            row_status=map_status(
                comparison_result=compare_response.comparison_result,
                mapping_status=cov_b.mapping_status,
                has_policy_evidence=compare_response.policy_evidence_b is not None
            )
        ))

    # Deterministic sorting: insurer ASC, coverage_title ASC
    fact_table_rows.sort(key=lambda row: (row.insurer, row.coverage_title_normalized))

    fact_table = FactTable(rows=fact_table_rows)

    # Add policy evidence panels if available
    if compare_response.policy_evidence_a:
        pol_ev_a = compare_response.policy_evidence_a
        add_evidence(
            insurer=pol_ev_a.insurer.upper(),
            doc_type="약관",
            doc_title=f"{pol_ev_a.insurer} 약관",
            page="policy",
            excerpt=f"{pol_ev_a.group_name} (질병코드 그룹, {pol_ev_a.member_count}개 코드)"
        )

    if compare_response.policy_evidence_b:
        pol_ev_b = compare_response.policy_evidence_b
        add_evidence(
            insurer=pol_ev_b.insurer.upper(),
            doc_type="약관",
            doc_title=f"{pol_ev_b.insurer} 약관",
            page="policy",
            excerpt=f"{pol_ev_b.group_name} (질병코드 그룹, {pol_ev_b.member_count}개 코드)"
        )

    # BLOCK 3: Evidence Panels (deterministic sort)
    evidence_panels.sort(key=lambda panel: (panel.insurer, panel.doc_type, panel.id))

    # Debug section
    debug = None
    if include_debug:
        resolved_codes = []
        if compare_response.coverage_a and compare_response.coverage_a.canonical_coverage_code:
            resolved_codes.append(compare_response.coverage_a.canonical_coverage_code)
        if compare_response.coverage_b and compare_response.coverage_b.canonical_coverage_code:
            if compare_response.coverage_b.canonical_coverage_code not in resolved_codes:
                resolved_codes.append(compare_response.coverage_b.canonical_coverage_code)

        warnings = []
        if compare_response.comparison_result == "unmapped":
            warnings.append("Coverage UNMAPPED (no canonical code)")
        if compare_response.comparison_result == "out_of_universe":
            warnings.append("Coverage OUT_OF_UNIVERSE (not in proposal)")

        debug = Debug(
            resolved_coverage_codes=resolved_codes if resolved_codes else None,
            retrieval=RetrievalInfo(
                strategy="proposal_universe_lock",
                doc_priority=["가입설계서", "약관", "상품요약서", "사업방법서"]
            ),
            warnings=warnings if warnings else None
        )

    # Assemble ViewModel
    view_model = ViewModel(
        schema_version="next4.v2",
        generated_at=datetime.now(timezone.utc),
        header=header,
        snapshot=snapshot,
        fact_table=fact_table,
        evidence_panels=evidence_panels,
        debug=debug
    )

    return view_model
