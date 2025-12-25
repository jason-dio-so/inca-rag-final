/**
 * Premium API Adapter (STEP 32-κ-FIX - SSOT for Mapping)
 *
 * Constitutional Principles:
 * - basePremium = spec field ONLY (prInfo: monthlyPrem, prDetail: monthlyPremSum)
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
 * STEP 32-κ-FIX: Supports both API response structures:
 * - prInfo (simple): outPrList[] → monthlyPrem
 * - prDetail (onepage): prProdLineCondOutSearchDiv[].prProdLineCondOutIns[] → monthlyPremSum
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

  // Handle potential data wrapper (some responses wrap in { data: {...} }, others don't)
  const payload = (upstream as any)?.data ?? (upstream as any);

  // A) prInfo (simple) shape: has outPrList[]
  if (payload.outPrList && Array.isArray(payload.outPrList)) {
    return adaptSimpleCompareResponse(payload);
  }

  // B) prDetail (onepage) shape: has prProdLineCondOutSearchDiv[]
  if (payload.prProdLineCondOutSearchDiv && Array.isArray(payload.prProdLineCondOutSearchDiv)) {
    return adaptOnepageCompareResponse(payload);
  }

  // C) Unknown shape
  return {
    ok: false,
    reason: 'INVALID_RESPONSE',
    message: 'Unknown upstream response structure',
    items: [],
  };
}

/**
 * Adapt prInfo (simple compare) response
 *
 * Source: docs/api/upstream/premium_simple_compare_spec.txt
 * Structure: { outPrList: [{ insCd, monthlyPrem, ... }] }
 */
function adaptSimpleCompareResponse(rawData: any): PremiumProxyResponse {
  const items: PremiumItem[] = [];

  for (const product of rawData.outPrList) {
    const insurerCode = mapInsurerCode(product.insCd);
    if (!insurerCode) {
      // Skip unknown insurer (graceful degradation)
      continue;
    }

    const basePremium = product.monthlyPrem ?? null;

    items.push({
      insurer: insurerCode,
      coverageName: 'PREMIUM_TOTAL', // Simple API doesn't provide coverage breakdown
      basePremium,
      multiplier: null,
    });
  }

  if (items.length === 0) {
    return {
      ok: false,
      reason: 'INVALID_RESPONSE',
      message: 'No valid insurers found in outPrList',
      items: [],
    };
  }

  return {
    ok: true,
    items,
  };
}

/**
 * Adapt prDetail (onepage compare) response
 *
 * Source: docs/api/upstream/premium_onepage_compare_spec.txt
 * Structure: { prProdLineCondOutSearchDiv: [{ prProdLineCondOutIns: [{ insCd, monthlyPremSum, ... }] }] }
 */
function adaptOnepageCompareResponse(rawData: any): PremiumProxyResponse {
  const items: PremiumItem[] = [];

  for (const searchDiv of rawData.prProdLineCondOutSearchDiv) {
    if (!searchDiv.prProdLineCondOutIns || !Array.isArray(searchDiv.prProdLineCondOutIns)) {
      continue;
    }

    for (const insurer of searchDiv.prProdLineCondOutIns) {
      const insurerCode = mapInsurerCode(insurer.insCd);
      if (!insurerCode) {
        // Skip unknown insurer (graceful degradation)
        continue;
      }

      const basePremium = insurer.monthlyPremSum ?? null;

      // Extract coverage name from first coverage (if available)
      const coverageName = insurer.cvrAmtArrLst?.[0]?.cvrNm || 'PREMIUM_TOTAL';

      items.push({
        insurer: insurerCode,
        coverageName,
        basePremium,
        multiplier: null,
      });
    }
  }

  if (items.length === 0) {
    return {
      ok: false,
      reason: 'INVALID_RESPONSE',
      message: 'No valid insurers found in prProdLineCondOutIns',
      items: [],
    };
  }

  return {
    ok: true,
    items,
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
