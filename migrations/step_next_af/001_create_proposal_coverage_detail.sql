-- STEP NEXT-AF: Proposal Coverage Detail Table
-- Purpose: Store proposal detail table (보장내용 설명) for Comparison Description
-- Constitutional Rule: This is NOT evidence - it's comparison description only

-- Drop existing if exists
DROP TABLE IF EXISTS v2.proposal_coverage_detail CASCADE;

-- Create table
CREATE TABLE v2.proposal_coverage_detail (
    detail_id SERIAL PRIMARY KEY,
    template_id TEXT NOT NULL,
    coverage_id INTEGER,  -- FK to v2.proposal_coverage, nullable if unmatched
    insurer_coverage_name TEXT NOT NULL,  -- Coverage name from detail table
    detail_text TEXT NOT NULL,  -- Original detail content (normalized)
    detail_struct JSONB,  -- Structured result if parseable
    source_doc_type TEXT NOT NULL DEFAULT 'proposal_detail' CHECK (source_doc_type = 'proposal_detail'),
    source_page INTEGER,  -- Page number in proposal PDF
    excerpt_hash TEXT NOT NULL,  -- For deduplication
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_template FOREIGN KEY (template_id) REFERENCES v2.template(template_id) ON DELETE CASCADE,
    CONSTRAINT fk_coverage FOREIGN KEY (coverage_id) REFERENCES v2.proposal_coverage(coverage_id) ON DELETE CASCADE,
    CONSTRAINT unique_detail_per_template UNIQUE (template_id, coverage_id, excerpt_hash)
);

-- Indexes
CREATE INDEX idx_proposal_coverage_detail_template ON v2.proposal_coverage_detail(template_id);
CREATE INDEX idx_proposal_coverage_detail_coverage ON v2.proposal_coverage_detail(coverage_id);
CREATE INDEX idx_proposal_coverage_detail_updated ON v2.proposal_coverage_detail(updated_at DESC);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_proposal_coverage_detail_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_proposal_coverage_detail_updated_at
    BEFORE UPDATE ON v2.proposal_coverage_detail
    FOR EACH ROW
    EXECUTE FUNCTION update_proposal_coverage_detail_updated_at();

-- Comments
COMMENT ON TABLE v2.proposal_coverage_detail IS 'Proposal detail table content for Comparison Description (NOT Evidence)';
COMMENT ON COLUMN v2.proposal_coverage_detail.detail_text IS 'Original detail content from proposal detail table';
COMMENT ON COLUMN v2.proposal_coverage_detail.source_doc_type IS 'Always proposal_detail - constitutional separation from evidence';
COMMENT ON COLUMN v2.proposal_coverage_detail.coverage_id IS 'Matched coverage from proposal_coverage, NULL if unmatched';
