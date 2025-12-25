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
 * Based on standard Korean insurance API patterns.
 * Upstream endpoint: POST /api/v1/premium/simple
 */
export interface SimplePremiumRequest {
  /** 피보험자 나이 */
  age: number;
  /** 성별 (M/F) */
  gender: 'M' | 'F';
  /** 보험사 코드 (001=삼성, 002=메리츠, 004=KB, etc.) */
  insrCoCd: string;
  /** 담보 코드 리스트 */
  cvrCdLst?: string[];
  /** 가입금액 (optional) */
  insAmt?: number;
}

/**
 * Premium API Request (한장비교)
 *
 * Based on standard Korean insurance API patterns.
 * Upstream endpoint: POST /api/v1/premium/onepage
 */
export interface OnepagePremiumRequest {
  /** 설계서 ID */
  proposalId: string;
  /** 보험사 코드 (001=삼성, 002=메리츠, 004=KB, etc.) */
  insrCoCd: string;
}

/**
 * Insurer Code Mapping (Premium API → Our System)
 *
 * Maps upstream insurer codes to our InsurerCode type.
 */
export const INSURER_CODE_MAP: Record<string, InsurerCode> = {
  '001': 'SAMSUNG', // 삼성화재
  '002': 'MERITZ', // 메리츠화재
  '003': 'HYUNDAI', // 현대해상
  '004': 'KB', // KB손해보험
  '005': 'HANWHA', // 한화손해보험
  '006': 'LOTTE', // 롯데손해보험
  '007': 'DB', // DB손해보험
  '008': 'HEUNGKUK', // 흥국화재
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
