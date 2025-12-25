/**
 * Price Ranking View (STEP 31)
 *
 * Displays Top-N proposals sorted by premium (cheapest first)
 *
 * Constitutional Principle:
 * - Comparison target = Proposals (not policies)
 * - Premium = proposal field (not calculated)
 * - Data absence ≠ error (show placeholders)
 */

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import type { PremiumCardData } from '@/lib/premium/types';
import type { PriceStateConfig } from '@/contracts/priceStateMap';
import { formatPremium } from '@/lib/premium/calc';

export interface PriceRankingViewProps {
  cards: PremiumCardData[];
  stateConfig: PriceStateConfig;
  onCompare: (proposalIdA: string, proposalIdB: string) => void;
  onSearchAgain: () => void;
}

export function PriceRankingView({
  cards,
  stateConfig,
  onCompare,
  onSearchAgain,
}: PriceRankingViewProps) {
  const availableCards = cards.filter(
    (card) => card.premiumResult.nonCancellation.status === 'READY'
  );
  const unavailableCards = cards.filter(
    (card) => card.premiumResult.nonCancellation.status !== 'READY'
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold">{stateConfig.title}</h2>
        <p className="text-gray-600 mt-2">
          {stateConfig.description.replace('{N}', availableCards.length.toString())}
        </p>

        {/* Warning for PRICE_DATA_PARTIAL */}
        {stateConfig.state === 'PRICE_DATA_PARTIAL' && unavailableCards.length > 0 && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <p className="text-sm text-yellow-800">
              ⚠ 일부 보험사의 보험료 정보가 준비 중입니다 (현재 {availableCards.length}개 보험사 비교 가능)
            </p>
          </div>
        )}
      </div>

      {/* Available Cards */}
      {availableCards.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold">비교 가능</h3>
          {availableCards.map((card) => (
            <PremiumCard
              key={card.proposalId}
              card={card}
              onCompare={(proposalId) => {
                // Compare against the cheapest (rank 1)
                const cheapest = availableCards[0];
                if (proposalId !== cheapest.proposalId) {
                  onCompare(cheapest.proposalId, proposalId);
                }
              }}
            />
          ))}
        </div>
      )}

      {/* Unavailable Cards (placeholders) */}
      {unavailableCards.length > 0 && (
        <div className="space-y-3 mt-6">
          <h3 className="text-lg font-semibold text-gray-500">데이터 준비 중</h3>
          {unavailableCards.map((card) => (
            <PremiumCardPlaceholder key={card.proposalId} card={card} />
          ))}
        </div>
      )}

      {/* Footer CTAs */}
      <div className="flex gap-4 pt-4 border-t">
        <Button onClick={onSearchAgain} variant="secondary">
          다른 담보 검색
        </Button>
      </div>
    </div>
  );
}

/**
 * Premium Card (with data)
 */
function PremiumCard({
  card,
  onCompare,
}: {
  card: PremiumCardData;
  onCompare: (proposalId: string) => void;
}) {
  const premium = card.premiumResult.nonCancellation.premium;
  const isLowest = card.rank === 1;

  return (
    <Card>
      <div className="flex items-center justify-between p-4">
        {/* Rank + Insurer */}
        <div className="flex items-center gap-4">
          <div
            className={`text-2xl font-bold ${
              isLowest ? 'text-blue-600' : 'text-gray-700'
            }`}
          >
            {card.rank}위
          </div>
          <div>
            <div className="font-semibold text-lg">{card.insurer}</div>
            {card.canonicalCoverageCode && (
              <div className="text-xs text-gray-500">
                {card.canonicalCoverageCode}
              </div>
            )}
          </div>
        </div>

        {/* Premium */}
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div
              className={`text-xl font-bold ${
                isLowest ? 'text-blue-600' : 'text-gray-900'
              }`}
            >
              월 {formatPremium(premium)}
            </div>
            {isLowest && (
              <div className="text-sm text-blue-600 font-semibold">최저가</div>
            )}
          </div>

          {/* CTA */}
          {!isLowest && (
            <Button onClick={() => onCompare(card.proposalId)} size="sm">
              비교하기
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}

/**
 * Premium Card Placeholder (no data)
 */
function PremiumCardPlaceholder({ card }: { card: PremiumCardData }) {
  const status = card.premiumResult.nonCancellation.status;
  const reason = card.premiumResult.nonCancellation.reason || '데이터 준비 중';

  return (
    <Card>
      <div className="flex items-center justify-between p-4 opacity-60">
        {/* Rank + Insurer */}
        <div className="flex items-center gap-4">
          <div className="text-2xl font-bold text-gray-400">-</div>
          <div>
            <div className="font-semibold text-lg text-gray-600">{card.insurer}</div>
            <div className="text-xs text-gray-500">{reason}</div>
          </div>
        </div>

        {/* Status Badge */}
        <div className="text-right">
          <div className="text-sm text-gray-500">
            {status === 'PARTIAL' ? '일부 데이터' : '보험료 정보 없음'}
          </div>
        </div>
      </div>
    </Card>
  );
}
