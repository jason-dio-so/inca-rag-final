"""
Slot Extractor

Purpose: Extract Slot Schema v1.1.1 fields from proposal text
Method: Deterministic regex/rule-based only (no LLM)

Constitution Article II: Deterministic Compiler Principle
"""

import re
from typing import Dict, Optional, List


class SlotExtractor:
    """
    Extract slot values from proposal coverage text.

    Slot Schema v1.1.1 fields extractable from proposals:
    - event_type (inferred from coverage name)
    - waiting_period_days (from qualifiers)
    - reduction_periods (from qualifiers like "1년50%")
    - renewal_flag / renewal_period_years (from "[갱신형]")
    - payout_limit (from qualifiers like "최초1회한")
    - treatment_method (from coverage name)
    - disease_scope_raw (from parentheses)

    Fields NOT extracted (require policy docs):
    - disease_scope_norm (NULL - requires 약관)
    - hospitalization_exclusions (usually NULL from proposal)
    """

    # Waiting period patterns
    WAITING_PERIOD_PATTERNS = [
        re.compile(r'보장개시일\s*(\d+)일\s*(?:후|경과)'),
        re.compile(r'(\d+)일\s*(?:후|경과)'),
    ]

    # Reduction period patterns
    REDUCTION_PATTERNS = [
        re.compile(r'(\d+)년\s*(\d+)%'),
        re.compile(r'(\d+)개월\s*(\d+)%'),
    ]

    # Payout limit patterns
    PAYOUT_LIMIT_PATTERNS = {
        'once_lifetime': re.compile(r'최초\s*1회\s*한'),
        'once_per_year': re.compile(r'1년간\s*1회'),
        'unlimited': re.compile(r'횟수\s*무제한'),
    }

    # Renewal patterns
    RENEWAL_PATTERN = re.compile(r'\[갱신형\]')
    RENEWAL_PERIOD_PATTERN = re.compile(r'(\d+)년\s*갱신')

    # Treatment method keywords
    TREATMENT_METHODS = {
        '로봇수술': 'robotic_surgery',
        '다빈치': 'robotic_surgery',
        '내시경': 'endoscopic',
        '항암': 'chemotherapy',
        '방사선': 'radiation',
        '표적항암': 'targeted_therapy',
    }

    def extract(
        self,
        coverage_name: str,
        span_text: str,
        amount_value: Optional[int],
        page: int,
        proposal_id: str
    ) -> Dict:
        """
        Extract slots from coverage text.

        Args:
            coverage_name: Original coverage name
            span_text: Full span text from proposal
            amount_value: Parsed amount (원)
            page: Page number
            proposal_id: Proposal document ID

        Returns:
            Slot dict conforming to Slot Schema v1.1.1
        """

        # Combine name and span for pattern matching
        full_text = f"{coverage_name} {span_text}"

        return {
            'event_type': self._extract_event_type(coverage_name),
            'disease_scope_raw': self._extract_disease_scope_raw(coverage_name),
            'disease_scope_norm': None,  # NULL - requires policy doc
            'waiting_period_days': self._extract_waiting_period(full_text),
            'coverage_start_rule': self._extract_start_rule(full_text),
            'reduction_periods': self._extract_reduction_periods(full_text),
            'payout_limit': self._extract_payout_limit(full_text),
            'treatment_method': self._extract_treatment_method(coverage_name),
            'hospitalization_exclusions': None,  # NULL - requires policy doc
            'renewal_flag': self._extract_renewal_flag(full_text),
            'renewal_period_years': self._extract_renewal_period(full_text),
            'renewal_max_age': None,  # NULL - not in proposal
            'source_confidence': self._determine_confidence(coverage_name, full_text),
            'qualification_suffix': self._extract_qualification_suffix(coverage_name),
            'evidence': {
                'document_id': proposal_id,
                'page': page,
                'span': span_text,
                'extraction_rule': 'slot_extractor_v1_1_1',
            }
        }

    def _extract_event_type(self, name: str) -> str:
        """Infer event_type from coverage name."""
        if '진단비' in name or '진단금' in name:
            return 'diagnosis'
        elif '수술비' in name or '수술금' in name:
            return 'surgery'
        elif '입원비' in name or '입원일당' in name:
            return 'hospitalization'
        elif '치료비' in name or '치료금' in name:
            return 'treatment'
        elif '사망' in name:
            return 'death'
        else:
            return 'unknown'

    def _extract_disease_scope_raw(self, name: str) -> Optional[str]:
        """
        Extract disease_scope_raw from parentheses.

        Examples:
            "암 진단비(유사암 제외)" -> "유사암 제외"
            "유사암 진단비(5종)" -> "5종"
        """
        match = re.search(r'\(([^)]+)\)', name)
        if match:
            content = match.group(1)
            # Filter out non-scope qualifiers
            if any(kw in content for kw in ['갱신', '만기', '1년', '회', '%']):
                return None
            return content
        return None

    def _extract_waiting_period(self, text: str) -> Optional[int]:
        """
        Extract waiting_period_days.

        Returns:
            int (days), 0 (explicit none), or None (unknown)
        """
        for pattern in self.WAITING_PERIOD_PATTERNS:
            match = pattern.search(text)
            if match:
                return int(match.group(1))

        # Check for explicit "보장개시일부터" (no waiting)
        if re.search(r'보장개시일\s*(?:부터|즉시)', text):
            return 0

        return None  # unknown

    def _extract_start_rule(self, text: str) -> Optional[str]:
        """Extract coverage_start_rule text."""
        patterns = [
            r'보장개시일\s*\d+일\s*후',
            r'보장개시일부터',
            r'계약일\s*익일',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return None

    def _extract_reduction_periods(self, text: str) -> Optional[List[Dict]]:
        """
        Extract reduction_periods.

        Returns:
            List of {from_days, to_days, rate, condition} or
            [] (explicit none) or
            None (unknown)
        """
        periods = []

        for pattern in self.REDUCTION_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                period_value = int(match.group(1))
                rate_pct = int(match.group(2))

                # Convert to days
                if '년' in match.group(0):
                    to_days = period_value * 365
                elif '개월' in match.group(0):
                    to_days = period_value * 30
                else:
                    to_days = period_value

                periods.append({
                    'from_days': 0,
                    'to_days': to_days,
                    'rate': rate_pct / 100,
                    'condition': match.group(0),
                })

        # Check for explicit "감액 없음"
        if re.search(r'감액\s*없음', text):
            return []  # explicit none

        if periods:
            return periods

        return None  # unknown

    def _extract_payout_limit(self, text: str) -> Optional[Dict]:
        """
        Extract payout_limit (v1.1.1 consolidated format).

        Returns:
            {type, count, period} or None (unknown)
        """
        for limit_type, pattern in self.PAYOUT_LIMIT_PATTERNS.items():
            if pattern.search(text):
                if limit_type == 'once_lifetime':
                    return {
                        'type': 'once',
                        'count': 1,
                        'period': 'lifetime',
                    }
                elif limit_type == 'once_per_year':
                    return {
                        'type': 'once',
                        'count': 1,
                        'period': 'per_year',
                    }
                elif limit_type == 'unlimited':
                    return {
                        'type': 'unlimited',
                        'count': None,
                        'period': None,
                    }

        # Check for numeric limits like "5회 한도"
        match = re.search(r'(\d+)회\s*한도', text)
        if match:
            return {
                'type': 'multiple',
                'count': int(match.group(1)),
                'period': 'lifetime',
            }

        return None  # unknown

    def _extract_treatment_method(self, name: str) -> List[str]:
        """Extract treatment_method from coverage name."""
        methods = []

        for keyword, method in self.TREATMENT_METHODS.items():
            if keyword in name:
                methods.append(method)

        return methods

    def _extract_renewal_flag(self, text: str) -> bool:
        """Extract renewal_flag from "[갱신형]" marker."""
        return bool(self.RENEWAL_PATTERN.search(text))

    def _extract_renewal_period(self, text: str) -> Optional[int]:
        """Extract renewal_period_years from "10년갱신" etc."""
        match = self.RENEWAL_PERIOD_PATTERN.search(text)
        if match:
            return int(match.group(1))
        return None

    def _determine_confidence(self, name: str, text: str) -> str:
        """
        Determine source_confidence level.

        Rules:
        - proposal_confirmed: extractable from proposal
        - policy_required: requires policy doc verification
        """
        # If disease scope mentioned but not confirmed -> policy_required
        if self._extract_disease_scope_raw(name) is not None:
            return 'policy_required'

        # If reduction periods unknown -> policy_required
        if self._extract_reduction_periods(text) is None:
            return 'policy_required'

        return 'proposal_confirmed'

    def _extract_qualification_suffix(self, name: str) -> Optional[str]:
        """
        Extract qualification_suffix from parentheses.

        Examples:
            "암 진단비(유사암 제외)" -> "유사암 제외"
            "[갱신형] 치료비" -> "갱신형"
        """
        # Check for renewal prefix
        if '[갱신형]' in name:
            return '갱신형'

        # Extract parentheses content
        match = re.search(r'\(([^)]+)\)', name)
        if match:
            return match.group(1)

        return None
