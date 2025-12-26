# STEP NEXT-4: Compare View Model Schema
## UI 출력 전용 ViewModel JSON 계약

> **Constitutional Document**: This schema is governed by CLAUDE.md and STEP_NEXT3_UI_LAYOUT.md.
> **All content must be fact-only, no inference, no recommendation.**

---

## 0. Document Purpose

This document defines the **ViewModel JSON Schema** for the insurance comparison UI.

**ViewModel = Presentation Layer Contract:**
- Backend generates JSON matching this schema
- Frontend renders JSON without processing logic
- Schema enforces constitutional compliance (fact-only, no recommendation)

---

## 1. Constitutional Principles (Enforced by Schema)

### Absolute Rules
1. **Fact-only**: All values must be backed by evidence (document/page/excerpt)
2. **No Recommendation / No Inference**: No comparative judgment, no advice
3. **Presentation Only**: Schema is ViewModel, contains no business logic
4. **Canonical Coverage Rule**: Internal coverage_code must align with Shinjungwon unified codes (not exposed in UI)

### Prohibited in Schema/Examples
- ❌ Judgment fields ("better", "recommended", "superior")
- ❌ Comparative phrases ("same as", "no difference")
- ❌ Opinion sections ("summary opinion", "conclusion")
- ❌ Ranking/scoring fields

---

## 2. ViewModel Structure (Fixed 3-Block + Debug)

The ViewModel represents exactly **3 Blocks** from STEP NEXT-3:

```
┌─────────────────────────────────────────────────────────┐
│ header (BLOCK 0: User Query)                           │
├─────────────────────────────────────────────────────────┤
│ snapshot (BLOCK 1: Coverage Snapshot)                  │
├─────────────────────────────────────────────────────────┤
│ fact_table (BLOCK 2: Fact Table)                       │
├─────────────────────────────────────────────────────────┤
│ evidence_panels (BLOCK 3: Evidence Panels)             │
├─────────────────────────────────────────────────────────┤
│ debug (Non-UI: Reproducibility/Debugging)              │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Top-Level Schema

### Required Fields
- `schema_version`: string (e.g., "next4.v1")
- `generated_at`: ISO 8601 datetime string
- `header`: object (BLOCK 0)
- `snapshot`: object (BLOCK 1)
- `fact_table`: object (BLOCK 2)
- `evidence_panels`: array (BLOCK 3, can be empty)

### Optional Fields
- `debug`: object (non-UI, reproducibility only)

---

## 4. BLOCK 0: header

### Purpose
Display user's original question exactly as asked.

### Schema
```json
{
  "type": "object",
  "required": ["user_query"],
  "properties": {
    "user_query": {
      "type": "string",
      "description": "Original user question (1 line)",
      "minLength": 1
    },
    "normalized_query": {
      "type": "string",
      "description": "Cleaned query (whitespace normalization only, NO semantic change)"
    }
  }
}
```

### Prohibited
- ❌ Rephrasing user query
- ❌ Adding clarifications/interpretations
- ❌ Exposing internal processing (coverage_code, etc.)

---

## 5. BLOCK 1: snapshot

### Purpose
Fact-only summary of comparison scope.

### Schema
```json
{
  "type": "object",
  "required": ["comparison_basis", "insurers"],
  "properties": {
    "comparison_basis": {
      "type": "string",
      "description": "Normalized coverage name (canonical)"
    },
    "insurers": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["insurer", "status"],
        "properties": {
          "insurer": {
            "type": "string",
            "enum": ["SAMSUNG", "HANWHA", "LOTTE", "MERITZ", "KB", "HYUNDAI", "HEUNGKUK", "DB"]
          },
          "headline_amount": {
            "type": ["object", "null"],
            "properties": {
              "amount_value": {"type": "number"},
              "amount_unit": {"type": "string", "enum": ["만원"]},
              "display_text": {"type": "string"},
              "evidence_ref_id": {"type": "string"}
            }
          },
          "status": {
            "type": "string",
            "enum": ["OK", "MISSING_EVIDENCE", "UNMAPPED", "AMBIGUOUS", "OUT_OF_UNIVERSE"]
          }
        }
      }
    }
  }
}
```

### Prohibited Fields
- ❌ `comparison_judgment` (e.g., "same", "different")
- ❌ `recommendation`
- ❌ Any comparative/evaluative field

---

## 6. BLOCK 2: fact_table

### Purpose
Tabular display of coverage facts per insurer.

### Schema
```json
{
  "type": "object",
  "required": ["columns", "rows"],
  "properties": {
    "columns": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Fixed column headers",
      "const": ["보험사", "담보명(정규화)", "보장금액", "지급 조건 요약", "보험기간", "비고"]
    },
    "rows": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["insurer", "coverage_title_normalized", "row_status"],
        "properties": {
          "insurer": {
            "type": "string",
            "enum": ["SAMSUNG", "HANWHA", "LOTTE", "MERITZ", "KB", "HYUNDAI", "HEUNGKUK", "DB"]
          },
          "coverage_title_normalized": {
            "type": "string",
            "description": "Canonical coverage name from coverage_standard"
          },
          "benefit_amount": {
            "type": ["object", "null"],
            "properties": {
              "amount_value": {"type": "number"},
              "amount_unit": {"type": "string", "enum": ["만원"]},
              "display_text": {"type": "string"},
              "evidence_ref_id": {"type": "string"}
            }
          },
          "payout_conditions": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["slot_key", "value_text"],
              "properties": {
                "slot_key": {
                  "type": "string",
                  "enum": [
                    "waiting_period",
                    "payment_frequency",
                    "diagnosis_definition",
                    "method_condition",
                    "exclusion_scope",
                    "payout_limit",
                    "disease_scope"
                  ]
                },
                "value_text": {
                  "type": "string",
                  "description": "Slot value as-is from evidence (NO rewriting)"
                },
                "evidence_ref_id": {"type": "string"}
              }
            }
          },
          "term_text": {
            "type": ["string", "null"],
            "description": "Insurance period (e.g., '80세 만기')"
          },
          "note_text": {
            "type": ["string", "null"],
            "description": "Remarks (mapping status, evidence gaps)"
          },
          "row_status": {
            "type": "string",
            "enum": ["OK", "MISSING_EVIDENCE", "UNMAPPED", "AMBIGUOUS", "OUT_OF_UNIVERSE"]
          }
        }
      }
    }
  }
}
```

### Slot-Based Conditions (Deterministic Only)
- **waiting_period**: "90일", "없음"
- **payment_frequency**: "최초 1회", "1년 1회 (5회 한도)"
- **diagnosis_definition**: Disease code range or medical definition
- **method_condition**: "로봇수술 포함", "수술 방법 불문"
- **exclusion_scope**: "유사암, 갑상선암, 경계성종양, 제자리암"
- **payout_limit**: "1회 한도", "연간 5회"
- **disease_scope**: KCD-7 code range (e.g., "C00-C97")

**NO sentence rewriting**: All values must be direct quotes or deterministic extractions.

---

## 7. BLOCK 3: evidence_panels

### Purpose
Provide document evidence per insurer (collapsible accordion).

### Schema
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "insurer", "doc_type", "excerpt"],
    "properties": {
      "id": {
        "type": "string",
        "description": "Unique evidence ID (for ref_id linking)"
      },
      "insurer": {
        "type": "string",
        "enum": ["SAMSUNG", "HANWHA", "LOTTE", "MERITZ", "KB", "HYUNDAI", "HEUNGKUK", "DB"]
      },
      "doc_type": {
        "type": "string",
        "enum": ["가입설계서", "약관", "상품요약서", "사업방법서"]
      },
      "doc_title": {
        "type": "string",
        "description": "Document title (optional)"
      },
      "page": {
        "type": ["string", "number"],
        "description": "Page number (e.g., 'p.3', 3)"
      },
      "excerpt": {
        "type": "string",
        "minLength": 25,
        "maxLength": 400,
        "description": "Original text excerpt (NO rewriting, NO summarization)"
      },
      "bbox": {
        "type": "object",
        "description": "Optional PDF bounding box",
        "properties": {
          "x": {"type": "number"},
          "y": {"type": "number"},
          "width": {"type": "number"},
          "height": {"type": "number"}
        }
      },
      "source_meta": {
        "type": "object",
        "description": "Optional metadata (filename, hash, etc.)"
      }
    }
  }
}
```

### Absolute Prohibitions
- ❌ Rewriting original text
- ❌ Semantic summarization
- ❌ Adding interpretation sentences
- ❌ Combining multiple spans into narrative

---

## 8. debug (Optional, Non-UI)

### Purpose
Reproducibility and internal audit trail (NOT displayed in UI).

### Schema
```json
{
  "type": "object",
  "properties": {
    "resolved_coverage_codes": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Shinjungwon unified codes resolved internally"
    },
    "retrieval": {
      "type": "object",
      "description": "Retrieval parameters (topk, strategy, doc_priority)"
    },
    "warnings": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Non-fatal warnings (e.g., 'AMBIGUOUS mapping detected')"
    },
    "execution_time_ms": {
      "type": "number",
      "description": "Backend processing time"
    }
  }
}
```

### Usage
- Frontend MUST NOT display `debug` in UI
- Used for: logging, reproducibility, performance monitoring

---

## 9. Enum Definitions

### Insurer Codes (Canonical)
```
SAMSUNG, HANWHA, LOTTE, MERITZ, KB, HYUNDAI, HEUNGKUK, DB
```

### Status Codes
- **OK**: Normal display (all data available)
- **MISSING_EVIDENCE**: Data incomplete, evidence gaps exist
- **UNMAPPED**: Coverage exists in proposal but not mapped to canonical code
- **AMBIGUOUS**: Multiple canonical code candidates, manual resolution needed
- **OUT_OF_UNIVERSE**: Coverage not in proposal (Universe Lock violation)

### Document Types
```
가입설계서, 약관, 상품요약서, 사업방법서
```

### Slot Keys
```
waiting_period, payment_frequency, diagnosis_definition, method_condition,
exclusion_scope, payout_limit, disease_scope
```

---

## 10. Special Comparison Cases

### Case 1: 경계성종양/제자리암 (Definition-based)
When comparing disease definitions (not amounts), use `payout_conditions` with:
- `slot_key`: "disease_scope"
- `value_text`: KCD-7 code range (e.g., "D37-D48")

### Case 2: 다빈치/로봇 수술비 (Method-based)
When comparing surgical methods (not standalone coverage), use:
- `slot_key`: "method_condition"
- `value_text`: "로봇수술 포함", "다빈치수술 포함", "수술 방법 불문"

---

## 11. Forbidden Phrases (Hard Ban)

The following expressions are **absolutely prohibited** in all ViewModel fields:

### Judgment/Recommendation
- ❌ "더 좋다", "유리하다", "불리하다"
- ❌ "추천", "권장", "선택하세요"
- ❌ "우수", "뛰어남", "최선"

### Comparative Evaluation
- ❌ "동일함", "차이 없음"
- ❌ "A사가 B사보다..."
- ❌ "종합적으로 볼 때..."
- ❌ "결론적으로..."

### Inference/Opinion
- ❌ "사실상 같은 담보"
- ❌ "유사한 담보"
- ❌ "일반적으로", "보통은"

---

## 12. Version Strategy

### Schema Version Format
- `next4.v1`: Initial version (STEP NEXT-4)
- `next4.v2`: Breaking changes (add/remove required fields)
- `next4.v1.1`: Non-breaking changes (add optional fields)

### Backwards Compatibility
- Frontend MUST handle unknown optional fields gracefully
- Backend MUST NOT remove required fields without major version bump

---

## 13. Validation Requirements

### Schema Validation
All ViewModel JSON instances MUST:
1. Pass JSON Schema Draft 2020-12 validation
2. Contain NO forbidden phrases (hard ban list)
3. Have all `evidence_ref_id` resolvable to `evidence_panels[].id`
4. Use only canonical insurer codes
5. Use only enum-defined status/doc_type/slot_key values

### Test Coverage
- ✅ 4+ example JSONs validate against schema
- ✅ Forbidden phrase detection test (fails if hard ban found)
- ✅ Reference integrity test (`evidence_ref_id` → `evidence_panels[].id`)

---

## 14. Frontend Rendering Contract

### Frontend MUST
- Render blocks in fixed order: header → snapshot → fact_table → evidence_panels
- NOT display `debug` section in UI
- NOT process/interpret data (display only)
- Handle `null` values gracefully (show empty/placeholder)

### Frontend MUST NOT
- Reorder table columns
- Add comparative judgments
- Perform calculations (except formatting)
- Make recommendations

---

## 15. Example Scenarios (See compare_view_model.examples.json)

Minimum 4 examples required:

1. **Standard Cancer Diagnosis** (암 진단비)
   - 2 insurers, normal amounts, slot-based conditions

2. **Borderline Tumor** (경계성종양)
   - Definition-based comparison, disease_scope slot

3. **Robotic Surgery** (다빈치 수술비)
   - Method-based comparison, method_condition slot

4. **UNMAPPED Coverage** (Edge Case)
   - Missing canonical code, status="UNMAPPED", note_text with tag

---

## 16. Constitutional Compliance Matrix

| Principle | Schema Enforcement |
|-----------|-------------------|
| Fact-only | All values require evidence_ref_id |
| No Recommendation | Forbidden phrases validation |
| Presentation Only | No logic fields (score/rank/judgment) |
| Canonical Coverage | coverage_title_normalized from coverage_standard |
| Coverage Universe Lock | OUT_OF_UNIVERSE status for non-proposal coverages |
| Evidence Rule | evidence_panels required, excerpt minLength=25 |
| Deterministic Output | Same input → same JSON structure |

---

## 17. Schema File Location

**Canonical Schema File:**
```
docs/ui/compare_view_model.schema.json
```

**JSON Schema Draft:** 2020-12

**Validation Tool:** `jsonschema` (Python library)

---

## 18. Future Extensions (Non-Breaking)

Potential optional additions (major version unchanged):
- `pagination`: For large result sets
- `filters_applied`: User-selected filters (if any)
- `related_queries`: Suggested refinements (fact-based only)

**All extensions MUST maintain constitutional compliance.**

---

## 19. DoD (Definition of Done)

- ✅ `compare_view_model.schema.json` exists (Draft 2020-12)
- ✅ 4+ examples validate against schema
- ✅ Forbidden phrase test implemented
- ✅ Reference integrity test implemented
- ✅ `debug` excluded from UI rendering contract
- ✅ STATUS.md updated with NEXT-4 completion

---

**Document Version**: 1.0.0
**Date**: 2025-12-26
**Status**: Constitutional (Immutable without Amendment)
**Schema Version**: next4.v1
