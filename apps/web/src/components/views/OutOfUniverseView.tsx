/**
 * Out of Universe View (STEP 28)
 *
 * State: out_of_universe:REQUEST_MORE_INFO:COVERAGE_NOT_IN_UNIVERSE
 * Scenario: E
 *
 * Purpose: Inform user that query coverage does not exist in proposal universe
 */

import React from 'react';
import type { CompareResponse } from '@/lib/api/compareClient';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/Card';
import { Button } from '../ui/Button';

interface OutOfUniverseViewProps {
  response: CompareResponse;
  onSearchAgain: () => void;
  onSelectInsurer: () => void;
}

export function OutOfUniverseView({
  response,
  onSearchAgain,
  onSelectInsurer,
}: OutOfUniverseViewProps) {
  const query = response.query;
  const insurer = response.debug?.raw_name_used || 'SAMSUNG'; // Fallback from debug or assume

  return (
    <Card severity="info">
      <CardHeader>
        <CardTitle>📭 담보 없음</CardTitle>
        <CardDescription>
          해당 담보는 선택한 보험사의 가입설계서에 존재하지 않습니다
        </CardDescription>
      </CardHeader>

      <CardContent>
        <div className="bg-white border rounded-lg p-4 mb-4">
          <div className="space-y-3">
            <div>
              <span className="text-sm text-gray-600">검색한 담보:</span>
              <p className="font-bold text-lg">{query}</p>
            </div>
            <div>
              <span className="text-sm text-gray-600">확인한 보험사:</span>
              <p>{insurer}</p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-blue-50 rounded-lg mb-4">
          <div className="flex items-start gap-2">
            <span className="text-2xl">🔒</span>
            <div className="flex-1">
              <h4 className="font-bold mb-1">Universe Lock 원칙</h4>
              <p className="text-sm text-gray-700">
                STEP 6-C 헌법 원칙에 따라, 가입설계서에 없는 담보는 비교 대상이 될 수 없습니다.
                이는 시스템 오류가 아닌 정상적인 상태입니다.
              </p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-bold mb-2">💡 해결 방법</h4>
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
            <li>담보명을 다시 확인해주세요</li>
            <li>다른 보험사를 선택해주세요</li>
            <li>또는 보험사에 해당 담보 가입 가능 여부를 문의하세요</li>
          </ul>
        </div>

        {response.debug?.universe_lock_enforced && (
          <div className="mt-4 text-sm text-gray-500">
            <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs mr-2">
              Universe Lock 적용
            </span>
            가입설계서 기준 검증 완료
          </div>
        )}
      </CardContent>

      <CardFooter>
        <Button variant="primary" onClick={onSearchAgain}>
          🔍 다시 검색
        </Button>
        <Button variant="outline" onClick={onSelectInsurer}>
          🏢 다른 보험사 선택
        </Button>
      </CardFooter>
    </Card>
  );
}
