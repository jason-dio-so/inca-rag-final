-- STEP NEXT-AC: Universe Lock Table
-- Purpose: Separate raw extraction results from Universe classification
-- Principle: Raw data (proposal_coverage) is immutable, lock results are separate

-- Create migration directory marker
-- migrations/step_next_ac/

-- Universe Lock Classification Table
CREATE TABLE IF NOT EXISTS v2.proposal_coverage_universe_lock (
    lock_id SERIAL PRIMARY KEY,

    -- Reference to raw coverage
    coverage_id INTEGER NOT NULL REFERENCES v2.proposal_coverage(coverage_id) ON DELETE CASCADE,
    template_id VARCHAR(300) NOT NULL REFERENCES v2.template(template_id) ON DELETE CASCADE,

    -- Classification result
    lock_class VARCHAR(50) NOT NULL CHECK (
        lock_class IN ('UNIVERSE_COVERAGE', 'NON_UNIVERSE_META', 'UNCLASSIFIED')
    ),

    -- Classification reason (human-readable)
    lock_reason TEXT NOT NULL,

    -- Classification metadata
    locked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    locked_by_script VARCHAR(100) NOT NULL DEFAULT 'universe_lock_v2_stage1',
    script_version VARCHAR(50) NOT NULL DEFAULT 'v1.0',

    -- Audit
    meta JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT uq_coverage_lock UNIQUE (coverage_id, template_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_universe_lock_template ON v2.proposal_coverage_universe_lock(template_id);
CREATE INDEX IF NOT EXISTS idx_universe_lock_class ON v2.proposal_coverage_universe_lock(lock_class);
CREATE INDEX IF NOT EXISTS idx_universe_lock_coverage ON v2.proposal_coverage_universe_lock(coverage_id);

-- Comments
COMMENT ON TABLE v2.proposal_coverage_universe_lock IS
'Universe Lock classification results. Separates SSOT-eligible coverage rows from metadata/header/summary rows.';

COMMENT ON COLUMN v2.proposal_coverage_universe_lock.lock_class IS
'Classification: UNIVERSE_COVERAGE (SSOT eligible) | NON_UNIVERSE_META (header/summary/customer info) | UNCLASSIFIED (ambiguous)';

COMMENT ON COLUMN v2.proposal_coverage_universe_lock.lock_reason IS
'Human-readable reason for classification (e.g., "has_amount_value", "header_keyword:통합고객", "summary_keyword:합계")';
