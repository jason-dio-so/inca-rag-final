/**
 * BLOCK 1: CoverageSnapshot
 * Per-insurer snapshot with headline amount/status
 *
 * Constitution:
 * - Display facts only (no "same/different" interpretation)
 * - Show status as-is when headline_amount is null
 * - No reordering (use ViewModel order)
 */

import React from "react";
import type { Snapshot } from "@/lib/compare/viewModelTypes";

interface CoverageSnapshotProps {
  snapshot: Snapshot;
}

const STATUS_DISPLAY: Record<string, string> = {
  OK: "OK",
  MISSING_EVIDENCE: "약관 확인 필요",
  UNMAPPED: "매핑 미완료",
  AMBIGUOUS: "매핑 모호",
  OUT_OF_UNIVERSE: "가입설계서 미포함",
};

export function CoverageSnapshot({ snapshot }: CoverageSnapshotProps) {
  return (
    <div className="mb-8 rounded-lg border bg-gray-50 p-6">
      <h2 className="mb-4 text-base font-semibold text-gray-700">
        비교 기준: {snapshot.comparison_basis}
      </h2>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {snapshot.insurers.map((insurer) => (
          <div
            key={insurer.insurer}
            className="rounded-md border bg-white p-4 shadow-sm"
          >
            <div className="mb-2 text-sm font-medium text-gray-600">
              {insurer.insurer}
            </div>
            {insurer.headline_amount ? (
              <div className="text-2xl font-bold text-blue-600">
                {insurer.headline_amount.display_text}
              </div>
            ) : (
              <div className="text-sm text-gray-500">
                {STATUS_DISPLAY[insurer.status] || insurer.status}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
