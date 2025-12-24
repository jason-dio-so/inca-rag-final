"""
STEP 10-C: Evidence Order Enforcement

Purpose: Deterministic evidence grouping and ordering by document priority

Constitutional Requirements:
- Document priority: PROPOSAL → PRODUCT_SUMMARY → BUSINESS_METHOD → POLICY
- Policy evidence is conditional (only when required for interpretation)
- Evidence within each group sorted deterministically (page, then span_text)
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class DocumentType(str, Enum):
    """Document types in priority order (Constitutional)"""
    PROPOSAL = "PROPOSAL"
    PRODUCT_SUMMARY = "PRODUCT_SUMMARY"
    BUSINESS_METHOD = "BUSINESS_METHOD"
    POLICY = "POLICY"


# Fixed document priority order (Constitutional requirement)
DOCUMENT_PRIORITY_ORDER = [
    DocumentType.PROPOSAL,
    DocumentType.PRODUCT_SUMMARY,
    DocumentType.BUSINESS_METHOD,
    DocumentType.POLICY,
]


@dataclass
class EvidenceItem:
    """
    Single evidence item with source information

    Constitutional requirement: All fields required when evidence exists
    """
    document_id: str
    doc_type: DocumentType
    page: int
    span_text: str
    source_confidence: str  # proposal_confirmed | policy_required | unknown
    extracted_at: Optional[str] = None  # ISO 8601 datetime (optional)

    def __post_init__(self):
        """Validate required fields"""
        if not self.document_id:
            raise ValueError("document_id required for evidence")
        if not self.span_text:
            raise ValueError("span_text required for evidence")
        if self.page < 1:
            raise ValueError("page must be >= 1")


@dataclass
class GroupedEvidence:
    """
    Evidence grouped by document type in priority order

    Constitutional requirement:
    - proposal: Always present (minimum 1 item for valid comparison)
    - product_summary: Optional
    - business_method: Optional
    - policy: Conditional (only when interpretation required)
    """
    proposal: List[EvidenceItem]
    product_summary: List[EvidenceItem]
    business_method: List[EvidenceItem]
    policy: List[EvidenceItem]

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert to dictionary for JSON serialization"""
        return {
            "proposal": [_evidence_to_dict(e) for e in self.proposal],
            "product_summary": [_evidence_to_dict(e) for e in self.product_summary],
            "business_method": [_evidence_to_dict(e) for e in self.business_method],
            "policy": [_evidence_to_dict(e) for e in self.policy],
        }


def _evidence_to_dict(evidence: EvidenceItem) -> Dict[str, Any]:
    """Convert EvidenceItem to dictionary"""
    result = {
        "document_id": evidence.document_id,
        "doc_type": evidence.doc_type.value,
        "page": evidence.page,
        "span_text": evidence.span_text,
        "source_confidence": evidence.source_confidence,
    }
    if evidence.extracted_at:
        result["extracted_at"] = evidence.extracted_at
    return result


def _sort_evidence_deterministic(evidence_list: List[EvidenceItem]) -> List[EvidenceItem]:
    """
    Sort evidence deterministically within a group

    Sort order:
    1. page (ascending)
    2. span_text (ascending, for same page)

    Returns:
        Sorted list (deterministic)
    """
    return sorted(evidence_list, key=lambda e: (e.page, e.span_text))


def group_and_order_evidence(
    evidence_items: List[EvidenceItem],
    disease_scope_norm: Optional[Dict[str, str]] = None
) -> GroupedEvidence:
    """
    Group evidence by document type and order deterministically

    Constitutional requirements:
    1. Evidence grouped by doc_type in priority order
    2. Within each group, sorted by page then span_text (deterministic)
    3. Policy evidence only included if:
       - disease_scope_norm is not None (policy interpretation required)
       - OR other slots requiring legal interpretation exist

    Args:
        evidence_items: List of all evidence items
        disease_scope_norm: Normalized disease scope (if policy enrichment applied)

    Returns:
        GroupedEvidence with deterministic ordering

    Raises:
        ValueError: If proposal evidence missing (Constitutional violation)
    """
    # Group by document type
    proposal = []
    product_summary = []
    business_method = []
    policy = []

    for item in evidence_items:
        if item.doc_type == DocumentType.PROPOSAL:
            proposal.append(item)
        elif item.doc_type == DocumentType.PRODUCT_SUMMARY:
            product_summary.append(item)
        elif item.doc_type == DocumentType.BUSINESS_METHOD:
            business_method.append(item)
        elif item.doc_type == DocumentType.POLICY:
            policy.append(item)

    # Constitutional requirement: Proposal evidence must exist for valid comparison
    if not proposal:
        raise ValueError(
            "Proposal evidence required (Constitutional: 가입설계서 = 비교 대상 SSOT)"
        )

    # Deterministic sorting within each group
    proposal = _sort_evidence_deterministic(proposal)
    product_summary = _sort_evidence_deterministic(product_summary)
    business_method = _sort_evidence_deterministic(business_method)

    # Policy evidence is conditional
    # Only include if disease_scope_norm exists (policy interpretation was needed)
    if disease_scope_norm is None:
        # No policy interpretation required → empty policy evidence
        policy = []
    else:
        # Policy interpretation was used → sort policy evidence
        policy = _sort_evidence_deterministic(policy)

    return GroupedEvidence(
        proposal=proposal,
        product_summary=product_summary,
        business_method=business_method,
        policy=policy,
    )


def get_document_priority() -> List[str]:
    """
    Get fixed document priority order

    Constitutional requirement: This order NEVER changes

    Returns:
        ["PROPOSAL", "PRODUCT_SUMMARY", "BUSINESS_METHOD", "POLICY"]
    """
    return [dt.value for dt in DOCUMENT_PRIORITY_ORDER]


def validate_policy_evidence_conditional(
    evidence: GroupedEvidence,
    disease_scope_norm: Optional[Dict[str, str]]
) -> bool:
    """
    Validate that policy evidence is only present when conditionally required

    Constitutional requirement:
    - If disease_scope_norm is None, policy evidence must be empty
    - If disease_scope_norm exists, policy evidence may be present (but not required)

    Args:
        evidence: Grouped evidence
        disease_scope_norm: Normalized disease scope

    Returns:
        True if valid, False if constitutional violation
    """
    if disease_scope_norm is None and len(evidence.policy) > 0:
        # Constitutional violation: Policy evidence present without interpretation need
        return False

    return True
