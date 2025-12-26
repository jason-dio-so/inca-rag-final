"""
Compiler version management.

Constitutional Principle:
- Rule version must be tracked for determinism
- Same version → same compilation rules
"""

COMPILER_VERSION = "1.0.0"
RULE_VERSION = "v1.0.0-next6"

# Version history
# v1.0.0-next6: Initial deterministic compiler (STEP NEXT-6)
#   - Support surgery_method (da_vinci, robot, laparoscopic, any)
#   - Support cancer_subtypes (제자리암, 경계성종양, 유사암, 일반암)
#   - Support comparison_focus (amount, definition, condition)
#   - No LLM, no inference, rule-based only
