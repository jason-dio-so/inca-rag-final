/**
 * Premium API Adapter (STEP 32 - SSOT for Mapping)
 *
 * Constitutional Principles:
 * - basePremium = monthlyPremSum (ONLY)
 * - NO calculation from cvrAmtArrLst ❌
 * - NO inference from policy documents ❌
 * - Coverage name mismatch → graceful (not error)
 */

import type {
  UpstreamPremiumResponse,
  PremiumProxyResponse,
  PremiumItem,
  PremiumFailureReason,
} from './types';
import { mapInsurerCode } from './types';
import type { InsurerCode } from '@/lib/premium/multipliers';

/**
 * Adapt upstream Premium API response to PremiumProxyResponse
 *
 * STEP 32 Mapping Rule:
 * - basePremium = data.monthlyPremSum (ONLY source)
 * - insurer = mapInsurerCode(data.insrCoCd)
 * - coverageName = first coverage name (if available, else "상품")
 *
 * @param upstream - upstream API response
 * @returns PremiumProxyResponse
 */
export function adaptPremiumResponse(
  upstream: UpstreamPremiumResponse | null | undefined
): PremiumProxyResponse {
  // Case 1: Upstream null/undefined
  if (!upstream) {
    return {
      ok: false,
      reason: 'INVALID_RESPONSE',
      message: 'Upstream response is null',
      items: [],
    };
  }

  // Case 2: Upstream error (returnCode !== "0000")
  if (upstream.returnCode !== '0000') {
    return {
      ok: false,
      reason: 'UPSTREAM_ERROR',
      message: upstream.returnMsg || 'Upstream API returned error',
      items: [],
    };
  }

  // Case 3: No data
  if (!upstream.data) {
    return {
      ok: false,
      reason: 'INVALID_RESPONSE',
      message: 'Upstream data is missing',
      items: [],
    };
  }

  // Extract basePremium (STEP 32 SSOT)
  const basePremium = upstream.data.monthlyPremSum ?? null;

  // Extract insurer
  const insurerCode = mapInsurerCode(upstream.data.insrCoCd);
  if (!insurerCode) {
    return {
      ok: false,
      reason: 'INVALID_RESPONSE',
      message: `Unknown insurer code: ${upstream.data.insrCoCd}`,
      items: [],
    };
  }

  // Extract coverage name (fallback to "상품")
  const coverageName =
    upstream.data.cvrAmtArrLst?.[0]?.cvrNm || '상품';

  // Build item
  const item: PremiumItem = {
    insurer: insurerCode,
    coverageName,
    basePremium,
    multiplier: null, // Upstream rarely provides this
  };

  return {
    ok: true,
    items: [item],
  };
}

/**
 * Adapt multiple upstream responses (for ranking scenarios)
 *
 * @param upstreams - array of upstream responses
 * @returns PremiumProxyResponse with multiple items
 */
export function adaptMultiplePremiumResponses(
  upstreams: Array<UpstreamPremiumResponse | null | undefined>
): PremiumProxyResponse {
  const items: PremiumItem[] = [];
  let hasError = false;
  let errorReason: PremiumFailureReason = 'UPSTREAM_ERROR';
  let errorMessage = '';

  for (const upstream of upstreams) {
    const adapted = adaptPremiumResponse(upstream);

    if (adapted.ok) {
      items.push(...adapted.items);
    } else {
      hasError = true;
      errorReason = adapted.reason || 'UPSTREAM_ERROR';
      errorMessage = adapted.message || '';
    }
  }

  // If all failed, return error
  if (items.length === 0 && hasError) {
    return {
      ok: false,
      reason: errorReason,
      message: errorMessage,
      items: [],
    };
  }

  // If some succeeded, return partial success
  return {
    ok: true,
    items,
  };
}

/**
 * Validate basePremium value
 *
 * @param basePremium - premium value to validate
 * @returns true if valid (positive number or null)
 */
export function isValidBasePremium(basePremium: number | null | undefined): boolean {
  if (basePremium === null || basePremium === undefined) {
    return true; // null is valid (means MISSING state)
  }

  return typeof basePremium === 'number' && basePremium >= 0;
}
