# Database Schema Inventory

**Purpose**: Classify all tables by current architectural status
**Design Baseline**: STEP 6-C Proposal Universe Lock
**Last Updated**: 2025-12-24

---

## Table Classification Legend

| Status | Meaning |
|--------|---------|
| **ACTIVE** | Core table, actively used in current architecture |
| **ACTIVE (Context)** | Used for context/metadata, not primary comparison axis |
| **ARCHIVED** | Deprecated design, table definition moved to `archive/` |
| **NOT IMPLEMENTED** | Defined in archived schemas but never created in actual DB |

---

## Canonical Layer (기준/마스터 계층)

| Table | Status | Role | Reason |
|-------|--------|------|--------|
| `insurer` | **ACTIVE (Context)** | 보험사 마스터 | Context axis - identifies proposal source, not comparison axis |
| `product` | **ACTIVE (Context)** | 보험 상품 마스터 | Context axis - links documents to insurer, NOT primary compare axis |
| `coverage_standard` | **ACTIVE** | 신정원 통일 담보 코드 (READ-ONLY) | Single source of truth for canonical coverage codes |
| `document` | **ACTIVE** | 보험 문서 메타데이터 | Stores all document types (proposals, policies, terms) for evidence |

### Notes:
- **product role shift**: Originally designed for product-centered comparison → Now serves as **Context Axis only**
- product is NOT the primary comparison dimension (Proposal Universe Lock principle)
- Products provide context (insurer, document grouping) but comparisons happen at **proposal coverage** level

---

## Normalization Layer (매핑/정규화 계층)

| Table | Status | Role | Reason |
|-------|--------|------|--------|
| `coverage_alias` | **ACTIVE** | 보험사별 담보명 매핑 | Maps insurer-specific coverage names to canonical codes (auto-INSERT allowed) |
| `coverage_code_alias` | **ACTIVE** | 레거시 코드 매핑 | Maps legacy coverage codes to canonical codes |
| `coverage_subtype` | **ACTIVE** | 담보 세부 유형 | Defines subtypes like 경계성종양, 제자리암, 유사암 |
| `coverage_condition` | **ACTIVE** | 담보 지급 조건 | Stores coverage payout conditions, reduction rules, exclusions |

---

## Document & Chunk Layer (문서/청크 계층)

| Table | Status | Role | Reason |
|-------|--------|------|--------|
| `chunk` | **ACTIVE** | RAG 청크 (원본 + synthetic) | Document chunks for RAG retrieval, synthetic chunks for Amount Bridge |
| `chunk_entity` | **ACTIVE** | 추출 엔티티 | All extracted entities (coverage/amount/disease/surgery) from chunks |
| `amount_entity` | **ACTIVE** | 금액 엔티티 (Amount Bridge) | Amount-specific structured data for Amount Bridge use case |

### Constitutional Rules:
- **Synthetic chunks**: `is_synthetic=true` → Amount Bridge ONLY
- **Compare/retrieval**: MUST filter `is_synthetic=false` (hard-coded in SQL)
- **Meta field**: Reference only, NOT for filtering (use `is_synthetic` column)

---

## STEP 6-C: Proposal Universe Lock (현행 비교 시스템)

### 3-Tier Disease Code Model

| Table | Status | Tier | Role |
|-------|--------|------|------|
| `disease_code_master` | **ACTIVE** | Tier 1 | KCD-7 코드 사전 - 공식 배포본 ONLY (보험 의미 금지) |
| `disease_code_group` | **ACTIVE** | Tier 2 | 보험 질병 개념 그룹 (유사암, 소액암 등) - insurer별 분리 |
| `disease_code_group_member` | **ACTIVE** | Tier 2 | 그룹 멤버 (단일 코드 또는 범위) |
| `coverage_disease_scope` | **ACTIVE** | Tier 3 | 담보별 질병 범위 (include/exclude 그룹 참조) |

#### Constitutional Principles:
- **KCD-7 single source**: `disease_code_master` source MUST be "KCD-7 Official Distribution"
- **Insurance concepts ≠ disease codes**: 유사암, 소액암 → `disease_code_group` (NOT disease_code_master)
- **insurer=NULL restriction**: Only for medical/KCD classification groups (C00-C97 범위 등)
- **Evidence required**: `disease_code_group` MUST have `basis_doc_id`, `basis_span`

### Proposal Universe Lock Tables

| Table | Status | Role | Reason |
|-------|--------|------|--------|
| `proposal_coverage_universe` | **ACTIVE** | **가입설계서 담보 Universe** | **Comparison SSOT** - 비교 대상의 절대 기준 (Coverage Universe Lock) |
| `proposal_coverage_mapped` | **ACTIVE** | Universe → Canonical 매핑 | Excel-based mapping results (MAPPED/UNMAPPED/AMBIGUOUS) |
| `proposal_coverage_slots` | **ACTIVE** | Slot Schema v1.1.1 저장소 | Extracted slots from proposals (20 slots including disease_scope, payout_limit) |

#### Comparison Flow:
```
1. proposal_coverage_universe (설계서 담보 원본)
   ↓
2. proposal_coverage_mapped (Excel 기반 canonical code 매핑)
   ↓
3. proposal_coverage_slots (Slot Schema v1.1.1 추출)
   ↓
4. 5-State Comparison (comparable / comparable_with_gaps / non_comparable / unmapped / out_of_universe)
```

#### 5-State Comparison System:
1. **comparable** - All critical slots match, no gaps
2. **comparable_with_gaps** - Same canonical code, some slots NULL (policy_required)
3. **non_comparable** - Different canonical codes or incompatible
4. **unmapped** - Exists in universe but Excel mapping failed
5. **out_of_universe** - NOT in proposal (Universe Lock violation)

---

## Archived Tables (NOT in current schema)

These tables were defined in `archive/schema_v2_additions.sql` but are **NOT part of current architecture**:

| Table | Status | Original Purpose | Conflict with Current Design |
|-------|--------|------------------|------------------------------|
| `product_coverage` | **ARCHIVED (NOT IMPLEMENTED)** | 상품별 담보 보장 금액/조건 | **Product-centered comparison** - conflicts with Proposal Universe Lock |
| `premium` | **ARCHIVED (NOT IMPLEMENTED)** | 보험료 (연령/성별별) | Product-level data - not relevant for coverage comparison |

### Why Archived:
- **Architectural shift**: 약관/상품 중심 → 가입설계서 담보 중심 (Proposal Universe Lock)
- **product_coverage conflicts**: Assumes "product → coverage" as primary comparison axis
- **Current approach**: `proposal_coverage_universe` (proposal-level) → `proposal_coverage_mapped` (canonical mapping)
- **Evidence source**: Proposals (설계서), not products

### Archive Location:
- `docs/db/archive/schema_v2_additions.sql`
- These tables were **never created** in actual database
- Kept for historical context only

---

## Views (4 active views)

| View | Status | Purpose |
|------|--------|---------|
| `v_active_products` | **ACTIVE** | 활성 상품 목록 (Context axis) |
| `v_coverage_mapping` | **ACTIVE** | 담보 매핑 현황 |
| `v_original_chunks` | **ACTIVE** | 원본 청크 (is_synthetic=false 필터링) |
| `v_proposal_coverage_full` | **ACTIVE** | **Universe → Mapping → Slots 전체 파이프라인** |

### Primary View for Comparisons:
**`v_proposal_coverage_full`** - End-to-end proposal coverage pipeline view

---

## Summary Statistics

### Active Tables by Category:
- **Canonical Layer**: 4 tables (insurer, product, coverage_standard, document)
- **Normalization Layer**: 4 tables (coverage_alias, coverage_code_alias, coverage_subtype, coverage_condition)
- **Document & Chunk Layer**: 3 tables (chunk, chunk_entity, amount_entity)
- **STEP 6-C Disease Model**: 4 tables (disease_code_master, disease_code_group, disease_code_group_member, coverage_disease_scope)
- **STEP 6-C Proposal Universe**: 3 tables (proposal_coverage_universe, proposal_coverage_mapped, proposal_coverage_slots)

**Total Active**: 18 tables

### Archived Tables:
- **product_coverage**: 1 table (never implemented)
- **premium**: 1 table (never implemented)

**Total Archived**: 2 tables (documentation only, not in actual DB)

---

## Deletion Timeline

### NOW (STEP 6-D α) ❌
- **No actual DROP statements**
- Documentation cleanup only
- Archive old design artifacts

### LATER (Post-STEP 7) △
- Evaluate `product_coverage`, `premium` references in codebase
- If truly unused → Consider DROP (with migration)
- Re-evaluate `product` role (keep as Context Axis)

---

## Related Documentation

- **schema_current.sql**: Full canonical schema (STEP 6-C baseline)
- **erd_current.mermaid**: Visual representation (1:1 with schema_current.sql)
- **table_usage_report.md**: Code usage analysis for each table
- **archive/schema_v2_additions.sql**: Deprecated product-centered design

---

**Inventory Baseline**: STEP 6-C (Proposal Universe Lock v1)
**Architecture Principle**: Proposal-centered comparison, product as context only
**Next Step**: STEP 7 (약관 파이프라인 - disease_scope_norm population)
