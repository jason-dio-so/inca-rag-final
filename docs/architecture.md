# inca-RAG-final 전체 아키텍처 설계

> 본 문서는 보험 약관 비교 RAG 시스템의 최종 아키텍처를 정의한다.

---

## 1. 시스템 개요

### 1.1 목적
- 여러 보험사의 보험 상품을 담보(coverage) 단위로 정확하게 비교
- 신정원 통일 담보 코드 기반의 canonical coverage 체계
- Amount Bridge를 통한 금액 의도 질의 처리

### 1.2 핵심 원칙
1. **신정원 통일 코드 절대 기준**: coverage_code는 신정원 canonical만 사용
2. **Synthetic chunk는 Amount Bridge 전용**: 비교축에서 제외
3. **의미 규칙 외부화**: 비즈니스 로직은 설정/테이블로 관리
4. **Plan 기반 검색**: 성별/나이별 플랜 자동 선택 후 검색

---

## 2. 시스템 구성도

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                      │
│  - Chat UI                                                  │
│  - Coverage Compare View                                   │
│  - Evidence Viewer (PDF page viewer)                       │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────┴────────────────────────────────────────┐
│                   Backend (FastAPI)                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  /compare API                                       │  │
│  │  - Query parsing & intent detection                 │  │
│  │  - Coverage resolution (SAFE_RESOLVED/UNRESOLVED)   │  │
│  │  - Plan selection                                   │  │
│  │  - Compare axis retrieval                           │  │
│  │  - Diff summary generation                          │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Retrieval Layer                                    │  │
│  │  - Compare axis (coverage_code + plan_id)           │  │
│  │  - Policy axis (약관 keyword 검색)                  │  │
│  │  - Amount Bridge (금액 의도 처리)                   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Extraction Layer                                   │  │
│  │  - Amount extractor                                 │  │
│  │  - Condition snippet extractor                      │  │
│  │  - Subtype classifier                               │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│              Database (PostgreSQL + pgvector)               │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Canonical │  │   Document  │  │    Chunk    │        │
│  │   Coverage  │  │   Metadata  │  │  (vector +  │        │
│  │   Tables    │  │             │  │   metadata) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  coverage_standard, coverage_alias, coverage_name_map      │
│  insurer, product, product_plan, document, chunk           │
└─────────────────────────────────────────────────────────────┘
                     ▲
                     │
┌────────────────────┴────────────────────────────────────────┐
│                  Ingestion Pipeline                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  1. Document Loader (PDF → Text)                    │  │
│  │  2. Plan Detector (성별/나이 → plan_id)             │  │
│  │  3. Chunker (문서 → chunk 분할)                     │  │
│  │  4. Coverage Tagger (coverage_alias → code)         │  │
│  │  5. Amount Tagger (금액 추출 → meta.amount)         │  │
│  │  6. Embedder (chunk → vector)                       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Synthetic Chunk Generator (선택적)                 │  │
│  │  - Mixed coverage chunk 분해                        │  │
│  │  - Amount Bridge 전용                               │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                     ▲
                     │ Copy (read-only)
┌────────────────────┴────────────────────────────────────────┐
│            Original Documents (data/)                       │
│  - SAMSUNG/약관/*.pdf                                       │
│  - SAMSUNG/상품요약서/*.pdf                                 │
│  - LOTTE/약관/*.pdf                                         │
│  - ...                                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 데이터 흐름

### 3.1 Ingestion 흐름

```
원본 PDF
  ↓
1. Document Loader
  - PDF → Text 변환
  - 메타데이터 추출 (doc_type, version 등)
  ↓
2. Plan Detector
  - 성별/나이 조건 탐지 → plan_id
  - manifest.csv 기반 자동 매핑
  ↓
3. Chunker
  - 청크 분할 (페이지/섹션 단위)
  - page_start, page_end 기록
  ↓
4. Coverage Tagger
  - coverage_alias 매칭 (보험사별)
  - coverage_code 부여 (신정원 기준)
  ↓
5. Amount Tagger
  - amount_extractor로 금액 추출
  - meta.entities.amount 저장
  - payment-context / count-context 필터 적용
  ↓
6. Embedder
  - OpenAI text-embedding-3-small
  - chunk.embedding 저장
  ↓
DB INSERT
  - chunk 테이블에 저장
  - is_synthetic = false (일반 chunk)
```

### 3.2 Synthetic Chunk 생성 흐름 (선택적)

```
Mixed Coverage Chunk 후보 스캔
  ↓
담보별 라인 추출
  - coverage_alias 매칭
  - amount_extractor 적용
  - payment/count-context 필터
  ↓
Synthetic Chunk 생성
  - 담보별로 1개씩 분리
  - meta.is_synthetic = true
  - meta.synthetic_type = "split"
  - meta.synthetic_method = "v1_6_3_beta_2_split"
  ↓
DB INSERT
  - Amount Bridge 전용
```

### 3.3 Compare 흐름

```
User Query
  ↓
1. Query Parsing
  - 질의 의도 분석
  - 금액 의도 여부 판단
  ↓
2. Coverage Resolution
  - 질의 → domain 판별
  - domain → representative coverage 선택
  - SAFE_RESOLVED / UNRESOLVED 상태 결정
  ↓
3. Plan Selection
  - 질의에서 성별/나이 추출
  - plan_id 자동 선택
  ↓
4-A. Compare Axis Retrieval (일반 비교)
  - coverage_code + plan_id 기반 검색
  - is_synthetic = false 필터
  - doc_type 우선순위 적용
  ↓
4-B. Amount Bridge Retrieval (금액 의도)
  - SAFE_RESOLVED + 금액 의도인 경우만
  - is_synthetic 필터 없음 (synthetic 허용)
  - amount_bearing_evidence 검색
  ↓
5. Diff Summary Generation
  - 보험사별 차이점 추출
  - 규칙 엔진 기반
  ↓
Response
  - coverage_compare_result (비교표)
  - diff_summary (차이점 요약)
  - amount_bridge (금액 비교, 조건부)
```

---

## 4. 핵심 컴포넌트 책임

### 4.1 Coverage Resolution
- **입력**: User query
- **출력**: resolved_coverage_codes, resolution_state
- **책임**:
  - 질의 → domain 판별
  - domain → representative coverage 선택
  - SAFE_RESOLVED: 자동 선택 성공
  - UNRESOLVED: 후보만 제시, 사용자 선택 필요

### 4.2 Plan Selector
- **입력**: User query
- **출력**: plan_ids (보험사별)
- **책임**:
  - 질의에서 성별/나이 추출
  - product_plan 테이블 기반 plan_id 매핑

### 4.3 Compare Axis Retrieval
- **입력**: coverage_codes, insurers, plan_ids
- **출력**: CompareAxisResult[]
- **책임**:
  - coverage_code + plan_id 기반 검색
  - is_synthetic = false 필터
  - doc_type 우선순위 적용
  - 보험사별 quota 균형

### 4.4 Amount Bridge
- **입력**: coverage_code, insurers, plan_ids, 금액 의도
- **출력**: AmountBridgeResult
- **책임**:
  - 금액 포함 chunk 우선 검색
  - is_synthetic 필터 없음 (synthetic 허용)
  - amount_extractor 결과 활용

### 4.5 Synthetic Chunk Generator
- **입력**: Mixed coverage chunk 후보
- **출력**: Synthetic chunks
- **책임**:
  - 담보별 라인 추출
  - coverage_alias 매칭만 허용
  - payment/count-context 필터
  - meta 정규화 (β-2 기준)

---

## 5. Synthetic Chunk의 위치와 책임

### 5.1 생성 시점
- Ingestion 이후, 선택적 backfill
- Mixed coverage chunk 식별 시

### 5.2 저장 위치
- chunk 테이블 (일반 chunk와 동일)
- meta.is_synthetic = true 로 구분

### 5.3 사용 범위
- ✅ Amount Bridge 전용
  - 금액 의도 + SAFE_RESOLVED 조건
  - get_amount_bearing_evidence()
- ❌ Compare Axis
  - get_compare_axis() 에서 제외
- ❌ Policy Axis
  - get_policy_axis() 에서 제외
- ❌ Coverage 추천
  - recommend_coverage_codes() 에서 제외

### 5.4 필터 규칙
```sql
-- Compare / Policy / 추천 경로
WHERE COALESCE((meta->>'is_synthetic')::boolean, false) = false

-- Amount Bridge 경로
-- (필터 없음 - synthetic 허용)
```

---

## 6. 확정된 정책

### 6.1 신정원 통일 코드 원칙
- coverage_code는 신정원 coverage_standard 기준
- coverage_alias로만 자동 매핑
- coverage_standard는 report-only

### 6.2 Domain 강제 원칙
- 질의 domain → 대표 담보는 해당 domain만
- 다른 domain 담보는 제외

### 6.3 메인 담보 우선
- 동일 domain 내 메인 담보 우선
- 파생 담보는 연관으로만

### 6.4 문서 우선순위
- 약관 > 사업방법서 > 상품요약서 > 가입설계서

---

## 7. 다음 단계

**STEP 2: DB 설계**
- 모든 테이블 정의
- 신정원 기준 coverage 테이블 중심
- synthetic meta 구조 명시
- ERD 제공

참조 파일: `docs/db_schema.md`
