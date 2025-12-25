/**
 * Premium API Types (STEP 32-κ-POST - Spec-Driven)
 *
 * Constitutional Principles:
 * - Premium = proposal field (not calculated from policy)
 * - basePremium source = spec field ONLY (prInfo: monthlyPrem, prDetail: monthlyPremSum)
 * - Coverage name mapping is NOT enforced (graceful PARTIAL)
 * - This is additional feature (does NOT affect /compare)
 *
 * Source: docs/api/upstream/premium_*_spec.txt (SSOT)
 */

import type { InsurerCode } from '@/lib/premium/multipliers';

/**
 * Upstream prInfo (Simple Compare) Response
 *
 * Source: docs/api/upstream/premium_simple_compare_spec.txt
 * Structure: Top-level fields (no data wrapper)
 */
export interface UpstreamPrInfoResponse {
  customerSeq: number;
  customerIpSeq: number;
  compPlanId: number;
  outPrList: Array<{
    prProdLineCd: string;
    insCd: string;         // "N01", "N02", etc.
    insNm: string;
    prCd: string;
    prNm: string;
    prScore: number;
    newDispYn: string;
    monthlyPrem: number;   // ★ basePremium source for simple
    updateDt: string;
    updatingYn: string;
  }>;
}

/**
 * Upstream prDetail (Onepage Compare) Response
 *
 * Source: docs/api/upstream/premium_onepage_compare_spec.txt
 * Structure: Top-level fields (no data wrapper)
 */
export interface UpstreamPrDetailResponse {
  calSubSeq: number;
  prProdLineCd: string;
  prProdLineNm: string;
  disSearchDiv: string | null;
  baseDate: string;
  nm: string | null;
  age: number;
  sex: string;
  prProdLineCondOutSearchDiv: Array<{
    searchDiv: string;
    prProdLineCondOutIns: Array<{
      insCd: string;
      insNm: string;
      prCd: string;
      prNm: string;
      insTrm: string;
      pyTrm: string;
      rnwCycle: string;
      prodType: string;
      updateDt: string;
      recommYn: string | null;
      monthlyPremSum: number;  // ★ basePremium source for onepage
      cvrAmtArrLst?: Array<{   // Coverage list (display ONLY - NOT for calculation)
        cvrDiv: string;
        dispOrder: number;
        cvrCd: string;
        cvrNm: string;
        creCvrCd: string;
        accAmt: number;
        accAmtNm: string;
        monthlyPrem: number;
        amtDispYn: string;
      }>;
    }>;
  }>;
}

/**
 * Generic upstream response wrapper
 *
 * Note: Actual upstream APIs do NOT use this wrapper in practice.
 * This exists for compatibility with potential future API changes.
 * Current adapter handles both wrapped and unwrapped responses.
 */
export interface UpstreamWrapped<T> {
  returnCode: string;  // "0000" = success
  returnMsg: string;
  data?: T;
}

/**
 * Union type for all possible upstream response formats
 *
 * Adapter uses runtime shape detection to handle both:
 * - Direct response (spec-confirmed)
 * - Wrapped response (defensive)
 */
export type UpstreamPremiumResponse =
  | UpstreamPrInfoResponse
  | UpstreamPrDetailResponse
  | UpstreamWrapped<UpstreamPrInfoResponse>
  | UpstreamWrapped<UpstreamPrDetailResponse>;

/**
 * Premium Proxy Contract (STEP 32 SSOT)
 *
 * This is the standardized response from our proxy routes.
 */
export interface PremiumProxyResponse {
  ok: boolean;
  items: PremiumItem[];
  reason?: PremiumFailureReason;
  message?: string;
}

/**
 * Premium Item (proxy response element)
 */
export interface PremiumItem {
  insurer: InsurerCode;
  coverageName: string; // UI label (may not match canonical)
  basePremium: number | null; // ①전체 (from monthlyPremSum)
  multiplier?: number | null; // optional (rarely provided by upstream)
}

/**
 * Premium Failure Reason
 */
export type PremiumFailureReason =
  | 'UPSTREAM_ERROR'
  | 'TIMEOUT'
  | 'UNAUTHORIZED'
  | 'BAD_REQUEST'
  | 'INVALID_RESPONSE';

/**
 * Premium API Request (간편비교)
 *
 * Source: docs/api/upstream/premium_simple_compare_spec.txt
 * Method: GET (query parameters)
 * URL: /public/prdata/prInfo
 */
export interface SimplePremiumRequest {
  /** Base date (YYYYMMDD) */
  baseDt: string;
  /** Birthday (YYYYMMDD) */
  birthday: string;
  /** Customer name */
  customerNm: string;
  /** Gender ("1"=M, "2"=F) */
  sex: string;
  /** Age (string) */
  age: string;
}

/**
 * Premium API Request (한장비교)
 *
 * Source: docs/api/upstream/premium_onepage_compare_spec.txt
 * Method: GET (query parameters)
 * URL: /public/prdata/prDetail
 */
export interface OnepagePremiumRequest {
  /** Base date (YYYYMMDD) */
  baseDt: string;
  /** Birthday (YYYYMMDD) */
  birthday: string;
  /** Customer name */
  customerNm: string;
  /** Gender ("1"=M, "2"=F) */
  sex: string;
  /** Age (string) */
  age: string;
}

/**
 * Insurer Code Mapping (Premium API → Our System)
 *
 * Source: docs/api/upstream/premium_simple_compare_spec.txt
 * Maps upstream insurer codes (insCd) to our InsurerCode type.
 */
export const INSURER_CODE_MAP: Record<string, InsurerCode> = {
  'N01': 'MERITZ',   // 메리츠화재
  'N02': 'HANWHA',   // 한화손보
  'N03': 'LOTTE',    // 롯데손보
  'N05': 'HEUNGKUK', // 흥국화재
  'N08': 'SAMSUNG',  // 삼성화재
  'N09': 'HYUNDAI',  // 현대해상
  'N10': 'KB',       // KB손보
  'N13': 'DB',       // DB손보
};

/**
 * Map upstream insurer code to our InsurerCode
 *
 * @param upstreamCode - insurer code from Premium API
 * @returns InsurerCode or undefined if not found
 */
export function mapInsurerCode(upstreamCode: string | undefined): InsurerCode | undefined {
  if (!upstreamCode) return undefined;
  return INSURER_CODE_MAP[upstreamCode];
}
