/**
 * Price Comparison View (STEP 31)
 *
 * Extends ComparableView with "Why different?" explanation section
 *
 * Constitutional Principle:
 * - Premium comparison is ADDITIONAL feature on proposal comparison
 * - Policy evidence = explanation (not source)
 * - Data absence ≠ error
 */

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import type { PremiumResult, PremiumExplanation } from '@/lib/premium/types';
import {
  formatPremium,
  calculatePremiumDiff,
  calculatePremiumDiffPercent,
  getCheaperInsurer,
} from '@/lib/premium/calc';

export interface PriceComparisonViewProps {
  // Proposal data
  insurerA: string;
  insurerB: string;
  coverageName: string;
  canonicalCoverageCode?: string;

  // Premium data
  premiumResultA: PremiumResult;
  premiumResultB: PremiumResult;

  // Policy evidence (for explanation)
  policyEvidenceA?: any;
  policyEvidenceB?: any;

  // Actions
  onViewPolicy?: () => void;
  onCompareOther: () => void;
}

export function PriceComparisonView({
  insurerA,
  insurerB,
  coverageName,
  canonicalCoverageCode,
  premiumResultA,
  premiumResultB,
  policyEvidenceA,
  policyEvidenceB,
  onViewPolicy,
  onCompareOther,
}: PriceComparisonViewProps) {
  // Extract premium values (using nonCancellation as primary)
  const premiumA = premiumResultA.nonCancellation.premium;
  const premiumB = premiumResultB.nonCancellation.premium;

  // Calculate differences
  const premiumDiff = calculatePremiumDiff(premiumA, premiumB);
  const premiumDiffPercent = calculatePremiumDiffPercent(premiumA, premiumB);
  const cheaperInsurer = getCheaperInsurer(premiumA, premiumB, insurerA, insurerB);

  // Build explanation
  const explanation = buildExplanation(
    premiumDiff,
    premiumDiffPercent,
    cheaperInsurer,
    policyEvidenceA,
    policyEvidenceB
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold">보험료 비교 상세</h2>
        <p className="text-gray-600 mt-2">{coverageName}</p>
        {canonicalCoverageCode && (
          <p className="text-xs text-gray-500 mt-1">{canonicalCoverageCode}</p>
        )}
      </div>

      {/* Two-column Premium Comparison */}
      <div className="grid grid-cols-2 gap-4">
        <PremiumColumn
          insurer={insurerA}
          premiumResult={premiumResultA}
          isCheaper={cheaperInsurer === insurerA}
          premiumDiffPercent={cheaperInsurer === insurerB ? premiumDiffPercent : null}
        />
        <PremiumColumn
          insurer={insurerB}
          premiumResult={premiumResultB}
          isCheaper={cheaperInsurer === insurerB}
          premiumDiffPercent={cheaperInsurer === insurerA ? premiumDiffPercent : null}
        />
      </div>

      {/* Why Different? Section */}
      {explanation.show && (
        <Card>
          <div className="p-4">
            <h3 className="text-lg font-semibold mb-3">왜 보험료가 다른가요?</h3>

            {/* Explanation Reasons */}
            <div className="space-y-2">
              {explanation.reasons.map((reason, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-blue-600 mt-1">•</span>
                  <span className="text-gray-700">{reason}</span>
                </div>
              ))}
            </div>

            {/* Policy Evidence Link */}
            {explanation.hasPolicyEvidence && onViewPolicy && (
              <div className="mt-4 pt-4 border-t">
                <Button onClick={onViewPolicy} variant="secondary" size="sm">
                  📄 약관 근거 보기
                </Button>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Footer CTAs */}
      <div className="flex gap-4">
        <Button onClick={onCompareOther} variant="secondary">
          다른 보험사 비교
        </Button>
      </div>
    </div>
  );
}

/**
 * Premium Column (single insurer)
 */
function PremiumColumn({
  insurer,
  premiumResult,
  isCheaper,
  premiumDiffPercent,
}: {
  insurer: string;
  premiumResult: PremiumResult;
  isCheaper: boolean;
  premiumDiffPercent: number | null;
}) {
  const premium = premiumResult.nonCancellation.premium;
  const status = premiumResult.nonCancellation.status;

  return (
    <Card>
      <div className="p-4">
        {/* Insurer */}
        <h3 className="text-lg font-semibold mb-4">{insurer}</h3>

        {/* Premium */}
        <div className="space-y-2">
          {status === 'READY' ? (
            <>
              <div
                className={`text-2xl font-bold ${
                  isCheaper ? 'text-blue-600' : 'text-gray-900'
                }`}
              >
                월 {formatPremium(premium)}
              </div>

              {/* Badge */}
              {isCheaper && (
                <div className="inline-block px-2 py-1 bg-blue-100 text-blue-700 text-sm font-semibold rounded">
                  최저가
                </div>
              )}

              {/* Diff Percent */}
              {!isCheaper && premiumDiffPercent !== null && (
                <div className="text-sm text-gray-600">
                  (+{premiumDiffPercent}%)
                </div>
              )}
            </>
          ) : (
            <div className="text-gray-500">
              보험료 정보 없음
              <div className="text-xs mt-1">
                {premiumResult.nonCancellation.reason || '데이터 준비 중'}
              </div>
            </div>
          )}
        </div>

        {/* Plan Type Info (if general premium available) */}
        {premiumResult.general.status === 'READY' && (
          <div className="mt-4 pt-4 border-t text-sm text-gray-600">
            <div className="flex justify-between">
              <span>③ 무해지</span>
              <span className="font-semibold">
                {formatPremium(premiumResult.nonCancellation.premium)}
              </span>
            </div>
            <div className="flex justify-between mt-1">
              <span>② 일반</span>
              <span className="font-semibold">
                {formatPremium(premiumResult.general.premium)}
              </span>
            </div>
          </div>
        )}

        {/* Partial data warning */}
        {premiumResult.general.status === 'PARTIAL' && (
          <div className="mt-4 pt-4 border-t text-xs text-yellow-700">
            ⚠ 일반 보험료: {premiumResult.general.reason}
          </div>
        )}
      </div>
    </Card>
  );
}

/**
 * Build explanation for premium difference
 */
function buildExplanation(
  premiumDiff: number | null,
  premiumDiffPercent: number | null,
  cheaperInsurer: string | null,
  policyEvidenceA: any,
  policyEvidenceB: any
): {
  show: boolean;
  reasons: string[];
  hasPolicyEvidence: boolean;
} {
  // No explanation if no premium data
  if (premiumDiff === null || premiumDiffPercent === null) {
    return { show: false, reasons: [], hasPolicyEvidence: false };
  }

  // No explanation if difference is small (<5%)
  if (premiumDiffPercent < 5) {
    return { show: false, reasons: [], hasPolicyEvidence: false };
  }

  const reasons: string[] = [];
  let hasPolicyEvidence = false;

  // Check policy evidence differences
  if (policyEvidenceA && policyEvidenceB) {
    hasPolicyEvidence = true;

    // Exclusion period difference
    if (
      policyEvidenceA.exclusion_period_days !==
      policyEvidenceB.exclusion_period_days
    ) {
      reasons.push(
        `면책기간 차이: ${policyEvidenceA.exclusion_period_days || 0}일 vs ${
          policyEvidenceB.exclusion_period_days || 0
        }일`
      );
    }

    // Reduction period difference
    if (
      policyEvidenceA.reduction_period_years !==
      policyEvidenceB.reduction_period_years
    ) {
      reasons.push(
        `감액기간 차이: ${policyEvidenceA.reduction_period_years || 0}년 vs ${
          policyEvidenceB.reduction_period_years || 0
        }년`
      );
    }

    // Disease scope difference (placeholder)
    if (policyEvidenceA.disease_scope_raw !== policyEvidenceB.disease_scope_raw) {
      reasons.push('질병 범위 차이 (약관 확인 필요)');
    }
  }

  // Fallback explanation if no policy evidence differences found
  if (reasons.length === 0) {
    reasons.push('담보 조건은 동일하나 보험사 가격 정책 차이로 보험료가 다릅니다');
    if (cheaperInsurer) {
      reasons.push(`${cheaperInsurer}이(가) 약 ${premiumDiffPercent}% 저렴합니다`);
    }
  }

  return {
    show: true,
    reasons,
    hasPolicyEvidence,
  };
}
