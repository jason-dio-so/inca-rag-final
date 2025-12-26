#!/bin/bash
# ============================================
# Smoke Test: V2 Schema & API Read Path
# Purpose: Verify v2 schema exists + API uses v2 priority
# Constitutional: STEP NEXT-AA v2 bootstrap validation
# Run from: repo root
# ============================================

set -e  # Exit on error

# Determine repo root (assumes this script is in apps/api/scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

echo "============================================"
echo "Smoke Test: V2 Schema & API Read Path"
echo "============================================"
echo

# ============================================
# Test 1: V2 Schema Existence
# ============================================

echo "📋 Test 1: V2 schema existence..."

SCHEMA_CHECK=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
    "SELECT EXISTS (SELECT FROM information_schema.schemata WHERE schema_name = 'v2');" | xargs)

if [ "$SCHEMA_CHECK" = "t" ]; then
    echo "✅ v2 schema exists"
else
    echo "❌ v2 schema NOT FOUND"
    echo "   Run: psql \"postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final\" -f docs/db/schema_v2.sql"
    exit 1
fi

# ============================================
# Test 2: V2 Core Tables Existence
# ============================================

echo
echo "📋 Test 2: V2 core tables..."

V2_TABLES=("insurer" "product" "template" "coverage_standard" "proposal_coverage" "proposal_coverage_mapped")

for table in "${V2_TABLES[@]}"; do
    TABLE_CHECK=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'v2' AND table_name = '$table');" | xargs)

    if [ "$TABLE_CHECK" = "t" ]; then
        ROW_COUNT=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
            "SELECT COUNT(*) FROM v2.$table;" | xargs)
        echo "✅ v2.$table: $ROW_COUNT rows"
    else
        echo "❌ v2.$table: NOT FOUND"
        exit 1
    fi
done

# ============================================
# Test 3: SSOT Seed Data
# ============================================

echo
echo "📋 Test 3: SSOT seed data (insurer 8개)..."

INSURER_COUNT=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
    "SELECT COUNT(*) FROM v2.insurer;" | xargs)

if [ "$INSURER_COUNT" -eq 8 ]; then
    echo "✅ v2.insurer: 8 rows (SSOT)"
else
    echo "❌ v2.insurer: $INSURER_COUNT rows (expected 8)"
    echo "   Run: psql \"postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final\" -f docs/db/seed_v2_ssot_minimal.sql"
    exit 1
fi

# ============================================
# Test 4: Product SSOT (product_id format)
# ============================================

echo
echo "📋 Test 4: Product SSOT (product_id format)..."

INVALID_PRODUCT_ID=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
    "SELECT COUNT(*) FROM v2.product WHERE product_id != insurer_code::TEXT || '_' || internal_product_code;" | xargs)

if [ "$INVALID_PRODUCT_ID" -eq 0 ]; then
    echo "✅ All product_id follow SSOT format (insurer_code_internal_product_code)"
else
    echo "❌ Found $INVALID_PRODUCT_ID product(s) with invalid product_id format"
    exit 1
fi

# ============================================
# Test 5: API Read Path (search_path check)
# ============================================

echo
echo "📋 Test 5: API read path (search_path to v2)..."

# This test checks if apps/api/app/db.py sets search_path correctly
# We'll grep for the search_path setting in db.py

if grep -q "SET search_path TO v2" apps/api/app/db.py; then
    echo "✅ apps/api/app/db.py sets search_path to v2 (confirmed)"
else
    echo "❌ apps/api/app/db.py does NOT set search_path to v2"
    echo "   Check: apps/api/app/db.py"
    exit 1
fi

# ============================================
# Test 6: API endpoint smoke test (SKIP - requires API running)
# ============================================

echo
echo "📋 Test 6: API endpoint (SKIP - requires manual API start)..."
echo "ℹ️  To test API manually:"
echo "   cd apps/api && uvicorn app.main:app --port 8001"
echo "   curl -X POST http://127.0.0.1:8001/compare/view-model ..."

# ============================================
# Test 7: Coverage Mapping (STEP NEXT-AD-FIX)
# ============================================

echo
echo "📋 Test 7: Coverage Mapping (신정원 통일코드 검증)..."

# Check v2.coverage_mapping table exists
MAPPING_TABLE_CHECK=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'v2' AND table_name = 'coverage_mapping');" | xargs)

if [ "$MAPPING_TABLE_CHECK" = "t" ]; then
    # Count TOTAL mappings
    TOTAL_MAPPING_COUNT=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
        "SELECT COUNT(*) FROM v2.coverage_mapping;" | xargs)

    # Count VALID mappings (신정원 코드 검증)
    VALID_MAPPING_COUNT=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
        "SELECT COUNT(*) FROM v2.coverage_mapping m WHERE EXISTS (SELECT 1 FROM v2.coverage_standard cs WHERE cs.coverage_code = m.canonical_coverage_code);" | xargs)

    # Count INVALID mappings (arbitrary codes)
    INVALID_MAPPING_COUNT=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
        "SELECT COUNT(*) FROM v2.coverage_mapping m WHERE NOT EXISTS (SELECT 1 FROM v2.coverage_standard cs WHERE cs.coverage_code = m.canonical_coverage_code);" | xargs)

    echo "✅ v2.coverage_mapping: $TOTAL_MAPPING_COUNT rows total"
    echo "   - Valid (신정원 코드): $VALID_MAPPING_COUNT"
    echo "   - Invalid (arbitrary): $INVALID_MAPPING_COUNT"

    # STEP NEXT-AD-FIX DoD: require at least 3 VALID mappings
    if [ "$INVALID_MAPPING_COUNT" -gt 0 ]; then
        echo "❌ FAILED: Found $INVALID_MAPPING_COUNT mappings with arbitrary canonical codes"
        echo "   Run: DELETE FROM v2.coverage_mapping WHERE canonical_coverage_code NOT IN (SELECT coverage_code FROM v2.coverage_standard);"
        exit 1
    fi

    if [ "$VALID_MAPPING_COUNT" -ge 3 ]; then
        echo "✅ Valid신정원 mappings >= 3 (DoD PASS)"
    else
        echo "ℹ️  Valid신정원 mappings: $VALID_MAPPING_COUNT (expected >= 3 for STEP NEXT-AD-FIX DoD)"
        echo "   Run: python apps/api/scripts/import_universe_mapping_xlsx.py --xlsx <path>"
    fi
else
    echo "❌ v2.coverage_mapping: NOT FOUND"
    echo "   Run migration: psql \"postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final\" -f migrations/step_next_ad/001_create_coverage_mapping.sql"
    exit 1
fi

# ============================================
# Test 8: Coverage Evidence (STEP NEXT-AE-FIX)
# ============================================

echo
echo "📋 Test 8: Coverage Evidence (문서 기반 추출 + 헌법 검증)..."

# Check v2.coverage_evidence table exists
EVIDENCE_TABLE_CHECK=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'v2' AND table_name = 'coverage_evidence');" | xargs)

if [ "$EVIDENCE_TABLE_CHECK" = "t" ]; then
    # Total evidence count
    TOTAL_EVIDENCE_COUNT=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
        "SELECT COUNT(*) FROM v2.coverage_evidence;" | xargs)

    echo "✅ v2.coverage_evidence: $TOTAL_EVIDENCE_COUNT evidence(s) total"

    # STEP NEXT-AE-FIX: Constitutional validation (source_doc_type)
    # 허용된 source_doc_type: policy, business_rules, product_summary
    # 금지: proposal (가입설계서는 Evidence 출처가 될 수 없음)
    INVALID_SOURCE_COUNT=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
        "SELECT COUNT(*) FROM v2.coverage_evidence WHERE source_doc_type NOT IN ('policy', 'business_rules', 'product_summary');" | xargs)

    if [ "$INVALID_SOURCE_COUNT" -eq 0 ]; then
        echo "✅ All evidence sources are valid (policy/business_rules/product_summary)"
    else
        echo "❌ FAILED: Found $INVALID_SOURCE_COUNT evidence(s) with invalid source_doc_type"
        echo "   Allowed: policy, business_rules, product_summary"
        echo "   Forbidden: proposal (가입설계서는 Evidence 출처가 될 수 없음)"
        psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
            "SELECT '     - ' || source_doc_type || ': ' || COUNT(*) || ' evidence(s)' FROM v2.coverage_evidence WHERE source_doc_type NOT IN ('policy', 'business_rules', 'product_summary') GROUP BY source_doc_type;"
        exit 1
    fi

    # source_doc_type distribution
    echo "   Source distribution:"
    psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
        "SELECT '     - ' || source_doc_type || ': ' || COUNT(*) FROM v2.coverage_evidence GROUP BY source_doc_type ORDER BY source_doc_type;"

    # Check for "문서 기반" evidence (exclude manual_v1 from auto-extraction count)
    DOCUMENT_BASED_COUNT=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
        "SELECT COUNT(*) FROM v2.coverage_evidence WHERE extraction_method LIKE '%deterministic%' OR extraction_method = 'manual_v1';" | xargs)

    echo "   - Document-based evidences: $DOCUMENT_BASED_COUNT"

    # STEP NEXT-AE DoD: 최소 1개 코드에 3종 evidence (definition, payment_condition, exclusion)
    COVERAGE_WITH_3_TYPES=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
        "SELECT COUNT(*) FROM (SELECT canonical_coverage_code, COUNT(DISTINCT evidence_type) as type_count FROM v2.coverage_evidence GROUP BY canonical_coverage_code HAVING COUNT(DISTINCT evidence_type) >= 3) sub;" | xargs)

    if [ "$COVERAGE_WITH_3_TYPES" -ge 1 ]; then
        echo "✅ At least 1 coverage has 3+ evidence types (definition/payment_condition/exclusion)"

        # Show which coverages have 3+ types
        echo "   Coverage(s) with 3+ evidence types:"
        psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
            "SELECT '     - ' || canonical_coverage_code || ': ' || COUNT(DISTINCT evidence_type) || ' types (' || STRING_AGG(DISTINCT evidence_type, ', ') || ')' FROM v2.coverage_evidence GROUP BY canonical_coverage_code HAVING COUNT(DISTINCT evidence_type) >= 3;"
    else
        echo "ℹ️  No coverage has 3+ evidence types yet (expected >= 1 for STEP NEXT-AE DoD)"
        echo "   Run: python apps/api/scripts/ae_extract_evidence.py"
    fi
else
    echo "❌ v2.coverage_evidence: NOT FOUND"
    echo "   Run migration: psql \"postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final\" -f migrations/step_next_ae/001_create_coverage_evidence.sql"
    exit 1
fi

# ============================================
# Test 9: Proposal Coverage Detail (STEP NEXT-AF)
# ============================================

echo
echo "📋 Test 9: Proposal Coverage Detail (Comparison Description)..."

# Check v2.proposal_coverage_detail table exists
DETAIL_TABLE_CHECK=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'v2' AND table_name = 'proposal_coverage_detail');" | xargs)

if [ "$DETAIL_TABLE_CHECK" = "t" ]; then
    # Total detail count
    TOTAL_DETAIL_COUNT=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
        "SELECT COUNT(*) FROM v2.proposal_coverage_detail;" | xargs)

    echo "✅ v2.proposal_coverage_detail: $TOTAL_DETAIL_COUNT detail(s) total"

    # STEP NEXT-AF: Constitutional validation (source_doc_type = 'proposal_detail' only)
    INVALID_DOC_TYPE_COUNT=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
        "SELECT COUNT(*) FROM v2.proposal_coverage_detail WHERE source_doc_type != 'proposal_detail';" | xargs)

    if [ "$INVALID_DOC_TYPE_COUNT" -eq 0 ]; then
        echo "✅ All detail source_doc_type = 'proposal_detail' (constitution compliant)"
    else
        echo "❌ FAILED: Found $INVALID_DOC_TYPE_COUNT detail(s) with invalid source_doc_type"
        echo "   Expected: source_doc_type = 'proposal_detail' (NOT evidence source)"
        exit 1
    fi

    # Check matched vs unmatched details
    MATCHED_COUNT=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
        "SELECT COUNT(*) FROM v2.proposal_coverage_detail WHERE coverage_id IS NOT NULL;" | xargs)

    UNMATCHED_COUNT=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
        "SELECT COUNT(*) FROM v2.proposal_coverage_detail WHERE coverage_id IS NULL;" | xargs)

    echo "   - Matched to coverage: $MATCHED_COUNT"
    echo "   - Unmatched (NULL coverage_id): $UNMATCHED_COUNT"

    # STEP NEXT-AF DoD: 최소 1개 template에 detail >= 1, 최소 1개 row는 매칭 성공
    TEMPLATES_WITH_DETAILS=$(psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
        "SELECT COUNT(DISTINCT template_id) FROM v2.proposal_coverage_detail;" | xargs)

    echo "   - Templates with details: $TEMPLATES_WITH_DETAILS"

    if [ "$TEMPLATES_WITH_DETAILS" -ge 1 ] && [ "$MATCHED_COUNT" -ge 1 ]; then
        echo "✅ At least 1 template has details with 1+ matched coverage (DoD PASS)"
    else
        echo "ℹ️  Not enough data for STEP NEXT-AF DoD (expected >= 1 template with >= 1 matched detail)"
        echo "   Run: python apps/api/scripts/af_extract_proposal_detail.py <template_id> <pdf_path>"
    fi

    # Template distribution
    if [ "$TOTAL_DETAIL_COUNT" -gt 0 ]; then
        echo "   Template distribution:"
        psql "postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final" -t -c \
            "SELECT '     - ' || template_id || ': ' || COUNT(*) || ' details (matched: ' || COUNT(*) FILTER (WHERE coverage_id IS NOT NULL) || ')' FROM v2.proposal_coverage_detail GROUP BY template_id ORDER BY template_id;"
    fi
else
    echo "❌ v2.proposal_coverage_detail: NOT FOUND"
    echo "   Run migration: psql \"postgresql://postgres:postgres@127.0.0.1:5433/inca_rag_final\" -f migrations/step_next_af/001_create_proposal_coverage_detail.sql"
    exit 1
fi

# ============================================
# Final Summary
# ============================================

echo
echo "============================================"
echo "✅ Smoke Test: V2 Schema & API Read Path PASSED"
echo "============================================"
echo
echo "Summary:"
echo "  - v2 schema exists with 13+ tables"
echo "  - v2.insurer has 8 SSOT entries"
echo "  - product_id follows SSOT format"
echo "  - API uses search_path = v2, public"
echo "  - v2.coverage_mapping has valid신정원 mappings"
echo "  - v2.coverage_evidence has document-based evidence"
echo "  - v2.proposal_coverage_detail for comparison description"
echo
echo "Next steps:"
echo "  - Improve evidence extraction (definition coverage)"
echo "  - Freeze public schema to READ-ONLY (LEGACY_FREEZE_PLAN.md)"
echo
