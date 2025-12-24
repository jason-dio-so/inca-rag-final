"""
Meritz Policy Parser (STEP 8)

Partial implementation for multi-insurer testing

Constitutional principles:
- Deterministic extraction only (regex + rules)
- NO LLM/inference/similarity
- Evidence required (basis_doc_id, basis_page, basis_span)
"""
from typing import Optional, List
import re
from ..base_parser import (
    BasePolicyParser,
    DiseaseGroupDefinition,
    CoverageScopeDefinition
)


class MeritzPolicyParser(BasePolicyParser):
    """
    Meritz-specific policy parser

    Implementation status: PARTIAL
    Supported concepts: 유사암 (simplified pattern)

    NOTE: This is a partial implementation for STEP 8 multi-insurer testing.
    Full implementation would require actual Meritz policy document patterns.
    """

    @property
    def insurer_code(self) -> str:
        return 'MERITZ'

    @property
    def supported_concepts(self) -> List[str]:
        return ['유사암']

    @property
    def implementation_status(self) -> str:
        return 'PARTIAL'

    def extract_disease_group_definition(
        self,
        policy_text: str,
        group_concept: str,
        document_id: str,
        page_number: int
    ) -> Optional[DiseaseGroupDefinition]:
        """
        Extract disease group definition from Meritz policy

        Currently supports:
        - 유사암 (Similar Cancer) - simplified pattern

        Constitutional guarantee:
        - Deterministic regex extraction only
        - Evidence required (basis_span must not be empty)
        - NO code generation
        """
        if group_concept == '유사암':
            return self._extract_similar_cancer(policy_text, document_id, page_number)
        else:
            # Not implemented for other concepts
            return None

    def _extract_similar_cancer(
        self,
        policy_text: str,
        document_id: str,
        page_number: int
    ) -> Optional[DiseaseGroupDefinition]:
        """
        Parse Meritz 유사암 (Similar Cancer) definition from policy text

        Simplified pattern for STEP 8 multi-insurer testing
        Real implementation would use actual Meritz policy document patterns
        """
        # Simplified pattern for Meritz
        # Assumes similar structure to Samsung but may have variations
        patterns = [
            r'유사암.*?정의.*?[:：]\s*([^。\.]+)',
            r'갑상선암.*?C73',  # Simplified pattern
        ]

        for pattern in patterns:
            match = re.search(pattern, policy_text, re.DOTALL)
            if match:
                span_text = match.group(0)

                # Extract mentioned codes (if any)
                code_pattern = r'C\d{2,3}'
                mentioned_codes = re.findall(code_pattern, span_text)

                return DiseaseGroupDefinition(
                    group_id='SIMILAR_CANCER_MERITZ_V1',
                    group_label='유사암 (메리츠)',
                    insurer='MERITZ',
                    version_tag='V1',
                    basis_doc_id=document_id,
                    basis_page=page_number,
                    basis_span=span_text.strip()[:500],
                    mentioned_codes=mentioned_codes
                )

        return None

    def extract_coverage_disease_scope(
        self,
        policy_text: str,
        coverage_name: str,
        document_id: str,
        page_number: int
    ) -> Optional[CoverageScopeDefinition]:
        """
        Extract disease scope definition for specific coverage from Meritz policy

        Simplified implementation for STEP 8 multi-insurer testing

        Constitutional guarantee:
        - Links to disease_code_group (not raw codes)
        - Evidence required (span_text)
        """
        # Simplified pattern for Meritz
        # Assumes similar exclusion clause structure
        pattern = rf'{re.escape(coverage_name)}.*?(유사암.*?제외|제외.*?유사암)'

        match = re.search(pattern, policy_text, re.DOTALL)
        if match:
            span_text = match.group(0)

            return CoverageScopeDefinition(
                coverage_name=coverage_name,
                include_group_label='일반암',
                exclude_group_label='유사암',
                source_doc_id=document_id,
                source_page=page_number,
                span_text=span_text.strip()[:500],
                extraction_rule_id='meritz_cancer_scope_v1'
            )

        return None
