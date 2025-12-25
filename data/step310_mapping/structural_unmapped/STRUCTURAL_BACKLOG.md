# STEP 3.10-θ Structural UNMAPPED Backlog

**Generated**: 2025-12-26T00:45:58.841146

This document lists future work items for handling structural UNMAPPED cases.

---

## A3_DEFER_TO_DETAIL_TABLE (5 cases)

**Requirement**: Extract evidence from detailed proposal tables (STEP 4.x)

**Cases**:
- [HANWHA--8.0] HANWHA - 4대유사암진단비
- [HANWHA--9.0] HANWHA - - 4대유사암진단비(기타피부암)
- [HANWHA--10.0] HANWHA - - 4대유사암진단비(제자리암)
- [HANWHA--11.0] HANWHA - - 4대유사암진단비(경계성종양)
- [HANWHA--12.0] HANWHA - - 4대유사암진단비(갑상선암)

**Next Step**: Implement detailed table parser for composite coverage extraction

---

## A4_DEFER_TO_POLICY_LAYER (0 cases)

**Requirement**: Policy/business method document analysis

**Cases**:

**Next Step**: Policy document ingestion pipeline (약관/사업방법서 layer)

---

## A5_MANUAL_REVIEW_QUEUE (0 cases)

**Requirement**: Human structural definition needed

**Cases**:

**Next Step**: Admin UI for manual structure definition

---

## A2_REQUIRE_USER_DISAMBIGUATION (10 cases)

**Requirement**: User query refinement at compare-time

**Example Patterns**:

**Group: - 4대유사암진단비**
- HANWHA: - 4대유사암진단비(기타피부암)
- HANWHA: - 4대유사암진단비(제자리암)
- HANWHA: - 4대유사암진단비(경계성종양)

**Group: 4대유사암진단비**
- HANWHA: 4대유사암진단비

**Group: 갑상선암및전립선암다빈치로봇수술비**
- HANWHA: 갑상선암및전립선암다빈치로봇수술비(1회한)(갱신형)

**Group: 다빈치로봇 갑상선암 및 전립선암수술비**
- KB: 다빈치로봇 갑상선암 및 전립선암수술비(최초1회한)(갱신형)

**Group: 다빈치로봇 암수술비**
- KB: 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)

**Next Step**: Compare API query parameter enhancement (subcategory selection)

---

## Implementation Priority

1. **High**: A3 (Detailed table parser) - enables S2_COMPOSITE resolution
2. **Medium**: A2 (Query refinement) - improves UX for S1_SPLIT cases
3. **Medium**: A4 (Policy layer) - enables S3_POLICY_ONLY resolution
4. **Low**: A5 (Manual review) - case-by-case handling

---

**Total Backlog Items**: 10
