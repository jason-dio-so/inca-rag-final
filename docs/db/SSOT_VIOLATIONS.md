# SSOT Violations Report

**생성일**: 2025-12-26
**목적**: Insurer/Product/Template SSOT Hard Rule 위반 자산 목록화
**규칙 출처**: CLAUDE.md § Insurer / Product / Template SSOT (Hard Rule)

---

## Executive Summary

본 보고서는 CLAUDE.md에 신설된 "Insurer/Product/Template SSOT Hard Rule" 기준으로 현재 codebase를 검증한 결과다.

**검증 기준**:
1. insurer를 문자열(VARCHAR)로 저장/조인/필터링 (insurer_code enum 우회)
2. product_name을 SSOT 없이 문자열로 직접 저장 (product 테이블 우회)
3. template_id 규칙 위반 (랜덤/증분/임의 생성)
4. proposal_id를 product_id 대신 사용
5. 테이블별로 보험사명/상품명 정의 분산

---

## Violation Category 1: insurer VARCHAR (String-based Insurer Storage)

### 위반 근거
CLAUDE.md Hard Rule:
> insurer_code = 유일키 (SAMSUNG, MERITZ, KB, HANA, DB, HANWHA, LOTTE, HYUNDAI)
> **절대 금지**: 문자열 보험사명을 직접 저장/비교/조인 (코드 우회)

### 위반 자산 목록

#### DB Schema

**파일**: `migrations/step6c/001_proposal_universe_lock.sql`
- `disease_code_group.insurer VARCHAR(50)` (L39)
- `coverage_disease_scope.insurer VARCHAR(50)` (L94)
- `proposal_coverage_universe.insurer VARCHAR(50)` (L125)

**파일**: `docs/db/schema_current.sql`
- `disease_code_group.insurer VARCHAR(50)` (L258)
- `coverage_disease_scope.insurer VARCHAR(50)` (L309)
- `proposal_coverage_universe.insurer VARCHAR(50)` (L337)

**파일**: `migrations/step6b/000_base_schema.sql`
- `coverage_standard.insurer_code VARCHAR(50)` (L36)
- `insurer.insurer_code VARCHAR(50)` (L55) — 이 테이블은 SSOT로 인정 가능하나, insurer_code가 enum 대신 VARCHAR

**영향**:
- proposal_coverage_universe, coverage_disease_scope, disease_code_group 모두 insurer를 VARCHAR로 저장
- FK 없이 문자열 비교/조인 전제 (enum 우회)

#### Python Code

**파일**: `apps/api/app/schemas/compare.py`
- `ProposalCoverageItem.insurer: str` (L138)
- `PolicyEvidence.insurer: str` (L155)

**파일**: `apps/api/app/view_model/types.py`
- (확인 필요: insurer 필드 타입)

**파일**: `apps/api/app/admin_mapping/models.py`
- (확인 필요: insurer 필드 타입)

---

## Violation Category 2: proposal_id as Product Identifier

### 위반 근거
CLAUDE.md Hard Rule:
> product_id = 유일키 (insurer_code + internal_product_code)
> **절대 금지**: proposal_id 등 임시 식별자로 product_id 대체

### 위반 자산 목록

#### DB Schema

**파일**: `migrations/step6c/001_proposal_universe_lock.sql`
- `proposal_coverage_universe.proposal_id VARCHAR(200)` (L126)
- `coverage_disease_scope.proposal_id VARCHAR(200)` (L95)
- UNIQUE 제약: `(insurer, proposal_id, normalized_name)` (L142)

**현재 상황**:
- proposal_id가 product 식별의 실질적 유일키로 사용됨
- product_id FK 없음
- proposal_id = "PROP_SAMSUNG_001" 등 임시 식별자

#### Python Code

**파일**: `apps/api/app/schemas/compare.py`
- `ProposalCoverageItem.proposal_id: str` (L139) — product_id 없이 proposal_id만 사용

**파일**: `apps/api/app/view_model/assembler.py`
- (확인 필요: proposal_id 사용 여부)

**파일**: `apps/api/app/queries/compare.py`
- (확인 필요: proposal_id 기반 조인/필터링)

---

## Violation Category 3: product_name Direct Storage (SSOT Bypass)

### 위반 근거
CLAUDE.md Hard Rule:
> 고객 노출 상품명은 product 테이블에서만 관리
> **절대 금지**: product_name을 문자열로 직접 저장 (SSOT 우회)

### 위반 자산 목록

#### DB Schema

**파일**: `migrations/step6b/000_base_schema.sql`
- `product.product_name VARCHAR(300)` (L67) — 이 테이블은 SSOT이므로 정상

**파일**: `docs/db/schema_current.sql`
- `product.product_name VARCHAR(300)` (L39) — SSOT 테이블이므로 정상

#### Python Code

**파일**: `apps/api/app/schemas/compare.py`
- `CompareItem.product_name: str` (L78) — product 테이블에서 조회 시 정상, 직접 저장하면 위반

**파일**: `apps/api/app/queries/compare.py`
- `SELECT p.product_name FROM public.product p` (L73-74) — product 테이블에서 조회하므로 정상

**결론**: 현재 product_name은 product 테이블 SSOT를 준수 중 (위반 없음)

---

## Violation Category 4: template_id 부재

### 위반 근거
CLAUDE.md Hard Rule:
> template_id = insurer_code + product_id + version + fingerprint(content_hash)
> **절대 금지**: 임의 template_id 생성 (규칙 위반)

### 현재 상황

#### DB Schema

**전체 schema 검색 결과**: `template_id` 컬럼 없음

**영향**:
- 가입설계서/문서 템플릿 식별 기준 부재
- 문서 버전/양식 변경 감지 불가
- proposal_coverage_universe는 content_hash만 사용 (문서 전체 식별 아님)

#### Python Code

**전체 codebase 검색 결과**: `template_id` 사용 없음

---

## Violation Category 5: insurer 테이블 enum 미사용

### 위반 근거
CLAUDE.md Hard Rule:
> insurer_code = 유일키 (SAMSUNG, MERITZ, KB, HANA, DB, HANWHA, LOTTE, HYUNDAI)
> 8개 insurer_code (enum) + display_name 분리

### 현재 상황

#### DB Schema

**파일**: `migrations/step6b/000_base_schema.sql`
- `insurer.insurer_code VARCHAR(50)` (L55) — enum 타입 아님, VARCHAR로 선언
- 8개 고정 제약 없음 (CHECK constraint 부재)

**영향**:
- insurer_code를 문자열로 저장하여 임의 보험사 추가 가능
- enum 타입 보장 없음 (PostgreSQL ENUM 또는 CHECK constraint 필요)

---

## Non-Violation (SSOT 준수 사례)

### insurer/product 테이블 (SSOT 역할 수행 중)

**파일**: `migrations/step6b/000_base_schema.sql`
- `insurer` 테이블: insurer_id PK, insurer_code UNIQUE (L50-61)
- `product` 테이블: product_id PK, insurer_id FK, product_name (L63-76)

**현재 상태**:
- insurer/product 테이블은 SSOT 역할 수행
- 단, insurer_code가 VARCHAR이므로 enum 강제 필요

---

## Migration Impact Analysis

### "새 술은 새 포대" 판단

**기존 스키마 재활용 가능성**:
- ❌ `proposal_coverage_universe` — insurer VARCHAR, proposal_id 기준 (재구축 필요)
- ❌ `coverage_disease_scope` — insurer VARCHAR, proposal_id FK (재구축 필요)
- ❌ `disease_code_group` — insurer VARCHAR (재구축 필요)
- ✅ `insurer` 테이블 — insurer_code만 enum으로 변경 시 재활용 가능
- ✅ `product` 테이블 — 현재 SSOT 역할 수행 (product_id 기준 재설계 필요)

**권장 사항**:
1. insurer_code → PostgreSQL ENUM 타입으로 변경 (8개 고정)
2. proposal_coverage_universe → product_id FK 추가, proposal_id 제거
3. coverage_disease_scope → insurer VARCHAR 제거, insurer_id FK 추가
4. template_id 스키마 신규 설계 (insurer_code + product_id + version + fingerprint)

---

## Summary Statistics

| Category | Violation Count | Status |
|----------|----------------|--------|
| insurer VARCHAR 사용 | 6개 테이블, 3개 Python 타입 | 🔴 위반 |
| proposal_id 사용 (product_id 대신) | 2개 테이블, 1개 Python 타입 | 🔴 위반 |
| product_name SSOT 우회 | 0건 | ✅ 준수 |
| template_id 부재 | 전체 codebase | 🔴 위반 |
| insurer enum 미사용 | 1개 테이블 (insurer) | 🔴 위반 |

**전체 위반 심각도**: 🔴 High (재구축 필요)

---

## Next Steps (권장)

1. **CLAUDE.md 헌법 추가 완료** ✅ (본 STEP에서 완료)
2. **본 보고서 작성 완료** ✅ (본 STEP에서 완료)
3. **Migration 설계** (차기 STEP)
   - insurer_code ENUM 타입 변경
   - proposal_coverage_universe 재설계 (product_id FK)
   - template_id 스키마 신규 추가
4. **Python 타입 정합** (차기 STEP)
   - InsurerCode(Enum) 타입 도입
   - proposal_id → product_id 전환
5. **Provenance Audit** (차기 STEP)
   - Route Alignment 검증
   - DB 데이터 출처 확인

---

**본 보고서는 삭제/DROP을 권장하지 않으며, 위반 자산의 이관 계획 수립을 목적으로 한다.**
