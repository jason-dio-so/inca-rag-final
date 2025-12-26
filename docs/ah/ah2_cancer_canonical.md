# STEP NEXT-AH-2: Cancer Coverage Canonical Split & Evidence Alignment

**Status**: ✅ ALL PASS
**Date**: 2025-12-27

---

## Constitutional Declaration (Non-Negotiable)

> **"암진단비"는 하나의 담보가 아니다.**

가입설계서·약관·상품요약서·사업방법서·신정원 코드의 표현 차이는
**Alias 문제가 아니라 Canonical Split 문제**다.

---

## 4 Cancer Canonical Codes (Fixed)

| Code | Korean Name | Scope |
|------|-------------|-------|
| `CA_DIAG_GENERAL` | 일반암진단비 | 유사암/제자리암/경계성종양 제외 |
| `CA_DIAG_SIMILAR` | 유사암진단비 | 갑상선암, 기타피부암 등 |
| `CA_DIAG_IN_SITU` | 제자리암진단비 | 제자리암 (D0x) |
| `CA_DIAG_BORDERLINE` | 경계성종양진단비 | 경계성종양 (D3x, D4x) |

**Absolute Rule**:
- ❌ "암진단비" 단일 Canonical Code 사용 금지
- ✅ 반드시 4종 중 하나로 분류

---

## Evidence-Based Canonical Determination

### Priority Logic

1. **Policy Evidence (Constitutional)**
   - 약관 보장 정의 문단 분석
   - `includes_general`, `includes_similar`, `includes_in_situ`, `includes_borderline` 결정
   - Evidence 필수: `document_id`, `page`, `span_text`

2. **Heuristic (Backward Compatibility)**
   - Coverage name 기반 추론
   - Policy evidence 없을 때만 사용
   - `confidence='inferred'` 로 명시

### Heuristic Priority Rules

**Context-Aware Split**:
1. `유사암 진단비(제자리암)` → `CA_DIAG_IN_SITU` (specific wins)
2. `유사암 진단비(경계성종양)` → `CA_DIAG_BORDERLINE` (specific wins)
3. `유사암 진단비(갑상선암)` → `CA_DIAG_SIMILAR` (similar category)
4. `유사암 진단비` (no parentheses) → `CA_DIAG_SIMILAR` (general similar)
5. `암진단비(유사암제외)` → `CA_DIAG_GENERAL`
6. `제자리암` (alone) → `CA_DIAG_IN_SITU`
7. `경계성종양` (alone) → `CA_DIAG_BORDERLINE`

---

## Validation Results

### Scenario A: SAMSUNG vs MERITZ Cancer Coverage Split ✅

**SAMSUNG**:
- `암 진단비(유사암 제외)` → `CA_DIAG_GENERAL` ✅
- `유사암 진단비(갑상선암)` → `CA_DIAG_SIMILAR` ✅
- `유사암 진단비(제자리암)` → `CA_DIAG_IN_SITU` ✅
- `유사암 진단비(경계성종양)` → `CA_DIAG_BORDERLINE` ✅

**MERITZ**:
- `암진단비(유사암제외)` → `CA_DIAG_GENERAL` ✅
- `유사암진단비` → `CA_DIAG_SIMILAR` ✅

### Scenario B: 유사암 Coverage Canonical Mapping ✅

**Exclusion Coverages (`유사암제외`)**:
- 16 coverages → All mapped to `CA_DIAG_GENERAL` ✅

**Actual 유사암 Coverages**:
- 32 coverages → All mapped to cancer canonical (SIMILAR/IN_SITU/BORDERLINE) ✅
- No `CA_DIAG_GENERAL` in actual 유사암 coverages ✅

---

## Overall Split Statistics

**Total cancer coverages**: 128

**Split by method**:
- Heuristic: 128 (100%)
- Policy evidence: 0 (not yet implemented)

**Canonical distribution**:
- `CA_DIAG_GENERAL`: 33 coverages (25.8%)
- `CA_DIAG_SIMILAR`: 28 coverages (21.9%)
- `CA_DIAG_IN_SITU`: 3 coverages (2.3%)
- `CA_DIAG_BORDERLINE`: 3 coverages (2.3%)
- Unmapped: 61 coverages (47.7%) *

\* Unmapped = Non-diagnosis coverages (수술비, 입원일당, 항암치료비 etc.)

**Ambiguous**: 0 (all unambiguous) ✅

---

## Key Achievements

### 1. Constitutional Cancer Canonical Set
✅ 4종 Canonical Code 고정 (`CA_DIAG_GENERAL`, `CA_DIAG_SIMILAR`, `CA_DIAG_IN_SITU`, `CA_DIAG_BORDERLINE`)

### 2. Evidence-Based Determination Framework
✅ Policy evidence → Scope flags → Canonical code 결정 로직 구현
✅ Heuristic fallback with explicit `confidence='inferred'`

### 3. Context-Aware Split
✅ "유사암 진단비(제자리암)" → `CA_DIAG_IN_SITU` (specific wins over category)
✅ "유사암 진단비(갑상선암)" → `CA_DIAG_SIMILAR` (stays in category)

### 4. Structural Clarity
✅ SAMSUNG "암 진단비(유사암 제외)" 명확히 `CA_DIAG_GENERAL`로 귀속
✅ 유사암/제자리암/경계성종양 분리 확인

---

## Modules Implemented

### 1. `cancer_canonical.py`
- Constitutional cancer canonical code set (Enum)
- `CancerScopeEvidence` dataclass
- `get_canonical_code()` logic
- Legacy code mapping (backward compatibility)

### 2. `cancer_scope_detector.py`
- Deterministic policy text analysis (pattern matching)
- Heuristic coverage name analysis
- Evidence metadata (document_id, page, span_text)

### 3. `canonical_split_mapper.py`
- Coverage instance → Canonical code(s) mapping
- Split result tracking (`CoverageSplitResult`)
- Priority logic (policy > heuristic > legacy)
- Split report generation

### 4. `ah_test_cancer_split.py`
- Scenario A: SAMSUNG vs MERITZ split validation
- Scenario B: 유사암 mapping validation
- Overall split report generation

---

## Next Steps (Roadmap)

### Option A: Policy Evidence Integration
- Connect to `v2.coverage_evidence` table
- Extract policy text for cancer coverages
- Replace heuristic with policy-based determination

### Option B: Comparison Layer Integration
- Update `/compare` endpoint to use canonical codes
- Split comparison rows by canonical code
- Display separate rows for GENERAL vs SIMILAR vs IN_SITU vs BORDERLINE

### Option C: UI Visualization
- Show split coverages in comparison table
- Evidence panel for canonical determination
- Confidence indicator (policy_confirmed vs inferred)

---

## Constitutional Impact

### Before AH-2
- "암진단비" = single ambiguous concept
- SAMSUNG "암 진단비" vs MERITZ "암진단비(유사암제외)" → unclear comparison
- 유사암/제자리암/경계성종양 혼재

### After AH-2
- "암진단비" = 4 distinct canonical codes
- SAMSUNG "암 진단비(유사암 제외)" = `CA_DIAG_GENERAL` (clear)
- 유사암/제자리암/경계성종양 → separate rows in comparison

---

## Test Reproduction

```bash
python apps/api/scripts/ah_test_cancer_split.py
```

**Expected Output**:
```
Scenario A: ✅ PASS
Scenario B: ✅ PASS
Overall: ✅ ALL PASS
```

---

## References

- `apps/api/app/ah/cancer_canonical.py`: Constitutional code set
- `apps/api/app/ah/cancer_scope_detector.py`: Evidence-based detector
- `apps/api/app/ah/canonical_split_mapper.py`: Split mapper
- `docs/ah/coverage_alias_audit.md`: AH-0 Audit (128 cancer coverages)
- `CLAUDE.md`: Constitutional rules

---

**End of AH-2**
