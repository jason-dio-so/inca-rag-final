"""
STEP 5 Contract Tests

운영 헌법을 400/422로 강제하는지 검증

Test Coverage:
1. /compare + mode=premium + premium filter 누락 → 400 + VALIDATION_ERROR
2. /search/products + sort.mode=premium + premium filter 누락 → 400 + VALIDATION_ERROR
3. /compare + options.include_synthetic=true → 400 + POLICY_VIOLATION
4. /compare 정상 호출 → 200 + debug.hard_rules.is_synthetic_filter_applied == true
5. /evidence/amount-bridge에 axis=compare → 400 + VALIDATION_ERROR
"""
import pytest
from fastapi.testclient import TestClient
from apps.api.app.main import app

client = TestClient(app)


class TestCompareHardRules:
    """Compare endpoint 헌법 검증"""

    def test_compare_premium_mode_requires_premium_filter(self):
        """
        Test1: /compare + mode=premium + premium filter 누락 → 400 + VALIDATION_ERROR
        """
        request_body = {
            "axis": "compare",
            "mode": "premium",
            "filter": {
                "product": {
                    "insurer_codes": ["SAMSUNG"]
                }
                # premium filter 누락
            }
        }

        response = client.post("/compare", json=request_body)

        assert response.status_code == 400
        data = response.json()
        # FastAPI wraps error response in "detail"
        error = data.get("detail")
        assert error is not None
        assert error["code"] == "VALIDATION_ERROR"
        assert "premium" in error["message"].lower()
        assert "details" in error
        assert error["details"]["rule"] == "premium_mode_requires_premium_filter"

    def test_compare_forbids_synthetic_chunks(self):
        """
        Test3: /compare + options.include_synthetic=true → 400 + POLICY_VIOLATION
        """
        request_body = {
            "axis": "compare",
            "mode": "compensation",
            "filter": {
                "coverage": {
                    "coverage": {
                        "coverage_code": "C001"
                    }
                }
            },
            "options": {
                "include_synthetic": True  # 금지!
            }
        }

        response = client.post("/compare", json=request_body)

        assert response.status_code == 400
        data = response.json()
        error = data.get("detail")
        assert error is not None
        assert error["code"] == "POLICY_VIOLATION"
        assert "synthetic" in error["message"].lower()
        assert "details" in error
        assert error["details"]["rule"] == "compare_axis_forbids_synthetic"

    def test_compare_success_with_hard_rules_debug(self):
        """
        Test4: /compare 정상 호출 → 200 + debug.hard_rules.is_synthetic_filter_applied == true
        """
        request_body = {
            "axis": "compare",
            "mode": "compensation",
            "filter": {
                "coverage": {
                    "coverage": {
                        "coverage_code": "C001"
                    }
                }
            },
            "options": {
                "include_synthetic": False
            }
        }

        response = client.post("/compare", json=request_body)

        assert response.status_code == 200
        data = response.json()
        assert data["axis"] == "compare"
        assert data["mode"] == "compensation"
        assert "debug" in data
        assert "hard_rules" in data["debug"]

        hard_rules = data["debug"]["hard_rules"]
        assert hard_rules["is_synthetic_filter_applied"] is True
        assert hard_rules["compare_axis_forbids_synthetic"] is True
        assert hard_rules["premium_mode_requires_premium_filter"] is False  # mode != premium


class TestSearchProductsHardRules:
    """Search products endpoint 헌법 검증"""

    def test_search_products_premium_mode_requires_premium_filter(self):
        """
        Test2: /search/products + sort.mode=premium + premium filter 누락 → 400 + VALIDATION_ERROR
        """
        request_body = {
            "filter": {
                "product": {
                    "insurer_codes": ["SAMSUNG"]
                }
                # premium filter 누락
            },
            "sort": {
                "mode": "premium",
                "direction": "asc"
            }
        }

        response = client.post("/search/products", json=request_body)

        assert response.status_code == 400
        data = response.json()
        error = data.get("detail")
        assert error is not None
        assert error["code"] == "VALIDATION_ERROR"
        assert "premium" in error["message"].lower()
        assert "details" in error
        assert error["details"]["rule"] == "premium_mode_requires_premium_filter"


class TestAmountBridgeHardRules:
    """Amount Bridge endpoint 헌법 검증"""

    def test_amount_bridge_requires_amount_bridge_axis(self):
        """
        Test5: /evidence/amount-bridge에 axis=compare → 400 + VALIDATION_ERROR
        """
        request_body = {
            "axis": "compare",  # 잘못된 axis!
            "coverage_code": "C001"
        }

        response = client.post("/evidence/amount-bridge", json=request_body)

        assert response.status_code == 400
        data = response.json()
        error = data.get("detail")
        assert error is not None
        assert error["code"] == "VALIDATION_ERROR"
        assert "amount_bridge" in error["message"].lower()
        assert "details" in error
        assert error["details"]["rule"] == "amount_bridge_axis_only"

    def test_amount_bridge_success_allows_synthetic(self):
        """
        Bonus test: /evidence/amount-bridge는 synthetic 허용
        """
        request_body = {
            "axis": "amount_bridge",
            "coverage_code": "C001",
            "options": {
                "include_synthetic": True  # 이 축에서는 허용!
            }
        }

        response = client.post("/evidence/amount-bridge", json=request_body)

        assert response.status_code == 200
        data = response.json()
        assert data["axis"] == "amount_bridge"
        assert data["coverage_code"] == "C001"
        assert "debug" in data


class TestPydanticValidation:
    """Pydantic 스키마 검증 (422)"""

    def test_missing_required_field_returns_422(self):
        """
        Bonus test: coverage_code 누락은 Pydantic 422
        """
        request_body = {
            "axis": "amount_bridge"
            # coverage_code 누락
        }

        response = client.post("/evidence/amount-bridge", json=request_body)

        assert response.status_code == 422  # Pydantic validation error


class TestCompareAxisValidation:
    """Compare endpoint axis 검증"""

    def test_compare_wrong_axis_returns_400(self):
        """
        Bonus test: /compare에 axis=amount_bridge → 400
        """
        request_body = {
            "axis": "amount_bridge",  # 잘못된 axis
            "mode": "compensation"
        }

        response = client.post("/compare", json=request_body)

        assert response.status_code == 400
        data = response.json()
        error = data.get("detail")
        assert error is not None
        assert error["code"] == "VALIDATION_ERROR"
        assert error["details"]["rule"] == "compare_axis_only"
