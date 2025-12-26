# STATUS - inca-RAG-final

**Last Updated**: 2025-12-26

## STEP NEXT-AF-FIX 완료 (Commit 9611fce)

### 목표 달성
✅ Proposal Detail (상세표) → Comparison Description 저장/표시 (Production-Quality)

### 핵심 개선사항

#### 1. Migration Safety (Commit 57cc9b3)
- ❌ DROP TABLE 제거 → ✅ CREATE IF NOT EXISTS
- ✅ extraction_method 컬럼 추가 (deterministic_v1/v2/manual 구분)
- ✅ 누적 데이터 보존 (여러 보험사/템플릿)
- ✅ Idempotent migration (재실행 안전)

#### 2. Extraction Quality (af_extract_proposal_detail_v2.py)
- ✅ Section detection: 키워드 기반 detail 섹션 탐지 (보장내용/지급사유)
- ✅ Line-based fallback: 테이블 추출 실패 시 텍스트 파싱
- ✅ Meta row filtering: 주계약/선택계약/통합고객 등 제외
- ✅ Template isolation: 동일 template_id 내에서만 매칭 (혼입 방지)
- ✅ Deterministic only: extraction_method='deterministic_v2' 고정

**결과**:
- 36 details extracted (vs 7 in v1)
- 4 matched (11.1% match rate)
- 0 manual entries

#### 3. ViewModel Enrichment Fix (apps/api/app/routers/view_model.py)
- ✅ Row-level matching: 각 fact_table row에 개별 comparison_description 연결
- ✅ Template_id resolution: v2.proposal_coverage에서 template_id 조회
- ✅ Deterministic filter: extraction_method LIKE 'deterministic%' 만 사용
- ❌ Cross-template mixing 방지

#### 4. Smoke Test Quality Checks (Test 9)
- ✅ Match rate 표시 (11.1%)
- ✅ Manual entry detection (manual 있으면 WARNING)
- ✅ Quality threshold (< 10% 시 WARNING)
- ✅ DoD: >= 1 template + >= 1 matched + no manual entries

### Data Quality 이슈 발견
⚠️ **proposal_coverage에 meta-header row 존재** (통합고객 보험나이변경일...)
- 영향: Universe에 비담보 row 포함
- 현재 조치: AF-FIX에서 meta row 필터링으로 회피
- 향후 조치: Proposal Summary ingest 버그 픽스 별도 티켓

### DoD 달성
✅ Test 9 PASS:
- 1 template with deterministic details
- 4 matched details
- 0 manual entries
- 11.1% match rate (threshold 10% 초과)

### Git Status
- **Branch**: main
- **Commits**:
  - 57cc9b3: fix(migration): AF-FIX safe migration
  - 9611fce: fix(af): AF-FIX deterministic extraction + row-level join
- **Pushed**: ✅ origin/main

### 다음 단계
- Proposal summary ingest 버그 픽스 (통합고객 row 제거)
- Match rate 개선 (현재 11.1% → 목표 30%+)
  - Normalization 개선
  - Partial matching threshold 조정
- 추가 보험사 테스트 (현재 Samsung만)

---

## 이전 단계

### STEP NEXT-AF (Commit 8c6784a)
- v2.proposal_coverage_detail 테이블 생성
- af_extract_proposal_detail.py (v1) 초기 구현
- ViewModel.FactTableRow에 comparison_description 필드 추가
- DoD 임시 달성 (manual INSERT로 1개 matched)

**문제점**:
- ❌ DROP TABLE → 데이터 파괴
- ❌ Manual INSERT 허용
- ❌ 낮은 추출 품질 (7 details, 0 matched)
- ❌ Template 혼입 가능성

→ AF-FIX에서 전면 개선 완료

---

**현행 시스템**: STEP NEXT-AF-FIX (Production-Ready)
