/**
 * DebugPanel - Compiler debug info display (hidden by default)
 *
 * Constitutional Principles:
 * - Fact-only (no recommendation/judgment)
 * - Presentation only
 * - Show compiler trace + compiled request
 * - Hidden by default (toggle-able)
 */

import React, { useState } from "react";
import type { CompilerDebug } from "@/lib/clarify/types";

interface DebugPanelProps {
  compilerDebug?: CompilerDebug;
  compiledRequest?: Record<string, any>;
}

export function DebugPanel({ compilerDebug, compiledRequest }: DebugPanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!compilerDebug && !compiledRequest) {
    return null;
  }

  return (
    <div className="mt-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        <span>{isOpen ? "▼" : "▶"}</span>
        <span>Debug Info</span>
        {compilerDebug?.warnings && compilerDebug.warnings.length > 0 && (
          <span className="rounded bg-yellow-100 px-2 py-0.5 text-xs text-yellow-800">
            {compilerDebug.warnings.length} warning{compilerDebug.warnings.length > 1 ? "s" : ""}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="mt-2 space-y-4 rounded-lg border border-gray-300 bg-gray-50 p-4">
          {compilerDebug && (
            <div>
              <h4 className="mb-2 text-sm font-semibold text-gray-900">
                Compiler Debug
              </h4>

              <div className="space-y-3">
                <div>
                  <p className="text-xs font-medium text-gray-600">Rule Version:</p>
                  <p className="font-mono text-xs text-gray-800">
                    {compilerDebug.rule_version}
                  </p>
                </div>

                {compilerDebug.resolved_coverage_codes && (
                  <div>
                    <p className="text-xs font-medium text-gray-600">
                      Resolved Coverage Codes (신정원 통일코드):
                    </p>
                    <pre className="mt-1 rounded bg-white p-2 font-mono text-xs text-gray-800">
                      {JSON.stringify(compilerDebug.resolved_coverage_codes, null, 2)}
                    </pre>
                  </div>
                )}

                <div>
                  <p className="text-xs font-medium text-gray-600">Selected Slots:</p>
                  <pre className="mt-1 rounded bg-white p-2 font-mono text-xs text-gray-800">
                    {JSON.stringify(compilerDebug.selected_slots, null, 2)}
                  </pre>
                </div>

                <div>
                  <p className="text-xs font-medium text-gray-600">Decision Trace:</p>
                  <div className="mt-1 space-y-1">
                    {compilerDebug.decision_trace.map((trace, idx) => (
                      <div
                        key={idx}
                        className="rounded bg-white px-2 py-1 font-mono text-xs text-gray-700"
                      >
                        {trace}
                      </div>
                    ))}
                  </div>
                </div>

                {compilerDebug.warnings.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-yellow-700">Warnings:</p>
                    <div className="mt-1 space-y-1">
                      {compilerDebug.warnings.map((warning, idx) => (
                        <div
                          key={idx}
                          className="rounded bg-yellow-50 px-2 py-1 text-xs text-yellow-800"
                        >
                          {warning}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {compiledRequest && (
            <div>
              <h4 className="mb-2 text-sm font-semibold text-gray-900">
                Compiled Request
              </h4>
              <pre className="overflow-x-auto rounded bg-white p-3 font-mono text-xs text-gray-800">
                {JSON.stringify(compiledRequest, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
