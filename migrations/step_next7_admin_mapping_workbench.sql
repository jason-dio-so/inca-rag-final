-- Migration: STEP NEXT-7 Admin Mapping Workbench
-- Purpose: Create tables for UNMAPPED/AMBIGUOUS mapping resolution workflow
-- Constitutional Requirement: Canonical Coverage Rule - all mappings must reference 신정원 통일코드

-- ============================================================================
-- 1. mapping_event_queue: Queue for UNMAPPED/AMBIGUOUS events
-- ============================================================================
CREATE TABLE IF NOT EXISTS mapping_event_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Source context
    insurer TEXT NOT NULL,
    query_text TEXT NOT NULL,
    normalized_query TEXT,
    raw_coverage_title TEXT NOT NULL,

    -- Detection status
    detected_status TEXT NOT NULL CHECK (detected_status IN ('UNMAPPED', 'AMBIGUOUS')),

    -- Candidates (신정원 통일코드 후보들)
    candidate_coverage_codes JSONB,  -- Array of canonical coverage codes
    evidence_ref_ids JSONB,           -- Reference to evidence blocks

    -- Resolution state
    state TEXT NOT NULL DEFAULT 'OPEN' CHECK (state IN ('OPEN', 'APPROVED', 'REJECTED', 'SNOOZED')),
    resolved_coverage_code TEXT,      -- 승인된 신정원 통일코드
    resolution_type TEXT CHECK (resolution_type IN ('ALIAS', 'NAME_MAP', 'MANUAL_NOTE')),
    resolution_note TEXT,
    resolved_at TIMESTAMP,
    resolved_by TEXT,

    -- Deduplication: only one OPEN event per (insurer, raw_coverage_title, detected_status)
    CONSTRAINT unique_open_event UNIQUE (insurer, raw_coverage_title, detected_status, state)
        WHERE state = 'OPEN'
);

CREATE INDEX idx_mapping_event_state ON mapping_event_queue(state, created_at DESC);
CREATE INDEX idx_mapping_event_insurer ON mapping_event_queue(insurer);
CREATE INDEX idx_mapping_event_status ON mapping_event_queue(detected_status);

COMMENT ON TABLE mapping_event_queue IS 'Queue for admin to resolve UNMAPPED/AMBIGUOUS mapping events';
COMMENT ON COLUMN mapping_event_queue.candidate_coverage_codes IS 'Array of 신정원 통일코드 candidates';
COMMENT ON COLUMN mapping_event_queue.resolved_coverage_code IS 'Approved 신정원 통일코드 (canonical only)';

-- ============================================================================
-- 2. coverage_code_alias: Alias mapping table
-- ============================================================================
-- This table may already exist, create if not
CREATE TABLE IF NOT EXISTS coverage_code_alias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insurer TEXT NOT NULL,
    alias_text TEXT NOT NULL,
    coverage_code TEXT NOT NULL,  -- 신정원 통일코드 (canonical)
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by TEXT,

    CONSTRAINT unique_alias_per_insurer UNIQUE (insurer, alias_text)
);

CREATE INDEX IF NOT EXISTS idx_coverage_alias_lookup ON coverage_code_alias(insurer, alias_text);

COMMENT ON TABLE coverage_code_alias IS 'Alias to canonical coverage code mapping';
COMMENT ON COLUMN coverage_code_alias.coverage_code IS '신정원 통일코드 (canonical only)';

-- ============================================================================
-- 3. coverage_name_map: Name normalization mapping table
-- ============================================================================
CREATE TABLE IF NOT EXISTS coverage_name_map (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insurer TEXT NOT NULL,
    raw_name TEXT NOT NULL,
    coverage_title_normalized TEXT NOT NULL,
    coverage_code TEXT NOT NULL,  -- 신정원 통일코드 (canonical)
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by TEXT,

    CONSTRAINT unique_raw_name_per_insurer UNIQUE (insurer, raw_name)
);

CREATE INDEX IF NOT EXISTS idx_coverage_name_lookup ON coverage_name_map(insurer, raw_name);

COMMENT ON TABLE coverage_name_map IS 'Raw name to normalized title and canonical code mapping';
COMMENT ON COLUMN coverage_name_map.coverage_code IS '신정원 통일코드 (canonical only)';

-- ============================================================================
-- 4. admin_audit_log: Audit trail for all admin actions
-- ============================================================================
CREATE TABLE IF NOT EXISTS admin_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Actor (simple username for now, can be upgraded to auth later)
    actor TEXT NOT NULL,

    -- Action details
    action TEXT NOT NULL CHECK (action IN ('APPROVE', 'REJECT', 'SNOOZE', 'UPSERT_ALIAS', 'UPSERT_NAME_MAP')),
    target_type TEXT NOT NULL CHECK (target_type IN ('EVENT', 'ALIAS', 'NAME_MAP')),
    target_id TEXT NOT NULL,

    -- Change tracking
    before JSONB,
    after JSONB,

    -- Evidence and notes
    evidence_ref_ids JSONB,
    note TEXT
);

CREATE INDEX idx_audit_log_created ON admin_audit_log(created_at DESC);
CREATE INDEX idx_audit_log_actor ON admin_audit_log(actor);
CREATE INDEX idx_audit_log_target ON admin_audit_log(target_type, target_id);

COMMENT ON TABLE admin_audit_log IS 'Audit trail for all admin mapping actions (Constitutional: Deterministic & Auditable)';
COMMENT ON COLUMN admin_audit_log.actor IS 'Username or X-Admin-Actor header value';

-- ============================================================================
-- 5. Trigger for updated_at on mapping_event_queue
-- ============================================================================
CREATE OR REPLACE FUNCTION update_mapping_event_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER mapping_event_queue_updated_at
    BEFORE UPDATE ON mapping_event_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_mapping_event_timestamp();

-- ============================================================================
-- Migration complete
-- ============================================================================
