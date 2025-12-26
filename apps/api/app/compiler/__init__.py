"""
Deterministic compiler module.

Constitutional Principles:
- No LLM, no inference
- Rule-based compilation only
- Deterministic (same input → same output)
"""

from .compiler import compile_request, detect_clarification_needed
from .schemas import CompileInput, CompileOutput, CompilerDebug, CompileOptions
from .rules import (
    SurgeryMethod,
    CancerSubtype,
    ComparisonFocus,
    detect_surgery_method,
    detect_cancer_subtypes,
    detect_comparison_focus,
)
from .version import COMPILER_VERSION, RULE_VERSION

__all__ = [
    "compile_request",
    "detect_clarification_needed",
    "CompileInput",
    "CompileOutput",
    "CompilerDebug",
    "CompileOptions",
    "SurgeryMethod",
    "CancerSubtype",
    "ComparisonFocus",
    "detect_surgery_method",
    "detect_cancer_subtypes",
    "detect_comparison_focus",
    "COMPILER_VERSION",
    "RULE_VERSION",
]
