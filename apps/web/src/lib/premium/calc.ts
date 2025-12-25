/**
 * Premium Calculation Logic (STEP 31 + 31-α - SSOT)
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
 * STEP 31-α Changes:
 * - Multiplier source: GENERAL_MULTIPLIERS_BY_COVERAGE (embedded Excel data)
 * - Lookup: getGeneralMultiplier(coverageName, insurer)
 * - Backward compatible: explicit multiplier param takes precedence
 */

import type {
  PremiumInput,
  PremiumComputed,
  PremiumResult,
  PlanType,
} from './types';
import { getGeneralMultiplier, type InsurerCode } from './multipliers';

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
 * Extended PremiumInput with coverageName and insurer for multiplier lookup
 */
export interface PremiumInputExtended extends PremiumInput {
  coverageName?: string;
  insurer?: InsurerCode;
}

/**
 * Compute premiums for both nonCancellation and general plans
 *
 * STEP 31-α: Enhanced with coverageName/insurer lookup
 *
 * Multiplier Priority:
 * 1. Explicit multiplier param (backward compatibility)
 * 2. Lookup via getGeneralMultiplier(coverageName, insurer)
 * 3. undefined → general becomes PARTIAL
 *
 * @param input - basePremium, multiplier (optional), coverageName (optional), insurer (optional)
 * @returns PremiumResult with both plans
 */
export function computePremiums(input: PremiumInputExtended): PremiumResult {
  const { basePremium, multiplier, coverageName, insurer } = input;

  // Determine effective multiplier
  let effectiveMultiplier = multiplier;

  // STEP 31-α: Lookup multiplier if not provided but coverageName/insurer are
  if (
    effectiveMultiplier === null ||
    effectiveMultiplier === undefined
  ) {
    if (coverageName && insurer) {
      effectiveMultiplier = getGeneralMultiplier(coverageName, insurer);
    }
  }

  const nonCancellation = computePlanPremium(
    basePremium,
    effectiveMultiplier,
    'NON_CANCELLATION'
  );

  const general = computePlanPremium(basePremium, effectiveMultiplier, 'GENERAL');

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
