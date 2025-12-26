#!/usr/bin/env python3
"""
STEP NEXT-AF: Proposal Detail Table Extractor
Extract detail table (보장내용 상세표) for Comparison Description

Constitutional Principles:
- Detail table is for Comparison Description (NOT Evidence)
- Deterministic structure-based parsing only
- Match to proposal_coverage universe via insurer_coverage_name
- Unknown match state = NULL coverage_id (no guessing)

Forbidden:
- ❌ LLM-based extraction
- ❌ Saving to coverage_evidence
- ❌ Guessing coverage_id from similarity
- ❌ Using detail content as evidence source
"""

import hashlib
import json
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional
import pdfplumber
import psycopg2
from psycopg2.extensions import connection as PGConnection

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.db import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProposalDetailExtractor:
    """
    Extract proposal detail table (보장내용 설명) using deterministic structure-based parsing.

    Principles:
    1. Structure-first: locate detail section by layout markers
    2. Coverage name matching: exact or normalized match to proposal_coverage
    3. No LLM: regex and table structure only
    4. NULL coverage_id if no match (no guessing)
    """

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.pdf = pdfplumber.open(str(pdf_path))
        logger.info(f"Opened PDF: {pdf_path.name}, pages={len(self.pdf.pages)}")

    def close(self):
        """Close PDF"""
        if self.pdf:
            self.pdf.close()

    def extract_details(self, start_page: int = 3, max_pages: int = 10) -> List[Dict]:
        """
        Extract coverage details from detail section pages.

        Detail section typically starts after summary table (page 3+).

        Args:
            start_page: Page number to start (1-indexed)
            max_pages: Maximum pages to scan

        Returns:
            List of {
                insurer_coverage_name: str,
                detail_text: str,
                detail_struct: dict | None,
                source_page: int,
                excerpt_hash: str
            }
        """
        details = []

        for page_idx in range(start_page - 1, min(start_page - 1 + max_pages, len(self.pdf.pages))):
            page = self.pdf.pages[page_idx]
            page_details = self._extract_page_details(page, page_idx + 1)
            details.extend(page_details)
            logger.info(f"Page {page_idx + 1}: extracted {len(page_details)} detail blocks")

        logger.info(f"Total extracted: {len(details)} detail blocks")
        return details

    def _extract_page_details(self, page, page_num: int) -> List[Dict]:
        """Extract detail blocks from a single page"""
        details = []

        # Strategy 1: Extract tables (some insurers use table format)
        tables = page.extract_tables()
        if tables:
            for table in tables:
                table_details = self._parse_detail_table(table, page_num)
                details.extend(table_details)

        # Strategy 2: Extract text blocks (some insurers use paragraph format)
        # Look for pattern: coverage name header + detail content
        text = page.extract_text()
        if text:
            text_details = self._parse_detail_text(text, page_num)
            details.extend(text_details)

        return details

    def _parse_detail_table(self, table: List[List[str]], page_num: int) -> List[Dict]:
        """
        Parse detail table structure.

        Expected formats:
        - Format A: [담보명 | 보장내용]
        - Format B: [구분 | 담보명 | 보장내용 | 비고]
        """
        details = []

        # Find header row
        header_idx = None
        for idx, row in enumerate(table):
            row_text = ' '.join([str(c) if c else '' for c in row])
            if '보장내용' in row_text or '지급사유' in row_text:
                header_idx = idx
                break

        if header_idx is None:
            return details

        # Process data rows
        for row_idx in range(header_idx + 1, len(table)):
            row = table[row_idx]
            if not any(row):
                continue

            # Extract coverage name and detail
            coverage_name = None
            detail_text = None

            # Try different column layouts
            if len(row) >= 2:
                # Format: [담보명, 보장내용, ...]
                coverage_name = row[0] if row[0] else None
                detail_text = row[1] if row[1] else None

            if coverage_name and detail_text:
                coverage_name = self._normalize_coverage_name(coverage_name)
                detail_text = detail_text.strip()

                if coverage_name and detail_text and len(detail_text) > 10:
                    excerpt_hash = hashlib.sha256(
                        f"{coverage_name}:{detail_text}".encode()
                    ).hexdigest()[:16]

                    details.append({
                        'insurer_coverage_name': coverage_name,
                        'detail_text': detail_text,
                        'detail_struct': {'format': 'table', 'row_count': 1},
                        'source_page': page_num,
                        'excerpt_hash': excerpt_hash
                    })

        return details

    def _parse_detail_text(self, text: str, page_num: int) -> List[Dict]:
        """
        Parse detail from plain text using pattern matching.

        Pattern:
        - Coverage name (usually bold/header, may contain keywords like "암진단비", "입원비")
        - Detail content (multiple lines, contains "지급", "보장", etc.)
        """
        details = []

        # Split by common section markers
        # Look for patterns like:
        # "암진단비\n- 보장내용: ..."
        # "입원비\n지급사유: ..."

        # Pattern: coverage name line + detail content (greedy)
        pattern = r'([^\n]+(?:진단|입원|수술|사망|후유장해|치료)[^\n]*)\n([^\n]+(?:지급|보장)[^\n]{20,})'

        matches = re.finditer(pattern, text, re.MULTILINE)
        for match in matches:
            coverage_name_raw = match.group(1).strip()
            detail_content = match.group(2).strip()

            coverage_name = self._normalize_coverage_name(coverage_name_raw)

            if coverage_name and detail_content and len(detail_content) > 10:
                excerpt_hash = hashlib.sha256(
                    f"{coverage_name}:{detail_content}".encode()
                ).hexdigest()[:16]

                details.append({
                    'insurer_coverage_name': coverage_name,
                    'detail_text': detail_content,
                    'detail_struct': {'format': 'text', 'pattern_match': True},
                    'source_page': page_num,
                    'excerpt_hash': excerpt_hash
                })

        return details

    def _normalize_coverage_name(self, name: str) -> str:
        """
        Normalize coverage name for matching.

        Rules:
        - Remove whitespace
        - Remove parentheses content (optional info)
        - Remove special chars except Korean/digits
        """
        if not name:
            return ""

        # Remove leading markers/numbers
        name = re.sub(r'^[\d\-\.\)\s]+', '', name)

        # Remove parentheses
        name = re.sub(r'\([^)]*\)', '', name)

        # Remove brackets
        name = re.sub(r'\[[^\]]*\]', '', name)

        # Remove special chars (keep Korean, digits, 진단/입원/수술 etc.)
        name = re.sub(r'[^\w가-힣]', '', name)

        return name.strip()


def match_coverage_id(
    conn: PGConnection,
    template_id: str,
    insurer_coverage_name: str
) -> Optional[int]:
    """
    Match insurer_coverage_name to coverage_id from proposal_coverage.

    Matching strategy:
    1. Exact match (normalized)
    2. Partial match (prefix/suffix)
    3. NULL if no confident match

    Args:
        conn: DB connection
        template_id: Template ID to scope search
        insurer_coverage_name: Normalized coverage name from detail

    Returns:
        coverage_id or None
    """
    cursor = conn.cursor()

    # Try exact match
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
    start_page: int = 3,
    max_pages: int = 10
) -> Dict[str, int]:
    """
    Extract and ingest proposal detail table.

    Args:
        conn: DB connection
        template_id: Template ID (must exist in v2.template)
        pdf_path: Path to proposal PDF
        start_page: Start page for detail section
        max_pages: Max pages to scan

    Returns:
        Stats dict with counts
    """
    extractor = ProposalDetailExtractor(pdf_path)

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

            # Insert
            cursor.execute("""
                INSERT INTO v2.proposal_coverage_detail (
                    template_id,
                    coverage_id,
                    insurer_coverage_name,
                    detail_text,
                    detail_struct,
                    source_doc_type,
                    source_page,
                    excerpt_hash
                )
                VALUES (%s, %s, %s, %s, %s, 'proposal_detail', %s, %s)
                ON CONFLICT (template_id, coverage_id, excerpt_hash)
                DO UPDATE SET
                    detail_text = EXCLUDED.detail_text,
                    detail_struct = EXCLUDED.detail_struct,
                    source_page = EXCLUDED.source_page,
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
        python af_extract_proposal_detail.py <template_id> <pdf_path>
    """
    if len(sys.argv) < 3:
        print("Usage: python af_extract_proposal_detail.py <template_id> <pdf_path>")
        print("Example: python af_extract_proposal_detail.py SAMSUNG_CANCER_V1 data/samsung/가입설계서/삼성_가입설계서_2511.pdf")
        sys.exit(1)

    template_id = sys.argv[1]
    pdf_path = Path(sys.argv[2])

    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        sys.exit(1)

    # Get DB connection (write mode for ingestion)
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
        stats = ingest_proposal_detail(conn, template_id, pdf_path)

        print(f"\n✅ Ingestion complete:")
        print(f"  Extracted: {stats['extracted']}")
        print(f"  Matched: {stats['matched']}")
        print(f"  Unmatched: {stats['unmatched']}")
        print(f"  Inserted: {stats['inserted']}")

    finally:
        conn.close()


if __name__ == '__main__':
    main()
