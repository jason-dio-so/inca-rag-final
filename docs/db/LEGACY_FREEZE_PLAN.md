# Legacy Schema Freeze Plan

**Date**: 2025-12-26
**Purpose**: 기존 public schema 동결 및 v2 schema 이관 계획
**Principle**: "새 술은 새 포대" - DROP 금지, audit-only 동결

---

## Executive Summary

### Decision
- **A안 선택**: 같은 DB 내 schema 분리 (`public` vs `v2`)
- **Legacy**: public schema는 READ-ONLY audit trail로 동결
- **New**: v2 schema는 SSOT 기반 신규 구축

### Rationale
1. Docker Compose 운영 편의성 (기존 `inca_pg_step14` 컨테이너 유지)
2. 데이터 이관/조회 용이성 (cross-schema query 가능)
3. Volume 보존 (기존 데이터 유실 방지)
4. SSOT 위반 정도가 전면 재설계 필요 수준 (재활용 불가)

---

## Legacy Schema SSOT Violation Analysis

### Tier 1: Master Tables

| Table | SSOT Violation | Impact |
|-------|----------------|--------|
| `insurer` | `insurer_id` SERIAL (내부키), `insurer_code`가 enum 아님 | High - 모든 FK 재설계 필요 |
| `product` | `product_id` SERIAL (독립키), insurer+internal_product_code 규칙 미준수 | High - product_id FK 재설계 필요 |
| `document` | template_id 개념 없음, file_hash만으로 버전 관리 | Medium - template 계층 신규 도입 |

### Tier 2: Coverage Tables

| Table | SSOT Violation | Impact |
|-------|----------------|--------|
| `proposal_coverage_universe` | `insurer VARCHAR`, `proposal_id VARCHAR` (SSOT 우회) | High - insurer_code enum + product_id FK 필요 |
| `coverage_disease_scope` | `insurer VARCHAR`, `proposal_id VARCHAR` (동일) | High - 동일 |
| `coverage_alias` | `insurer_id` FK (SERIAL), `insurer_coverage_name` 중복 가능 | Medium - normalized_name + unique 제약 필요 |

### Tier 3: Chunk/Evidence Tables

| Table | SSOT Violation | Impact |
|-------|----------------|--------|
| `chunk` | `is_synthetic` 필터 기준이나 meta JSONB도 혼용 | Low - 스키마는 정합, 사용 규칙 준수 필요 |
| `chunk_entity` | 특이사항 없음 | None |
| `amount_entity` | 특이사항 없음 | None |

### Conclusion
**판정**: Tier 1/2 전면 재설계 필요 → 기존 schema 재활용 불가

---

## Legacy Freeze Strategy

### Phase 1: Schema Isolation (Immediate)

**Action**: public schema를 READ-ONLY로 전환

```sql
-- 1. 모든 애플리케이션 role의 public schema WRITE 권한 제거
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM app_ingestion;
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM app_api;
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM PUBLIC;

-- 2. SELECT만 허용
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_ingestion;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_api;

-- 3. Admin role만 WRITE 허용 (audit 목적)
GRANT ALL ON ALL TABLES IN SCHEMA public TO admin_role;

-- 4. 동결 표시
COMMENT ON SCHEMA public IS
'Legacy schema (FROZEN 2025-12-26) - READ-ONLY audit trail, DO NOT INSERT/UPDATE/DELETE';
```

**Timeline**: STEP NEXT-Z 완료 즉시 실행

### Phase 2: Legacy Data Cataloging

**Action**: 기존 데이터 3분류

#### Category A: 필수 이관 (Must Migrate)

| Table | Rows | Reason | Target v2 Table |
|-------|------|--------|-----------------|
| `insurer` | ~8 | 보험사 SSOT 기준 | `v2.insurer` (enum 기반 재생성) |
| `coverage_standard` | ~수백 | 신정원 코드 SSOT | `v2.coverage_standard` (Excel 기반 재생성) |
| `coverage_alias` | ~수천 | 담보명 매핑 이력 | `v2.coverage_name_map` (Excel 우선, legacy 보조) |

**Migration Method**:
- Excel/YAML 기반 재생성 (legacy는 참고용)
- insurer: 8개 enum 수동 INSERT
- coverage_standard: 기존 Excel (`data/담보명mapping자료.xlsx`) 재load
- coverage_alias: Excel 우선, legacy는 UNMAPPED 보완용

#### Category B: 동결 보관 (Freeze for Audit)

| Table | Rows | Reason | Action |
|-------|------|--------|--------|
| `proposal_coverage_universe` | ~수십 | 이전 추출 결과 (SSOT 위반) | 동결, 신규 추출은 v2 사용 |
| `proposal_coverage_mapped` | ~수십 | 이전 매핑 결과 | 동결, 신규 매핑은 v2 사용 |
| `proposal_coverage_slots` | ~수십 | 이전 slot 추출 결과 | 동결, 신규 추출은 v2 사용 |
| `disease_code_group` | ~수십 | 이전 질병 그룹 정의 | 동결, v2 재정의 |
| `chunk` / `chunk_entity` | ~수백 | 이전 ingestion 결과 | 동결, 신규 ingestion은 v2 사용 |

**Action**: READ-ONLY 유지, 신규 데이터는 v2로만 INSERT

#### Category C: 폐기 후보 (Deprecate)

| Table | Rows | Reason | Timeline |
|-------|------|--------|----------|
| `product` | ~수십 | product_id SSOT 위반, 재생성 필요 | 동결 후 6개월 뒤 DROP 검토 |
| `document` | ~수십 | template_id 개념 없음, 재생성 필요 | 동결 후 6개월 뒤 DROP 검토 |
| `coverage_condition` | ~수십 | 미사용 (현재 로직에서 참조 없음) | 동결 후 3개월 뒤 DROP 검토 |
| `coverage_subtype` | ~수십 | 미사용 | 동결 후 3개월 뒤 DROP 검토 |
| `coverage_code_alias` | ~수십 | 미사용 | 동결 후 3개월 뒤 DROP 검토 |

**Action**: 동결 후 사용 여부 모니터링, 미사용 확인 시 DROP

---

## Phase 3: v2 Schema Bootstrap

### Step 1: Schema Creation
```bash
psql -U postgres -d inca_rag_final -f docs/db/schema_v2.sql
```

### Step 2: Seed Data (Category A 이관)

**2.1 Insurer Seed** (8개 enum):
```sql
INSERT INTO v2.insurer (insurer_code, display_name, display_name_eng, is_active) VALUES
    ('SAMSUNG', '삼성화재', 'Samsung Fire & Marine Insurance', true),
    ('MERITZ', '메리츠화재', 'Meritz Fire & Marine Insurance', true),
    ('KB', 'KB손해보험', 'KB Insurance', true),
    ('HANA', '하나손해보험', 'Hana Insurance', true),
    ('DB', 'DB손해보험', 'DB Insurance', true),
    ('HANWHA', '한화손해보험', 'Hanwha General Insurance', true),
    ('LOTTE', '롯데손해보험', 'Lotte Insurance', true),
    ('HYUNDAI', '현대해상', 'Hyundai Marine & Fire Insurance', true);
```

**2.2 Coverage Standard Seed** (Excel 기반):
```bash
python apps/api/scripts/seed_coverage_standard_v2.py \
    --excel data/담보명mapping자료.xlsx \
    --target v2.coverage_standard
```

**2.3 Coverage Name Map Seed** (Excel 기반):
```bash
python apps/api/scripts/seed_coverage_name_map_v2.py \
    --excel data/담보명mapping자료.xlsx \
    --target v2.coverage_name_map
```

### Step 3: Extraction Pipeline Setup

**3.1 Template Extraction**:
```bash
python apps/api/scripts/extract_proposal_template_v2.py \
    --pdf data/가입설계서/삼성화재_암보험_202401.pdf \
    --insurer SAMSUNG \
    --product_code CANCER_2024
```

**3.2 Coverage Extraction**:
```bash
python apps/api/scripts/extract_proposal_coverage_v2.py \
    --template_id SAMSUNG_CANCER_2024_proposal_202401_a1b2c3d4
```

**3.3 Coverage Mapping**:
```bash
python apps/api/scripts/map_coverage_excel_v2.py \
    --template_id SAMSUNG_CANCER_2024_proposal_202401_a1b2c3d4
```

---

## Phase 4: Legacy Data Migration (Optional)

### When to Migrate
- v2 schema 안정화 후 (STEP NEXT-Z+1 이후)
- 기존 추출 결과를 v2로 재현 필요 시

### Migration Script Template
```python
# scripts/migrate_legacy_to_v2.py
import psycopg2

# 1. Legacy insurer → v2 insurer (enum 기반 재매핑)
legacy_insurer = query("SELECT insurer_code, insurer_name FROM public.insurer")
for row in legacy_insurer:
    legacy_code = row['insurer_code']
    v2_code = map_to_enum(legacy_code)  # 예: "SAMSUNG_FIRE" → "SAMSUNG"
    insert("INSERT INTO v2.insurer ... WHERE insurer_code = %s", v2_code)

# 2. Legacy product → v2 product (product_id 재생성)
legacy_product = query("SELECT * FROM public.product")
for row in legacy_product:
    insurer_code = resolve_v2_insurer(row['insurer_id'])
    internal_code = row['product_code']
    product_id = f"{insurer_code}_{internal_code}"
    insert("INSERT INTO v2.product (product_id, ...) VALUES (%s, ...)", product_id)

# 3. Legacy proposal_coverage_universe → v2 proposal_coverage
# SKIP - SSOT 위반으로 재추출 권장 (migration 비권장)
```

### Migration Policy
- **Tier 1 (insurer/coverage_standard)**: Excel 기반 재생성 (legacy 참고만)
- **Tier 2 (proposal_coverage)**: 재추출 권장 (legacy migration 비권장)
- **Tier 3 (chunk/entity)**: 필요시만 migration (대부분 재ingestion 권장)

---

## Phase 5: Application Layer Migration

### Code Change Scope

#### 5.1 Database Connection
```python
# Before (legacy)
from app.db import engine  # uses public schema

# After (v2)
from app.db_v2 import engine_v2  # uses v2 schema
```

#### 5.2 Model Change
```python
# Before
class ProposalCoverageUniverse(Base):
    __tablename__ = "proposal_coverage_universe"
    insurer = Column(String)  # SSOT 위반

# After
class ProposalCoverage(BaseV2):
    __tablename__ = "proposal_coverage"
    __table_args__ = {'schema': 'v2'}
    template_id = Column(String, ForeignKey('v2.template.template_id'))  # SSOT 준수
```

#### 5.3 API Endpoint Change
```python
# Before
@router.get("/compare")
async def compare(insurer_a: str, insurer_b: str):
    # uses public.proposal_coverage_universe
    pass

# After
@router.get("/compare")
async def compare_v2(product_a: str, product_b: str):
    # uses v2.proposal_coverage + v2.proposal_coverage_mapped
    pass
```

### Rollback Strategy
- v2 schema 장애 시: legacy public schema 읽기 fallback
- Feature flag: `USE_V2_SCHEMA` (default: true, rollback: false)

---

## Monitoring & Validation

### Migration Metrics

| Metric | Target | Validation Query |
|--------|--------|------------------|
| v2.insurer row count | 8 | `SELECT COUNT(*) FROM v2.insurer` |
| v2.coverage_standard row count | ~수백 (Excel 기준) | `SELECT COUNT(*) FROM v2.coverage_standard` |
| v2.proposal_coverage row count | > legacy count (재추출 포함) | `SELECT COUNT(*) FROM v2.proposal_coverage` |
| public schema WRITE 시도 | 0 | `SELECT COUNT(*) FROM pg_stat_user_tables WHERE schemaname='public' AND (n_tup_ins + n_tup_upd + n_tup_del) > 0 SINCE freeze_time` |

### Audit Trail

**Freeze Log**:
```sql
CREATE TABLE v2.migration_log (
    log_id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL, -- freeze / migrate / validate
    event_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    schema_name VARCHAR(50),
    table_name VARCHAR(200),
    row_count BIGINT,
    details JSONB,
    status VARCHAR(20) -- success / fail / pending
);

INSERT INTO v2.migration_log (event_type, schema_name, details, status) VALUES
    ('freeze', 'public', '{"action": "REVOKE INSERT/UPDATE/DELETE", "reason": "SSOT violation"}', 'success');
```

---

## Timeline

| Phase | Target Date | Status | DoD |
|-------|-------------|--------|-----|
| Phase 1: Schema Isolation | 2025-12-26 (STEP NEXT-Z 완료 시) | Pending | public schema READ-ONLY |
| Phase 2: Legacy Cataloging | 2025-12-26 (동일) | Pending | 3-category 분류 완료 |
| Phase 3: v2 Bootstrap | 2025-12-27 (NEXT-Z+1) | Pending | v2 schema + seed data 완료 |
| Phase 4: Legacy Migration | 2025-12-28 (NEXT-Z+2) | Optional | Category A 이관 완료 |
| Phase 5: App Layer Migration | 2025-12-29 (NEXT-Z+3) | Pending | API/ViewModel v2 연결 |
| Legacy Drop Review | 2026-03-26 (3개월 후) | Future | Category C DROP 검토 |

---

## Risk Mitigation

### Risk 1: Legacy Data 유실
**Mitigation**:
- Volume backup before freeze
- public schema는 DROP 금지 (audit trail 유지)
- Category C도 최소 3개월 유예

### Risk 2: v2 Migration 실패
**Mitigation**:
- Feature flag rollback (`USE_V2_SCHEMA=false`)
- Legacy public schema 읽기 fallback 코드 유지
- v2 schema 장애 시 자동 rollback

### Risk 3: SSOT 재위반
**Mitigation**:
- v2 schema CHECK 제약 강제 (chk_product_id_format 등)
- Migration script validation (SSOT 준수 검증)
- Code review checklist (SSOT compliance)

---

## Appendix: SSOT Compliance Checklist

### v2 Schema Validation

#### Insurer SSOT
- [ ] insurer_code가 8개 enum 중 하나인가?
- [ ] display_name이 UI 노출용으로 분리되었는가?
- [ ] 문자열 insurer로 저장/조인/필터링하지 않았는가?

#### Product SSOT
- [ ] product_id가 `{insurer_code}_{internal_product_code}` 형식인가?
- [ ] product_id가 CHECK 제약으로 강제되는가?
- [ ] display_name이 UI 노출용으로 분리되었는가?

#### Template SSOT
- [ ] template_id가 `{product_id}_{type}_{version}_{fingerprint[0:8]}` 형식인가?
- [ ] template_id가 CHECK 제약으로 강제되는가?
- [ ] fingerprint가 64자 SHA256인가?

#### Coverage Mapping SSOT
- [ ] canonical_coverage_code가 Excel 단일 출처에서만 왔는가?
- [ ] mapping_status가 MAPPED/UNMAPPED/AMBIGUOUS 중 하나인가?
- [ ] MAPPED 시 canonical_coverage_code IS NOT NULL CHECK 제약이 있는가?

---

## Decision Log

| Date | Decision | Reason | Status |
|------|----------|--------|--------|
| 2025-12-26 | A안 선택 (같은 DB 내 schema 분리) | Docker Compose 운영 편의성, 데이터 이관/조회 용이성 | Approved |
| 2025-12-26 | Legacy public schema READ-ONLY 동결 | SSOT 위반 정도가 재활용 불가 수준 | Approved |
| 2025-12-26 | Category A (insurer/coverage_standard) Excel 기반 재생성 | Legacy 참고용만, Excel SSOT 원칙 준수 | Approved |
| 2025-12-26 | Category B (proposal_coverage 등) 동결, 재추출 권장 | SSOT 위반 데이터 migration 비권장 | Approved |
| 2025-12-26 | Category C (product/document 등) 3~6개월 후 DROP 검토 | 미사용 확인 필요 | Pending |

---

## Contact

**Questions**: CLAUDE.md 수정 PR 제출
**Issues**: GitHub `inca-rag-final` repository issue 등록
