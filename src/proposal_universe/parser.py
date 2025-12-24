"""
Proposal Coverage Parser

Purpose: Extract coverage universe from enrollment proposals (가입설계서)
Output: proposal_coverage_universe table entries

Constitution: Coverage Universe Lock = 가입설계서 담보 리스트
"""

import re
import hashlib
from typing import List, Dict, Optional
from pathlib import Path
import fitz  # PyMuPDF


class ProposalCoverageParser:
    """
    Parse enrollment proposals to extract coverage universe.

    Principles:
    1. Only extract what is explicitly in the proposal
    2. No inference or LLM-based extraction
    3. Every coverage must have evidence (page + span)
    4. Generate content_hash for deduplication
    """

    # Coverage line patterns (deterministic regex)
    COVERAGE_PATTERNS = [
        # Pattern 1: "담보명 금액 [한정어]"
        # Example: "암 진단비(유사암 제외) 3,000만원"
        re.compile(
            r'(?P<name>[가-힣a-zA-Z·\s]+(?:\([^)]+\))?)\s+'
            r'(?P<amount>[\d,]+(?:만원|원))\s*'
            r'(?P<qualifier>.*?)$',
            re.MULTILINE
        ),

        # Pattern 2: "[갱신형] 담보명 금액"
        # Example: "[갱신형] 표적항암약물허가 치료비 1,000만원"
        re.compile(
            r'\[(?P<renewal>갱신형)\]\s*'
            r'(?P<name>[가-힣a-zA-Z·\s]+)\s+'
            r'(?P<amount>[\d,]+(?:만원|원))\s*'
            r'(?P<qualifier>.*?)$',
            re.MULTILINE
        ),

        # Pattern 3: Simple "담보명 금액"
        re.compile(
            r'^(?P<name>[가-힣]+(?:진단|수술|치료|입원)비(?:\([^)]*\))?)\s+'
            r'(?P<amount>[\d,]+(?:만원|원))',
            re.MULTILINE
        ),
    ]

    def __init__(self, insurer: str, proposal_path: Path):
        self.insurer = insurer
        self.proposal_path = proposal_path
        self.proposal_id = self._generate_proposal_id()

    def _generate_proposal_id(self) -> str:
        """Generate proposal_id from filename."""
        return f"{self.insurer.lower()}_proposal_{self.proposal_path.stem}"

    def parse(self) -> List[Dict]:
        """
        Parse proposal PDF and extract coverage universe.

        Returns:
            List of coverage entries with evidence
        """
        coverages = []

        try:
            doc = fitz.open(self.proposal_path)
        except Exception as e:
            raise RuntimeError(f"Failed to open PDF: {e}")

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # Try each pattern
            for pattern in self.COVERAGE_PATTERNS:
                matches = pattern.finditer(text)

                for match in matches:
                    coverage = self._extract_coverage(
                        match=match,
                        page_num=page_num + 1,  # 1-indexed
                        full_text=text
                    )
                    if coverage:
                        coverages.append(coverage)

        doc.close()
        return self._deduplicate(coverages)

    def _extract_coverage(
        self,
        match: re.Match,
        page_num: int,
        full_text: str
    ) -> Optional[Dict]:
        """Extract single coverage from regex match."""

        name = match.group('name').strip()
        amount_str = match.group('amount')

        # Skip if name is too short or generic
        if len(name) < 3 or name in ['보험료', '합계', '총액']:
            return None

        # Parse amount
        amount_value = self._parse_amount(amount_str)

        # Normalize name
        normalized_name = self._normalize_name(name)

        # Extract span (full line containing match)
        span_text = self._extract_span(match, full_text)

        # Generate content hash
        content_hash = self._generate_hash(
            insurer=self.insurer,
            proposal_id=self.proposal_id,
            page=page_num,
            span=span_text
        )

        return {
            'insurer': self.insurer,
            'proposal_id': self.proposal_id,
            'insurer_coverage_name': name,
            'normalized_name': normalized_name,
            'currency': 'KRW',
            'amount_value': amount_value,
            'payout_amount_unit': self._infer_payout_unit(name),
            'source_page': page_num,
            'span_text': span_text,
            'content_hash': content_hash,
        }

    def _parse_amount(self, amount_str: str) -> Optional[int]:
        """
        Parse amount string to integer (원 단위).

        Examples:
            "3,000만원" -> 30000000
            "600만원" -> 6000000
            "5만원" -> 50000
        """
        amount_str = amount_str.replace(',', '')

        if '만원' in amount_str:
            num = amount_str.replace('만원', '')
            try:
                return int(num) * 10000
            except ValueError:
                return None
        elif '원' in amount_str:
            num = amount_str.replace('원', '')
            try:
                return int(num)
            except ValueError:
                return None

        return None

    def _normalize_name(self, name: str) -> str:
        """
        Normalize coverage name for matching.

        Rules:
        1. Remove spaces
        2. Normalize parentheses: ( ) → ()
        3. Lowercase for consistency (optional)
        """
        normalized = name.strip()
        normalized = re.sub(r'\s+', '', normalized)  # Remove all spaces
        normalized = re.sub(r'\(\s+', '(', normalized)  # "( " -> "("
        normalized = re.sub(r'\s+\)', ')', normalized)  # " )" -> ")"

        return normalized

    def _infer_payout_unit(self, name: str) -> str:
        """
        Infer payout_amount_unit from coverage name (deterministic only).

        Returns:
            'lump_sum' (default), 'daily', 'per_event', or 'unknown'
        """
        if '입원일당' in name or '일당' in name:
            return 'daily'
        elif '수술비' in name or '치료비' in name:
            return 'per_event'
        elif '진단비' in name:
            return 'lump_sum'
        else:
            return 'lump_sum'  # default for most Korean insurance

    def _extract_span(self, match: re.Match, full_text: str) -> str:
        """Extract full line containing the match."""
        start = match.start()
        end = match.end()

        # Find line boundaries
        line_start = full_text.rfind('\n', 0, start) + 1
        line_end = full_text.find('\n', end)
        if line_end == -1:
            line_end = len(full_text)

        return full_text[line_start:line_end].strip()

    def _generate_hash(
        self,
        insurer: str,
        proposal_id: str,
        page: int,
        span: str
    ) -> str:
        """
        Generate SHA256 content hash for deduplication.

        Hash input: insurer||proposal_id||page||span_text
        """
        content = f"{insurer}||{proposal_id}||{page}||{span}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _deduplicate(self, coverages: List[Dict]) -> List[Dict]:
        """
        Remove duplicate coverages based on normalized_name.

        Keep first occurrence only.
        """
        seen = set()
        unique = []

        for cov in coverages:
            key = (cov['insurer'], cov['proposal_id'], cov['normalized_name'])
            if key not in seen:
                seen.add(key)
                unique.append(cov)

        return unique
