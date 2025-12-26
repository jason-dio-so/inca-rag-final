-- STEP NEXT-AD: Coverage Mapping Table
-- Purpose: Universe → Canonical Code mapping (DB-First, XLSX Import/Export)
-- Principle: DB is SSOT, XLSX is I/O medium only

-- Coverage Mapping Table
CREATE TABLE IF NOT EXISTS v2.coverage_mapping (
    mapping_id SERIAL PRIMARY KEY,

    -- Join keys (UNIQUE constraint)
    template_id VARCHAR(300) NOT NULL REFERENCES v2.template(template_id) ON DELETE CASCADE,
    coverage_id INTEGER NOT NULL REFERENCES v2.proposal_coverage(coverage_id) ON DELETE CASCADE,

    -- Canonical code (신정원 통일코드)
    canonical_coverage_code TEXT NOT NULL,

    -- Mapping metadata
    mapping_source TEXT NOT NULL DEFAULT 'xlsx_manual',
    mapping_status v2.mapping_status_enum NOT NULL DEFAULT 'MAPPED',
    note TEXT,

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT uq_template_coverage_mapping UNIQUE (template_id, coverage_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_coverage_mapping_template ON v2.coverage_mapping(template_id);
CREATE INDEX IF NOT EXISTS idx_coverage_mapping_coverage ON v2.coverage_mapping(coverage_id);
CREATE INDEX IF NOT EXISTS idx_coverage_mapping_canonical ON v2.coverage_mapping(canonical_coverage_code);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION v2.update_coverage_mapping_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_coverage_mapping_updated_at
    BEFORE UPDATE ON v2.coverage_mapping
    FOR EACH ROW
    EXECUTE FUNCTION v2.update_coverage_mapping_updated_at();

-- Comments
COMMENT ON TABLE v2.coverage_mapping IS
'Universe → Canonical coverage code mapping. DB is SSOT, XLSX is I/O medium only.';

COMMENT ON COLUMN v2.coverage_mapping.template_id IS
'Template reference (join key). Part of UNIQUE constraint with coverage_id.';

COMMENT ON COLUMN v2.coverage_mapping.coverage_id IS
'Coverage reference (join key). Part of UNIQUE constraint with template_id.';

COMMENT ON COLUMN v2.coverage_mapping.canonical_coverage_code IS
'신정원 통일코드 (canonical coverage code). NOT NULL enforced.';

COMMENT ON COLUMN v2.coverage_mapping.mapping_source IS
'Mapping source: xlsx_manual (default) | api_manual | auto_rule (future).';

COMMENT ON COLUMN v2.coverage_mapping.mapping_status IS
'Mapping status: MAPPED (default) | UNMAPPED | AMBIGUOUS.';

COMMENT ON COLUMN v2.coverage_mapping.note IS
'Optional notes for manual review or ambiguous cases.';
