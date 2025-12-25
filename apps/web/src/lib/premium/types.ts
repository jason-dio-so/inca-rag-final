/**
 * Premium Calculation Types (STEP 31)
 *
 * Constitutional Principle:
 * - Premium comparison is an ADDITIONAL FEATURE on proposal-centered system
 * - Premium = proposal field (not calculated from policy)
 * - PlanType (일반/무해지) = UI presentation type
 */

/**
 * Plan Type
 * - ALL: "① 전체" (base premium, default)
 * - GENERAL: "② 일반" (base × multiplier)
 * - NON_CANCELLATION: "③ 무해지" (base, no multiplier)
 */
export type PlanType = 'ALL' | 'GENERAL' | 'NON_CANCELLATION';

/**
 * Premium Input
 * - basePremium: "① 전체" premium from proposal (nullable)
 * - multiplier: policy-specific multiplier for "② 일반" (nullable)
 *
 * NOTE: In STEP 31, multiplier source is NOT implemented.
 * Future: multiplier comes from Excel table (inca-rag integration)
 */
export interface PremiumInput {
  basePremium?: number | null;
  multiplier?: number | null;
}

/**
 * Premium Computation Result
 * - planType: which plan this result represents
 * - premium: computed amount (KRW, integer)
 * - status: data availability state
 * - reason: why PARTIAL or MISSING (optional)
 */
export interface PremiumComputed {
  planType: PlanType;
  premium?: number | null;
  status: 'READY' | 'PARTIAL' | 'MISSING';
  reason?: string;
}

/**
 * Premium Calculation Result
 * - nonCancellation: "③ 무해지" = basePremium
 * - general: "② 일반" = basePremium × multiplier
 */
export interface PremiumResult {
  nonCancellation: PremiumComputed;
  general: PremiumComputed;
}

/**
 * Premium Display Mode
 * - SINGLE: Show one plan type (default: ALL)
 * - COMPARISON: Show nonCancellation vs general
 */
export type PremiumDisplayMode = 'SINGLE' | 'COMPARISON';

/**
 * Premium Card Data (for PriceRankingView)
 */
export interface PremiumCardData {
  rank: number;
  insurer: string;
  proposalId: string;
  premiumResult: PremiumResult;
  displayMode: PremiumDisplayMode;
  canonicalCoverageCode?: string;
}

/**
 * Premium Explanation (for PriceComparisonView)
 */
export interface PremiumExplanation {
  premiumDiff: number; // abs difference
  premiumDiffPercent: number; // (diff / min) * 100
  cheaperInsurer: string;
  reasons: string[]; // explanation lines
  hasPolicyEvidence: boolean;
}
