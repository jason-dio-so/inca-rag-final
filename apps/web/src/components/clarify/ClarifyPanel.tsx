/**
 * ClarifyPanel - Selection UI for ambiguous queries
 *
 * Constitutional Principles:
 * - No recommendation/judgment
 * - Presentation only (show options, let user choose)
 * - No inference (all options come from backend rules)
 */

import React from "react";
import type {
  ClarificationRequirement,
  UserSelections,
  SurgeryMethod,
  CancerSubtype,
  ComparisonFocus,
} from "@/lib/clarify/types";

interface ClarifyPanelProps {
  requirements: ClarificationRequirement[];
  selections: UserSelections;
  onSelectionsChange: (selections: UserSelections) => void;
  onConfirm: () => void;
}

const INSURER_OPTIONS = [
  { code: "SAMSUNG", name: "삼성화재" },
  { code: "MERITZ", name: "메리츠화재" },
  { code: "HANWHA", name: "한화생명" },
  { code: "HYUNDAI", name: "현대해상" },
  { code: "HEUNGKUK", name: "흥국화재" },
];

export function ClarifyPanel({
  requirements,
  selections,
  onSelectionsChange,
  onConfirm,
}: ClarifyPanelProps) {
  const handleInsurerToggle = (insurerCode: string) => {
    const current = selections.insurers || [];
    const updated = current.includes(insurerCode)
      ? current.filter((c) => c !== insurerCode)
      : [...current, insurerCode];
    onSelectionsChange({ ...selections, insurers: updated });
  };

  const handleSurgeryMethodChange = (method: SurgeryMethod) => {
    onSelectionsChange({ ...selections, surgery_method: method });
  };

  const handleCancerSubtypeToggle = (subtype: CancerSubtype) => {
    const current = selections.cancer_subtypes || [];
    const updated = current.includes(subtype)
      ? current.filter((s) => s !== subtype)
      : [...current, subtype];
    onSelectionsChange({ ...selections, cancer_subtypes: updated });
  };

  const handleComparisonFocusChange = (focus: ComparisonFocus) => {
    onSelectionsChange({ ...selections, comparison_focus: focus });
  };

  const canConfirm = () => {
    // Check if all required selections are filled
    for (const req of requirements) {
      if (req.type === "insurers") {
        if (!selections.insurers || selections.insurers.length < (req.min_required || 2)) {
          return false;
        }
      }
      // Other requirements are optional
    }
    return true;
  };

  return (
    <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
      <h3 className="mb-3 text-lg font-semibold text-blue-900">
        Select Comparison Options
      </h3>
      <div className="space-y-4">
        {requirements.map((req, idx) => (
          <div key={idx} className="rounded-md border border-blue-300 bg-white p-3">
            <p className="mb-2 text-sm font-medium text-gray-700">{req.reason}</p>

            {req.type === "insurers" && (
              <div className="space-y-2">
                <p className="text-xs text-gray-500">
                  Select at least {req.min_required || 2} insurers:
                </p>
                <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
                  {INSURER_OPTIONS.map((insurer) => (
                    <label
                      key={insurer.code}
                      className="flex cursor-pointer items-center gap-2 rounded border border-gray-300 p-2 hover:bg-gray-50"
                    >
                      <input
                        type="checkbox"
                        checked={selections.insurers?.includes(insurer.code) || false}
                        onChange={() => handleInsurerToggle(insurer.code)}
                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm">{insurer.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {req.type === "surgery_method" && req.options && (
              <div className="space-y-2">
                {req.options.map((option) => (
                  <label
                    key={option}
                    className="flex cursor-pointer items-center gap-2 rounded border border-gray-300 p-2 hover:bg-gray-50"
                  >
                    <input
                      type="radio"
                      name="surgery_method"
                      value={option}
                      checked={selections.surgery_method === option}
                      onChange={() => handleSurgeryMethodChange(option as SurgeryMethod)}
                      className="h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm capitalize">{option.replace("_", " ")}</span>
                  </label>
                ))}
              </div>
            )}

            {req.type === "cancer_subtypes" && req.options && (
              <div className="space-y-2">
                <p className="text-xs text-gray-500">
                  Detected: {req.detected?.join(", ")}
                </p>
                {req.options.map((option) => (
                  <label
                    key={option}
                    className="flex cursor-pointer items-center gap-2 rounded border border-gray-300 p-2 hover:bg-gray-50"
                  >
                    <input
                      type="checkbox"
                      checked={selections.cancer_subtypes?.includes(option as CancerSubtype) || false}
                      onChange={() => handleCancerSubtypeToggle(option as CancerSubtype)}
                      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm">{option}</span>
                  </label>
                ))}
              </div>
            )}

            {req.type === "comparison_focus" && req.options && (
              <div className="space-y-2">
                {req.options.map((option) => (
                  <label
                    key={option}
                    className="flex cursor-pointer items-center gap-2 rounded border border-gray-300 p-2 hover:bg-gray-50"
                  >
                    <input
                      type="radio"
                      name="comparison_focus"
                      value={option}
                      checked={selections.comparison_focus === option}
                      onChange={() => handleComparisonFocusChange(option as ComparisonFocus)}
                      className="h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm capitalize">{option}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <button
        onClick={onConfirm}
        disabled={!canConfirm()}
        className="mt-4 w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400"
      >
        Confirm Selection
      </button>
    </div>
  );
}
