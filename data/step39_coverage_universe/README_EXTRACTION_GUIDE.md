# STEP 3.9: Coverage Universe Extraction Guide

## Purpose

Extract **ALL coverage rows** from insurer proposal PDFs as raw data.

## Output Format: CSV

**Schema (FIXED)**:
```csv
insurer,proposal_file,proposal_variant,row_id,coverage_name_raw,amount_raw,premium_raw,pay_term_raw,maturity_raw,renewal_raw,notes
```

## Extraction Rules

### ✅ DO
- Extract raw text exactly as it appears in PDF table
- One PDF table row = One CSV row
- Use NULL for missing/unclear values
- Copy coverage names verbatim (NO normalization)
- Include all visible table rows (no filtering)

### ❌ DO NOT
- Interpret or normalize coverage names
- Merge similar coverages
- Skip any rows
- Guess or estimate missing values
- Reference other documents (약관/요약서)

## Progress

| Insurer | PDF Count | Rows Extracted | Status | File |
|---------|-----------|----------------|--------|------|
| SAMSUNG | 1 | 41 | ✅ Complete | `SAMSUNG_proposal_coverage_universe.csv` |
| KB | 1 | 0 | ⏳ Pending | - |
| MERITZ | 1 | 0 | ⏳ Pending | - |
| DB | 2 | 0 | ⏳ Pending | - |
| LOTTE | 2 | 0 | ⏳ Pending | - |
| HANWHA | 1 | 0 | ⏳ Pending | - |
| HEUNGKUK | 1 | 0 | ⏳ Pending | - |
| HYUNDAI | 1 | 0 | ⏳ Pending | - |

**Total**: 10 PDFs → Target: ~300-400 rows (estimated)

## Samsung Extraction Example

From `삼성_가입설계서_2511.pdf` pages 2-3:

```csv
SAMSUNG,삼성_가입설계서_2511.pdf,NULL,NULL,암 진단비(유사암 제외),3000만원,40620,20년납,100세만기,NULL,ZD8200010
SAMSUNG,삼성_가입설계서_2511.pdf,NULL,NULL,뇌출혈 진단비,1000만원,1790,20년납,100세만기,NULL,ZD4295010
```

## Next Steps

1. Extract remaining 7 insurers using same manual method
2. Generate consolidated `ALL_INSURERS_proposal_coverage_universe.csv`
3. Generate validation report
4. Verify no coverage rows are missing

## Notes

- Manual extraction is intentional (deterministic, verifiable)
- LLM/OCR parsing is prohibited per Constitution
- Human verification is required for DoD
