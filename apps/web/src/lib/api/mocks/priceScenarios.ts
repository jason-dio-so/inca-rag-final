/**
 * Price Comparison Mock Scenarios (STEP 31)
 *
 * DEV_MOCK_MODE extension for premium comparison testing
 *
 * Constitutional Principle:
 * - These are FRONTEND mock data only
 * - DO NOT modify golden snapshots (Backend Contract)
 * - Premium data is simulated for UX testing
 */

import type { PremiumCardData } from '@/lib/premium/types';
import type { PremiumResult } from '@/lib/premium/types';

/**
 * Mock Premium Result (READY)
 */
function createReadyPremiumResult(basePremium: number, multiplier: number = 0.85): PremiumResult {
  return {
    nonCancellation: {
      planType: 'NON_CANCELLATION',
      premium: Math.round(basePremium),
      status: 'READY',
    },
    general: {
      planType: 'GENERAL',
      premium: Math.round(basePremium * multiplier),
      status: 'READY',
    },
  };
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
 * - Ranking ready
 */
export const SCENARIO_A_PRICE_READY: PremiumCardData[] = [
  {
    rank: 1,
    insurer: 'KB손해보험',
    proposalId: 'KB_proposal_001',
    premiumResult: createReadyPremiumResult(15000, 0.85),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 2,
    insurer: '메리츠화재',
    proposalId: 'MERITZ_proposal_002',
    premiumResult: createReadyPremiumResult(16200, 0.86),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 3,
    insurer: '삼성화재',
    proposalId: 'SAMSUNG_proposal_003',
    premiumResult: createReadyPremiumResult(17500, 0.87),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 4,
    insurer: '현대해상',
    proposalId: 'HYUNDAI_proposal_004',
    premiumResult: createReadyPremiumResult(18800, 0.88),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 5,
    insurer: 'DB손해보험',
    proposalId: 'DB_proposal_005',
    premiumResult: createReadyPremiumResult(19500, 0.89),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
];

/**
 * Scenario A_PRICE_PARTIAL
 * - 3 insurers have premium data (READY)
 * - 2 insurers have partial data (PARTIAL or MISSING)
 */
export const SCENARIO_A_PRICE_PARTIAL: PremiumCardData[] = [
  {
    rank: 1,
    insurer: 'KB손해보험',
    proposalId: 'KB_proposal_001',
    premiumResult: createReadyPremiumResult(15000, 0.85),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 2,
    insurer: '메리츠화재',
    proposalId: 'MERITZ_proposal_002',
    premiumResult: createReadyPremiumResult(16200, 0.86),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 3,
    insurer: '삼성화재',
    proposalId: 'SAMSUNG_proposal_003',
    premiumResult: createReadyPremiumResult(17500, 0.87),
    displayMode: 'COMPARISON',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 0, // unranked (partial)
    insurer: '현대해상',
    proposalId: 'HYUNDAI_proposal_004',
    premiumResult: createPartialPremiumResult(18800),
    displayMode: 'SINGLE',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
  {
    rank: 0, // unranked (missing)
    insurer: 'DB손해보험',
    proposalId: 'DB_proposal_005',
    premiumResult: createMissingPremiumResult(),
    displayMode: 'SINGLE',
    canonicalCoverageCode: 'CRE_CVR_001',
  },
];

/**
 * Scenario Comparison (KB vs SAMSUNG)
 * - For PriceComparisonView testing
 */
export const SCENARIO_PRICE_COMPARISON = {
  insurerA: 'KB손해보험',
  insurerB: '삼성화재',
  coverageName: '일반암진단비',
  canonicalCoverageCode: 'CRE_CVR_001',
  premiumResultA: createReadyPremiumResult(15000, 0.85),
  premiumResultB: createReadyPremiumResult(17500, 0.87),
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
