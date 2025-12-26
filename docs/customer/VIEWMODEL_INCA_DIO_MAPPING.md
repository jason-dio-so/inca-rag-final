# ViewModel ↔ INCA DIO Requirements Mapping

**Purpose:** Map inca_dio.pdf examples 1-4 to existing ViewModel schema (STEP NEXT-4)

**Schema SSOT:** `docs/ui/compare_view_model.schema.json`

**Customer Requirements:** `docs/customer/INCA_DIO_REQUIREMENTS.md`

---

## Schema Compatibility Check

### Existing Schema Blocks (STEP NEXT-4)
1. `header` - User query (BLOCK 0)
2. `snapshot` - Coverage snapshot (BLOCK 1)
3. `fact_table` - Comparison table (BLOCK 2)
4. `evidence_panels` - Evidence accordion (BLOCK 3)
5. `debug` - Non-UI debugging info

### INCA DIO Requirements
1. **Example 1:** Premium sorting + ranking
2. **Example 2:** Condition difference detection
3. **Example 3:** Specific insurers + coverage comparison
4. **Example 4:** Disease-based coverage matrix (O/X table)

---

## Mapping Strategy

### Example 1: Premium Sorting
**Requirement:** "가장 저렴한 보험료 정렬순으로 4개만 비교"

**ViewModel Mapping:**
```json
{
  "header": {
    "user_query": "가장 저렴한 보험료 정렬순으로 4개만 비교해줘"
  },
  "fact_table": {
    "columns": ["순위", "보험사", "상품명", "총납입보험료_일반", "총납입보험료_무해지", "월납보험료_일반", "월납보험료_무해지"],
    "rows": [
      /* sorted by 총납입보험료_일반 ASC, limit 4 */
    ],
    "sort_metadata": {
      "sort_by": "총납입보험료_일반",
      "sort_order": "asc",
      "limit": 4
    }
  }
}
```

**Schema Amendment Needed:**
- ✅ `fact_table.sort_metadata` (optional field)
- ✅ `fact_table.visual_emphasis` (optional field for min/max highlighting)

---

### Example 2: Condition Difference
**Requirement:** "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"

**ViewModel Mapping:**
```json
{
  "header": {
    "user_query": "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
  },
  "snapshot": {
    "comparison_basis": "암직접입원비",
    "filter_criteria": {
      "slot_key": "payout_limit",
      "difference_detected": true
    }
  },
  "fact_table": {
    "rows": [
      {"구분": "보장한도", "A사": "1~120일", "B사": "1~180일", "C사": "1~180일", "highlight": ["A사"]}
    ]
  }
}
```

**Schema Amendment Needed:**
- ✅ `snapshot.filter_criteria` (optional)
- ✅ `fact_table.rows[].highlight` (optional array for cell emphasis)

---

### Example 3: Specific Insurers Comparison
**Requirement:** "삼성화재, 메리츠화재의 암진단비를 비교해줘"

**ViewModel Mapping:**
```json
{
  "header": {
    "user_query": "삼성화재, 메리츠화재의 암진단비를 비교해줘"
  },
  "snapshot": {
    "comparison_basis": "암진단비",
    "insurers": [
      {"insurer": "SAMSUNG", "status": "OK", ...},
      {"insurer": "MERITZ", "status": "OK", ...}
    ],
    "filter_criteria": {
      "insurer_filter": ["SAMSUNG", "MERITZ"]
    }
  }
}
```

**Schema Amendment Needed:**
- ✅ Already supported (insurer filtering via snapshot.insurers)

---

### Example 4: O/X Coverage Matrix
**Requirement:** "제자리암, 경계성종양 보장내용에 따라 A사, B사 상품 비교"

**ViewModel Mapping:**
```json
{
  "header": {
    "user_query": "제자리암, 경계성종양 보장내용에 따라 A사, B사 상품 비교해줘"
  },
  "snapshot": {
    "comparison_basis": "제자리암, 경계성종양 보장내용",
    "filter_criteria": {
      "disease_scope": ["제자리암", "경계성종양"],
      "insurer_filter": ["A사", "B사"]
    }
  },
  "fact_table": {
    "table_type": "ox_matrix",
    "columns": ["구분", "담보 항목", "A사", "B사"],
    "rows": [
      {"구분": "제자리암, 경계성종양", "담보 항목": "진단비", "A사": "O", "B사": "O"},
      {"구분": "제자리암, 경계성종양", "담보 항목": "수술비", "A사": "O", "B사": "O"},
      {"구분": "제자리암, 경계성종양", "담보 항목": "항암약물", "A사": "O", "B사": "O"},
      {"구분": "제자리암, 경계성종양", "담보 항목": "표적항암", "A사": "X", "B사": "O"},
      {"구분": "제자리암, 경계성종양", "담보 항목": "다빈치치료", "A사": "O", "B사": "X"}
    ]
  },
  "warnings": [
    {
      "type": "note",
      "message": "보장 여부는 약관 기준이며, 정확한 보장 범위는 약관 확인이 필요합니다."
    }
  ]
}
```

**Schema Amendment Needed:**
- ✅ `fact_table.table_type` (optional enum: "default" | "ox_matrix")
- ✅ O/X values in cell data (already supported as string values)

---

## Required Schema Amendments

### Amendment 1: fact_table.sort_metadata (Optional)
```json
{
  "fact_table": {
    "sort_metadata": {
      "type": "object",
      "properties": {
        "sort_by": {"type": "string", "description": "Column name to sort by"},
        "sort_order": {"type": "string", "enum": ["asc", "desc"]},
        "limit": {"type": "number", "description": "Maximum rows to display"}
      }
    }
  }
}
```

### Amendment 2: fact_table.visual_emphasis (Optional)
```json
{
  "fact_table": {
    "visual_emphasis": {
      "type": "object",
      "properties": {
        "min_value_style": {"type": "string", "enum": ["blue", "green", "default"]},
        "max_value_style": {"type": "string", "enum": ["red", "orange", "default"]}
      }
    }
  }
}
```

### Amendment 3: fact_table.table_type (Optional)
```json
{
  "fact_table": {
    "table_type": {
      "type": "string",
      "enum": ["default", "ox_matrix"],
      "default": "default",
      "description": "Table display mode (default: standard comparison, ox_matrix: O/X coverage availability)"
    }
  }
}
```

### Amendment 4: fact_table.rows[].highlight (Optional)
```json
{
  "fact_table": {
    "rows": {
      "items": {
        "properties": {
          "highlight": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Array of cell keys to highlight (difference emphasis)"
          }
        }
      }
    }
  }
}
```

### Amendment 5: snapshot.filter_criteria (Optional)
```json
{
  "snapshot": {
    "filter_criteria": {
      "type": "object",
      "properties": {
        "insurer_filter": {"type": "array", "items": {"type": "string"}},
        "disease_scope": {"type": "array", "items": {"type": "string"}},
        "slot_key": {"type": "string"},
        "difference_detected": {"type": "boolean"}
      }
    }
  }
}
```

---

## Schema Version Update

**Current:** `next4.v1`
**After Amendments:** `next4.v2` (non-breaking, all fields optional)

**Rationale:** All amendments are optional fields, existing consumers remain compatible.

---

## Implementation Plan

1. ✅ Customer requirements documented (INCA_DIO_REQUIREMENTS.md)
2. ⏳ Update `compare_view_model.schema.json` with amendments
3. ⏳ Update ViewModel assembler to populate new fields
4. ⏳ Update frontend renderer to support new fields (sorting, O/X matrix, highlighting)
5. ⏳ Create E2E tests for examples 1-4

---

**Status:** READY FOR IMPLEMENTATION
**Constitutional Compliance:** VERIFIED (all amendments fact-only, no judgment)
