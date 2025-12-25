#!/usr/bin/env python3
"""
STEP 3.9: Extract Coverage Universe from Proposal PDFs

Purpose: Extract ALL coverage rows from insurer proposal PDFs as-is
Output: CSV files (per-insurer + consolidated)
Rules:
  - Extract raw text only (NO interpretation/normalization)
  - One PDF row = One CSV row
  - NULL for empty/unknown values
"""

import os
import sys
import csv
import re
from pathlib import Path
from typing import List, Dict, Optional
import PyPDF2

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Output directory
OUTPUT_DIR = PROJECT_ROOT / "data" / "step39_coverage_universe"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# CSV Schema (FIXED - do NOT modify)
CSV_COLUMNS = [
    "insurer",
    "proposal_file",
    "proposal_variant",
    "row_id",
    "coverage_name_raw",
    "amount_raw",
    "premium_raw",
    "pay_term_raw",
    "maturity_raw",
    "renewal_raw",
    "notes"
]

# Insurer mapping
INSURER_MAP = {
    "samsung": "SAMSUNG",
    "kb": "KB",
    "meritz": "MERITZ",
    "db": "DB",
    "lotte": "LOTTE",
    "hanwha": "HANWHA",
    "heungkuk": "HEUNGKUK",
    "hyundai": "HYUNDAI"
}


def extract_text_from_pdf(pdf_path: Path) -> Dict[int, str]:
    """Extract text from PDF by page."""
    pages = {}
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for i, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                pages[i] = text if text else ""
    except Exception as e:
        print(f"  ⚠️  Error reading {pdf_path.name}: {e}")
    return pages


def parse_samsung_proposal(pdf_path: Path) -> List[Dict[str, str]]:
    """Parse Samsung proposal and extract coverage rows."""
    rows = []
    pages = extract_text_from_pdf(pdf_path)

    # Determine variant from filename
    variant = None
    if "남" in pdf_path.stem or "여" in pdf_path.stem:
        variant = "남" if "남" in pdf_path.stem else "여"

    # Samsung specific: coverage table is on pages 2-3
    coverage_section = ""
    for page_num in [2, 3]:
        if page_num in pages:
            coverage_section += pages[page_num] + "\n"

    # Extract coverage rows from table
    # Pattern: coverage name followed by amount, premium, term
    lines = coverage_section.split('\n')

    current_row = None
    row_counter = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Match coverage rows (담보가입현황 section)
        # Look for pattern: coverage_name | amount | premium | term
        if any(keyword in line for keyword in ["진단", "수술", "입원", "사망", "장해", "치료비"]):
            row_counter += 1

            # Try to extract components
            # Samsung format: coverage_name  amount  premium  term  code
            parts = re.split(r'\s{2,}', line)  # Split on 2+ spaces

            if len(parts) >= 3:
                coverage_name = parts[0]
                amount = parts[1] if len(parts) > 1 else None
                premium = parts[2] if len(parts) > 2 else None
                term = parts[3] if len(parts) > 3 else None

                # Extract renewal info (갱신형 keyword)
                renewal = "갱신형" if "갱신형" in line else None

                rows.append({
                    "insurer": "SAMSUNG",
                    "proposal_file": pdf_path.name,
                    "proposal_variant": variant,
                    "row_id": str(row_counter) if row_counter else None,
                    "coverage_name_raw": coverage_name,
                    "amount_raw": amount,
                    "premium_raw": premium,
                    "pay_term_raw": term,
                    "maturity_raw": term,  # Same as pay_term in Samsung format
                    "renewal_raw": renewal,
                    "notes": None
                })

    return rows


def extract_insurer_proposals(data_dir: Path, insurer_code: str) -> List[Dict[str, str]]:
    """Extract proposals for one insurer."""
    insurer_folder = data_dir / insurer_code / "가입설계서"

    if not insurer_folder.exists():
        print(f"  ⚠️  No proposal folder for {insurer_code}")
        return []

    pdf_files = list(insurer_folder.glob("*.pdf"))
    print(f"  📄 Found {len(pdf_files)} proposal PDF(s) for {insurer_code}")

    all_rows = []
    for pdf_path in pdf_files:
        print(f"    Processing: {pdf_path.name}")

        # For now, only Samsung parser is implemented
        if insurer_code == "samsung":
            rows = parse_samsung_proposal(pdf_path)
        else:
            # Placeholder for other insurers
            rows = []
            print(f"      ℹ️  Parser not yet implemented for {insurer_code}")

        all_rows.extend(rows)
        print(f"      ✅ Extracted {len(rows)} coverage rows")

    return all_rows


def write_csv(rows: List[Dict[str, str]], output_path: Path):
    """Write rows to CSV file."""
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✅ Written to: {output_path}")


def generate_validation_report(all_rows: List[Dict[str, str]]) -> str:
    """Generate validation report."""
    from collections import Counter

    report = []
    report.append("=" * 80)
    report.append("STEP 3.9 Coverage Universe Extraction Report")
    report.append("=" * 80)
    report.append("")

    # Per-insurer summary
    report.append("## 6.1 Per-Insurer Summary")
    report.append("")
    insurer_counts = Counter(row["insurer"] for row in all_rows)
    for insurer, count in sorted(insurer_counts.items()):
        report.append(f"  - {insurer}: {count} rows")
    report.append(f"\n  **Total: {len(all_rows)} rows**")
    report.append("")

    # File-level summary
    report.append("## 6.2 Per-File Summary")
    report.append("")
    file_counts = Counter(row["proposal_file"] for row in all_rows)
    for filename, count in sorted(file_counts.items()):
        report.append(f"  - {filename}: {count} rows")
    report.append("")

    # Data quality metrics
    report.append("## 6.3 Data Quality Metrics")
    report.append("")

    # row_id missing count
    missing_row_id = sum(1 for row in all_rows if not row.get("row_id"))
    report.append(f"  - Missing row_id: {missing_row_id} / {len(all_rows)} ({missing_row_id/len(all_rows)*100:.1f}%)")

    # coverage_name exact duplicates
    coverage_names = [row["coverage_name_raw"] for row in all_rows]
    name_counts = Counter(coverage_names)
    duplicates = {name: count for name, count in name_counts.items() if count > 1}
    report.append(f"  - Exact duplicate coverage names: {len(duplicates)} unique names")

    # amount_raw NULL ratio
    null_amounts = sum(1 for row in all_rows if not row.get("amount_raw"))
    report.append(f"  - NULL amount_raw: {null_amounts} / {len(all_rows)} ({null_amounts/len(all_rows)*100:.1f}%)")

    report.append("")
    report.append("=" * 80)

    return "\n".join(report)


def main():
    """Main execution."""
    print("\n" + "=" * 80)
    print("STEP 3.9: Extract Proposal Coverage Universe")
    print("=" * 80 + "\n")

    data_dir = PROJECT_ROOT / "data"

    all_rows = []

    # Process each insurer
    for insurer_code in sorted(INSURER_MAP.keys()):
        insurer_name = INSURER_MAP[insurer_code]
        print(f"\n📂 Processing {insurer_name}...")

        rows = extract_insurer_proposals(data_dir, insurer_code)

        if rows:
            # Write per-insurer CSV
            output_csv = OUTPUT_DIR / f"{insurer_name}_proposal_coverage_universe.csv"
            write_csv(rows, output_csv)
            all_rows.extend(rows)

    # Write consolidated CSV
    print(f"\n📊 Generating consolidated CSV...")
    consolidated_csv = OUTPUT_DIR / "ALL_INSURERS_proposal_coverage_universe.csv"
    write_csv(all_rows, consolidated_csv)

    # Generate validation report
    print(f"\n📋 Generating validation report...")
    report = generate_validation_report(all_rows)
    report_path = OUTPUT_DIR / "VALIDATION_REPORT.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(report)
    print(f"  ✅ Report saved to: {report_path}")

    print("\n" + "=" * 80)
    print("✅ STEP 3.9 Complete")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
