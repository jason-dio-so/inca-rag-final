# STEP 6-B: Confirm Function Sealing Evidence

**Date**: 2025-12-23
**Purpose**: Prove `confirm_candidate_to_entity()` is NOT called by pipeline (manual-only)

---

## 1. Code Search Evidence

**Command**: `rg "confirm_candidate_to_entity" -n --type py --type sql`

**Results**:
```
migrations/step6b/001_create_candidate_tables.sql:271:CREATE OR REPLACE FUNCTION confirm_candidate_to_entity(p_candidate_id INTEGER)
migrations/step6b/001_create_candidate_tables.sql:313:COMMENT ON FUNCTION confirm_candidate_to_entity IS 'Confirm resolved candidate to production chunk_entity (STEP 6-B). Enforces FK and prevents duplicates.';
migrations/step6b/001_create_candidate_tables.sql:317:-- DROP FUNCTION IF EXISTS confirm_candidate_to_entity(INTEGER);
```

**Analysis**:
✅ **NO Python code calls `confirm_candidate_to_entity()`**
✅ Function only exists in migration SQL (definition + comment + rollback)
✅ Repository layer (`apps/api/app/ingest_llm/repository.py`) does NOT call confirm function

**Constitutional Compliance**: ✅ VERIFIED
- Confirm function is MANUAL-ONLY (no automatic calls from pipeline)
- Candidate storage ends at repository.insert_candidate() + resolver.update_result()
- Production (`chunk_entity`) remains untouched by automated pipeline

---

## 2. Repository Layer Contract

**File**: `apps/api/app/ingest_llm/repository.py`

**Methods Implemented**:
1. `insert_candidate()` - Insert into `chunk_entity_candidate` (NOT `chunk_entity`)
2. `update_resolver_result()` - Update candidate status (NOT production)
3. `get_pending_candidates()` - Read candidates for processing
4. `get_metrics()` - Calculate statistics

**Methods NOT Implemented** (Constitutional Prohibition):
- ❌ `confirm_to_production()` - FORBIDDEN (would violate manual-only principle)
- ❌ Any method calling SQL function `confirm_candidate_to_entity()`

**Code Grep Verification**:
```bash
$ grep -n "confirm" apps/api/app/ingest_llm/repository.py
# Result: No matches
```

✅ Repository does NOT contain any confirm logic

---

## 3. Pipeline Contract (When Implemented)

**File**: `apps/api/app/ingest_llm/pipeline.py` (pending implementation)

**Required Contract**:
```python
class IngestionPipeline:
    """
    E2E pipeline for LLM-assisted candidate generation.

    Constitutional Guarantee:
    - Pipeline ends at candidate storage (resolver_status updated)
    - NO automatic confirmation to production
    - Confirm is MANUAL-ONLY via admin CLI/script
    """

    def run(self, chunks: List[Chunk]) -> PipelineReport:
        # Steps:
        # 1. Prefilter
        # 2. LLM candidate generation
        # 3. Resolver
        # 4. Validator
        # 5. Repository.insert_candidate()  # STOPS HERE
        # 6. ❌ FORBIDDEN: confirm_candidate_to_entity()

        # Return report only (no production writes)
        return PipelineReport(...)
```

**Enforcement**: Code review required before merge (human verification)

---

## 4. Manual Confirmation Workflow (Future)

**Tools** (to be created in future admin CLI):

```python
# admin_tools/confirm_candidates.py (NOT IMPLEMENTED YET)
"""
Manual admin tool for confirming resolved candidates to production.

Usage:
    python admin_tools/confirm_candidates.py --candidate-id 123
    python admin_tools/confirm_candidates.py --batch-file candidates.csv

Requires:
    - Admin credentials
    - Manual review of resolver_status=resolved
    - FK verification before confirm
"""
```

**Database Function Call** (admin-only):
```sql
-- Manual execution via psql (admin user)
SELECT confirm_candidate_to_entity(123);  -- Explicit candidate_id
```

**Constitutional Gates in Function** (from migration):
1. ✅ `resolver_status = 'resolved'` required
2. ✅ `resolved_coverage_code IS NOT NULL` required
3. ✅ FK existence verified: `coverage_code IN coverage_standard`
4. ✅ Duplicate prevention: `ON CONFLICT DO NOTHING`

---

## 5. Additional Safeguards (Optional Enhancement)

### Option A: Add Approval Column (Recommended)

**Migration Hotfix** (if DB available):
```sql
ALTER TABLE chunk_entity_candidate
ADD COLUMN confirmation_approved_by VARCHAR(100),
ADD COLUMN confirmation_approved_at TIMESTAMP;

-- Update function to require approval
CREATE OR REPLACE FUNCTION confirm_candidate_to_entity(p_candidate_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_candidate RECORD;
BEGIN
    -- Fetch candidate with approval check
    SELECT * INTO v_candidate
    FROM chunk_entity_candidate
    WHERE candidate_id = p_candidate_id
      AND resolver_status = 'resolved'
      AND resolved_coverage_code IS NOT NULL
      AND confirmation_approved_by IS NOT NULL;  -- NEW GATE

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Candidate % not found, not resolved, or not approved', p_candidate_id;
    END IF;

    -- ... rest of function ...
END;
$$ LANGUAGE plpgsql;
```

**Impact**: Pipeline can NEVER set `confirmation_approved_by` (manual-only field)

### Option B: Schema-Level Permissions

**PostgreSQL Roles** (if DB available):
```sql
-- Create admin role for confirms
CREATE ROLE inca_admin;
GRANT EXECUTE ON FUNCTION confirm_candidate_to_entity TO inca_admin;

-- Application role (pipeline) does NOT have permission
CREATE ROLE inca_pipeline;
REVOKE EXECUTE ON FUNCTION confirm_candidate_to_entity FROM inca_pipeline;
```

**Impact**: Even if code called function, database would reject (permission denied)

---

## 6. Conclusion

**Sealing Status**: ✅ **CONFIRMED**

| Layer | Mechanism | Status |
|-------|-----------|--------|
| Code | No Python calls to confirm function | ✅ Verified (ripgrep) |
| Repository | No confirm methods implemented | ✅ Verified (grep) |
| Pipeline | Contract specifies manual-only | ✅ Documented (pending impl) |
| Database | Function requires resolved status + FK | ✅ Implemented (migration) |

**Risk Level**: **LOW**
- Multiple layers prevent accidental auto-confirm
- Code review required for any changes touching confirm logic
- Database gates prevent invalid confirmations even if called

**Recommendation**: Proceed with Phase 2 implementation (Validator) with current safeguards.

**Optional Enhancement**: Add `confirmation_approved_by` column when DB becomes available (deferred to deployment phase).

---

**Document Status**: Sealing evidence complete - NO auto-confirm in codebase ✅
