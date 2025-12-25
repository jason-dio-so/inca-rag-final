/**
 * Policy Required View (STEP 28)
 *
 * State: policy_required:VERIFY_POLICY:DISEASE_SCOPE_VERIFICATION_REQUIRED
 * Scenario: C
 *
 * Purpose: Inform user that policy verification is needed (disease scope)
 */

import React from 'react';
import type { CompareResponse } from '@/lib/api/compareClient';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/Card';
import { Button } from '../ui/Button';

interface PolicyRequiredViewProps {
  response: CompareResponse;
  onViewPolicy: () => void;
  onContinueComparison: () => void;
}

export function PolicyRequiredView({
  response,
  onViewPolicy,
  onContinueComparison,
}: PolicyRequiredViewProps) {
  const { coverage_a, policy_evidence_a } = response;

  return (
    <Card severity="info">
      <CardHeader>
        <CardTitle>ℹ️ 약관 확인 필요</CardTitle>
        <CardDescription>
          담보의 질병 범위를 확인하려면 약관 검증이 필요합니다
        </CardDescription>
      </CardHeader>

      <CardContent>
        {coverage_a && (
          <div className="bg-white border rounded-lg p-4 mb-4">
            <h3 className="font-bold mb-3">{coverage_a.insurer} - {coverage_a.coverage_name_raw}</h3>
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-gray-600">보장금액:</span>
                <p className="font-bold text-lg">
                  {coverage_a.amount_value ? `${(coverage_a.amount_value / 10000).toLocaleString()}만원` : 'N/A'}
                </p>
              </div>
              <div>
                <span className="text-gray-600">질병 범위 (원문):</span>
                <p className="bg-yellow-50 p-2 rounded mt-1">
                  {coverage_a.disease_scope_raw || 'N/A'}
                </p>
              </div>
              <div>
                <span className="inline-block px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs">
                  {coverage_a.source_confidence || 'UNKNOWN'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Policy Evidence */}
        {policy_evidence_a && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <h4 className="font-bold mb-2">📋 약관 근거 정보</h4>
            <div className="space-y-1 text-sm">
              <div>
                <span className="text-gray-600">질병 코드 그룹:</span>
                <p className="font-medium">{policy_evidence_a.group_name}</p>
              </div>
              <div>
                <span className="text-gray-600">보험사:</span>
                <p>{policy_evidence_a.insurer}</p>
              </div>
              <div>
                <span className="text-gray-600">코드 개수:</span>
                <p>{policy_evidence_a.member_count}개</p>
              </div>
            </div>
          </div>
        )}

        <div className="p-4 bg-orange-50 rounded-lg">
          <h4 className="font-bold mb-2">⚠️ 주의사항</h4>
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
            <li>질병 범위(disease_scope_norm)가 정의되어 있습니다</li>
            <li>정확한 비교를 위해 약관 검증이 권장됩니다</li>
            <li>약관 없이 진행할 경우 정보가 불완전할 수 있습니다</li>
          </ul>
        </div>
      </CardContent>

      <CardFooter>
        <Button variant="primary" onClick={onViewPolicy}>
          📄 약관 보기
        </Button>
        <Button variant="outline" onClick={onContinueComparison}>
          ⏭️ 비교 진행
        </Button>
      </CardFooter>
    </Card>
  );
}
