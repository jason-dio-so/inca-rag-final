"""
Deterministic compiler implementation.

Constitutional Principles:
- No LLM, no inference
- Rule-based compilation only
- Same input → same output (determinism)
- No recommendation/judgment

Compilation Process:
1. Normalize input selections
2. Apply deterministic rules
3. Build ProposalCompareRequest
4. Generate debug trace
"""

from typing import Dict, List, Any, Optional
from .schemas import CompileInput, CompileOutput, CompilerDebug
from .rules import (
    detect_surgery_method,
    detect_cancer_subtypes,
    detect_comparison_focus,
    resolve_coverage_domain,
    get_main_coverage_priority,
    SurgeryMethod,
    CancerSubtype,
    ComparisonFocus,
)
from .version import RULE_VERSION


def compile_request(input_data: CompileInput) -> CompileOutput:
    """
    Compile user selections into ProposalCompareRequest.

    Constitutional Compliance:
    - Deterministic (same input → same output)
    - No LLM inference
    - Rule-based only

    Args:
        input_data: CompileInput with user selections

    Returns:
        CompileOutput with compiled_request and compiler_debug
    """
    trace: List[str] = []
    warnings: List[str] = []
    selected_slots: Dict[str, Any] = {}

    # Step 1: Normalize insurers
    trace.append("Step 1: Normalize insurers")
    if len(input_data.selected_insurers) < 2:
        warnings.append("Less than 2 insurers selected")
    selected_slots["insurers"] = input_data.selected_insurers
    trace.append(f"  → Selected insurers: {input_data.selected_insurers}")

    # Step 2: Normalize comparison basis
    trace.append("Step 2: Normalize comparison basis")
    if input_data.selected_comparison_basis:
        selected_slots["comparison_basis"] = input_data.selected_comparison_basis
        trace.append(f"  → Comparison basis: {input_data.selected_comparison_basis}")
    else:
        # Try to infer from query using deterministic rules
        detected_domain = None
        for coverage_name, domain in [
            ("암진단비", "cancer"),
            ("일반암진단비", "cancer"),
            ("수술비", "surgery"),
        ]:
            if coverage_name in input_data.user_query:
                detected_domain = domain
                main_coverage = get_main_coverage_priority(domain)
                if main_coverage:
                    selected_slots["comparison_basis"] = main_coverage[0]
                    trace.append(f"  → Auto-detected domain: {domain}")
                    trace.append(f"  → Using main coverage: {main_coverage[0]}")
                break

        if not detected_domain:
            warnings.append("No comparison basis specified and could not auto-detect")
            trace.append("  → No comparison basis detected")

    # Step 3: Process options
    trace.append("Step 3: Process options")
    if input_data.options:
        # Surgery method
        if input_data.options.surgery_method:
            selected_slots["surgery_method"] = input_data.options.surgery_method
            trace.append(f"  → Surgery method: {input_data.options.surgery_method}")

        # Cancer subtypes
        if input_data.options.cancer_subtypes:
            selected_slots["cancer_subtypes"] = input_data.options.cancer_subtypes
            trace.append(f"  → Cancer subtypes: {input_data.options.cancer_subtypes}")

        # Comparison focus
        if input_data.options.comparison_focus:
            selected_slots["comparison_focus"] = input_data.options.comparison_focus
            trace.append(f"  → Comparison focus: {input_data.options.comparison_focus}")
    else:
        trace.append("  → No options specified")

    # Step 4: Build compiled request
    trace.append("Step 4: Build ProposalCompareRequest")

    compiled_request: Dict[str, Any] = {
        "query": selected_slots.get("comparison_basis", input_data.user_query),
        "include_policy_evidence": True,
    }

    # Add insurers if exactly 2 selected
    if len(input_data.selected_insurers) >= 2:
        compiled_request["insurer_a"] = input_data.selected_insurers[0]
        compiled_request["insurer_b"] = input_data.selected_insurers[1]
        trace.append(f"  → insurer_a: {input_data.selected_insurers[0]}")
        trace.append(f"  → insurer_b: {input_data.selected_insurers[1]}")

    trace.append(f"  → Final query: {compiled_request['query']}")

    # Step 5: Build compiler debug
    trace.append("Step 5: Finalize compiler debug")

    compiler_debug = CompilerDebug(
        rule_version=RULE_VERSION,
        resolved_coverage_codes=None,  # Will be filled by compare endpoint
        selected_slots=selected_slots,
        decision_trace=trace,
        warnings=warnings,
    )

    trace.append(f"  → Total warnings: {len(warnings)}")
    trace.append(f"  → Compilation complete (rule_version={RULE_VERSION})")

    return CompileOutput(
        compiled_request=compiled_request,
        compiler_debug=compiler_debug,
    )


def detect_clarification_needed(query: str, insurers: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Detect if clarification is needed (deterministic).

    Constitutional Compliance:
    - No LLM inference
    - Rule-based detection only
    - Returns structured clarification requirements

    Args:
        query: User query string
        insurers: Selected insurers (optional)

    Returns:
        Dict with clarification_needed flag and required_selections
    """
    required_selections = []

    # Check insurer selection
    if not insurers or len(insurers) < 2:
        required_selections.append({
            "type": "insurers",
            "reason": "Need at least 2 insurers to compare",
            "min_required": 2,
        })

    # Check for surgery method keywords
    surgery_method = detect_surgery_method(query)
    if any(kw in query.lower() for kw in ["다빈치", "로봇", "복강경"]):
        if not surgery_method or surgery_method == SurgeryMethod.UNKNOWN:
            required_selections.append({
                "type": "surgery_method",
                "reason": "Query mentions surgery method but it's ambiguous",
                "options": ["da_vinci", "robot", "laparoscopic", "any"],
            })

    # Check for cancer subtype keywords
    cancer_subtypes = detect_cancer_subtypes(query)
    if any(kw in query.lower() for kw in ["제자리암", "경계성", "유사암"]):
        if len(cancer_subtypes) > 1:
            required_selections.append({
                "type": "cancer_subtypes",
                "reason": "Query mentions multiple cancer subtypes",
                "detected": [s.value for s in cancer_subtypes],
                "options": ["제자리암", "경계성종양", "유사암", "일반암"],
            })

    # Check for comparison focus
    comparison_focus = detect_comparison_focus(query)
    if not comparison_focus:
        required_selections.append({
            "type": "comparison_focus",
            "reason": "Comparison focus unclear (amount vs definition vs condition)",
            "options": ["amount", "definition", "condition"],
        })

    return {
        "clarification_needed": len(required_selections) > 0,
        "required_selections": required_selections,
    }
