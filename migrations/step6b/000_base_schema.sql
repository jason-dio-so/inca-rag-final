-- STEP 6-B Phase 3: Minimal Base Schema (NO pgvector)
-- Purpose: Create only essential tables needed for candidate tables
-- Phase 3 scope: DB realization + verification + minimal E2E
-- Note: pgvector/embedding removed for minimal testing

-- ========================================
-- Canonical Layer: coverage_standard
-- ========================================
-- Constitutional principle: coverage_code is canonical key (신정원 통일코드)
-- PK: coverage_id (SERIAL) for internal use
-- Canonical key: coverage_code (TEXT UNIQUE NOT NULL) for all references

CREATE TABLE IF NOT EXISTS coverage_standard (
    coverage_id SERIAL PRIMARY KEY,
    coverage_code TEXT UNIQUE NOT NULL,
    coverage_name TEXT NOT NULL,
    domain VARCHAR(100),
    coverage_type VARCHAR(100),
    priority INTEGER DEFAULT 999,
    is_main BOOLEAN DEFAULT false,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE coverage_standard IS 'Canonical coverage codes (신정원 통일 담보 코드) - Excel-only source';
COMMENT ON COLUMN coverage_standard.coverage_code IS 'Canonical key - all FKs reference this';

-- ========================================
-- Canonical Layer: coverage_alias
-- ========================================

CREATE TABLE IF NOT EXISTS coverage_alias (
    alias_id SERIAL PRIMARY KEY,
    coverage_code TEXT NOT NULL REFERENCES coverage_standard(coverage_code) ON DELETE CASCADE,
    insurer_code VARCHAR(50) NOT NULL,
    insurer_name VARCHAR(200),
    alias_name TEXT NOT NULL,
    confidence VARCHAR(20) DEFAULT 'medium',
    mapping_method VARCHAR(50) DEFAULT 'excel',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coverage_code, insurer_code, alias_name)
);

CREATE INDEX IF NOT EXISTS idx_coverage_alias_code ON coverage_alias(coverage_code);
CREATE INDEX IF NOT EXISTS idx_coverage_alias_insurer ON coverage_alias(insurer_code);

-- ========================================
-- Document Layer (Minimal - for chunk FK)
-- ========================================

CREATE TABLE IF NOT EXISTS insurer (
    insurer_id SERIAL PRIMARY KEY,
    insurer_code VARCHAR(50) UNIQUE NOT NULL,
    insurer_name VARCHAR(200) NOT NULL,
    insurer_name_eng VARCHAR(200),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product (
    product_id SERIAL PRIMARY KEY,
    insurer_id INTEGER NOT NULL REFERENCES insurer(insurer_id) ON DELETE CASCADE,
    product_code VARCHAR(100) NOT NULL,
    product_name VARCHAR(300) NOT NULL,
    product_type VARCHAR(100),
    sale_start_date DATE,
    sale_end_date DATE,
    is_active BOOLEAN DEFAULT true,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(insurer_id, product_code)
);

CREATE TABLE IF NOT EXISTS document (
    document_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL,
    document_version VARCHAR(50),
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64),
    effective_date DATE,
    doc_type_priority INTEGER NOT NULL,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, document_type, file_hash)
);

-- ========================================
-- Chunk Layer (NO embedding/vector)
-- ========================================

CREATE TABLE IF NOT EXISTS chunk (
    chunk_id BIGSERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
    page_number INTEGER,
    content TEXT NOT NULL,
    is_synthetic BOOLEAN NOT NULL DEFAULT false,
    synthetic_source_chunk_id BIGINT REFERENCES chunk(chunk_id) ON DELETE SET NULL,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE chunk IS 'Document chunks (원본 + synthetic) - NO embedding for Phase 3';
COMMENT ON COLUMN chunk.is_synthetic IS 'Synthetic chunk flag (Amount Bridge only)';

-- ========================================
-- Indexes
-- ========================================

CREATE INDEX IF NOT EXISTS idx_chunk_document ON chunk(document_id);
CREATE INDEX IF NOT EXISTS idx_chunk_synthetic ON chunk(is_synthetic);
CREATE INDEX IF NOT EXISTS idx_document_product ON document(product_id);
CREATE INDEX IF NOT EXISTS idx_product_insurer ON product(insurer_id);
