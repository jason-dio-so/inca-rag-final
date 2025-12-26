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
  const { filter_criteria } = snapshot;

  return (
    <div className="mb-8 rounded-lg border bg-gray-50 p-6">
      <h2 className="mb-4 text-base font-semibold text-gray-700">
        비교 기준: {snapshot.comparison_basis}
      </h2>

      {/* v2: Filter Criteria Display (fact-only) */}
      {filter_criteria && (
        <div className="mb-4 rounded-md bg-blue-50 p-3 text-sm text-gray-700">
          <div className="font-medium text-gray-800 mb-1">필터 조건:</div>
          <ul className="list-inside list-disc space-y-1">
            {filter_criteria.insurer_filter && (
              <li>보험사: {filter_criteria.insurer_filter.join(", ")}</li>
            )}
            {filter_criteria.disease_scope && (
              <li>질병 범위: {filter_criteria.disease_scope.join(", ")}</li>
            )}
            {filter_criteria.slot_key && (
              <li>비교 항목: {filter_criteria.slot_key}</li>
            )}
            {filter_criteria.difference_detected !== undefined && (
              <li>
                차이 감지:{" "}
                {filter_criteria.difference_detected ? "있음" : "없음"}
              </li>
            )}
          </ul>
        </div>
      )}

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
