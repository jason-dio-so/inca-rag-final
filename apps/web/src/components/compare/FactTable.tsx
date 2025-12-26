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
 */

import React from "react";
import type { FactTable as FactTableType } from "@/lib/compare/viewModelTypes";

interface FactTableProps {
  factTable: FactTableType;
}

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
  return (
    <div className="mb-8 overflow-x-auto">
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
                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                  {row.insurer}
                </td>

                {/* Column 2: 담보명(정규화) */}
                <td className="px-4 py-3 text-sm text-gray-900">
                  {row.coverage_title_normalized}
                </td>

                {/* Column 3: 보장금액 */}
                <td className="px-4 py-3 text-sm text-gray-900">
                  {row.benefit_amount ? row.benefit_amount.display_text : "—"}
                </td>

                {/* Column 4: 지급 조건 요약 */}
                <td className="px-4 py-3 text-sm text-gray-700">
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
                <td className="px-4 py-3 text-sm text-gray-700">
                  {row.term_text || "—"}
                </td>

                {/* Column 6: 비고 */}
                <td className="px-4 py-3 text-sm text-gray-500">
                  {row.note_text || "—"}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
