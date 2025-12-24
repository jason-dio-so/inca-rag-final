# Table Usage Report

**Purpose**: Document actual code usage for each table
**Analysis Date**: 2025-12-24
**Codebase Baseline**: STEP 6-C (Proposal Universe Lock v1)

---

## Analysis Methodology

1. **Grep Search**: Searched entire codebase for table references
2. **Code Path Analysis**: Identified which modules use each table
3. **Alignment Check**: Verified usage aligns with Proposal Universe Lock architecture
4. **Deletion Safety**: Assessed whether tables can be safely archived/dropped

---

## Active Tables - Usage Analysis

### Canonical Layer

#### `insurer`
- **Status**: ACTIVE (Context)
- **Used By**:
  - `apps/ingestion/*/*.py` - All ingestion modules reference insurer
  - Proposal Universe parser links proposals to insurer
- **Purpose**: Context axis - identifies proposal source
- **Alignment**: ✅ ALIGNED - Used for context, not primary comparison
- **Deletion**: ❌ NOW / ❌ LATER (Core context table)

#### `product`
- **Status**: ACTIVE (Context)
- **Used By**:
  - `apps/api/app/queries/compare.py` - JOIN for coverage amount lookup
  - `apps/ingestion/*/*.py` - Document ingestion pipeline
  - `tests/integration/test_step5_readonly.py` - Schema validation tests
- **Purpose**: Context axis - links documents to insurer
- **Current Usage Pattern**:
  ```python
  # Query: Coverage amount
  FROM public.product_coverage pc
  JOIN public.product p ON pc.product_id = p.product_id
  JOIN public.coverage_standard cs ON pc.coverage_id = cs.coverage_id
  ```
- **Alignment**: ⚠️ PARTIAL - Used via `product_coverage` which conflicts with Universe Lock
- **Deletion**: ❌ NOW / △ LATER (Keep as context, remove `product_coverage` dependency)

#### `coverage_standard`
- **Status**: ACTIVE (READ-ONLY)
- **Used By**:
  - ALL comparison queries
  - `proposal_universe/mapper.py` - Canonical code validation
  - Excel mapping resolver
- **Purpose**: Single source of truth for canonical coverage codes
- **Alignment**: ✅ ALIGNED - Core SSOT
- **Deletion**: ❌ NOW / ❌ LATER (Constitutional SSOT)

#### `document`
- **Status**: ACTIVE
- **Used By**:
  - All ingestion modules
  - Chunk → document FK relationships
  - Evidence tracking
- **Purpose**: Document metadata for all doc types (proposals, policies, terms)
- **Alignment**: ✅ ALIGNED - Evidence source
- **Deletion**: ❌ NOW / ❌ LATER (Core evidence table)

---

### Normalization Layer

#### `coverage_alias`
- **Status**: ACTIVE
- **Used By**:
  - Ingestion pipeline (coverage name normalization)
  - Excel mapping fallback (when exact match fails)
- **Purpose**: Maps insurer-specific coverage names to canonical codes
- **Alignment**: ✅ ALIGNED - Supports Excel-based mapping
- **Deletion**: ❌ NOW / ❌ LATER (Active mapping support)

#### `coverage_code_alias`
- **Status**: ACTIVE
- **Used By**: Legacy code mapping (if implemented)
- **Purpose**: Maps old coverage codes to canonical codes
- **Alignment**: ✅ ALIGNED - Backward compatibility
- **Deletion**: ❌ NOW / △ LATER (Low usage, but harmless)

#### `coverage_subtype`
- **Status**: ACTIVE
- **Used By**: Coverage subtype classification (if implemented)
- **Purpose**: Defines subtypes like 유사암, 제자리암
- **Note**: May be superseded by `disease_code_group` in STEP 6-C
- **Alignment**: ⚠️ PARTIAL - Overlaps with disease_code_group
- **Deletion**: ❌ NOW / △ LATER (Consider consolidation with disease_code_group)

#### `coverage_condition`
- **Status**: ACTIVE
- **Used By**: Coverage condition extraction (if implemented)
- **Purpose**: Stores payout conditions, reduction rules
- **Alignment**: ✅ ALIGNED - Evidence enrichment
- **Deletion**: ❌ NOW / ❌ LATER (Future use for policy processing)

---

### Document & Chunk Layer

#### `chunk`
- **Status**: ACTIVE
- **Used By**:
  - RAG retrieval queries
  - All comparison/evidence queries
  - Ingestion pipeline
- **Purpose**: Document chunks for RAG, synthetic chunks for Amount Bridge
- **Constitutional Rule**: MUST filter `is_synthetic=false` for compare/retrieval
- **Alignment**: ✅ ALIGNED - Core RAG table
- **Deletion**: ❌ NOW / ❌ LATER (Core RAG infrastructure)

#### `chunk_entity`
- **Status**: ACTIVE
- **Used By**:
  - Entity extraction pipeline
  - Coverage filtering (entity_type='coverage', coverage_code FK)
- **Purpose**: All extracted entities from chunks
- **Alignment**: ✅ ALIGNED - Evidence layer
- **Deletion**: ❌ NOW / ❌ LATER (Active entity extraction)

#### `amount_entity`
- **Status**: ACTIVE
- **Used By**:
  - Amount Bridge use case
  - Coverage amount context hints
- **Purpose**: Amount-specific structured data
- **Alignment**: ✅ ALIGNED - Amount Bridge (specific use case)
- **Deletion**: ❌ NOW / ❌ LATER (Amount Bridge active)

---

### STEP 6-C: Proposal Universe Lock Tables

#### `disease_code_master`
- **Status**: ACTIVE (Tier 1)
- **Used By**: STEP 6-C disease scope pipeline (when implemented)
- **Purpose**: KCD-7 코드 사전 (공식 배포본 ONLY)
- **Alignment**: ✅ ALIGNED - Constitutional SSOT
- **Deletion**: ❌ NOW / ❌ LATER (Constitutional principle)

#### `disease_code_group`
- **Status**: ACTIVE (Tier 2)
- **Used By**: STEP 6-C disease scope pipeline (when implemented)
- **Purpose**: Insurance concept groups (유사암, 소액암 등)
- **Alignment**: ✅ ALIGNED - STEP 6-C Amendment v1.0.1
- **Deletion**: ❌ NOW / ❌ LATER (Active for STEP 7)

#### `disease_code_group_member`
- **Status**: ACTIVE (Tier 2)
- **Used By**: STEP 6-C disease scope pipeline (when implemented)
- **Purpose**: Group membership (CODE or RANGE)
- **Alignment**: ✅ ALIGNED - STEP 6-C Amendment v1.0.1
- **Deletion**: ❌ NOW / ❌ LATER (Active for STEP 7)

#### `coverage_disease_scope`
- **Status**: ACTIVE (Tier 3)
- **Used By**: STEP 6-C disease scope pipeline (when implemented)
- **Purpose**: Coverage → disease group mapping
- **Alignment**: ✅ ALIGNED - STEP 6-C Amendment v1.0.1
- **Deletion**: ❌ NOW / ❌ LATER (Active for STEP 7)

#### `proposal_coverage_universe`
- **Status**: ACTIVE ⭐ **COMPARISON SSOT**
- **Used By**: STEP 6-C E2E pipeline (implemented in `src/proposal_universe/`)
- **Purpose**: 가입설계서 담보 Universe - 비교 절대 기준
- **Code Paths**:
  - `src/proposal_universe/parser.py` - ProposalCoverageParser
  - `src/proposal_universe/pipeline.py` - ProposalUniversePipeline
  - `tests/test_proposal_universe_e2e.py` - E2E validation
- **Alignment**: ✅ ALIGNED - **Universe Lock SSOT**
- **Deletion**: ❌ NOW / ❌ LATER (Constitutional principle)

#### `proposal_coverage_mapped`
- **Status**: ACTIVE
- **Used By**: STEP 6-C E2E pipeline
- **Purpose**: Universe → Canonical code mapping (Excel-based)
- **Code Paths**:
  - `src/proposal_universe/mapper.py` - CoverageMapper
  - Stores MAPPED/UNMAPPED/AMBIGUOUS status
- **Alignment**: ✅ ALIGNED - Excel SSOT enforcement
- **Deletion**: ❌ NOW / ❌ LATER (Active mapping table)

#### `proposal_coverage_slots`
- **Status**: ACTIVE
- **Used By**: STEP 6-C E2E pipeline
- **Purpose**: Slot Schema v1.1.1 storage
- **Code Paths**:
  - `src/proposal_universe/extractor.py` - SlotExtractor
  - Stores 20 slots including disease_scope, payout_limit
- **Alignment**: ✅ ALIGNED - Slot Schema v1.1.1
- **Deletion**: ❌ NOW / ❌ LATER (Active slot storage)

---

## Archived Tables - Usage Analysis

### `product_coverage`

- **Status**: ARCHIVED (NOT IMPLEMENTED in actual DB)
- **Definition**: `docs/db/archive/schema_v2_additions.sql`
- **Used By**:
  - ⚠️ `apps/api/app/queries/compare.py` (Line 116)
  - ⚠️ `tests/integration/test_step5_readonly.py` (Lines 8, 385, 409-414)
- **Purpose (Original)**: 상품별 담보 보장 금액 및 조건
- **Code Reference**:
  ```python
  # apps/api/app/queries/compare.py
  COVERAGE_AMOUNT_SQL = """
  SELECT
      cs.coverage_code,
      cs.coverage_name,
      pc.coverage_amount,
      p.product_name,
      i.insurer_name
  FROM public.product_coverage pc
  JOIN public.product p ON pc.product_id = p.product_id
  JOIN public.insurer i ON p.insurer_id = i.insurer_id
  JOIN public.coverage_standard cs ON pc.coverage_id = cs.coverage_id
  WHERE cs.coverage_code = %s
  """
  ```
- **Conflict**: Product-centered comparison conflicts with Proposal Universe Lock
- **Current Architecture**: Should use `proposal_coverage_universe` → `proposal_coverage_mapped` → `proposal_coverage_slots`
- **Alignment**: ❌ MISALIGNED - **Conflicts with Universe Lock**
- **Action Required**:
  - ❌ NOW: Do NOT drop (table doesn't exist in DB anyway)
  - ✅ STEP 7: Refactor queries to use `proposal_coverage_universe` + `proposal_coverage_mapped`
  - ✅ STEP 7: Update tests to validate Universe Lock queries
- **Deletion**: ❌ NOW / ✅ LATER (After query refactoring in STEP 7)

### `premium`

- **Status**: ARCHIVED (NOT IMPLEMENTED in actual DB)
- **Definition**: `docs/db/archive/schema_v2_additions.sql`
- **Used By**: ❌ NONE (no code references found)
- **Purpose (Original)**: 보험료 (연령/성별/납입방식별)
- **Alignment**: ❌ NOT RELEVANT - Premium comparison out of scope
- **Deletion**: ❌ NOW / △ LATER (Not used, but harmless in documentation)

---

## Critical Migration Path

### STEP 5 → STEP 6-C Query Alignment

**Current State (STEP 5)**:
```sql
-- STEP 5 Compare Query (MISALIGNED)
FROM public.product_coverage pc
JOIN public.product p ON pc.product_id = p.product_id
WHERE cs.coverage_code = %s
```

**Target State (STEP 6-C)**:
```sql
-- STEP 6-C Universe Lock Query (ALIGNED)
FROM proposal_coverage_universe u
JOIN proposal_coverage_mapped m ON u.id = m.universe_id
WHERE m.canonical_coverage_code = %s
  AND m.mapping_status = 'MAPPED'
```

### Action Items for STEP 7:

1. **Refactor `apps/api/app/queries/compare.py`**:
   - Replace `product_coverage` references with `proposal_coverage_universe`
   - Use `proposal_coverage_mapped` for canonical code filtering
   - Filter by `mapping_status = 'MAPPED'`

2. **Update `tests/integration/test_step5_readonly.py`**:
   - Remove `product_coverage` schema validation tests
   - Add `proposal_coverage_universe` schema validation
   - Test Universe Lock 5-state comparison

3. **Preserve Context Axis**:
   - Keep `product` table for context (insurer linkage, document grouping)
   - Do NOT use `product` as primary comparison dimension

---

## Summary Matrix

| Table | Status | Code Usage | Alignment | NOW | LATER |
|-------|--------|------------|-----------|-----|-------|
| **insurer** | ACTIVE (Context) | ✅ High | ✅ ALIGNED | ❌ | ❌ |
| **product** | ACTIVE (Context) | ✅ High | ⚠️ PARTIAL | ❌ | ❌ |
| **coverage_standard** | ACTIVE (READ-ONLY) | ✅ High | ✅ ALIGNED | ❌ | ❌ |
| **document** | ACTIVE | ✅ High | ✅ ALIGNED | ❌ | ❌ |
| **coverage_alias** | ACTIVE | ✅ Medium | ✅ ALIGNED | ❌ | ❌ |
| **coverage_code_alias** | ACTIVE | ⚠️ Low | ✅ ALIGNED | ❌ | △ |
| **coverage_subtype** | ACTIVE | ⚠️ Low | ⚠️ PARTIAL | ❌ | △ |
| **coverage_condition** | ACTIVE | ⚠️ Low | ✅ ALIGNED | ❌ | ❌ |
| **chunk** | ACTIVE | ✅ High | ✅ ALIGNED | ❌ | ❌ |
| **chunk_entity** | ACTIVE | ✅ Medium | ✅ ALIGNED | ❌ | ❌ |
| **amount_entity** | ACTIVE | ✅ Medium | ✅ ALIGNED | ❌ | ❌ |
| **disease_code_master** | ACTIVE | ✅ STEP 6-C | ✅ ALIGNED | ❌ | ❌ |
| **disease_code_group** | ACTIVE | ✅ STEP 6-C | ✅ ALIGNED | ❌ | ❌ |
| **disease_code_group_member** | ACTIVE | ✅ STEP 6-C | ✅ ALIGNED | ❌ | ❌ |
| **coverage_disease_scope** | ACTIVE | ✅ STEP 6-C | ✅ ALIGNED | ❌ | ❌ |
| **proposal_coverage_universe** | **ACTIVE (SSOT)** | ✅ High | ✅ ALIGNED | ❌ | ❌ |
| **proposal_coverage_mapped** | ACTIVE | ✅ High | ✅ ALIGNED | ❌ | ❌ |
| **proposal_coverage_slots** | ACTIVE | ✅ High | ✅ ALIGNED | ❌ | ❌ |
| **product_coverage** | ARCHIVED | ⚠️ **STEP 5 queries** | ❌ MISALIGNED | ❌ | ✅ |
| **premium** | ARCHIVED | ❌ None | ❌ NOT RELEVANT | ❌ | △ |

### Legend:
- ✅ High/Medium/Low = Active usage level
- ⚠️ = Warning - requires attention
- ❌ NOW = Do NOT delete now
- ❌ LATER = Never delete (core table)
- △ LATER = Consider deletion after evaluation
- ✅ LATER = Delete after refactoring

---

## Recommendations

### Immediate (STEP 6-D α) ✅
- ✅ Document cleanup only (this file + schema_inventory.md)
- ✅ Archive legacy schema definitions
- ✅ NO table drops, NO code changes

### STEP 7 (약관 파이프라인) 🔧
- Refactor `apps/api/app/queries/compare.py` to use Universe Lock tables
- Update integration tests to validate Universe Lock queries
- Implement `disease_scope_norm` population from policy documents
- Remove `product_coverage` references from code

### Post-STEP 7 △
- Evaluate `coverage_subtype` vs `disease_code_group` consolidation
- Consider dropping `product_coverage` table definition from archive (after confirming no code references)
- Review `coverage_code_alias` usage (low priority)

---

## Related Documentation

- **schema_inventory.md**: Table classification by architectural status
- **schema_current.sql**: Canonical schema (STEP 6-C baseline)
- **CLAUDE.md**: Constitutional principles (Universe Lock, Excel SSOT, KCD-7 SSOT)
- **STATUS.md**: Project status and STEP completion tracking

---

**Report Baseline**: STEP 6-C (Proposal Universe Lock v1)
**Critical Finding**: `product_coverage` used in STEP 5 queries - requires refactoring in STEP 7
**Next Action**: STEP 7 query refactoring to align with Universe Lock architecture
