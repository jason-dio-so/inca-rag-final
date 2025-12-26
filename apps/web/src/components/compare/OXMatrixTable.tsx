/**
 * O/X Matrix Table Renderer
 * Displays coverage availability in O/X format (Example 4: Disease-based comparison)
 *
 * Constitution:
 * - Fact-only: O (covered) / X (not covered) / — (unknown)
 * - NO judgment: "O is better" or "X is worse" expressions prohibited
 * - Presentation only: Display ViewModel data as-is
 *
 * Used when: factTable.table_type = "ox_matrix"
 */

import React from "react";
import type { FactTable as FactTableType } from "@/lib/compare/viewModelTypes";

interface OXMatrixTableProps {
  factTable: FactTableType;
}

export function OXMatrixTable({ factTable }: OXMatrixTableProps) {
  // Extract unique disease scopes from payout_conditions
  const getCoverageItems = () => {
    const items = new Set<string>();
    factTable.rows.forEach((row) => {
      row.payout_conditions.forEach((cond) => {
        if (cond.slot_key === "disease_scope" || cond.value_text) {
          items.add(cond.value_text);
        }
      });
    });
    return Array.from(items);
  };

  const coverageItems = getCoverageItems();

  // Get O/X status for insurer + coverage item
  const getOXStatus = (insurer: string, item: string): string => {
    const row = factTable.rows.find((r) => r.insurer === insurer);
    if (!row) return "—";

    // Check if coverage item is mentioned in payout_conditions
    const hasCoverage = row.payout_conditions.some((cond) =>
      cond.value_text.includes(item)
    );

    if (hasCoverage) {
      return row.benefit_amount ? "O" : "X";
    }

    return "—";
  };

  // Get unique insurers
  const insurers = Array.from(
    new Set(factTable.rows.map((row) => row.insurer))
  );

  return (
    <div className="mb-8">
      <div className="mb-2 text-sm font-medium text-gray-700">
        보장 가능 여부 (O: 보장, X: 미보장, —: 정보 없음)
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 border">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                담보 항목
              </th>
              {insurers.map((insurer) => (
                <th
                  key={insurer}
                  className="px-4 py-3 text-center text-sm font-semibold text-gray-700"
                >
                  {insurer}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {coverageItems.length === 0 ? (
              <tr>
                <td
                  colSpan={insurers.length + 1}
                  className="px-4 py-8 text-center text-sm text-gray-500"
                >
                  비교 데이터 없음
                </td>
              </tr>
            ) : (
              coverageItems.map((item, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {item}
                  </td>
                  {insurers.map((insurer) => {
                    const status = getOXStatus(insurer, item);
                    return (
                      <td
                        key={insurer}
                        className={`px-4 py-3 text-center text-sm font-bold ${
                          status === "O"
                            ? "text-green-600"
                            : status === "X"
                            ? "text-red-600"
                            : "text-gray-400"
                        }`}
                      >
                        {status}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Constitutional note: NO judgment text */}
      <div className="mt-2 text-xs text-gray-500">
        ※ 정확한 보장 범위는 약관 확인이 필요합니다
      </div>
    </div>
  );
}
