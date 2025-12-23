"""
Amount extraction utilities for STEP 5-B

Simple regex-based extraction from chunk content.
Minimal implementation - extraction quality not critical for STEP 5-B validation.
"""
import re
from typing import Optional, Tuple
from ..schemas.evidence import AmountContextType


def extract_amount_from_text(text: str) -> Tuple[Optional[int], Optional[str], AmountContextType]:
    """
    Extract amount information from chunk text.

    Returns:
        (amount_value_krw, amount_text, context_type)

    Examples:
        "600만원" -> (6000000, "600만원", ...)
        "3억원" -> (300000000, "3억원", ...)
        "5천만원" -> (50000000, "5천만원", ...)
    """
    if not text:
        return (None, None, AmountContextType.other)

    # Pattern: 숫자 + 단위 (억/만/천만)
    patterns = [
        (r'(\d+(?:,\d{3})*)\s*억\s*원?', 100000000),
        (r'(\d+(?:,\d{3})*)\s*천만\s*원?', 10000000),
        (r'(\d+(?:,\d{3})*)\s*만\s*원?', 10000),
        (r'(\d+(?:,\d{3})*)\s*원', 1),
    ]

    amount_value = None
    amount_text = None

    for pattern, multiplier in patterns:
        match = re.search(pattern, text)
        if match:
            num_str = match.group(1).replace(',', '')
            amount_value = int(num_str) * multiplier
            amount_text = match.group(0)
            break

    # Detect context type (simple keyword matching)
    context_type = AmountContextType.other
    if amount_text:
        text_lower = text.lower()
        if any(kw in text_lower for kw in ['진단', 'diagnosis']):
            context_type = AmountContextType.payment
        elif any(kw in text_lower for kw in ['한도', 'limit', '최고']):
            context_type = AmountContextType.limit
        elif any(kw in text_lower for kw in ['회', '횟수', 'count']):
            context_type = AmountContextType.count
        else:
            context_type = AmountContextType.payment  # default to payment

    return (amount_value, amount_text, context_type)
