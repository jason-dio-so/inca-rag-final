/**
 * General Plan Multiplier Table (STEP 31-α)
 *
 * Source: 4. 일반보험요율예시.xlsx
 * Interpretation: Excel integer like 117 => multiplier 1.17 (i.e., percent/100).
 *
 * Usage:
 *  - basePremium = '무해지(① 전체)' premium (KRW)
 *  - generalPremium = round(basePremium * multiplier)
 *
 * Notes:
 *  - This is FRONTEND-only reference data (UI aggregation), not Backend Contract.
 *  - Missing multiplier => generalPremium becomes PARTIAL (nonCancellation still READY).
 */

export type InsurerCode =
  | 'SAMSUNG'
  | 'MERITZ'
  | 'HYUNDAI'
  | 'KB'
  | 'HANWHA'
  | 'LOTTE'
  | 'DB'
  | 'HEUNGKUK';

export const GENERAL_MULTIPLIERS_BY_COVERAGE: Record<
  string,
  Partial<Record<InsurerCode, number>>
> = {
  질병사망: {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  질병후유장해: {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '질병입원일당(1~180일)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '질병입원일당(1~200일)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '질병입원일당(1~365일)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '질병수술비(1종)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '질병수술비(2종)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '질병수술비(3종)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '질병수술비(4종)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  상해사망: {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  상해후유장해: {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '상해입원일당(1~180일)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '상해입원일당(1~200일)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '상해입원일당(1~365일)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '상해수술비(1종)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '상해수술비(2종)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '상해수술비(3종)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '상해수술비(4종)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  '자동차사고부상치료비(1~14급)': {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  암진단비: {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  유사암진단비: {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  뇌혈관질환진단비: {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  허혈성심장질환진단비: {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  특정순환계질환진단비: {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  질병진단비: {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  암수술비: {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  질병수술비: {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
  상해수술비: {
    SAMSUNG: 1.17,
    MERITZ: 1.55,
    HYUNDAI: 1.31,
    KB: 1.32,
    HANWHA: 1.26,
    LOTTE: 1.3,
    DB: 1.36,
    HEUNGKUK: 1.34,
  },
} as const;

/**
 * Get general plan multiplier for a coverage and insurer
 *
 * @param coverageName - Coverage name from proposal (Korean)
 * @param insurer - Insurer code
 * @returns multiplier (e.g., 1.17) or undefined if not found
 */
export function getGeneralMultiplier(
  coverageName: string,
  insurer: InsurerCode
): number | undefined {
  return GENERAL_MULTIPLIERS_BY_COVERAGE[coverageName]?.[insurer];
}
