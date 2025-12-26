#!/usr/bin/env python3
"""
STEP NEXT-AB (FINAL): v2 Proposal Ingestion Stage-1
Structure-First Universe Extraction

Constitutional Principles:
- PDF는 레이아웃 문서로 취급 (텍스트가 아님)
- 구조 파악 → 테이블 추출 → 행 단위 저장
- 의미 해석 / 정규화 / 매핑 전면 금지
- 실패 / 누락도 데이터로 저장

Stage-0: PDF 문서 타입 확인 (proposal)
Stage-1: Template 식별 (product + version + fingerprint)
Stage-2: 앞 2장 담보 테이블 구조 기반 추출

금지 사항:
- ❌ 텍스트 키워드 기반 추출
- ❌ LLM 기반 분류/판단
- ❌ coverage_standard 참조
- ❌ Excel 매핑
- ❌ 정규화 / 표준코드 추론
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
from datetime import date

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.db import get_db_connection
from app.ah.proposal_meta_filter import ProposalMetaFilter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProposalStructureExtractor:
    """
    Structure-First PDF Table Extractor

    Principles:
    1. PDF = Layout Document (not text)
    2. Table structure first, content second
    3. Row-by-row extraction (no interpretation)
    4. Failures stored as data
    """

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.pdf = pdfplumber.open(str(pdf_path))
        logger.info(f"Opened PDF: {pdf_path.name}, pages={len(self.pdf.pages)}")

    def close(self):
        """Close PDF"""
        if self.pdf:
            self.pdf.close()

    def extract_coverage_universe(self, max_pages: int = 3) -> List[Dict]:
        """
        Extract coverage universe from front pages (Structure-First).

        Process:
        1. Locate table on each page
        2. Extract table structure (rows × columns)
        3. Parse each row as coverage
        4. Store failures as NULL

        Returns:
            List of {
                coverage_name_raw: str,
                amount_value: int | None,
                amount_text: str | None,
                source_page: int,
                span_text: str,
                extraction_status: str  # 'success' | 'partial' | 'failed'
            }
        """
        coverages = []

        for page_num in range(min(max_pages, len(self.pdf.pages))):
            page = self.pdf.pages[page_num]
            page_coverages = self._extract_page_coverages(page, page_num + 1)
            coverages.extend(page_coverages)
            logger.info(f"Page {page_num + 1}: extracted {len(page_coverages)} coverage rows")

        logger.info(f"Total extracted: {len(coverages)} coverage rows")
        return coverages

    def _extract_page_coverages(self, page, page_num: int) -> List[Dict]:
        """Extract coverages from a single page using table structure"""
        coverages = []

        # Extract tables from page
        tables = page.extract_tables()

        if not tables:
            logger.warning(f"Page {page_num}: No tables found")
            return coverages

        # Process first table (assumption: coverage table is first)
        table = tables[0]
        logger.debug(f"Page {page_num}: Table with {len(table)} rows")

        # Find header row to determine column indices
        header_row_idx = self._find_header_row(table)
        if header_row_idx is None:
            logger.warning(f"Page {page_num}: Could not find header row")
            # Try to extract anyway with default column mapping
            header_row_idx = 0

        # Extract coverages from data rows (skip header rows)
        for row_idx in range(header_row_idx + 1, len(table)):
            row = table[row_idx]
            coverage = self._parse_coverage_row(row, page_num)
            if coverage:
                coverages.append(coverage)

        return coverages

    def _find_header_row(self, table: List[List[str]]) -> Optional[int]:
        """
        Find header row by looking for known column headers.

        Headers: 담보가입현황, 가입금액, 보험료
        """
        for idx, row in enumerate(table):
            row_text = ' '.join([str(cell) if cell else '' for cell in row])
            if '담보가입현황' in row_text or '가입금액' in row_text:
                logger.debug(f"Found header at row {idx}")
                return idx
        return None

    def _parse_coverage_row(self, row: List[str], page_num: int) -> Optional[Dict]:
        """
        Parse a single table row as coverage.

        Expected columns (Samsung proposal format):
        [0] Category (진단/입원/수술) or None
        [1] Coverage name
        [2] Coverage amount (가입금액)
        [3] Premium (보험료)
        [4] Period/Code (납입기간/보험기간)

        Returns:
            {
                coverage_name_raw: str,
                amount_value: int | None,
                amount_text: str | None,
                source_page: int,
                span_text: str,
                extraction_status: str
            }
        """
        # Skip empty rows
        if not any(row):
            return None

        # Column 1 should contain coverage name
        coverage_name = row[1] if len(row) > 1 and row[1] else None
        if not coverage_name:
            return None

        # Skip header-like rows
        if '담보가입현황' in coverage_name or '피보험자' in coverage_name:
            return None

        coverage_name = coverage_name.strip()

        # Column 2 contains amount text (e.g., "3,000만원", "10만원")
        amount_text = row[2] if len(row) > 2 and row[2] else None
        amount_value = None
        extraction_status = 'success'

        if amount_text:
            amount_text = amount_text.strip()
            # Try to parse amount
            parsed_amount = self._parse_amount(amount_text)
            if parsed_amount is not None:
                amount_value = parsed_amount
            else:
                extraction_status = 'partial'  # Name found, amount parse failed
        else:
            extraction_status = 'partial'  # Name found, no amount

        # Build span text from entire row
        span_text = ' | '.join([str(cell) if cell else '' for cell in row])

        return {
            'coverage_name_raw': coverage_name,
            'amount_value': amount_value,
            'amount_text': amount_text,
            'source_page': page_num,
            'span_text': span_text,
            'extraction_status': extraction_status
        }

    def _parse_amount(self, amount_text: str) -> Optional[int]:
        """
        Parse Korean amount text to integer.

        Examples:
        - "3,000만원" → 30000000
        - "600만원" → 6000000
        - "10만원" → 100000
        - "1만원" → 10000
        - "10,000,000원" → 10000000

        Returns None if parsing fails.
        """
        # Remove spaces
        amount_text = amount_text.replace(' ', '').replace(',', '')

        # Pattern 1: N만원
        match = re.match(r'(\d+(?:\.\d+)?)만원', amount_text)
        if match:
            try:
                return int(float(match.group(1)) * 10000)
            except ValueError:
                return None

        # Pattern 2: N원
        match = re.match(r'(\d+)원', amount_text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None

        # Pattern 3: Just number
        if amount_text.isdigit():
            return int(amount_text)

        return None


class V2ProposalIngestion:
    """
    Stage-1 Ingestion: Template + Coverage Universe (Structure-First)

    Constitutional Guarantees:
    - NO coverage mapping
    - NO normalization
    - NO Excel reference
    - NO coverage_standard access
    - Structure → Data only
    """

    def __init__(self, conn: PGConnection):
        self.conn = conn

    def ingest_proposal(
        self,
        pdf_path: Path,
        product_id: str,
        version: str,
        effective_date: Optional[date] = None
    ) -> Tuple[str, int]:
        """
        Ingest proposal PDF to v2 schema (Structure-First).

        Args:
            pdf_path: Path to proposal PDF
            product_id: Product ID (must exist in v2.product)
            version: Template version (e.g., "2511")
            effective_date: Effective date (optional)

        Returns:
            (template_id, coverage_count)
        """
        logger.info(f"Ingesting proposal (Structure-First): {pdf_path}")
        logger.info(f"  Product: {product_id}")
        logger.info(f"  Version: {version}")

        # Step 1: Calculate fingerprint from PDF
        fingerprint = self._calculate_fingerprint(pdf_path)
        logger.info(f"  Fingerprint: {fingerprint}")

        # Step 2: Get or create template
        template_id = self._get_or_create_template(
            product_id=product_id,
            version=version,
            fingerprint=fingerprint,
            effective_date=effective_date
        )
        logger.info(f"  Template ID: {template_id}")

        # Step 3: Extract coverage table (Structure-First)
        extractor = ProposalStructureExtractor(pdf_path)
        try:
            coverages_raw = extractor.extract_coverage_universe(max_pages=3)

            if not coverages_raw:
                logger.warning("No coverages extracted from PDF")
                return template_id, 0

            # Step 3.5: Apply meta row filter (AH-6)
            logger.info(f"  Applying meta row filter to {len(coverages_raw)} rows...")
            coverages, filter_stats = ProposalMetaFilter.filter_proposal_rows(coverages_raw)
            logger.info(f"  Meta filter results:")
            logger.info(f"    Total rows: {filter_stats['total_rows']}")
            logger.info(f"    Filtered out: {filter_stats['filtered_rows']}")
            logger.info(f"    Kept: {filter_stats['kept_rows']}")
            logger.info(f"    Filter rate: {filter_stats['filter_rate']:.2%}")

            # Log sample of filtered rows (first 10)
            if filter_stats['filtered_rows'] > 0:
                filtered_samples = [
                    r.get('coverage_name_raw')
                    for r in coverages_raw
                    if ProposalMetaFilter.is_meta_row(r.get('coverage_name_raw'))
                ][:10]
                logger.info(f"  Sample filtered rows: {filtered_samples}")

            if not coverages:
                logger.warning("No valid coverages after meta filtering")
                return template_id, 0

            # Step 4: Insert coverages
            coverage_count = self._insert_coverages(template_id, coverages)
            logger.info(f"  Inserted {coverage_count} coverages")

            # Log extraction quality
            success_count = sum(1 for c in coverages if c['extraction_status'] == 'success')
            partial_count = sum(1 for c in coverages if c['extraction_status'] == 'partial')
            logger.info(f"  Extraction quality: success={success_count}, partial={partial_count}")

            return template_id, coverage_count

        finally:
            extractor.close()

    def _calculate_fingerprint(self, pdf_path: Path) -> str:
        """Calculate content hash for template fingerprint"""
        hasher = hashlib.sha256()
        with open(pdf_path, 'rb') as f:
            # Read first 1MB for fingerprint
            hasher.update(f.read(1024 * 1024))
        return hasher.hexdigest()

    def _get_or_create_template(
        self,
        product_id: str,
        version: str,
        fingerprint: str,
        effective_date: Optional[date]
    ) -> str:
        """Get existing template or create new one"""
        template_type = 'proposal'
        template_id = f"{product_id}_{template_type}_{version}_{fingerprint[:8]}"

        with self.conn.cursor() as cur:
            # Check if template exists
            cur.execute(
                "SELECT template_id FROM v2.template WHERE template_id = %s",
                (template_id,)
            )
            existing = cur.fetchone()

            if existing:
                logger.info(f"Template exists: {template_id}")
                return template_id

            # Create new template
            cur.execute("""
                INSERT INTO v2.template (
                    template_id,
                    product_id,
                    template_type,
                    version,
                    fingerprint,
                    effective_date,
                    meta
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (template_id) DO NOTHING
                RETURNING template_id
            """, (
                template_id,
                product_id,
                template_type,
                version,
                fingerprint,
                effective_date,
                json.dumps({'extraction_method': 'structure_first_v1'})
            ))

            self.conn.commit()
            logger.info(f"Template created: {template_id}")
            return template_id

    def _insert_coverages(self, template_id: str, coverages: List[Dict]) -> int:
        """Insert coverages to v2.proposal_coverage"""
        inserted = 0

        with self.conn.cursor() as cur:
            for cov in coverages:
                coverage_name_raw = cov['coverage_name_raw']
                amount_value = cov.get('amount_value')
                page = cov['source_page']
                span_text = cov['span_text']

                # Calculate content hash
                content = f"{coverage_name_raw}|{amount_value}|{page}|{span_text}"
                content_hash = hashlib.sha256(content.encode()).hexdigest()

                # Determine payout_amount_unit from amount_text
                payout_unit = 'unknown'
                if cov.get('amount_text'):
                    if '만원' in cov['amount_text']:
                        payout_unit = '만원'
                    elif '원' in cov['amount_text']:
                        payout_unit = '원'

                try:
                    cur.execute("""
                        INSERT INTO v2.proposal_coverage (
                            template_id,
                            insurer_coverage_name,
                            normalized_name,
                            currency,
                            amount_value,
                            payout_amount_unit,
                            source_page,
                            span_text,
                            content_hash
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (template_id, content_hash) DO NOTHING
                    """, (
                        template_id,
                        coverage_name_raw,
                        coverage_name_raw,  # normalized_name = raw for now (no normalization)
                        'KRW',
                        amount_value,
                        payout_unit,
                        page,
                        span_text,
                        content_hash
                    ))
                    if cur.rowcount > 0:
                        inserted += 1
                except Exception as e:
                    logger.error(f"Failed to insert coverage {coverage_name_raw}: {e}")

            self.conn.commit()

        return inserted


def main():
    """Main ingestion script"""
    import argparse

    parser = argparse.ArgumentParser(
        description='v2 Proposal Ingestion Stage-1 (Structure-First)'
    )
    parser.add_argument('pdf_path', type=Path, help='Path to proposal PDF')
    parser.add_argument('--product-id', required=True, help='Product ID')
    parser.add_argument('--version', required=True, help='Template version')
    parser.add_argument('--effective-date', type=str, help='Effective date (YYYY-MM-DD)')

    args = parser.parse_args()

    if not args.pdf_path.exists():
        logger.error(f"PDF not found: {args.pdf_path}")
        return 1

    effective_date = None
    if args.effective_date:
        effective_date = date.fromisoformat(args.effective_date)

    # Connect to DB
    conn = get_db_connection(readonly=False)

    try:
        ingestion = V2ProposalIngestion(conn)
        template_id, count = ingestion.ingest_proposal(
            pdf_path=args.pdf_path,
            product_id=args.product_id,
            version=args.version,
            effective_date=effective_date
        )

        logger.info(f"✅ Ingestion complete (Structure-First):")
        logger.info(f"  Template: {template_id}")
        logger.info(f"  Coverages: {count}")

        return 0

    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}", exc_info=True)
        return 1

    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
