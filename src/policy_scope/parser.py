"""
Policy Scope Parser v1 (MVP)

Purpose: Extract disease code group definitions from policy documents (약관)
Constitutional principles:
- Deterministic extraction only (regex + rules)
- NO LLM/inference/similarity
- Evidence required (basis_doc_id, basis_page, basis_span)
- KCD-7 codes from official distribution only (no generation from policy text)

MVP Scope:
- Samsung "유사암" definition extraction only
- Regex-based span extraction from policy PDF text
"""
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re


class PolicyScopeParser:
    """
    Extract disease scope definitions from policy documents (deterministic only)
    """

    def __init__(self):
        self.extracted_groups: List[Dict] = []

    def parse_samsung_similar_cancer(
        self,
        policy_text: str,
        document_id: str,
        page_number: int
    ) -> Optional[Dict]:
        """
        Parse Samsung 유사암 (Similar Cancer) definition from policy text.

        Constitutional guarantee:
        - Deterministic regex extraction only
        - Evidence required (span_text)
        - NO code generation (KCD-7 codes must come from master data)

        Args:
            policy_text: Policy document text content
            document_id: Policy document ID for evidence
            page_number: Page number for evidence

        Returns:
            Dict with group definition + evidence, or None if not found
            {
                'group_id': 'SIMILAR_CANCER_SAMSUNG_V1',
                'group_label': '유사암 (삼성)',
                'insurer': 'SAMSUNG',
                'version_tag': 'V1',
                'basis_doc_id': document_id,
                'basis_page': page_number,
                'basis_span': '...',  # Evidence text
                'member_codes': ['C73', 'C44']  # Example - must come from KCD-7 master
            }
        """
        # Regex pattern for 유사암 definition (example pattern)
        # Real implementation would use actual policy document pattern
        patterns = [
            r'유사암.*?다음.*?질병.*?[:：]\s*([^。\.]+)',
            r'유사암.*?정의.*?[:：]\s*([^。\.]+)',
            r'갑상선암.*?C73.*?피부암.*?C44',  # Direct code mention pattern
        ]

        for pattern in patterns:
            match = re.search(pattern, policy_text, re.DOTALL)
            if match:
                span_text = match.group(0)

                # Extract mentioned codes (if any) - must validate against KCD-7 master
                code_pattern = r'C\d{2,3}'
                mentioned_codes = re.findall(code_pattern, span_text)

                return {
                    'group_id': 'SIMILAR_CANCER_SAMSUNG_V1',
                    'group_label': '유사암 (삼성)',
                    'insurer': 'SAMSUNG',
                    'version_tag': 'V1',
                    'basis_doc_id': document_id,
                    'basis_page': page_number,
                    'basis_span': span_text.strip()[:500],  # Limit span length
                    'mentioned_codes': mentioned_codes,  # For reference only, not inserted
                }

        return None

    def extract_disease_scope_for_coverage(
        self,
        policy_text: str,
        coverage_name: str,
        document_id: str,
        page_number: int
    ) -> Optional[Dict]:
        """
        Extract disease scope definition for specific coverage from policy.

        Constitutional guarantee:
        - Links to disease_code_group (not raw codes)
        - Evidence required (source_doc_id, span_text)

        Args:
            policy_text: Policy document text
            coverage_name: Coverage name to find scope for
            document_id: Policy document ID
            page_number: Page number

        Returns:
            Dict with scope definition + evidence, or None if not found
            {
                'coverage_name': coverage_name,
                'include_group_label': '일반암',
                'exclude_group_label': '유사암',
                'source_doc_id': document_id,
                'source_page': page_number,
                'span_text': '...',  # Evidence
                'extraction_rule_id': 'samsung_cancer_scope_v1'
            }
        """
        # Example pattern for "유사암 제외" clauses
        # Pattern: "[coverage_name]...(유사암|제자리암|경계성종양)...제외"
        pattern = rf'{re.escape(coverage_name)}.*?(유사암.*?제외|제외.*?유사암)'

        match = re.search(pattern, policy_text, re.DOTALL)
        if match:
            span_text = match.group(0)

            return {
                'coverage_name': coverage_name,
                'include_group_label': '일반암',  # Would be determined by rule
                'exclude_group_label': '유사암',
                'source_doc_id': document_id,
                'source_page': page_number,
                'span_text': span_text.strip()[:500],
                'extraction_rule_id': 'samsung_cancer_scope_v1'
            }

        return None
