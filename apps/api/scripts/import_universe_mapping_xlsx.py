#!/usr/bin/env python3
"""
STEP NEXT-AD-FIX: Import Universe Mapping (XLSX → DB) with SSOT Enforcement

Purpose:
Import manually-filled canonical codes from XLSX to v2.coverage_mapping.

Constitutional Guarantees:
- DB is SSOT, XLSX is I/O medium only
- Strict validation (all-or-nothing, ON_ERROR_STOP semantics)
- 신정원 통일코드 검증 필수 (v2.coverage_standard reference)
- NO legacy public schema writes
- Upsert on (template_id, coverage_id) conflict
"""

import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd
import psycopg2
from psycopg2.extensions import connection as PGConnection

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.db import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MappingValidator:
    """
    Validate XLSX rows before import.

    Validation Rules (strict, all-or-nothing):
    1. template_id must be identical across all rows
    2. template_id must exist in DB
    3. coverage_id must exist in DB with matching template_id
    4. canonical_coverage_code must not be empty
    5. canonical_coverage_code format: [A-Z0-9_]+ (conservative)
    6. canonical_coverage_code must exist in v2.coverage_standard (신정원 SSOT)
    """

    def __init__(self, conn: PGConnection):
        self.conn = conn
        self._load_coverage_standard()

    def _load_coverage_standard(self):
        """Load신정원 coverage codes from v2.coverage_standard (SSOT)"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT coverage_code FROM v2.coverage_standard")
            self.valid_coverage_codes = {row[0] for row in cur.fetchall()}

        logger.info(f"Loaded {len(self.valid_coverage_codes)} valid신정원 coverage codes from v2.coverage_standard")
        if not self.valid_coverage_codes:
            logger.warning("⚠️  v2.coverage_standard is EMPTY - all canonical_coverage_code will FAIL validation")

    def validate_xlsx(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate XLSX DataFrame.

        Returns:
            (is_valid, errors)
        """
        errors = []

        # Rule 1: template_id identical across all rows
        template_ids = df['template_id'].unique()
        if len(template_ids) != 1:
            errors.append(
                f"Rule 1 FAILED: template_id must be identical across all rows. "
                f"Found {len(template_ids)} unique values: {list(template_ids)}"
            )
            return False, errors

        template_id = template_ids[0]

        # Rule 2: template_id exists in DB
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM v2.template WHERE template_id = %s",
                (template_id,)
            )
            if cur.fetchone()[0] == 0:
                errors.append(
                    f"Rule 2 FAILED: template_id '{template_id}' does not exist in DB"
                )
                return False, errors

        # Rule 3: coverage_id exists with matching template_id
        coverage_ids = df['coverage_id'].dropna().astype(int).tolist()
        with self.conn.cursor() as cur:
            for coverage_id in coverage_ids:
                cur.execute("""
                    SELECT template_id
                    FROM v2.proposal_coverage
                    WHERE coverage_id = %s
                """, (coverage_id,))
                result = cur.fetchone()
                if not result:
                    errors.append(
                        f"Rule 3 FAILED: coverage_id {coverage_id} does not exist in DB"
                    )
                elif result[0] != template_id:
                    errors.append(
                        f"Rule 3 FAILED: coverage_id {coverage_id} has template_id '{result[0]}', "
                        f"expected '{template_id}'"
                    )

        if errors:
            return False, errors

        # Rule 4, 5, 6: canonical_coverage_code validation (per row with code)
        for idx, row in df.iterrows():
            canonical_code = row.get('canonical_coverage_code', '')

            # Skip if empty (unmapped rows are OK, just not imported)
            if pd.isna(canonical_code) or str(canonical_code).strip() == '':
                continue

            canonical_code = str(canonical_code).strip()

            # Rule 4: not empty (already checked above)

            # Rule 5: format validation [A-Z0-9_]+
            if not re.match(r'^[A-Z0-9_]+$', canonical_code):
                errors.append(
                    f"Rule 5 FAILED: Row {idx+2} (Excel row): "
                    f"canonical_coverage_code '{canonical_code}' "
                    f"has invalid format (expected [A-Z0-9_]+)"
                )
                continue

            # Rule 6: 신정원 SSOT validation (must exist in v2.coverage_standard)
            if canonical_code not in self.valid_coverage_codes:
                errors.append(
                    f"Rule 6 FAILED: Row {idx+2} (Excel row): "
                    f"canonical_coverage_code '{canonical_code}' "
                    f"NOT FOUND in v2.coverage_standard (신정원 통일코드 SSOT). "
                    f"Valid codes: {sorted(self.valid_coverage_codes)}"
                )

        if errors:
            return False, errors

        return True, []


class MappingImporter:
    """
    Import canonical coverage mapping from XLSX to DB.

    Constitutional Guarantees:
    - Upsert on (template_id, coverage_id) conflict
    - Write ONLY to v2.coverage_mapping
    - NO legacy public schema writes
    """

    def __init__(self, conn: PGConnection):
        self.conn = conn
        self.validator = MappingValidator(conn)

    def import_mapping(
        self,
        xlsx_path: Path,
        dry_run: bool = False
    ) -> Dict:
        """
        Import mapping from XLSX to DB.

        Args:
            xlsx_path: Path to XLSX file
            dry_run: If True, validate only (no DB write)

        Returns:
            {
                'valid': bool,
                'errors': List[str],
                'total_rows': int,
                'mappable_rows': int,
                'skipped_rows': int,
                'inserted': int,
                'updated': int
            }
        """
        logger.info(f"Importing mapping from: {xlsx_path}")
        logger.info(f"Dry-run mode: {dry_run}")

        # Read XLSX
        try:
            df = pd.read_excel(xlsx_path, sheet_name='Universe Mapping')
        except Exception as e:
            logger.error(f"Failed to read XLSX: {e}")
            return {
                'valid': False,
                'errors': [f"Failed to read XLSX: {e}"],
                'total_rows': 0,
                'mappable_rows': 0,
                'skipped_rows': 0,
                'inserted': 0,
                'updated': 0
            }

        logger.info(f"Read {len(df)} rows from XLSX")

        # Validate
        is_valid, errors = self.validator.validate_xlsx(df)

        if not is_valid:
            logger.error(f"Validation FAILED: {len(errors)} errors")
            for error in errors:
                logger.error(f"  - {error}")
            return {
                'valid': False,
                'errors': errors,
                'total_rows': len(df),
                'mappable_rows': 0,
                'skipped_rows': 0,
                'inserted': 0,
                'updated': 0
            }

        logger.info("✅ Validation PASSED")

        # Count mappable rows (rows with canonical_coverage_code)
        mappable_rows = []
        skipped_rows = []

        for idx, row in df.iterrows():
            canonical_code = row.get('canonical_coverage_code', '')
            if pd.isna(canonical_code) or str(canonical_code).strip() == '':
                skipped_rows.append(idx)
            else:
                mappable_rows.append(row)

        logger.info(f"Mappable rows: {len(mappable_rows)}")
        logger.info(f"Skipped rows (empty code): {len(skipped_rows)}")

        if dry_run:
            logger.info("✅ Dry-run complete (no DB write)")
            return {
                'valid': True,
                'errors': [],
                'total_rows': len(df),
                'mappable_rows': len(mappable_rows),
                'skipped_rows': len(skipped_rows),
                'inserted': 0,
                'updated': 0
            }

        # Import to DB (upsert)
        inserted_count = 0
        updated_count = 0

        for row in mappable_rows:
            template_id = str(row['template_id']).strip()
            coverage_id = int(row['coverage_id'])
            canonical_code = str(row['canonical_coverage_code']).strip()
            note = str(row.get('note', '')).strip() if pd.notna(row.get('note')) else None

            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO v2.coverage_mapping (
                        template_id,
                        coverage_id,
                        canonical_coverage_code,
                        mapping_source,
                        mapping_status,
                        note
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (template_id, coverage_id)
                    DO UPDATE SET
                        canonical_coverage_code = EXCLUDED.canonical_coverage_code,
                        note = EXCLUDED.note,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING (xmax = 0) AS inserted
                """, (
                    template_id,
                    coverage_id,
                    canonical_code,
                    'xlsx_manual',
                    'MAPPED',
                    note
                ))

                # xmax = 0 means INSERT, xmax != 0 means UPDATE
                was_inserted = cur.fetchone()[0]
                if was_inserted:
                    inserted_count += 1
                else:
                    updated_count += 1

        self.conn.commit()

        logger.info(f"✅ Import complete: inserted={inserted_count}, updated={updated_count}")

        return {
            'valid': True,
            'errors': [],
            'total_rows': len(df),
            'mappable_rows': len(mappable_rows),
            'skipped_rows': len(skipped_rows),
            'inserted': inserted_count,
            'updated': updated_count
        }


def main():
    """Main import script"""
    import argparse

    parser = argparse.ArgumentParser(
        description='STEP NEXT-AD: Import Universe Mapping (XLSX → DB)'
    )
    parser.add_argument(
        '--xlsx',
        type=Path,
        required=True,
        help='Path to XLSX file to import'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate only (no DB write)'
    )

    args = parser.parse_args()

    if not args.xlsx.exists():
        logger.error(f"XLSX file not found: {args.xlsx}")
        return 1

    # Connect to DB (writable)
    conn = get_db_connection(readonly=False)

    try:
        importer = MappingImporter(conn)
        result = importer.import_mapping(
            xlsx_path=args.xlsx,
            dry_run=args.dry_run
        )

        print("\n" + "=" * 60)
        print("STEP NEXT-AD: Import Result")
        print("=" * 60)
        print(f"Valid: {result['valid']}")
        if result['errors']:
            print(f"\nErrors ({len(result['errors'])}):")
            for error in result['errors']:
                print(f"  - {error}")
            return 1

        print(f"Total Rows: {result['total_rows']}")
        print(f"Mappable Rows: {result['mappable_rows']}")
        print(f"Skipped Rows: {result['skipped_rows']}")

        if not args.dry_run:
            print(f"\nDB Write:")
            print(f"  Inserted: {result['inserted']}")
            print(f"  Updated: {result['updated']}")
        else:
            print(f"\n✅ Dry-run PASSED (no DB write)")

        print("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"❌ Import failed: {e}", exc_info=True)
        return 1

    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
