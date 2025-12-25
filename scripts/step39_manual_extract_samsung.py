#!/usr/bin/env python3
"""
STEP 3.9: Manual extraction helper for Samsung proposal
Based on direct PDF viewing, manually transcribe coverage table
"""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "step39_coverage_universe"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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

# Manually transcribed from Samsung proposal PDF pages 2-3
# Direct copy from table rows - NO interpretation
samsung_rows = [
    # Page 2 - from "담보가입현황" table
    {"row_id": None, "coverage_name_raw": "보험료 납입면제대상Ⅱ", "amount_raw": "10만원", "premium_raw": "189", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD0547010"},
    {"row_id": None, "coverage_name_raw": "암 진단비(유사암 제외)", "amount_raw": "3,000만원", "premium_raw": "40,620", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD8200010"},
    {"row_id": None, "coverage_name_raw": "유사암 진단비(기타피부암)(1년50%)", "amount_raw": "600만원", "premium_raw": "1,440", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD4431010"},
    {"row_id": None, "coverage_name_raw": "유사암 진단비(갑상선암)(1년50%)", "amount_raw": "600만원", "premium_raw": None, "pay_term_raw": None, "maturity_raw": None, "renewal_raw": None, "notes": None},
    {"row_id": None, "coverage_name_raw": "유사암 진단비(대장점막내암)(1년50%)", "amount_raw": "600만원", "premium_raw": None, "pay_term_raw": None, "maturity_raw": None, "renewal_raw": None, "notes": None},
    {"row_id": None, "coverage_name_raw": "유사암 진단비(제자리암)(1년50%)", "amount_raw": "600만원", "premium_raw": None, "pay_term_raw": None, "maturity_raw": None, "renewal_raw": None, "notes": None},
    {"row_id": None, "coverage_name_raw": "유사암 진단비(경계성종양)(1년50%)", "amount_raw": "600만원", "premium_raw": None, "pay_term_raw": None, "maturity_raw": None, "renewal_raw": None, "notes": None},
    {"row_id": None, "coverage_name_raw": "신재진단암(기타피부암 및 갑상선암 포함) 진단비(1년주기,5회한)", "amount_raw": "1,000만원", "premium_raw": "15,760", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD1849010"},
    {"row_id": None, "coverage_name_raw": "뇌출혈 진단비", "amount_raw": "1,000만원", "premium_raw": "1,790", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD4295010"},
    {"row_id": None, "coverage_name_raw": "뇌졸중 진단비(1년50%)", "amount_raw": "1,000만원", "premium_raw": "7,060", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD2779010"},
    {"row_id": None, "coverage_name_raw": "뇌혈관질환 진단비(1년50%)", "amount_raw": "1,000만원", "premium_raw": "9,300", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD4564010"},
    {"row_id": None, "coverage_name_raw": "허혈성심장질환 진단비(1년50%)", "amount_raw": "1,000만원", "premium_raw": "5,700", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD4566010"},
    {"row_id": None, "coverage_name_raw": "기타 심장부정맥 진단비(1년50%)", "amount_raw": "100만원", "premium_raw": "870", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD2167010"},
    {"row_id": None, "coverage_name_raw": "특정3대심장질환 진단비(1년50%)", "amount_raw": "100만원", "premium_raw": "1,681", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD2168010"},
    {"row_id": None, "coverage_name_raw": "골절 진단비(치아파절(깨짐, 부러짐) 제외)", "amount_raw": "10만원", "premium_raw": "626", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD8202010"},
    {"row_id": None, "coverage_name_raw": "화상 진단비", "amount_raw": "10만원", "premium_raw": "81", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD2438010"},
    {"row_id": None, "coverage_name_raw": "상해 입원일당(1일이상)", "amount_raw": "1만원", "premium_raw": "1,267", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD2800010"},
    {"row_id": None, "coverage_name_raw": "질병 입원일당(1일이상)", "amount_raw": "1만원", "premium_raw": "4,386", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD2841010"},
    {"row_id": None, "coverage_name_raw": "암 직접치료 입원일당Ⅱ(1일이상)(요양병원 제외)", "amount_raw": "2만원", "premium_raw": "2,006", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD7237020"},
    {"row_id": None, "coverage_name_raw": "항암방사선·약물 치료비Ⅲ(암(기타피부암 및 갑상선암 제외))", "amount_raw": "300만원", "premium_raw": "3,318", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD7472010"},
    {"row_id": None, "coverage_name_raw": "항암방사선·약물 치료비Ⅲ(기타피부암 및 갑상선암)", "amount_raw": "300만원", "premium_raw": "72", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD7473010"},
    {"row_id": None, "coverage_name_raw": "[갱신형] 표적항암약물허가 치료비(1년50%)", "amount_raw": "1,000만원", "premium_raw": "400", "pay_term_raw": "10년갱신", "maturity_raw": "100세만기", "renewal_raw": "갱신형", "notes": "ZR7469010"},
    {"row_id": None, "coverage_name_raw": "혈전용해 치료비(뇌경색증)", "amount_raw": "200만원", "premium_raw": "166", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD7410010"},
    {"row_id": None, "coverage_name_raw": "혈전용해 치료비(급성심근경색증)", "amount_raw": "200만원", "premium_raw": None, "pay_term_raw": None, "maturity_raw": None, "renewal_raw": None, "notes": None},
    {"row_id": None, "coverage_name_raw": "상해 입원 수술비(당일입원 제외)", "amount_raw": "10만원", "premium_raw": "381", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD7108010"},
    {"row_id": None, "coverage_name_raw": "상해 통원 수술비(외래 및 당일입원)", "amount_raw": "10만원", "premium_raw": "321", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD7109010"},
    {"row_id": None, "coverage_name_raw": "질병 입원 수술비Ⅱ(당일입원 제외)", "amount_raw": "10만원", "premium_raw": "925", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD7367010"},
    {"row_id": None, "coverage_name_raw": "질병 통원 수술비Ⅱ(외래 및 당일입원)", "amount_raw": "10만원", "premium_raw": "1,130", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD7368010"},
    {"row_id": None, "coverage_name_raw": "암 수술비(유사암 제외)", "amount_raw": "500만원", "premium_raw": "9,450", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD7112010"},

    # Page 3 continuation
    {"row_id": None, "coverage_name_raw": "기타피부암 수술비", "amount_raw": "30만원", "premium_raw": "52", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD7113010"},
    {"row_id": None, "coverage_name_raw": "제자리암 수술비", "amount_raw": "30만원", "premium_raw": None, "pay_term_raw": None, "maturity_raw": None, "renewal_raw": None, "notes": None},
    {"row_id": None, "coverage_name_raw": "경계성종양 수술비", "amount_raw": "30만원", "premium_raw": None, "pay_term_raw": None, "maturity_raw": None, "renewal_raw": None, "notes": None},
    {"row_id": None, "coverage_name_raw": "갑상선암 수술비", "amount_raw": "30만원", "premium_raw": None, "pay_term_raw": None, "maturity_raw": None, "renewal_raw": None, "notes": None},
    {"row_id": None, "coverage_name_raw": "대장점막내암 수술비", "amount_raw": "30만원", "premium_raw": None, "pay_term_raw": None, "maturity_raw": None, "renewal_raw": None, "notes": None},
    {"row_id": None, "coverage_name_raw": "[갱신형] 암(특정암 제외) 다빈치로봇 수술비(1년 감액)", "amount_raw": "1,000만원", "premium_raw": "470", "pay_term_raw": "10년갱신", "maturity_raw": "100세만기", "renewal_raw": "갱신형", "notes": "ZR0022010"},
    {"row_id": None, "coverage_name_raw": "[갱신형] 특정암 다빈치로봇 수술비(1년 감액)", "amount_raw": "1,000만원", "premium_raw": "180", "pay_term_raw": "10년갱신", "maturity_raw": "100세만기", "renewal_raw": "갱신형", "notes": "ZR0023010"},
    {"row_id": None, "coverage_name_raw": "2대주요기관질병 관혈수술비Ⅱ(1년50%)", "amount_raw": "500만원", "premium_raw": "1,585", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD7371010"},
    {"row_id": None, "coverage_name_raw": "2대주요기관질병 비관혈수술비Ⅱ(1년50%)", "amount_raw": "500만원", "premium_raw": "1,070", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD7372010"},
    {"row_id": None, "coverage_name_raw": "상해 후유장해(3~100%)", "amount_raw": "1,000만원", "premium_raw": "540", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD7308010"},
    {"row_id": None, "coverage_name_raw": "상해 사망", "amount_raw": "1,000만원", "premium_raw": "560", "pay_term_raw": "20년납", "maturity_raw": "100세만기", "renewal_raw": None, "notes": "ZD1163010"},
    {"row_id": None, "coverage_name_raw": "질병 사망", "amount_raw": "1,000만원", "premium_raw": "6,000", "pay_term_raw": "20년납", "maturity_raw": "80세만기", "renewal_raw": None, "notes": "ZD2400010"},
]


def main():
    """Write manually extracted Samsung rows to CSV."""
    print("\n" + "=" * 80)
    print("STEP 3.9 (Samsung Manual Extract)")
    print("=" * 80 + "\n")

    # Add metadata to all rows
    for row in samsung_rows:
        row["insurer"] = "SAMSUNG"
        row["proposal_file"] = "삼성_가입설계서_2511.pdf"
        row["proposal_variant"] = None

    # Write CSV
    output_path = OUTPUT_DIR / "SAMSUNG_proposal_coverage_universe.csv"
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(samsung_rows)

    print(f"✅ Extracted {len(samsung_rows)} coverage rows from Samsung proposal")
    print(f"✅ Written to: {output_path}\n")

    # Print sample
    print("Sample rows (first 5):")
    print("-" * 80)
    for i, row in enumerate(samsung_rows[:5], 1):
        print(f"{i}. {row['coverage_name_raw']} | {row['amount_raw']} | {row['premium_raw']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
