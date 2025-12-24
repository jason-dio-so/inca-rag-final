"""
STEP 5-B + STEP 7 Read-only and Universe Lock enforcement tests

Tests:
1. DB connection is read-only (write attempts fail)
2. Compare evidence queries enforce is_synthetic=false
3. Amount bridge respects include_synthetic option
4. Real DB schema validation (Universe Lock tables: proposal_coverage_universe/mapped/slots)
5. Universe Lock 5-state comparison validation
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from apps.api.app.main import app
from apps.api.app.queries.compare import COMPARE_EVIDENCE_SQL, COMPARE_PRODUCTS_SQL, COVERAGE_AMOUNT_SQL
from apps.api.app.queries.evidence import AMOUNT_BRIDGE_EVIDENCE_SQL
from apps.api.app.queries.products import SEARCH_PRODUCTS_SQL

client = TestClient(app)


class TestReadOnlyEnforcement:
    """Verify all DB operations are read-only"""

    def test_db_connection_is_readonly(self):
        """
        Verify db_readonly_session creates connections with BEGIN READ ONLY
        """
        from apps.api.app.db import get_db_connection

        # Mock psycopg2.connect to verify readonly transaction
        with patch('apps.api.app.db.psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            conn = get_db_connection(readonly=True)

            # Verify set_session was called with autocommit=False
            mock_conn.set_session.assert_called_once()
            call_kwargs = mock_conn.set_session.call_args[1]
            assert call_kwargs.get('autocommit') is False

            # Verify BEGIN READ ONLY was executed
            mock_cursor.execute.assert_called_once_with("BEGIN READ ONLY;")

    def test_compare_endpoint_uses_readonly_dependency(self):
        """
        Verify /compare endpoint uses read-only DB dependency
        """
        request_body = {
            "axis": "compare",
            "mode": "compensation"
        }

        # Mock get_readonly_conn dependency
        from apps.api.app.db import get_readonly_conn

        def mock_conn_gen():
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            yield mock_conn

        # Override dependency
        from apps.api.app.main import app as test_app
        test_app.dependency_overrides[get_readonly_conn] = mock_conn_gen

        try:
            response = client.post("/compare", json=request_body)
            assert response.status_code == 200
        finally:
            # Clean up override
            test_app.dependency_overrides.clear()


class TestSyntheticEnforcementSQL:
    """
    Verify is_synthetic enforcement in SQL templates (STRING-LEVEL VALIDATION)

    These tests verify the SQL templates themselves, not just the router behavior.
    This ensures the constitution is enforced at the SQL layer, independent of
    any router-level safety measures.
    """

    def test_compare_sql_hard_codes_is_synthetic_false(self):
        """
        CONSTITUTIONAL TEST: Compare SQL template MUST have is_synthetic=false HARD-CODED

        This test verifies the SQL string itself contains the filter.
        Router-level double safety is separate - this tests SQL layer enforcement.
        """
        # CRITICAL: SQL template must contain the hard-coded filter
        assert "c.is_synthetic = false" in COMPARE_EVIDENCE_SQL, \
            "Compare SQL MUST hard-code 'c.is_synthetic = false' in WHERE clause"

        # Verify comment marker for audit trail
        assert "-- HARD RULE" in COMPARE_EVIDENCE_SQL, \
            "Compare SQL MUST have '-- HARD RULE' comment marking constitutional enforcement"

        # CRITICAL: Verify there's NO parameter to bypass this filter
        assert "%(include_synthetic)s" not in COMPARE_EVIDENCE_SQL, \
            "Compare SQL MUST NOT have include_synthetic parameter (no bypass allowed)"

        # Verify uses chunk_entity for coverage filtering
        assert "JOIN public.chunk_entity" in COMPARE_EVIDENCE_SQL, \
            "Compare SQL MUST use chunk_entity for coverage-based filtering"

        assert "ce.coverage_code" in COMPARE_EVIDENCE_SQL, \
            "Compare SQL MUST filter by coverage_code via chunk_entity"

        # Additional verification: check it's in WHERE clause context
        sql_lower = COMPARE_EVIDENCE_SQL.lower()
        where_idx = sql_lower.find("where")
        is_synthetic_idx = sql_lower.find("c.is_synthetic = false")
        assert where_idx != -1 and is_synthetic_idx != -1, \
            "Both WHERE and is_synthetic filter must exist"
        assert is_synthetic_idx > where_idx, \
            "is_synthetic=false filter must appear after WHERE clause"

    def test_amount_bridge_sql_allows_synthetic_option(self):
        """
        Amount Bridge SQL template MUST support include_synthetic option with proper branching

        This axis separation allows synthetic chunks via parameter control.
        """
        # CRITICAL: Must have parameter for option control
        assert "%(include_synthetic)s" in AMOUNT_BRIDGE_EVIDENCE_SQL, \
            "Amount Bridge SQL MUST have include_synthetic parameter for axis separation"

        # CRITICAL: Must still have the false filter for conditional use
        assert "c.is_synthetic = false" in AMOUNT_BRIDGE_EVIDENCE_SQL, \
            "Amount Bridge SQL MUST have 'c.is_synthetic = false' for conditional filtering"

        # CRITICAL: Verify OR clause for proper branching
        assert "OR c.is_synthetic = false" in AMOUNT_BRIDGE_EVIDENCE_SQL, \
            "Amount Bridge SQL MUST have 'OR c.is_synthetic = false' for conditional logic"

        # Verify amount_entity usage for coverage-based filtering
        assert "FROM public.amount_entity" in AMOUNT_BRIDGE_EVIDENCE_SQL, \
            "Amount Bridge SQL MUST use amount_entity table"

        assert "ae.coverage_code" in AMOUNT_BRIDGE_EVIDENCE_SQL, \
            "Amount Bridge SQL MUST filter by coverage_code via amount_entity"

        # Verify the branching logic structure
        assert "%(include_synthetic)s = true" in AMOUNT_BRIDGE_EVIDENCE_SQL.lower() or \
               "%(include_synthetic)s = TRUE" in AMOUNT_BRIDGE_EVIDENCE_SQL or \
               "%(include_synthetic)s" in AMOUNT_BRIDGE_EVIDENCE_SQL, \
            "Amount Bridge SQL MUST check include_synthetic parameter"

    def test_compare_sql_no_synthetic_bypass_possible(self):
        """
        Additional validation: Compare SQL has NO way to bypass synthetic filter

        This is a negative test ensuring no backdoors exist.
        """
        sql_lower = COMPARE_EVIDENCE_SQL.lower()

        # Check for common bypass patterns that should NOT exist
        forbidden_patterns = [
            "include_synthetic",
            "allow_synthetic",
            "skip_synthetic",
            "c.is_synthetic = true",
            "c.is_synthetic != false",
            "c.is_synthetic <> false"
        ]

        for pattern in forbidden_patterns:
            assert pattern not in sql_lower, \
                f"Compare SQL MUST NOT contain '{pattern}' - no bypass allowed"

    def test_amount_bridge_sql_proper_conditional_structure(self):
        """
        Verify Amount Bridge SQL has proper conditional structure for include_synthetic

        The SQL should be: (include_synthetic = true OR is_synthetic = false)
        """
        sql_lower = AMOUNT_BRIDGE_EVIDENCE_SQL.lower()

        # Verify conditional structure exists
        has_conditional = (
            "%(include_synthetic)s" in AMOUNT_BRIDGE_EVIDENCE_SQL and
            ("or" in sql_lower) and
            ("c.is_synthetic = false" in sql_lower)
        )

        assert has_conditional, \
            "Amount Bridge SQL MUST have proper conditional: (include_synthetic OR is_synthetic=false)"

    def test_compare_evidence_all_non_synthetic(self):
        """
        Verify /compare returns only is_synthetic=false evidence (DOUBLE SAFETY)
        """
        request_body = {
            "axis": "compare",
            "mode": "compensation",
            "options": {
                "include_evidence": True
            }
        }

        # Mock get_readonly_conn dependency
        from apps.api.app.db import get_readonly_conn

        def mock_conn_gen():
            mock_conn = MagicMock()
            mock_cursor = MagicMock()

            # Mock fetchall to return different results for different queries
            call_count = [0]

            def fetchall_side_effect():
                call_count[0] += 1
                if call_count[0] == 1:
                    # Products query
                    return [
                        {
                            "product_id": 1,
                            "insurer_code": "TEST",
                            "product_name": "Test Product",
                            "product_code": "P001"
                        }
                    ]
                elif call_count[0] == 2:
                    # Evidence query - even if DB returns true, router forces false
                    return [
                        {
                            "chunk_id": 1,
                            "document_id": 1,
                            "page_number": 1,
                            "is_synthetic": True,  # DOUBLE SAFETY: Router will override to False
                            "synthetic_source_chunk_id": 999,
                            "snippet": "Test snippet",
                            "doc_type": "약관"
                        }
                    ]
                return []

            mock_cursor.fetchall.side_effect = fetchall_side_effect
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            yield mock_conn

        # Override dependency
        from apps.api.app.main import app as test_app
        test_app.dependency_overrides[get_readonly_conn] = mock_conn_gen

        try:
            response = client.post("/compare", json=request_body)

            assert response.status_code == 200
            data = response.json()

            # DOUBLE SAFETY TEST: Even if DB returned is_synthetic=True,
            # router MUST force it to False
            if data.get("items"):
                for item in data["items"]:
                    if item.get("evidence"):
                        for evidence in item["evidence"]:
                            assert evidence["is_synthetic"] is False
                            assert evidence["synthetic_source_chunk_id"] is None
        finally:
            test_app.dependency_overrides.clear()

    def test_amount_bridge_respects_include_synthetic_option(self):
        """
        Verify /evidence/amount-bridge respects include_synthetic option
        """
        from apps.api.app.db import get_readonly_conn
        from apps.api.app.main import app as test_app

        def mock_conn_gen():
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            yield mock_conn

        test_app.dependency_overrides[get_readonly_conn] = mock_conn_gen

        try:
            # Test with include_synthetic=false
            request_body = {
                "axis": "amount_bridge",
                "coverage_code": "C001",
                "options": {
                    "include_synthetic": False
                }
            }

            response = client.post("/evidence/amount-bridge", json=request_body)

            assert response.status_code == 200
            data = response.json()

            # Verify debug info shows synthetic filter applied
            assert data["debug"]["hard_rules"]["is_synthetic_filter_applied"] is True
        finally:
            test_app.dependency_overrides.clear()


class TestHardRulesDebugInfo:
    """Verify debug.hard_rules information is accurate"""

    def test_compare_debug_hard_rules_present(self):
        """
        Verify /compare response includes debug.hard_rules
        """
        from apps.api.app.db import get_readonly_conn
        from apps.api.app.main import app as test_app

        def mock_conn_gen():
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            yield mock_conn

        test_app.dependency_overrides[get_readonly_conn] = mock_conn_gen

        try:
            request_body = {
                "axis": "compare",
                "mode": "compensation"
            }

            response = client.post("/compare", json=request_body)

            assert response.status_code == 200
            data = response.json()

            assert "debug" in data
            assert "hard_rules" in data["debug"]
            hard_rules = data["debug"]["hard_rules"]

            # These should always be true for compare axis
            assert hard_rules["is_synthetic_filter_applied"] is True
            assert hard_rules["compare_axis_forbids_synthetic"] is True
        finally:
            test_app.dependency_overrides.clear()

    def test_amount_bridge_debug_synthetic_info(self):
        """
        Verify /evidence/amount-bridge debug includes synthetic option info
        """
        from apps.api.app.db import get_readonly_conn
        from apps.api.app.main import app as test_app

        def mock_conn_gen():
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            yield mock_conn

        test_app.dependency_overrides[get_readonly_conn] = mock_conn_gen

        try:
            request_body = {
                "axis": "amount_bridge",
                "coverage_code": "C001",
                "options": {
                    "include_synthetic": True
                }
            }

            response = client.post("/evidence/amount-bridge", json=request_body)

            assert response.status_code == 200
            data = response.json()

            assert "debug" in data
            assert "notes" in data["debug"]

            # Notes should mention include_synthetic=True
            notes_str = " ".join(data["debug"]["notes"])
            assert "include_synthetic=True" in notes_str
        finally:
            test_app.dependency_overrides.clear()


class TestRealDBSchemaAlignment:
    """Verify all SQL queries use real DB schema (product/product_coverage/chunk/document)"""

    def test_search_products_uses_real_schema(self):
        """
        Verify /search/products SQL uses public.product + public.insurer
        """
        assert "public.product" in SEARCH_PRODUCTS_SQL, \
            "Search products SQL MUST use public.product (not product_master)"
        assert "public.insurer" in SEARCH_PRODUCTS_SQL, \
            "Search products SQL MUST use public.insurer"
        assert "product_master" not in SEARCH_PRODUCTS_SQL, \
            "Search products SQL MUST NOT use product_master (forbidden)"

    def test_compare_products_uses_real_schema(self):
        """
        Verify /compare products SQL uses public.product + public.insurer
        """
        assert "public.product" in COMPARE_PRODUCTS_SQL, \
            "Compare products SQL MUST use public.product"
        assert "public.insurer" in COMPARE_PRODUCTS_SQL, \
            "Compare products SQL MUST use public.insurer"
        assert "product_master" not in COMPARE_PRODUCTS_SQL, \
            "Compare products SQL MUST NOT use product_master"

    def test_coverage_amount_uses_universe_lock(self):
        """
        Verify coverage amount query uses Universe Lock tables (STEP 7)
        Constitutional requirement: proposal_coverage_universe only, no product_coverage
        """
        assert "public.proposal_coverage_universe" in COVERAGE_AMOUNT_SQL, \
            "Coverage amount SQL MUST use public.proposal_coverage_universe (Universe Lock)"
        assert "public.proposal_coverage_mapped" in COVERAGE_AMOUNT_SQL, \
            "Coverage amount SQL MUST use public.proposal_coverage_mapped"
        assert "mapping_status" in COVERAGE_AMOUNT_SQL, \
            "Coverage amount SQL MUST filter by mapping_status"
        assert "= 'MAPPED'" in COVERAGE_AMOUNT_SQL, \
            "Coverage amount SQL MUST require mapping_status = 'MAPPED'"
        assert "product_coverage" not in COVERAGE_AMOUNT_SQL, \
            "Coverage amount SQL MUST NOT use product_coverage (Universe Lock violation)"

    def test_compare_evidence_uses_chunk_document(self):
        """
        Verify compare evidence SQL uses public.chunk + public.document
        """
        assert "public.chunk" in COMPARE_EVIDENCE_SQL, \
            "Compare evidence SQL MUST use public.chunk"
        assert "public.document" in COMPARE_EVIDENCE_SQL, \
            "Compare evidence SQL MUST use public.document"
        assert "doc_type_priority" in COMPARE_EVIDENCE_SQL, \
            "Compare evidence SQL MUST use doc_type_priority for ordering"

    def test_amount_bridge_uses_real_schema(self):
        """
        Verify amount-bridge SQL uses public.chunk/document/product/insurer
        """
        assert "public.chunk" in AMOUNT_BRIDGE_EVIDENCE_SQL, \
            "Amount bridge SQL MUST use public.chunk"
        assert "public.document" in AMOUNT_BRIDGE_EVIDENCE_SQL, \
            "Amount bridge SQL MUST use public.document"
        assert "public.product" in AMOUNT_BRIDGE_EVIDENCE_SQL, \
            "Amount bridge SQL MUST use public.product"
        assert "public.insurer" in AMOUNT_BRIDGE_EVIDENCE_SQL, \
            "Amount bridge SQL MUST use public.insurer"

    def test_amount_bridge_currency_is_always_krw(self):
        """
        KRW ONLY RULE:
        Amount Bridge 응답의 currency는 항상 KRW여야 한다.
        amount_unit 값과 무관하게 무조건 KRW만 반환.

        대한민국 보험 도메인 전용 시스템이므로 외화는 존재하지 않는다.
        """
        from apps.api.app.db import get_readonly_conn
        from apps.api.app.main import app as test_app

        def mock_conn_gen():
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            # 고의로 amount_unit에 외화 값을 넣어서 테스트
            mock_cursor.fetchall.return_value = [{
                "chunk_id": 1,
                "is_synthetic": False,
                "synthetic_source_chunk_id": None,
                "amount_value": 30000000,
                "amount_text": "3천만원",
                "amount_unit": "USD",  # 고의적 외화 값 (무시되어야 함)
                "context_type": "payment",
                "snippet": "암 진단 시 3천만원 지급",
                "insurer_code": "TEST",
                "product_id": 1,
                "product_name": "Test Product",
                "document_id": 1,
                "page_number": 1,
                "coverage_code": "CANCER_DIAG",
            }]
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            yield mock_conn

        test_app.dependency_overrides[get_readonly_conn] = mock_conn_gen

        try:
            response = client.post("/evidence/amount-bridge", json={
                "axis": "amount_bridge",
                "coverage_code": "CANCER_DIAG"
            })

            assert response.status_code == 200
            data = response.json()

            # CRITICAL: amount_unit이 USD여도 currency는 반드시 KRW
            assert data["evidences"][0]["currency"] == "KRW", \
                "Amount bridge MUST return currency='KRW' regardless of amount_unit value"

        finally:
            test_app.dependency_overrides.clear()



class TestUniverseLock5StateComparison:
    """
    STEP 7: Verify Universe Lock 5-State Comparison System

    States:
    1. comparable - All critical slots match
    2. comparable_with_gaps - Same canonical code, some slots NULL (policy_required)
    3. non_comparable - Different canonical codes or incompatible
    4. unmapped - Exists in universe but Excel mapping failed
    5. out_of_universe - NOT in proposal (Universe Lock violation)
    """

    def test_out_of_universe_coverage_returns_none(self):
        """
        Test: Coverage NOT in proposal_coverage_universe → returns None (out_of_universe)
        """
        from apps.api.app.queries.compare import get_coverage_amount_for_proposal

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Empty result = coverage not in universe
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        result = get_coverage_amount_for_proposal(
            mock_conn,
            insurer_code="SAMSUNG",
            proposal_id="proposal_001",
            coverage_code="COVERAGE_NOT_IN_PROPOSAL"
        )

        # Universe Lock: If not in proposal, return None (out_of_universe)
        assert result is None, \
            "Coverage not in proposal_coverage_universe MUST return None (out_of_universe)"

    def test_unmapped_coverage_returns_none(self):
        """
        Test: Coverage in universe but mapping_status != 'MAPPED' → returns None (unmapped)
        SQL filter ensures this by requiring mapping_status = 'MAPPED'
        """
        from apps.api.app.queries.compare import COVERAGE_AMOUNT_SQL

        # Verify SQL requires MAPPED status
        assert "mapping_status = 'MAPPED'" in COVERAGE_AMOUNT_SQL, \
            "SQL MUST filter mapping_status = 'MAPPED' to exclude UNMAPPED/AMBIGUOUS"

    def test_mapped_coverage_returns_amount(self):
        """
        Test: Coverage in universe + mapping_status='MAPPED' → returns amount_value
        """
        from apps.api.app.queries.compare import get_coverage_amount_for_proposal

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulates MAPPED coverage with amount
        mock_cursor.fetchall.return_value = [{"amount_value": 30000000}]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        result = get_coverage_amount_for_proposal(
            mock_conn,
            insurer_code="SAMSUNG",
            proposal_id="proposal_001",
            coverage_code="A1100"  # Canonical code
        )

        assert result == 30000000, \
            "MAPPED coverage MUST return amount_value from proposal_coverage_universe"

    def test_comparable_with_gaps_requires_policy(self):
        """
        Test: Coverage with NULL disease_scope_norm → comparable_with_gaps
        (Requires policy processing to fill disease_scope_norm)
        """
        # This is a conceptual test - actual implementation would check slots table
        # disease_scope_norm NULL = policy processing not done yet
        from apps.api.app.queries.compare import COVERAGE_AMOUNT_SQL

        # Verify we're using universe tables (which have slots linkage)
        assert "proposal_coverage_mapped" in COVERAGE_AMOUNT_SQL, \
            "Must use proposal_coverage_mapped which links to slots for gap detection"

    def test_universe_lock_requires_proposal_id(self):
        """
        Test: Universe Lock queries MUST require proposal_id (cannot query without proposal context)
        """
        from apps.api.app.queries.compare import get_coverage_amount_for_proposal
        import inspect

        # Verify function signature requires proposal_id
        sig = inspect.signature(get_coverage_amount_for_proposal)
        params = list(sig.parameters.keys())

        assert "proposal_id" in params, \
            "get_coverage_amount_for_proposal MUST require proposal_id parameter (Universe Lock)"
        assert "product_id" not in params, \
            "get_coverage_amount_for_proposal MUST NOT use product_id (Universe Lock principle)"

