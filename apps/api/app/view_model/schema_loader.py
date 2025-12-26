"""
Schema loader and validator for ViewModel JSON Schema.

Loads the canonical schema from docs/ui/compare_view_model.schema.json
and provides runtime validation.
"""

import json
from pathlib import Path
from typing import Any, Dict

try:
    from jsonschema import Draft202012Validator, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


# Schema file path (relative to project root)
SCHEMA_PATH = Path(__file__).parent.parent.parent.parent.parent / "docs/ui/compare_view_model.schema.json"


def load_schema() -> Dict[str, Any]:
    """
    Load the ViewModel JSON Schema from canonical location.

    Returns:
        Dict containing the JSON Schema

    Raises:
        FileNotFoundError: If schema file not found
        json.JSONDecodeError: If schema is invalid JSON
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_view_model(view_model: Dict[str, Any], schema: Dict[str, Any] = None) -> None:
    """
    Validate ViewModel against JSON Schema.

    Args:
        view_model: ViewModel JSON to validate
        schema: JSON Schema (if None, loads from canonical location)

    Raises:
        ImportError: If jsonschema library not available
        ValidationError: If validation fails
    """
    if not JSONSCHEMA_AVAILABLE:
        raise ImportError("jsonschema library required for validation. Install with: pip install jsonschema")

    if schema is None:
        schema = load_schema()

    validator = Draft202012Validator(schema)

    # This will raise ValidationError if validation fails
    validator.validate(view_model)
