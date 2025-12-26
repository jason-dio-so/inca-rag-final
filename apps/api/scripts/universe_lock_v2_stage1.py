#!/usr/bin/env python3
"""
STEP NEXT-AC: Universe Lock + Structure Contract (No Mapping)

Purpose:
Lock Universe data quality by classifying raw extraction results into:
- UNIVERSE_COVERAGE (SSOT eligible)
- NON_UNIVERSE_META (header/customer/summary)
- UNCLASSIFIED (ambiguous)

Constitutional Guarantees:
- ❌ NO Excel mapping
- ❌ NO coverage_standard reference
- ❌ NO proposal_coverage_mapped access
- ❌ NO semantic interpretation
- ✅ Structure-based classification only
- ✅ Raw data preservation (no deletion/modification)
"""

import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
import psycopg2
from psycopg2.extensions import connection as PGConnection

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.db import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRIPT_VERSION = 'v1.0'


@dataclass
class ClassificationRule:
    """Rule for classifying a coverage row"""
    pattern: str  # Regex or keyword
    lock_class: str  # UNIVERSE_COVERAGE | NON_UNIVERSE_META | UNCLASSIFIED
    reason: str  # Human-readable reason
    priority: int = 0  # Higher priority rules apply first


class UniverseRowClassifier:
    """
    Structure-based classifier for Universe Lock.

    Classification Logic (NO semantic interpretation):
    1. NON_UNIVERSE_META (highest priority)
       - Header keywords: 담보가입현황, 가입금액, 보험료, 피보험자
       - Customer info: 통합고객, 보험나이변경일
       - Summary: 합계, 총보험료, 계

    2. UNIVERSE_COVERAGE (medium priority)
       - Has amount_value (parsed successfully)
       - Has coverage_name_raw (non-empty)
       - NOT matching NON_UNIVERSE_META patterns

    3. UNCLASSIFIED (lowest priority)
       - Ambiguous cases (e.g., coverage_name exists but no amount)
    """

    def __init__(self):
        self.rules = self._build_classification_rules()

    def _build_classification_rules(self) -> List[ClassificationRule]:
        """
        Build classification rules (Structure-First).

        Rules are deterministic and based on:
        - Keyword matching (header/summary/customer info)
        - Amount presence (amount_value IS NOT NULL)
        - Column structure (not semantic interpretation)
        """
        rules = []

        # Priority 1: NON_UNIVERSE_META (exclude from Universe)
        # More specific patterns to avoid false positives
        non_universe_keywords = [
            ('담보가입현황', 'header_keyword'),
            ('가입금액', 'header_keyword'),
            ('피보험자', 'customer_info_keyword'),
            ('통합고객', 'customer_info_keyword'),
            ('보험나이변경일', 'customer_info_keyword'),
            ('합계', 'summary_keyword'),
            ('총보험료', 'summary_keyword'),
            ('갱신보험료 합계', 'summary_keyword'),  # More specific
            ('비갱신보험료 합계', 'summary_keyword'),  # More specific
        ]

        for keyword, reason_prefix in non_universe_keywords:
            rules.append(ClassificationRule(
                pattern=keyword,
                lock_class='NON_UNIVERSE_META',
                reason=f'{reason_prefix}:{keyword}',
                priority=10
            ))

        return rules

    def classify_row(
        self,
        coverage_name: str,
        amount_value: int or None
    ) -> Tuple[str, str]:
        """
        Classify a single coverage row.

        Args:
            coverage_name: insurer_coverage_name (raw)
            amount_value: amount_value (parsed, can be NULL)

        Returns:
            (lock_class, lock_reason)
        """
        # Priority 1: Check NON_UNIVERSE_META rules
        for rule in sorted(self.rules, key=lambda r: r.priority, reverse=True):
            if rule.pattern in coverage_name:
                return rule.lock_class, rule.reason

        # Priority 2: UNIVERSE_COVERAGE (has amount + coverage name)
        if amount_value is not None and coverage_name.strip():
            return 'UNIVERSE_COVERAGE', 'has_amount_value'

        # Priority 3: UNCLASSIFIED (coverage name exists but no amount)
        if coverage_name.strip():
            return 'UNCLASSIFIED', 'no_amount_value'

        # Fallback: Empty coverage name
        return 'NON_UNIVERSE_META', 'empty_coverage_name'


class UniverseLockProcessor:
    """
    Process Universe Lock for a template.

    Constitutional Guarantees:
    - Raw data (v2.proposal_coverage) is NEVER modified
    - Lock results stored separately (v2.proposal_coverage_universe_lock)
    - Idempotent (re-running produces same results)
    """

    def __init__(self, conn: PGConnection):
        self.conn = conn
        self.classifier = UniverseRowClassifier()

    def process_template(self, template_id: str) -> Dict:
        """
        Process Universe Lock for a template.

        Args:
            template_id: Template ID to process

        Returns:
            {
                'template_id': str,
                'total_rows': int,
                'universe_coverage': int,
                'non_universe_meta': int,
                'unclassified': int,
                'classification_results': List[Dict]
            }
        """
        logger.info(f"Processing Universe Lock for template: {template_id}")

        # Fetch all coverage rows for this template
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT
                    coverage_id,
                    insurer_coverage_name,
                    amount_value
                FROM v2.proposal_coverage
                WHERE template_id = %s
                ORDER BY coverage_id
            """, (template_id,))

            rows = cur.fetchall()

        if not rows:
            logger.warning(f"No coverage rows found for template: {template_id}")
            return {
                'template_id': template_id,
                'total_rows': 0,
                'universe_coverage': 0,
                'non_universe_meta': 0,
                'unclassified': 0,
                'classification_results': []
            }

        logger.info(f"Found {len(rows)} coverage rows to classify")

        # Classify each row
        classification_results = []
        for coverage_id, coverage_name, amount_value in rows:
            lock_class, lock_reason = self.classifier.classify_row(
                coverage_name=coverage_name,
                amount_value=amount_value
            )

            classification_results.append({
                'coverage_id': coverage_id,
                'coverage_name': coverage_name,
                'amount_value': amount_value,
                'lock_class': lock_class,
                'lock_reason': lock_reason
            })

            logger.debug(
                f"Row {coverage_id}: {lock_class} ({lock_reason}) | {coverage_name[:30]}"
            )

        # Insert lock results
        self._insert_lock_results(template_id, classification_results)

        # Count by class
        universe_count = sum(1 for r in classification_results if r['lock_class'] == 'UNIVERSE_COVERAGE')
        meta_count = sum(1 for r in classification_results if r['lock_class'] == 'NON_UNIVERSE_META')
        unclass_count = sum(1 for r in classification_results if r['lock_class'] == 'UNCLASSIFIED')

        result = {
            'template_id': template_id,
            'total_rows': len(rows),
            'universe_coverage': universe_count,
            'non_universe_meta': meta_count,
            'unclassified': unclass_count,
            'classification_results': classification_results
        }

        logger.info(
            f"Classification complete: "
            f"UNIVERSE={universe_count}, "
            f"META={meta_count}, "
            f"UNCLASSIFIED={unclass_count}"
        )

        return result

    def _insert_lock_results(
        self,
        template_id: str,
        classification_results: List[Dict]
    ):
        """Insert lock results to v2.proposal_coverage_universe_lock"""
        with self.conn.cursor() as cur:
            for result in classification_results:
                cur.execute("""
                    INSERT INTO v2.proposal_coverage_universe_lock (
                        coverage_id,
                        template_id,
                        lock_class,
                        lock_reason,
                        locked_by_script,
                        script_version
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (coverage_id, template_id)
                    DO UPDATE SET
                        lock_class = EXCLUDED.lock_class,
                        lock_reason = EXCLUDED.lock_reason,
                        locked_at = CURRENT_TIMESTAMP,
                        script_version = EXCLUDED.script_version
                """, (
                    result['coverage_id'],
                    template_id,
                    result['lock_class'],
                    result['lock_reason'],
                    'universe_lock_v2_stage1',
                    SCRIPT_VERSION
                ))

            self.conn.commit()

        logger.info(f"Inserted {len(classification_results)} lock results")


def main():
    """Main Universe Lock script"""
    import argparse

    parser = argparse.ArgumentParser(
        description='STEP NEXT-AC: Universe Lock + Structure Contract'
    )
    parser.add_argument(
        '--template-id',
        help='Template ID to process (e.g., SAMSUNG_CANCER_2024_proposal_2511_a840f677)'
    )
    parser.add_argument(
        '--product-id',
        help='Product ID (will lookup latest template for this product)'
    )

    args = parser.parse_args()

    if not args.template_id and not args.product_id:
        logger.error("Either --template-id or --product-id must be specified")
        return 1

    # Connect to DB
    conn = get_db_connection(readonly=False)

    try:
        # Resolve template_id
        if args.template_id:
            template_id = args.template_id
        else:
            # Lookup latest template for product_id
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT template_id
                    FROM v2.template
                    WHERE product_id = %s AND template_type = 'proposal'
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (args.product_id,))
                result = cur.fetchone()
                if not result:
                    logger.error(f"No template found for product_id: {args.product_id}")
                    return 1
                template_id = result[0]

        logger.info(f"Processing template: {template_id}")

        # Process Universe Lock
        processor = UniverseLockProcessor(conn)
        result = processor.process_template(template_id)

        # Print summary
        print("\n" + "=" * 60)
        print("STEP NEXT-AC: Universe Lock Summary")
        print("=" * 60)
        print(f"Template ID: {result['template_id']}")
        print(f"Total Rows: {result['total_rows']}")
        print(f"  UNIVERSE_COVERAGE: {result['universe_coverage']}")
        print(f"  NON_UNIVERSE_META: {result['non_universe_meta']}")
        print(f"  UNCLASSIFIED: {result['unclassified']}")
        print("=" * 60)

        # Show sample classifications
        print("\nSample UNIVERSE_COVERAGE rows:")
        universe_rows = [r for r in result['classification_results'] if r['lock_class'] == 'UNIVERSE_COVERAGE']
        for row in universe_rows[:3]:
            print(f"  - {row['coverage_name'][:40]}")

        print("\nSample NON_UNIVERSE_META rows:")
        meta_rows = [r for r in result['classification_results'] if r['lock_class'] == 'NON_UNIVERSE_META']
        for row in meta_rows[:3]:
            print(f"  - {row['coverage_name'][:40]} ({row['lock_reason']})")

        if result['unclassified'] > 0:
            print("\nSample UNCLASSIFIED rows:")
            unclass_rows = [r for r in result['classification_results'] if r['lock_class'] == 'UNCLASSIFIED']
            for row in unclass_rows[:3]:
                print(f"  - {row['coverage_name'][:40]} ({row['lock_reason']})")

        print("\n✅ Universe Lock complete")

        return 0

    except Exception as e:
        logger.error(f"❌ Universe Lock failed: {e}", exc_info=True)
        return 1

    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
