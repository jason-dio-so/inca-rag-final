"""
Policy Scope Pipeline (STEP 7 + STEP 8)

STEP 7 Phase B: disease_scope_norm population from policy documents
STEP 8: Multi-insurer expansion (3+ insurers)

Constitutional principles:
- KCD-7 single source of truth (disease_code_master)
- Group-based normalization (disease_code_group)
- Evidence required at every level
- Deterministic extraction only (no LLM)
- Multi-insurer comparison with explainable reasons
"""
from .parser import PolicyScopeParser  # STEP 7 legacy (keep for compatibility)
from .pipeline import PolicyScopePipeline
from .registry import PolicyParserRegistry
from .base_parser import BasePolicyParser, DiseaseGroupDefinition, CoverageScopeDefinition

# Auto-register parsers
from .parsers import SamsungPolicyParser, MeritzPolicyParser, DBPolicyParser

# Register all parsers on module import
PolicyParserRegistry.register(SamsungPolicyParser())
PolicyParserRegistry.register(MeritzPolicyParser())
PolicyParserRegistry.register(DBPolicyParser())

__all__ = [
    # STEP 7 legacy
    'PolicyScopeParser',
    'PolicyScopePipeline',
    # STEP 8 multi-insurer
    'PolicyParserRegistry',
    'BasePolicyParser',
    'DiseaseGroupDefinition',
    'CoverageScopeDefinition',
]
