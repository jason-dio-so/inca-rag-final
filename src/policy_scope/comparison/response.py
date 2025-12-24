"""
STEP 9: Comparison Response Schema (구조화 응답 고정)

Purpose: Generate structured comparison response for 3+ insurers

Constitutional Requirements:
- NO free-form text (structured response only)
- NO value judgments or recommendations
- NO prohibited phrases
- Evidence included at every level
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from .explainer import ComparisonReason, validate_explanation_no_prohibited_phrases


@dataclass
class InsurerEvidence:
    """
    Evidence for insurer's disease scope definition

    Required: basis_doc_id, basis_page, basis_span
    """
    basis_doc_id: str
    basis_page: int
    basis_span: str


@dataclass
class InsurerDiseaseScopeResponse:
    """
    Insurer-specific disease scope in comparison response

    Constitutional guarantee:
    - disease_scope_norm is group references (not raw code arrays)
    - Evidence included (from policy document)
    """
    insurer: str
    disease_scope_norm: Optional[Dict[str, str]]  # {"include_group_id": "...", "exclude_group_id": "..."}
    evidence: Optional[InsurerEvidence]


@dataclass
class ComparisonResponse:
    """
    Structured comparison response for 3+ insurers

    Constitutional requirements:
    - comparison_state: Single unified state (not per-insurer states)
    - insurers: All insurers included (even if disease_scope_norm is NULL)
    - comparison_reason: Factual explanation only (NO value judgments)
    - prohibited_phrases_check: Must be PASS
    """
    comparison_state: str  # comparable | comparable_with_gaps | non_comparable
    coverage_code: str  # Canonical coverage code
    coverage_name: str  # Korean name
    insurers: List[InsurerDiseaseScopeResponse]
    comparison_reason: ComparisonReason
    prohibited_phrases_check: str  # PASS | FAIL

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "comparison_state": self.comparison_state,
            "coverage_code": self.coverage_code,
            "coverage_name": self.coverage_name,
            "insurers": [
                {
                    "insurer": ins.insurer,
                    "disease_scope_norm": ins.disease_scope_norm,
                    "evidence": asdict(ins.evidence) if ins.evidence else None
                }
                for ins in self.insurers
            ],
            "comparison_reason": {
                "reason_code": self.comparison_reason.reason_code,
                "summary_ko": self.comparison_reason.explanation,
                "evidence_refs": [
                    {
                        "insurer": detail.insurer,
                        "doc_id": detail.basis_doc_id,
                        "page": detail.basis_page
                    }
                    for detail in self.comparison_reason.details
                    if detail.basis_doc_id is not None
                ]
            },
            "prohibited_phrases_check": self.prohibited_phrases_check
        }


def generate_comparison_response(
    coverage_code: str,
    coverage_name: str,
    insurer_scopes: List[InsurerDiseaseScopeResponse],
    comparison_reason: ComparisonReason
) -> ComparisonResponse:
    """
    Generate structured comparison response

    Constitutional guarantee:
    - Validates prohibited phrases
    - Ensures structured format
    - Includes evidence at all levels

    Args:
        coverage_code: Canonical coverage code
        coverage_name: Coverage name (Korean)
        insurer_scopes: List of insurer disease scopes
        comparison_reason: Comparison reason with explanation

    Returns:
        ComparisonResponse with prohibited_phrases_check

    Raises:
        ValueError: If prohibited phrases detected
    """
    # Validate prohibited phrases
    if not validate_explanation_no_prohibited_phrases(comparison_reason.explanation):
        prohibited_check = "FAIL"
        raise ValueError(
            f"Prohibited phrases detected in explanation: {comparison_reason.explanation}"
        )
    else:
        prohibited_check = "PASS"

    return ComparisonResponse(
        comparison_state=comparison_reason.comparison_state,
        coverage_code=coverage_code,
        coverage_name=coverage_name,
        insurers=insurer_scopes,
        comparison_reason=comparison_reason,
        prohibited_phrases_check=prohibited_check
    )


def validate_comparison_response(response: ComparisonResponse) -> bool:
    """
    Validate comparison response against constitutional requirements

    Requirements:
    1. Single comparison_state (not per-insurer states)
    2. All insurers included (even if disease_scope_norm is NULL)
    3. NO prohibited phrases
    4. Evidence included where available

    Args:
        response: ComparisonResponse to validate

    Returns:
        True if valid, False otherwise
    """
    # 1. Check single comparison_state
    if response.comparison_state not in ['comparable', 'comparable_with_gaps', 'non_comparable']:
        return False

    # 2. Check all insurers included
    if len(response.insurers) < 3:
        return False

    # 3. Check prohibited phrases
    if response.prohibited_phrases_check != "PASS":
        return False

    # 4. Check evidence included (where disease_scope_norm exists)
    for insurer_scope in response.insurers:
        if insurer_scope.disease_scope_norm is not None:
            if insurer_scope.evidence is None:
                return False  # Evidence required when disease_scope_norm exists

    return True
