/**
 * Test page for CompareViewModelRenderer
 * Load example ViewModel JSON and render with 3-Block layout
 */

import React, { useState, useEffect } from "react";
import { CompareViewModelRenderer } from "@/components/compare/CompareViewModelRenderer";
import type { CompareViewModel } from "@/lib/compare/viewModelTypes";

interface ExampleData {
  name: string;
  description: string;
  view_model: CompareViewModel;
}

export default function CompareTestPage() {
  const [examples, setExamples] = useState<ExampleData[]>([]);
  const [selectedExample, setSelectedExample] = useState<number>(0);
  const [apiViewModel, setApiViewModel] = useState<CompareViewModel | null>(
    null
  );
  const [apiLoading, setApiLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/compare_view_model.examples.json")
      .then((res) => res.json())
      .then((data) => setExamples(data.examples))
      .catch((err) => setLoadError(err.message));
  }, []);

  if (loadError) {
    return <div className="p-4 text-red-600">Error loading examples: {loadError}</div>;
  }

  if (examples.length === 0) {
    return <div className="p-4">Loading examples...</div>;
  }

  const currentViewModel = apiViewModel || examples[selectedExample].view_model;

  const handleApiTest = async () => {
    setApiLoading(true);
    setApiError(null);
    try {
      const response = await fetch("http://localhost:8001/compare/view-model", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: "암 진단비 기준으로 삼성화재와 메리츠화재를 비교해줘",
          insurers: ["SAMSUNG", "MERITZ"],
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setApiViewModel(data);
    } catch (error) {
      setApiError(error instanceof Error ? error.message : "Network error");
    } finally {
      setApiLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            ViewModel Renderer Test
          </h1>
          <div className="mt-4 flex items-center gap-4">
            <select
              value={selectedExample}
              onChange={(e) => {
                setSelectedExample(Number(e.target.value));
                setApiViewModel(null);
              }}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              {examples.map((example, idx) => (
                <option key={idx} value={idx}>
                  {example.name}
                </option>
              ))}
            </select>

            <button
              onClick={handleApiTest}
              disabled={apiLoading}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
            >
              {apiLoading ? "Loading..." : "Test Live API"}
            </button>

            {apiViewModel && (
              <button
                onClick={() => setApiViewModel(null)}
                className="text-sm text-blue-600 hover:underline"
              >
                Reset to Example
              </button>
            )}
          </div>

          {apiError && (
            <div className="mt-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {apiError}
            </div>
          )}
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8">
        <CompareViewModelRenderer viewModel={currentViewModel} />
      </div>
    </div>
  );
}
