# STEP 8: Policy Scope Pipeline Expansion (Multi-Insurer)

**Date:** 2025-12-24
**Base:** STEP 7 Complete (feature/step7-universe-refactor-policy-scope-v1)
**Purpose:** Generalize Policy Scope Pipeline to support 3+ insurers with stable multi-party comparison

---

## 0. Preconditions (Constitutional)

- ✅ STEP 7 complete (Universe Lock + Policy Scope Pipeline v1 MVP)
- ✅ Samsung 유사암 definition extraction working
- ✅ Evidence-based pipeline validated
- ✅ KCD-7 FK constraints enforced

**STEP 8 builds on STEP 7 foundation (additive only, no redesign)**

### ⚠️ Document Hierarchy (Constitutional Requirement)

**가입설계서 중심 비교 Universe (SSOT):**

1. **가입설계서 (Proposal)** → `proposal_coverage_universe` (비교 대상 SSOT)
   - **비교 가능 담보는 가입설계서에 있는 담보만**
   - Universe Lock의 절대 기준
   - 약관/사업방법서는 Universe를 **확장하지 않음**

2. **상품요약서 / 사업방법서 / 약관** → Evidence Enrichment only
   - `disease_scope_norm` 채우기 (약관 정의 근거)
   - `coverage_condition` 보강
   - `exclusion_reason` 명시
   - **가입설계서 담보를 "해석"할 뿐, "선정"하지 않음**

**STEP 8 Policy Parsers Role:**
- 약관에서 disease group definition 추출
- **기존 Universe 담보의 슬롯을 채우는 하위 계층 파이프라인**
- Universe에 없는 담보는 처리 대상 아님 (out_of_universe)

---

## 1. Problem Statement

### Current State (STEP 7)
- Single insurer (Samsung) hardcoded
- Single coverage (유사암) hardcoded
- Single parser method (`parse_samsung_similar_cancer`)
- Cannot support multi-insurer comparison

### STEP 8 Goal
- Support **3+ insurers** with different disease group definitions
- Stable **multi-party comparison** logic (pairwise → unified state)
- **Explainable reasons** for comparable/non-comparable decisions
- **NO scoring, ranking, or recommendation**

---

## 2. Architecture Design

### 2.1 Policy Scope Generalization Strategy

**Registry Pattern** - Decouple insurer-specific logic from pipeline core

```
src/policy_scope/
├── __init__.py
├── base_parser.py          # Abstract base class (NEW)
├── registry.py             # Insurer → Parser mapping (NEW)
├── pipeline.py             # Existing (unchanged)
├── parsers/
│   ├── __init__.py
│   ├── samsung.py          # SamsungPolicyParser (migrated from parser.py)
│   ├── meritz.py           # MeritzPolicyParser (partial/stub)
│   └── db.py               # DBPolicyParser (stub)
└── comparison/
    ├── __init__.py
    ├── overlap.py          # Multi-party overlap detection (NEW)
    └── explainer.py        # Comparison reason generation (NEW)
```

### 2.2 Base Parser Interface (Abstract)

```python
class BasePolicyParser(ABC):
    """
    Abstract base class for insurer-specific policy parsers

    Constitutional requirements:
    - Deterministic extraction only (regex/rules)
    - NO LLM/inference
    - Evidence required (basis_doc_id, basis_page, basis_span)
    """

    @abstractmethod
    def extract_disease_group_definition(
        self,
        policy_text: str,
        group_concept: str,  # e.g., "유사암", "소액암"
        document_id: str,
        page_number: int
    ) -> Optional[DiseaseGroupDefinition]:
        """
        Extract disease group definition from policy document

        Returns:
            DiseaseGroupDefinition with evidence, or None if not found
        """
        pass

    @abstractmethod
    def extract_coverage_disease_scope(
        self,
        policy_text: str,
        coverage_name: str,
        document_id: str,
        page_number: int
    ) -> Optional[CoverageScopeDefinition]:
        """
        Extract disease scope for specific coverage

        Returns:
            CoverageScopeDefinition with evidence, or None if not found
        """
        pass

    @property
    @abstractmethod
    def insurer_code(self) -> str:
        """Return insurer code (e.g., 'SAMSUNG')"""
        pass

    @property
    @abstractmethod
    def supported_concepts(self) -> List[str]:
        """Return list of supported disease concepts (e.g., ['유사암', '소액암'])"""
        pass
```

### 2.3 Registry Design

```python
class PolicyParserRegistry:
    """
    Central registry for insurer-specific policy parsers

    Constitutional guarantee:
    - Only registered insurers can be processed
    - Unregistered insurers → NOT_IMPLEMENTED_YET error
    """

    _parsers: Dict[str, BasePolicyParser] = {}

    @classmethod
    def register(cls, parser: BasePolicyParser) -> None:
        """Register a parser for an insurer"""
        cls._parsers[parser.insurer_code] = parser

    @classmethod
    def get_parser(cls, insurer_code: str) -> BasePolicyParser:
        """Get parser for insurer, raise if not registered"""
        if insurer_code not in cls._parsers:
            raise NotImplementedError(
                f"Policy parser for {insurer_code} not yet implemented. "
                f"Available: {list(cls._parsers.keys())}"
            )
        return cls._parsers[insurer_code]

    @classmethod
    def list_supported_insurers(cls) -> List[str]:
        """List all registered insurers"""
        return list(cls._parsers.keys())
```

### 2.4 Insurer-Specific Parsers

**Samsung Parser** (full implementation)
- Migrate existing `parse_samsung_similar_cancer` logic
- Implement `BasePolicyParser` interface
- Support: 유사암, 소액암 (if data available)

**Meritz Parser** (partial/stub)
- Implement basic structure
- Support: 유사암 (simplified pattern)
- Can return NOT_IMPLEMENTED for complex cases

**DB Parser** (stub)
- Implement interface only
- All methods return None or raise NotImplementedError
- Clearly marked as "STUB - Not Implemented Yet"

---

## 3. Multi-Party Comparison Logic

### 3.1 Group Overlap States (3+ Insurers)

```python
class GroupOverlapState(Enum):
    FULL_MATCH = "full_match"              # All insurers have identical groups
    PARTIAL_OVERLAP = "partial_overlap"     # Some insurers have intersection
    NO_OVERLAP = "no_overlap"               # No common intersection across all
    UNKNOWN = "unknown"                     # One or more disease_scope_norm is NULL
```

### 3.2 Pairwise Overlap Detection

For N insurers, compute pairwise overlaps:
1. For each pair (insurer_A, insurer_B):
   - Compare include_group_id members
   - Compare exclude_group_id members
   - Determine overlap state

2. Aggregate pairwise results:
   - If all pairs = FULL_MATCH → FULL_MATCH
   - If any pair = NO_OVERLAP → NO_OVERLAP
   - If any pair = UNKNOWN → UNKNOWN
   - Otherwise → PARTIAL_OVERLAP

### 3.3 Comparison State Mapping

| Group Overlap | Comparison State | Reason Code |
|--------------|------------------|-------------|
| FULL_MATCH | `comparable` | `disease_scope_identical` |
| PARTIAL_OVERLAP | `comparable_with_gaps` | `disease_scope_partial_overlap` |
| NO_OVERLAP | `non_comparable` | `disease_scope_multi_insurer_conflict` |
| UNKNOWN | `comparable_with_gaps` | `disease_scope_policy_required` |

---

## 4. Explainable Comparison Reasons

### 4.1 Reason Schema

```python
@dataclass
class ComparisonReason:
    """
    Explainable reason for comparison state

    Constitutional requirement:
    - NO value judgments (best/worst)
    - NO recommendations
    - Only factual differences with evidence
    """
    comparison_state: str  # comparable, comparable_with_gaps, non_comparable
    reason_code: str       # disease_scope_identical, disease_scope_multi_insurer_conflict, etc.
    explanation: str       # Human-readable explanation (Korean)
    details: List[InsurerGroupDetail]

@dataclass
class InsurerGroupDetail:
    """Evidence for insurer-specific disease group"""
    insurer: str
    group_id: Optional[str]
    group_label: Optional[str]
    basis_doc_id: Optional[str]
    basis_page: Optional[int]
    member_count: Optional[int]  # Number of KCD codes in group
```

### 4.2 Explanation Examples

**FULL_MATCH:**
```
"삼성, 메리츠, DB 모두 동일한 유사암 정의를 사용합니다 (C73 갑상선암, C44 피부암)."
```

**PARTIAL_OVERLAP:**
```
"삼성과 메리츠는 유사암 정의에 교집합이 있으나 (C73), DB의 정의는 상이합니다. 약관 확인이 필요합니다."
```

**NO_OVERLAP:**
```
"삼성, 메리츠, DB의 유사암 정의가 상호 교집합을 가지지 않아 비교가 불가능합니다."
```

**UNKNOWN:**
```
"메리츠의 유사암 정의가 약관에서 추출되지 않았습니다. 약관 확인이 필요합니다."
```

### 4.3 Prohibited Phrases

- ❌ "가장 넓은 보장"
- ❌ "가장 유리함"
- ❌ "추천합니다"
- ❌ "더 나은 상품"
- ❌ Any comparative value judgment

---

## 5. Implementation Plan

### 5.1 Phase A: Structure Refactoring
1. Create `base_parser.py` (abstract interface)
2. Create `registry.py` (parser registry)
3. Migrate Samsung parser to `parsers/samsung.py`
4. Register Samsung parser in registry

### 5.2 Phase B: Multi-Insurer Support
1. Implement Meritz parser (partial)
2. Implement DB parser (stub)
3. Register Meritz and DB parsers
4. Verify 3+ insurers supported

### 5.3 Phase C: Multi-Party Comparison
1. Implement `comparison/overlap.py` (pairwise → unified)
2. Implement `comparison/explainer.py` (reason generation)
3. Update pipeline to use multi-party logic

### 5.4 Phase D: Testing
1. Add multi-insurer comparison tests (3+ insurers)
2. Test all overlap states (FULL_MATCH, PARTIAL_OVERLAP, NO_OVERLAP, UNKNOWN)
3. Validate explanation generation
4. Verify evidence included in all cases

---

## 6. Testing Requirements (Mandatory)

### 6.1 Test Scenarios

**Scenario 1: FULL_MATCH (3 insurers)**
- Samsung, Meritz, DB all have identical 유사암 definition
- Expected: `comparable`, reason_code = `disease_scope_identical`

**Scenario 2: PARTIAL_OVERLAP (3 insurers)**
- Samsung and Meritz share C73, DB has C44 only
- Expected: `comparable_with_gaps`, reason_code = `disease_scope_partial_overlap`

**Scenario 3: NO_OVERLAP (3 insurers)**
- Samsung (C73), Meritz (C44), DB (C00) - no common codes
- Expected: `non_comparable`, reason_code = `disease_scope_multi_insurer_conflict`

**Scenario 4: UNKNOWN (3 insurers)**
- Samsung and Meritz defined, DB has disease_scope_norm = NULL
- Expected: `comparable_with_gaps`, reason_code = `disease_scope_policy_required`

### 6.2 Test Validation Checklist

For each test:
- ✅ comparison_state matches expected
- ✅ reason_code matches expected
- ✅ explanation is human-readable Korean
- ✅ details include all 3 insurers
- ✅ Evidence (basis_doc_id, page) included where available
- ✅ NO prohibited phrases in explanation

---

## 7. Database Changes

### 7.1 Allowed Changes

**New Enum Values** (reason_code):
```sql
ALTER TYPE comparison_reason_code ADD VALUE IF NOT EXISTS 'disease_scope_identical';
ALTER TYPE comparison_reason_code ADD VALUE IF NOT EXISTS 'disease_scope_partial_overlap';
ALTER TYPE comparison_reason_code ADD VALUE IF NOT EXISTS 'disease_scope_multi_insurer_conflict';
ALTER TYPE comparison_reason_code ADD VALUE IF NOT EXISTS 'disease_scope_policy_required';
```

**Helper View** (optional):
```sql
CREATE VIEW v_multi_insurer_disease_scope AS
SELECT
  canonical_coverage_code,
  insurer,
  include_group_id,
  exclude_group_id,
  source_doc_id,
  source_page
FROM coverage_disease_scope;
```

### 7.2 Prohibited Changes

- ❌ proposal_coverage_universe schema change
- ❌ proposal_coverage_mapped schema change
- ❌ disease_code_group schema change
- ❌ Deleting existing data

---

## 8. Constitutional Compliance

### 8.1 Principles Enforced

- ✅ Deterministic extraction only (NO LLM)
- ✅ Evidence required at every step
- ✅ KCD-7 FK validation against disease_code_master
- ✅ insurer=NULL restricted to medical/KCD classification
- ✅ **Universe Lock (가입설계서 = 비교 대상 SSOT)**
- ✅ **약관 = Evidence Enrichment only (Universe 확장 금지)**
- ✅ Excel mapping single source (coverage codes)

### 8.2 New Prohibitions

- ❌ Unregistered insurer processing (must raise NotImplementedError)
- ❌ Value judgments in explanations (best/worst/recommended)
- ❌ Multi-state comparison results (must return single unified state)

---

## 9. Definition of Done

- ✅ 3+ insurers registered (Samsung full, Meritz partial, DB stub)
- ✅ Base parser interface defined and implemented by all parsers
- ✅ Registry pattern working (can add insurer by file addition only)
- ✅ Multi-party overlap detection (pairwise → unified state)
- ✅ Explainable reasons generated with evidence
- ✅ 4+ test scenarios covering all overlap states
- ✅ NO prohibited phrases in explanations
- ✅ STATUS.md updated
- ✅ All commits pushed to GitHub

---

## 10. Success Criteria

**Structural Stability:**
- Adding 4th insurer requires only 1 new file + registry call
- No changes to pipeline.py core logic
- No changes to STEP 7 tables

**Multi-Party Robustness:**
- 3-way comparison returns single state (not 3 states)
- Pairwise aggregation logic deterministic
- Evidence preserved from all insurers

**Explainability:**
- Every comparison state has human-readable reason
- Reason includes insurer-specific evidence
- NO value judgments or recommendations

---

## 11. Rollback Plan

If STEP 8 fails:
- Revert to STEP 7 branch: `feature/step7-universe-refactor-policy-scope-v1`
- STEP 7 remains functional
- No data corruption (additive changes only)

---

## References

- STEP 7 Complete: commits 917b595, 5f4de04, 64f5159, d69c207
- Constitution v1.0 + Amendment v1.0.1
- CLAUDE.md (project constitution)
