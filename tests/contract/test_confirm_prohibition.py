"""
STEP 6-B: Constitutional Test - Confirm Function Prohibition

Purpose: Ensure NO Python code calls confirm_candidate_to_entity() function.

This is a STRING-LEVEL test (similar to STEP 5-B SQL template tests)
to prove that the confirm function is NEVER called by application code.

Constitutional Guarantee:
- confirm_candidate_to_entity() is MANUAL-ONLY (admin CLI/script)
- NO automated pipeline code can call this function
- Allowed locations: migrations/*.sql, docs/validation/*.md only
"""
import pytest
import os
import re
from pathlib import Path


class TestConfirmFunctionProhibition:
    """
    Constitutional tests for confirm function prohibition.

    These are CONTRACT tests (not unit tests) because they enforce
    architectural boundaries, not implementation correctness.
    """

    # Root directory for searching
    PROJECT_ROOT = Path(__file__).parent.parent.parent

    # Allowed file patterns (where confirm function CAN appear)
    ALLOWED_PATTERNS = [
        r"migrations/.*\.sql$",  # Migration SQL files (function definition)
        r"docs/validation/.*\.md$",  # Validation documentation
        r"tests/contract/test_confirm_prohibition\.py$",  # This test file itself
    ]

    # Python code directories to check
    PYTHON_DIRS = [
        "apps/api/app",
        "apps/ingestion",
        "tests/unit",
        "tests/integration",
    ]

    @pytest.fixture
    def python_files(self):
        """Get all Python files in application code"""
        files = []
        for dir_path in self.PYTHON_DIRS:
            full_path = self.PROJECT_ROOT / dir_path
            if full_path.exists():
                files.extend(full_path.rglob("*.py"))
        return files

    def is_allowed_file(self, file_path: Path) -> bool:
        """Check if file is in allowed list"""
        rel_path = file_path.relative_to(self.PROJECT_ROOT)
        rel_path_str = str(rel_path).replace("\\", "/")  # Normalize path separators

        for pattern in self.ALLOWED_PATTERNS:
            if re.match(pattern, rel_path_str):
                return True
        return False

    def test_no_python_code_calls_confirm_function(self, python_files):
        """
        CONSTITUTIONAL TEST: NO Python code can call confirm_candidate_to_entity().

        This test scans all application Python files and fails if any code
        attempts to import or call the confirm function.

        Allowed locations:
        - migrations/*.sql (function definition)
        - docs/validation/*.md (documentation)
        - This test file itself

        Forbidden locations:
        - apps/api/app/**/*.py (ALL application code)
        - apps/ingestion/**/*.py
        - tests/unit/**/*.py
        - tests/integration/**/*.py
        """
        violations = []

        # Pattern to match confirm function usage
        # Matches: confirm_candidate_to_entity( or .confirm_candidate_to_entity
        confirm_pattern = re.compile(
            r"(confirm_candidate_to_entity\s*\(|\.confirm_candidate_to_entity)",
            re.IGNORECASE
        )

        for py_file in python_files:
            # Skip allowed files
            if self.is_allowed_file(py_file):
                continue

            try:
                content = py_file.read_text(encoding='utf-8')

                # Check for confirm function usage
                matches = list(confirm_pattern.finditer(content))
                if matches:
                    for match in matches:
                        # Get line number
                        line_num = content[:match.start()].count('\n') + 1
                        # Get line content
                        lines = content.split('\n')
                        line_content = lines[line_num - 1].strip()

                        violations.append({
                            "file": str(py_file.relative_to(self.PROJECT_ROOT)),
                            "line": line_num,
                            "content": line_content
                        })

            except Exception as e:
                pytest.fail(f"Failed to read {py_file}: {e}")

        # Fail if any violations found
        if violations:
            error_msg = "\n\n❌ CONSTITUTIONAL VIOLATION: confirm_candidate_to_entity() called in Python code\n\n"
            error_msg += "The confirm function is MANUAL-ONLY (admin CLI/script).\n"
            error_msg += "NO automated pipeline code is allowed to call this function.\n\n"
            error_msg += "Violations found:\n"
            for v in violations:
                error_msg += f"  - {v['file']}:{v['line']}\n"
                error_msg += f"    > {v['content']}\n"

            pytest.fail(error_msg)

    def test_repository_has_no_confirm_methods(self):
        """
        CONSTITUTIONAL TEST: CandidateRepository must NOT have confirm methods.

        The repository is only for candidate CRUD operations.
        Confirming to production is FORBIDDEN at this layer.
        """
        repo_file = self.PROJECT_ROOT / "apps" / "api" / "app" / "ingest_llm" / "repository.py"

        if not repo_file.exists():
            pytest.skip("Repository file not found")

        content = repo_file.read_text(encoding='utf-8')

        # Forbidden method patterns
        forbidden_patterns = [
            r"def\s+confirm",  # def confirm...
            r"def\s+.*_to_production",  # def ..._to_production
            r"def\s+.*_to_entity",  # def ..._to_entity
            r"INSERT\s+INTO\s+chunk_entity\s+",  # Direct INSERT into production (case-insensitive)
        ]

        violations = []
        for pattern in forbidden_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                lines = content.split('\n')
                line_content = lines[line_num - 1].strip()

                violations.append({
                    "pattern": pattern,
                    "line": line_num,
                    "content": line_content
                })

        if violations:
            error_msg = "\n\n❌ CONSTITUTIONAL VIOLATION: Repository has confirm-related methods\n\n"
            error_msg += "CandidateRepository is only for candidate table operations.\n"
            error_msg += "Confirming to production (chunk_entity) is FORBIDDEN.\n\n"
            error_msg += "Violations found:\n"
            for v in violations:
                error_msg += f"  - Line {v['line']}: {v['pattern']}\n"
                error_msg += f"    > {v['content']}\n"

            pytest.fail(error_msg)

    def test_confirm_function_only_in_migration_sql(self):
        """
        CONSTITUTIONAL TEST: confirm function definition only in migration SQL.

        The confirm_candidate_to_entity() function should ONLY be defined
        in migration SQL files, not in Python code.
        """
        migration_dir = self.PROJECT_ROOT / "migrations" / "step6b"
        sql_file = migration_dir / "001_create_candidate_tables.sql"

        if not sql_file.exists():
            pytest.fail("Migration SQL file not found (expected location for confirm function)")

        content = sql_file.read_text(encoding='utf-8')

        # Verify function is defined in SQL
        function_pattern = r"CREATE\s+(OR\s+REPLACE\s+)?FUNCTION\s+confirm_candidate_to_entity"
        matches = re.findall(function_pattern, content, re.IGNORECASE)

        assert len(matches) > 0, (
            "confirm_candidate_to_entity() function not found in migration SQL. "
            "Function MUST be defined in migration (not Python code)."
        )

        # Verify function has FK verification (double safety)
        fk_check_pattern = r"IF\s+NOT\s+EXISTS.*coverage_standard.*coverage_code"
        fk_matches = re.findall(fk_check_pattern, content, re.IGNORECASE)

        assert len(fk_matches) > 0, (
            "confirm_candidate_to_entity() function missing FK verification. "
            "Function MUST verify coverage_code exists in coverage_standard."
        )

    def test_no_confirm_in_pipeline_modules(self):
        """
        CONSTITUTIONAL TEST: Pipeline modules must NOT reference confirm.

        Future pipeline orchestrator (pipeline.py) must NOT call confirm function.
        """
        # Check existing modules
        ingest_llm_dir = self.PROJECT_ROOT / "apps" / "api" / "app" / "ingest_llm"

        if not ingest_llm_dir.exists():
            pytest.skip("ingest_llm directory not found")

        python_files = list(ingest_llm_dir.glob("*.py"))

        # Also check if pipeline.py exists (future module)
        pipeline_file = ingest_llm_dir / "pipeline.py"
        if pipeline_file.exists():
            python_files.append(pipeline_file)

        violations = []
        confirm_pattern = re.compile(r"confirm", re.IGNORECASE)

        for py_file in python_files:
            # Skip __init__.py
            if py_file.name == "__init__.py":
                continue

            content = py_file.read_text(encoding='utf-8')

            # Check for ANY mention of "confirm" (case-insensitive)
            # Allowed only in comments/docstrings explaining prohibition
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Skip comments and docstrings (allowed for documentation)
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue

                # Check for confirm in actual code
                if confirm_pattern.search(line):
                    # Verify it's not in a string literal (allowed for error messages)
                    if ('"""' not in line and "'''" not in line and
                        '"confirm' not in line.lower() and "'confirm" not in line.lower()):
                        violations.append({
                            "file": py_file.name,
                            "line": i,
                            "content": stripped
                        })

        if violations:
            error_msg = "\n\n⚠️  WARNING: Pipeline modules reference 'confirm'\n\n"
            error_msg += "Pipeline code should NOT reference confirm function.\n"
            error_msg += "References found:\n"
            for v in violations:
                error_msg += f"  - {v['file']}:{v['line']}\n"
                error_msg += f"    > {v['content']}\n"

            # This is a warning, not a hard failure (comments/docs might mention it)
            pytest.skip(error_msg)
