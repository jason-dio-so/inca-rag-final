/**
 * Example 1-4 UI Test Page
 * Purpose: Visual validation of ViewModel v2 rendering
 *
 * Usage: Visit http://localhost:3000/examples-test
 * Validates: All 4 INCA DIO examples render correctly
 *
 * Constitutional Compliance:
 * - All examples are fact-only
 * - NO recommendation/judgment/interpretation displayed
 */

import React, { useState } from "react";
import { CompareViewModelRenderer } from "@/components/compare/CompareViewModelRenderer";
import {
  example1PremiumSorting,
  example2ConditionDifference,
  example3SpecificInsurers,
  example4OXMatrix,
} from "@/fixtures/example-viewmodels";
import type { CompareViewModel } from "@/lib/compare/viewModelTypes";

const EXAMPLES: Record<string, CompareViewModel> = {
  "Example 1: Premium Sorting": example1PremiumSorting,
  "Example 2: Condition Difference": example2ConditionDifference,
  "Example 3: Specific Insurers": example3SpecificInsurers,
  "Example 4: O/X Matrix": example4OXMatrix,
};

export default function ExamplesTestPage() {
  const [selectedExample, setSelectedExample] = useState<string>(
    "Example 1: Premium Sorting"
  );

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4">
        <div className="mb-8">
          <h1 className="mb-2 text-3xl font-bold text-gray-900">
            ViewModel v2 Examples (INCA DIO)
          </h1>
          <p className="text-sm text-gray-600">
            Schema: next4.v2 | Examples: 1-4 from docs/customer/INCA_DIO_REQUIREMENTS.md
          </p>
        </div>

        {/* Example Selector */}
        <div className="mb-6 flex flex-wrap gap-2">
          {Object.keys(EXAMPLES).map((exampleName) => (
            <button
              key={exampleName}
              onClick={() => setSelectedExample(exampleName)}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                selectedExample === exampleName
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-700 hover:bg-gray-100"
              }`}
            >
              {exampleName}
            </button>
          ))}
        </div>

        {/* Schema Version Badge */}
        <div className="mb-4 rounded-md bg-blue-50 p-3">
          <div className="text-sm font-medium text-blue-900">
            Schema Version:{" "}
            {EXAMPLES[selectedExample].schema_version}
          </div>
          <div className="text-xs text-blue-700 mt-1">
            Generated: {EXAMPLES[selectedExample].generated_at}
          </div>
        </div>

        {/* ViewModel Renderer */}
        <div className="rounded-lg bg-white p-6 shadow-md">
          <CompareViewModelRenderer viewModel={EXAMPLES[selectedExample]} />
        </div>

        {/* Constitutional Compliance Notice */}
        <div className="mt-6 rounded-md bg-gray-100 p-4 text-xs text-gray-600">
          <div className="font-medium mb-2">Constitutional Compliance:</div>
          <ul className="list-inside list-disc space-y-1">
            <li>✅ Fact-only rendering (no AI-generated text)</li>
            <li>✅ No recommendation/judgment/interpretation</li>
            <li>✅ Evidence-based display (all values traceable)</li>
            <li>✅ v2 features: filter_criteria, table_type, highlight, sort_metadata</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
