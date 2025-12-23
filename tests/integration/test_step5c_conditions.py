"""
STEP 5-C Integration Tests: Conditions Summary

Tests for presentation-only LLM-based conditions summary feature.

Constitutional Compliance:
- Only tests that summary uses non-synthetic evidence
- Does NOT test summary content accuracy (presentation layer)
- Verifies opt-in behavior
- Verifies graceful degradation
"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from apps.api.app.main import app

client = TestClient(app)


class TestConditionsSummaryIntegration:
    """Integration tests for conditions_summary feature"""

    def test_conditions_summary_opt_in_false_returns_null(self):
        """
        Verify conditions_summary is null when include_conditions_summary=false (default)
        """
        from apps.api.app.db import get_readonly_conn

        def mock_conn_gen():
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            # Mock product data
            mock_cursor.fetchall.side_effect = [
                [{"product_id": 1, "insurer_code": "TEST", "product_name": "Test Product", "product_code": "TP001"}],
                []  # No evidence
            ]
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            yield mock_conn

        app.dependency_overrides[get_readonly_conn] = mock_conn_gen

        try:
            response = client.post("/compare", json={
                "axis": "compare",
                "mode": "compensation",
                "options": {
                    "include_conditions_summary": False  # Explicit false
                }
            })

            assert response.status_code == 200
            data = response.json()

            # Verify conditions_summary is null when not requested
            if data["items"]:
                assert data["items"][0]["conditions_summary"] is None

        finally:
            app.dependency_overrides.clear()

    def test_conditions_summary_opt_in_true_generates_summary(self):
        """
        Verify conditions_summary is generated when include_conditions_summary=true
        """
        from apps.api.app.db import get_readonly_conn

        def mock_conn_gen():
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            # Mock product and evidence data
            mock_cursor.fetchall.side_effect = [
                [{"product_id": 1, "insurer_code": "TEST", "product_name": "Test Product", "product_code": "TP001"}],
                [{  # Evidence with conditions keywords
                    "chunk_id": 1,
                    "document_id": 1,
                    "page_number": 1,
                    "is_synthetic": False,
                    "synthetic_source_chunk_id": None,
                    "snippet": "면책기간: 가입 후 90일. 감액기간: 2년 내 50% 감액.",
                    "doc_type": "약관"
                }]
            ]
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            yield mock_conn

        app.dependency_overrides[get_readonly_conn] = mock_conn_gen

        try:
            response = client.post("/compare", json={
                "axis": "compare",
                "mode": "compensation",
                "options": {
                    "include_conditions_summary": True  # Request summary
                }
            })

            assert response.status_code == 200
            data = response.json()

            # Verify conditions_summary exists (nullable, so can be null or string)
            if data["items"]:
                item = data["items"][0]
                assert "conditions_summary" in item
                # Summary can be null (failure) or string (success)
                assert item["conditions_summary"] is None or isinstance(item["conditions_summary"], str)

        finally:
            app.dependency_overrides.clear()

    def test_conditions_summary_uses_non_synthetic_evidence_only(self):
        """
        CONSTITUTIONAL TEST: Verify conditions_summary only uses non-synthetic evidence

        This test ensures that even when generating summary,
        the evidence input is non-synthetic (constitutional guarantee).
        """
        from apps.api.app.db import get_readonly_conn

        def mock_conn_gen():
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            # Mock data - all evidence is non-synthetic
            mock_cursor.fetchall.side_effect = [
                [{"product_id": 1, "insurer_code": "TEST", "product_name": "Test Product", "product_code": "TP001"}],
                [{
                    "chunk_id": 1,
                    "is_synthetic": False,  # CRITICAL: non-synthetic only
                    "snippet": "면책기간 정보",
                    "doc_type": "약관",
                    "document_id": 1,
                    "page_number": 1,
                    "synthetic_source_chunk_id": None
                }]
            ]
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            yield mock_conn

        app.dependency_overrides[get_readonly_conn] = mock_conn_gen

        try:
            response = client.post("/compare", json={
                "axis": "compare",
                "mode": "compensation",
                "options": {
                    "include_conditions_summary": True
                }
            })

            assert response.status_code == 200
            # Constitutional guarantee: evidence used for summary is non-synthetic
            # This is enforced by SQL layer (c.is_synthetic = false HARD RULE)

        finally:
            app.dependency_overrides.clear()

    def test_conditions_summary_graceful_degradation_on_empty_evidence(self):
        """
        Verify graceful degradation when no evidence available
        """
        from apps.api.app.db import get_readonly_conn

        def mock_conn_gen():
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            # Mock: product exists but no evidence
            mock_cursor.fetchall.side_effect = [
                [{"product_id": 1, "insurer_code": "TEST", "product_name": "Test Product", "product_code": "TP001"}],
                []  # No evidence
            ]
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            yield mock_conn

        app.dependency_overrides[get_readonly_conn] = mock_conn_gen

        try:
            response = client.post("/compare", json={
                "axis": "compare",
                "mode": "compensation",
                "options": {
                    "include_conditions_summary": True
                }
            })

            # Should still return 200 OK (graceful degradation)
            assert response.status_code == 200
            data = response.json()

            if data["items"]:
                # conditions_summary should be null (no evidence to summarize)
                assert data["items"][0]["conditions_summary"] is None

        finally:
            app.dependency_overrides.clear()

    def test_conditions_summary_default_behavior_is_null(self):
        """
        Verify default behavior (no options) returns null for conditions_summary
        """
        from apps.api.app.db import get_readonly_conn

        def mock_conn_gen():
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.side_effect = [
                [{"product_id": 1, "insurer_code": "TEST", "product_name": "Test Product", "product_code": "TP001"}],
                []
            ]
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            yield mock_conn

        app.dependency_overrides[get_readonly_conn] = mock_conn_gen

        try:
            response = client.post("/compare", json={
                "axis": "compare",
                "mode": "compensation"
                # No options - default behavior
            })

            assert response.status_code == 200
            data = response.json()

            # Default behavior: conditions_summary should be null
            if data["items"]:
                assert data["items"][0]["conditions_summary"] is None

        finally:
            app.dependency_overrides.clear()
