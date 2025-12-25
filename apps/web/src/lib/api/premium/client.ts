/**
 * Premium API Client (STEP 32)
 *
 * Constitutional Principles:
 * - Calls server-side proxy routes (NOT direct upstream API)
 * - NO API keys exposed to client
 * - Timeout/error handling with graceful degradation
 */

import type {
  PremiumProxyResponse,
  SimplePremiumRequest,
  OnepagePremiumRequest,
} from './types';

/**
 * Premium API Client
 *
 * Calls our proxy routes (/api/premium/*)
 */
export class PremiumClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string = '', timeout: number = 10000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  /**
   * Call simple-compare Premium API
   *
   * @param request - simple premium request
   * @returns PremiumProxyResponse
   */
  async simpleCompare(request: SimplePremiumRequest): Promise<PremiumProxyResponse> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.baseUrl}/api/premium/simple-compare`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        return {
          ok: false,
          reason: 'UPSTREAM_ERROR',
          message: `HTTP ${response.status}: ${response.statusText}`,
          items: [],
        };
      }

      const data: PremiumProxyResponse = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return {
          ok: false,
          reason: 'TIMEOUT',
          message: `Request timeout after ${this.timeout}ms`,
          items: [],
        };
      }

      return {
        ok: false,
        reason: 'UPSTREAM_ERROR',
        message: error instanceof Error ? error.message : 'Unknown error',
        items: [],
      };
    }
  }

  /**
   * Call onepage-compare Premium API
   *
   * @param request - onepage premium request
   * @returns PremiumProxyResponse
   */
  async onepageCompare(request: OnepagePremiumRequest): Promise<PremiumProxyResponse> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.baseUrl}/api/premium/onepage-compare`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        return {
          ok: false,
          reason: 'UPSTREAM_ERROR',
          message: `HTTP ${response.status}: ${response.statusText}`,
          items: [],
        };
      }

      const data: PremiumProxyResponse = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return {
          ok: false,
          reason: 'TIMEOUT',
          message: `Request timeout after ${this.timeout}ms`,
          items: [],
        };
      }

      return {
        ok: false,
        reason: 'UPSTREAM_ERROR',
        message: error instanceof Error ? error.message : 'Unknown error',
        items: [],
      };
    }
  }
}

/**
 * Default Premium Client instance
 */
export const premiumClient = new PremiumClient();
