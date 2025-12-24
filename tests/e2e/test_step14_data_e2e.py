"""
STEP 14: Docker Proposal Data E2E Verification

Purpose:
    Verify proposal seed data is queryable for comparison scenarios
    Foundation for future proposal-based API implementation

Scenarios:
    A: Normal comparison (삼성 vs 메리츠 일반암진단비)
    B: UNMAPPED coverage (KB 매핑안된담보)
    C: Disease scope required (삼성 유사암진단금)

DoD:
    - All scenarios return expected data from seed
    - mapping_status validation
    - disease_scope_norm validation
    - FK integrity verified
"""

import pytest
import psycopg2


@pytest.fixture(scope="module")
def db_conn():
    """Connect to Docker PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            dbname="inca_rag_final",
            user="postgres",
            password="postgres"
        )
        yield conn
        conn.close()
    except psycopg2.OperationalError:
        pytest.skip("Docker DB not running. Run scripts/step14_api_e2e_docker.sh first")


class TestScenarioA_NormalComparison:
    """
    Scenario A: 삼성 vs 메리츠 일반암진단비 비교

    Expected:
    - Both insurers: CA_DIAG_GENERAL
    - mapping_status: MAPPED
    - amount_value: exists (50M for SAMSUNG, 30M for MERITZ)
    - disease_scope_norm: NULL (no policy enrichment needed)
    """

    def test_both_insurers_exist(self, db_conn):
        """Verify both SAMSUNG and MERITZ have CA_DIAG_GENERAL"""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT u.insurer, m.canonical_coverage_code, u.amount_value
            FROM proposal_coverage_universe u
            JOIN proposal_coverage_mapped m ON u.id = m.universe_id
            WHERE u.insurer IN ('SAMSUNG', 'MERITZ')
              AND m.canonical_coverage_code = 'CA_DIAG_GENERAL'
            ORDER BY u.insurer
        """)
        results = cursor.fetchall()
        cursor.close()

        assert len(results) == 2, f"Expected 2 insurers, got {len(results)}"

        insurers = [row[0] for row in results]
        assert 'MERITZ' in insurers, "MERITZ not found"
        assert 'SAMSUNG' in insurers, "SAMSUNG not found"

    def test_mapping_status_mapped(self, db_conn):
        """Verify mapping_status is MAPPED for both"""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT u.insurer, m.mapping_status
            FROM proposal_coverage_universe u
            JOIN proposal_coverage_mapped m ON u.id = m.universe_id
            WHERE u.insurer IN ('SAMSUNG', 'MERITZ')
              AND m.canonical_coverage_code = 'CA_DIAG_GENERAL'
        """)
        results = cursor.fetchall()
        cursor.close()

        for insurer, status in results:
            assert status == 'MAPPED', f"{insurer} should have MAPPED status, got {status}"

    def test_amount_values_exist(self, db_conn):
        """Verify amount_value exists and is correct"""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT u.insurer, u.amount_value
            FROM proposal_coverage_universe u
            JOIN proposal_coverage_mapped m ON u.id = m.universe_id
            WHERE u.insurer IN ('SAMSUNG', 'MERITZ')
              AND m.canonical_coverage_code = 'CA_DIAG_GENERAL'
            ORDER BY u.insurer
        """)
        results = dict(cursor.fetchall())
        cursor.close()

        assert results['MERITZ'] == 30000000, "MERITZ amount should be 30M"
        assert results['SAMSUNG'] == 50000000, "SAMSUNG amount should be 50M"

    def test_disease_scope_norm_null(self, db_conn):
        """Verify disease_scope_norm is NULL (no policy enrichment needed)"""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT u.insurer, s.disease_scope_norm
            FROM proposal_coverage_universe u
            JOIN proposal_coverage_mapped m ON u.id = m.universe_id
            JOIN proposal_coverage_slots s ON m.id = s.mapped_id
            WHERE u.insurer IN ('SAMSUNG', 'MERITZ')
              AND m.canonical_coverage_code = 'CA_DIAG_GENERAL'
        """)
        results = cursor.fetchall()
        cursor.close()

        for insurer, disease_scope_norm in results:
            assert disease_scope_norm is None, \
                f"{insurer} should have NULL disease_scope_norm, got {disease_scope_norm}"


class TestScenarioB_UnmappedCoverage:
    """
    Scenario B: KB 매핑안된담보

    Expected:
    - mapping_status: UNMAPPED
    - canonical_coverage_code: NULL
    - Universe exists but not mapped
    """

    def test_universe_exists(self, db_conn):
        """Verify unmapped coverage exists in universe"""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT id, coverage_name_raw
            FROM proposal_coverage_universe
            WHERE insurer = 'KB'
              AND coverage_name_raw = '매핑안된담보'
        """)
        result = cursor.fetchone()
        cursor.close()

        assert result is not None, "Unmapped coverage not found in universe"

    def test_mapping_status_unmapped(self, db_conn):
        """Verify mapping_status is UNMAPPED"""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT m.mapping_status, m.canonical_coverage_code
            FROM proposal_coverage_universe u
            JOIN proposal_coverage_mapped m ON u.id = m.universe_id
            WHERE u.insurer = 'KB'
              AND u.coverage_name_raw = '매핑안된담보'
        """)
        result = cursor.fetchone()
        cursor.close()

        assert result is not None, "Mapping record not found"
        status, canonical_code = result

        assert status == 'UNMAPPED', f"Expected UNMAPPED, got {status}"
        assert canonical_code is None, f"Expected NULL canonical_code, got {canonical_code}"

    def test_no_slots_for_unmapped(self, db_conn):
        """Verify no slots exist for UNMAPPED coverage"""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM proposal_coverage_universe u
            JOIN proposal_coverage_mapped m ON u.id = m.universe_id
            LEFT JOIN proposal_coverage_slots s ON m.id = s.mapped_id
            WHERE u.insurer = 'KB'
              AND u.coverage_name_raw = '매핑안된담보'
              AND s.id IS NOT NULL
        """)
        count = cursor.fetchone()[0]
        cursor.close()

        assert count == 0, f"UNMAPPED coverage should not have slots, found {count}"


class TestScenarioC_DiseaseScopeRequired:
    """
    Scenario C: 삼성 유사암진단금 보장범위

    Expected:
    - CA_DIAG_SIMILAR
    - disease_scope_norm: NOT NULL
    - disease_code_group referenced
    - source_confidence: policy_required
    """

    def test_canonical_code_similar(self, db_conn):
        """Verify canonical_coverage_code is CA_DIAG_SIMILAR"""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT m.canonical_coverage_code
            FROM proposal_coverage_universe u
            JOIN proposal_coverage_mapped m ON u.id = m.universe_id
            WHERE u.insurer = 'SAMSUNG'
              AND u.coverage_name_raw = '유사암진단금'
        """)
        result = cursor.fetchone()
        cursor.close()

        assert result is not None, "SAMSUNG 유사암진단금 not found"
        canonical_code = result[0]
        assert canonical_code == 'CA_DIAG_SIMILAR', \
            f"Expected CA_DIAG_SIMILAR, got {canonical_code}"

    def test_disease_scope_norm_exists(self, db_conn):
        """Verify disease_scope_norm is NOT NULL"""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT s.disease_scope_norm
            FROM proposal_coverage_universe u
            JOIN proposal_coverage_mapped m ON u.id = m.universe_id
            JOIN proposal_coverage_slots s ON m.id = s.mapped_id
            WHERE u.insurer = 'SAMSUNG'
              AND m.canonical_coverage_code = 'CA_DIAG_SIMILAR'
        """)
        result = cursor.fetchone()
        cursor.close()

        assert result is not None, "Slots not found for CA_DIAG_SIMILAR"
        disease_scope_norm = result[0]

        assert disease_scope_norm is not None, \
            "disease_scope_norm should NOT be NULL for CA_DIAG_SIMILAR"
        assert 'include_group_id' in disease_scope_norm, \
            "disease_scope_norm should have include_group_id"

    def test_disease_group_exists(self, db_conn):
        """Verify disease_code_group exists for SAMSUNG"""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT group_id, group_name, insurer
            FROM disease_code_group
            WHERE insurer = 'SAMSUNG'
        """)
        result = cursor.fetchone()
        cursor.close()

        assert result is not None, "SAMSUNG disease group not found"
        group_id, group_name, group_insurer = result

        assert group_id is not None, "group_id should not be NULL"
        assert '유사암' in group_name, f"Expected 유사암 in group name, got {group_name}"
        assert group_insurer == 'SAMSUNG', \
            f"Expected SAMSUNG, got {group_insurer}"

    def test_source_confidence_policy_required(self, db_conn):
        """Verify source_confidence is policy_required"""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT s.source_confidence
            FROM proposal_coverage_universe u
            JOIN proposal_coverage_mapped m ON u.id = m.universe_id
            JOIN proposal_coverage_slots s ON m.id = s.mapped_id
            WHERE u.insurer = 'SAMSUNG'
              AND m.canonical_coverage_code = 'CA_DIAG_SIMILAR'
        """)
        result = cursor.fetchone()
        cursor.close()

        assert result is not None, "Slots not found"
        source_confidence = result[0]

        assert source_confidence == 'policy_required', \
            f"Expected 'policy_required', got '{source_confidence}'"


class TestUniverseLockPrinciple:
    """Verify Universe Lock principle compliance"""

    def test_all_comparisons_from_universe(self, db_conn):
        """Verify all mapped coverages exist in universe"""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM proposal_coverage_mapped m
            LEFT JOIN proposal_coverage_universe u ON m.universe_id = u.id
            WHERE u.id IS NULL
        """)
        orphan_count = cursor.fetchone()[0]
        cursor.close()

        assert orphan_count == 0, \
            f"Found {orphan_count} mapped coverages not in universe (Universe Lock violation)"

    def test_no_product_based_comparison(self, db_conn):
        """Verify no product_coverage table exists (Constitutional violation)"""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = 'product_coverage'
        """)
        count = cursor.fetchone()[0]
        cursor.close()

        assert count == 0, \
            "product_coverage table should not exist (Universe Lock principle)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
