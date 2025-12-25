/**
 * Premium API Types (STEP 32)
 *
 * Constitutional Principles:
 * - Premium = proposal field (not calculated from policy)
 * - basePremium source = Premium API (monthlyPremSum)
 * - Coverage name mapping is NOT enforced (graceful PARTIAL)
 * - This is additional feature (does NOT affect /compare)
 */

import type { InsurerCode } from '@/lib/premium/multipliers';

/**
 * Upstream Premium API Response (간편비교/한장비교)
 *
 * Source: 간편비교_api.txt, 한장비교_API.txt
 */
export interface UpstreamPremiumResponse {
  returnCode: string; // "0000" = success
  returnMsg: string;
  data?: {
    insrCoCd?: string; // insurer code
    monthlyPremSum?: number; // STEP 32: basePremium source (①전체)
    cvrAmtArrLst?: Array<{
      // Coverage details (NOT used for basePremium calculation)
      cvrNm?: string;
      cvrAmt?: number;
      // ... other fields
    }>;
    // ... other fields
  };
}

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
