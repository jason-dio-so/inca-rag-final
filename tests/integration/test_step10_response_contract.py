"""
STEP 10-C: Response Contract Integration Tests

Constitutional Requirements Tested:
1. Document priority fixed order (PROPOSAL → PRODUCT_SUMMARY → BUSINESS_METHOD → POLICY)
2. Evidence grouping and deterministic ordering
3. Policy evidence conditional (only when disease_scope_norm exists)
4. All evidence items have required fields

Test Strategy:
- Test evidence ordering and grouping functions directly (unit-style)
- No DB dependency (deterministic logic only)
"""
import pytest
from src.policy_scope.comparison.evidence_order import (
    EvidenceItem,
    DocumentType,
    GroupedEvidence,
    group_and_order_evidence,
    get_document_priority,
    validate_policy_evidence_conditional,
)


class TestSTEP10ResponseContract:
    """
    STEP 10-C: Response contract integration tests

    Constitutional Requirement:
    - 가입설계서 = 비교 대상 SSOT (proposal evidence required)
    - 약관 = 조건부 (policy evidence conditional on interpretation need)
    - 문서 우선순위 고정 (document priority never changes)
    """

    def test_document_priority_fixed_order(self):
        """
        Test 1: Document priority is always fixed order

        Constitutional requirement:
        - document_priority = ["PROPOSAL", "PRODUCT_SUMMARY", "BUSINESS_METHOD", "POLICY"]
        - This order NEVER changes
        """
        priority = get_document_priority()

        assert priority == [
            "PROPOSAL",
            "PRODUCT_SUMMARY",
            "BUSINESS_METHOD",
            "POLICY",
        ], "Document priority must be fixed order (Constitutional)"

    def test_evidence_grouping_and_ordering(self):
        """
        Test 2: Evidence grouped by doc_type and sorted deterministically

        Constitutional requirement:
        - Evidence grouped by document type
        - Within each group, sorted by page then span_text (deterministic)
        """
        # Create mixed evidence (out of order)
        evidence_items = [
            # POLICY (should go to policy group, page 10)
            EvidenceItem(
                document_id="POLICY_DOC",
                doc_type=DocumentType.POLICY,
                page=10,
                span_text="유사암 정의...",
                source_confidence="policy_required",
            ),
            # PROPOSAL (should go to proposal group, page 2)
            EvidenceItem(
                document_id="PROPOSAL_DOC",
                doc_type=DocumentType.PROPOSAL,
                page=2,
                span_text="일반암진단비",
                source_confidence="proposal_confirmed",
            ),
            # PROPOSAL (should go to proposal group, page 1 - earlier than page 2)
            EvidenceItem(
                document_id="PROPOSAL_DOC",
                doc_type=DocumentType.PROPOSAL,
                page=1,
                span_text="담보 목록",
                source_confidence="proposal_confirmed",
            ),
            # POLICY (should go to policy group, page 9 - earlier than page 10)
            EvidenceItem(
                document_id="POLICY_DOC",
                doc_type=DocumentType.POLICY,
                page=9,
                span_text="갑상선암 정의",
                source_confidence="policy_required",
            ),
        ]

        # Group and order (disease_scope_norm exists → policy evidence allowed)
        grouped = group_and_order_evidence(
            evidence_items,
            disease_scope_norm={"include_group_id": "GROUP_A", "exclude_group_id": "GROUP_B"},
        )

        # Verify proposal group (sorted by page)
        assert len(grouped.proposal) == 2
        assert grouped.proposal[0].page == 1  # Earlier page first
        assert grouped.proposal[1].page == 2

        # Verify policy group (sorted by page)
        assert len(grouped.policy) == 2
        assert grouped.policy[0].page == 9  # Earlier page first
        assert grouped.policy[1].page == 10

        # Verify other groups empty
        assert len(grouped.product_summary) == 0
        assert len(grouped.business_method) == 0

    def test_policy_evidence_conditional_none_disease_scope(self):
        """
        Test 3: Policy evidence empty when disease_scope_norm is None

        Constitutional requirement:
        - If disease_scope_norm is None (no policy interpretation needed),
          policy evidence MUST be empty
        """
        # Create evidence with policy items
        evidence_items = [
            EvidenceItem(
                document_id="PROPOSAL_DOC",
                doc_type=DocumentType.PROPOSAL,
                page=1,
                span_text="일반암진단비",
                source_confidence="proposal_confirmed",
            ),
            EvidenceItem(
                document_id="POLICY_DOC",
                doc_type=DocumentType.POLICY,
                page=10,
                span_text="유사암 정의",
                source_confidence="policy_required",
            ),
        ]

        # Group with disease_scope_norm = None (no policy interpretation)
        grouped = group_and_order_evidence(
            evidence_items,
            disease_scope_norm=None,  # No policy interpretation needed
        )

        # Policy evidence MUST be empty (Constitutional requirement)
        assert len(grouped.policy) == 0, \
            "Policy evidence must be empty when disease_scope_norm is None (Constitutional)"

        # Proposal evidence still present
        assert len(grouped.proposal) == 1

    def test_policy_evidence_exists_when_disease_scope_norm_present(self):
        """
        Test 4: Policy evidence allowed when disease_scope_norm exists

        Constitutional requirement:
        - If disease_scope_norm is not None (policy interpretation was used),
          policy evidence may be present
        """
        evidence_items = [
            EvidenceItem(
                document_id="PROPOSAL_DOC",
                doc_type=DocumentType.PROPOSAL,
                page=1,
                span_text="일반암진단비",
                source_confidence="proposal_confirmed",
            ),
            EvidenceItem(
                document_id="POLICY_DOC",
                doc_type=DocumentType.POLICY,
                page=10,
                span_text="유사암 정의: 갑상선암(C73), 기타피부암(C44)",
                source_confidence="policy_required",
            ),
        ]

        # Group with disease_scope_norm present (policy interpretation applied)
        grouped = group_and_order_evidence(
            evidence_items,
            disease_scope_norm={"include_group_id": "CANCER_GENERAL", "exclude_group_id": "SIMILAR_CANCER"},
        )

        # Policy evidence allowed (not required, but allowed)
        assert len(grouped.policy) == 1
        assert grouped.policy[0].document_id == "POLICY_DOC"
        assert grouped.policy[0].page == 10

    def test_proposal_evidence_required(self):
        """
        Test 5: Proposal evidence is required (Constitutional)

        Constitutional requirement:
        - 가입설계서 = 비교 대상 SSOT
        - Proposal evidence must exist for valid comparison
        """
        # Create evidence without proposal (only policy)
        evidence_items = [
            EvidenceItem(
                document_id="POLICY_DOC",
                doc_type=DocumentType.POLICY,
                page=10,
                span_text="유사암 정의",
                source_confidence="policy_required",
            ),
        ]

        # Should raise ValueError (Constitutional violation)
        with pytest.raises(ValueError, match="Proposal evidence required"):
            group_and_order_evidence(
                evidence_items,
                disease_scope_norm={"include_group_id": "GROUP_A"},
            )

    def test_evidence_item_required_fields(self):
        """
        Test 6: All evidence items must have required fields

        Constitutional requirement:
        - document_id, doc_type, page, span_text, source_confidence required
        - Missing any field should raise ValueError
        """
        # Missing document_id
        with pytest.raises(ValueError, match="document_id required"):
            EvidenceItem(
                document_id="",
                doc_type=DocumentType.PROPOSAL,
                page=1,
                span_text="test",
                source_confidence="proposal_confirmed",
            )

        # Missing span_text
        with pytest.raises(ValueError, match="span_text required"):
            EvidenceItem(
                document_id="DOC_ID",
                doc_type=DocumentType.PROPOSAL,
                page=1,
                span_text="",
                source_confidence="proposal_confirmed",
            )

        # Invalid page (< 1)
        with pytest.raises(ValueError, match="page must be >= 1"):
            EvidenceItem(
                document_id="DOC_ID",
                doc_type=DocumentType.PROPOSAL,
                page=0,
                span_text="test",
                source_confidence="proposal_confirmed",
            )

    def test_validate_policy_evidence_conditional(self):
        """
        Test 7: Validate policy evidence conditional logic

        Constitutional requirement:
        - Policy evidence only when disease_scope_norm exists
        """
        # Case 1: disease_scope_norm = None, policy evidence = [] → VALID
        grouped_valid = GroupedEvidence(
            proposal=[
                EvidenceItem("DOC", DocumentType.PROPOSAL, 1, "test", "proposal_confirmed")
            ],
            product_summary=[],
            business_method=[],
            policy=[],
        )
        assert validate_policy_evidence_conditional(grouped_valid, disease_scope_norm=None)

        # Case 2: disease_scope_norm = None, policy evidence = [item] → INVALID
        grouped_invalid = GroupedEvidence(
            proposal=[
                EvidenceItem("DOC", DocumentType.PROPOSAL, 1, "test", "proposal_confirmed")
            ],
            product_summary=[],
            business_method=[],
            policy=[
                EvidenceItem("POLICY", DocumentType.POLICY, 10, "test", "policy_required")
            ],
        )
        assert not validate_policy_evidence_conditional(grouped_invalid, disease_scope_norm=None)

        # Case 3: disease_scope_norm exists, policy evidence = [item] → VALID
        grouped_with_policy = GroupedEvidence(
            proposal=[
                EvidenceItem("DOC", DocumentType.PROPOSAL, 1, "test", "proposal_confirmed")
            ],
            product_summary=[],
            business_method=[],
            policy=[
                EvidenceItem("POLICY", DocumentType.POLICY, 10, "test", "policy_required")
            ],
        )
        assert validate_policy_evidence_conditional(
            grouped_with_policy,
            disease_scope_norm={"include_group_id": "GROUP_A"},
        )

    def test_deterministic_ordering_same_page(self):
        """
        Test 8: Evidence on same page sorted by span_text (deterministic)

        Constitutional requirement:
        - Deterministic ordering: page ASC, then span_text ASC
        """
        evidence_items = [
            EvidenceItem(
                document_id="PROPOSAL_DOC",
                doc_type=DocumentType.PROPOSAL,
                page=1,
                span_text="ZZZ 담보",  # Same page, but later alphabetically
                source_confidence="proposal_confirmed",
            ),
            EvidenceItem(
                document_id="PROPOSAL_DOC",
                doc_type=DocumentType.PROPOSAL,
                page=1,
                span_text="AAA 담보",  # Same page, earlier alphabetically
                source_confidence="proposal_confirmed",
            ),
        ]

        grouped = group_and_order_evidence(evidence_items, disease_scope_norm=None)

        # Verify sorted by span_text (alphabetical)
        assert len(grouped.proposal) == 2
        assert grouped.proposal[0].span_text == "AAA 담보"  # Earlier alphabetically
        assert grouped.proposal[1].span_text == "ZZZ 담보"

    def test_grouped_evidence_to_dict(self):
        """
        Test 9: GroupedEvidence serializes to dict correctly

        Requirement:
        - to_dict() returns evidence grouped by doc_type
        - Each group is array of dicts with required fields
        """
        evidence_items = [
            EvidenceItem(
                document_id="PROPOSAL_DOC",
                doc_type=DocumentType.PROPOSAL,
                page=1,
                span_text="일반암진단비",
                source_confidence="proposal_confirmed",
            ),
            EvidenceItem(
                document_id="POLICY_DOC",
                doc_type=DocumentType.POLICY,
                page=10,
                span_text="유사암 정의",
                source_confidence="policy_required",
            ),
        ]

        grouped = group_and_order_evidence(
            evidence_items,
            disease_scope_norm={"include_group_id": "GROUP_A"},
        )

        result = grouped.to_dict()

        # Verify structure
        assert "proposal" in result
        assert "product_summary" in result
        assert "business_method" in result
        assert "policy" in result

        # Verify proposal evidence
        assert len(result["proposal"]) == 1
        assert result["proposal"][0]["document_id"] == "PROPOSAL_DOC"
        assert result["proposal"][0]["doc_type"] == "PROPOSAL"
        assert result["proposal"][0]["page"] == 1
        assert result["proposal"][0]["span_text"] == "일반암진단비"
        assert result["proposal"][0]["source_confidence"] == "proposal_confirmed"

        # Verify policy evidence
        assert len(result["policy"]) == 1
        assert result["policy"][0]["document_id"] == "POLICY_DOC"
