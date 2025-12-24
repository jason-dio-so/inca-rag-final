-- STEP 6-B Migration: Create Candidate Tables for LLM-Assisted Ingestion
-- Constitutional Principle: LLM proposes candidates, code confirms
-- Production tables (chunk_entity/amount_entity) updated only via confirm process

-- ============================================================================
-- Table: chunk_entity_candidate
-- Purpose: Store LLM-proposed coverage entity candidates before confirmation
-- ============================================================================

CREATE TABLE IF NOT EXISTS chunk_entity_candidate (
    -- Primary Key
    candidate_id SERIAL PRIMARY KEY,

    -- Foreign Keys
    chunk_id INTEGER NOT NULL REFERENCES chunk(chunk_id) ON DELETE CASCADE,

    -- LLM Proposal (Raw Output)
    coverage_name_raw TEXT NOT NULL,  -- Original coverage name from LLM
    entity_type_proposed VARCHAR(50) NOT NULL,  -- definition/condition/exclusion/amount/benefit
    text_offset INTEGER[],  -- [start, end] character positions in chunk
    confidence NUMERIC(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),

    -- LLM Metadata
    llm_model VARCHAR(100),  -- e.g., "gpt-4-1106-preview"
    llm_prompt_version VARCHAR(50),  -- Track prompt changes for A/B testing
    llm_response_raw JSONB,  -- Full LLM response for audit
    llm_tokens_used INTEGER,  -- Track cost
    llm_called_at TIMESTAMP,

    -- Content Hash (for deduplication/caching)
    content_hash VARCHAR(64),  -- SHA-256 of chunk.content
    prefilter_passed BOOLEAN DEFAULT TRUE,  -- Whether passed prefilter

    -- Resolution Status
    resolver_status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending/resolved/rejected/needs_review
    resolver_reason TEXT,  -- Why rejected/needs review
    resolved_coverage_code VARCHAR(100),  -- Canonical coverage_code (FK to coverage_standard)
    resolved_entity_type VARCHAR(50),  -- May differ from proposed after validation

    -- Resolver Metadata
    resolver_method VARCHAR(50),  -- exact_alias/exact_standard/fuzzy/none
    resolver_confidence NUMERIC(3,2),  -- Resolver's confidence in mapping
    resolver_version VARCHAR(50),  -- Code version that resolved this
    resolved_at TIMESTAMP,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_resolver_status CHECK (resolver_status IN ('pending', 'resolved', 'rejected', 'needs_review')),
    CONSTRAINT valid_entity_type_proposed CHECK (entity_type_proposed IN ('definition', 'condition', 'exclusion', 'amount', 'benefit')),
    CONSTRAINT valid_entity_type_resolved CHECK (
        resolved_entity_type IS NULL OR
        resolved_entity_type IN ('definition', 'condition', 'exclusion', 'amount', 'benefit')
    ),
    CONSTRAINT resolved_code_required CHECK (
        (resolver_status = 'resolved' AND resolved_coverage_code IS NOT NULL) OR
        (resolver_status != 'resolved')
    ),
    CONSTRAINT resolved_code_fk_check CHECK (
        resolved_coverage_code IS NULL OR
        EXISTS (SELECT 1 FROM coverage_standard WHERE coverage_code = resolved_coverage_code)
    )
);

-- Indexes for performance
CREATE INDEX idx_chunk_entity_candidate_chunk ON chunk_entity_candidate(chunk_id);
CREATE INDEX idx_chunk_entity_candidate_status ON chunk_entity_candidate(resolver_status);
CREATE INDEX idx_chunk_entity_candidate_created ON chunk_entity_candidate(created_at);
CREATE INDEX idx_chunk_entity_candidate_hash ON chunk_entity_candidate(content_hash) WHERE content_hash IS NOT NULL;
CREATE INDEX idx_chunk_entity_candidate_resolved_code ON chunk_entity_candidate(resolved_coverage_code) WHERE resolved_coverage_code IS NOT NULL;

-- Unique constraint: Prevent duplicate candidates for same chunk + coverage
CREATE UNIQUE INDEX idx_chunk_entity_candidate_unique ON chunk_entity_candidate(chunk_id, resolved_coverage_code)
    WHERE resolver_status = 'resolved' AND resolved_coverage_code IS NOT NULL;

-- Comments
COMMENT ON TABLE chunk_entity_candidate IS 'LLM-proposed coverage entity candidates (STEP 6-B). Only confirmed candidates copied to chunk_entity.';
COMMENT ON COLUMN chunk_entity_candidate.resolver_status IS 'pending: awaiting resolution, resolved: confirmed, rejected: failed validation, needs_review: ambiguous/manual review';
COMMENT ON COLUMN chunk_entity_candidate.resolved_coverage_code IS 'Canonical coverage_code from coverage_standard (MUST exist, no auto-INSERT)';
COMMENT ON COLUMN chunk_entity_candidate.content_hash IS 'SHA-256 of chunk.content for deduplication and change detection';

-- ============================================================================
-- Table: amount_entity_candidate
-- Purpose: Store LLM-proposed amount context candidates (optional for STEP 6-B)
-- Note: Amount extraction already works well via DB columns. This is for context hints only.
-- ============================================================================

CREATE TABLE IF NOT EXISTS amount_entity_candidate (
    -- Primary Key
    candidate_id SERIAL PRIMARY KEY,

    -- Foreign Keys
    chunk_id INTEGER NOT NULL REFERENCES chunk(chunk_id) ON DELETE CASCADE,

    -- LLM Proposal (Context Only - NOT final amount values)
    context_type_proposed VARCHAR(50),  -- direct_amount/range/table_reference/conditional
    amount_qualifier VARCHAR(100),  -- "최대", "최소", "1회당", "연간 한도"
    calculation_hint TEXT,  -- "가입금액의 10%", "기본 보험료 × 계약기간"
    confidence NUMERIC(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),

    -- LLM Metadata
    llm_model VARCHAR(100),
    llm_prompt_version VARCHAR(50),
    llm_response_raw JSONB,
    llm_tokens_used INTEGER,
    llm_called_at TIMESTAMP,

    -- Content Hash
    content_hash VARCHAR(64),

    -- Resolution Status
    resolver_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    resolver_reason TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_resolver_status_amount CHECK (resolver_status IN ('pending', 'resolved', 'rejected'))
);

-- Indexes
CREATE INDEX idx_amount_entity_candidate_chunk ON amount_entity_candidate(chunk_id);
CREATE INDEX idx_amount_entity_candidate_status ON amount_entity_candidate(resolver_status);
CREATE INDEX idx_amount_entity_candidate_hash ON amount_entity_candidate(content_hash) WHERE content_hash IS NOT NULL;

-- Comments
COMMENT ON TABLE amount_entity_candidate IS 'LLM-proposed amount context hints (STEP 6-B). Actual amount extraction remains rule-based via amount_entity.';
COMMENT ON COLUMN amount_entity_candidate.context_type_proposed IS 'LLM hint for amount context classification (not binding)';

-- ============================================================================
-- View: candidate_metrics
-- Purpose: Real-time metrics for monitoring LLM extraction quality
-- ============================================================================

CREATE OR REPLACE VIEW candidate_metrics AS
SELECT
    DATE(created_at) AS date,
    resolver_status,
    COUNT(*) AS count,
    AVG(confidence) AS avg_confidence,
    SUM(llm_tokens_used) AS total_tokens,
    COUNT(DISTINCT chunk_id) AS unique_chunks,
    COUNT(DISTINCT resolved_coverage_code) AS unique_coverages
FROM chunk_entity_candidate
GROUP BY DATE(created_at), resolver_status
ORDER BY date DESC, resolver_status;

COMMENT ON VIEW candidate_metrics IS 'Daily metrics for LLM candidate generation and resolution (STEP 6-B)';

-- ============================================================================
-- Function: confirm_candidate_to_entity
-- Purpose: Move resolved candidate to production chunk_entity table
-- Constitutional Guarantee: Only resolved candidates with valid FK can be confirmed
-- ============================================================================

CREATE OR REPLACE FUNCTION confirm_candidate_to_entity(p_candidate_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_candidate RECORD;
BEGIN
    -- Fetch candidate
    SELECT * INTO v_candidate
    FROM chunk_entity_candidate
    WHERE candidate_id = p_candidate_id
      AND resolver_status = 'resolved'
      AND resolved_coverage_code IS NOT NULL;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Candidate % not found or not resolved', p_candidate_id;
    END IF;

    -- Verify FK (double safety)
    IF NOT EXISTS (SELECT 1 FROM coverage_standard WHERE coverage_code = v_candidate.resolved_coverage_code) THEN
        RAISE EXCEPTION 'Coverage code % does not exist in coverage_standard (FK violation)', v_candidate.resolved_coverage_code;
    END IF;

    -- Insert into production table (idempotent via ON CONFLICT)
    INSERT INTO chunk_entity (chunk_id, coverage_code, entity_type, confidence, meta)
    VALUES (
        v_candidate.chunk_id,
        v_candidate.resolved_coverage_code,
        v_candidate.resolved_entity_type,
        v_candidate.resolver_confidence,  -- Use resolver confidence (more reliable than LLM confidence)
        jsonb_build_object(
            'source', 'llm',
            'candidate_id', v_candidate.candidate_id,
            'llm_model', v_candidate.llm_model,
            'llm_prompt_version', v_candidate.llm_prompt_version,
            'coverage_name_raw', v_candidate.coverage_name_raw,
            'llm_confidence', v_candidate.confidence,
            'resolver_method', v_candidate.resolver_method,
            'confirmed_at', NOW()
        )
    )
    ON CONFLICT (chunk_id, coverage_code) DO NOTHING;  -- Prevent duplicates

    -- Update candidate resolved_at
    UPDATE chunk_entity_candidate
    SET updated_at = NOW()
    WHERE candidate_id = p_candidate_id;

END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION confirm_candidate_to_entity IS 'Confirm resolved candidate to production chunk_entity (STEP 6-B). Enforces FK and prevents duplicates.';

-- ============================================================================
-- Rollback Script (for testing/development)
-- ============================================================================

-- DROP FUNCTION IF EXISTS confirm_candidate_to_entity(INTEGER);
-- DROP VIEW IF EXISTS candidate_metrics;
-- DROP TABLE IF EXISTS amount_entity_candidate CASCADE;
-- DROP TABLE IF EXISTS chunk_entity_candidate CASCADE;

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- Verification Queries (run after migration)
-- SELECT COUNT(*) FROM chunk_entity_candidate;
-- SELECT * FROM candidate_metrics LIMIT 10;
-- \d chunk_entity_candidate
-- \d amount_entity_candidate
