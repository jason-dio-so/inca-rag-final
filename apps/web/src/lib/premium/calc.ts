/**
 * Premium Calculation Logic (STEP 31 - SSOT)
 *
 * Constitutional Principles:
 * - Premium = proposal field (not calculated from policy)
 * - This is UI aggregation logic (NOT Backend Contract)
 * - Data absence ≠ error (graceful degradation)
 *
 * Calculation Rules:
 * 1. basePremium missing → both MISSING
 * 2. basePremium present, multiplier missing → nonCancellation READY, general PARTIAL
 * 3. basePremium present, multiplier present → both READY
 *
 * Important:
 * - In STEP 31, multiplier source is NOT implemented (hardcoded/mock for now)
 * - Future: multiplier comes from Excel table via inca-rag
 * - NO API calls, NO Backend changes
 */

import type {
  PremiumInput,
  PremiumComputed,
  PremiumResult,
  PlanType,
} from './types';

/**
 * Compute premium for a specific plan type
 *
 * @param basePremium - "① 전체" premium from proposal
 * @param multiplier - multiplier for "② 일반" (optional)
 * @param planType - which plan to compute
 * @returns PremiumComputed with status
 */
function computePlanPremium(
  basePremium: number | null | undefined,
  multiplier: number | null | undefined,
  planType: PlanType
): PremiumComputed {
  // Case 1: basePremium missing → MISSING
  if (basePremium === null || basePremium === undefined) {
    return {
      planType,
      premium: null,
      status: 'MISSING',
      reason: 'basePremium 데이터 없음',
    };
  }

  // Case 2: NON_CANCELLATION (무해지) = basePremium (no multiplier needed)
  if (planType === 'NON_CANCELLATION') {
    return {
      planType,
      premium: Math.round(basePremium),
      status: 'READY',
    };
  }

  // Case 3: GENERAL (일반) = basePremium × multiplier
  if (planType === 'GENERAL') {
    if (multiplier === null || multiplier === undefined) {
      return {
        planType,
        premium: null,
        status: 'PARTIAL',
        reason: 'multiplier 데이터 준비 중 (향후 요율표 연계)',
      };
    }

    return {
      planType,
      premium: Math.round(basePremium * multiplier),
      status: 'READY',
    };
  }

  // Case 4: ALL (전체) = basePremium (same as NON_CANCELLATION)
  if (planType === 'ALL') {
    return {
      planType,
      premium: Math.round(basePremium),
      status: 'READY',
    };
  }

  // Fallback: unknown plan type
  return {
    planType,
    premium: null,
    status: 'MISSING',
    reason: 'Unknown plan type',
  };
}

/**
 * Compute premiums for both nonCancellation and general plans
 *
 * @param input - basePremium and multiplier
 * @returns PremiumResult with both plans
 */
export function computePremiums(input: PremiumInput): PremiumResult {
  const { basePremium, multiplier } = input;

  const nonCancellation = computePlanPremium(
    basePremium,
    multiplier,
    'NON_CANCELLATION'
  );

  const general = computePlanPremium(basePremium, multiplier, 'GENERAL');

  return {
    nonCancellation,
    general,
  };
}

/**
 * Format premium for display
 *
 * @param premium - premium in KRW (integer)
 * @returns formatted string (e.g., "15,000원")
 */
export function formatPremium(premium: number | null | undefined): string {
  if (premium === null || premium === undefined) {
    return '정보 없음';
  }

  return `${premium.toLocaleString('ko-KR')}원`;
}

/**
 * Calculate premium difference
 *
 * @param premiumA - premium A
 * @param premiumB - premium B
 * @returns absolute difference
 */
export function calculatePremiumDiff(
  premiumA: number | null | undefined,
  premiumB: number | null | undefined
): number | null {
  if (
    premiumA === null ||
    premiumA === undefined ||
    premiumB === null ||
    premiumB === undefined
  ) {
    return null;
  }

  return Math.abs(premiumA - premiumB);
}

/**
 * Calculate premium difference percentage
 *
 * @param premiumA - premium A
 * @param premiumB - premium B
 * @returns percentage difference (based on minimum premium)
 */
export function calculatePremiumDiffPercent(
  premiumA: number | null | undefined,
  premiumB: number | null | undefined
): number | null {
  const diff = calculatePremiumDiff(premiumA, premiumB);
  if (diff === null) {
    return null;
  }

  if (
    premiumA === null ||
    premiumA === undefined ||
    premiumB === null ||
    premiumB === undefined
  ) {
    return null;
  }

  const minPremium = Math.min(premiumA, premiumB);
  if (minPremium === 0) {
    return null;
  }

  return Math.round((diff / minPremium) * 100);
}

/**
 * Check if premium explanation is required
 * (based on STEP 29 PRICE_STATE_EXTENSION.md)
 *
 * @param premiumA - premium A
 * @param premiumB - premium B
 * @param threshold - percentage threshold (default: 5%)
 * @returns true if difference > threshold
 */
export function isPremiumExplanationRequired(
  premiumA: number | null | undefined,
  premiumB: number | null | undefined,
  threshold: number = 5
): boolean {
  const diffPercent = calculatePremiumDiffPercent(premiumA, premiumB);
  if (diffPercent === null) {
    return false;
  }

  return diffPercent > threshold;
}

/**
 * Get cheaper insurer
 *
 * @param premiumA - premium A
 * @param premiumB - premium B
 * @param insurerA - insurer A name
 * @param insurerB - insurer B name
 * @returns cheaper insurer name
 */
export function getCheaperInsurer(
  premiumA: number | null | undefined,
  premiumB: number | null | undefined,
  insurerA: string,
  insurerB: string
): string | null {
  if (
    premiumA === null ||
    premiumA === undefined ||
    premiumB === null ||
    premiumB === undefined
  ) {
    return null;
  }

  return premiumA < premiumB ? insurerA : insurerB;
}
