# Premium API Customer Clarification Request

**Date:** 2025-12-25
**Status:** Awaiting Customer Response
**Issue:** Upstream API returns 400 with empty body

---

## 1. Observed Behavior

### Test Environment
- **Date/Time:** 2025-12-25 07:43 GMT
- **Test Methods:** Next.js proxy, curl, browser DevTools
- **Test Conditions:** Multiple header configurations, parameter variations

### Actual Upstream Response
```
HTTP/1.1 400 Bad Request
Server: nginx
Content-Type: application/json
Content-Length: 0
Date: Thu, 25 Dec 2025 07:43:13 GMT

(empty body)
```

---

## 2. Attempted API Calls

### prInfo (간편비교)
**URL Tested:**
```
https://new-prod.greenlight.direct/public/prdata/prInfo?baseDt=20251225&birthday=19760101&customerNm=Hong&sex=1&age=50
```

**Result:** 400 Bad Request, empty body

### prDetail (한장비교)
**URL Tested:**
```
https://new-prod.greenlight.direct/public/prdata/prDetail?baseDt=20251225&birthday=19760101&customerNm=Hong&sex=1&age=50
```

**Result:** 400 Bad Request, empty body

---

## 3. Variations Tested (All Failed with Same 400)

| Test Case | customerNm | Other Changes | Result |
|-----------|------------|---------------|--------|
| Original | 홍길동 (Korean) | - | 400 empty |
| ASCII | Hong | - | 400 empty |
| Omitted | (none) | - | 400 empty |
| Browser Headers | Hong | User-Agent, Referer, Accept-Language | 400 empty |

**Headers Tested (no effect):**
- `User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36`
- `Accept: application/json, text/plain, */*`
- `Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7`
- `Referer: https://new-prod.greenlight.direct/`
- `Cache-Control: no-cache`

---

## 4. Next.js Terminal Log Evidence

```
[Premium Simple] upstreamFullUrl: https://new-prod.greenlight.direct/public/prdata/prInfo?baseDt=20251225&birthday=19760101&customerNm=Hong&sex=1&age=50
[Premium Simple] Upstream Error Meta: {
  status: 400,
  statusText: '',
  url: 'https://new-prod.greenlight.direct/public/prdata/prInfo?baseDt=20251225&birthday=19760101&customerNm=Hong&sex=1&age=50',
  contentType: 'application/json',
  contentLength: '0',
  server: 'nginx',
  date: 'Thu, 25 Dec 2025 07:43:13 GMT',
  bodyLen: 0
}
[Premium Simple] Upstream Error Body (first 800):
```

---

## 5. Customer Clarification Needed

### Required Information

1. **Correct Base URL / Environment**
   - Is `https://new-prod.greenlight.direct` the correct production URL?
   - Are there alternative endpoints (staging, test, production domains)?

2. **Authentication Requirements**
   - API Key required? If yes, where to include (header, query param)?
   - Session cookie required? If yes, how to obtain?
   - IP whitelist? If yes, what IPs are allowed?

3. **Required Headers**
   - Are there mandatory HTTP headers beyond basic GET request?
   - Example: `X-API-Key`, `Authorization`, `X-Request-ID`, etc.

4. **Required Query Parameters**
   - Are there additional mandatory parameters not in spec?
   - Example: `apiKey`, `sessionId`, `clientId`, etc.

5. **Working Sample Request**
   - Provide curl command that successfully returns 200 OK
   - Provide Postman collection export
   - Provide actual successful request/response log

6. **Access Restrictions**
   - WAF/firewall rules?
   - Rate limiting policy?
   - Allowed user agents or referers?
   - Geographic restrictions?

---

## 6. Specification Reference

**Current Spec Document:** `docs/api/premium_api_spec.md`

**Spec States (SSOT):**
- Method: GET
- Parameters: baseDt, birthday, customerNm, sex, age
- Authentication: "Public API - no authentication required" (per spec)

**Discrepancy:**
Spec indicates public access, but actual behavior suggests authentication or additional requirements.

---

## 7. Impact

**Current Status:**
- Premium API integration blocked
- Cannot proceed without clarification
- All client-side/proxy-side implementations verified correct

**Next Steps:**
- Await customer response with correct access method
- Update `docs/api/premium_api_spec.md` with verified information
- Resume integration after receiving working sample

---

**Contact:** Please provide clarification via email or update specification document with correct access requirements.
