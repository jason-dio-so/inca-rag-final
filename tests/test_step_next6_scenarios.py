"""
STEP NEXT-6 E2E Scenario Tests

Required Scenarios (Constitutional):
1. "다빈치 수술비를 삼성과 현대 비교" - surgery_method selection
2. "경계성 종양·제자리암을 한화와 흥국 비교" - cancer_subtypes selection
3. "암 진단비 비교" - general comparison (may require basis selection)

Constitutional Principles:
- Clarify Panel → Compile → ViewModel → Renderer
- Debug toggle must work
- No recommendation/judgment
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.app.main import app


client = TestClient(app)


class TestSTEPNEXT6Scenarios:
    """
    Test 3 required E2E scenarios.
    """

    def test_scenario_1_da_vinci_surgery(self):
        """
        Scenario 1: "다빈치 수술비를 삼성과 현대 비교"

        Flow:
        1. Check clarification needed
        2. Should detect surgery_method requirement
        3. Compile with user selection
        4. Verify compiled request
        """
        query = "다빈치 수술비를 삼성과 현대 비교"

        # Step 1: Check clarification
        clarify_response = client.post("/compare/clarify", json={
            "query": query,
            "insurers": ["SAMSUNG", "HYUNDAI"],
        })
        assert clarify_response.status_code == 200
        clarify_data = clarify_response.json()

        # May require surgery_method clarification
        # (depending on rule implementation)

        # Step 2: Compile with user selection
        compile_payload = {
            "user_query": query,
            "selected_insurers": ["SAMSUNG", "HYUNDAI"],
            "options": {
                "surgery_method": "da_vinci",
            },
        }

        compile_response = client.post("/compare/compile", json=compile_payload)
        assert compile_response.status_code == 200
        compile_data = compile_response.json()

        # Verify compilation
        assert "compiled_request" in compile_data
        assert "compiler_debug" in compile_data

        debug = compile_data["compiler_debug"]
        assert "surgery_method" in debug["selected_slots"]
        assert debug["selected_slots"]["surgery_method"] == "da_vinci"

        # Verify decision trace exists
        assert len(debug["decision_trace"]) > 0

        # Verify rule version
        assert "rule_version" in debug
        assert "v1.0.0-next6" in debug["rule_version"]

    def test_scenario_2_cancer_subtypes(self):
        """
        Scenario 2: "경계성 종양·제자리암을 한화와 흥국 비교"

        Flow:
        1. Check clarification needed
        2. Should detect cancer_subtypes requirement
        3. Compile with user selection
        4. Verify compiled request
        """
        query = "경계성 종양·제자리암을 한화와 흥국 비교"

        # Step 1: Check clarification
        clarify_response = client.post("/compare/clarify", json={
            "query": query,
            "insurers": ["HANWHA", "HEUNGKUK"],
        })
        assert clarify_response.status_code == 200
        clarify_data = clarify_response.json()

        # Should detect multiple cancer subtypes
        assert "required_selections" in clarify_data

        # Step 2: Compile with user selection
        compile_payload = {
            "user_query": query,
            "selected_insurers": ["HANWHA", "HEUNGKUK"],
            "options": {
                "cancer_subtypes": ["경계성종양", "제자리암"],
                "comparison_focus": "definition",  # Definition/condition focus
            },
        }

        compile_response = client.post("/compare/compile", json=compile_payload)
        assert compile_response.status_code == 200
        compile_data = compile_response.json()

        # Verify compilation
        debug = compile_data["compiler_debug"]
        assert "cancer_subtypes" in debug["selected_slots"]
        assert set(debug["selected_slots"]["cancer_subtypes"]) == {"경계성종양", "제자리암"}

        # Verify comparison_focus
        assert "comparison_focus" in debug["selected_slots"]
        assert debug["selected_slots"]["comparison_focus"] == "definition"

        # Verify decision trace
        assert len(debug["decision_trace"]) > 0

    def test_scenario_3_general_cancer_diagnosis(self):
        """
        Scenario 3: "암 진단비 비교"

        Flow:
        1. Check clarification needed
        2. May require insurers or comparison basis
        3. Compile with user selection
        4. Verify compiled request
        """
        query = "암 진단비 비교"

        # Step 1: Check clarification (no insurers)
        clarify_response = client.post("/compare/clarify", json={
            "query": query,
            "insurers": None,
        })
        assert clarify_response.status_code == 200
        clarify_data = clarify_response.json()

        # Should require insurers
        assert clarify_data["clarification_needed"] is True
        assert any(r["type"] == "insurers" for r in clarify_data["required_selections"])

        # Step 2: Check clarification with insurers
        clarify_response_2 = client.post("/compare/clarify", json={
            "query": query,
            "insurers": ["SAMSUNG", "MERITZ"],
        })
        assert clarify_response_2.status_code == 200

        # Step 3: Compile with full selection
        compile_payload = {
            "user_query": query,
            "selected_insurers": ["SAMSUNG", "MERITZ"],
            "selected_comparison_basis": "일반암진단비",
        }

        compile_response = client.post("/compare/compile", json=compile_payload)
        assert compile_response.status_code == 200
        compile_data = compile_response.json()

        # Verify compilation
        compiled_req = compile_data["compiled_request"]
        assert compiled_req["query"] == "일반암진단비"
        assert compiled_req["insurer_a"] == "SAMSUNG"
        assert compiled_req["insurer_b"] == "MERITZ"

        # Verify debug
        debug = compile_data["compiler_debug"]
        assert "insurers" in debug["selected_slots"]
        assert debug["selected_slots"]["insurers"] == ["SAMSUNG", "MERITZ"]

        assert "comparison_basis" in debug["selected_slots"]
        assert debug["selected_slots"]["comparison_basis"] == "일반암진단비"

    def test_scenario_determinism_guarantee(self):
        """
        Test that all scenarios produce deterministic output.
        """
        scenarios = [
            {
                "user_query": "다빈치 수술비 비교",
                "selected_insurers": ["SAMSUNG", "HYUNDAI"],
                "options": {"surgery_method": "da_vinci"},
            },
            {
                "user_query": "경계성종양 비교",
                "selected_insurers": ["HANWHA", "HEUNGKUK"],
                "options": {"cancer_subtypes": ["경계성종양"]},
            },
            {
                "user_query": "암 진단비 비교",
                "selected_insurers": ["SAMSUNG", "MERITZ"],
                "selected_comparison_basis": "일반암진단비",
            },
        ]

        for scenario in scenarios:
            # Compile twice
            response1 = client.post("/compare/compile", json=scenario)
            response2 = client.post("/compare/compile", json=scenario)

            assert response1.status_code == 200
            assert response2.status_code == 200

            data1 = response1.json()
            data2 = response2.json()

            # Must be identical
            assert data1["compiled_request"] == data2["compiled_request"]
            assert data1["compiler_debug"]["decision_trace"] == data2["compiler_debug"]["decision_trace"]
            assert data1["compiler_debug"]["selected_slots"] == data2["compiler_debug"]["selected_slots"]

    def test_debug_info_always_present(self):
        """
        Constitutional Requirement: Debug info must always be present.
        """
        # Given: Any compilation
        payload = {
            "user_query": "암 진단비",
            "selected_insurers": ["SAMSUNG", "MERITZ"],
        }

        # When: Compile
        response = client.post("/compare/compile", json=payload)

        # Then: Debug info must be present
        assert response.status_code == 200
        data = response.json()

        assert "compiler_debug" in data
        debug = data["compiler_debug"]

        # Required debug fields
        assert "rule_version" in debug
        assert "selected_slots" in debug
        assert "decision_trace" in debug
        assert "warnings" in debug

        # Decision trace must not be empty
        assert len(debug["decision_trace"]) > 0

        # Rule version must be valid
        assert "v1.0.0-next6" in debug["rule_version"]
