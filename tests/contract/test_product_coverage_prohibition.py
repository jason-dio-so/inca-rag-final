"""
STEP 7: product_coverage Prohibition Test

Constitutional requirement:
- product_coverage table is DEPRECATED (conflicts with Universe Lock)
- No code should reference product_coverage or premium tables
- This test ensures the codebase is clean of these references

If this test fails, it means someone added product_coverage back to the code.
This is a CONSTITUTIONAL VIOLATION and must be fixed immediately.
"""
import pytest
from pathlib import Path


class TestProductCoverageProhibition:
    """
    Ensure no code references deprecated product_coverage or premium tables
    """

    def test_no_product_coverage_in_python_code(self):
        """
        PROHIBITION: No Python code should reference 'product_coverage' table

        This test searches all .py files in apps/ and src/ for product_coverage references.
        Exceptions:
        - This test file itself
        - Archive documentation (docs/db/archive/)
        - Documentation files (*.md)
        """
        prohibited_pattern = "product_coverage"
        violations = []

        # Search paths
        search_paths = [
            Path("apps"),
            Path("src") if Path("src").exists() else None,
        ]
        search_paths = [p for p in search_paths if p and p.exists()]

        for search_path in search_paths:
            for py_file in search_path.rglob("*.py"):
                # Skip test files (except integration tests which should validate Universe Lock)
                if "test" in str(py_file) and "prohibition" not in str(py_file):
                    continue

                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                    # Check for prohibited pattern
                    if prohibited_pattern in content:
                        # Find line numbers
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if prohibited_pattern in line and not line.strip().startswith('#'):
                                violations.append(f"{py_file}:{i} - {line.strip()}")

        assert len(violations) == 0, \
            f"product_coverage references found (Universe Lock violation):\n" + "\n".join(violations)

    def test_no_premium_table_in_python_code(self):
        """
        PROHIBITION: No Python code should reference 'premium' table

        Exception: 'premium' mode references are OK (filter/sort mode), but not table references.
        """
        violations = []

        # Search paths
        search_paths = [
            Path("apps"),
            Path("src") if Path("src").exists() else None,
        ]
        search_paths = [p for p in search_paths if p and p.exists()]

        for search_path in search_paths:
            for py_file in search_path.rglob("*.py"):
                # Skip test files
                if "test" in str(py_file) and "prohibition" not in str(py_file):
                    continue

                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                    for i, line in enumerate(lines, 1):
                        # Check for table references (FROM premium, JOIN premium)
                        # Ignore mode references (mode="premium", "premium_mode")
                        if ("FROM premium" in line or "JOIN premium" in line or "public.premium" in line):
                            if not line.strip().startswith('#'):
                                violations.append(f"{py_file}:{i} - {line.strip()}")

        assert len(violations) == 0, \
            f"premium table references found (deprecated table):\n" + "\n".join(violations)

    def test_queries_use_universe_lock_pattern(self):
        """
        POSITIVE TEST: Verify compare queries use Universe Lock pattern

        Expected pattern:
        - FROM public.proposal_coverage_universe
        - JOIN public.proposal_coverage_mapped
        - WHERE mapping_status = 'MAPPED'
        """
        from apps.api.app.queries.compare import COVERAGE_AMOUNT_SQL

        # Verify Universe Lock pattern
        assert "proposal_coverage_universe" in COVERAGE_AMOUNT_SQL, \
            "Coverage queries MUST use proposal_coverage_universe (Universe Lock SSOT)"

        assert "proposal_coverage_mapped" in COVERAGE_AMOUNT_SQL, \
            "Coverage queries MUST use proposal_coverage_mapped (canonical mapping)"

        assert "mapping_status = 'MAPPED'" in COVERAGE_AMOUNT_SQL, \
            "Coverage queries MUST filter mapping_status = 'MAPPED'"

    def test_no_product_id_in_universe_queries(self):
        """
        PROHIBITION: Universe Lock queries should NOT use product_id as filter

        Universe Lock queries should use:
        - insurer_code (context)
        - proposal_id (universe identifier)
        - canonical_coverage_code (comparison axis)

        NOT:
        - product_id (product-centered comparison - deprecated)
        """
        from apps.api.app.queries.compare import get_coverage_amount_for_proposal
        import inspect

        sig = inspect.signature(get_coverage_amount_for_proposal)
        params = list(sig.parameters.keys())

        assert "product_id" not in params, \
            "Universe Lock queries MUST NOT use product_id parameter (use proposal_id instead)"

        assert "proposal_id" in params, \
            "Universe Lock queries MUST use proposal_id (Universe Lock identifier)"

        assert "insurer_code" in params, \
            "Universe Lock queries MUST use insurer_code (context)"
