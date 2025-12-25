#!/usr/bin/env python3
"""
STEP 3.9-1: Extract coverage universe from proposal PDFs

Extract ONLY summary tables from proposal PDFs for 6 insurers.
Output: CSV files with strict schema (one PDF row = one CSV row).

CSV Schema:
insurer,proposal_file,proposal_variant,row_id,coverage_name_raw,amount_raw,premium_raw,pay_term_raw,maturity_raw,renewal_raw,notes

Rules:
1. Extract ONLY from summary tables (NOT detailed tables)
2. One PDF row = one CSV row (1:1)
3. Use original text exactly (no normalization)
4. NULL for empty/missing values
"""

import pdfplumber
import pandas as pd
from pathlib import Path
import re
import sys

# Base paths
DATA_DIR = Path("/Users/cheollee/inca-RAG-final/data")
OUTPUT_DIR = DATA_DIR / "step39_coverage_universe" / "extracts"

# Insurer configurations based on YAML profiles
INSURERS = {
    "DB": {
        "variants": [
            {
                "name": "40세이하",
                "file": DATA_DIR / "db" / "가입설계서" / "DB_가입설계서(40세이하)_2511.pdf",
                "summary_pages": [3],  # page 4 in human terms = index 3
                "table_name": "가입담보요약",
            },
            {
                "name": "41세이상",
                "file": DATA_DIR / "db" / "가입설계서" / "DB_가입설계서(41세이상)_2511.pdf",
                "summary_pages": [3],
                "table_name": "가입담보요약",
            },
        ]
    },
    "LOTTE": {
        "variants": [
            {
                "name": "남",
                "file": DATA_DIR / "lotte" / "가입설계서" / "롯데_가입설계서(남)_2511.pdf",
                "summary_pages": [1, 2],  # pages 2-3 in human terms = indices 1-2
                "table_name": "피보험자 / 소유자별 가입담보",
            },
            {
                "name": "여",
                "file": DATA_DIR / "lotte" / "가입설계서" / "롯데_가입설계서(여)_2511.pdf",
                "summary_pages": [1, 2],
                "table_name": "피보험자 / 소유자별 가입담보",
            },
        ]
    },
    "HANWHA": {
        "variants": [
            {
                "name": None,
                "file": DATA_DIR / "hanwha" / "가입설계서" / "한화_가입설계서_2511.pdf",
                "summary_pages": [2, 3],  # pages 3-4 in human terms = indices 2-3
                "table_name": "가입담보요약",
            },
        ]
    },
    "HEUNGKUK": {
        "variants": [
            {
                "name": None,
                "file": DATA_DIR / "heungkuk" / "가입설계서" / "흥국_가입설계서_2511.pdf",
                "summary_pages": [6, 7],  # pages 7-8 in human terms = indices 6-7
                "table_name": "가입담보 리스트",
            },
        ]
    },
    "HYUNDAI": {
        "variants": [
            {
                "name": None,
                "file": DATA_DIR / "hyundai" / "가입설계서" / "현대_가입설계서_2511.pdf",
                "summary_pages": [1, 2],  # pages 2-3 in human terms = indices 1-2
                "table_name": "가입담보 요약표",
            },
        ]
    },
    "MERITZ": {
        "variants": [
            {
                "name": None,
                "file": DATA_DIR / "meritz" / "가입설계서" / "메리츠_가입설계서_2511.pdf",
                "summary_pages": [2, 3],  # pages 3-4 in human terms = indices 2-3
                "table_name": "가입담보리스트",
            },
        ]
    },
}


def clean_text(text):
    """Clean extracted text (preserve original but remove extra whitespace)"""
    if text is None or pd.isna(text):
        return None
    text = str(text).strip()
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    return text if text else None


def is_header_row(row_values, insurer):
    """Check if row is a header row (skip it)"""
    if not row_values:
        return False

    # Join all cell values
    text = ' '.join([str(v).lower() for v in row_values if v])

    # Specific patterns to skip
    skip_patterns = [
        '본 가입제안서는',
        '가입제안서',
        '발행번호',
        'page \\d+/\\d+',
        '발행일:',
        '보험대리점',
        '준법감시인',
        '영업담당자',
        '설계번호',
        '고유번호',
        '발행일시',
    ]

    for pattern in skip_patterns:
        if re.search(pattern, text):
            return True

    # Common header patterns
    header_patterns = [
        '담보', '가입금액', '보험료', '납기', '만기', '순번',
        '구분', '번호', '피보험자', '소유자별'
    ]

    # If row contains multiple header keywords and no numbers, it's likely a header
    matches = sum(1 for pattern in header_patterns if pattern in text)
    has_amount = bool(re.search(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?', text))

    return matches >= 2 and not has_amount


def is_total_row(row_values):
    """Check if row is a total/summary row (skip it)"""
    if not row_values:
        return False

    text = ' '.join([str(v).lower() for v in row_values if v])

    # Total row patterns
    total_patterns = ['합계', '총계', '보장보험료 합계', '전체']

    return any(pattern in text for pattern in total_patterns)


def find_coverage_table(tables, insurer):
    """Find the coverage table among multiple tables on a page"""

    # For HEUNGKUK, look for table with '담 보 명' header
    if insurer == "HEUNGKUK":
        for table_idx, table in enumerate(tables):
            if len(table) > 1:
                # Check second row for column headers
                header_text = ' '.join([str(cell) for cell in table[1] if cell])
                if '담 보 명' in header_text or '담보명' in header_text:
                    return table_idx

    # For HYUNDAI, look for table with '가입담보' and '가입금액' and '보험료' headers
    if insurer == "HYUNDAI":
        for table_idx, table in enumerate(tables):
            if len(table) > 1:
                # Check first row for column headers
                header_text = ' '.join([str(cell) for cell in table[0] if cell])
                if '가입담보' in header_text and '가입금액' in header_text and '보험료' in header_text:
                    return table_idx

    # For MERITZ, look for table with numbered coverages (가입담보 with numbers)
    if insurer == "MERITZ":
        for table_idx, table in enumerate(tables):
            if len(table) > 3:
                # Check if table has the coverage structure
                for row in table[:3]:
                    row_text = ' '.join([str(cell) for cell in row if cell])
                    if '가입담보' in row_text or ('일반상해' in row_text and '후유장해' in row_text):
                        return table_idx

    # For other insurers, return the first table with sufficient rows
    for table_idx, table in enumerate(tables):
        if len(table) > 3:  # At least header + 2 data rows
            return table_idx

    return 0  # Default to first table


def extract_coverage_rows(pdf_path, page_indices, insurer):
    """Extract coverage rows from summary table pages"""
    rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx in page_indices:
            if page_idx >= len(pdf.pages):
                print(f"  WARNING: Page {page_idx + 1} not found in {pdf_path.name}")
                continue

            page = pdf.pages[page_idx]
            tables = page.extract_tables()

            if not tables:
                print(f"  WARNING: No tables found on page {page_idx + 1} of {pdf_path.name}")
                continue

            # Find the coverage table
            coverage_table_idx = find_coverage_table(tables, insurer)
            table = tables[coverage_table_idx]

            # Process table rows
            for row_idx, row in enumerate(table):
                # Skip empty rows
                if not any(row):
                    continue

                # Skip header rows
                if is_header_row(row, insurer):
                    continue

                # Skip total rows
                if is_total_row(row):
                    continue

                # Extract based on insurer-specific column structure
                extracted_row = extract_row_by_insurer(row, insurer)
                if extracted_row:
                    rows.append(extracted_row)

    return rows


def extract_row_by_insurer(row, insurer):
    """Extract coverage data from row based on insurer-specific format"""

    # Clean all cells
    cells = [clean_text(cell) for cell in row]

    # Skip if all cells are empty
    if not any(cells):
        return None

    # Insurer-specific column mappings based on YAML profiles
    if insurer == "DB":
        # Actual table structure: No. | empty | 가입담보 | 가입금액 | 보험료(원) | 납기/만기(갱신종료시기)
        if len(cells) >= 6:
            # Extract from correct columns
            coverage_name = cells[2]  # 가입담보
            amount = cells[3]  # 가입금액
            premium = cells[4]  # 보험료
            term = cells[5]  # 납기/만기

            # Skip if coverage name is empty
            if not coverage_name:
                return None

            return {
                'coverage_name_raw': coverage_name,
                'amount_raw': amount,
                'premium_raw': premium,
                'pay_term_raw': term,
                'maturity_raw': None,
                'renewal_raw': '(갱신형)' if coverage_name and '(갱신형)' in coverage_name else None,
                'notes': None
            }

    elif insurer == "LOTTE":
        # Columns: 순번 | 담보명 | 가입금액 | 납기/만기 | 보험료(원)
        if len(cells) >= 5:
            return {
                'coverage_name_raw': cells[1],  # 담보명
                'amount_raw': cells[2],  # 가입금액
                'premium_raw': cells[4],  # 보험료
                'pay_term_raw': cells[3],  # 납기/만기
                'maturity_raw': None,
                'renewal_raw': '갱신' if cells[3] and '갱신' in cells[3] else None,
                'notes': None
            }

    elif insurer == "HANWHA":
        # Columns: 번호 | 가입담보 | 가입금액 | 보험료(원) | 납기/만기
        if len(cells) >= 5:
            return {
                'coverage_name_raw': cells[1],  # 가입담보
                'amount_raw': cells[2],  # 가입금액
                'premium_raw': cells[3],  # 보험료
                'pay_term_raw': cells[4],  # 납기/만기
                'maturity_raw': None,
                'renewal_raw': '(갱신형)' if cells[1] and '(갱신형)' in cells[1] else None,
                'notes': None
            }

    elif insurer == "HEUNGKUK":
        # Actual structure: 구분 | 담 보 명 | 납입 및 만기 | 가입금액 | 보험료(원)
        # Note: 구분 column may be None for most rows (only shows "기본"/"선택" for first row of each category)
        if len(cells) >= 5:
            coverage_name = cells[1]  # 담 보 명

            # Skip if coverage name is empty
            if not coverage_name:
                return None

            # Skip category header rows (just "기본" or "선택" without coverage name)
            if coverage_name in ['기본', '선택']:
                return None

            return {
                'coverage_name_raw': coverage_name,
                'amount_raw': cells[3],  # 가입금액
                'premium_raw': cells[4],  # 보험료
                'pay_term_raw': cells[2],  # 납입 및 만기
                'maturity_raw': None,
                'renewal_raw': '[갱신형]' if coverage_name and '[갱신형]' in coverage_name else None,
                'notes': None
            }

    elif insurer == "HYUNDAI":
        # Actual structure varies:
        # Page 2 table: 가입담보 | empty | 가입금액 | 보험료(원) | 납기/만기 (5 cols with numbering in col 0)
        # Page 3 table: 가입담보 | empty | empty | 가입금액 | 보험료(원) | empty | 납기/만기 (7 cols)

        # Try to find coverage name, amount, premium, term
        coverage_name = None
        amount = None
        premium = None
        term = None

        # Find coverage name (usually in cells[0] or cells[1], may have numbering)
        if cells[0] and not cells[0].isdigit() and '.' not in cells[0]:
            coverage_name = cells[0]
        elif cells[1]:
            # Numbering in cells[0], coverage in cells[1]
            coverage_name = cells[1]

        # Remove numbering if present in coverage name
        if coverage_name:
            coverage_name = re.sub(r'^\d+\.\s*', '', coverage_name)

        # Find amount, premium, term by scanning cells from right to left
        # Term is usually last non-empty cell
        # Premium is usually second-to-last
        # Amount is usually third-to-last
        non_empty = [(i, cell) for i, cell in enumerate(cells) if cell and cell != coverage_name]
        if len(non_empty) >= 3:
            term = non_empty[-1][1]
            premium = non_empty[-2][1]
            amount = non_empty[-3][1]

        if not coverage_name:
            return None

        # Skip rows with no amount, premium, or term (incomplete data)
        if not amount and not premium and not term:
            return None

        return {
            'coverage_name_raw': coverage_name,
            'amount_raw': amount,
            'premium_raw': premium,
            'pay_term_raw': term,
            'maturity_raw': None,
            'renewal_raw': '(갱신형)' if coverage_name and '(갱신형)' in coverage_name else None,
            'notes': None
        }

    elif insurer == "MERITZ":
        # Actual structure: category | number | 가입담보 | 가입금액 | 보험료(원) | 납기/만기
        # Example: ['사망후유', '2', '일반상해사망', '1백만원', '60', '20년 / 100세']
        if len(cells) >= 6:
            category = cells[0]  # May be None for subsequent rows in same category
            number = cells[1]  # Coverage number
            coverage_name = cells[2]  # 가입담보
            amount = cells[3]  # 가입금액
            premium = cells[4]  # 보험료
            term = cells[5]  # 납기/만기

            # Skip if coverage name is empty
            if not coverage_name:
                return None

            # Skip category-only rows (category in first cell, no coverage name)
            category_keywords = ['기본계약', '사망후유', '3대진단', '입원일당', '수술', '골절/화상', '기타', '할증/제도성']
            if category and category in category_keywords and not coverage_name:
                return None

            # Skip special rows with no amount and premium (like "자동갱신특약")
            if coverage_name and not amount and not premium:
                return None

            return {
                'coverage_name_raw': coverage_name,
                'amount_raw': amount,
                'premium_raw': premium,
                'pay_term_raw': term,
                'maturity_raw': None,
                'renewal_raw': '갱신' if coverage_name and ('갱신' in coverage_name or '(10년갱신)' in coverage_name or '(20년갱신)' in coverage_name) else None,
                'notes': None
            }

    return None


def process_insurer(insurer_name, config):
    """Process all variants for an insurer"""
    all_results = []

    print(f"\n{'='*60}")
    print(f"Processing {insurer_name}")
    print(f"{'='*60}")

    for variant in config['variants']:
        variant_name = variant['name']
        pdf_path = variant['file']
        pages = variant['summary_pages']

        print(f"\nVariant: {variant_name if variant_name else 'default'}")
        print(f"File: {pdf_path.name}")
        print(f"Pages: {[p+1 for p in pages]} (human-readable)")

        if not pdf_path.exists():
            print(f"  ERROR: File not found: {pdf_path}")
            continue

        # Extract rows
        rows = extract_coverage_rows(pdf_path, pages, insurer_name)

        print(f"  Extracted {len(rows)} coverage rows")

        # Add metadata
        for idx, row in enumerate(rows, start=1):
            row.update({
                'insurer': insurer_name,
                'proposal_file': pdf_path.name,
                'proposal_variant': variant_name if variant_name else None,
                'row_id': idx
            })
            all_results.append(row)

    return all_results


def save_to_csv(insurer_name, rows):
    """Save extracted rows to CSV with strict schema"""
    if not rows:
        print(f"  WARNING: No rows to save for {insurer_name}")
        return None

    # Create DataFrame with strict schema
    df = pd.DataFrame(rows, columns=[
        'insurer',
        'proposal_file',
        'proposal_variant',
        'row_id',
        'coverage_name_raw',
        'amount_raw',
        'premium_raw',
        'pay_term_raw',
        'maturity_raw',
        'renewal_raw',
        'notes'
    ])

    # Save to CSV
    output_file = OUTPUT_DIR / f"{insurer_name}_coverage_universe.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"\n  ✓ Saved: {output_file}")
    print(f"  ✓ Rows: {len(df)}")

    return output_file


def main():
    """Main extraction process"""
    print("="*60)
    print("STEP 3.9-1: Coverage Universe Extraction")
    print("="*60)
    print(f"Output directory: {OUTPUT_DIR}")

    results_summary = []

    # Process each insurer
    for insurer_name, config in INSURERS.items():
        rows = process_insurer(insurer_name, config)
        output_file = save_to_csv(insurer_name, rows)

        if output_file:
            results_summary.append({
                'insurer': insurer_name,
                'file': output_file.name,
                'rows': len(rows)
            })

    # Print summary
    print("\n" + "="*60)
    print("EXTRACTION SUMMARY")
    print("="*60)

    for result in results_summary:
        print(f"{result['insurer']:10s} | {result['file']:40s} | {result['rows']:3d} rows")

    print(f"\nTotal insurers processed: {len(results_summary)}")
    print(f"Total CSV files created: {len(results_summary)}")
    print(f"\n✓ STEP 3.9-1 Complete")


if __name__ == "__main__":
    main()
