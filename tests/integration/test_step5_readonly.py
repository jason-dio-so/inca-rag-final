"""
STEP 5-B Read-only and is_synthetic enforcement tests

Tests:
1. DB connection is read-only (write attempts fail)
2. Compare evidence queries enforce is_synthetic=false
3. Amount bridge respects include_synthetic option
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from apps.api.app.main import app
from apps.api.app.queries.compare import COMPARE_EVIDENCE_SQL
from apps.api.app.queries.evidence import AMOUNT_BRIDGE_EVIDENCE_SQL

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
    """Verify is_synthetic enforcement in SQL templates"""

    def test_compare_sql_hard_codes_is_synthetic_false(self):
        """
        CONSTITUTIONAL TEST: Compare SQL template MUST have is_synthetic=false
        """
        # This is a compile-time guarantee - SQL template must contain the filter
        assert "c.is_synthetic = false" in COMPARE_EVIDENCE_SQL
        assert "-- HARD RULE" in COMPARE_EVIDENCE_SQL

        # Verify there's no option to skip this filter
        assert "%(include_synthetic)s" not in COMPARE_EVIDENCE_SQL

    def test_amount_bridge_sql_allows_synthetic_option(self):
        """
        Amount Bridge SQL template MUST support include_synthetic option
        """
        # Amount bridge should have conditional synthetic filtering
        assert "%(include_synthetic)s" in AMOUNT_BRIDGE_EVIDENCE_SQL
        assert "c.is_synthetic = false" in AMOUNT_BRIDGE_EVIDENCE_SQL

        # Should have OR clause for conditional filtering
        assert "OR c.is_synthetic = false" in AMOUNT_BRIDGE_EVIDENCE_SQL

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
