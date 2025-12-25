#!/usr/bin/env python3
"""
STEP 3.10-θ: Structural UNMAPPED Processing Strategy (C3/C4/C7 only)

Purpose:
- Identify structural UNMAPPED cases (C3/C4/C7)
- Classify into S1/S2/S3 types
- Generate group keys (labeling only, no inference)
- Assign NextActions for future steps
- Create backlog for detailed table / policy layer work

Hard Constraints:
- ❌ NO UNMAPPED → MAPPED conversion
- ❌ NO shinjeongwon code inference
- ❌ NO coverage consolidation ("same coverage" claims)
- ❌ NO similarity/embedding/LLM
- ❌ NO PRIME state changes
- ❌ NO actual policy/detail table reading (backlog only)

Output:
- STRUCTURAL_UNMAPPED_CASES.csv
- STRUCTURAL_UNMAPPED_SUMMARY.md
- STRUCTURAL_BACKLOG.md
"""

import sys
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
from collections import Counter, defaultdict

# ============================================================================
# Configuration
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Inputs (read-only)
ETA2_MAPPING_CSV = PROJECT_ROOT / "data/step310_mapping/proposal_coverage_mapping_insurer_filtered__eta2.csv"
CAUSE_EFFECT_CSV = PROJECT_ROOT / "data/step310_mapping/unmapped_cause_effect_report.csv"
UNIVERSE_CSV = PROJECT_ROOT / "data/step39_coverage_universe/extracts/ALL_INSURERS_coverage_universe.csv"

# Outputs (new files only)
OUTPUT_DIR = PROJECT_ROOT / "data/step310_mapping/structural_unmapped"
CASES_CSV = OUTPUT_DIR / "STRUCTURAL_UNMAPPED_CASES.csv"
SUMMARY_MD = OUTPUT_DIR / "STRUCTURAL_UNMAPPED_SUMMARY.md"
BACKLOG_MD = OUTPUT_DIR / "STRUCTURAL_BACKLOG.md"

# ============================================================================
# Enums (Fixed)
# ============================================================================

# Structural Types
STRUCTURAL_TYPES = {
    "S1_SPLIT": "C3_SUBCATEGORY_SPLIT",           # Subcategory split
    "S2_COMPOSITE": "C4_COMPOSITE_COVERAGE",      # Composite coverage
    "S3_POLICY_ONLY": "C7_POLICY_LEVEL_ONLY"      # Policy-level only
}

# NextActions
NEXT_ACTIONS = {
    "A1_CREATE_GROUP_KEY": "Create group key for comparison grouping",
    "A2_REQUIRE_USER_DISAMBIGUATION": "User must choose specific subcategory",
    "A3_DEFER_TO_DETAIL_TABLE": "Requires detailed table evidence (STEP 4.x)",
    "A4_DEFER_TO_POLICY_LAYER": "Requires policy/business method evidence",
    "A5_MANUAL_REVIEW_QUEUE": "Human must define structure"
}

# Effect Codes (Fixed)
EFFECT_CODES = {
    "E2_LIMITED_COMPARISON": "Comparison limited without detailed info",
    "E3_EXPLANATION_REQUIRED": "User explanation required",
    "E5_STRUCTURAL_DIFFERENCE": "Structural difference between insurers"
}

# ============================================================================
# Core Functions
# ============================================================================

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace (multiple spaces → one space)"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())


def extract_prefix_pattern(coverage_name: str) -> str:
    """
    Extract prefix pattern for group key (deterministic rules only)
    No inference, no similarity - simple string pattern matching

    Rules:
    - Keep Korean/English/numbers
    - Keep parentheses content
    - Extract up to first parenthesis (if exists)
    - If extraction fails, return NULL
    """
    if not coverage_name:
        return ""

    # Normalize whitespace first
    normalized = normalize_whitespace(coverage_name)

    # Extract prefix (up to first open parenthesis)
    match = re.match(r'^([^(]+)', normalized)
    if match:
        prefix = match.group(1).strip()
        return prefix if prefix else ""

    # If no parenthesis, use full name
    return normalized


def load_cause_effect_mapping() -> Dict[str, Dict]:
    """Load cause-effect report to map coverage names to causes"""
    mapping = {}

    if not CAUSE_EFFECT_CSV.exists():
        print(f"⚠️  Warning: Cause-effect report not found, will infer from eta2 only")
        return mapping

    with open(CAUSE_EFFECT_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['insurer'], row['coverage_name_raw'])
            if key not in mapping:
                mapping[key] = {
                    'cause_codes': row['cause_codes'],
                    'effect_codes': row['effect_codes'],
                    'evidence_note': row.get('evidence_note', '')
                }

    return mapping


def classify_structural_type(cause_codes: str) -> str:
    """
    Classify structural type based on cause codes
    Priority: C7 > C4 > C3
    """
    if not cause_codes:
        return ""

    codes = set(cause_codes.split('|'))

    # Priority order
    if 'C7_POLICY_LEVEL_ONLY' in codes:
        return 'S3_POLICY_ONLY'
    elif 'C4_COMPOSITE_COVERAGE' in codes:
        return 'S2_COMPOSITE'
    elif 'C3_SUBCATEGORY_SPLIT' in codes:
        return 'S1_SPLIT'
    else:
        return ""  # Not a structural case


def assign_next_actions(structural_type: str, group_key: str) -> List[str]:
    """
    Assign NextActions based on structural type and group key

    Rules:
    - S1_SPLIT: A1 + A2
    - S2_COMPOSITE: A1 + A2 + A3
    - S3_POLICY_ONLY: A4 (+ A5 if needed)
    - If group_key is NULL: add A5
    """
    actions = []

    if structural_type == 'S1_SPLIT':
        actions.extend(['A1_CREATE_GROUP_KEY', 'A2_REQUIRE_USER_DISAMBIGUATION'])

    elif structural_type == 'S2_COMPOSITE':
        actions.extend(['A1_CREATE_GROUP_KEY', 'A2_REQUIRE_USER_DISAMBIGUATION', 'A3_DEFER_TO_DETAIL_TABLE'])

    elif structural_type == 'S3_POLICY_ONLY':
        actions.append('A4_DEFER_TO_POLICY_LAYER')

    # Add A5 if group_key is NULL
    if not group_key and structural_type in ['S1_SPLIT', 'S2_COMPOSITE']:
        if 'A5_MANUAL_REVIEW_QUEUE' not in actions:
            actions.append('A5_MANUAL_REVIEW_QUEUE')

    return actions


def assign_effect_codes(structural_type: str) -> List[str]:
    """
    Assign effect codes based on structural type

    All: E3_EXPLANATION_REQUIRED
    S1/S2: + E2_LIMITED_COMPARISON
    S3: + E5_STRUCTURAL_DIFFERENCE
    """
    effects = ['E3_EXPLANATION_REQUIRED']

    if structural_type in ['S1_SPLIT', 'S2_COMPOSITE']:
        effects.append('E2_LIMITED_COMPARISON')

    elif structural_type == 'S3_POLICY_ONLY':
        effects.append('E5_STRUCTURAL_DIFFERENCE')

    return effects


# ============================================================================
# Main Processing
# ============================================================================

def process_structural_unmapped():
    """Main processing function"""
    print("=" * 80)
    print("STEP 3.10-θ: Structural UNMAPPED Processing Strategy")
    print("=" * 80)

    # Validate inputs
    print("\n[1] Validating inputs...")
    if not ETA2_MAPPING_CSV.exists():
        raise FileNotFoundError(f"eta2 mapping CSV not found: {ETA2_MAPPING_CSV}")
    print(f"   ✅ eta2 mapping: {ETA2_MAPPING_CSV.name}")

    # Load cause-effect mapping
    print("\n[2] Loading cause-effect mapping...")
    cause_effect_map = load_cause_effect_mapping()
    print(f"   ✅ Loaded {len(cause_effect_map)} cause-effect entries")

    # Load eta2 mapping and filter UNMAPPED
    print("\n[3] Loading eta2 mapping results...")
    unmapped_rows = []

    with open(ETA2_MAPPING_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['mapping_status'] == 'UNMAPPED':
                unmapped_rows.append(row)

    print(f"   ✅ Found {len(unmapped_rows)} UNMAPPED entries")

    # Filter for structural cases (C3/C4/C7)
    print("\n[4] Filtering structural cases (C3/C4/C7)...")
    structural_cases = []

    for row in unmapped_rows:
        key = (row['insurer'], row['coverage_name_raw'])

        # Get cause codes from cause-effect report
        cause_info = cause_effect_map.get(key, {})
        cause_codes = cause_info.get('cause_codes', '')

        # Classify structural type
        structural_type = classify_structural_type(cause_codes)

        if structural_type:
            # Generate case_id
            case_id = f"{row['insurer']}-{row['proposal_variant']}-{row['row_id']}"

            # Generate group key (for S1/S2 only)
            group_key = ""
            if structural_type in ['S1_SPLIT', 'S2_COMPOSITE']:
                group_key = extract_prefix_pattern(row['coverage_name_raw'])

            # Assign NextActions
            next_actions = assign_next_actions(structural_type, group_key)

            # Assign effect codes
            effect_codes = assign_effect_codes(structural_type)

            # Build case record
            case = {
                'case_id': case_id,
                'insurer': row['insurer'],
                'proposal_file': row['proposal_file'],
                'proposal_variant': row['proposal_variant'],
                'row_id': row['row_id'],
                'coverage_name_raw': row['coverage_name_raw'],
                'amount_raw': '',  # Will fill from universe if needed
                'premium_raw': '',
                'pay_term_raw': '',
                'maturity_raw': '',
                'cause_codes': cause_codes,
                'structural_type': structural_type,
                'group_key': group_key,
                'next_actions': '|'.join(next_actions),
                'effect_codes': '|'.join(effect_codes),
                'evidence_hint': '',  # TODO: extract from profiles if needed
                'notes': f"Classified as {structural_type}"
            }

            structural_cases.append(case)

    print(f"   ✅ Identified {len(structural_cases)} structural cases")

    # Load universe data to enrich with amount/premium info
    print("\n[5] Enriching with universe data...")
    universe_map = {}
    with open(UNIVERSE_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['insurer'], row['proposal_variant'], row['row_id'])
            universe_map[key] = row

    for case in structural_cases:
        key = (case['insurer'], case['proposal_variant'], case['row_id'])
        if key in universe_map:
            universe_row = universe_map[key]
            case['amount_raw'] = universe_row.get('amount_raw', '')
            case['premium_raw'] = universe_row.get('premium_raw', '')
            case['pay_term_raw'] = universe_row.get('pay_term_raw', '')
            case['maturity_raw'] = universe_row.get('maturity_raw', '')

    print(f"   ✅ Enriched {len(structural_cases)} cases")

    # Save results
    print("\n[6] Saving results...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save CSV
    with open(CASES_CSV, 'w', newline='', encoding='utf-8-sig') as f:
        fieldnames = [
            'case_id', 'insurer', 'proposal_file', 'proposal_variant', 'row_id',
            'coverage_name_raw', 'amount_raw', 'premium_raw', 'pay_term_raw', 'maturity_raw',
            'cause_codes', 'structural_type', 'group_key', 'next_actions', 'effect_codes',
            'evidence_hint', 'notes'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(structural_cases)

    print(f"   ✅ Saved: {CASES_CSV.name}")

    # Generate reports
    print("\n[7] Generating reports...")
    generate_summary_report(structural_cases)
    generate_backlog_report(structural_cases)

    print("\n" + "=" * 80)
    print("✅ STEP 3.10-θ COMPLETE")
    print("=" * 80)

    # Print summary stats
    print_summary_stats(structural_cases)


# ============================================================================
# Report Generation
# ============================================================================

def generate_summary_report(cases: List[Dict]):
    """Generate STRUCTURAL_UNMAPPED_SUMMARY.md"""

    # Calculate stats
    total_cases = len(cases)
    type_counts = Counter([c['structural_type'] for c in cases])
    group_key_success = len([c for c in cases if c['group_key']])
    group_key_rate = group_key_success / total_cases * 100 if total_cases > 0 else 0

    # NextActions distribution
    action_counter = Counter()
    for case in cases:
        actions = case['next_actions'].split('|')
        for action in actions:
            action_counter[action] += 1

    report = f"""# STEP 3.10-θ Structural UNMAPPED Summary

**Generated**: {datetime.now().isoformat()}

---

## Overview

- **Total Structural Cases**: {total_cases}
- **Group Key Success Rate**: {group_key_success}/{total_cases} ({group_key_rate:.1f}%)

---

## Structural Type Distribution

| Type | Count | Percentage |
|------|-------|------------|
"""

    for stype in ['S1_SPLIT', 'S2_COMPOSITE', 'S3_POLICY_ONLY']:
        count = type_counts[stype]
        pct = count / total_cases * 100 if total_cases > 0 else 0
        desc = STRUCTURAL_TYPES[stype]
        report += f"| {stype} | {count} | {pct:.1f}% |\n"

    report += f"""
---

## NextAction Distribution

| Action | Count | Description |
|--------|-------|-------------|
"""

    for action in sorted(action_counter.keys()):
        count = action_counter[action]
        desc = NEXT_ACTIONS.get(action, "")
        report += f"| {action} | {count} | {desc} |\n"

    report += f"""
---

## Per-Insurer Breakdown

| Insurer | Total | S1 | S2 | S3 |
|---------|-------|----|----|-----|
"""

    insurer_counts = defaultdict(lambda: {'total': 0, 'S1_SPLIT': 0, 'S2_COMPOSITE': 0, 'S3_POLICY_ONLY': 0})
    for case in cases:
        ins = case['insurer']
        insurer_counts[ins]['total'] += 1
        insurer_counts[ins][case['structural_type']] += 1

    for insurer in sorted(insurer_counts.keys()):
        counts = insurer_counts[insurer]
        report += f"| {insurer} | {counts['total']} | {counts['S1_SPLIT']} | {counts['S2_COMPOSITE']} | {counts['S3_POLICY_ONLY']} |\n"

    report += f"""
---

## Files Generated

1. **Cases CSV**: `{CASES_CSV.name}`
2. **Summary Report**: `{SUMMARY_MD.name}`
3. **Backlog Report**: `{BACKLOG_MD.name}`

---

## Constitutional Compliance

- ✅ No UNMAPPED → MAPPED conversion
- ✅ No shinjeongwon code inference
- ✅ No coverage consolidation
- ✅ No similarity/embedding/LLM
- ✅ PRIME state unchanged
- ✅ Backlog only (no actual policy reading)

---

**Status**: ✅ COMPLETE
"""

    SUMMARY_MD.write_text(report, encoding='utf-8')
    print(f"   ✅ Summary report: {SUMMARY_MD.name}")


def generate_backlog_report(cases: List[Dict]):
    """Generate STRUCTURAL_BACKLOG.md for future steps"""

    # Group by NextAction
    action_cases = defaultdict(list)
    for case in cases:
        actions = case['next_actions'].split('|')
        for action in actions:
            action_cases[action].append(case)

    report = f"""# STEP 3.10-θ Structural UNMAPPED Backlog

**Generated**: {datetime.now().isoformat()}

This document lists future work items for handling structural UNMAPPED cases.

---

## A3_DEFER_TO_DETAIL_TABLE ({len(action_cases['A3_DEFER_TO_DETAIL_TABLE'])} cases)

**Requirement**: Extract evidence from detailed proposal tables (STEP 4.x)

**Cases**:
"""

    for case in action_cases.get('A3_DEFER_TO_DETAIL_TABLE', []):
        report += f"- [{case['case_id']}] {case['insurer']} - {case['coverage_name_raw']}\n"

    report += f"""
**Next Step**: Implement detailed table parser for composite coverage extraction

---

## A4_DEFER_TO_POLICY_LAYER ({len(action_cases['A4_DEFER_TO_POLICY_LAYER'])} cases)

**Requirement**: Policy/business method document analysis

**Cases**:
"""

    for case in action_cases.get('A4_DEFER_TO_POLICY_LAYER', []):
        report += f"- [{case['case_id']}] {case['insurer']} - {case['coverage_name_raw']}\n"

    report += f"""
**Next Step**: Policy document ingestion pipeline (약관/사업방법서 layer)

---

## A5_MANUAL_REVIEW_QUEUE ({len(action_cases['A5_MANUAL_REVIEW_QUEUE'])} cases)

**Requirement**: Human structural definition needed

**Cases**:
"""

    for case in action_cases.get('A5_MANUAL_REVIEW_QUEUE', []):
        report += f"- [{case['case_id']}] {case['insurer']} - {case['coverage_name_raw']}\n"

    report += f"""
**Next Step**: Admin UI for manual structure definition

---

## A2_REQUIRE_USER_DISAMBIGUATION ({len(action_cases['A2_REQUIRE_USER_DISAMBIGUATION'])} cases)

**Requirement**: User query refinement at compare-time

**Example Patterns**:
"""

    # Show sample group keys
    group_keys = defaultdict(list)
    for case in action_cases.get('A2_REQUIRE_USER_DISAMBIGUATION', []):
        if case['group_key']:
            group_keys[case['group_key']].append(case)

    for group_key in sorted(group_keys.keys())[:5]:  # Show top 5
        report += f"\n**Group: {group_key}**\n"
        for case in group_keys[group_key][:3]:  # Show 3 examples per group
            report += f"- {case['insurer']}: {case['coverage_name_raw']}\n"

    report += f"""
**Next Step**: Compare API query parameter enhancement (subcategory selection)

---

## Implementation Priority

1. **High**: A3 (Detailed table parser) - enables S2_COMPOSITE resolution
2. **Medium**: A2 (Query refinement) - improves UX for S1_SPLIT cases
3. **Medium**: A4 (Policy layer) - enables S3_POLICY_ONLY resolution
4. **Low**: A5 (Manual review) - case-by-case handling

---

**Total Backlog Items**: {len(cases)}
"""

    BACKLOG_MD.write_text(report, encoding='utf-8')
    print(f"   ✅ Backlog report: {BACKLOG_MD.name}")


def print_summary_stats(cases: List[Dict]):
    """Print summary statistics to stdout"""
    total = len(cases)
    type_counts = Counter([c['structural_type'] for c in cases])

    print(f"\n📊 SUMMARY STATISTICS:")
    print(f"   Total structural cases: {total}")
    print(f"\n   Structural Types:")
    print(f"      S1_SPLIT:      {type_counts['S1_SPLIT']:>2}")
    print(f"      S2_COMPOSITE:  {type_counts['S2_COMPOSITE']:>2}")
    print(f"      S3_POLICY_ONLY: {type_counts['S3_POLICY_ONLY']:>2}")

    group_key_success = len([c for c in cases if c['group_key']])
    print(f"\n   Group Keys:")
    print(f"      Generated: {group_key_success}/{total} ({group_key_success/total*100:.1f}%)")

    print(f"\n   Files:")
    print(f"      {CASES_CSV.relative_to(PROJECT_ROOT)}")
    print(f"      {SUMMARY_MD.relative_to(PROJECT_ROOT)}")
    print(f"      {BACKLOG_MD.relative_to(PROJECT_ROOT)}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main execution"""
    try:
        process_structural_unmapped()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
