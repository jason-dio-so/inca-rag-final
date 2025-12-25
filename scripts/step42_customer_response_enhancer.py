#!/usr/bin/env python3
"""
STEP 4.2 FINAL: Customer Response Enhancement (Structural UNMAPPED Handling)

Purpose:
- Enhance STEP 4.0 customer responses with Structural Notice Block
- Make structural UNMAPPED cases understandable (not failures)
- Guide customers to next actions without recommendations

Constitution Rules:
✅ PRIME results IMMUTABLE (STEP 3.11 untouched)
✅ Explanations IMMUTABLE (STEP 3.12 untouched)
✅ STEP 4.0 format preserved + Structural Notice added
✅ Pure presentation layer (표현 only)
❌ NO state changes
❌ NO result recalculation
❌ NO inference ("사실상 같다" banned)
❌ NO recommendations
❌ NO shinjeongwon code mentions in customer output

STEP 3.x = 판결문
STEP 3.12 = 이유서
STEP 4.0 = 표현 방식
STEP 4.2 = Structural UNMAPPED 표현 강화
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

# ============================================================================
# Configuration
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STRUCTURAL_CASES_CSV = PROJECT_ROOT / "data/step310_mapping/structural_unmapped/STRUCTURAL_UNMAPPED_CASES.csv"

# ============================================================================
# Structural Type Enums
# ============================================================================

class StructuralType(Enum):
    """Structural UNMAPPED types (from STEP 3.10-θ)"""
    S1_SPLIT = "S1_SPLIT"           # Subcategory split
    S2_COMPOSITE = "S2_COMPOSITE"    # Composite coverage
    S3_POLICY_ONLY = "S3_POLICY_ONLY"  # Policy-level only


class PRIMEState(Enum):
    """PRIME states (from STEP 3.11) - for reference only"""
    IN_UNIVERSE_COMPARABLE = "in_universe_comparable"
    IN_UNIVERSE_WITH_GAPS = "in_universe_with_gaps"
    IN_UNIVERSE_UNMAPPED = "in_universe_unmapped"
    OUT_OF_UNIVERSE = "out_of_universe"


# ============================================================================
# Customer Message Templates (Fixed)
# ============================================================================

STRUCTURAL_MESSAGES = {
    StructuralType.S1_SPLIT: """
이 담보는 보험사별로 세부 항목이 나뉘어 기재되어 있어
하나의 금액으로 단순 비교하기 어렵습니다.
""".strip(),

    StructuralType.S2_COMPOSITE: """
이 담보는 여러 보장 내용을 하나의 이름으로 묶어 제공됩니다.
포함된 보장 범위가 보험사마다 달라 직접 비교에 제한이 있습니다.
""".strip(),

    StructuralType.S3_POLICY_ONLY: """
이 담보는 가입설계서 요약 정보만으로는
보장 범위를 확정하기 어려워 약관 확인이 필요합니다.
""".strip()
}

COMMON_CONTEXT_MESSAGE = "현재 비교는 가입설계서 요약표 기준으로 이루어졌습니다."

NEXT_STEP_PROMPT = """
다음 중 어떤 정보를 더 확인해볼까요?

□ 특정 하위 담보만 선택해서 보기
□ 가입설계서 상세 보장 내용 확인
□ 약관 기준으로 비교 요청
""".strip()

# ============================================================================
# Structural UNMAPPED Metadata Loader
# ============================================================================

class StructuralMetadataLoader:
    """Load structural UNMAPPED metadata from STEP 3.10-θ"""

    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self._metadata: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        """Load structural cases CSV"""
        if not self.csv_path.exists():
            print(f"⚠️  Structural cases CSV not found: {self.csv_path}")
            return

        with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Use coverage_name_raw as key
                key = (row['insurer'], row['coverage_name_raw'])
                self._metadata[key] = {
                    'structural_type': row['structural_type'],
                    'group_key': row['group_key'],
                    'next_actions': row['next_actions'],
                    'effect_codes': row['effect_codes'],
                    'notes': row['notes']
                }

    def get_structural_type(self, insurer: str, coverage_name: str) -> Optional[str]:
        """Get structural type for a coverage"""
        key = (insurer, coverage_name)
        meta = self._metadata.get(key)
        return meta['structural_type'] if meta else None

    def get_metadata(self, insurer: str, coverage_name: str) -> Optional[Dict]:
        """Get full metadata for a coverage"""
        key = (insurer, coverage_name)
        return self._metadata.get(key)


# ============================================================================
# CustomerResponse v2 - Enhanced with Structural Notice
# ============================================================================

class CustomerResponseV2:
    """
    Enhanced Customer Response with Structural Notice Block

    Structure (4 sections):
    1. Summary Header (from STEP 4.0)
    2. Comparison Table (from STEP 4.0)
    3. Insurer Explanation Blocks (from STEP 4.0)
    4. Structural Notice Block (NEW in STEP 4.2) ← KEY ADDITION
    """

    def __init__(self):
        """Initialize enhancer with structural metadata"""
        self.metadata_loader = StructuralMetadataLoader(STRUCTURAL_CASES_CSV)
        print("✅ CustomerResponse v2 initialized with structural metadata")

    def enhance_response(self, base_response: str, comparison_results: List[Dict]) -> str:
        """
        Enhance base STEP 4.0 response with Structural Notice Block

        Args:
            base_response: STEP 4.0 formatted response
            comparison_results: List of comparison results with metadata

        Returns:
            Enhanced response with Structural Notice if applicable
        """
        # Check if any structural cases exist
        structural_cases = self._find_structural_cases(comparison_results)

        if not structural_cases:
            # No structural issues, return base response unchanged
            return base_response

        # Build Structural Notice Block
        notice_block = self._build_structural_notice(structural_cases)

        # Append notice block to base response
        enhanced_response = f"{base_response}\n\n{notice_block}"

        return enhanced_response

    def _find_structural_cases(self, comparison_results: List[Dict]) -> List[Dict]:
        """
        Find structural UNMAPPED cases in comparison results

        Display conditions (ANY of):
        - PRIME state = in_universe_with_gaps
        - mapping_status = UNMAPPED
        - structural_type ∈ {S1_SPLIT, S2_COMPOSITE, S3_POLICY_ONLY}
        """
        structural_cases = []

        for result in comparison_results:
            insurer = result.get('insurer', '')
            coverage_name = result.get('coverage_name', '')
            prime_state = result.get('prime_state', '')
            mapping_status = result.get('mapping_status', '')

            # Check structural metadata
            structural_type = self.metadata_loader.get_structural_type(insurer, coverage_name)

            # Display conditions
            should_display = (
                prime_state == PRIMEState.IN_UNIVERSE_WITH_GAPS.value or
                mapping_status == 'UNMAPPED' or
                structural_type in ['S1_SPLIT', 'S2_COMPOSITE', 'S3_POLICY_ONLY']
            )

            if should_display and structural_type:
                structural_cases.append({
                    'insurer': insurer,
                    'coverage_name': coverage_name,
                    'structural_type': structural_type,
                    'metadata': self.metadata_loader.get_metadata(insurer, coverage_name)
                })

        return structural_cases

    def _build_structural_notice(self, structural_cases: List[Dict]) -> str:
        """
        Build Structural Notice Block (Section 4)

        Format:
        ═══════════════════════════════════════════
        📋 담보 비교 안내
        ═══════════════════════════════════════════

        [Structural Type Message]

        [Common Context]

        [Next Step Prompt]
        """
        # Group by structural type
        by_type = {}
        for case in structural_cases:
            stype = case['structural_type']
            if stype not in by_type:
                by_type[stype] = []
            by_type[stype].append(case)

        # Build notice
        notice_lines = []
        notice_lines.append("═" * 50)
        notice_lines.append("📋 담보 비교 안내")
        notice_lines.append("═" * 50)
        notice_lines.append("")

        # Add structural type messages
        for stype_str in by_type.keys():
            try:
                stype = StructuralType(stype_str)
                message = STRUCTURAL_MESSAGES[stype]
                notice_lines.append(message)
                notice_lines.append("")
            except (ValueError, KeyError):
                continue

        # Add common context
        notice_lines.append(COMMON_CONTEXT_MESSAGE)
        notice_lines.append("")

        # Add next step prompt
        notice_lines.append(NEXT_STEP_PROMPT)

        return "\n".join(notice_lines)


# ============================================================================
# Pure Function Interface
# ============================================================================

def enhance_customer_response(
    base_response: str,
    comparison_results: List[Dict]
) -> str:
    """
    Pure function: enhance STEP 4.0 response with structural notices

    Args:
        base_response: STEP 4.0 formatted response
        comparison_results: List of comparison results

    Returns:
        Enhanced response (same input → same output)

    Constitutional Guarantees:
    - PRIME states unchanged
    - No result modification
    - No inference/recommendations
    - Pure presentation layer
    """
    enhancer = CustomerResponseV2()
    return enhancer.enhance_response(base_response, comparison_results)


# ============================================================================
# Example Usage & Validation
# ============================================================================

def generate_examples():
    """Generate example outputs for validation"""

    # Example 1: S1_SPLIT case (HANWHA - Da Vinci Robot Surgery)
    example1_results = [
        {
            'insurer': 'HANWHA',
            'coverage_name': '암(갑상선암및전립선암제외)다빈치로봇수술비(1회한)(갱신형)',
            'prime_state': 'in_universe_with_gaps',
            'mapping_status': 'UNMAPPED'
        }
    ]

    base_response1 = """
══════════════════════════════════════════════
📊 담보 비교 결과
══════════════════════════════════════════════

질의 담보: 다빈치로봇수술비
비교 대상: 2개 보험사

보험사별 비교
──────────────────────────────────────────────
HANWHA: 제한적 비교 가능
- 상태: 표준 코드 미대응
- 담보명: 암(갑상선암및전립선암제외)다빈치로봇수술비(1회한)(갱신형)
""".strip()

    print("=" * 70)
    print("Example 1: S1_SPLIT case")
    print("=" * 70)

    enhanced1 = enhance_customer_response(base_response1, example1_results)
    print(enhanced1)
    print("\n")

    # Example 2: S2_COMPOSITE case (HANWHA - 4대유사암)
    example2_results = [
        {
            'insurer': 'HANWHA',
            'coverage_name': '4대유사암진단비',
            'prime_state': 'in_universe_with_gaps',
            'mapping_status': 'UNMAPPED'
        }
    ]

    base_response2 = """
══════════════════════════════════════════════
📊 담보 비교 결과
══════════════════════════════════════════════

질의 담보: 유사암진단비
비교 대상: 1개 보험사

보험사별 비교
──────────────────────────────────────────────
HANWHA: 제한적 비교 가능
- 상태: 표준 코드 미대응
- 담보명: 4대유사암진단비
""".strip()

    print("=" * 70)
    print("Example 2: S2_COMPOSITE case")
    print("=" * 70)

    enhanced2 = enhance_customer_response(base_response2, example2_results)
    print(enhanced2)
    print("\n")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main execution - generate examples"""
    print("=" * 70)
    print("STEP 4.2: Customer Response Enhancement")
    print("=" * 70)
    print()

    generate_examples()

    print("=" * 70)
    print("✅ STEP 4.2 Examples Generated")
    print("=" * 70)


if __name__ == "__main__":
    main()
