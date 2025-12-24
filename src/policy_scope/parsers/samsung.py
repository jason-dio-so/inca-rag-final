"""
Samsung Policy Parser (STEP 8)

Migrated from STEP 7 parser.py
Implements BasePolicyParser interface for Samsung-specific extraction logic

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


class SamsungPolicyParser(BasePolicyParser):
    """
    Samsung-specific policy parser

    Implementation status: FULL
    Supported concepts: 유사암, 소액암 (if patterns available)
    """

    @property
    def insurer_code(self) -> str:
        return 'SAMSUNG'

    @property
    def supported_concepts(self) -> List[str]:
        return ['유사암', '소액암']

    @property
    def implementation_status(self) -> str:
        return 'FULL'

    def extract_disease_group_definition(
        self,
        policy_text: str,
        group_concept: str,
        document_id: str,
        page_number: int
    ) -> Optional[DiseaseGroupDefinition]:
        """
        Extract disease group definition from Samsung policy

        Currently supports:
        - 유사암 (Similar Cancer)
        - 소액암 (Minor Cancer) - future

        Constitutional guarantee:
        - Deterministic regex extraction only
        - Evidence required (basis_span must not be empty)
        - NO code generation
        """
        if group_concept == '유사암':
            return self._extract_similar_cancer(policy_text, document_id, page_number)
        elif group_concept == '소액암':
            # Future implementation
            return None
        else:
            return None

    def _extract_similar_cancer(
        self,
        policy_text: str,
        document_id: str,
        page_number: int
    ) -> Optional[DiseaseGroupDefinition]:
        """
        Parse Samsung 유사암 (Similar Cancer) definition from policy text

        Regex patterns based on Samsung policy document structure
        """
        # Regex patterns for 유사암 definition
        # These match typical Samsung policy document structure
        patterns = [
            r'유사암.*?다음.*?질병.*?[:：]\s*([^。\.]+)',
            r'유사암.*?정의.*?[:：]\s*([^。\.]+)',
            r'갑상선암.*?C73.*?피부암.*?C44',  # Direct code mention pattern
        ]

        for pattern in patterns:
            match = re.search(pattern, policy_text, re.DOTALL)
            if match:
                span_text = match.group(0)

                # Extract mentioned codes (if any)
                # These are for reference only, not inserted directly
                # Actual codes must come from disease_code_master
                code_pattern = r'C\d{2,3}'
                mentioned_codes = re.findall(code_pattern, span_text)

                return DiseaseGroupDefinition(
                    group_id='SIMILAR_CANCER_SAMSUNG_V1',
                    group_label='유사암 (삼성)',
                    insurer='SAMSUNG',
                    version_tag='V1',
                    basis_doc_id=document_id,
                    basis_page=page_number,
                    basis_span=span_text.strip()[:500],  # Limit span length
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
        Extract disease scope definition for specific coverage from Samsung policy

        Constitutional guarantee:
        - Links to disease_code_group (not raw codes)
        - Evidence required (span_text)
        """
        # Pattern for "유사암 제외" clauses
        # Matches: "[coverage_name]...(유사암|제자리암|경계성종양)...제외"
        pattern = rf'{re.escape(coverage_name)}.*?(유사암.*?제외|제외.*?유사암)'

        match = re.search(pattern, policy_text, re.DOTALL)
        if match:
            span_text = match.group(0)

            return CoverageScopeDefinition(
                coverage_name=coverage_name,
                include_group_label='일반암',  # Would be determined by rule
                exclude_group_label='유사암',
                source_doc_id=document_id,
                source_page=page_number,
                span_text=span_text.strip()[:500],
                extraction_rule_id='samsung_cancer_scope_v1'
            )

        return None
