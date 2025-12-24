"""
Policy Scope Pipeline v1 (MVP)

STEP 7 Phase B: disease_scope_norm population from policy documents

Constitutional principles:
- KCD-7 single source of truth (disease_code_master)
- Group-based normalization (disease_code_group)
- Evidence required at every level
- Deterministic extraction only (no LLM)
"""
from .parser import PolicyScopeParser
from .pipeline import PolicyScopePipeline

__all__ = ['PolicyScopeParser', 'PolicyScopePipeline']
