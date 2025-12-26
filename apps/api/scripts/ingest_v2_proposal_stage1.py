#!/usr/bin/env python3
"""
STEP NEXT-AB: v2 Proposal Ingestion Stage-1
Template + Coverage Universe Only

Constitutional Rules:
- ❌ NO coverage mapping (Excel)
- ❌ NO coverage_standard reference
- ❌ NO proposal_coverage_mapped
- ✅ Coverage name as-is (insurer_coverage_name)
- ✅ Simple normalization (lowercase, strip)
- ✅ Extract amount if visible in table
"""

import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pypdf
import psycopg2
from psycopg2.extensions import connection as PGConnection
from datetime import date

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.db import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProposalParser:
    """Simple rule-based parser for proposal front-page coverage table"""

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.reader = pypdf.PdfReader(str(pdf_path))

    def extract_coverage_table(self, max_pages: int = 3) -> List[Dict]:
        """
        Extract coverage table from front pages.

        Returns:
            List of {coverage_name, amount_value, page, span_text}
        """
        coverages = []

        for page_num in range(min(max_pages, len(self.reader.pages))):
            page = self.reader.pages[page_num]
            text = page.extract_text()

            # Simple heuristic: look for lines with coverage names and amounts
            # This is a placeholder - real implementation would need PDF table extraction
            lines = text.split('\n')

            for line in lines:
                # Skip empty or header lines
                if not line.strip() or len(line.strip()) < 3:
                    continue

                # Look for patterns like "암진단비 1,000만원" or "암진단비 10,000,000원"
                if self._looks_like_coverage_line(line):
                    coverage = self._parse_coverage_line(line, page_num + 1)
                    if coverage:
                        coverages.append(coverage)

        logger.info(f"Extracted {len(coverages)} coverages from {self.pdf_path.name}")
        return coverages

    def _looks_like_coverage_line(self, line: str) -> bool:
        """Check if line looks like a coverage item"""
        # Simple heuristic: contains common coverage keywords
        keywords = ['암', '진단', '수술', '입원', '통원', '치료', '사망', '장해']
        return any(kw in line for kw in keywords)

    def _parse_coverage_line(self, line: str, page: int) -> Optional[Dict]:
        """
        Parse coverage line to extract name and amount.

        This is a simplified implementation. Real parser would need:
        - PDF table structure extraction
        - Column alignment
        - Amount parsing with proper unit detection
        """
        import re

        # Try to find amount patterns
        # Pattern 1: "1,000만원" or "10,000,000원"
        amount_match = re.search(r'([\d,]+)\s*(만원|원)', line)

        coverage_name = line.strip()
        amount_value = None

        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            unit = amount_match.group(2)

            try:
                if unit == '만원':
                    amount_value = int(amount_str) * 10000
                elif unit == '원':
                    amount_value = int(amount_str)
            except ValueError:
                pass

        return {
            'coverage_name': coverage_name,
            'amount_value': amount_value,
            'page': page,
            'span_text': line.strip()
        }


class V2ProposalIngestion:
    """Stage-1 ingestion: Template + Coverage Universe only"""

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
        Ingest proposal PDF to v2 schema.

        Args:
            pdf_path: Path to proposal PDF
            product_id: Product ID (must exist in v2.product)
            version: Template version (e.g., "2511")
            effective_date: Effective date (optional)

        Returns:
            (template_id, coverage_count)
        """
        logger.info(f"Ingesting proposal: {pdf_path}")
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

        # Step 3: Extract coverage table
        parser = ProposalParser(pdf_path)
        coverages = parser.extract_coverage_table(max_pages=3)

        if not coverages:
            logger.warning("No coverages extracted from PDF")
            return template_id, 0

        # Step 4: Insert coverages
        coverage_count = self._insert_coverages(template_id, coverages)
        logger.info(f"  Inserted {coverage_count} coverages")

        return template_id, coverage_count

    def _calculate_fingerprint(self, pdf_path: Path) -> str:
        """Calculate content hash for template fingerprint"""
        hasher = hashlib.sha256()
        with open(pdf_path, 'rb') as f:
            # Read first 10 pages or entire file
            hasher.update(f.read(1024 * 1024))  # First 1MB
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
                json.dumps({})
            ))

            self.conn.commit()
            logger.info(f"Template created: {template_id}")
            return template_id

    def _insert_coverages(self, template_id: str, coverages: List[Dict]) -> int:
        """Insert coverages to v2.proposal_coverage"""
        inserted = 0

        with self.conn.cursor() as cur:
            for cov in coverages:
                coverage_name = cov['coverage_name']
                normalized_name = self._normalize_name(coverage_name)
                amount_value = cov.get('amount_value')
                page = cov['page']
                span_text = cov['span_text']

                # Calculate content hash
                content = f"{normalized_name}|{amount_value}|{page}|{span_text}"
                content_hash = hashlib.sha256(content.encode()).hexdigest()

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
                        coverage_name,
                        normalized_name,
                        'KRW',
                        amount_value,
                        'unknown',  # Will be resolved in later stage
                        page,
                        span_text,
                        content_hash
                    ))
                    if cur.rowcount > 0:
                        inserted += 1
                except Exception as e:
                    logger.error(f"Failed to insert coverage {coverage_name}: {e}")

            self.conn.commit()

        return inserted

    def _normalize_name(self, name: str) -> str:
        """Simple normalization: lowercase + strip"""
        return name.lower().strip()


def main():
    """Main ingestion script"""
    import argparse

    parser = argparse.ArgumentParser(description='v2 Proposal Ingestion Stage-1')
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

    # Connect to DB (writable mode)
    conn = get_db_connection(readonly=False)

    try:
        ingestion = V2ProposalIngestion(conn)
        template_id, count = ingestion.ingest_proposal(
            pdf_path=args.pdf_path,
            product_id=args.product_id,
            version=args.version,
            effective_date=effective_date
        )

        logger.info(f"✅ Ingestion complete:")
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
