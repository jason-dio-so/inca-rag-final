"""
STEP 14-α: Docker API E2E Verification for /compare endpoint

Purpose:
    Verify proposal-universe based /compare endpoint works E2E
    with Docker DB + API containers

Scenarios:
    A: Normal comparison (삼성 vs 메리츠 일반암진단비)
    B: UNMAPPED coverage (KB 매핑안된담보)
    C: Disease scope required (삼성 유사암진단금)

DoD:
    - All scenarios return HTTP 200
    - Response JSON schema validation
    - UX message contract validation
    - Evidence order validation (PROPOSAL → POLICY)
    - Constitutional principles enforced
"""

import pytest
import requests
import json
from typing import Dict, Any


API_BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def api_health_check():
    """Verify API is running before tests"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            pytest.skip("API not healthy. Run scripts/step14_api_e2e_docker.sh first")
    except requests.exceptions.ConnectionError:
        pytest.skip("API not running. Run scripts/step14_api_e2e_docker.sh first")


class TestScenarioA_NormalComparison:
    """
    Scenario A: 삼성 vs 메리츠 일반암진단비 비교

    Expected:
    - HTTP 200
    - comparison_result: "comparable"
    - Both insurers: CA_DIAG_GENERAL
    - mapping_status: MAPPED
    - amount_value: exists (50M for SAMSUNG, 30M for MERITZ)
    - policy_evidence: not included (disease_scope_norm is NULL)
    """

    def test_http_200(self, api_health_check):
        """Verify HTTP 200 response"""
        payload = {
            "query": "일반암진단비",
            "insurer_a": "SAMSUNG",
            "insurer_b": "MERITZ",
            "include_policy_evidence": False
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_json_schema_valid(self, api_health_check):
        """Verify response JSON schema"""
        payload = {
            "query": "일반암진단비",
            "insurer_a": "SAMSUNG",
            "insurer_b": "MERITZ",
            "include_policy_evidence": False
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        # Required fields
        assert "query" in data
        assert "comparison_result" in data
        assert "next_action" in data
        assert "coverage_a" in data
        assert "coverage_b" in data
        assert "message" in data

    def test_comparison_result_comparable(self, api_health_check):
        """Verify comparison_result is 'comparable'"""
        payload = {
            "query": "일반암진단비",
            "insurer_a": "SAMSUNG",
            "insurer_b": "MERITZ",
            "include_policy_evidence": False
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["comparison_result"] == "comparable", \
            f"Expected 'comparable', got '{data['comparison_result']}'"

    def test_canonical_code_ca_diag_general(self, api_health_check):
        """Verify both insurers have CA_DIAG_GENERAL"""
        payload = {
            "query": "일반암진단비",
            "insurer_a": "SAMSUNG",
            "insurer_b": "MERITZ",
            "include_policy_evidence": False
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["coverage_a"]["canonical_coverage_code"] == "CA_DIAG_GENERAL"
        assert data["coverage_b"]["canonical_coverage_code"] == "CA_DIAG_GENERAL"

    def test_mapping_status_mapped(self, api_health_check):
        """Verify mapping_status is MAPPED for both"""
        payload = {
            "query": "일반암진단비",
            "insurer_a": "SAMSUNG",
            "insurer_b": "MERITZ",
            "include_policy_evidence": False
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["coverage_a"]["mapping_status"] == "MAPPED"
        assert data["coverage_b"]["mapping_status"] == "MAPPED"

    def test_amount_values_exist(self, api_health_check):
        """Verify amount_value exists and is correct"""
        payload = {
            "query": "일반암진단비",
            "insurer_a": "SAMSUNG",
            "insurer_b": "MERITZ",
            "include_policy_evidence": False
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["coverage_a"]["amount_value"] == 50000000, \
            "SAMSUNG amount should be 50M"
        assert data["coverage_b"]["amount_value"] == 30000000, \
            "MERITZ amount should be 30M"

    def test_policy_evidence_not_included(self, api_health_check):
        """Verify policy_evidence is not included (disease_scope_norm is NULL)"""
        payload = {
            "query": "일반암진단비",
            "insurer_a": "SAMSUNG",
            "insurer_b": "MERITZ",
            "include_policy_evidence": False
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["policy_evidence_a"] is None
        assert data["policy_evidence_b"] is None


class TestScenarioB_UnmappedCoverage:
    """
    Scenario B: KB 매핑안된담보

    Expected:
    - HTTP 200
    - comparison_result: "unmapped"
    - mapping_status: UNMAPPED
    - canonical_coverage_code: NULL
    - next_action: REQUEST_MORE_INFO
    - policy_evidence: forbidden (not included)
    """

    def test_http_200(self, api_health_check):
        """Verify HTTP 200 response"""
        payload = {
            "query": "매핑안된담보",
            "insurer_a": "KB",
            "insurer_b": None,
            "include_policy_evidence": False
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_comparison_result_unmapped(self, api_health_check):
        """Verify comparison_result is 'unmapped'"""
        payload = {
            "query": "매핑안된담보",
            "insurer_a": "KB",
            "insurer_b": None,
            "include_policy_evidence": False
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["comparison_result"] == "unmapped", \
            f"Expected 'unmapped', got '{data['comparison_result']}'"

    def test_mapping_status_unmapped(self, api_health_check):
        """Verify mapping_status is UNMAPPED"""
        payload = {
            "query": "매핑안된담보",
            "insurer_a": "KB",
            "insurer_b": None,
            "include_policy_evidence": False
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["coverage_a"]["mapping_status"] == "UNMAPPED"
        assert data["coverage_a"]["canonical_coverage_code"] is None

    def test_next_action_request_more_info(self, api_health_check):
        """Verify next_action is REQUEST_MORE_INFO"""
        payload = {
            "query": "매핑안된담보",
            "insurer_a": "KB",
            "insurer_b": None,
            "include_policy_evidence": False
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["next_action"] == "REQUEST_MORE_INFO"

    def test_policy_evidence_forbidden(self, api_health_check):
        """Verify policy_evidence is not included (UNMAPPED forbids it)"""
        payload = {
            "query": "매핑안된담보",
            "insurer_a": "KB",
            "insurer_b": None,
            "include_policy_evidence": False
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["policy_evidence_a"] is None


class TestScenarioC_DiseaseScopeRequired:
    """
    Scenario C: 삼성 유사암진단금 보장범위

    Expected:
    - HTTP 200
    - comparison_result: "policy_required"
    - canonical_coverage_code: CA_DIAG_SIMILAR
    - disease_scope_norm: NOT NULL
    - policy_evidence: exists (disease_code_group)
    - next_action: VERIFY_POLICY
    - source_confidence: policy_required
    """

    def test_http_200(self, api_health_check):
        """Verify HTTP 200 response"""
        payload = {
            "query": "유사암진단금",
            "insurer_a": "SAMSUNG",
            "insurer_b": None,
            "include_policy_evidence": True
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_canonical_code_ca_diag_similar(self, api_health_check):
        """Verify canonical_coverage_code is CA_DIAG_SIMILAR"""
        payload = {
            "query": "유사암진단금",
            "insurer_a": "SAMSUNG",
            "insurer_b": None,
            "include_policy_evidence": True
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["coverage_a"]["canonical_coverage_code"] == "CA_DIAG_SIMILAR"

    def test_disease_scope_norm_exists(self, api_health_check):
        """Verify disease_scope_norm is NOT NULL"""
        payload = {
            "query": "유사암진단금",
            "insurer_a": "SAMSUNG",
            "insurer_b": None,
            "include_policy_evidence": True
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["coverage_a"]["disease_scope_norm"] is not None, \
            "disease_scope_norm should NOT be NULL for CA_DIAG_SIMILAR"

    def test_policy_evidence_exists(self, api_health_check):
        """Verify policy_evidence exists"""
        payload = {
            "query": "유사암진단금",
            "insurer_a": "SAMSUNG",
            "insurer_b": None,
            "include_policy_evidence": True
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["policy_evidence_a"] is not None, \
            "policy_evidence_a should exist for disease_scope_norm"
        assert "group_name" in data["policy_evidence_a"]
        assert "유사암" in data["policy_evidence_a"]["group_name"]

    def test_next_action_verify_policy(self, api_health_check):
        """Verify next_action is VERIFY_POLICY"""
        payload = {
            "query": "유사암진단금",
            "insurer_a": "SAMSUNG",
            "insurer_b": None,
            "include_policy_evidence": True
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["next_action"] == "VERIFY_POLICY"

    def test_source_confidence_policy_required(self, api_health_check):
        """Verify source_confidence is policy_required"""
        payload = {
            "query": "유사암진단금",
            "insurer_a": "SAMSUNG",
            "insurer_b": None,
            "include_policy_evidence": True
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["coverage_a"]["source_confidence"] == "policy_required"


class TestUniverseLockPrinciple:
    """Verify Universe Lock principle compliance"""

    def test_out_of_universe_returns_error_state(self, api_health_check):
        """Verify out_of_universe query returns appropriate state"""
        payload = {
            "query": "존재하지않는담보",
            "insurer_a": "SAMSUNG",
            "insurer_b": None,
            "include_policy_evidence": False
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert data["comparison_result"] == "out_of_universe"
        assert data["next_action"] == "REQUEST_MORE_INFO"

    def test_universe_lock_enforced(self, api_health_check):
        """Verify debug.universe_lock_enforced is True"""
        payload = {
            "query": "일반암진단비",
            "insurer_a": "SAMSUNG",
            "insurer_b": "MERITZ",
            "include_policy_evidence": False
        }
        response = requests.post(f"{API_BASE_URL}/compare", json=payload)
        data = response.json()

        assert "debug" in data
        assert data["debug"]["universe_lock_enforced"] is True


class TestDependencySSoT:
    """
    Regression guard: Ensure single-source requirements

    STEP 14-α cleanup enforces:
    - apps/api/requirements.txt = SSOT for API dependencies
    - Root requirements.txt must NOT exist
    - Dockerfile.api must reference apps/api/requirements.txt only
    """

    def test_root_requirements_does_not_exist(self):
        """Verify root requirements.txt does not exist"""
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        root_requirements = os.path.join(project_root, "requirements.txt")

        assert not os.path.exists(root_requirements), \
            "Root requirements.txt should not exist. SSOT is apps/api/requirements.txt"

    def test_dockerfile_uses_api_requirements(self):
        """Verify Dockerfile.api references apps/api/requirements.txt"""
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        dockerfile_path = os.path.join(project_root, "Dockerfile.api")

        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()

        # Must contain apps/api/requirements.txt reference
        assert "apps/api/requirements.txt" in dockerfile_content, \
            "Dockerfile.api must COPY apps/api/requirements.txt (not root requirements.txt)"

        # Must NOT contain root requirements.txt reference
        assert "COPY requirements.txt" not in dockerfile_content, \
            "Dockerfile.api must not COPY root requirements.txt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
