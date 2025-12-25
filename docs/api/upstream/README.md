# Upstream Premium API Specifications

**Directory Purpose:** Store upstream Premium API specification files (source of truth)

---

## Required Files

Please add the following upstream API specification files to this directory:

### 1. Simple Compare API (간편비교)
**Filename:** `premium_simple_compare_spec.txt`
**Source:** 간편비교_api.txt (original specification)
**Status:** ⚠️ **PENDING** - File needs to be added

**How to add:**
```bash
cp "/path/to/간편비교_api.txt" \
   docs/api/upstream/premium_simple_compare_spec.txt
```

---

### 2. Onepage Compare API (한장비교)
**Filename:** `premium_onepage_compare_spec.txt`
**Source:** 한장비교_API.txt (original specification)
**Status:** ⚠️ **PENDING** - File needs to be added

**How to add:**
```bash
cp "/path/to/한장비교_API.txt" \
   docs/api/upstream/premium_onepage_compare_spec.txt
```

---

### 3. API Definitions (Optional)
**Filename:** `premium_api_definitions.xlsx`
**Source:** 장기상품비교추천 화면별 API 정의.xlsx
**Status:** ⚠️ **PENDING** - File needs to be added (if available)

**How to add:**
```bash
cp "/path/to/장기상품비교추천 화면별 API 정의.xlsx" \
   docs/api/upstream/premium_api_definitions.xlsx
```

---

## After Adding Files

Once the specification files are added:

1. **Update minimal spec:**
   ```bash
   # Update docs/api/premium_api_spec_minimal.md with actual details
   # from the upstream spec files
   ```

2. **Update implementation:**
   - `apps/web/src/lib/api/premium/types.ts` - Request/response interfaces
   - `apps/web/src/app/api/premium/*/route.ts` - Upstream endpoint paths
   - `apps/web/README.md` - Smoke test curl examples

3. **Verify alignment:**
   ```bash
   # All files must align with upstream specs:
   # upstream specs → types.ts → route.ts → README.md
   ```

---

## Constitutional Principle

**No confirmed payloads without actual specs.**

Until the actual specification files are added to this directory:
- Request schemas in `types.ts` remain placeholders
- Upstream paths in `route.ts` remain placeholders
- README smoke tests remain examples (not confirmed)

Once specs are added:
- Specs become SSOT (Single Source of Truth)
- All implementations must match specs exactly
- README smoke tests become executable confirmations

---

## Current Status

**Spec Files in Repo:** 0 / 2 required

- [ ] `premium_simple_compare_spec.txt`
- [ ] `premium_onepage_compare_spec.txt`
- [ ] `premium_api_definitions.xlsx` (optional)

**Next Action:** Add the upstream specification files to this directory.

---

**Last Updated:** 2025-12-25
**Related:** [../premium_api_spec_minimal.md](../premium_api_spec_minimal.md) (placeholder until specs added)
