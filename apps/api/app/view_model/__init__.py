"""
ViewModel module for UI presentation layer.

This module converts backend comparison results into ViewModel JSON
that matches the UI contract (compare_view_model.schema.json).

Constitutional Principles:
- Fact-only (no inference)
- No recommendations/judgments
- Presentation layer only (no business logic)
- Canonical coverage rule (Shinjungwon unified codes)
"""

from .assembler import assemble_view_model
from .schema_loader import load_schema, validate_view_model
from .types import ViewModel

__all__ = ["assemble_view_model", "load_schema", "validate_view_model", "ViewModel"]
