"""
Explainable Comparison Reasons (STEP 8)

Purpose: Generate human-readable explanations for comparison states

Constitutional prohibitions:
- NO value judgments (best/worst/better)
- NO recommendations
- Only factual differences with evidence
"""
from typing import List, Optional
from dataclasses import dataclass
from .overlap import GroupOverlapState, InsurerDiseaseScope


@dataclass
class InsurerGroupDetail:
    """
    Evidence for insurer-specific disease group

    Constitutional requirement:
    - Includes evidence (basis_doc_id, basis_page)
    - NO value judgments
    """
    insurer: str
    group_id: Optional[str]
    group_label: Optional[str]
    basis_doc_id: Optional[str]
    basis_page: Optional[int]
    member_count: Optional[int]  # Number of KCD codes in group


@dataclass
class ComparisonReason:
    """
    Explainable reason for comparison state

    Constitutional requirement:
    - NO value judgments (best/worst)
    - NO recommendations
    - Only factual differences with evidence
    """
    comparison_state: str  # comparable, comparable_with_gaps, non_comparable
    reason_code: str       # disease_scope_identical, disease_scope_multi_insurer_conflict, etc.
    explanation: str       # Human-readable explanation (Korean)
    details: List[InsurerGroupDetail]


def generate_comparison_reason(
    overlap_state: GroupOverlapState,
    scopes: List[InsurerDiseaseScope],
    group_details: Optional[List[InsurerGroupDetail]] = None
) -> ComparisonReason:
    """
    Generate human-readable comparison reason from overlap state

    Constitutional guarantee:
    - NO value judgments or recommendations
    - Only factual differences
    - Evidence included where available

    Args:
        overlap_state: Group overlap state
        scopes: List of insurer disease scopes
        group_details: Optional group details with evidence

    Returns:
        ComparisonReason with explanation and evidence
    """
    # Map overlap state to comparison state
    if overlap_state == GroupOverlapState.FULL_MATCH:
        comparison_state = "comparable"
        reason_code = "disease_scope_identical"
    elif overlap_state == GroupOverlapState.PARTIAL_OVERLAP:
        comparison_state = "comparable_with_gaps"
        reason_code = "disease_scope_partial_overlap"
    elif overlap_state == GroupOverlapState.NO_OVERLAP:
        comparison_state = "non_comparable"
        reason_code = "disease_scope_multi_insurer_conflict"
    else:  # UNKNOWN
        comparison_state = "comparable_with_gaps"
        reason_code = "disease_scope_policy_required"

    # Generate explanation
    explanation = _generate_explanation(overlap_state, scopes)

    # Use provided group_details or create minimal ones
    if group_details is None:
        group_details = _create_minimal_details(scopes)

    return ComparisonReason(
        comparison_state=comparison_state,
        reason_code=reason_code,
        explanation=explanation,
        details=group_details
    )


def _generate_explanation(
    overlap_state: GroupOverlapState,
    scopes: List[InsurerDiseaseScope]
) -> str:
    """
    Generate Korean explanation for overlap state

    Constitutional guarantee:
    - NO prohibited phrases (가장 넓은, 가장 유리함, 추천, 더 나은)
    - Only factual description
    """
    insurer_names = [_get_insurer_korean_name(s.insurer) for s in scopes]
    insurers_text = ", ".join(insurer_names)

    if overlap_state == GroupOverlapState.FULL_MATCH:
        return f"{insurers_text} 모두 동일한 유사암 정의를 사용합니다."

    elif overlap_state == GroupOverlapState.PARTIAL_OVERLAP:
        return (
            f"{insurers_text}의 유사암 정의에 일부 교집합이 있습니다. "
            f"약관 확인이 필요합니다."
        )

    elif overlap_state == GroupOverlapState.NO_OVERLAP:
        return (
            f"{insurers_text}의 유사암 정의가 상호 교집합을 가지지 않아 "
            f"비교가 불가능합니다."
        )

    else:  # UNKNOWN
        # Find which insurers have NULL disease_scope_norm
        unknown_insurers = []
        for scope in scopes:
            if scope.include_group_id is None:
                unknown_insurers.append(_get_insurer_korean_name(scope.insurer))

        if len(unknown_insurers) > 0:
            unknown_text = ", ".join(unknown_insurers)
            return (
                f"{unknown_text}의 유사암 정의가 약관에서 추출되지 않았습니다. "
                f"약관 확인이 필요합니다."
            )
        else:
            return f"{insurers_text}의 유사암 정의 확인이 필요합니다."


def _get_insurer_korean_name(insurer_code: str) -> str:
    """
    Get Korean name for insurer code

    Args:
        insurer_code: Insurer code (e.g., 'SAMSUNG')

    Returns:
        Korean name (e.g., '삼성')
    """
    mapping = {
        'SAMSUNG': '삼성',
        'MERITZ': '메리츠',
        'DB': 'DB',
        'LOTTE': '롯데',
        'KB': 'KB',
    }
    return mapping.get(insurer_code, insurer_code)


def _create_minimal_details(
    scopes: List[InsurerDiseaseScope]
) -> List[InsurerGroupDetail]:
    """
    Create minimal group details from scopes (without evidence)

    Used when evidence not available
    """
    details = []

    for scope in scopes:
        detail = InsurerGroupDetail(
            insurer=scope.insurer,
            group_id=scope.include_group_id,
            group_label=None,  # Not available
            basis_doc_id=None,  # Not available
            basis_page=None,    # Not available
            member_count=len(scope.include_codes) if scope.include_codes else None
        )
        details.append(detail)

    return details


def validate_explanation_no_prohibited_phrases(explanation: str) -> bool:
    """
    Validate that explanation contains no prohibited phrases

    Constitutional requirement:
    - NO value judgments
    - NO recommendations

    Args:
        explanation: Explanation text to validate

    Returns:
        True if valid, False if contains prohibited phrases
    """
    prohibited_phrases = [
        '가장 넓은',
        '가장 유리',
        '추천',
        '더 나은',
        '더 좋은',
        '최고',
        '최선',
        '우수',
    ]

    for phrase in prohibited_phrases:
        if phrase in explanation:
            return False

    return True
