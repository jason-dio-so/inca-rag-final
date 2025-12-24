"""
Proposal Coverage Universe Lock System

Implementation of Constitution v1.0 + Amendment v1.0.1 (Article VIII)
Slot Schema v1.1.1

Principle: "가입설계서에 있는 담보만 비교 대상"
"""

from .parser import ProposalCoverageParser
from .mapper import CoverageMapper
from .extractor import SlotExtractor
from .compare import CompareEngine, ComparisonResult

__all__ = [
    "ProposalCoverageParser",
    "CoverageMapper",
    "SlotExtractor",
    "CompareEngine",
    "ComparisonResult",
]
