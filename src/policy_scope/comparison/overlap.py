"""
Multi-Party Disease Group Overlap Detection (STEP 8)

Purpose: Determine overlap state for 3+ insurers' disease group definitions

Constitutional principles:
- Pairwise comparison → unified state
- Deterministic logic (no probabilistic inference)
- Return single comparison state (not per-insurer states)
"""
from enum import Enum
from typing import List, Set, Optional, Dict
from dataclasses import dataclass


class GroupOverlapState(Enum):
    """
    Group overlap states for multi-party comparison

    Used to determine if disease scopes from 3+ insurers are comparable
    """
    FULL_MATCH = "full_match"              # All insurers have identical groups
    PARTIAL_OVERLAP = "partial_overlap"     # Some insurers have intersection
    NO_OVERLAP = "no_overlap"               # No common intersection across all
    UNKNOWN = "unknown"                     # One or more disease_scope_norm is NULL


@dataclass
class InsurerDiseaseScope:
    """
    Disease scope for single insurer

    Used as input to multi-party overlap detection
    """
    insurer: str
    canonical_coverage_code: str
    include_group_id: Optional[str]  # None = disease_scope_norm NULL
    exclude_group_id: Optional[str]
    include_codes: Optional[Set[str]]  # KCD-7 codes in include group
    exclude_codes: Optional[Set[str]]  # KCD-7 codes in exclude group


def detect_pairwise_overlap(
    scope_a: InsurerDiseaseScope,
    scope_b: InsurerDiseaseScope
) -> GroupOverlapState:
    """
    Detect overlap state between two insurers' disease scopes

    Constitutional guarantee:
    - Deterministic logic based on set operations
    - NO probabilistic inference

    Args:
        scope_a: Disease scope for insurer A
        scope_b: Disease scope for insurer B

    Returns:
        GroupOverlapState for this pair
    """
    # UNKNOWN if either scope has NULL disease_scope_norm
    if scope_a.include_group_id is None or scope_b.include_group_id is None:
        return GroupOverlapState.UNKNOWN

    # If both have no codes loaded, treat as UNKNOWN
    if scope_a.include_codes is None or scope_b.include_codes is None:
        return GroupOverlapState.UNKNOWN

    # Compare include/exclude groups
    # FULL_MATCH: Identical include AND exclude groups
    if (scope_a.include_group_id == scope_b.include_group_id and
        scope_a.exclude_group_id == scope_b.exclude_group_id):
        return GroupOverlapState.FULL_MATCH

    # Calculate effective coverage (include - exclude)
    effective_a = scope_a.include_codes - (scope_a.exclude_codes or set())
    effective_b = scope_b.include_codes - (scope_b.exclude_codes or set())

    # Check for intersection
    intersection = effective_a & effective_b

    if len(intersection) == 0:
        return GroupOverlapState.NO_OVERLAP

    # Check if fully identical
    if effective_a == effective_b:
        return GroupOverlapState.FULL_MATCH

    # Has intersection but not identical
    return GroupOverlapState.PARTIAL_OVERLAP


def aggregate_multi_party_overlap(
    scopes: List[InsurerDiseaseScope]
) -> GroupOverlapState:
    """
    Aggregate pairwise overlap results for 3+ insurers into single state

    Constitutional guarantee:
    - Deterministic aggregation logic
    - Returns single unified state (not per-insurer states)

    Algorithm:
    1. Compute pairwise overlap for all pairs
    2. If any pair is UNKNOWN → UNKNOWN
    3. If any pair is NO_OVERLAP → NO_OVERLAP
    4. If all pairs are FULL_MATCH → FULL_MATCH
    5. Otherwise → PARTIAL_OVERLAP

    Args:
        scopes: List of disease scopes (3+ insurers)

    Returns:
        Single GroupOverlapState for all insurers

    Raises:
        ValueError: If fewer than 2 scopes provided
    """
    if len(scopes) < 2:
        raise ValueError(
            f"Multi-party overlap requires at least 2 insurers, got {len(scopes)}"
        )

    # Single insurer pair - direct pairwise comparison
    if len(scopes) == 2:
        return detect_pairwise_overlap(scopes[0], scopes[1])

    # Multi-party (3+) - aggregate pairwise results
    pairwise_states = []

    for i in range(len(scopes)):
        for j in range(i + 1, len(scopes)):
            state = detect_pairwise_overlap(scopes[i], scopes[j])
            pairwise_states.append(state)

    # Aggregation rules
    # 1. Any UNKNOWN → UNKNOWN
    if GroupOverlapState.UNKNOWN in pairwise_states:
        return GroupOverlapState.UNKNOWN

    # 2. Any NO_OVERLAP → NO_OVERLAP
    if GroupOverlapState.NO_OVERLAP in pairwise_states:
        return GroupOverlapState.NO_OVERLAP

    # 3. All FULL_MATCH → FULL_MATCH
    if all(state == GroupOverlapState.FULL_MATCH for state in pairwise_states):
        return GroupOverlapState.FULL_MATCH

    # 4. Otherwise → PARTIAL_OVERLAP
    return GroupOverlapState.PARTIAL_OVERLAP


def load_group_codes_from_db(
    conn,
    group_id: str
) -> Set[str]:
    """
    Load KCD-7 codes for a disease_code_group from database

    Args:
        conn: Database connection
        group_id: Disease code group ID

    Returns:
        Set of KCD-7 codes in this group

    Raises:
        ValueError: If group not found
    """
    sql = """
    SELECT code, code_from, code_to
    FROM disease_code_group_member
    WHERE group_id = %(group_id)s
    """

    codes = set()

    with conn.cursor() as cursor:
        cursor.execute(sql, {'group_id': group_id})
        rows = cursor.fetchall()

        for row in rows:
            code = row[0]
            code_from = row[1]
            code_to = row[2]

            if code:
                # Single code
                codes.add(code)
            elif code_from and code_to:
                # Range - for now, just add both endpoints
                # Future: expand range to all codes
                codes.add(code_from)
                codes.add(code_to)

    return codes
