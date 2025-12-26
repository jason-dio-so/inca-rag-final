/**
 * Test page for Clarify Panel + Debug Panel (STEP NEXT-6)
 *
 * Constitutional Principles:
 * - Fact-only (no recommendation/judgment)
 * - Presentation only
 * - User-driven selection flow
 */

import React, { useState } from "react";
import { ClarifyPanel } from "@/components/clarify/ClarifyPanel";
import { DebugPanel } from "@/components/debug/DebugPanel";
import { CompareViewModelRenderer } from "@/components/compare/CompareViewModelRenderer";
import { normalizeToCompileInput } from "@/lib/clarify/normalize";
import type {
  UserSelections,
  ClarificationNeeded,
  CompileOutput,
  CompilerDebug,
} from "@/lib/clarify/types";
import type { CompareViewModel } from "@/lib/compare/viewModelTypes";

const API_BASE = "http://localhost:8001";

export default function CompareClarifyTestPage() {
  const [query, setQuery] = useState("");
  const [clarificationNeeded, setClarificationNeeded] = useState<ClarificationNeeded | null>(null);
  const [userSelections, setUserSelections] = useState<UserSelections>({ insurers: [] });
  const [compileOutput, setCompileOutput] = useState<CompileOutput | null>(null);
  const [viewModel, setViewModel] = useState<CompareViewModel | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleQuerySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Step 1: Check if clarification is needed
      const clarifyResponse = await fetch(`${API_BASE}/compare/clarify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          insurers: userSelections.insurers.length > 0 ? userSelections.insurers : null,
        }),
      });

      if (!clarifyResponse.ok) {
        throw new Error(`Clarify API error: ${clarifyResponse.status}`);
      }

      const clarifyData: ClarificationNeeded = await clarifyResponse.json();
      setClarificationNeeded(clarifyData);

      // If no clarification needed, proceed directly
      if (!clarifyData.clarification_needed) {
        await executeCompileAndCompare();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmSelections = async () => {
    setError(null);
    setLoading(true);

    try {
      await executeCompileAndCompare();
      setClarificationNeeded(null); // Hide clarify panel after confirmation
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const executeCompileAndCompare = async () => {
    // Step 2: Compile selections to ProposalCompareRequest
    const compileInput = normalizeToCompileInput(query, userSelections);

    const compileResponse = await fetch(`${API_BASE}/compare/compile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(compileInput),
    });

    if (!compileResponse.ok) {
      throw new Error(`Compile API error: ${compileResponse.status}`);
    }

    const compileData: CompileOutput = await compileResponse.json();
    setCompileOutput(compileData);

    // Step 3: Call /compare/view-model with compiled request
    const viewModelResponse = await fetch(`${API_BASE}/compare/view-model`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(compileData.compiled_request),
    });

    if (!viewModelResponse.ok) {
      throw new Error(`ViewModel API error: ${viewModelResponse.status}`);
    }

    const viewModelData: CompareViewModel = await viewModelResponse.json();
    setViewModel(viewModelData);
  };

  const handleReset = () => {
    setQuery("");
    setClarificationNeeded(null);
    setUserSelections({ insurers: [] });
    setCompileOutput(null);
    setViewModel(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Clarify Panel + Debug Panel Test (STEP NEXT-6)
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Test deterministic compiler with question refinement UI
          </p>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="space-y-6">
          {/* Query Input */}
          <div className="rounded-lg bg-white p-4 shadow">
            <form onSubmit={handleQuerySubmit}>
              <label className="block text-sm font-medium text-gray-700">
                Query
              </label>
              <div className="mt-2 flex gap-2">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="예: 다빈치 수술비를 삼성과 현대 비교"
                  className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  disabled={loading || !query}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {loading ? "Loading..." : "Submit"}
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Reset
                </button>
              </div>
            </form>

            {error && (
              <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            )}
          </div>

          {/* Clarify Panel (shown when clarification needed) */}
          {clarificationNeeded?.clarification_needed && (
            <ClarifyPanel
              requirements={clarificationNeeded.required_selections}
              selections={userSelections}
              onSelectionsChange={setUserSelections}
              onConfirm={handleConfirmSelections}
            />
          )}

          {/* Debug Panel (hidden by default, toggle-able) */}
          {compileOutput && (
            <DebugPanel
              compilerDebug={compileOutput.compiler_debug}
              compiledRequest={compileOutput.compiled_request}
            />
          )}

          {/* ViewModel Renderer */}
          {viewModel && (
            <div className="rounded-lg bg-white p-4 shadow">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">
                Comparison Result
              </h2>
              <CompareViewModelRenderer viewModel={viewModel} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
