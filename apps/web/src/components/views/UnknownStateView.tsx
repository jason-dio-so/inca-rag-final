/**
 * Unknown State View (STEP 28)
 *
 * State: FALLBACK_STATE (any unknown combination)
 *
 * Purpose: Graceful degradation for unknown Backend Contract states
 */

import React from 'react';
import type { CompareResponse } from '@/lib/api/compareClient';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/Card';
import { Button } from '../ui/Button';

interface UnknownStateViewProps {
  response: CompareResponse;
  onRetry: () => void;
  onContactSupport: () => void;
}

export function UnknownStateView({
  response,
  onRetry,
  onContactSupport,
}: UnknownStateViewProps) {
  const stateKey = `${response.comparison_result}:${response.next_action}:${response.ux_message_code}`;

  return (
    <Card severity="warning">
      <CardHeader>
        <CardTitle>⏳ 처리 중</CardTitle>
        <CardDescription>
          요청하신 담보 정보를 확인하고 있습니다
        </CardDescription>
      </CardHeader>

      <CardContent>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <h4 className="font-bold mb-2">ℹ️ 상태 정보</h4>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-gray-600">검색 담보:</span>
              <p className="font-medium">{response.query}</p>
            </div>
            <div>
              <span className="text-gray-600">시스템 메시지:</span>
              <p className="italic">{response.message}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 border rounded-lg p-4 mb-4">
          <h4 className="font-bold mb-2 text-sm">🔧 디버그 정보</h4>
          <div className="space-y-1 text-xs text-gray-600 font-mono">
            <div>State Key: <code className="bg-white px-1 py-0.5 rounded">{stateKey}</code></div>
            <div>Comparison Result: <code className="bg-white px-1 py-0.5 rounded">{response.comparison_result}</code></div>
            <div>Next Action: <code className="bg-white px-1 py-0.5 rounded">{response.next_action}</code></div>
            <div>UX Message Code: <code className="bg-white px-1 py-0.5 rounded">{response.ux_message_code}</code></div>
          </div>
        </div>

        <div className="p-4 bg-orange-50 rounded-lg">
          <h4 className="font-bold mb-2">⚠️ Contract Drift 감지</h4>
          <p className="text-sm text-gray-700 mb-2">
            이 상태는 UI State Map에 정의되지 않은 새로운 Backend Contract 상태입니다.
          </p>
          <p className="text-sm text-gray-700">
            시스템은 FALLBACK_STATE로 처리했지만, UI Contract 업데이트가 필요할 수 있습니다.
          </p>
        </div>

        <div className="mt-4 text-sm text-gray-500">
          <p>이 메시지는 모니터링 시스템에 자동으로 기록되었습니다.</p>
          <p className="mt-1">관리자가 확인 중입니다.</p>
        </div>
      </CardContent>

      <CardFooter>
        <Button variant="primary" onClick={onRetry}>
          🔄 다시 시도
        </Button>
        <Button variant="outline" onClick={onContactSupport}>
          📧 관리자 문의
        </Button>
      </CardFooter>
    </Card>
  );
}
