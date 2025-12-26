/**
 * BLOCK 2: FactTable
 * Comparison table with fixed column order
 *
 * Constitution:
 * - Fixed column order (no reordering)
 * - Display rows in ViewModel order (no frontend sorting)
 * - Show "—" for null benefit_amount
 * - Display payout_conditions as bullet list (slot_key + value_text)
 * - No interpretation text generation
 * - v2: Support table_type (default | ox_matrix)
 * - v2: Support visual_emphasis (UI hint only, NO ranking/judgment)
 * - v2: Support highlight (difference detection, NO superiority judgment)
 */

import React from "react";
import type {
  FactTable as FactTableType,
  FactTableRow,
} from "@/lib/compare/viewModelTypes";
import { OXMatrixTable } from "./OXMatrixTable";

interface FactTableProps {
  factTable: FactTableType;
}

// Visual emphasis styles (UI hint only, NO judgment)
const MIN_VALUE_STYLES = {
  blue: "bg-blue-50 border-blue-200",
  green: "bg-green-50 border-green-200",
  default: "",
};

const MAX_VALUE_STYLES = {
  red: "bg-red-50 border-red-200",
  orange: "bg-orange-50 border-orange-200",
  default: "",
};

const SLOT_KEY_LABELS: Record<string, string> = {
  waiting_period: "대기기간",
  payment_frequency: "지급횟수",
  diagnosis_definition: "진단정의",
  method_condition: "수술방법",
  exclusion_scope: "제외사항",
  payout_limit: "지급한도",
  disease_scope: "질병범위",
};

export function FactTable({ factTable }: FactTableProps) {
  const { table_type = "default", sort_metadata, visual_emphasis } = factTable;

  // v2: Render O/X matrix table when table_type = "ox_matrix"
  if (table_type === "ox_matrix") {
    return <OXMatrixTable factTable={factTable} />;
  }

  // Helper: Check if cell should be highlighted
  const isCellHighlighted = (row: FactTableRow, cellKey: string): boolean => {
    return row.highlight?.includes(cellKey) ?? false;
  };

  // v2: Display sort metadata (fact-only, NO ranking)
  const sortLabel = sort_metadata
    ? `정렬: ${sort_metadata.sort_by} (${
        sort_metadata.sort_order === "asc" ? "오름차순" : "내림차순"
      })${sort_metadata.limit ? ` / 상위 ${sort_metadata.limit}개` : ""}`
    : null;

  return (
    <div className="mb-8">
      {/* v2: Sort metadata display (fact-only) */}
      {sortLabel && (
        <div className="mb-2 text-sm text-gray-600">
          {sortLabel}
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 border">
          <thead className="bg-gray-100">
            <tr>
              {factTable.columns.map((col, idx) => (
                <th
                  key={idx}
                  className="px-4 py-3 text-left text-sm font-semibold text-gray-700"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {factTable.rows.length === 0 ? (
              <tr>
                <td
                  colSpan={factTable.columns.length}
                  className="px-4 py-8 text-center text-sm text-gray-500"
                >
                  비교 데이터 없음
                </td>
              </tr>
            ) : (
              factTable.rows.map((row, rowIdx) => (
                <tr key={rowIdx} className="hover:bg-gray-50">
                  {/* Column 1: 보험사 */}
                  <td
                    className={`px-4 py-3 text-sm font-medium text-gray-900 ${
                      isCellHighlighted(row, "insurer") ? "bg-yellow-50" : ""
                    }`}
                  >
                    {row.insurer}
                  </td>

                  {/* Column 2: 담보명(정규화) */}
                  <td
                    className={`px-4 py-3 text-sm text-gray-900 ${
                      isCellHighlighted(row, "coverage_title_normalized")
                        ? "bg-yellow-50"
                        : ""
                    }`}
                  >
                    {row.coverage_title_normalized}
                  </td>

                  {/* Column 3: 보장금액 */}
                  <td
                    className={`px-4 py-3 text-sm text-gray-900 ${
                      isCellHighlighted(row, "benefit_amount") ||
                      isCellHighlighted(row, "amount_value")
                        ? "bg-yellow-50"
                        : ""
                    }`}
                  >
                    {row.benefit_amount ? row.benefit_amount.display_text : "—"}
                  </td>

                  {/* Column 4: 지급 조건 요약 */}
                  <td
                    className={`px-4 py-3 text-sm text-gray-700 ${
                      isCellHighlighted(row, "payout_conditions") ||
                      isCellHighlighted(row, "payout_limit")
                        ? "bg-yellow-50"
                        : ""
                    }`}
                  >
                    {row.payout_conditions.length > 0 ? (
                      <ul className="list-inside list-disc space-y-1">
                        {row.payout_conditions.map((cond, condIdx) => (
                          <li key={condIdx}>
                            <span className="font-medium">
                              {SLOT_KEY_LABELS[cond.slot_key] || cond.slot_key}:
                            </span>{" "}
                            {cond.value_text}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>

                  {/* Column 5: 보험기간 */}
                  <td
                    className={`px-4 py-3 text-sm text-gray-700 ${
                      isCellHighlighted(row, "term_text") ? "bg-yellow-50" : ""
                    }`}
                  >
                    {row.term_text || "—"}
                  </td>

                  {/* Column 6: 비고 */}
                  <td
                    className={`px-4 py-3 text-sm text-gray-500 ${
                      isCellHighlighted(row, "note_text") ? "bg-yellow-50" : ""
                    }`}
                  >
                    {row.note_text || "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
