#!/usr/bin/env python3
"""
STEP NEXT-AD: Export Universe for Mapping (DB → XLSX)

Purpose:
Export UNIVERSE_COVERAGE rows to XLSX for manual canonical code mapping.

Constitutional Guarantees:
- DB is SSOT, XLSX is I/O medium only
- NO insurer_code/product_id input fields (prevents past mismatch issues)
- Join key is ONLY (template_id, coverage_id)
- Read-only export (no DB modification)
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict
import pandas as pd
import psycopg2
from psycopg2.extensions import connection as PGConnection

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.db import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UniverseExporter:
    """
    Export UNIVERSE_COVERAGE rows to XLSX for manual mapping.

    Export Columns (fixed order):
    1. template_id (READ-ONLY)
    2. coverage_id (READ-ONLY)
    3. insurer_coverage_name (raw)
    4. amount_value
    5. payout_amount_unit
    6. source_page
    7. canonical_coverage_code (EMPTY - to be filled)
    8. note (EMPTY)
    """

    def __init__(self, conn: PGConnection):
        self.conn = conn

    def export_universe(self, template_id: str, output_path: Path) -> Dict:
        """
        Export Universe coverage to XLSX.

        Args:
            template_id: Template ID to export
            output_path: Output XLSX file path

        Returns:
            {
                'template_id': str,
                'universe_count': int,
                'output_path': Path
            }
        """
        logger.info(f"Exporting Universe for template: {template_id}")

        # Query UNIVERSE_COVERAGE rows
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT
                    pc.coverage_id,
                    pc.insurer_coverage_name,
                    pc.amount_value,
                    pc.payout_amount_unit,
                    pc.source_page
                FROM v2.proposal_coverage pc
                JOIN v2.proposal_coverage_universe_lock ul
                    ON pc.coverage_id = ul.coverage_id
                WHERE
                    pc.template_id = %s
                    AND ul.lock_class = 'UNIVERSE_COVERAGE'
                ORDER BY pc.coverage_id
            """, (template_id,))

            rows = cur.fetchall()

        if not rows:
            logger.warning(f"No UNIVERSE_COVERAGE rows found for template: {template_id}")
            return {
                'template_id': template_id,
                'universe_count': 0,
                'output_path': None
            }

        logger.info(f"Found {len(rows)} UNIVERSE_COVERAGE rows")

        # Build DataFrame
        data = []
        for coverage_id, coverage_name, amount_value, payout_unit, source_page in rows:
            data.append({
                'template_id': template_id,  # Fixed for all rows
                'coverage_id': coverage_id,
                'insurer_coverage_name': coverage_name,
                'amount_value': amount_value if amount_value is not None else '',
                'payout_amount_unit': payout_unit,
                'source_page': source_page,
                'canonical_coverage_code': '',  # EMPTY - to be filled manually
                'note': ''  # EMPTY
            })

        df = pd.DataFrame(data)

        # Create output directory if not exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Export to XLSX
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Universe Mapping', index=False)

            # Apply minimal formatting (header bold)
            workbook = writer.book
            worksheet = writer.sheets['Universe Mapping']

            # Bold header
            for cell in worksheet[1]:
                cell.font = cell.font.copy(bold=True)

            # Auto-adjust column width
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        logger.info(f"Exported to: {output_path}")

        return {
            'template_id': template_id,
            'universe_count': len(rows),
            'output_path': output_path
        }


def main():
    """Main export script"""
    import argparse

    parser = argparse.ArgumentParser(
        description='STEP NEXT-AD: Export Universe for Mapping (DB → XLSX)'
    )
    parser.add_argument(
        '--template-id',
        required=True,
        help='Template ID to export (e.g., SAMSUNG_CANCER_2024_proposal_2511_a840f677)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output XLSX path (default: artifacts/mapping/{template_id}__universe_mapping.xlsx)'
    )

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        # Default: artifacts/mapping/{template_id}__universe_mapping.xlsx
        output_path = Path('artifacts/mapping') / f"{args.template_id}__universe_mapping.xlsx"

    # Connect to DB (read-only)
    conn = get_db_connection(readonly=True)

    try:
        exporter = UniverseExporter(conn)
        result = exporter.export_universe(
            template_id=args.template_id,
            output_path=output_path
        )

        if result['universe_count'] == 0:
            logger.warning("❌ No Universe rows to export")
            return 1

        print("\n" + "=" * 60)
        print("STEP NEXT-AD: Universe Export Complete")
        print("=" * 60)
        print(f"Template ID: {result['template_id']}")
        print(f"Universe Rows: {result['universe_count']}")
        print(f"Output File: {result['output_path']}")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Open XLSX file")
        print("2. Fill 'canonical_coverage_code' column (신정원 통일코드)")
        print("3. Optionally fill 'note' column")
        print("4. Run import script:")
        print(f"   python apps/api/scripts/import_universe_mapping_xlsx.py \\")
        print(f"     --xlsx {result['output_path']} \\")
        print(f"     --dry-run  # Validate first")
        print("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"❌ Export failed: {e}", exc_info=True)
        return 1

    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
