/**
 * Main Compare Page (STEP 28)
 *
 * ChatGPT-style layout:
 * - Left: Chat/Input panel
 * - Right: Result panel (Contract-driven View)
 *
 * Features:
 * - DEV_MOCK_MODE: Scenario switcher
 * - Real/Mock API calls
 * - Contract-driven rendering
 * - STEP 33-β: DEV Premium API triggers (for live request capture)
 */

import React, { useState } from 'react';
import { compareClient, CompareResponse, ScenarioId } from '@/lib/api/compareClient';
import { ViewRenderer } from '@/components/ViewRenderer';
import { ScenarioSwitcher } from '@/components/ScenarioSwitcher';
import { Button } from '@/components/ui/Button';
import type { SimplePremiumRequest, OnepagePremiumRequest, PremiumProxyResponse } from '@/lib/api/premium/types';

export default function ComparePage() {
  const [query, setQuery] = useState('일반암진단비');
  const [insurerA, setInsurerA] = useState('SAMSUNG');
  const [insurerB, setInsurerB] = useState('MERITZ');
  const [response, setResponse] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentScenario, setCurrentScenario] = useState<ScenarioId | null>(null);

  const isMockMode = process.env.DEV_MOCK_MODE === '1';

  const handleCompare = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await compareClient.compare({
        query,
        insurer_a: insurerA,
        insurer_b: insurerB,
        include_policy_evidence: true,
      });
      setResponse(result);
      setCurrentScenario(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleScenarioSelect = async (scenarioId: ScenarioId) => {
    setLoading(true);
    setError(null);
    try {
      const result = await compareClient.loadScenario(scenarioId);
      setResponse(result);
      setCurrentScenario(scenarioId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleAction = (action: string, data?: any) => {
    console.log('User action:', action, data);

    switch (action) {
      case 'search_again':
        setResponse(null);
        break;
      case 'compare':
        alert('상세 비교 페이지로 이동 (구현 예정)');
        break;
      case 'view_policy':
        alert('약관 원문 뷰어 (데이터 준비 중 - inca-rag dependency)');
        break;
      case 'continue_comparison':
        alert('약관 없이 비교 진행');
        break;
      case 'select_insurer':
        setResponse(null);
        break;
      case 'contact_support':
        alert('관리자 문의 (이메일 또는 채팅)');
        break;
      case 'retry':
        handleCompare();
        break;
    }
  };

  /**
   * DEV PREMIUM TRIGGERS (STEP 33-β)
   *
   * Purpose: Generate live Premium API requests for Network capture
   * SSOT: docs/api/premium_api_spec.md
   */
  const handlePremiumSimpleCompare = async () => {
    console.log('[DEV] Premium Simple Compare - Request sent');

    // SSOT-based request payload (fixed test values)
    const request: SimplePremiumRequest = {
      baseDt: '20251225',
      birthday: '19760101',
      customerNm: '홍길동',
      sex: '1',
      age: '50',
    };

    try {
      const response = await fetch('/api/premium/simple-compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      const data: PremiumProxyResponse = await response.json();
      console.log('[DEV] Premium Simple Compare - Response:', data);
      alert(`Simple Compare OK: ${data.items.length} items (check Network tab)`);
    } catch (err) {
      console.error('[DEV] Premium Simple Compare - Error:', err);
      alert(`Simple Compare FAIL: ${err instanceof Error ? err.message : 'Unknown'}`);
    }
  };

  const handlePremiumOnepageCompare = async () => {
    console.log('[DEV] Premium Onepage Compare - Request sent');

    // SSOT-based request payload (fixed test values)
    const request: OnepagePremiumRequest = {
      baseDt: '20251225',
      birthday: '19760101',
      customerNm: '홍길동',
      sex: '1',
      age: '50',
    };

    try {
      const response = await fetch('/api/premium/onepage-compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      const data: PremiumProxyResponse = await response.json();
      console.log('[DEV] Premium Onepage Compare - Response:', data);
      alert(`Onepage Compare OK: ${data.items.length} items (check Network tab)`);
    } catch (err) {
      console.error('[DEV] Premium Onepage Compare - Error:', err);
      alert(`Onepage Compare FAIL: ${err instanceof Error ? err.message : 'Unknown'}`);
    }
  };

  /**
   * STEP 33-β-1c: Experimental tests for 400 root cause
   */
  const handlePremiumSimpleASCII = async () => {
    console.log('[DEV] Premium Simple (ASCII customerNm) - Request sent');

    const request: SimplePremiumRequest = {
      baseDt: '20251225',
      birthday: '19760101',
      customerNm: 'Hong', // ASCII only
      sex: '1',
      age: '50',
    };

    try {
      const response = await fetch('/api/premium/simple-compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      const data: PremiumProxyResponse = await response.json();
      console.log('[DEV] Premium Simple ASCII - Response:', data);
      alert(`Simple ASCII: ${response.status} - ${data.items.length} items`);
    } catch (err) {
      console.error('[DEV] Premium Simple ASCII - Error:', err);
      alert(`Simple ASCII FAIL: ${err instanceof Error ? err.message : 'Unknown'}`);
    }
  };

  const handlePremiumSimpleNoName = async () => {
    console.log('[DEV] Premium Simple (No customerNm) - Request sent');

    const request = {
      baseDt: '20251225',
      birthday: '19760101',
      // customerNm omitted
      sex: '1',
      age: '50',
    };

    try {
      const response = await fetch('/api/premium/simple-compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      const data: PremiumProxyResponse = await response.json();
      console.log('[DEV] Premium Simple NoName - Response:', data);
      alert(`Simple NoName: ${response.status} - ${data.items.length} items`);
    } catch (err) {
      console.error('[DEV] Premium Simple NoName - Error:', err);
      alert(`Simple NoName FAIL: ${err instanceof Error ? err.message : 'Unknown'}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold">보험 담보 비교 시스템</h1>
          <p className="text-sm text-gray-600 mt-1">
            STEP 28 - Contract-driven Frontend MVP
            {isMockMode && <span className="ml-2 px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">DEV_MOCK_MODE</span>}
          </p>
        </div>
      </header>

      {/* Main Content - ChatGPT Style Layout */}
      <div className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Panel - Input/Chat */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">🔍 담보 비교 검색</h2>

            {/* Scenario Switcher (DEV_MOCK_MODE) */}
            {isMockMode && (
              <ScenarioSwitcher
                currentScenario={currentScenario}
                onSelectScenario={handleScenarioSelect}
              />
            )}

            {/* Input Form */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">담보명</label>
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="예: 일반암진단비"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">보험사 A</label>
                  <select
                    value={insurerA}
                    onChange={(e) => setInsurerA(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="SAMSUNG">삼성생명</option>
                    <option value="MERITZ">메리츠화재</option>
                    <option value="KB">KB손해보험</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">보험사 B</label>
                  <select
                    value={insurerB}
                    onChange={(e) => setInsurerB(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="MERITZ">메리츠화재</option>
                    <option value="SAMSUNG">삼성생명</option>
                    <option value="KB">KB손해보험</option>
                  </select>
                </div>
              </div>

              <Button
                variant="primary"
                onClick={handleCompare}
                disabled={loading}
                className="w-full"
              >
                {loading ? '검색 중...' : '🔍 비교하기'}
              </Button>
            </div>

            {/* Error Display */}
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <h4 className="font-bold text-red-800 mb-1">⚠️ 시스템 오류</h4>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Info Box */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-bold mb-2 text-sm">💡 사용 방법</h3>
              <ul className="text-xs text-gray-600 space-y-1">
                <li>• 비교하려는 담보명을 입력하세요</li>
                <li>• 2개 보험사를 선택하세요</li>
                <li>• DEV 모드: 시나리오 버튼으로 테스트</li>
              </ul>
            </div>

            {/* DEV Premium Triggers (STEP 33-β) */}
            <div className="mt-6 p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <h3 className="font-bold mb-3 text-sm text-orange-800">🧪 DEV: Premium API Triggers</h3>
              <p className="text-xs text-orange-700 mb-3">
                Network 탭에서 Request/Response 캡처용 (STEP 33-β)
              </p>
              <div className="space-y-2">
                <Button
                  variant="secondary"
                  onClick={handlePremiumSimpleCompare}
                  className="w-full text-xs"
                >
                  [DEV] Premium Simple Compare
                </Button>
                <Button
                  variant="secondary"
                  onClick={handlePremiumOnepageCompare}
                  className="w-full text-xs"
                >
                  [DEV] Premium Onepage Compare
                </Button>
              </div>
              <p className="text-xs text-orange-600 mt-2">
                ⚠️ 버튼 클릭 후 DevTools → Network 탭 확인
              </p>

              {/* STEP 33-β-1c: Experimental tests */}
              <div className="mt-3 pt-3 border-t border-orange-300">
                <p className="text-xs font-bold text-orange-800 mb-2">🔬 실험: 400 원인 분리</p>
                <div className="space-y-2">
                  <Button
                    variant="secondary"
                    onClick={handlePremiumSimpleASCII}
                    className="w-full text-xs"
                  >
                    [TEST] Simple (customerNm=ASCII)
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={handlePremiumSimpleNoName}
                    className="w-full text-xs"
                  >
                    [TEST] Simple (No customerNm)
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Right Panel - Result */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">📊 비교 결과</h2>

            {!response && !loading && (
              <div className="text-center py-12 text-gray-400">
                <div className="text-6xl mb-4">🔍</div>
                <p>담보를 검색하거나 시나리오를 선택하세요</p>
              </div>
            )}

            {loading && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4 animate-pulse">⏳</div>
                <p className="text-gray-600">결과를 가져오는 중...</p>
              </div>
            )}

            {response && (
              <ViewRenderer response={response} onAction={handleAction} />
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-12 py-6 border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 text-center text-sm text-gray-600">
          <p>🤖 STEP 28 - Contract-driven Frontend MVP</p>
          <p className="mt-1">Backend Contract: STEP 14-26 (Frozen) | UI Contract: STEP 27 (SSOT)</p>
        </div>
      </footer>
    </div>
  );
}
