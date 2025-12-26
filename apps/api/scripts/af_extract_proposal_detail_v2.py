#!/usr/bin/env python3
"""
STEP NEXT-AF-FIX: Improved Proposal Detail Table Extractor
Extract detail table (보장내용 상세표) for Comparison Description

Improvements over v1:
1. Section detection: Find detail section by header keywords
2. Line-based fallback: Parse text blocks when table extraction fails
3. Template_id isolation: Only match within same template universe
4. extraction_method tracking: Deterministic only (no manual)

Constitutional Principles:
- Detail table is for Comparison Description (NOT Evidence)
- Deterministic structure-based parsing only
- Match to proposal_coverage universe via (template_id, insurer_coverage_name)
- NULL coverage_id if no confident match (no guessing)

Forbidden:
- ❌ LLM-based extraction
- ❌ Saving to coverage_evidence
- ❌ Guessing coverage_id from similarity
- ❌ Cross-template matching
"""

import hashlib
import json
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pdfplumber
import psycopg2
from psycopg2.extensions import connection as PGConnection

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.db import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Section header keywords for detail table
DETAIL_SECTION_KEYWORDS = [
    '보장내용',
    '보장내역',
    '담보별',
    '지급사유',
    '보험금 지급',
    '주요 보장내용',
]


class ProposalDetailExtractorV2:
    """
    Improved detail extractor with section detection and line-based fallback.

    Principles:
    1. Find detail section by header keywords
    2. Try table extraction first
    3. Fall back to line-based parsing if table fails
    4. Deterministic only (no LLM, no guessing)
    """

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.pdf = pdfplumber.open(str(pdf_path))
        logger.info(f"Opened PDF: {pdf_path.name}, pages={len(self.pdf.pages)}")

    def close(self):
        """Close PDF"""
        if self.pdf:
            self.pdf.close()

    def find_detail_section_pages(self) -> List[int]:
        """
        Find pages containing detail section by header keywords.

        Returns:
            List of 0-indexed page numbers
        """
        detail_pages = []

        for page_idx, page in enumerate(self.pdf.pages):
            text = page.extract_text()
            if not text:
                continue

            # Check for detail section headers
            for keyword in DETAIL_SECTION_KEYWORDS:
                if keyword in text:
                    detail_pages.append(page_idx)
                    logger.info(f"Found detail section keyword '{keyword}' on page {page_idx + 1}")
                    break  # One keyword per page is enough

        return detail_pages

    def extract_details(self, start_page: Optional[int] = None, max_pages: int = 10) -> List[Dict]:
        """
        Extract coverage details from detail section pages.

        Args:
            start_page: Page number to start (1-indexed), None = auto-detect
            max_pages: Maximum pages to scan

        Returns:
            List of detail dicts
        """
        details = []

        # Auto-detect detail section if not specified
        if start_page is None:
            detail_page_indices = self.find_detail_section_pages()
            if not detail_page_indices:
                logger.warning("No detail section found - trying all pages after page 3")
                detail_page_indices = list(range(2, min(len(self.pdf.pages), 12)))  # Pages 3-12
        else:
            detail_page_indices = list(range(start_page - 1, min(start_page - 1 + max_pages, len(self.pdf.pages))))

        for page_idx in detail_page_indices:
            page = self.pdf.pages[page_idx]
            page_details = self._extract_page_details_improved(page, page_idx + 1)
            details.extend(page_details)
            logger.info(f"Page {page_idx + 1}: extracted {len(page_details)} detail blocks")

        logger.info(f"Total extracted: {len(details)} detail blocks")
        return details

    def _extract_page_details_improved(self, page, page_num: int) -> List[Dict]:
        """
        Extract detail blocks from a single page with improved strategy.

        Strategy:
        1. Try table extraction (pdfplumber tables)
        2. If tables are empty/malformed, fall back to line-based parsing
        3. Normalize coverage names before saving
        """
        details = []

        # Strategy 1: Try table extraction
        tables = page.extract_tables()
        if tables:
            for table in tables:
                table_details = self._parse_detail_table_improved(table, page_num)
                if table_details:
                    details.extend(table_details)
                    logger.debug(f"Page {page_num}: Extracted {len(table_details)} details from table")

        # Strategy 2: Fall back to line-based parsing if no table details
        if not details:
            text = page.extract_text()
            if text:
                text_details = self._parse_detail_text_improved(text, page_num)
                details.extend(text_details)
                logger.debug(f"Page {page_num}: Extracted {len(text_details)} details from text (fallback)")

        return details

    def _parse_detail_table_improved(self, table: List[List[str]], page_num: int) -> List[Dict]:
        """
        Parse detail table with improved row detection.

        Expected formats:
        - [담보명 | 보장내용]
        - [구분 | 담보명 | 보장내용]

        Improvements:
        - Better header detection
        - Filter out meta rows (주계약, 선택계약 etc.)
        - Require minimum detail length (> 20 chars)
        """
        details = []

        if not table or len(table) < 2:
            return details

        # Find header row
        header_idx = None
        for idx, row in enumerate(table):
            row_text = ' '.join([str(c) if c else '' for c in row]).lower()
            if any(kw in row_text for kw in ['보장내용', '지급사유', '보장금액']):
                header_idx = idx
                break

        if header_idx is None:
            return details

        # Process data rows
        for row_idx in range(header_idx + 1, len(table)):
            row = table[row_idx]
            if not any(row):  # Empty row
                continue

            # Try to extract coverage name and detail text
            # Format heuristic: find first column with Korean text as coverage name
            # Find longest column as detail text
            coverage_name = None
            detail_text = None

            row_cells = [str(cell).strip() if cell else '' for cell in row]

            # Find coverage name (first non-empty cell with Korean)
            for cell in row_cells:
                if cell and len(cell) > 2 and self._has_korean(cell):
                    coverage_name = cell
                    break

            # Find detail text (longest cell, excluding coverage name)
            for cell in row_cells:
                if cell and cell != coverage_name and len(cell) > 20:
                    if not detail_text or len(cell) > len(detail_text):
                        detail_text = cell

            # Filter out meta rows
            if coverage_name and self._is_meta_row(coverage_name):
                continue

            if coverage_name and detail_text and len(detail_text) > 20:
                normalized_name = self._normalize_coverage_name(coverage_name)
                if normalized_name:
                    excerpt_hash = hashlib.sha256(
                        f"{normalized_name}:{detail_text}".encode()
                    ).hexdigest()[:16]

                    details.append({
                        'insurer_coverage_name': normalized_name,
                        'detail_text': detail_text.strip(),
                        'detail_struct': {'format': 'table', 'method': 'deterministic_v2'},
                        'source_page': page_num,
                        'excerpt_hash': excerpt_hash
                    })

        return details

    def _parse_detail_text_improved(self, text: str, page_num: int) -> List[Dict]:
        """
        Parse detail from plain text using improved pattern matching.

        Pattern detection:
        - Coverage name line (usually bold/header, contains keywords like 진단/입원/수술)
        - Detail content (multiple lines, contains 지급/보장)
        - Block boundaries (bold headers, numbers, blank lines)
        """
        details = []

        # Split by double newlines or section markers
        blocks = re.split(r'\n\s*\n', text)

        for block in blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if len(lines) < 2:
                continue

            # First line might be coverage name
            potential_coverage = lines[0]
            potential_detail = ' '.join(lines[1:])

            # Check if first line looks like coverage name
            if (self._has_korean(potential_coverage) and
                len(potential_coverage) < 100 and  # Not too long
                any(kw in potential_coverage for kw in ['진단', '입원', '수술', '사망', '치료', '질환']) and
                not self._is_meta_row(potential_coverage)):

                # Check if rest looks like detail
                if (len(potential_detail) > 30 and
                    any(kw in potential_detail for kw in ['지급', '보장', '경우', '확정', '받은'])):

                    normalized_name = self._normalize_coverage_name(potential_coverage)
                    if normalized_name:
                        excerpt_hash = hashlib.sha256(
                            f"{normalized_name}:{potential_detail}".encode()
                        ).hexdigest()[:16]

                        details.append({
                            'insurer_coverage_name': normalized_name,
                            'detail_text': potential_detail,
                            'detail_struct': {'format': 'text', 'method': 'deterministic_v2'},
                            'source_page': page_num,
                            'excerpt_hash': excerpt_hash
                        })

        return details

    def _has_korean(self, text: str) -> bool:
        """Check if text contains Korean characters"""
        return bool(re.search(r'[가-힣]', text))

    def _is_meta_row(self, name: str) -> bool:
        """
        Check if coverage name is actually a meta/header row.

        Meta patterns:
        - 주계약, 선택계약
        - 통합고객, 피보험자
        - 보험나이
        - 구분, 분류
        """
        meta_keywords = [
            '주계약', '선택계약', '특약',
            '통합고객', '피보험자', '계약자',
            '보험나이', '변경일',
            '구분', '분류', '가입형',
            '담보가입', '담보명', '보장내용',  # Table headers
        ]

        normalized = name.replace(' ', '').lower()
        return any(kw in normalized for kw in meta_keywords)

    def _normalize_coverage_name(self, name: str) -> str:
        """
        Normalize coverage name for matching.

        Rules:
        - Remove leading markers/numbers
        - Remove parentheses content (optional info) - KEEP for initial matching
        - Remove special chars except Korean/digits/parentheses
        - Strip whitespace
        """
        if not name:
            return ""

        # Remove leading markers/numbers
        name = re.sub(r'^[\d\-\.\)\s]+', '', name)

        # DO NOT remove parentheses for matching (they are part of canonical name)
        # name = re.sub(r'\([^)]*\)', '', name)  # REMOVED

        # Keep Korean, digits, parentheses, spaces
        name = re.sub(r'[^\w가-힣()\s]', '', name)

        return name.strip()


def match_coverage_id(
    conn: PGConnection,
    template_id: str,
    insurer_coverage_name: str
) -> Optional[int]:
    """
    Match insurer_coverage_name to coverage_id from proposal_coverage.

    IMPORTANT: Only match within same template_id (template isolation).

    Matching strategy:
    1. Exact match (normalized)
    2. Partial match (prefix/suffix) with length check
    3. NULL if no confident match

    Args:
        conn: DB connection
        template_id: Template ID to scope search (REQUIRED for isolation)
        insurer_coverage_name: Normalized coverage name from detail

    Returns:
        coverage_id or None
    """
    cursor = conn.cursor()

    # CONSTITUTIONAL: Match within same template only
    cursor.execute("""
        SELECT coverage_id, insurer_coverage_name
        FROM v2.proposal_coverage
        WHERE template_id = %s
        ORDER BY coverage_id
    """, (template_id,))

    rows = cursor.fetchall()
    cursor.close()

    # Normalize all and compare
    normalized_input = insurer_coverage_name.replace(' ', '').lower()

    for coverage_id, insurer_coverage_name_db in rows:
        normalized_db = insurer_coverage_name_db.replace(' ', '').lower()

        # Exact match
        if normalized_input == normalized_db:
            return coverage_id

        # Partial match (input contains db name or vice versa)
        if normalized_input in normalized_db or normalized_db in normalized_input:
            # Additional check: length difference < 30%
            len_diff = abs(len(normalized_input) - len(normalized_db))
            if len_diff / max(len(normalized_input), len(normalized_db)) < 0.3:
                return coverage_id

    # No confident match
    return None


def ingest_proposal_detail(
    conn: PGConnection,
    template_id: str,
    pdf_path: Path,
    start_page: Optional[int] = None,
    max_pages: int = 10
) -> Dict[str, int]:
    """
    Extract and ingest proposal detail table (v2 - improved).

    Args:
        conn: DB connection
        template_id: Template ID (must exist in v2.template)
        pdf_path: Path to proposal PDF
        start_page: Start page for detail section (None = auto-detect)
        max_pages: Max pages to scan

    Returns:
        Stats dict with counts
    """
    extractor = ProposalDetailExtractorV2(pdf_path)

    try:
        # Extract details
        details = extractor.extract_details(start_page, max_pages)

        if not details:
            logger.warning(f"No details extracted from {pdf_path.name}")
            return {'extracted': 0, 'matched': 0, 'unmatched': 0, 'inserted': 0}

        # Match and insert
        cursor = conn.cursor()
        matched_count = 0
        unmatched_count = 0
        inserted_count = 0

        for detail in details:
            coverage_id = match_coverage_id(
                conn,
                template_id,
                detail['insurer_coverage_name']
            )

            if coverage_id:
                matched_count += 1
            else:
                unmatched_count += 1
                logger.debug(f"Unmatched: {detail['insurer_coverage_name']}")

            # Insert with extraction_method
            cursor.execute("""
                INSERT INTO v2.proposal_coverage_detail (
                    template_id,
                    coverage_id,
                    insurer_coverage_name,
                    detail_text,
                    detail_struct,
                    source_doc_type,
                    source_page,
                    excerpt_hash,
                    extraction_method
                )
                VALUES (%s, %s, %s, %s, %s, 'proposal_detail', %s, %s, 'deterministic_v2')
                ON CONFLICT (template_id, coverage_id, excerpt_hash)
                DO UPDATE SET
                    detail_text = EXCLUDED.detail_text,
                    detail_struct = EXCLUDED.detail_struct,
                    source_page = EXCLUDED.source_page,
                    extraction_method = EXCLUDED.extraction_method,
                    updated_at = NOW()
            """, (
                template_id,
                coverage_id,  # nullable
                detail['insurer_coverage_name'],
                detail['detail_text'],
                json.dumps(detail['detail_struct']) if detail['detail_struct'] else None,
                detail['source_page'],
                detail['excerpt_hash']
            ))
            inserted_count += 1

        conn.commit()
        cursor.close()

        logger.info(
            f"Ingested {inserted_count} details "
            f"(matched={matched_count}, unmatched={unmatched_count})"
        )

        return {
            'extracted': len(details),
            'matched': matched_count,
            'unmatched': unmatched_count,
            'inserted': inserted_count
        }

    finally:
        extractor.close()


def main():
    """
    Main entry point.

    Usage:
        python af_extract_proposal_detail_v2.py <template_id> <pdf_path> [start_page]
    """
    if len(sys.argv) < 3:
        print("Usage: python af_extract_proposal_detail_v2.py <template_id> <pdf_path> [start_page]")
        print("Example: python af_extract_proposal_detail_v2.py SAMSUNG_CANCER_V1 data/samsung/가입설계서/삼성_가입설계서_2511.pdf")
        print("         python af_extract_proposal_detail_v2.py SAMSUNG_CANCER_V1 data/samsung/가입설계서/삼성_가입설계서_2511.pdf 4")
        sys.exit(1)

    template_id = sys.argv[1]
    pdf_path = Path(sys.argv[2])
    start_page = int(sys.argv[3]) if len(sys.argv) > 3 else None

    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        sys.exit(1)

    # Get DB connection (write mode)
    conn = get_db_connection(readonly=False)

    try:
        # Verify template exists
        cursor = conn.cursor()
        cursor.execute("SELECT template_id FROM v2.template WHERE template_id = %s", (template_id,))
        if not cursor.fetchone():
            logger.error(f"Template not found: {template_id}")
            cursor.close()
            sys.exit(1)
        cursor.close()

        # Ingest
        stats = ingest_proposal_detail(conn, template_id, pdf_path, start_page)

        print(f"\n✅ Ingestion complete:")
        print(f"  Extracted: {stats['extracted']}")
        print(f"  Matched: {stats['matched']}")
        print(f"  Unmatched: {stats['unmatched']}")
        print(f"  Inserted: {stats['inserted']}")

        if stats['matched'] > 0:
            match_rate = stats['matched'] / stats['extracted'] * 100
            print(f"  Match rate: {match_rate:.1f}%")

    finally:
        conn.close()


if __name__ == '__main__':
    main()
