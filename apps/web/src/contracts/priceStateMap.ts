/**
 * Price UI Aggregation State Map (STEP 31)
 *
 * Constitutional Principle:
 * - These are UI-level aggregation states (NOT Backend Contract states)
 * - Backend Contract (STEP 14-26) remains immutable
 * - Price states are derived from Backend response + premium data availability
 *
 * Relationship with STEP 27 UI_STATE_MAP:
 * - UI_STATE_MAP: Base contract states (comparison_result:next_action:ux_message_code)
 * - PRICE_STATE_MAP: Aggregation states for premium-specific UX
 */

import type { PremiumResult } from '@/lib/premium/types';

/**
 * Price Aggregation State
 * (from STEP 29 PRICE_STATE_EXTENSION.md)
 */
export type PriceAggregationState =
  | 'PRICE_RANKING_READY'
  | 'PRICE_DATA_PARTIAL'
  | 'PRICE_EXPLANATION_REQUIRED'
  | 'PRICE_RANKING_UNAVAILABLE';

/**
 * Price State Config
 */
export interface PriceStateConfig {
  state: PriceAggregationState;
  view: 'PriceRankingView' | 'PriceComparisonView' | 'GenericMessage';
  title: string;
  description: string;
  primaryCta: string;
  secondaryCta?: string;
  severity: 'success' | 'warning' | 'info' | 'error';
  requiresAggregation: boolean;
}

/**
 * Price State Map
 */
export const PRICE_STATE_MAP: Record<
  PriceAggregationState,
  PriceStateConfig
> = {
  PRICE_RANKING_READY: {
    state: 'PRICE_RANKING_READY',
    view: 'PriceRankingView',
    title: '보험료 최저가 비교',
    description: '{N}개 보험사 중 가장 저렴한 순위입니다',
    primaryCta: 'compare',
    secondaryCta: 'search_again',
    severity: 'success',
    requiresAggregation: true,
  },

  PRICE_DATA_PARTIAL: {
    state: 'PRICE_DATA_PARTIAL',
    view: 'PriceRankingView',
    title: '보험료 비교 (일부 데이터)',
    description: '현재 {N}개 보험사 비교 가능 (일부 준비 중)',
    primaryCta: 'compare',
    secondaryCta: 'view_all_insurers',
    severity: 'warning',
    requiresAggregation: true,
  },

  PRICE_EXPLANATION_REQUIRED: {
    state: 'PRICE_EXPLANATION_REQUIRED',
    view: 'PriceComparisonView',
    title: '보험료 비교 상세',
    description: '왜 보험료가 다른지 확인하세요',
    primaryCta: 'view_policy',
    secondaryCta: 'compare_other',
    severity: 'info',
    requiresAggregation: false,
  },

  PRICE_RANKING_UNAVAILABLE: {
    state: 'PRICE_RANKING_UNAVAILABLE',
    view: 'GenericMessage',
    title: '보험료 비교 불가',
    description: '비교 가능한 가입설계서가 부족합니다',
    primaryCta: 'search_again',
    severity: 'info',
    requiresAggregation: false,
  },
};

/**
 * Fallback Price State
 */
export const FALLBACK_PRICE_STATE: PriceStateConfig = {
  state: 'PRICE_RANKING_UNAVAILABLE',
  view: 'GenericMessage',
  title: '보험료 정보 확인 중',
  description: '요청하신 보험료 정보를 확인하고 있습니다',
  primaryCta: 'search_again',
  severity: 'info',
  requiresAggregation: false,
};

/**
 * Premium Data Summary (for state resolution)
 */
export interface PremiumDataSummary {
  totalCount: number;
  readyCount: number;
  partialCount: number;
  missingCount: number;
}

/**
 * Get premium data summary from array of PremiumResult
 *
 * @param results - array of PremiumResult
 * @returns PremiumDataSummary
 */
export function getPremiumDataSummary(
  results: PremiumResult[]
): PremiumDataSummary {
  const totalCount = results.length;
  let readyCount = 0;
  let partialCount = 0;
  let missingCount = 0;

  for (const result of results) {
    // Check nonCancellation status (primary plan)
    if (result.nonCancellation.status === 'READY') {
      readyCount++;
    } else if (result.nonCancellation.status === 'PARTIAL') {
      partialCount++;
    } else {
      missingCount++;
    }
  }

  return {
    totalCount,
    readyCount,
    partialCount,
    missingCount,
  };
}

/**
 * Check if price ranking is ready
 * (from STEP 29 PRICE_STATE_EXTENSION.md)
 *
 * @param summary - premium data summary
 * @returns true if ranking ready
 */
export function isPriceRankingReady(summary: PremiumDataSummary): boolean {
  return summary.totalCount >= 2 && summary.readyCount >= 2;
}

/**
 * Check if price data is partial
 *
 * @param summary - premium data summary
 * @returns true if partial data
 */
export function isPriceDataPartial(summary: PremiumDataSummary): boolean {
  return (
    summary.totalCount >= 2 &&
    summary.readyCount >= 1 &&
    (summary.partialCount > 0 || summary.missingCount > 0)
  );
}

/**
 * Resolve price aggregation state
 * (based on STEP 29 PRICE_STATE_EXTENSION.md logic)
 *
 * @param results - array of PremiumResult
 * @returns PriceAggregationState
 */
export function resolvePriceAggregationState(
  results: PremiumResult[]
): PriceAggregationState {
  const summary = getPremiumDataSummary(results);

  if (isPriceRankingReady(summary)) {
    return 'PRICE_RANKING_READY';
  }

  if (isPriceDataPartial(summary)) {
    return 'PRICE_DATA_PARTIAL';
  }

  return 'PRICE_RANKING_UNAVAILABLE';
}

/**
 * Get price state config
 *
 * @param state - price aggregation state
 * @returns PriceStateConfig
 */
export function getPriceStateConfig(
  state: PriceAggregationState
): PriceStateConfig {
  return PRICE_STATE_MAP[state] || FALLBACK_PRICE_STATE;
}
