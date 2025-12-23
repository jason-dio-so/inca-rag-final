"""
Conditions Summary Service (STEP 5-C)

LLM-based summarization of insurance coverage conditions.

Constitutional Compliance:
- PRESENTATION-ONLY: LLM used for text summarization after evidence retrieval
- INPUT: Non-synthetic evidence snippets (already filtered by queries layer)
- OUTPUT: Korean text summary or None
- FORBIDDEN: Coverage code inference, amount calculation, legal judgment

Usage Scope:
✅ Allowed: Text summarization, deduplication, user-friendly wording
❌ Forbidden: Decision-making, code inference, amount/premium calculation
"""
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def generate_conditions_summary(
    product_name: str,
    coverage_code: str,
    coverage_name: str,
    evidence_snippets: List[str],
    max_snippets: int = 5
) -> Optional[str]:
    """
    Generate conditions summary from evidence snippets.

    STEP 5-C Implementation:
    - Uses evidence snippets (non-synthetic, already filtered)
    - Generates Korean text summary
    - Returns None on failure (graceful degradation)

    Args:
        product_name: Product name
        coverage_code: Canonical coverage code
        coverage_name: Coverage name
        evidence_snippets: List of evidence content snippets
        max_snippets: Max snippets to use (default: 5)

    Returns:
        Korean text summary or None on failure

    Constitutional Guarantees:
    - No coverage_code inference
    - No amount calculation
    - No legal judgment
    - Input is pre-validated evidence only
    """
    if not evidence_snippets:
        logger.warning("No evidence snippets provided for conditions summary")
        return None

    # Limit to max_snippets
    snippets_to_use = evidence_snippets[:max_snippets]

    try:
        # STEP 5-C MINIMAL IMPLEMENTATION:
        # For now, return a simple concatenation with Korean formatting
        # LLM integration (OpenAI/Anthropic) can be added later

        # Simple rule-based summarization (fallback)
        summary_parts = []

        # Extract key information from snippets
        for i, snippet in enumerate(snippets_to_use, 1):
            # Simple heuristic: look for key patterns
            if "면책" in snippet:
                summary_parts.append(f"면책조건: {snippet[:100]}...")
            elif "감액" in snippet:
                summary_parts.append(f"감액조건: {snippet[:100]}...")
            elif "지급" in snippet and "조건" in snippet:
                summary_parts.append(f"지급조건: {snippet[:100]}...")

        if summary_parts:
            return "\n".join(summary_parts[:3])  # Limit to 3 key points
        else:
            # Generic fallback
            return f"보장 조건: {snippets_to_use[0][:200]}..." if snippets_to_use else None

    except Exception as e:
        logger.error(f"Failed to generate conditions summary: {str(e)}")
        return None  # Graceful degradation


# Future LLM integration placeholder
def _generate_with_llm(
    product_name: str,
    coverage_code: str,
    coverage_name: str,
    snippets: List[str]
) -> Optional[str]:
    """
    LLM-based summary generation (placeholder for future implementation).

    When implemented, this should:
    1. Construct prompt with evidence snippets
    2. Call LLM API (OpenAI/Anthropic)
    3. Parse and validate response
    4. Return Korean summary or None

    FORBIDDEN:
    - Coverage code inference
    - Amount calculation
    - Legal judgment
    - Decision-making

    ALLOWED:
    - Text summarization
    - Deduplication
    - User-friendly wording
    - Structuring
    """
    # TODO: Implement LLM integration
    # For now, return None to use fallback
    return None
