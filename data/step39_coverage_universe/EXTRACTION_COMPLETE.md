# STEP 3.9-1: Coverage Universe Extraction - COMPLETE

## Completion Date
2025-12-25

## Summary
Successfully extracted coverage universe data from 8 insurers' proposal PDFs (6 newly processed + 2 previously completed).

## Insurers Processed
1. **DB** (2 variants: 40세이하, 41세이상) - 62 rows total
2. **LOTTE** (2 variants: 남, 여) - 70 rows total  
3. **HANWHA** (single file) - 37 rows
4. **HEUNGKUK** (single file) - 23 rows
5. **HYUNDAI** (single file) - 27 rows
6. **MERITZ** (single file) - 34 rows
7. **KB** (previously completed) - 40 rows
8. **SAMSUNG** (previously completed) - 41 rows

## Total Statistics
- **Total CSV files created**: 8
- **Total coverage rows extracted**: 334 rows
- **Extraction method**: Rule-based PDF table extraction using pdfplumber
- **Schema compliance**: 100% (all files follow strict CSV schema)

## CSV Schema (Strict)
```
insurer,proposal_file,proposal_variant,row_id,coverage_name_raw,amount_raw,premium_raw,pay_term_raw,maturity_raw,renewal_raw,notes
```

## Output Location
```
/Users/cheollee/inca-RAG-final/data/step39_coverage_universe/extracts/
```

## Files Generated
1. DB_coverage_universe.csv (8.0K)
2. LOTTE_coverage_universe.csv (8.8K)
3. HANWHA_coverage_universe.csv (4.8K)
4. HEUNGKUK_coverage_universe.csv (2.9K)
5. HYUNDAI_coverage_universe.csv (3.3K)
6. MERITZ_coverage_universe.csv (4.2K)
7. KB_coverage_universe.csv (4.6K)
8. SAMSUNG_coverage_universe.csv (5.6K)

## Extraction Methodology

### Summary Table Only Principle
- Extracted **ONLY** from summary tables (가입담보요약, 가입담보 리스트, etc.)
- Did **NOT** extract from detailed tables (담보 및 보장내용 예시, 보장사항, etc.)
- Rationale: Summary tables are the SSOT for coverage universe (what is actually subscribed)

### Page Locations by Insurer
- **DB**: Page 4 (index 3) - "가입담보요약"
- **LOTTE**: Pages 2-3 (indices 1-2) - "피보험자 / 소유자별 가입담보"
- **HANWHA**: Pages 3-4 (indices 2-3) - "가입담보요약"
- **HEUNGKUK**: Pages 7-8 (indices 6-7) - "가입담보 리스트"
- **HYUNDAI**: Pages 2-3 (indices 1-2) - "가입담보 요약표"
- **MERITZ**: Pages 3-4 (indices 2-3) - "가입담보리스트"

### Data Extraction Rules Applied
1. **One PDF row = One CSV row** (1:1 mapping)
2. **Original text preservation** (no normalization or interpretation)
3. **NULL for missing values** (not empty strings)
4. **Header/footer filtering** (skipped document metadata rows)
5. **Total row filtering** (skipped "보장보험료 합계" rows)
6. **Incomplete row filtering** (skipped rows with no amount/premium/term)

### Insurer-Specific Handling
- **DB**: 6-column structure (No. | empty | 담보명 | 금액 | 보험료 | 납기/만기)
- **LOTTE**: 5-column structure (순번 | 담보명 | 금액 | 납기/만기 | 보험료)
- **HANWHA**: 5-column structure (번호 | 담보명 | 금액 | 보험료 | 납기/만기)
- **HEUNGKUK**: 5-column structure with category column (구분 | 담보명 | 납입/만기 | 금액 | 보험료)
- **HYUNDAI**: Variable column structure with numbering (담보명 with 1., 2., ... prefix)
- **MERITZ**: 6-column structure with category (category | number | 담보명 | 금액 | 보험료 | 납기/만기)

## Extraction Quality Assurance
✅ All files follow strict CSV schema  
✅ No header/footer noise in data rows  
✅ No total/summary rows included  
✅ Original text preserved (no normalization)  
✅ Variant handling correct (DB: 2 variants, LOTTE: 2 variants)  
✅ Row IDs sequential within each variant  
✅ All expected columns present and populated where applicable  

## Known Limitations
- Premium values include Korean "원" suffix in some insurers
- Amount values use mixed formats (e.g., "1천만원" vs "1,000만원")
- Term formats vary by insurer (e.g., "20년/100세" vs "20년납 100세만기")
- These variations are **intentional** to preserve original text

## Next Steps (Not Included in This Task)
- Consolidated CSV creation (merge all insurers)
- Validation report generation
- Canonical coverage code mapping
- Amount/premium normalization
- Universe lock enforcement

## Constitutional Compliance
✅ Coverage Universe Lock: Extracted from proposal summaries only (Article I)  
✅ Deterministic Extraction: Used rule-based regex patterns, no LLM inference (Article II)  
✅ Document Priority: Proposals treated as SSOT for universe (Section 1)  
✅ Single Source of Truth: Each insurer's proposal is the sole universe source  

## Extraction Script
Location: `/Users/cheollee/inca-RAG-final/scripts/step39_extract_coverage_universe.py`

## Status
**COMPLETE** ✅

All 6 insurers successfully extracted. No errors or data quality issues detected.
