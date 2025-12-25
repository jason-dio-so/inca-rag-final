# SESSION HANDOFF — STEP 33-β Premium API (SUSPENDED)

## Status
- State: 🚫 SUSPENDED (Intentionally paused)
- Reason: Customer clarification pending
- Resume allowed: ❌ NO (until customer reply)

---

## What This Is
This document freezes the Premium API investigation at STEP 33-β.
The issue is NOT a technical failure but an **external information gap**.

Any speculative debugging, workaround, or assumption-based change is strictly forbidden.

---

## Verified Facts (Evidence-Based)

### Implementation
- Frontend DEV trigger UI: ✅ Implemented
- Next.js API proxy routes: ✅ Working
- Adapter & parsing logic: ✅ Correct
- Simple / Onepage: Same behavior

### Observed Upstream Behavior
- Endpoints:
  - /public/prdata/prInfo
  - /public/prdata/prDetail
- Method: GET + query params
- Result:
  - HTTP 400
  - Response body: EMPTY
  - Server: nginx
- curl / browser / Next proxy → identical result

### Proven NOT the Cause
- ❌ Korean encoding issue
- ❌ customerNm required 여부
- ❌ CORS / proxy / routing
- ❌ UI trigger
- ❌ Header variation (UA, Referer, Accept)

---

## Root Cause (Confirmed)
Upstream API information provided by the customer is **insufficient or inaccurate**.

Likely missing one or more of:
- Correct Base URL
- Authentication / session / key
- Required parameters
- Valid success request example
- Environment distinction (test vs prod)

---

## Customer Clarification Requested
Reference document:

`docs/api/premium_api_customer_clarification.md`

Requested items:
- Confirmed Base URL
- Authentication or key requirements
- Full required parameter list
- A **known-working curl or URL example**
- Environment separation (test / prod)

---

## Hard Rules (Do NOT violate)
- ❌ No speculative fixes
- ❌ No temporary headers
- ❌ No mock success assumptions
- ❌ No fallback logic
- ❌ No "try this" experiments

This issue is frozen by design.

---

## Resume Conditions (ANY ONE required)
Do NOT resume unless customer provides at least one:

1. Working curl example
2. Authentication / header details
3. Corrected required parameters
4. Correct Base URL

---

## Resume Plan (Predefined)
Once resume condition is met:

- STEP 33-β-3: Live Success Verification
  - curl success
  - browser Network capture
  - SSOT update
  - Mark as "Verified (Live)"

---

## Priority
When resuming any Premium API work:
1. Read this file FIRST
2. Read STATUS.md
3. Read `docs/api/premium_api_customer_clarification.md`

END.
