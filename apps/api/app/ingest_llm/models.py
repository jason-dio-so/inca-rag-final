"""
STEP 6-B: Pydantic Models for LLM Candidate Generation

Constitutional Compliance:
- Models represent proposals (not final decisions)
- All coverage_code references are canonical (신정원 통일코드)
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class EntityCandidate(BaseModel):
    """
    LLM-proposed coverage entity candidate.

    This is a PROPOSAL, not a confirmed entity.
    Resolver must map coverage_name_span to canonical coverage_code.
    """
    coverage_name_span: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Coverage name extracted from chunk text"
    )
    entity_type: Literal["definition", "condition", "exclusion", "amount", "benefit"] = Field(
        ...,
        description="Entity type classification"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="LLM confidence score (0.0-1.0)"
    )
    text_offset: Optional[tuple[int, int]] = Field(
        None,
        description="[start, end] character positions in chunk text"
    )

    class Config:
        extra = "forbid"


class LLMCandidateResponse(BaseModel):
    """
    LLM API response containing coverage entity candidates.

    Constitutional Guarantee:
    - LLM output is parsed but NOT trusted
    - Resolver validates all coverage_code mappings
    - Invalid JSON → graceful degradation (empty candidates)
    """
    candidates: List[EntityCandidate] = Field(
        default_factory=list,
        description="List of coverage entity candidates"
    )

    @field_validator('candidates')
    @classmethod
    def limit_candidates(cls, v):
        """Limit to 10 candidates per chunk (prevent token abuse)"""
        if len(v) > 10:
            return v[:10]
        return v

    class Config:
        extra = "forbid"


class AmountContextCandidate(BaseModel):
    """
    LLM-proposed amount context hint (optional for STEP 6-B).

    NOTE: Actual amount extraction remains rule-based.
    LLM only suggests context classification.
    """
    context_type: Optional[Literal["direct_amount", "range", "table_reference", "conditional"]] = None
    amount_qualifier: Optional[str] = Field(None, max_length=100)
    calculation_hint: Optional[str] = Field(None, max_length=500)
    confidence: float = Field(..., ge=0.0, le=1.0)

    class Config:
        extra = "forbid"


class ResolverResult(BaseModel):
    """
    Result of coverage name → canonical code resolution.

    Constitutional Guarantee:
    - resolved_coverage_code MUST exist in coverage_standard
    - No auto-INSERT into coverage_standard
    """
    status: Literal["resolved", "rejected", "needs_review"]
    resolved_coverage_code: Optional[str] = None
    resolved_entity_type: Optional[str] = None
    resolver_method: Optional[Literal["exact_alias", "exact_standard", "fuzzy", "none"]] = None
    resolver_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    reason: Optional[str] = None

    @field_validator('resolved_coverage_code')
    @classmethod
    def validate_resolved_code(cls, v, info):
        """
        If status=resolved, coverage_code must be provided.
        """
        status = info.data.get('status')
        if status == 'resolved' and not v:
            raise ValueError("resolved_coverage_code required when status=resolved")
        return v

    class Config:
        extra = "forbid"


class CandidateMetrics(BaseModel):
    """
    Metrics for LLM candidate generation and resolution.
    """
    total_candidates: int = 0
    resolved_count: int = 0
    rejected_count: int = 0
    needs_review_count: int = 0
    llm_tokens_used: int = 0
    llm_cost_usd: float = 0.0
    cache_hits: int = 0
    prefilter_passed: int = 0
    prefilter_rejected: int = 0

    @property
    def resolution_rate(self) -> float:
        """Resolution rate (resolved / total)"""
        if self.total_candidates == 0:
            return 0.0
        return self.resolved_count / self.total_candidates

    @property
    def cache_hit_rate(self) -> float:
        """Cache hit rate (hits / total)"""
        total_attempts = self.cache_hits + self.total_candidates
        if total_attempts == 0:
            return 0.0
        return self.cache_hits / total_attempts

    class Config:
        extra = "forbid"
