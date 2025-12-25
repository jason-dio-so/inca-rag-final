/**
 * Premium Adapter Regression Tests (STEP 32-λ)
 *
 * Purpose: Ensure adapter handles SSOT-documented response structures
 * without network dependency.
 *
 * Fixtures based on: docs/api/premium_api_spec.md (SSOT)
 */

import { describe, it, expect } from 'vitest';
import { adaptPremiumResponse } from './adapter';
import type { UpstreamPrInfoResponse, UpstreamPrDetailResponse, UpstreamWrapped } from './types';

// Load fixtures
import prInfoSample from './__fixtures__/upstream_prInfo_sample.json';
import prDetailSample from './__fixtures__/upstream_prDetail_sample.json';
import wrappedSample from './__fixtures__/upstream_wrapped_sample.json';

describe('Premium Adapter - SSOT Structure Compliance', () => {
  describe('prInfo (Simple Compare) - SSOT § API 1', () => {
    it('should extract basePremium from outPrList[].monthlyPrem', () => {
      const result = adaptPremiumResponse(prInfoSample as UpstreamPrInfoResponse);

      expect(result.ok).toBe(true);
      expect(result.items).toHaveLength(2);
      expect(result.items[0].basePremium).toBe(48000); // KB (sorted by premium)
      expect(result.items[0].insurer).toBe('KB');
      expect(result.items[1].basePremium).toBe(50000); // SAMSUNG
      expect(result.items[1].insurer).toBe('SAMSUNG');
    });

    it('should handle unknown insurer codes gracefully', () => {
      const modified = {
        ...prInfoSample,
        outPrList: [
          { ...prInfoSample.outPrList[0], insCd: 'UNKNOWN' },
        ],
      };

      const result = adaptPremiumResponse(modified as any);

      // Unknown insurer should be skipped, resulting in empty items
      expect(result.ok).toBe(false);
      expect(result.reason).toBe('INVALID_RESPONSE');
      expect(result.items).toHaveLength(0);
    });
  });

  describe('prDetail (Onepage Compare) - SSOT § API 2', () => {
    it('should extract basePremium from monthlyPremSum', () => {
      const result = adaptPremiumResponse(prDetailSample as UpstreamPrDetailResponse);

      expect(result.ok).toBe(true);
      expect(result.items).toHaveLength(1);
      expect(result.items[0].basePremium).toBe(50000);
      expect(result.items[0].insurer).toBe('SAMSUNG');
    });

    it('should NOT use cvrAmtArrLst[].monthlyPrem for basePremium', () => {
      const result = adaptPremiumResponse(prDetailSample as UpstreamPrDetailResponse);

      // basePremium should be monthlyPremSum (50000), NOT cvrAmtArrLst sum
      expect(result.items[0].basePremium).toBe(50000);
      expect(result.items[0].basePremium).not.toBe(5000); // NOT individual coverage premium
    });
  });

  describe('Defensive: Wrapped Response (not in SSOT)', () => {
    it('should handle { returnCode, data } wrapper defensively', () => {
      const result = adaptPremiumResponse(wrappedSample as UpstreamWrapped<any>);

      expect(result.ok).toBe(true);
      expect(result.items).toHaveLength(1);
      expect(result.items[0].basePremium).toBe(50000);
    });

    it('should return error if returnCode !== "0000"', () => {
      const errorWrapped = {
        returnCode: '9999',
        returnMsg: 'Test Error',
        data: null,
      };

      const result = adaptPremiumResponse(errorWrapped as any);

      expect(result.ok).toBe(false);
      expect(result.reason).toBe('UPSTREAM_ERROR');
      expect(result.message).toContain('Test Error');
    });
  });

  describe('Edge Cases', () => {
    it('should handle null/undefined upstream gracefully', () => {
      expect(adaptPremiumResponse(null).ok).toBe(false);
      expect(adaptPremiumResponse(undefined).ok).toBe(false);
    });

    it('should handle empty outPrList gracefully', () => {
      const empty = {
        ...prInfoSample,
        outPrList: [],
      };

      const result = adaptPremiumResponse(empty as any);

      expect(result.ok).toBe(false);
      expect(result.reason).toBe('INVALID_RESPONSE');
    });
  });
});
