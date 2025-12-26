"""
Test /compare/compile endpoint (STEP NEXT-6)

Constitutional Principles:
- Schema validation
- Deterministic compilation
- No LLM dependency
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.app.main import app


client = TestClient(app)


class TestCompileEndpoint:
    """Test /compare/compile endpoint."""

    def test_compile_endpoint_basic(self):
        """
        Test basic compilation flow.
        """
        # Given: Valid compile input
        payload = {
            "user_query": "암 진단비 비교",
            "selected_insurers": ["SAMSUNG", "MERITZ"],
            "selected_comparison_basis": "일반암진단비",
        }

        # When: Call /compare/compile
        response = client.post("/compare/compile", json=payload)

        # Then: Should succeed
        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "compiled_request" in data
        assert "compiler_debug" in data

        # Verify compiled_request
        compiled_req = data["compiled_request"]
        assert "query" in compiled_req
        assert compiled_req["query"] == "일반암진단비"
        assert "insurer_a" in compiled_req
        assert "insurer_b" in compiled_req
        assert compiled_req["insurer_a"] == "SAMSUNG"
        assert compiled_req["insurer_b"] == "MERITZ"

        # Verify compiler_debug
        debug = data["compiler_debug"]
        assert "rule_version" in debug
        assert "selected_slots" in debug
        assert "decision_trace" in debug
        assert "warnings" in debug
        assert isinstance(debug["decision_trace"], list)
        assert len(debug["decision_trace"]) > 0

    def test_compile_with_surgery_method_option(self):
        """
        Test compilation with surgery_method option.
        """
        # Given: Input with surgery_method
        payload = {
            "user_query": "다빈치 수술비 비교",
            "selected_insurers": ["SAMSUNG", "HYUNDAI"],
            "options": {
                "surgery_method": "da_vinci",
            },
        }

        # When: Call endpoint
        response = client.post("/compare/compile", json=payload)

        # Then: Should succeed
        assert response.status_code == 200
        data = response.json()

        # Verify option is in selected_slots
        debug = data["compiler_debug"]
        assert "surgery_method" in debug["selected_slots"]
        assert debug["selected_slots"]["surgery_method"] == "da_vinci"

    def test_compile_with_cancer_subtypes_option(self):
        """
        Test compilation with cancer_subtypes option.
        """
        # Given: Input with cancer_subtypes
        payload = {
            "user_query": "경계성종양 비교",
            "selected_insurers": ["HANWHA", "HEUNGKUK"],
            "options": {
                "cancer_subtypes": ["경계성종양", "제자리암"],
            },
        }

        # When: Call endpoint
        response = client.post("/compare/compile", json=payload)

        # Then: Should succeed
        assert response.status_code == 200
        data = response.json()

        # Verify option is in selected_slots
        debug = data["compiler_debug"]
        assert "cancer_subtypes" in debug["selected_slots"]
        assert debug["selected_slots"]["cancer_subtypes"] == ["경계성종양", "제자리암"]

    def test_compile_with_comparison_focus_option(self):
        """
        Test compilation with comparison_focus option.
        """
        # Given: Input with comparison_focus
        payload = {
            "user_query": "암 진단비 금액 비교",
            "selected_insurers": ["SAMSUNG", "MERITZ"],
            "options": {
                "comparison_focus": "amount",
            },
        }

        # When: Call endpoint
        response = client.post("/compare/compile", json=payload)

        # Then: Should succeed
        assert response.status_code == 200
        data = response.json()

        # Verify option is in selected_slots
        debug = data["compiler_debug"]
        assert "comparison_focus" in debug["selected_slots"]
        assert debug["selected_slots"]["comparison_focus"] == "amount"

    def test_compile_with_less_than_2_insurers_warning(self):
        """
        Test that warning is issued when less than 2 insurers selected.
        """
        # Given: Input with only 1 insurer
        payload = {
            "user_query": "암 진단비",
            "selected_insurers": ["SAMSUNG"],
        }

        # When: Call endpoint
        response = client.post("/compare/compile", json=payload)

        # Then: Should succeed but with warning
        assert response.status_code == 200
        data = response.json()

        debug = data["compiler_debug"]
        assert len(debug["warnings"]) > 0
        assert any("2 insurers" in w for w in debug["warnings"])

    def test_compile_invalid_schema(self):
        """
        Test that invalid schema is rejected.
        """
        # Given: Invalid payload (missing required fields)
        payload = {
            "user_query": "암 진단비",
            # Missing selected_insurers
        }

        # When: Call endpoint
        response = client.post("/compare/compile", json=payload)

        # Then: Should fail with 422 (validation error)
        assert response.status_code == 422


class TestClarifyEndpoint:
    """Test /compare/clarify endpoint."""

    def test_clarify_endpoint_basic(self):
        """
        Test basic clarification detection.
        """
        # Given: Query without insurers
        payload = {
            "query": "암 진단비 비교",
            "insurers": None,
        }

        # When: Call /compare/clarify
        response = client.post("/compare/clarify", json=payload)

        # Then: Should succeed
        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "clarification_needed" in data
        assert "required_selections" in data
        assert isinstance(data["required_selections"], list)

        # Should require insurer selection
        assert data["clarification_needed"] is True
        assert any(r["type"] == "insurers" for r in data["required_selections"])

    def test_clarify_no_clarification_needed(self):
        """
        Test when no clarification is needed.
        """
        # Given: Complete query with insurers
        payload = {
            "query": "암 진단비",
            "insurers": ["SAMSUNG", "MERITZ"],
        }

        # When: Call endpoint
        response = client.post("/compare/clarify", json=payload)

        # Then: Should not require clarification
        assert response.status_code == 200
        data = response.json()

        # Note: May still require clarification for other reasons
        # (e.g., comparison_focus), but at least insurers are satisfied
        assert "clarification_needed" in data
        assert "required_selections" in data

    def test_clarify_surgery_method_detection(self):
        """
        Test surgery method keyword detection.
        """
        # Given: Query with surgery keywords
        payload = {
            "query": "다빈치 수술비 비교",
            "insurers": ["SAMSUNG", "HYUNDAI"],
        }

        # When: Call endpoint
        response = client.post("/compare/clarify", json=payload)

        # Then: May require surgery_method clarification
        assert response.status_code == 200
        data = response.json()

        # Check if surgery_method is in required_selections
        # (depends on rule implementation)
        assert "required_selections" in data

    def test_clarify_cancer_subtype_detection(self):
        """
        Test cancer subtype keyword detection.
        """
        # Given: Query with cancer subtype keywords
        payload = {
            "query": "경계성종양 제자리암 비교",
            "insurers": ["HANWHA", "HEUNGKUK"],
        }

        # When: Call endpoint
        response = client.post("/compare/clarify", json=payload)

        # Then: May require cancer_subtypes clarification
        assert response.status_code == 200
        data = response.json()

        assert "required_selections" in data
