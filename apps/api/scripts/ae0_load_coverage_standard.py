#!/usr/bin/env python3
"""
STEP NEXT-AE-0: Load신정원 Unified Coverage Codes to v2.coverage_standard

Purpose:
Load신정원 unified coverage codes from Excel to v2.coverage_standard (SSOT).

Constitutional Guarantees:
- Excel is input medium only, DB is SSOT
- coverage_code is immutable (INSERT only, no UPDATE of code)
- Duplicate/conflict validation (all-or-nothing)
- FK integrity check (all existing mappings must reference valid codes)
"""

import logging
import sys
import json
from pathlib import Path
from typing import Dict, List
import pandas as pd
import psycopg2
import psycopg2.extras

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.db import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register JSON adapter
psycopg2.extras.register_json(oid=3802, array_oid=3807, globally=True)


class CoverageStandardLoader:
    """Load신정원 unified coverage codes from Excel to v2.coverage_standard"""

    def __init__(self, conn):
        self.conn = conn

    def load_from_excel(
        self,
        xlsx_path: Path,
        code_column: str = 'cre_cvr_cd',
        name_column: str = '신정원코드명'
    ) -> Dict:
        """
        Load신정원 codes from Excel.

        Args:
            xlsx_path: Path to Excel file
            code_column: Column name for canonical coverage code
            name_column: Column name for display name

        Returns:
            {
                'success': bool,
                'errors': List[str],
                'inserted': int,
                'updated': int,
                'skipped': int,
                'total_codes': int
            }
        """
        logger.info(f"Loading from: {xlsx_path}")

        # Read Excel
        try:
            df = pd.read_excel(xlsx_path)
        except Exception as e:
            return {
                'success': False,
                'errors': [f"Failed to read Excel: {e}"],
                'inserted': 0,
                'updated': 0,
                'skipped': 0,
                'total_codes': 0
            }

        logger.info(f"Read {len(df)} rows from Excel")

        # Validate columns exist
        if code_column not in df.columns:
            return {
                'success': False,
                'errors': [f"Column '{code_column}' not found in Excel"],
                'inserted': 0,
                'updated': 0,
                'skipped': 0,
                'total_codes': 0
            }

        # Extract unique codes
        unique_codes_df = df[[code_column, name_column]].drop_duplicates(subset=[code_column])
        unique_codes_df = unique_codes_df.dropna(subset=[code_column])

        logger.info(f"Unique canonical codes: {len(unique_codes_df)}")

        # Check existing codes
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM v2.coverage_standard")
            existing_count = cur.fetchone()[0]
            logger.info(f"Existing v2.coverage_standard rows: {existing_count}")

        # Insert codes (UPSERT on coverage_code)
        inserted = 0
        updated = 0
        skipped = 0
        errors = []

        for _, row in unique_codes_df.iterrows():
            code = str(row[code_column]).strip()
            display_name = str(row[name_column]).strip() if pd.notna(row[name_column]) else code

            # Validation
            if not code or len(code) == 0:
                skipped += 1
                continue

            try:
                with self.conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO v2.coverage_standard (
                            coverage_code,
                            display_name,
                            domain,
                            coverage_type,
                            priority,
                            is_main,
                            meta
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                        ON CONFLICT (coverage_code)
                        DO UPDATE SET
                            display_name = EXCLUDED.display_name,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING (xmax = 0) AS inserted
                    """, (
                        code,
                        display_name,
                        None,  # domain: to be filled later
                        None,  # coverage_type: to be filled later
                        999,   # priority: default
                        False, # is_main: default
                        json.dumps({})  # meta: empty
                    ))

                    was_inserted = cur.fetchone()[0]
                    if was_inserted:
                        inserted += 1
                    else:
                        updated += 1

            except Exception as e:
                errors.append(f"Failed to insert code '{code}': {e}")
                skipped += 1

        if errors:
            logger.warning(f"Encountered {len(errors)} errors during insert")
            for error in errors[:5]:  # Show first 5
                logger.warning(f"  - {error}")

        self.conn.commit()

        logger.info(f"✅ Load complete: inserted={inserted}, updated={updated}, skipped={skipped}")

        # Verify final count
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM v2.coverage_standard")
            final_count = cur.fetchone()[0]
            logger.info(f"Final v2.coverage_standard rows: {final_count}")

        return {
            'success': True,
            'errors': errors,
            'inserted': inserted,
            'updated': updated,
            'skipped': skipped,
            'total_codes': final_count
        }

    def validate_fk_integrity(self) -> Dict:
        """
        Validate FK integrity: all coverage_mapping.canonical_coverage_code
        must exist in v2.coverage_standard.

        Returns:
            {
                'valid': bool,
                'invalid_mappings': List[str],
                'total_mappings': int
            }
        """
        logger.info("Validating FK integrity (coverage_mapping → coverage_standard)")

        with self.conn.cursor() as cur:
            # Check invalid mappings
            cur.execute("""
                SELECT m.canonical_coverage_code, COUNT(*) as count
                FROM v2.coverage_mapping m
                WHERE NOT EXISTS (
                    SELECT 1 FROM v2.coverage_standard cs
                    WHERE cs.coverage_code = m.canonical_coverage_code
                )
                GROUP BY m.canonical_coverage_code
            """)

            invalid_mappings = cur.fetchall()

            # Total mappings
            cur.execute("SELECT COUNT(*) FROM v2.coverage_mapping")
            total_mappings = cur.fetchone()[0]

        if invalid_mappings:
            logger.error(f"❌ FK integrity FAILED: {len(invalid_mappings)} invalid canonical codes")
            for code, count in invalid_mappings:
                logger.error(f"  - {code}: {count} mappings")

            return {
                'valid': False,
                'invalid_mappings': [code for code, _ in invalid_mappings],
                'total_mappings': total_mappings
            }

        logger.info(f"✅ FK integrity PASSED: all {total_mappings} mappings reference valid codes")

        return {
            'valid': True,
            'invalid_mappings': [],
            'total_mappings': total_mappings
        }


def main():
    """Main load script"""
    import argparse

    parser = argparse.ArgumentParser(
        description='STEP NEXT-AE-0: Load신정원 Coverage Codes to v2.coverage_standard'
    )
    parser.add_argument(
        '--xlsx',
        type=Path,
        default=Path('data/담보명mapping자료.xlsx'),
        help='Path to신정원 mapping Excel file'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Validate FK integrity only (no load)'
    )

    args = parser.parse_args()

    # Connect to DB
    conn = get_db_connection(readonly=False)

    try:
        loader = CoverageStandardLoader(conn)

        if args.validate_only:
            # Validate FK integrity only
            result = loader.validate_fk_integrity()

            print("\n" + "=" * 60)
            print("STEP NEXT-AE-0: FK Integrity Validation")
            print("=" * 60)
            print(f"Valid: {result['valid']}")
            print(f"Total Mappings: {result['total_mappings']}")

            if result['invalid_mappings']:
                print(f"\n❌ Invalid canonical codes ({len(result['invalid_mappings'])}):")
                for code in result['invalid_mappings']:
                    print(f"  - {code}")
                return 1

            print("\n✅ FK integrity PASSED")
            return 0

        # Load from Excel
        result = loader.load_from_excel(args.xlsx)

        print("\n" + "=" * 60)
        print("STEP NEXT-AE-0: Load Result")
        print("=" * 60)
        print(f"Success: {result['success']}")
        print(f"Total Codes: {result['total_codes']}")
        print(f"Inserted: {result['inserted']}")
        print(f"Updated: {result['updated']}")
        print(f"Skipped: {result['skipped']}")

        if result['errors']:
            print(f"\nErrors ({len(result['errors'])}):")
            for error in result['errors'][:10]:  # Show first 10
                print(f"  - {error}")

        # Validate FK integrity
        print("\n" + "-" * 60)
        fk_result = loader.validate_fk_integrity()

        if not fk_result['valid']:
            print("\n❌ FK integrity FAILED")
            return 1

        print("\n✅ AE-0 Gate PASSED")
        print("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"❌ Load failed: {e}", exc_info=True)
        return 1

    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
