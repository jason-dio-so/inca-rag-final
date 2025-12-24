"""
End-to-End Tests for Proposal Universe Lock System

Test Scenarios (from 4번 지시문):
A. 가입설계서에 있는 암진단비 비교 → 정상
B. 가입설계서에 없는 담보명 질의 → out_of_universe
C. 가입설계서에는 있으나 Excel 매핑 실패 → unmapped
D. 같은 canonical code지만 disease_scope_norm 없음 → comparable_with_gaps
"""

import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from proposal_universe import (
    ProposalCoverageParser,
    CoverageMapper,
    SlotExtractor,
    CompareEngine,
    ComparisonResult
)
from proposal_universe.pipeline import ProposalUniversePipeline


# Test configuration
TEST_DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5432,
}

TEST_EXCEL_PATH = Path(__file__).parent.parent / 'data' / '담보명mapping자료.xlsx'


@pytest.fixture
def db_connection():
    """Create test database connection."""
    conn = psycopg2.connect(**TEST_DB_CONFIG, cursor_factory=RealDictCursor)
    yield conn
    conn.close()


@pytest.fixture
def pipeline(db_connection):
    """Create pipeline instance."""
    return ProposalUniversePipeline(
        db_connection=db_connection,
        excel_path=TEST_EXCEL_PATH
    )


@pytest.fixture
def compare_engine(db_connection):
    """Create compare engine instance."""
    return CompareEngine(db_connection)


class TestScenarioA:
    """
    Scenario A: 가입설계서에 있는 암진단비 비교 → 정상

    Expected: comparable or comparable_with_gaps
    """

    def test_cancer_diagnosis_samsung_vs_meritz(
        self,
        pipeline,
        compare_engine
    ):
        """Test normal comparison of existing coverage."""

        # Ingest Samsung proposal
        samsung_proposal = Path(__file__).parent.parent / 'data' / 'samsung' / '가입설계서' / '삼성_가입설계서_2511.pdf'
        if samsung_proposal.exists():
            stats_samsung = pipeline.ingest_proposal('Samsung', samsung_proposal)
            assert stats_samsung['total_coverages'] > 0
            assert stats_samsung['mapping_status']['MAPPED'] > 0

        # Ingest Meritz proposal
        meritz_proposal = Path(__file__).parent.parent / 'data' / 'meritz' / '가입설계서' / '메리츠_가입설계서_2511.pdf'
        if meritz_proposal.exists():
            stats_meritz = pipeline.ingest_proposal('Meritz', meritz_proposal)
            assert stats_meritz['total_coverages'] > 0

        # Compare: 암진단비
        result = compare_engine.compare(
            insurer_a='Samsung',
            insurer_b='Meritz',
            coverage_query='암진단비(유사암제외)'
        )

        # Assertions
        assert result.comparison_result.value in ['comparable', 'comparable_with_gaps']
        assert result.universe_status_a == 'in_universe'
        assert result.universe_status_b == 'in_universe'
        assert result.canonical_coverage_code is not None

        # Should have some comparable slots
        assert len(result.comparable_slots) > 0

        # Print result
        print(f"\n=== Scenario A Result ===")
        print(f"State: {result.comparison_result.value}")
        print(f"Canonical: {result.canonical_coverage_code}")
        print(f"Comparable slots: {result.comparable_slots}")
        print(f"Gap slots: {result.gap_slots}")


class TestScenarioB:
    """
    Scenario B: 가입설계서에 없는 담보명 질의 → out_of_universe

    Expected: out_of_universe
    """

    def test_nonexistent_coverage(
        self,
        pipeline,
        compare_engine
    ):
        """Test query for coverage not in proposal."""

        # Ingest Samsung proposal
        samsung_proposal = Path(__file__).parent.parent / 'data' / 'samsung' / '가입설계서' / '삼성_가입설계서_2511.pdf'
        if samsung_proposal.exists():
            pipeline.ingest_proposal('Samsung', samsung_proposal)

        # Query for non-existent coverage
        result = compare_engine.compare(
            insurer_a='Samsung',
            insurer_b='Meritz',
            coverage_query='특수질환진단비'  # This does not exist in proposals
        )

        # Assertions
        assert result.comparison_result.value == 'out_of_universe'
        assert result.universe_status_a == 'out_of_universe' or \
               result.universe_status_b == 'out_of_universe'
        assert result.canonical_coverage_code is None

        # Print result
        print(f"\n=== Scenario B Result ===")
        print(f"State: {result.comparison_result.value}")
        print(f"Universe A: {result.universe_status_a}")
        print(f"Universe B: {result.universe_status_b}")


class TestScenarioC:
    """
    Scenario C: 가입설계서에는 있으나 Excel 매핑 실패 → unmapped

    Expected: unmapped
    """

    def test_unmapped_coverage(self, db_connection):
        """Test coverage that exists in proposal but not in Excel."""

        # Create mock coverage in universe without Excel entry
        mock_coverage = {
            'insurer': 'TestInsurer',
            'proposal_id': 'test_proposal_001',
            'insurer_coverage_name': '희귀질환특별진단비',  # Assume not in Excel
            'normalized_name': '희귀질환특별진단비',
            'currency': 'KRW',
            'amount_value': 10000000,
            'payout_amount_unit': 'lump_sum',
            'source_page': 1,
            'span_text': '희귀질환특별진단비 1,000만원',
            'content_hash': 'test_unmapped_coverage_001',
        }

        # Insert directly into universe
        with db_connection.cursor() as cur:
            cur.execute("""
                INSERT INTO proposal_coverage_universe
                (insurer, proposal_id, insurer_coverage_name, normalized_name,
                 currency, amount_value, payout_amount_unit, source_page, span_text, content_hash)
                VALUES (%(insurer)s, %(proposal_id)s, %(insurer_coverage_name)s, %(normalized_name)s,
                        %(currency)s, %(amount_value)s, %(payout_amount_unit)s, %(source_page)s,
                        %(span_text)s, %(content_hash)s)
                RETURNING id;
            """, mock_coverage)
            universe_id = cur.fetchone()['id']

            # Insert mapping with UNMAPPED status
            cur.execute("""
                INSERT INTO proposal_coverage_mapped
                (universe_id, canonical_coverage_code, mapping_status, mapping_evidence)
                VALUES (%s, NULL, 'UNMAPPED', %s);
            """, (universe_id, '{"reason": "no_match_found"}'))

            db_connection.commit()

        # Compare
        compare_engine = CompareEngine(db_connection)
        result = compare_engine.compare(
            insurer_a='TestInsurer',
            insurer_b='Samsung',
            coverage_query='희귀질환특별진단비'
        )

        # Assertions
        assert result.comparison_result.value == 'unmapped'
        assert result.universe_status_a == 'in_universe'

        # Print result
        print(f"\n=== Scenario C Result ===")
        print(f"State: {result.comparison_result.value}")
        print(f"Gap details: {result.gap_details}")


class TestScenarioD:
    """
    Scenario D: 같은 canonical code지만 disease_scope_norm 없음 → comparable_with_gaps

    Expected: comparable_with_gaps with disease_scope_norm in gap_slots
    """

    def test_comparable_with_gaps(
        self,
        pipeline,
        compare_engine
    ):
        """Test comparison with disease_scope_norm gap."""

        # Ingest proposals (disease_scope_norm will be NULL)
        samsung_proposal = Path(__file__).parent.parent / 'data' / 'samsung' / '가입설계서' / '삼성_가입설계서_2511.pdf'
        meritz_proposal = Path(__file__).parent.parent / 'data' / 'meritz' / '가입설계서' / '메리츠_가입설계서_2511.pdf'

        if samsung_proposal.exists():
            pipeline.ingest_proposal('Samsung', samsung_proposal)

        if meritz_proposal.exists():
            pipeline.ingest_proposal('Meritz', meritz_proposal)

        # Compare
        result = compare_engine.compare(
            insurer_a='Samsung',
            insurer_b='Meritz',
            coverage_query='암진단비(유사암제외)'
        )

        # Assertions
        assert result.comparison_result.value == 'comparable_with_gaps'
        assert 'disease_scope_norm' in result.gap_slots
        assert result.policy_verification_required is True
        assert result.canonical_coverage_code is not None

        # Print result
        print(f"\n=== Scenario D Result ===")
        print(f"State: {result.comparison_result.value}")
        print(f"Canonical: {result.canonical_coverage_code}")
        print(f"Gap slots: {result.gap_slots}")
        print(f"Policy verification: {result.policy_verification_required}")


class TestParserUnit:
    """Unit tests for ProposalCoverageParser."""

    def test_normalize_name(self):
        """Test name normalization."""
        parser = ProposalCoverageParser('Test', Path('test.pdf'))

        assert parser._normalize_name('암 진단비 (유사암 제외)') == '암진단비(유사암제외)'
        assert parser._normalize_name('  유사암   진단비  ') == '유사암진단비'

    def test_parse_amount(self):
        """Test amount parsing."""
        parser = ProposalCoverageParser('Test', Path('test.pdf'))

        assert parser._parse_amount('3,000만원') == 30000000
        assert parser._parse_amount('600만원') == 6000000
        assert parser._parse_amount('5만원') == 50000


class TestMapperUnit:
    """Unit tests for CoverageMapper."""

    def test_mapping_logic(self):
        """Test mapping logic with mock Excel data."""
        # This would require a test Excel file
        # Skip if TEST_EXCEL_PATH doesn't exist
        if not TEST_EXCEL_PATH.exists():
            pytest.skip("Excel mapping file not found")

        mapper = CoverageMapper(TEST_EXCEL_PATH)
        stats = mapper.get_stats()

        assert stats['total_aliases'] > 0
        assert stats['unique_canonical_codes'] > 0


class TestExtractorUnit:
    """Unit tests for SlotExtractor."""

    def test_waiting_period_extraction(self):
        """Test waiting period extraction."""
        extractor = SlotExtractor()

        assert extractor._extract_waiting_period('보장개시일 90일 후') == 90
        assert extractor._extract_waiting_period('보장개시일부터') == 0
        assert extractor._extract_waiting_period('즉시 보장') is None

    def test_reduction_period_extraction(self):
        """Test reduction period extraction."""
        extractor = SlotExtractor()

        periods = extractor._extract_reduction_periods('1년50%')
        assert periods is not None
        assert len(periods) == 1
        assert periods[0]['rate'] == 0.5

        assert extractor._extract_reduction_periods('감액 없음') == []
        assert extractor._extract_reduction_periods('일반 보장') is None

    def test_renewal_extraction(self):
        """Test renewal flag extraction."""
        extractor = SlotExtractor()

        assert extractor._extract_renewal_flag('[갱신형] 치료비') is True
        assert extractor._extract_renewal_flag('일반 진단비') is False

        assert extractor._extract_renewal_period('10년갱신') == 10


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
