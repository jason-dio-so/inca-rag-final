/**
 * Unmapped View (STEP 28)
 *
 * State: unmapped:REQUEST_MORE_INFO:COVERAGE_UNMAPPED
 * Scenario: B
 *
 * Purpose: Inform user that coverage name is not in canonical mapping
 */

import React from 'react';
import type { CompareResponse } from '@/lib/api/compareClient';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/Card';
import { Button } from '../ui/Button';

interface UnmappedViewProps {
  response: CompareResponse;
  onSearchAgain: () => void;
  onContactSupport: () => void;
}

export function UnmappedView({ response, onSearchAgain, onContactSupport }: UnmappedViewProps) {
  const { coverage_a } = response;

  return (
    <Card severity="warning">
      <CardHeader>
        <CardTitle>⚠️ 담보 매핑 실패</CardTitle>
        <CardDescription>
          해당 담보는 아직 신정원 코드로 매핑되지 않았습니다
        </CardDescription>
      </CardHeader>

      <CardContent>
        {coverage_a && (
          <div className="bg-white border rounded-lg p-4">
            <div className="space-y-3">
              <div>
                <span className="text-sm text-gray-600">담보명:</span>
                <p className="font-bold text-lg">{coverage_a.coverage_name_raw}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">보험사:</span>
                <p>{coverage_a.insurer}</p>
              </div>
              <div>
                <span className="inline-block px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm">
                  {coverage_a.mapping_status}
                </span>
              </div>
            </div>
          </div>
        )}

        <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
          <h4 className="font-bold mb-2">💡 다음 단계</h4>
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
            <li>더 구체적인 담보명을 입력해주세요</li>
            <li>예: "일반암진단금", "유사암진단금" 등</li>
            <li>또는 관리자에게 매핑 요청을 문의하세요</li>
          </ul>
        </div>

        <div className="mt-4 text-sm text-gray-500">
          <p>현재 시스템에는 {coverage_a?.coverage_name_raw}에 대한 신정원 통일 코드 매핑 정보가 없습니다.</p>
          <p className="mt-1">Excel 매핑 파일에 해당 담보명이 존재하지 않습니다.</p>
        </div>
      </CardContent>

      <CardFooter>
        <Button variant="primary" onClick={onSearchAgain}>
          🔍 다시 검색
        </Button>
        <Button variant="outline" onClick={onContactSupport}>
          📧 관리자 문의
        </Button>
      </CardFooter>
    </Card>
  );
}
