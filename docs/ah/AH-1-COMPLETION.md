# STEP NEXT-AH-1: Excel Alias 강제 적용 완료

**Commit**: `b69b425`
**Date**: 2025-12-27
**Status**: ✅ ALL PASS

---

## 목표 달성

### Constitutional Goal
> "담보명 매핑 Excel은 '참고 자료'가 아니라 Query 해석과 Universe Recall에 강제 적용되는 SSOT다."

✅ **달성**: 모든 Query는 Excel Alias Index를 거쳐 Canonical Code로 변환 후 Universe를 조회한다.

---

## 구현 내용

### 1. Alias Normalizer
**파일**: `apps/api/app/ah/alias_normalizer.py`

**기능**:
- Query/Raw 담보명 → 정규화된 매칭 키 생성
- Deterministic 규칙 기반 (LLM 금지)
- 괄호/공백/버전 표기 제거
- 조건절(유사암 제외, 1년50% 등) 메타데이터 추출

**핵심 원칙**:
- High recall priority (over-match 허용, under-match 금지)
- Repeatable normalization (Query/Excel/Universe 동일 규칙)

---

### 2. Alias Index
**파일**: `apps/api/app/ah/alias_index.py`

**기능**:
- Excel → (normalized_alias → Set[canonical_coverage_code]) 인덱스 구축
- Cancer Guardrail: 암 관련 Query → 암군 전체 확장
- Singleton instance (lazy loading)

**통계**:
- Total Aliases: 118
- Total Canonical Codes: 28
- Cancer Canonical Codes: 12

**암 Canonical Codes 예시**:
- A4200_1 (암진단비(유사암제외))
- A4209 (고액암진단비)
- A4210 (유사암진단비)
- A4299_1 (재진단암진단비)
- A5200 (암수술비(유사암제외))
- A5298_001 (유사암수술비)
- A6200 (암직접치료입원일당)
- A9617_1 (항암방사선약물치료비)
- A9619_1 (표적항암약물허가치료비)
- A9620_1 (카티(CAR-T)항암약물허가치료비)
- A9630_1 (다빈치로봇암수술비)
- A9640_1 (...)

---

### 3. Universe Recaller
**파일**: `apps/api/app/ah/universe_recall.py`

**기능**:
- Query → Alias Index → Canonical Codes → Universe Recall
- Insurer filter 지원
- Cancer Guardrail 적용/비적용 선택 가능

**금지 사항**:
- ❌ Direct DB raw name match
- ❌ LLM-based query interpretation
- ❌ Bypassing alias index

---

## 검증 결과

### Scenario A: "일반암진단비" → 8 insurers ✅
```
Query: 일반암진단비
Canonical Codes Resolved: 12 codes (A4200_1, A4209, A4210, ...)
Recall Count: 133
Insurers Covered: 8/8
- SAMSUNG ✅ (21 coverages including "암 진단비(유사암 제외)")
- MERITZ ✅
- KB ✅
- DB ✅
- HANWHA ✅
- LOTTE ✅
- HYUNDAI ✅
- HEUNGKUK ✅
```

### Scenario B: "암진단비" → Full Cancer Group ✅
```
Query: 암진단비
Canonical Codes Resolved: 12 codes
Recall Count: 133
유사암 coverages: 44
제자리암 coverages: 2
```

### Scenario C: Unmapped Query Handling ✅
```
Query: unmapped_query_xyz_12345
Canonical Codes: []
Recall Count: 0
Unmapped: True
(No crash, no inference)
```

---

## Constitutional Guarantees

### 1. Excel SSOT
✅ **모든 Query는 Excel Alias Index를 거친다**
- Direct DB match 절대 금지
- LLM 추론 절대 금지

### 2. Recall Priority
✅ **과잉 리콜 허용, 누락 금지**
- SAMSUNG "암 진단비" → "일반암진단비" Query에 포함
- 8개 보험사 전부 Universe 진입

### 3. Cancer Guardrail
✅ **암 Query → 암군 전체 확장**
- "암진단비" / "일반암진단비" / "암 진단비" → 동일 처리
- 유사암/제자리암/경계성종양 전부 포함

### 4. Deterministic Only
✅ **규칙 기반 정규화만 허용**
- Regex pattern matching
- Table/YAML lookup
- No LLM inference

---

## 핵심 성과

### Before (문제)
- "일반암진단비" Query → SAMSUNG 누락 (표현 차이)
- MERITZ/KB/DB/HYUNDAI/HEUNGKUK도 누락 가능성
- 보험사별 표현 차이로 인한 리콜 불안정

### After (해결)
- "일반암진단비" Query → 8/8 insurers 전부 포함
- SAMSUNG "암 진단비" 확실히 포함
- 표현 차이 무관하게 안정적 리콜

---

## 다음 단계 제안

### Option A: API Integration
- `/compare` endpoint에 AH-1 적용
- Query parsing layer 교체

### Option B: DB Universe Table Update
- proposal_coverage_universe에 canonical_coverage_code 컬럼 추가
- Excel alias 기반 역매핑 수행

### Option C: Advanced Recall Strategy
- Precision 개선 (현재 Recall 우선)
- Slot-level matching (disease_scope, amount 등)

---

## 테스트 재현

```bash
python apps/api/scripts/ah_test_recall.py
```

**예상 결과**:
```
Scenario A: ✅ PASS
Scenario B: ✅ PASS
Scenario C: ✅ PASS
Overall: ✅ ALL PASS
```

---

## 참고 문서

- `docs/ah/coverage_alias_audit.md`: 8개 보험사 암 담보 전수 감사 (AH-0)
- `data/담보명mapping자료.xlsx`: Canonical alias SSOT
- `CLAUDE.md`: Constitutional rules (Article I: Coverage Universe Lock)

---

## Decision Log Entry

**Date**: 2025-12-27
**Section**: Query Interpretation
**Before**: Query → DB raw name direct match
**After**: Query → Excel Alias Index → Canonical Code → Universe Recall (AH-1)
**Reason**: SAMSUNG "암 진단비" 등 표현 차이로 인한 리콜 누락 방지, 8개 보험사 암 담보 전수 감사 완료

---

**End of AH-1**
