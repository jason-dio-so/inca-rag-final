/**
 * Premium Proxy Response Bridge (STEP 32-δ)
 *
 * Constitutional Principles:
 * - Premium = additional feature (does NOT affect /compare)
 * - basePremium source = Premium API (monthlyPremSum ONLY)
 * - Coverage name mapping NOT enforced (PARTIAL is normal)
 * - Failures MUST be explicit (no empty arrays/blank screens)
 *
 * STEP 32-δ Changes:
 * - Moved from mocks/priceScenarios.ts (separation of concerns)
 * - No fake proposalId generation (use upstream or undefined)
 * - Explicit failure rendering (MISSING cards for failed items)
 *
 * @example Real mode usage (in UI component or page):
 * ```tsx
 * import { PremiumClient } from '@/lib/api/premium/client';
 * import { convertProxyResponseToCards } from '@/lib/api/premium/bridge';
 *
 * // In component/page:
 * const client = new PremiumClient();
 * const response = await client.simpleCompare(request);
 * const cards = convertProxyResponseToCards(response);
 *
 * // cards will ALWAYS have data (even for failures):
 * // - Success: ranked cards with premiums
 * // - Failure: MISSING cards with explicit reasons
 * // - Empty result: single "데이터 없음" card
 * ```
 */

import type { PremiumProxyResponse } from './types';
import type { PremiumCardData, PremiumResult } from '@/lib/premium/types';
import { computePremiums } from '@/lib/premium/calc';

/**
 * Create MISSING premium result (for failed items)
 */
function createMissingPremiumResult(reason: string): PremiumResult {
  return {
    nonCancellation: {
      planType: 'NON_CANCELLATION',
      premium: null,
      status: 'MISSING',
      reason,
    },
    general: {
      planType: 'GENERAL',
      premium: null,
      status: 'MISSING',
      reason,
    },
  };
}

/**
 * Convert Premium Proxy Response to PremiumCardData array
 *
 * Constitutional Guarantees:
 * 1. Failures are EXPLICIT (never return empty array for failed responses)
 * 2. No fake proposalId generation (use upstream or undefined)
 * 3. PARTIAL/MISSING states are normal (not errors)
 * 4. Ranking: basePremium ascending, null → rank 0 (bottom)
 *
 * @param response - Premium API proxy response
 * @returns PremiumCardData array (ALWAYS returns cards, even for failures)
 */
export function convertProxyResponseToCards(
  response: PremiumProxyResponse
): PremiumCardData[] {
  // Failure case: Return explicit MISSING cards (not empty array)
  if (!response.ok) {
    const failureReason = response.message || response.reason || 'Premium API 응답 실패';

    // If we have partial data (items exist but ok=false), render them as MISSING
    if (response.items.length > 0) {
      return response.items.map((item) => ({
        rank: 0, // unranked (failure)
        insurer: item.insurer,
        proposalId: undefined, // no fake IDs
        premiumResult: createMissingPremiumResult(failureReason),
        displayMode: 'SINGLE',
        canonicalCoverageCode: undefined,
      }));
    }

    // If no items at all, return a single generic failure card
    return [
      {
        rank: 0,
        insurer: '데이터 없음',
        proposalId: undefined,
        premiumResult: createMissingPremiumResult(failureReason),
        displayMode: 'SINGLE',
        canonicalCoverageCode: undefined,
      },
    ];
  }

  // Success case: Process items
  const successItems: (PremiumCardData & { sortKey: number })[] = [];
  const failedItems: PremiumCardData[] = [];

  response.items.forEach((item) => {
    // Items with null basePremium → MISSING (unranked)
    if (item.basePremium === null) {
      failedItems.push({
        rank: 0,
        insurer: item.insurer,
        proposalId: undefined, // no fake IDs
        premiumResult: createMissingPremiumResult('basePremium 데이터 없음'),
        displayMode: 'SINGLE',
        canonicalCoverageCode: undefined,
      });
      return;
    }

    // Items with valid basePremium → compute premiums
    const premiumResult = computePremiums({
      basePremium: item.basePremium,
      multiplier: item.multiplier,
      coverageName: item.coverageName,
      insurer: item.insurer,
    });

    successItems.push({
      rank: 0, // will be assigned below
      insurer: item.insurer,
      proposalId: undefined, // no fake IDs (use upstream if available)
      premiumResult,
      displayMode: 'COMPARISON',
      canonicalCoverageCode: undefined,
      sortKey: item.basePremium,
    });
  });

  // Sort success items by basePremium (ascending, cheapest first)
  successItems.sort((a, b) => a.sortKey - b.sortKey);

  // Assign ranks (1-based)
  const rankedItems = successItems.map((item, index) => ({
    rank: index + 1,
    insurer: item.insurer,
    proposalId: item.proposalId,
    premiumResult: item.premiumResult,
    displayMode: item.displayMode,
    canonicalCoverageCode: item.canonicalCoverageCode,
  }));

  // Return: ranked items first, then unranked failures
  return [...rankedItems, ...failedItems];
}
