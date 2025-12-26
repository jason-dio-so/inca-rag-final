"""
Tests for ViewModel assembler.

Validates:
1. ProposalCompareResponse → ViewModel assembly
2. Schema compliance (JSON Schema Draft 2020-12)
3. Evidence reference integrity
4. Hard-ban phrase detection
5. Deterministic output (reproducibility)

Constitutional Compliance:
- Fact-only (no inference)
- No recommendations/judgments
- Presentation layer only
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import pytest

# Import assembler and types
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "apps/api"))

from app.schemas.compare import (
    ProposalCompareResponse,
    ProposalCoverageItem,
    PolicyEvidence
)
from app.view_model.assembler import assemble_view_model
from app.view_model.schema_loader import load_schema, validate_view_model


# Hard ban phrases (from STEP NEXT-4)
FORBIDDEN_PHRASES = [
    r"더\s*좋다", r"유리하다", r"불리하다",
    r"추천", r"권장", r"선택하세요",
    r"우수", r"뛰어남", r"최선",
    r"동일함", r"차이\s*없음",
    r"사가\s*.*보다",
    r"종합적으로\s*볼\s*때",
    r"결론적으로",
    r"사실상\s*같은\s*담보",
    r"유사한\s*담보",
    r"일반적으로", r"보통은",
]


def find_forbidden_phrases(text: str) -> list:
    """Find forbidden phrases in text."""
    found = []
    for pattern in FORBIDDEN_PHRASES:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            found.extend(matches)
    return found


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


# Golden sample fixtures
@pytest.fixture
def sample_comparable_response():
    """Golden sample: Scenario A (comparable, both MAPPED)"""
    return ProposalCompareResponse(
        query="일반암진단비",
        comparison_result="comparable",
        next_action="COMPARE",
        coverage_a=ProposalCoverageItem(
            insurer="SAMSUNG",
            proposal_id="PROP_SAMSUNG_001",
            coverage_name_raw="일반암 진단비",
            canonical_coverage_code="CA_DIAG_GENERAL",
            mapping_status="MAPPED",
            amount_value=30000000,
            disease_scope_raw="유사암 제외",
            disease_scope_norm=None,
            source_confidence="proposal_confirmed"
        ),
        coverage_b=ProposalCoverageItem(
            insurer="MERITZ",
            proposal_id="PROP_MERITZ_001",
            coverage_name_raw="일반암 진단금",
            canonical_coverage_code="CA_DIAG_GENERAL",
            mapping_status="MAPPED",
            amount_value=30000000,
            disease_scope_raw="유사암, 갑상선암 제외",
            disease_scope_norm=None,
            source_confidence="proposal_confirmed"
        ),
        message="Both insurers have CA_DIAG_GENERAL",
        ux_message_code="COVERAGE_MATCH_COMPARABLE",
        debug={"canonical_code_resolved": "CA_DIAG_GENERAL"}
    )


@pytest.fixture
def sample_unmapped_response():
    """Golden sample: Scenario B (UNMAPPED)"""
    return ProposalCompareResponse(
        query="매핑안된담보",
        comparison_result="unmapped",
        next_action="REQUEST_MORE_INFO",
        coverage_a=ProposalCoverageItem(
            insurer="SAMSUNG",
            proposal_id="PROP_SAMSUNG_002",
            coverage_name_raw="신종수술비",
            canonical_coverage_code=None,
            mapping_status="UNMAPPED",
            amount_value=2000000,
            disease_scope_raw=None,
            disease_scope_norm=None,
            source_confidence="unknown"
        ),
        coverage_b=None,
        message="신종수술비 is not mapped to canonical coverage code",
        ux_message_code="COVERAGE_UNMAPPED",
        debug={"raw_name_used": "매핑안된담보"}
    )


@pytest.fixture
def sample_out_of_universe_response():
    """Golden sample: Scenario - OUT_OF_UNIVERSE"""
    return ProposalCompareResponse(
        query="존재하지않는담보",
        comparison_result="out_of_universe",
        next_action="REQUEST_MORE_INFO",
        coverage_a=None,
        coverage_b=None,
        message="'존재하지않는담보' coverage not found in SAMSUNG proposal universe",
        ux_message_code="COVERAGE_NOT_IN_UNIVERSE",
        debug={}
    )


@pytest.fixture
def sample_with_policy_evidence_response():
    """Golden sample: Scenario C (policy evidence required)"""
    return ProposalCompareResponse(
        query="유사암진단금",
        comparison_result="policy_required",
        next_action="VERIFY_POLICY",
        coverage_a=ProposalCoverageItem(
            insurer="SAMSUNG",
            proposal_id="PROP_SAMSUNG_003",
            coverage_name_raw="유사암 진단비",
            canonical_coverage_code="CA_DIAG_SIMILAR",
            mapping_status="MAPPED",
            amount_value=3000000,
            disease_scope_raw="유사암 5종",
            disease_scope_norm={"include_group_id": "SIMILAR_CANCER_SAMSUNG_V1"},
            source_confidence="policy_required"
        ),
        coverage_b=None,
        policy_evidence_a=PolicyEvidence(
            group_name="유사암 5종 (삼성)",
            insurer="SAMSUNG",
            member_count=5
        ),
        message="Disease scope verification required for 유사암 진단비",
        ux_message_code="DISEASE_SCOPE_VERIFICATION_REQUIRED",
        debug={"canonical_code_resolved": "CA_DIAG_SIMILAR"}
    )


class TestViewModelAssembler:
    """Test suite for ViewModel assembler."""

    def test_assembler_output_validates_against_schema(self, sample_comparable_response):
        """Assembled ViewModel validates against JSON Schema."""
        view_model = assemble_view_model(sample_comparable_response)
        view_model_dict = view_model.model_dump(mode="json")

        # Load schema and validate
        schema = load_schema()
        # This will raise ValidationError if invalid
        validate_view_model(view_model_dict, schema)

    def test_evidence_ref_id_integrity(self, sample_comparable_response):
        """All evidence_ref_id references resolve to evidence_panels[].id."""
        view_model = assemble_view_model(sample_comparable_response)
        view_model_dict = view_model.model_dump(mode="json")

        # Collect all evidence IDs
        evidence_ids = {panel["id"] for panel in view_model_dict["evidence_panels"]}

        # Collect all referenced evidence_ref_ids
        referenced_ids = set()

        # From snapshot
        for insurer_obj in view_model_dict["snapshot"]["insurers"]:
            if insurer_obj.get("headline_amount"):
                ref_id = insurer_obj["headline_amount"].get("evidence_ref_id")
                if ref_id:
                    referenced_ids.add(ref_id)

        # From fact_table
        for row in view_model_dict["fact_table"]["rows"]:
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
        assert not unresolved, f"Unresolved evidence_ref_id: {unresolved}"

    def test_no_forbidden_phrases_in_system_fields(self, sample_comparable_response):
        """System-generated fields contain no forbidden phrases."""
        view_model = assemble_view_model(sample_comparable_response)
        view_model_dict = view_model.model_dump(mode="json")

        # Exclude user_query (user input is allowed to contain anything)
        view_model_without_user_query = {
            k: v for k, v in view_model_dict.items()
            if k != "header"
        }

        # Also include header but without user_query
        if "header" in view_model_dict:
            view_model_without_user_query["header"] = {
                k: v for k, v in view_model_dict["header"].items()
                if k != "user_query"
            }

        # Exclude debug (not displayed in UI)
        if "debug" in view_model_without_user_query:
            del view_model_without_user_query["debug"]

        text = serialize_to_string(view_model_without_user_query)
        found_phrases = find_forbidden_phrases(text)

        assert not found_phrases, (
            f"Forbidden phrases found in system fields: {', '.join(found_phrases)}\n"
            f"Constitutional violation: No Recommendation / No Inference"
        )

    def test_schema_version_format(self, sample_comparable_response):
        """Schema version follows next4.vX or next4.vX.Y format."""
        view_model = assemble_view_model(sample_comparable_response)

        version_pattern = re.compile(r"^next4\.v\d+(\.\d+)?$")
        assert version_pattern.match(view_model.schema_version), (
            f"Invalid schema_version format: {view_model.schema_version}"
        )

    def test_deterministic_output(self, sample_comparable_response):
        """Same input → same output (deterministic)."""
        view_model_1 = assemble_view_model(sample_comparable_response)
        view_model_2 = assemble_view_model(sample_comparable_response)

        # Convert to dict and remove generated_at (timestamp varies)
        dict_1 = view_model_1.model_dump(mode="json")
        dict_2 = view_model_2.model_dump(mode="json")

        dict_1["generated_at"] = "REMOVED_FOR_COMPARISON"
        dict_2["generated_at"] = "REMOVED_FOR_COMPARISON"

        assert dict_1 == dict_2, "Assembler is not deterministic"

    def test_fact_table_columns_fixed(self, sample_comparable_response):
        """Fact table columns are fixed and in correct order."""
        view_model = assemble_view_model(sample_comparable_response)

        expected_columns = ["보험사", "담보명(정규화)", "보장금액", "지급 조건 요약", "보험기간", "비고"]
        assert view_model.fact_table.columns == expected_columns

    def test_fact_table_deterministic_sort(self, sample_comparable_response):
        """Fact table rows are sorted deterministically (insurer, coverage_title)."""
        view_model = assemble_view_model(sample_comparable_response)

        rows = view_model.fact_table.rows
        if len(rows) >= 2:
            # Check sorting: row[0].insurer <= row[1].insurer
            assert (rows[0].insurer, rows[0].coverage_title_normalized) <= \
                   (rows[1].insurer, rows[1].coverage_title_normalized), \
                   "Fact table rows not sorted deterministically"

    def test_unmapped_status_mapping(self, sample_unmapped_response):
        """UNMAPPED coverage maps to UNMAPPED status."""
        view_model = assemble_view_model(sample_unmapped_response)

        # Check snapshot status
        assert view_model.snapshot.insurers[0].status == "UNMAPPED"

        # Check fact_table row_status
        assert view_model.fact_table.rows[0].row_status == "UNMAPPED"

        # Check note_text
        assert view_model.fact_table.rows[0].note_text == "(UNMAPPED)"

    def test_out_of_universe_handling(self, sample_out_of_universe_response):
        """OUT_OF_UNIVERSE response handled correctly."""
        view_model = assemble_view_model(sample_out_of_universe_response)

        # No insurers in snapshot (no coverage found)
        assert len(view_model.snapshot.insurers) == 0

        # No fact_table rows
        assert len(view_model.fact_table.rows) == 0

        # Evidence panels empty
        assert len(view_model.evidence_panels) == 0

        # Debug warning present
        assert view_model.debug is not None
        assert "OUT_OF_UNIVERSE" in " ".join(view_model.debug.warnings or [])

    def test_policy_evidence_added_to_panels(self, sample_with_policy_evidence_response):
        """Policy evidence added to evidence_panels."""
        view_model = assemble_view_model(sample_with_policy_evidence_response)

        # Check policy evidence in panels
        policy_panels = [
            panel for panel in view_model.evidence_panels
            if panel.doc_type == "약관"
        ]

        assert len(policy_panels) >= 1, "Policy evidence not added to panels"

        # Check excerpt contains group name
        assert any("유사암 5종" in panel.excerpt for panel in policy_panels)

    def test_amount_formatting(self, sample_comparable_response):
        """Amount values formatted correctly (만원 unit)."""
        view_model = assemble_view_model(sample_comparable_response)

        # Check snapshot amount
        amount = view_model.snapshot.insurers[0].headline_amount
        assert amount is not None
        assert amount.amount_unit == "만원"
        assert amount.amount_value == 3000  # 30000000원 = 3000만원
        assert amount.display_text == "3,000만원"

    def test_debug_section_optional(self, sample_comparable_response):
        """Debug section is optional and can be excluded."""
        view_model_with_debug = assemble_view_model(sample_comparable_response, include_debug=True)
        view_model_without_debug = assemble_view_model(sample_comparable_response, include_debug=False)

        assert view_model_with_debug.debug is not None
        assert view_model_without_debug.debug is None

    def test_canonical_coverage_code_in_debug(self, sample_comparable_response):
        """Canonical coverage codes present in debug (not UI)."""
        view_model = assemble_view_model(sample_comparable_response)

        # Debug contains resolved codes
        assert view_model.debug is not None
        assert view_model.debug.resolved_coverage_codes is not None
        assert "CA_DIAG_GENERAL" in view_model.debug.resolved_coverage_codes

        # UI fields (snapshot/fact_table) use normalized coverage names, not raw codes
        # (canonical_coverage_code is the normalized name)
        assert view_model.snapshot.comparison_basis == "CA_DIAG_GENERAL"

    def test_excerpt_length_constraints(self, sample_comparable_response):
        """Evidence excerpts meet minLength=25 constraint."""
        view_model = assemble_view_model(sample_comparable_response)

        for panel in view_model.evidence_panels:
            assert len(panel.excerpt) >= 25, (
                f"Excerpt too short ({len(panel.excerpt)} chars): {panel.excerpt}"
            )

    def test_insurer_codes_uppercase(self, sample_comparable_response):
        """Insurer codes are uppercase (canonical format)."""
        view_model = assemble_view_model(sample_comparable_response)

        # Check snapshot
        for insurer_obj in view_model.snapshot.insurers:
            assert insurer_obj.insurer.isupper(), f"Insurer not uppercase: {insurer_obj.insurer}"

        # Check fact_table
        for row in view_model.fact_table.rows:
            assert row.insurer.isupper(), f"Insurer not uppercase: {row.insurer}"

        # Check evidence_panels
        for panel in view_model.evidence_panels:
            assert panel.insurer.isupper(), f"Insurer not uppercase: {panel.insurer}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
