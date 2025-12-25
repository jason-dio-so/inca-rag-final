# STEP 3.10-η-2 Forced Remapping Report

**Generated**: 2025-12-26T00:31:26.006872
**Input Excel**: `담보명mapping자료__inscd_patched_plus.xlsx`
**Output CSV**: `proposal_coverage_mapping_insurer_filtered__eta2.csv`

---

## Overall Statistics

| Status | ζ (Baseline) | η-2 (Enhanced) | Change |
|--------|--------------|----------------|--------|
| **MAPPED** | 259 (77.54%) | 315 (94.31%) | +56 |
| **UNMAPPED** | 75 (22.46%) | 19 (5.69%) | -56 |
| **AMBIGUOUS** | 0 (0.00%) | 0 (0.00%) | +0 |
| **TOTAL** | 334 | 334 | 0 |

---

## Per-Insurer Breakdown

| Insurer | MAPPED | UNMAPPED | AMBIGUOUS | Ratio |
|---------|--------|----------|-----------|-------|
| DB | 62 | 0 | 0 | 100.0% |
| HANWHA | 30 | 7 | 0 | 81.1% |
| HEUNGKUK | 21 | 2 | 0 | 91.3% |
| HYUNDAI | 25 | 2 | 0 | 92.6% |
| KB | 35 | 5 | 0 | 87.5% |
| LOTTE | 70 | 0 | 0 | 100.0% |
| MERITZ | 32 | 2 | 0 | 94.1% |
| SAMSUNG | 40 | 1 | 0 | 97.6% |

---

## Enhancement Effectiveness

### Excel Row Addition
- Base Excel: 264 rows
- Enhanced Excel: 312 rows
- Added: +48 rows

### Mapping Improvement
- MAPPED increase: +56 (116.7% of additions)
- UNMAPPED decrease: -56

---

## Files

1. **Input**:
   - Universe: `ALL_INSURERS_coverage_universe.csv`
   - Mapping: `담보명mapping자료__inscd_patched_plus.xlsx`

2. **Output**:
   - Results: `proposal_coverage_mapping_insurer_filtered__eta2.csv`
   - Report: `mapping_report_insurer_filtered__eta2.md`

3. **Baseline**:
   - Previous: `proposal_coverage_mapping_insurer_filtered.csv`

---

## Constitutional Compliance

- ✅ Mapping logic unchanged (STEP 3.10-2 as-is)
- ✅ Enhanced Excel as sole input
- ✅ No rule modifications
- ✅ Deterministic execution
- ✅ Numbers-only proof

---

**Status**: ✅ COMPLETE
