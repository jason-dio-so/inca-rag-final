"""
DB Insurance Policy Parser (STEP 8)

STUB implementation for multi-insurer architecture demonstration

Constitutional principles:
- Deterministic extraction only (regex + rules)
- NO LLM/inference/similarity
- Evidence required (basis_doc_id, basis_page, basis_span)
"""
from typing import Optional, List
from ..base_parser import (
    BasePolicyParser,
    DiseaseGroupDefinition,
    CoverageScopeDefinition
)


class DBPolicyParser(BasePolicyParser):
    """
    DB Insurance-specific policy parser

    Implementation status: STUB
    Supported concepts: None (stub only)

    NOTE: This is a STUB implementation for STEP 8 multi-insurer architecture.
    Full implementation requires actual DB Insurance policy document patterns.

    Purpose:
    - Demonstrate registry pattern (3+ insurers)
    - Show NotImplementedError handling
    - Placeholder for future implementation
    """

    @property
    def insurer_code(self) -> str:
        return 'DB'

    @property
    def supported_concepts(self) -> List[str]:
        return []  # Stub - no concepts supported yet

    @property
    def implementation_status(self) -> str:
        return 'STUB'

    def extract_disease_group_definition(
        self,
        policy_text: str,
        group_concept: str,
        document_id: str,
        page_number: int
    ) -> Optional[DiseaseGroupDefinition]:
        """
        Extract disease group definition from DB Insurance policy

        STUB: Not implemented yet

        Args:
            policy_text: Policy document text content
            group_concept: Disease concept to extract (e.g., '유사암')
            document_id: Policy document ID for evidence
            page_number: Page number for evidence

        Returns:
            None (stub implementation)

        Raises:
            NotImplementedError: If called (stub parser)
        """
        # Stub implementation - return None
        # Future: Implement actual DB Insurance pattern matching
        return None

    def extract_coverage_disease_scope(
        self,
        policy_text: str,
        coverage_name: str,
        document_id: str,
        page_number: int
    ) -> Optional[CoverageScopeDefinition]:
        """
        Extract disease scope definition for specific coverage from DB Insurance policy

        STUB: Not implemented yet

        Args:
            policy_text: Policy document text
            coverage_name: Coverage name to find scope for
            document_id: Policy document ID
            page_number: Page number

        Returns:
            None (stub implementation)

        Raises:
            NotImplementedError: If called (stub parser)
        """
        # Stub implementation - return None
        # Future: Implement actual DB Insurance pattern matching
        return None
