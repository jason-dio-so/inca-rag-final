#!/usr/bin/env python3
"""
Proposal Universe Lock - Demo Script

Demonstrates E2E functionality:
1. Ingest 5 proposals (Samsung, Meritz, DB, Lotte, KB)
2. Show universe statistics
3. Run comparison scenarios (A/B/C/D)

Usage:
    python scripts/run_proposal_universe_demo.py
"""

import sys
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from proposal_universe.pipeline import ProposalUniversePipeline
from proposal_universe.compare import CompareEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Configuration
DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5432,
}

DATA_DIR = Path(__file__).parent.parent / 'data'
EXCEL_PATH = DATA_DIR / '담보명mapping자료.xlsx'

PROPOSALS = [
    ('Samsung', DATA_DIR / 'samsung' / '가입설계서' / '삼성_가입설계서_2511.pdf'),
    ('Meritz', DATA_DIR / 'meritz' / '가입설계서' / '메리츠_가입설계서_2511.pdf'),
    ('DB', DATA_DIR / 'db' / '가입설계서' / 'DB_가입설계서(40세이하)_2511.pdf'),
    ('Lotte', DATA_DIR / 'lotte' / '가입설계서' / '롯데_가입설계서(남)_2511.pdf'),
]


def initialize_database(conn):
    """Initialize database with migration."""
    logger.info("Initializing database...")

    migration_path = Path(__file__).parent.parent / 'migrations' / 'step6c' / '001_proposal_universe_lock.sql'

    with open(migration_path, 'r') as f:
        migration_sql = f.read()

    with conn.cursor() as cur:
        # Drop existing tables (for clean demo)
        logger.info("Dropping existing tables...")
        cur.execute("""
            DROP TABLE IF EXISTS proposal_coverage_slots CASCADE;
            DROP TABLE IF EXISTS proposal_coverage_mapped CASCADE;
            DROP TABLE IF EXISTS proposal_coverage_universe CASCADE;
            DROP TABLE IF EXISTS coverage_disease_scope CASCADE;
            DROP TABLE IF EXISTS disease_code_group_member CASCADE;
            DROP TABLE IF EXISTS disease_code_group CASCADE;
            DROP TABLE IF EXISTS disease_code_master CASCADE;
            DROP TYPE IF EXISTS mapping_status_enum CASCADE;
            DROP TYPE IF EXISTS event_type_enum CASCADE;
            DROP TYPE IF EXISTS source_confidence_enum CASCADE;
            DROP TYPE IF EXISTS member_type_enum CASCADE;
        """)

        # Run migration
        logger.info("Running migration...")
        cur.execute(migration_sql)

    conn.commit()
    logger.info("Database initialized successfully")


def ingest_all_proposals(pipeline):
    """Ingest all proposals into universe."""
    logger.info("=" * 60)
    logger.info("STEP 1: Ingesting Proposals")
    logger.info("=" * 60)

    all_stats = {}

    for insurer, proposal_path in PROPOSALS:
        if not proposal_path.exists():
            logger.warning(f"Proposal not found: {proposal_path}")
            continue

        logger.info(f"\nIngesting {insurer} proposal: {proposal_path.name}")
        stats = pipeline.ingest_proposal(insurer, proposal_path)

        all_stats[insurer] = stats

        logger.info(f"Results for {insurer}:")
        logger.info(f"  Total coverages: {stats['total_coverages']}")
        logger.info(f"  Inserted to universe: {stats['inserted_universe']}")
        logger.info(f"  Mapping status:")
        for status, count in stats['mapping_status'].items():
            logger.info(f"    {status}: {count}")

    return all_stats


def show_universe_stats(conn):
    """Show universe statistics."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Universe Statistics")
    logger.info("=" * 60)

    with conn.cursor() as cur:
        # Total coverages
        cur.execute("SELECT COUNT(*) as total FROM proposal_coverage_universe;")
        total = cur.fetchone()['total']
        logger.info(f"\nTotal coverages in universe: {total}")

        # By insurer
        cur.execute("""
            SELECT insurer, COUNT(*) as count
            FROM proposal_coverage_universe
            GROUP BY insurer
            ORDER BY count DESC;
        """)
        logger.info("\nCoverages by insurer:")
        for row in cur.fetchall():
            logger.info(f"  {row['insurer']}: {row['count']}")

        # Mapping status distribution
        cur.execute("""
            SELECT mapping_status, COUNT(*) as count
            FROM proposal_coverage_mapped
            GROUP BY mapping_status;
        """)
        logger.info("\nMapping status distribution:")
        for row in cur.fetchall():
            logger.info(f"  {row['mapping_status']}: {row['count']}")

        # Top canonical codes
        cur.execute("""
            SELECT canonical_coverage_code, COUNT(*) as count
            FROM proposal_coverage_mapped
            WHERE mapping_status = 'MAPPED'
            GROUP BY canonical_coverage_code
            ORDER BY count DESC
            LIMIT 10;
        """)
        logger.info("\nTop 10 canonical coverage codes:")
        for row in cur.fetchall():
            logger.info(f"  {row['canonical_coverage_code']}: {row['count']} insurers")


def run_comparison_scenarios(compare_engine):
    """Run comparison scenarios A/B/C/D."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Comparison Scenarios")
    logger.info("=" * 60)

    # Scenario A: Normal comparison
    logger.info("\n--- Scenario A: 가입설계서에 있는 암진단비 비교 ---")
    try:
        result_a = compare_engine.compare(
            insurer_a='Samsung',
            insurer_b='Meritz',
            coverage_query='암진단비(유사암제외)'
        )
        logger.info(f"Result: {result_a.comparison_result.value}")
        logger.info(f"Canonical code: {result_a.canonical_coverage_code}")
        logger.info(f"Comparable slots: {result_a.comparable_slots}")
        logger.info(f"Gap slots: {result_a.gap_slots}")
        logger.info(f"Policy verification required: {result_a.policy_verification_required}")
    except Exception as e:
        logger.error(f"Scenario A failed: {e}")

    # Scenario B: Out of universe
    logger.info("\n--- Scenario B: 가입설계서에 없는 담보명 질의 ---")
    try:
        result_b = compare_engine.compare(
            insurer_a='Samsung',
            insurer_b='Meritz',
            coverage_query='특수질환진단비'  # Does not exist
        )
        logger.info(f"Result: {result_b.comparison_result.value}")
        logger.info(f"Universe status A: {result_b.universe_status_a}")
        logger.info(f"Universe status B: {result_b.universe_status_b}")
    except Exception as e:
        logger.error(f"Scenario B failed: {e}")

    # Scenario C: Try to find an UNMAPPED coverage
    logger.info("\n--- Scenario C: UNMAPPED coverage ---")
    try:
        # Query for first unmapped coverage
        with compare_engine.db.cursor() as cur:
            cur.execute("""
                SELECT u.insurer, u.normalized_name
                FROM proposal_coverage_universe u
                JOIN proposal_coverage_mapped m ON u.id = m.universe_id
                WHERE m.mapping_status = 'UNMAPPED'
                LIMIT 1;
            """)
            unmapped = cur.fetchone()

        if unmapped:
            logger.info(f"Found UNMAPPED coverage: {unmapped['normalized_name']} ({unmapped['insurer']})")
            result_c = compare_engine.compare(
                insurer_a=unmapped['insurer'],
                insurer_b='Samsung',
                coverage_query=unmapped['normalized_name']
            )
            logger.info(f"Result: {result_c.comparison_result.value}")
            logger.info(f"Gap details: {result_c.gap_details}")
        else:
            logger.info("No UNMAPPED coverages found (all mapped successfully)")

    except Exception as e:
        logger.error(f"Scenario C failed: {e}")

    # Scenario D: Comparable with gaps (always true for proposal-only data)
    logger.info("\n--- Scenario D: Comparable with gaps (disease_scope_norm NULL) ---")
    try:
        result_d = compare_engine.compare(
            insurer_a='Samsung',
            insurer_b='Meritz',
            coverage_query='암진단비(유사암제외)'
        )
        logger.info(f"Result: {result_d.comparison_result.value}")
        logger.info(f"Gap slots: {result_d.gap_slots}")
        logger.info(f"Expected gap: disease_scope_norm (NULL until policy docs processed)")
    except Exception as e:
        logger.error(f"Scenario D failed: {e}")


def main():
    """Main demo execution."""
    logger.info("=" * 60)
    logger.info("Proposal Universe Lock - Demo")
    logger.info("Constitution v1.0 + Amendment v1.0.1")
    logger.info("Slot Schema v1.1.1")
    logger.info("=" * 60)

    # Check Excel file
    if not EXCEL_PATH.exists():
        logger.error(f"Excel mapping file not found: {EXCEL_PATH}")
        logger.error("Please ensure 담보명mapping자료.xlsx exists in data/")
        sys.exit(1)

    # Connect to database
    logger.info(f"\nConnecting to database: {DB_CONFIG['dbname']}")
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

    try:
        # Initialize database
        initialize_database(conn)

        # Create pipeline
        pipeline = ProposalUniversePipeline(
            db_connection=conn,
            excel_path=EXCEL_PATH
        )

        # Create compare engine
        compare_engine = CompareEngine(conn)

        # Step 1: Ingest proposals
        all_stats = ingest_all_proposals(pipeline)

        # Step 2: Show statistics
        show_universe_stats(conn)

        # Step 3: Run comparison scenarios
        run_comparison_scenarios(compare_engine)

        logger.info("\n" + "=" * 60)
        logger.info("Demo completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        sys.exit(1)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
