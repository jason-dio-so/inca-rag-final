-- ============================================
-- STEP NEXT-AE: Coverage Evidence Schema
-- Purpose: Store coverage conditions, definitions, and evidence from policy docs
-- Constitutional: Evidence-based, deterministic extraction
-- ============================================

-- Table: v2.coverage_evidence
-- Stores条件/定義/Evidence for each canonical coverage code

CREATE TABLE IF NOT EXISTS v2.coverage_evidence (
    evidence_id SERIAL PRIMARY KEY,

    -- Coverage reference (FK to coverage_standard)
    canonical_coverage_code VARCHAR(100) NOT NULL,

    -- Product context (optional, for product-specific variations)
    product_id VARCHAR(200),  -- FK to v2.product
    insurer_code v2.insurer_code_enum,  -- FK to v2.insurer

    -- Evidence type
    evidence_type VARCHAR(100) NOT NULL,  -- definition, payment_condition, exclusion, partial_payment, etc.

    -- Evidence content
    excerpt TEXT NOT NULL,  -- Extracted text excerpt from policy doc
    excerpt_ko TEXT,  -- Korean translation (if source is not Korean)

    -- Source document reference
    source_doc_type VARCHAR(50) NOT NULL,  -- policy, business_rules, product_summary
    source_doc_id TEXT,  -- Document ID or path
    source_page INTEGER,  -- Page number
    source_span_start INTEGER,  -- Character offset start
    source_span_end INTEGER,  -- Character offset end

    -- Extraction metadata
    extraction_method VARCHAR(100) NOT NULL,  -- deterministic_v1, llm_assisted_v1, etc.
    extraction_confidence VARCHAR(50),  -- high, medium, low, unknown

    -- Structured slots (optional, for deterministic comparison)
    structured_data JSONB DEFAULT '{}',  -- e.g., {"payout_limit": {"type": "per_diagnosis", "count": 1}}

    -- Notes
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT fk_coverage_evidence_canonical_code
        FOREIGN KEY (canonical_coverage_code)
        REFERENCES v2.coverage_standard(coverage_code)
        ON DELETE CASCADE,

    CONSTRAINT fk_coverage_evidence_product
        FOREIGN KEY (product_id)
        REFERENCES v2.product(product_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_coverage_evidence_insurer
        FOREIGN KEY (insurer_code)
        REFERENCES v2.insurer(insurer_code)
        ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_coverage_evidence_canonical_code
    ON v2.coverage_evidence(canonical_coverage_code);

CREATE INDEX IF NOT EXISTS idx_coverage_evidence_product
    ON v2.coverage_evidence(product_id);

CREATE INDEX IF NOT EXISTS idx_coverage_evidence_insurer
    ON v2.coverage_evidence(insurer_code);

CREATE INDEX IF NOT EXISTS idx_coverage_evidence_type
    ON v2.coverage_evidence(evidence_type);

CREATE INDEX IF NOT EXISTS idx_coverage_evidence_doc_type
    ON v2.coverage_evidence(source_doc_type);

-- GIN index for structured_data JSONB queries
CREATE INDEX IF NOT EXISTS idx_coverage_evidence_structured_data
    ON v2.coverage_evidence USING GIN (structured_data);

-- Trigger: auto-update updated_at
CREATE OR REPLACE FUNCTION v2.update_coverage_evidence_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_coverage_evidence_updated_at ON v2.coverage_evidence;

CREATE TRIGGER trigger_coverage_evidence_updated_at
    BEFORE UPDATE ON v2.coverage_evidence
    FOR EACH ROW
    EXECUTE FUNCTION v2.update_coverage_evidence_updated_at();

-- Comments
COMMENT ON TABLE v2.coverage_evidence IS
'STEP NEXT-AE: Coverage conditions, definitions, and evidence from policy documents.
Evidence-based, deterministic extraction. All coverage-related rules stored here.';

COMMENT ON COLUMN v2.coverage_evidence.canonical_coverage_code IS
'FK to v2.coverage_standard. 신정원 통일 coverage code.';

COMMENT ON COLUMN v2.coverage_evidence.evidence_type IS
'Type of evidence: definition, payment_condition, exclusion, partial_payment, disease_scope, etc.';

COMMENT ON COLUMN v2.coverage_evidence.excerpt IS
'Raw text excerpt from policy document. Source of truth for evidence.';

COMMENT ON COLUMN v2.coverage_evidence.extraction_method IS
'How this evidence was extracted. deterministic_v1 = regex/rules, llm_assisted_v1 = LLM helper.';

COMMENT ON COLUMN v2.coverage_evidence.structured_data IS
'Optional structured slots extracted from excerpt. For deterministic comparison.';
