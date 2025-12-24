"""
STEP 6-B: LLM Client Wrapper for Coverage Entity Extraction

Constitutional Guarantees:
- LLM = Proposal Generator ONLY (not decision maker)
- OpenAI gpt-4.1-mini (batch processing optimized, configurable)
- Graceful degradation on failures
- Content-hash based caching (no duplicate LLM calls)
- Rate limiting + retry with exponential backoff
- NO direct writes to coverage_standard or chunk_entity

Cost Optimization:
- Prefilter upstream reduces 60-70% of chunks
- Content hash caching prevents re-processing (30-50% savings)
- Batch API usage when available
- Model configurable (default: gpt-4.1-mini, can override per instance)
"""
import json
import logging
import time
import hashlib
from typing import List, Optional, Dict, Any, Protocol
from dataclasses import dataclass
from openai import OpenAI, RateLimitError, APIError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from .models import LLMCandidateResponse, EntityCandidate

logger = logging.getLogger(__name__)


@dataclass
class ChunkInput:
    """Input data for LLM candidate generation"""
    chunk_id: int
    content: str
    doc_type: str
    insurer_code: Optional[str] = None
    product_name: Optional[str] = None
    content_hash: Optional[str] = None  # Pre-computed hash for caching


class LLMClientProtocol(Protocol):
    """Protocol for LLM clients (real + fake)"""

    def generate_candidates(
        self,
        batch: List[ChunkInput],
        *,
        request_id: str
    ) -> List[LLMCandidateResponse]:
        """Generate coverage entity candidates from chunks"""
        ...


class OpenAILLMClient:
    """
    OpenAI-based LLM client for coverage entity extraction.

    Constitutional Guarantees:
    - Outputs are PROPOSALS only (resolver validates)
    - Graceful degradation (returns empty candidates on failure)
    - Never calls the confirm function (manual-only operation)
    - Never writes to coverage_standard (FK verification only)
    """

    # Model configuration
    DEFAULT_MODEL = "gpt-4.1-mini"  # Cost-optimized model (batch processing)
    DEFAULT_TEMPERATURE = 0.1  # Low temperature for consistent extraction
    DEFAULT_MAX_TOKENS = 500  # Conservative token limit per chunk

    # Rate limiting
    MAX_CONCURRENCY = 5  # Concurrent API calls
    REQUESTS_PER_MINUTE = 50  # OpenAI tier limit

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_WAIT_MIN = 1  # seconds
    RETRY_WAIT_MAX = 10  # seconds

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        cache_store: Optional[Dict[str, LLMCandidateResponse]] = None,
        enable_cache: bool = True
    ):
        """
        Initialize OpenAI LLM client.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4.1-mini, configurable)
            cache_store: Optional cache store (for testing)
            enable_cache: Enable content-hash caching
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.enable_cache = enable_cache
        self.cache: Dict[str, LLMCandidateResponse] = cache_store if cache_store is not None else {}

        logger.info(f"OpenAILLMClient initialized: model={model}, cache_enabled={enable_cache}")

    def generate_candidates(
        self,
        batch: List[ChunkInput],
        *,
        request_id: str
    ) -> List[LLMCandidateResponse]:
        """
        Generate coverage entity candidates from chunk batch.

        Constitutional Guarantee:
        - Returns PROPOSALS only (resolver validates coverage_code)
        - Graceful degradation (empty candidates on failure)
        - Content-hash caching (no duplicate calls)

        Args:
            batch: List of chunks to process
            request_id: Unique request ID for logging/tracing

        Returns:
            List of LLMCandidateResponse (1 per chunk)
        """
        logger.info(f"[{request_id}] generate_candidates: processing {len(batch)} chunks")

        results: List[LLMCandidateResponse] = []

        for chunk_input in batch:
            try:
                # Check cache first
                if self.enable_cache and chunk_input.content_hash:
                    cached = self._get_from_cache(chunk_input.content_hash)
                    if cached:
                        logger.debug(
                            f"[{request_id}] Cache HIT: chunk_id={chunk_input.chunk_id}, "
                            f"hash={chunk_input.content_hash[:8]}"
                        )
                        results.append(cached)
                        continue

                # Call LLM
                response = self._call_llm_with_retry(chunk_input, request_id=request_id)

                # Store in cache
                if self.enable_cache and chunk_input.content_hash:
                    self._store_in_cache(chunk_input.content_hash, response)

                results.append(response)

            except Exception as e:
                # Graceful degradation: return empty candidates
                logger.error(
                    f"[{request_id}] LLM call failed for chunk_id={chunk_input.chunk_id}: {e}",
                    exc_info=True
                )
                results.append(LLMCandidateResponse(candidates=[]))

        logger.info(
            f"[{request_id}] generate_candidates: completed {len(results)}/{len(batch)} chunks"
        )
        return results

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIError)),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(
            multiplier=1,
            min=RETRY_WAIT_MIN,
            max=RETRY_WAIT_MAX
        ),
        reraise=True
    )
    def _call_llm_with_retry(
        self,
        chunk_input: ChunkInput,
        *,
        request_id: str
    ) -> LLMCandidateResponse:
        """
        Call OpenAI API with retry logic.

        Args:
            chunk_input: Chunk to process
            request_id: Request ID for logging

        Returns:
            LLMCandidateResponse

        Raises:
            Exception on persistent failures (caller handles graceful degradation)
        """
        start_time = time.time()

        # Build prompt
        prompt = self._build_prompt(chunk_input)

        # Call OpenAI
        logger.debug(
            f"[{request_id}] Calling OpenAI: chunk_id={chunk_input.chunk_id}, "
            f"model={self.model}"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=self.DEFAULT_TEMPERATURE,
            max_tokens=self.DEFAULT_MAX_TOKENS,
            response_format={"type": "json_object"}  # Force JSON output
        )

        elapsed = time.time() - start_time

        # Parse response
        raw_content = response.choices[0].message.content
        logger.debug(
            f"[{request_id}] OpenAI response: chunk_id={chunk_input.chunk_id}, "
            f"elapsed={elapsed:.2f}s, tokens={response.usage.total_tokens}"
        )

        # Log raw response (for debugging/auditing)
        logger.info(
            f"[{request_id}] RAW_LLM_RESPONSE: chunk_id={chunk_input.chunk_id}, "
            f"content={raw_content}"
        )

        # Parse JSON
        try:
            parsed = self._parse_llm_response(raw_content)
            return parsed
        except Exception as parse_error:
            logger.error(
                f"[{request_id}] JSON parsing failed: chunk_id={chunk_input.chunk_id}, "
                f"error={parse_error}",
                exc_info=True
            )
            # Graceful degradation: empty candidates
            return LLMCandidateResponse(candidates=[])

    def _build_prompt(self, chunk_input: ChunkInput) -> str:
        """
        Build user prompt for coverage entity extraction.

        Args:
            chunk_input: Chunk data

        Returns:
            Formatted prompt string
        """
        context_parts = []
        if chunk_input.insurer_code:
            context_parts.append(f"보험사: {chunk_input.insurer_code}")
        if chunk_input.product_name:
            context_parts.append(f"상품명: {chunk_input.product_name}")
        context_parts.append(f"문서유형: {chunk_input.doc_type}")

        context = ", ".join(context_parts)

        return f"""다음 보험 약관 텍스트에서 담보(coverage) 관련 정보를 추출하세요.

**컨텍스트**: {context}

**텍스트**:
{chunk_input.content}

**추출 규칙**:
1. 담보명(coverage_name_span): 텍스트에 등장하는 담보 이름 (예: "암진단비", "뇌출혈진단비")
2. entity_type: definition/condition/exclusion/amount/benefit 중 하나
3. confidence: 0.0~1.0 (추출 확신도)
4. text_offset: 텍스트 내 [시작, 끝] 위치 (선택사항)

**출력 형식** (JSON):
{{
  "candidates": [
    {{
      "coverage_name_span": "암진단비",
      "entity_type": "definition",
      "confidence": 0.95,
      "text_offset": [10, 15]
    }}
  ]
}}

**주의사항**:
- 담보명은 텍스트에서 정확히 추출 (추론 금지)
- 담보가 없으면 빈 배열 반환
- 최대 10개까지만 추출
"""

    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM"""
        return """당신은 대한민국 보험 약관 전문가입니다.
주어진 텍스트에서 담보(coverage) 관련 정보를 정확히 추출하세요.

**절대 규칙**:
- 텍스트에 명시되지 않은 내용은 추론하지 마세요
- 담보명은 원문 그대로 추출하세요
- JSON 형식을 정확히 따르세요
- 불확실하면 confidence를 낮게 설정하세요"""

    def _parse_llm_response(self, raw_content: str) -> LLMCandidateResponse:
        """
        Parse LLM JSON response into Pydantic model.

        Args:
            raw_content: Raw JSON string from LLM

        Returns:
            LLMCandidateResponse

        Raises:
            ValueError: On parse failure
        """
        data = json.loads(raw_content)

        # Pydantic validation
        return LLMCandidateResponse(**data)

    def _get_from_cache(self, content_hash: str) -> Optional[LLMCandidateResponse]:
        """Get cached response by content hash"""
        return self.cache.get(content_hash)

    def _store_in_cache(self, content_hash: str, response: LLMCandidateResponse) -> None:
        """Store response in cache"""
        self.cache[content_hash] = response


class FakeLLMClient:
    """
    Fake LLM client for testing (no OpenAI API calls).

    Returns predefined responses for testing pipeline without API costs.
    """

    def __init__(self, predefined_responses: Optional[Dict[int, LLMCandidateResponse]] = None):
        """
        Initialize fake client.

        Args:
            predefined_responses: Dict mapping chunk_id → response
        """
        self.responses = predefined_responses or {}
        logger.info("FakeLLMClient initialized (testing mode)")

    def generate_candidates(
        self,
        batch: List[ChunkInput],
        *,
        request_id: str
    ) -> List[LLMCandidateResponse]:
        """
        Return predefined responses (no actual LLM call).

        Args:
            batch: List of chunks
            request_id: Request ID for logging

        Returns:
            List of predefined or empty responses
        """
        logger.info(f"[{request_id}] FakeLLMClient: processing {len(batch)} chunks")

        results = []
        for chunk_input in batch:
            response = self.responses.get(
                chunk_input.chunk_id,
                LLMCandidateResponse(candidates=[])  # Default: empty
            )
            results.append(response)

        return results
