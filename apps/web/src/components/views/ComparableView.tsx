/**
 * Comparable View (STEP 28)
 *
 * State: comparable:COMPARE:COVERAGE_MATCH_COMPARABLE
 * Scenarios: A, D
 *
 * Purpose: Show successful comparison between two insurers
 */

import React from 'react';
import type { CompareResponse } from '@/lib/api/compareClient';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/Card';
import { Button } from '../ui/Button';

interface ComparableViewProps {
  response: CompareResponse;
  onCompare: () => void;
  onSearchAgain: () => void;
}

export function ComparableView({ response, onCompare, onSearchAgain }: ComparableViewProps) {
  const { coverage_a, coverage_b } = response;

  const formatAmount = (amount: number | null) => {
    if (!amount) return 'N/A';
    return `${(amount / 10000).toLocaleString()}만원`;
  };

  return (
    <Card severity="success">
      <CardHeader>
        <CardTitle>✅ 비교 가능</CardTitle>
        <CardDescription>
          두 보험사 모두 동일한 담보를 보유하고 있습니다
        </CardDescription>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {/* Coverage A */}
          {coverage_a && (
            <div className="border rounded-lg p-4 bg-white">
              <h3 className="font-bold text-lg mb-2">{coverage_a.insurer}</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-gray-600">담보명:</span>
                  <p className="font-medium">{coverage_a.coverage_name_raw}</p>
                </div>
                <div>
                  <span className="text-gray-600">보장금액:</span>
                  <p className="font-bold text-xl text-blue-600">
                    {formatAmount(coverage_a.amount_value)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-600">질병 범위:</span>
                  <p>{coverage_a.disease_scope_raw || 'N/A'}</p>
                </div>
                <div className="pt-2">
                  <span className="inline-block px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                    {coverage_a.mapping_status}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Coverage B */}
          {coverage_b && (
            <div className="border rounded-lg p-4 bg-white">
              <h3 className="font-bold text-lg mb-2">{coverage_b.insurer}</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-gray-600">담보명:</span>
                  <p className="font-medium">{coverage_b.coverage_name_raw}</p>
                </div>
                <div>
                  <span className="text-gray-600">보장금액:</span>
                  <p className="font-bold text-xl text-blue-600">
                    {formatAmount(coverage_b.amount_value)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-600">질병 범위:</span>
                  <p>{coverage_b.disease_scope_raw || 'N/A'}</p>
                </div>
                <div className="pt-2">
                  <span className="inline-block px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                    {coverage_b.mapping_status}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Amount Comparison */}
        {coverage_a && coverage_b && coverage_a.amount_value && coverage_b.amount_value && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-bold mb-2">💰 보장금액 비교</h4>
            <div className="flex items-center justify-between">
              <span>{coverage_a.insurer}: {formatAmount(coverage_a.amount_value)}</span>
              <span className="text-gray-400">vs</span>
              <span>{coverage_b.insurer}: {formatAmount(coverage_b.amount_value)}</span>
            </div>
            <div className="mt-2 text-sm text-gray-600">
              차액: {formatAmount(Math.abs(coverage_a.amount_value - coverage_b.amount_value))}
            </div>
          </div>
        )}

        {/* Canonical Code */}
        {response.debug?.canonical_code_resolved && (
          <div className="mt-4 text-sm text-gray-500">
            신정원 통일 코드: <code className="bg-gray-100 px-2 py-1 rounded">{response.debug.canonical_code_resolved}</code>
          </div>
        )}
      </CardContent>

      <CardFooter>
        <Button variant="primary" onClick={onCompare}>
          📊 상세 비교하기
        </Button>
        <Button variant="outline" onClick={onSearchAgain}>
          🔍 다른 담보 검색
        </Button>
      </CardFooter>
    </Card>
  );
}
