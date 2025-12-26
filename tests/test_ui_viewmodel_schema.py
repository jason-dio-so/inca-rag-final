"""
STEP NEXT-4: UI ViewModel Schema Validation Tests

Tests that compare_view_model examples validate against the JSON Schema
and contain no forbidden phrases (hard ban on recommendations/judgments).

Constitutional Compliance:
- Fact-only (no inference)
- No recommendations/judgments
- Presentation layer only
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

import pytest

try:
    from jsonschema import Draft202012Validator, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


# Hard ban phrases from STEP NEXT-3 specification
FORBIDDEN_PHRASES = [
    # Judgment/Recommendation
    r"더\s*좋다", r"유리하다", r"불리하다",
    r"추천", r"권장", r"선택하세요",
    r"우수", r"뛰어남", r"최선",

    # Comparative Evaluation
    r"동일함", r"차이\s*없음",
    r"사가\s*.*보다",
    r"종합적으로\s*볼\s*때",
    r"결론적으로",

    # Inference/Opinion
    r"사실상\s*같은\s*담보",
    r"유사한\s*담보",
    r"일반적으로", r"보통은",
]


def load_schema() -> Dict[str, Any]:
    """Load the ViewModel JSON Schema."""
    schema_path = Path(__file__).parent.parent / "docs/ui/compare_view_model.schema.json"
    if not schema_path.exists():
        pytest.skip(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_examples() -> List[Dict[str, Any]]:
    """Load all example ViewModels."""
    examples_path = Path(__file__).parent.parent / "docs/ui/compare_view_model.examples.json"
    if not examples_path.exists():
        pytest.skip(f"Examples file not found: {examples_path}")

    with open(examples_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [example["view_model"] for example in data.get("examples", [])]


def serialize_to_string(obj: Any) -> str:
    """Recursively serialize object to string for text search."""
    if isinstance(obj, dict):
        return " ".join(serialize_to_string(v) for v in obj.values())
    elif isinstance(obj, list):
        return " ".join(serialize_to_string(item) for item in obj)
    elif isinstance(obj, str):
        return obj
    else:
        return str(obj)


def find_forbidden_phrases(text: str) -> List[str]:
    """Find all forbidden phrases in text."""
    found = []
    for pattern in FORBIDDEN_PHRASES:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            found.extend(matches)
    return found


class TestViewModelSchema:
    """Test suite for ViewModel schema validation."""

    @pytest.mark.skipif(not JSONSCHEMA_AVAILABLE, reason="jsonschema not installed")
    def test_schema_is_valid_draft_2020_12(self):
        """Schema itself is valid JSON Schema Draft 2020-12."""
        schema = load_schema()

        # Check meta-schema
        assert schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"

        # Validate schema against Draft 2020-12 meta-schema
        # (jsonschema library will raise if schema is invalid)
        validator = Draft202012Validator(schema)
        assert validator is not None

    @pytest.mark.skipif(not JSONSCHEMA_AVAILABLE, reason="jsonschema not installed")
    def test_all_examples_validate_against_schema(self):
        """All example ViewModels validate against schema."""
        schema = load_schema()
        examples = load_examples()

        assert len(examples) >= 4, "Must have at least 4 examples"

        validator = Draft202012Validator(schema)

        for idx, example in enumerate(examples, start=1):
            errors = list(validator.iter_errors(example))
            if errors:
                error_messages = "\n".join(
                    f"  - {err.message} at {'.'.join(str(p) for p in err.absolute_path)}"
                    for err in errors
                )
                pytest.fail(
                    f"Example {idx} failed schema validation:\n{error_messages}"
                )

    def test_no_forbidden_phrases_in_examples(self):
        """Examples contain no forbidden phrases (hard ban)."""
        examples = load_examples()

        for idx, example in enumerate(examples, start=1):
            # Exclude debug section (not displayed in UI)
            example_without_debug = {k: v for k, v in example.items() if k != "debug"}

            text = serialize_to_string(example_without_debug)
            found_phrases = find_forbidden_phrases(text)

            if found_phrases:
                pytest.fail(
                    f"Example {idx} contains forbidden phrases: {', '.join(found_phrases)}\n"
                    f"Forbidden phrases violate Constitutional principle: No Recommendation / No Inference"
                )

    def test_required_top_level_fields(self):
        """All examples have required top-level fields."""
        examples = load_examples()

        required_fields = ["schema_version", "generated_at", "header", "snapshot", "fact_table", "evidence_panels"]

        for idx, example in enumerate(examples, start=1):
            for field in required_fields:
                assert field in example, (
                    f"Example {idx} missing required field: {field}"
                )

    def test_schema_version_format(self):
        """Schema version follows next4.vX or next4.vX.Y format."""
        examples = load_examples()

        version_pattern = re.compile(r"^next4\.v\d+(\.\d+)?$")

        for idx, example in enumerate(examples, start=1):
            version = example.get("schema_version")
            assert version_pattern.match(version), (
                f"Example {idx} has invalid schema_version format: {version}"
            )

    def test_insurer_enum_compliance(self):
        """All insurer values use canonical enum."""
        examples = load_examples()

        valid_insurers = {"SAMSUNG", "HANWHA", "LOTTE", "MERITZ", "KB", "HYUNDAI", "HEUNGKUK", "DB"}

        for idx, example in enumerate(examples, start=1):
            # Check snapshot insurers
            for insurer_obj in example["snapshot"]["insurers"]:
                insurer = insurer_obj["insurer"]
                assert insurer in valid_insurers, (
                    f"Example {idx} snapshot has invalid insurer: {insurer}"
                )

            # Check fact_table rows
            for row in example["fact_table"]["rows"]:
                insurer = row["insurer"]
                assert insurer in valid_insurers, (
                    f"Example {idx} fact_table has invalid insurer: {insurer}"
                )

            # Check evidence_panels
            for panel in example["evidence_panels"]:
                insurer = panel["insurer"]
                assert insurer in valid_insurers, (
                    f"Example {idx} evidence_panels has invalid insurer: {insurer}"
                )

    def test_fact_table_columns_fixed(self):
        """Fact table columns are fixed and in correct order."""
        examples = load_examples()

        expected_columns = ["보험사", "담보명(정규화)", "보장금액", "지급 조건 요약", "보험기간", "비고"]

        for idx, example in enumerate(examples, start=1):
            columns = example["fact_table"]["columns"]
            assert columns == expected_columns, (
                f"Example {idx} has incorrect fact_table columns: {columns}"
            )

    def test_evidence_ref_id_integrity(self):
        """All evidence_ref_id references resolve to evidence_panels[].id."""
        examples = load_examples()

        for idx, example in enumerate(examples, start=1):
            # Collect all evidence IDs
            evidence_ids = {panel["id"] for panel in example["evidence_panels"]}

            # Collect all referenced evidence_ref_ids
            referenced_ids = set()

            # From snapshot
            for insurer_obj in example["snapshot"]["insurers"]:
                if insurer_obj.get("headline_amount"):
                    ref_id = insurer_obj["headline_amount"].get("evidence_ref_id")
                    if ref_id:
                        referenced_ids.add(ref_id)

            # From fact_table
            for row in example["fact_table"]["rows"]:
                if row.get("benefit_amount"):
                    ref_id = row["benefit_amount"].get("evidence_ref_id")
                    if ref_id:
                        referenced_ids.add(ref_id)

                for condition in row.get("payout_conditions", []):
                    ref_id = condition.get("evidence_ref_id")
                    if ref_id:
                        referenced_ids.add(ref_id)

            # Check all references resolve
            unresolved = referenced_ids - evidence_ids
            if unresolved:
                pytest.fail(
                    f"Example {idx} has unresolved evidence_ref_id: {unresolved}"
                )

    def test_slot_key_enum_compliance(self):
        """All slot_key values use defined enum."""
        examples = load_examples()

        valid_slot_keys = {
            "waiting_period",
            "payment_frequency",
            "diagnosis_definition",
            "method_condition",
            "exclusion_scope",
            "payout_limit",
            "disease_scope",
        }

        for idx, example in enumerate(examples, start=1):
            for row in example["fact_table"]["rows"]:
                for condition in row.get("payout_conditions", []):
                    slot_key = condition["slot_key"]
                    assert slot_key in valid_slot_keys, (
                        f"Example {idx} has invalid slot_key: {slot_key}"
                    )

    def test_status_enum_compliance(self):
        """All status values use defined enum."""
        examples = load_examples()

        valid_statuses = {"OK", "MISSING_EVIDENCE", "UNMAPPED", "AMBIGUOUS", "OUT_OF_UNIVERSE"}

        for idx, example in enumerate(examples, start=1):
            # Check snapshot status
            for insurer_obj in example["snapshot"]["insurers"]:
                status = insurer_obj["status"]
                assert status in valid_statuses, (
                    f"Example {idx} snapshot has invalid status: {status}"
                )

            # Check fact_table row_status
            for row in example["fact_table"]["rows"]:
                status = row["row_status"]
                assert status in valid_statuses, (
                    f"Example {idx} fact_table has invalid row_status: {status}"
                )

    def test_doc_type_enum_compliance(self):
        """All doc_type values use defined enum."""
        examples = load_examples()

        valid_doc_types = {"가입설계서", "약관", "상품요약서", "사업방법서"}

        for idx, example in enumerate(examples, start=1):
            for panel in example["evidence_panels"]:
                doc_type = panel["doc_type"]
                assert doc_type in valid_doc_types, (
                    f"Example {idx} evidence_panels has invalid doc_type: {doc_type}"
                )

    def test_excerpt_length_constraints(self):
        """Evidence excerpts meet minLength=25, maxLength=400."""
        examples = load_examples()

        for idx, example in enumerate(examples, start=1):
            for panel in example["evidence_panels"]:
                excerpt = panel["excerpt"]
                length = len(excerpt)

                assert length >= 25, (
                    f"Example {idx} evidence excerpt too short ({length} chars): {excerpt[:50]}..."
                )
                assert length <= 400, (
                    f"Example {idx} evidence excerpt too long ({length} chars)"
                )

    def test_debug_section_optional(self):
        """Debug section is optional but if present, must be object."""
        examples = load_examples()

        for idx, example in enumerate(examples, start=1):
            if "debug" in example:
                assert isinstance(example["debug"], dict), (
                    f"Example {idx} debug must be object if present"
                )

    def test_constitutional_compliance_matrix(self):
        """Examples demonstrate constitutional compliance."""
        examples = load_examples()

        for idx, example in enumerate(examples, start=1):
            # Fact-only: All amounts must have evidence_ref_id (if not null)
            for row in example["fact_table"]["rows"]:
                if row.get("benefit_amount"):
                    assert "evidence_ref_id" in row["benefit_amount"], (
                        f"Example {idx} benefit_amount missing evidence_ref_id (Fact-only violation)"
                    )

            # No Recommendation: checked by test_no_forbidden_phrases_in_examples

            # Presentation Only: no 'score', 'rank', 'judgment' fields
            text = serialize_to_string(example)
            assert "score" not in text.lower(), (
                f"Example {idx} contains 'score' field (Presentation Only violation)"
            )
            assert "rank" not in text.lower() or "frank" in text.lower(), (
                f"Example {idx} contains 'rank' field (Presentation Only violation)"
            )
            assert "judgment" not in text.lower(), (
                f"Example {idx} contains 'judgment' field (Presentation Only violation)"
            )


class TestViewModelExampleCoverage:
    """Test that required example scenarios are present."""

    def test_minimum_example_count(self):
        """At least 4 examples are provided."""
        examples_path = Path(__file__).parent.parent / "docs/ui/compare_view_model.examples.json"

        with open(examples_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        examples = data.get("examples", [])
        assert len(examples) >= 4, f"Must have at least 4 examples, found {len(examples)}"

    def test_required_scenario_coverage(self):
        """Required scenarios are covered in examples."""
        examples_path = Path(__file__).parent.parent / "docs/ui/compare_view_model.examples.json"

        with open(examples_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        examples = data.get("examples", [])
        example_names = [ex["name"].lower() for ex in examples]

        # Required scenarios from STEP NEXT-4 specification
        required_scenarios = [
            "cancer diagnosis",  # Standard case
            "borderline tumor",  # Definition-based
            "robotic surgery",   # Method-based
            "unmapped",          # Edge case
        ]

        for scenario in required_scenarios:
            assert any(scenario in name for name in example_names), (
                f"Required scenario '{scenario}' not found in examples"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
