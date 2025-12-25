/**
 * Scenario Switcher (STEP 28 - DEV_MOCK_MODE)
 *
 * Allows developers to test all golden snapshot scenarios without real API calls.
 *
 * Constitutional Rules:
 * - Only available when DEV_MOCK_MODE=1
 * - Loads golden snapshots directly
 * - Scenarios: A, B, C, D, E, UNKNOWN
 */

import React from 'react';
import type { ScenarioId } from '@/lib/api/compareClient';

interface ScenarioSwitcherProps {
  currentScenario: ScenarioId | null;
  onSelectScenario: (scenarioId: ScenarioId) => void;
}

const SCENARIO_DESCRIPTIONS: Record<ScenarioId, string> = {
  A: '✅ Comparable (SAMSUNG vs MERITZ - 일반암)',
  B: '⚠️ Unmapped (KB - 매핑안된담보)',
  C: 'ℹ️ Policy Required (SAMSUNG - 유사암)',
  D: '✅ Comparable (KB vs MERITZ - 일반암)',
  E: '📭 Out of Universe (SAMSUNG - 다빈치 수술비)',
  UNKNOWN: '⏳ Unknown State (Contract Drift Test)',
};

export function ScenarioSwitcher({ currentScenario, onSelectScenario }: ScenarioSwitcherProps) {
  const isMockMode = process.env.DEV_MOCK_MODE === '1';

  if (!isMockMode) {
    return null;
  }

  return (
    <div className="bg-purple-50 border-2 border-purple-500 rounded-lg p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl">🧪</span>
        <h3 className="font-bold text-purple-900">DEV_MOCK_MODE - Scenario Switcher</h3>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {(Object.keys(SCENARIO_DESCRIPTIONS) as ScenarioId[]).map((scenarioId) => (
          <button
            key={scenarioId}
            onClick={() => onSelectScenario(scenarioId)}
            className={`
              text-left px-3 py-2 rounded border-2 transition-colors
              ${
                currentScenario === scenarioId
                  ? 'bg-purple-600 text-white border-purple-700'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-purple-400'
              }
            `}
          >
            <div className="font-bold text-sm">Scenario {scenarioId}</div>
            <div className="text-xs mt-1 opacity-90">
              {SCENARIO_DESCRIPTIONS[scenarioId]}
            </div>
          </button>
        ))}
      </div>

      <div className="mt-3 text-xs text-purple-800">
        <p>💡 Click a scenario to load golden snapshot data (no API call)</p>
        <p className="mt-1">Set DEV_MOCK_MODE=0 to disable mock mode</p>
      </div>
    </div>
  );
}
