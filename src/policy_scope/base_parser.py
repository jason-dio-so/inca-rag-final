"""
Base Policy Parser Interface (STEP 8)

Purpose: Abstract interface for insurer-specific policy parsers

Constitutional principles:
- Deterministic extraction only (regex/rules)
- NO LLM/inference
- Evidence required (basis_doc_id, basis_page, basis_span)
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class DiseaseGroupDefinition:
    """
    Disease group definition extracted from policy document

    Evidence required:
    - basis_doc_id: Policy document ID
    - basis_page: Page number where definition found
    - basis_span: Text span (evidence)
    """
    group_id: str                    # e.g., 'SIMILAR_CANCER_SAMSUNG_V1'
    group_label: str                 # e.g., '유사암 (삼성)'
    insurer: str                     # e.g., 'SAMSUNG'
    version_tag: str                 # e.g., 'V1'
    basis_doc_id: str                # Evidence: document ID
    basis_page: int                  # Evidence: page number
    basis_span: str                  # Evidence: text span
    mentioned_codes: List[str]       # KCD codes mentioned (for reference, not inserted)


@dataclass
class CoverageScopeDefinition:
    """
    Coverage disease scope definition extracted from policy

    Links to disease_code_group (not raw codes)
    Evidence required
    """
    coverage_name: str               # e.g., '일반암진단비'
    include_group_label: str         # e.g., '일반암'
    exclude_group_label: Optional[str]  # e.g., '유사암'
    source_doc_id: str               # Evidence: document ID
    source_page: int                 # Evidence: page number
    span_text: str                   # Evidence: text span
    extraction_rule_id: str          # Rule ID for reproducibility


class BasePolicyParser(ABC):
    """
    Abstract base class for insurer-specific policy parsers

    Constitutional requirements:
    - Deterministic extraction only (regex/rules)
    - NO LLM/inference
    - Evidence required (basis_doc_id, basis_page, basis_span)
    - Must implement all abstract methods
    """

    @abstractmethod
    def extract_disease_group_definition(
        self,
        policy_text: str,
        group_concept: str,  # e.g., "유사암", "소액암"
        document_id: str,
        page_number: int
    ) -> Optional[DiseaseGroupDefinition]:
        """
        Extract disease group definition from policy document

        Constitutional guarantee:
        - Deterministic regex/rules only
        - Evidence required (basis_span must not be empty)
        - NO code generation (KCD-7 codes must come from master data)

        Args:
            policy_text: Policy document text content
            group_concept: Disease concept to extract (e.g., '유사암')
            document_id: Policy document ID for evidence
            page_number: Page number for evidence

        Returns:
            DiseaseGroupDefinition with evidence, or None if not found

        Raises:
            ValueError: If evidence is missing
        """
        pass

    @abstractmethod
    def extract_coverage_disease_scope(
        self,
        policy_text: str,
        coverage_name: str,
        document_id: str,
        page_number: int
    ) -> Optional[CoverageScopeDefinition]:
        """
        Extract disease scope definition for specific coverage from policy

        Constitutional guarantee:
        - Links to disease_code_group (not raw codes)
        - Evidence required (span_text)

        Args:
            policy_text: Policy document text
            coverage_name: Coverage name to find scope for
            document_id: Policy document ID
            page_number: Page number

        Returns:
            CoverageScopeDefinition with evidence, or None if not found

        Raises:
            ValueError: If evidence is missing
        """
        pass

    @property
    @abstractmethod
    def insurer_code(self) -> str:
        """
        Return insurer code

        Returns:
            Insurer code (e.g., 'SAMSUNG', 'MERITZ', 'DB')
        """
        pass

    @property
    @abstractmethod
    def supported_concepts(self) -> List[str]:
        """
        Return list of supported disease concepts

        Returns:
            List of supported concepts (e.g., ['유사암', '소액암'])
        """
        pass

    @property
    def implementation_status(self) -> str:
        """
        Return implementation status

        Override in subclass if parser is stub/partial

        Returns:
            'FULL' | 'PARTIAL' | 'STUB'
        """
        return 'FULL'
