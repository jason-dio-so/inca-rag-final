/**
 * Price Comparison Mock Scenarios (STEP 31 + 31-α)
 *
 * DEV_MOCK_MODE extension for premium comparison testing
 *
 * Constitutional Principle:
 * - These are FRONTEND mock data only
 * - DO NOT modify golden snapshots (Backend Contract)
 * - Premium data is simulated for UX testing
 *
 * STEP 31-α: Use real multipliers from GENERAL_MULTIPLIERS_BY_COVERAGE
 */

import type { PremiumCardData } from '@/lib/premium/types';
import type { PremiumResult } from '@/lib/premium/types';
import { computePremiums } from '@/lib/premium/calc';
import type { InsurerCode } from '@/lib/premium/multipliers';

/**
 * Mock Premium Result (READY) - STEP 31-α: Use computePremiums with coverageName/insurer
 */
function createReadyPremiumResult(
  basePremium: number,
  coverageName: string,
  insurer: InsurerCode
): PremiumResult {
  return computePremiums({ basePremium, coverageName, insurer });
}

/**
 * Mock Premium Result (PARTIAL - no multiplier)
 */
function createPartialPremiumResult(basePremium: number): PremiumResult {
  return {
    nonCancellation: {
      planType: 'NON_CANCELLATION',
      premium: Math.round(basePremium),
      status: 'READY',
    },
    general: {
      planType: 'GENERAL',
      premium: null,
      status: 'PARTIAL',
      reason: 'multiplier 데이터 준비 중 (향후 요율표 연계)',
    },
  };
}

/**
 * Mock Premium Result (MISSING - no base premium)
 */
function createMissingPremiumResult(): PremiumResult {
  return {
    nonCancellation: {
      planType: 'NON_CANCELLATION',
      premium: null,
      status: 'MISSING',
      reason: 'basePremium 데이터 없음',
    },
    general: {
      planType: 'GENERAL',
      premium: null,
      status: 'MISSING',
      reason: 'basePremium 데이터 없음',
    },
  };
}

/**
 * Scenario A_PRICE_READY
 * - All 5 insurers have premium data
 * - Coverage: "암진단비" (real multipliers from Excel)
 * - Ranking ready
 *
 * STEP 31-α: Use real multipliers
 * - SAMSUNG: basePremium 100,000 → general 117,000 (1.17)
 * - MERITZ: basePremium 100,000 → general 155,000 (1.55)
 * - HYUNDAI: basePremium 100,000 → general 131,000 (1.31)
 * - KB: basePremium 100,000 → general 132,000 (1.32)
 * - DB: basePremium 100,000 → general 136,000 (1.36)
 */
export const SCENARIO_A_PRICE_READY: PremiumCardData[] = [
  {
    rank: 1,
    insurer: 'KB손해보험',
    proposalId: 'KB_proposal_001',
    premiumResult: createReadyPremiumResult(100000, '암진단비', 'KB'),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 2,
    insurer: '삼성화재',
    proposalId: 'SAMSUNG_proposal_003',
    premiumResult: createReadyPremiumResult(100000, '암진단비', 'SAMSUNG'),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 3,
    insurer: '현대해상',
    proposalId: 'HYUNDAI_proposal_004',
    premiumResult: createReadyPremiumResult(100000, '암진단비', 'HYUNDAI'),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 4,
    insurer: 'DB손해보험',
    proposalId: 'DB_proposal_005',
    premiumResult: createReadyPremiumResult(100000, '암진단비', 'DB'),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 5,
    insurer: '메리츠화재',
    proposalId: 'MERITZ_proposal_002',
    premiumResult: createReadyPremiumResult(100000, '암진단비', 'MERITZ'),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
];

/**
 * Scenario A_PRICE_PARTIAL
 * - 3 insurers have premium data (READY) with real multipliers
 * - 1 insurer has partial data (PARTIAL - coverage not in multiplier table)
 * - 1 insurer has missing data (MISSING - no basePremium)
 */
export const SCENARIO_A_PRICE_PARTIAL: PremiumCardData[] = [
  {
    rank: 1,
    insurer: 'KB손해보험',
    proposalId: 'KB_proposal_001',
    premiumResult: createReadyPremiumResult(100000, '암진단비', 'KB'),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 2,
    insurer: '삼성화재',
    proposalId: 'SAMSUNG_proposal_003',
    premiumResult: createReadyPremiumResult(100000, '암진단비', 'SAMSUNG'),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 3,
    insurer: '현대해상',
    proposalId: 'HYUNDAI_proposal_004',
    premiumResult: createReadyPremiumResult(100000, '암진단비', 'HYUNDAI'),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 0, // unranked (partial - coverage not in table)
    insurer: 'DB손해보험',
    proposalId: 'DB_proposal_005',
    premiumResult: createPartialPremiumResult(100000),
    displayMode: 'SINGLE',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 0, // unranked (missing - no basePremium)
    insurer: '메리츠화재',
    proposalId: 'MERITZ_proposal_002',
    premiumResult: createMissingPremiumResult(),
    displayMode: 'SINGLE',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
];

/**
 * Scenario Comparison (KB vs SAMSUNG)
 * - For PriceComparisonView testing
 *
 * STEP 31-α: Use real multipliers
 * - KB: basePremium 100,000 → general 132,000 (1.32)
 * - SAMSUNG: basePremium 100,000 → general 117,000 (1.17)
 * - KB is cheaper (nonCancellation = basePremium)
 */
export const SCENARIO_PRICE_COMPARISON = {
  insurerA: 'KB손해보험',
  insurerB: '삼성화재',
  coverageName: '암진단비',
  canonicalCoverageCode: 'CRE_CVR_001',
  premiumResultA: createReadyPremiumResult(100000, '암진단비', 'KB'),
  premiumResultB: createReadyPremiumResult(100000, '암진단비', 'SAMSUNG'),
  policyEvidenceA: {
    exclusion_period_days: 90,
    reduction_period_years: 1,
    reduction_percentage: 50,
    disease_scope_raw: 'C00-C97 (유사암 5종 제외)',
  },
  policyEvidenceB: {
    exclusion_period_days: 0,
    reduction_period_years: 2,
    reduction_percentage: 50,
    disease_scope_raw: 'C00-C97 (유사암 5종 제외)',
  },
};

/**
 * Price Scenario ID
 */
export type PriceScenarioId = 'A_PRICE_READY' | 'A_PRICE_PARTIAL' | 'PRICE_COMPARISON';

/**
 * Get price scenario by ID
 */
export function getPriceScenario(scenarioId: PriceScenarioId) {
  switch (scenarioId) {
    case 'A_PRICE_READY':
      return {
        type: 'ranking',
        cards: SCENARIO_A_PRICE_READY,
      };
    case 'A_PRICE_PARTIAL':
      return {
        type: 'ranking',
        cards: SCENARIO_A_PRICE_PARTIAL,
      };
    case 'PRICE_COMPARISON':
      return {
        type: 'comparison',
        data: SCENARIO_PRICE_COMPARISON,
      };
    default:
      throw new Error(`Unknown price scenario: ${scenarioId}`);
  }
}
