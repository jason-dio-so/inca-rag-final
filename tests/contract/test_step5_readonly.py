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
        Verify db_readonly_session creates connections with readonly=True
        """
        from apps.api.app.db import get_db_connection

        # Mock psycopg2.connect to verify readonly parameter
        with patch('apps.api.app.db.psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            conn = get_db_connection(readonly=True)

            # Verify set_session was called with readonly=True
            mock_conn.set_session.assert_called_once()
            call_kwargs = mock_conn.set_session.call_args[1]
            assert call_kwargs.get('readonly') is True
            assert call_kwargs.get('autocommit') is True

    def test_compare_endpoint_uses_readonly_session(self):
        """
        Verify /compare endpoint uses read-only DB session
        """
        request_body = {
            "axis": "compare",
            "mode": "compensation"
        }

        # Mock DB session to verify readonly usage
        with patch('apps.api.app.routers.compare.db_readonly_session') as mock_session:
            mock_conn = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_conn

            # Mock query results
            mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []

            response = client.post("/compare", json=request_body)

            # Verify readonly session was used
            mock_session.assert_called_once()
            assert response.status_code == 200


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
        Verify /compare returns only is_synthetic=false evidence
        """
        request_body = {
            "axis": "compare",
            "mode": "compensation",
            "options": {
                "include_evidence": True
            }
        }

        # Mock DB to return mixed synthetic data (should be filtered by SQL)
        with patch('apps.api.app.routers.compare.db_readonly_session') as mock_session:
            mock_conn = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_conn

            # Mock products query
            mock_cursor1 = MagicMock()
            mock_cursor1.fetchall.return_value = [
                {
                    "product_id": 1,
                    "insurer_code": "TEST",
                    "product_name": "Test Product",
                    "product_code": "P001"
                }
            ]

            # Mock evidence query - SQL should only return is_synthetic=false
            mock_cursor2 = MagicMock()
            mock_cursor2.fetchall.return_value = [
                {
                    "chunk_id": 1,
                    "document_id": 1,
                    "page_number": 1,
                    "is_synthetic": False,  # SQL enforces this
                    "synthetic_source_chunk_id": None,
                    "snippet": "Test snippet",
                    "doc_type": "약관"
                }
            ]

            # Setup cursor to return different results for different queries
            mock_conn.cursor.return_value.__enter__.side_effect = [
                mock_cursor1,
                mock_cursor2
            ]

            response = client.post("/compare", json=request_body)

            assert response.status_code == 200
            data = response.json()

            # Verify all evidence has is_synthetic=false
            if data.get("items"):
                for item in data["items"]:
                    if item.get("evidence"):
                        for evidence in item["evidence"]:
                            assert evidence["is_synthetic"] is False

    def test_amount_bridge_respects_include_synthetic_option(self):
        """
        Verify /evidence/amount-bridge respects include_synthetic option
        """
        # Test with include_synthetic=false
        request_body = {
            "axis": "amount_bridge",
            "coverage_code": "C001",
            "options": {
                "include_synthetic": False
            }
        }

        with patch('apps.api.app.routers.evidence.db_readonly_session') as mock_session:
            mock_conn = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_conn

            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

            response = client.post("/evidence/amount-bridge", json=request_body)

            assert response.status_code == 200
            data = response.json()

            # Verify debug info shows synthetic filter applied
            assert data["debug"]["hard_rules"]["is_synthetic_filter_applied"] is True


class TestHardRulesDebugInfo:
    """Verify debug.hard_rules information is accurate"""

    def test_compare_debug_hard_rules_present(self):
        """
        Verify /compare response includes debug.hard_rules
        """
        request_body = {
            "axis": "compare",
            "mode": "compensation"
        }

        with patch('apps.api.app.routers.compare.db_readonly_session') as mock_session:
            mock_conn = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []

            response = client.post("/compare", json=request_body)

            assert response.status_code == 200
            data = response.json()

            assert "debug" in data
            assert "hard_rules" in data["debug"]
            hard_rules = data["debug"]["hard_rules"]

            # These should always be true for compare axis
            assert hard_rules["is_synthetic_filter_applied"] is True
            assert hard_rules["compare_axis_forbids_synthetic"] is True

    def test_amount_bridge_debug_synthetic_info(self):
        """
        Verify /evidence/amount-bridge debug includes synthetic option info
        """
        request_body = {
            "axis": "amount_bridge",
            "coverage_code": "C001",
            "options": {
                "include_synthetic": True
            }
        }

        with patch('apps.api.app.routers.evidence.db_readonly_session') as mock_session:
            mock_conn = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []

            response = client.post("/evidence/amount-bridge", json=request_body)

            assert response.status_code == 200
            data = response.json()

            assert "debug" in data
            assert "notes" in data["debug"]

            # Notes should mention include_synthetic=True
            notes_str = " ".join(data["debug"]["notes"])
            assert "include_synthetic=True" in notes_str
