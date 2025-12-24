"""
Compare Engine with Universe Lock

Purpose: Compare coverage ONLY if in proposal universe
Constitution: Coverage Universe Lock enforcement

Comparison States (v1.1 + out_of_universe):
- comparable
- comparable_with_gaps
- non_comparable
- unmapped
- out_of_universe (NEW)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ComparisonState(Enum):
    """Comparison result states."""
    COMPARABLE = "comparable"
    COMPARABLE_WITH_GAPS = "comparable_with_gaps"
    NON_COMPARABLE = "non_comparable"
    UNMAPPED = "unmapped"
    OUT_OF_UNIVERSE = "out_of_universe"


@dataclass
class ComparisonResult:
    """
    Comparison result between two coverages.

    Slot Schema v1.1 + Universe Lock enforcement
    """
    insurer_a: str
    insurer_b: str
    coverage_query: str
    comparison_result: ComparisonState

    canonical_coverage_code: Optional[str] = None
    comparable_slots: List[str] = None
    gap_slots: List[str] = None
    gap_details: Optional[Dict] = None
    policy_verification_required: bool = False

    # Universe Lock specific
    universe_status_a: Optional[str] = None  # "in_universe" | "out_of_universe"
    universe_status_b: Optional[str] = None

    # Evidence
    evidence_a: Optional[Dict] = None
    evidence_b: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dict for API response."""
        return {
            'insurer_a': self.insurer_a,
            'insurer_b': self.insurer_b,
            'coverage_query': self.coverage_query,
            'comparison_result': self.comparison_result.value,
            'canonical_coverage_code': self.canonical_coverage_code,
            'comparable_slots': self.comparable_slots or [],
            'gap_slots': self.gap_slots or [],
            'gap_details': self.gap_details or {},
            'policy_verification_required': self.policy_verification_required,
            'universe_status': {
                'insurer_a': self.universe_status_a,
                'insurer_b': self.universe_status_b,
            },
            'evidence': {
                'insurer_a': self.evidence_a,
                'insurer_b': self.evidence_b,
            }
        }


class CompareEngine:
    """
    Coverage comparison engine with Universe Lock.

    Principles:
    1. Check universe existence FIRST
    2. If not in universe → out_of_universe (no estimation)
    3. Compare only MAPPED coverages
    4. Use Slot Schema v1.1.1 comparison logic
    """

    # Slots that must match for "comparable"
    CRITICAL_SLOTS = [
        'canonical_coverage_code',
        'event_type',
    ]

    # Slots that create gaps if null
    GAP_SLOTS = [
        'disease_scope_norm',
        'reduction_periods',
        'hospitalization_exclusions',
    ]

    def __init__(self, db_connection):
        """
        Initialize compare engine.

        Args:
            db_connection: Database connection for universe/slot queries
        """
        self.db = db_connection

    def compare(
        self,
        insurer_a: str,
        insurer_b: str,
        coverage_query: str
    ) -> ComparisonResult:
        """
        Compare coverage between two insurers.

        Args:
            insurer_a: First insurer name
            insurer_b: Second insurer name
            coverage_query: User's coverage query (e.g., "암진단비")

        Returns:
            ComparisonResult with state and details
        """

        # Step 1: Universe Lock - check existence
        coverage_a = self._get_from_universe(insurer_a, coverage_query)
        coverage_b = self._get_from_universe(insurer_b, coverage_query)

        # Check universe status
        if coverage_a is None:
            return ComparisonResult(
                insurer_a=insurer_a,
                insurer_b=insurer_b,
                coverage_query=coverage_query,
                comparison_result=ComparisonState.OUT_OF_UNIVERSE,
                universe_status_a="out_of_universe",
                universe_status_b="in_universe" if coverage_b else "out_of_universe",
            )

        if coverage_b is None:
            return ComparisonResult(
                insurer_a=insurer_a,
                insurer_b=insurer_b,
                coverage_query=coverage_query,
                comparison_result=ComparisonState.OUT_OF_UNIVERSE,
                universe_status_a="in_universe",
                universe_status_b="out_of_universe",
            )

        # Step 2: Check mapping status
        if coverage_a['mapping_status'] != 'MAPPED':
            return ComparisonResult(
                insurer_a=insurer_a,
                insurer_b=insurer_b,
                coverage_query=coverage_query,
                comparison_result=ComparisonState.UNMAPPED,
                universe_status_a="in_universe",
                universe_status_b="in_universe",
                gap_details={'unmapped_insurer': insurer_a},
            )

        if coverage_b['mapping_status'] != 'MAPPED':
            return ComparisonResult(
                insurer_a=insurer_a,
                insurer_b=insurer_b,
                coverage_query=coverage_query,
                comparison_result=ComparisonState.UNMAPPED,
                universe_status_a="in_universe",
                universe_status_b="in_universe",
                gap_details={'unmapped_insurer': insurer_b},
            )

        # Step 3: Check canonical code match
        if coverage_a['canonical_coverage_code'] != coverage_b['canonical_coverage_code']:
            return ComparisonResult(
                insurer_a=insurer_a,
                insurer_b=insurer_b,
                coverage_query=coverage_query,
                comparison_result=ComparisonState.NON_COMPARABLE,
                universe_status_a="in_universe",
                universe_status_b="in_universe",
                gap_details={
                    'reason': 'Different canonical_coverage_code',
                    'code_a': coverage_a['canonical_coverage_code'],
                    'code_b': coverage_b['canonical_coverage_code'],
                },
            )

        # Step 4: Slot-level comparison
        return self._compare_slots(coverage_a, coverage_b)

    def _get_from_universe(
        self,
        insurer: str,
        coverage_query: str
    ) -> Optional[Dict]:
        """
        Get coverage from universe + mapping + slots.

        Uses v_proposal_coverage_full view.

        Returns:
            Dict with all pipeline data or None if not in universe
        """
        # Normalize query for matching
        normalized_query = self._normalize_query(coverage_query)

        query = """
        SELECT
            universe_id,
            insurer,
            insurer_coverage_name,
            normalized_name,
            canonical_coverage_code,
            mapping_status,
            event_type,
            disease_scope_raw,
            disease_scope_norm,
            waiting_period_days,
            reduction_periods,
            payout_limit,
            treatment_method,
            renewal_flag,
            renewal_period_years,
            source_confidence,
            source_page,
            universe_span
        FROM v_proposal_coverage_full
        WHERE insurer = %s
          AND normalized_name = %s
        LIMIT 1;
        """

        with self.db.cursor() as cur:
            cur.execute(query, (insurer, normalized_query))
            row = cur.fetchone()

        if row is None:
            return None

        return dict(row)

    def _normalize_query(self, query: str) -> str:
        """Normalize user query to match normalized_name."""
        import re
        normalized = query.strip()
        normalized = re.sub(r'\s+', '', normalized)
        normalized = re.sub(r'\(\s+', '(', normalized)
        normalized = re.sub(r'\s+\)', ')', normalized)
        return normalized

    def _compare_slots(
        self,
        coverage_a: Dict,
        coverage_b: Dict
    ) -> ComparisonResult:
        """
        Compare slots between two MAPPED coverages.

        Returns:
            ComparisonResult with comparable/comparable_with_gaps state
        """
        canonical_code = coverage_a['canonical_coverage_code']

        comparable_slots = []
        gap_slots = []

        # Compare critical slots
        for slot in self.CRITICAL_SLOTS:
            if coverage_a.get(slot) == coverage_b.get(slot):
                comparable_slots.append(slot)

        # Compare other slots
        all_slots = [
            'waiting_period_days',
            'reduction_periods',
            'payout_limit',
            'renewal_flag',
            'treatment_method',
        ]

        for slot in all_slots:
            val_a = coverage_a.get(slot)
            val_b = coverage_b.get(slot)

            if val_a == val_b and val_a is not None:
                comparable_slots.append(slot)
            elif val_a is None or val_b is None:
                gap_slots.append(slot)

        # Check disease_scope_norm
        if coverage_a.get('disease_scope_norm') is None or \
           coverage_b.get('disease_scope_norm') is None:
            gap_slots.append('disease_scope_norm')

        # Determine state
        if len(gap_slots) == 0:
            state = ComparisonState.COMPARABLE
            policy_required = False
        else:
            state = ComparisonState.COMPARABLE_WITH_GAPS
            policy_required = True

        return ComparisonResult(
            insurer_a=coverage_a['insurer'],
            insurer_b=coverage_b['insurer'],
            coverage_query=coverage_a['insurer_coverage_name'],
            comparison_result=state,
            canonical_coverage_code=canonical_code,
            comparable_slots=comparable_slots,
            gap_slots=gap_slots,
            policy_verification_required=policy_required,
            universe_status_a="in_universe",
            universe_status_b="in_universe",
            evidence_a={
                'page': coverage_a['source_page'],
                'span': coverage_a['universe_span'],
            },
            evidence_b={
                'page': coverage_b['source_page'],
                'span': coverage_b['universe_span'],
            }
        )
