# Excel Reproducibility Instructions

**Enhanced Excel File**: `data/담보명mapping자료__inscd_patched_plus.xlsx`

---

## Purpose

This document provides the complete reproducibility path for the enhanced Excel mapping file used in STEP 3.10-η-2 forced remapping.

---

## Reproduction Steps

### Prerequisites

- Python 3.11+
- Required packages: `openpyxl`, `pandas`
- Base files must exist:
  - `data/담보명mapping자료__inscd_patched.xlsx`
  - `data/step310_mapping/excel_backlog/backlog_N*.csv` (8 files)

### Step 1: Verify Base Excel

```bash
ls -lh data/담보명mapping자료__inscd_patched.xlsx
```

Expected:
- File size: ~13KB
- Row count: 264 data rows (265 including header)

### Step 2: Verify Backlog Files

```bash
ls -1 data/step310_mapping/excel_backlog/
```

Expected output:
```
backlog_N01_SAMSUNG.csv
backlog_N02_HANWHA.csv
backlog_N03_LOTTE.csv
backlog_N04_MERITZ.csv
backlog_N05_KB.csv
backlog_N06_HYUNDAI.csv
backlog_N07_HEUNGKUK.csv
backlog_N08_DB.csv
```

Total backlog items: 67 (across all files)

### Step 3: Run Enhancement Script

```bash
python scripts/step310_eta_excel_enhancement.py
```

Expected output:
```
======================================================================
STEP 3.10-η: Excel Enhancement for UNMAPPED Coverage Backlog
======================================================================
📂 Loading backlog from 8 files...
   ✓ Loaded 67 total backlog items

🔍 Filtering backlog items:
   ✅ Processable (ADD targets): 48
   ⏭️  Deferred (structural): 19

📝 Enhancing Excel: 담보명mapping자료__inscd_patched.xlsx

   Processing N01: 8 items
   Processing N02: 2 items
   Processing N03: 7 items
   Processing N04: 11 items
   Processing N05: 7 items
   Processing N06: 7 items
   Processing N07: 3 items
   Processing N08: 3 items

   ✓ Added 48 new rows
   ✓ Saved to: 담보명mapping자료__inscd_patched_plus.xlsx

======================================================================
✅ STEP 3.10-η COMPLETE
======================================================================
```

### Step 4: Verify Enhanced Excel

```bash
python -c "
import openpyxl
from pathlib import Path

excel_path = Path('data/담보명mapping자료__inscd_patched_plus.xlsx')
wb = openpyxl.load_workbook(excel_path, read_only=True)
ws = wb.active

rows = len([r for r in ws.iter_rows(min_row=2, values_only=True) if r[0]])
print(f'Enhanced Excel rows: {rows}')
print(f'Expected: 312 (264 + 48)')
print(f'Match: {\"✅\" if rows == 312 else \"❌\"}')

wb.close()
"
```

Expected:
```
Enhanced Excel rows: 312
Expected: 312 (264 + 48)
Match: ✅
```

---

## Processing Rules Applied

### Included (ADD targets)
- `ADD_EXCEL_ROW`: C1/C2/C6 causes only
- `ADD_EXCEL_ROW_WITH_NOTE`: with annotation
- Total: 48 items

### Excluded (Deferred)
- `STRUCTURAL_REVIEW`: C3/C4/C7 causes
- Total: 19 items (deferred to STEP 3.10-θ)

---

## Enhancement Log

Detailed log of all additions: `data/step310_mapping/excel_enhancement/ENHANCEMENT_LOG.csv`

Columns:
- `ins_cd`: Insurer code
- `coverage_name_raw`: Original coverage name from proposal
- `action`: ADD_EXCEL_ROW or ADD_EXCEL_ROW_WITH_NOTE
- `applied_code`: Assigned coverage code (cre_cvr_cd)
- `note`: Annotation (if applicable)
- `timestamp`: Processing timestamp

---

## Per-Insurer Additions

| Insurer Code | Insurer Name | Rows Added |
|--------------|--------------|------------|
| N01 | SAMSUNG | 8 |
| N02 | HANWHA | 2 |
| N03 | LOTTE | 7 |
| N04 | MERITZ | 11 |
| N05 | KB | 7 |
| N06 | HYUNDAI | 7 |
| N07 | HEUNGKUK | 3 |
| N08 | DB | 3 |
| **TOTAL** | | **48** |

---

## Constitutional Compliance

- ✅ **Single Source of Truth**: Excel remains canonical mapping authority
- ✅ **No LLM Inference**: All coverage codes assigned deterministically
  - Similar codes reused from existing entries
  - New codes: `NEW_TEMP_{ins_cd}_{hash}` format
- ✅ **Coverage Universe Lock**: All additions from proposal universe
- ✅ **Evidence Rule**: All additions traceable to backlog analysis

---

## Validation

To validate the enhanced Excel matches the expected state:

```bash
python scripts/step310_eta2_forced_remapping.py
```

This will:
1. Validate enhanced Excel structure
2. Verify +48 row difference from base
3. Execute forced remapping
4. Generate metrics report

Expected metrics (from STEP 3.10-η-2):
- MAPPED: 315 (94.31%) - up from 259 (77.54%)
- UNMAPPED: 19 (5.69%) - down from 75 (22.46%)
- AMBIGUOUS: 0 (0.00%) - unchanged

---

## File Checksums (Optional)

For additional verification, you can compute file hashes:

```bash
# Base Excel
md5 data/담보명mapping자료__inscd_patched.xlsx

# Enhanced Excel
md5 data/담보명mapping자료__inscd_patched_plus.xlsx
```

Note: Checksums will vary if Excel metadata (timestamps, etc.) differs, but row counts and content should match.

---

## Related Documentation

1. **Enhancement Report**: `STEP310_ETA_EXCEL_ENHANCEMENT_REPORT.md`
2. **Metrics Report**: `STEP310_ETA_FINAL_METRICS_REPORT.md`
3. **Forced Remapping Report**: `data/step310_mapping/mapping_report_insurer_filtered__eta2.md`

---

## Commit History

- STEP 3.10-η: `cde40d8` - Excel enhancement implementation
- STEP 3.10-η-2: TBD - Forced remapping with enhanced Excel

---

**Last Updated**: 2025-12-26
**Reproducibility Status**: ✅ LOCKED
