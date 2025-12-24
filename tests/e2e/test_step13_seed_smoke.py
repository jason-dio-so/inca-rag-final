"""
STEP 13 Seed Data Smoke Test

Purpose:
    Verify that seed_step13_minimal.sql meets all DoD requirements

Requirements:
    1. Docker DB successfully loaded
    2. 3 insurers (SAMSUNG, MERITZ, KB)
    3. proposal_coverage_universe ≥ 3 records
    4. MAPPED + UNMAPPED mapping states both exist
    5. disease_scope_norm NULL + NOT NULL both exist
    6. Proposal evidence exists for all slots
    7. No slots without proposal evidence
"""

import pytest
import psycopg2
import os


@pytest.fixture(scope="module")
def db_conn():
    """Connect to Docker PostgreSQL database"""
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        dbname="inca_rag_final",
        user="postgres",
        password="postgres"
    )
    yield conn
    conn.close()


def test_insurers_count(db_conn):
    """DoD 2: Verify 3 insurers exist"""
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM insurer")
    count = cursor.fetchone()[0]
    cursor.close()

    assert count == 3, f"Expected 3 insurers, got {count}"


def test_insurers_names(db_conn):
    """DoD 2: Verify correct insurer codes"""
    cursor = db_conn.cursor()
    cursor.execute("SELECT insurer_code FROM insurer ORDER BY insurer_code")
    codes = [row[0] for row in cursor.fetchall()]
    cursor.close()

    expected = ['KB', 'MERITZ', 'SAMSUNG']
    assert codes == expected, f"Expected {expected}, got {codes}"


def test_universe_min_count(db_conn):
    """DoD 3: Verify proposal_coverage_universe has at least 3 records"""
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM proposal_coverage_universe")
    count = cursor.fetchone()[0]
    cursor.close()

    assert count >= 3, f"Expected at least 3 universe records, got {count}"


def test_mapping_states_exist(db_conn):
    """DoD 4: Verify both MAPPED and UNMAPPED states exist"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT mapping_status, COUNT(*)
        FROM proposal_coverage_mapped
        GROUP BY mapping_status
        ORDER BY mapping_status
    """)
    results = dict(cursor.fetchall())
    cursor.close()

    assert 'MAPPED' in results, "MAPPED status not found"
    assert 'UNMAPPED' in results, "UNMAPPED status not found"
    assert results['MAPPED'] >= 1, "At least 1 MAPPED record required"
    assert results['UNMAPPED'] >= 1, "At least 1 UNMAPPED record required"


def test_disease_scope_null_exists(db_conn):
    """DoD 5: Verify disease_scope_norm NULL exists"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM proposal_coverage_slots
        WHERE disease_scope_norm IS NULL
    """)
    count = cursor.fetchone()[0]
    cursor.close()

    assert count >= 1, f"Expected at least 1 NULL disease_scope_norm, got {count}"


def test_disease_scope_not_null_exists(db_conn):
    """DoD 5: Verify disease_scope_norm NOT NULL exists"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM proposal_coverage_slots
        WHERE disease_scope_norm IS NOT NULL
    """)
    count = cursor.fetchone()[0]
    cursor.close()

    assert count >= 1, f"Expected at least 1 NOT NULL disease_scope_norm, got {count}"


def test_proposal_evidence_required(db_conn):
    """DoD 6: Verify all slots have proposal evidence"""
    cursor = db_conn.cursor()

    # Check that meta contains evidence with document_id
    cursor.execute("""
        SELECT COUNT(*)
        FROM proposal_coverage_slots
        WHERE meta IS NULL
           OR NOT (meta ? 'evidence')
           OR NOT (meta->'evidence' ? 'document_id')
    """)
    count_without_evidence = cursor.fetchone()[0]
    cursor.close()

    assert count_without_evidence == 0, f"Found {count_without_evidence} slots without proposal evidence"


def test_no_slots_without_universe_link(db_conn):
    """DoD 7: Verify all slots link to valid universe records"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM proposal_coverage_slots s
        JOIN proposal_coverage_mapped m ON s.mapped_id = m.id
        JOIN proposal_coverage_universe u ON m.universe_id = u.id
    """)
    slots_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM proposal_coverage_slots")
    total_slots = cursor.fetchone()[0]
    cursor.close()

    assert slots_count == total_slots, \
        f"Universe link mismatch: {slots_count} linked vs {total_slots} total"


def test_canonical_codes_exist(db_conn):
    """Verify coverage_standard has canonical codes"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT coverage_code
        FROM coverage_standard
        ORDER BY coverage_code
    """)
    codes = [row[0] for row in cursor.fetchall()]
    cursor.close()

    assert 'CA_DIAG_GENERAL' in codes, "CA_DIAG_GENERAL not found in coverage_standard"
    assert 'CA_DIAG_SIMILAR' in codes, "CA_DIAG_SIMILAR not found in coverage_standard"


def test_disease_code_group_exists(db_conn):
    """Verify disease code group exists for SAMSUNG similar cancer"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM disease_code_group
        WHERE insurer = 'SAMSUNG'
    """)
    count = cursor.fetchone()[0]
    cursor.close()

    assert count >= 1, "No disease code group found for SAMSUNG"


def test_disease_code_group_members_exist(db_conn):
    """Verify disease code group has members"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM disease_code_group_member
    """)
    count = cursor.fetchone()[0]
    cursor.close()

    assert count >= 1, "No disease code group members found"


def test_coverage_disease_scope_exists(db_conn):
    """Verify coverage_disease_scope exists for CA_DIAG_SIMILAR"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM coverage_disease_scope
        WHERE coverage_code = 'CA_DIAG_SIMILAR'
          AND insurer = 'SAMSUNG'
    """)
    count = cursor.fetchone()[0]
    cursor.close()

    assert count >= 1, "No coverage_disease_scope found for SAMSUNG CA_DIAG_SIMILAR"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
