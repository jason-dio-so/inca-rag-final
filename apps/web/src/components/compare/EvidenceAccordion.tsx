/**
 * BLOCK 3: EvidenceAccordion
 * Collapsible per-insurer evidence panels
 *
 * Constitution:
 * - Display excerpt as-is (no summarization, no rewriting)
 * - Group by insurer
 * - Show doc_type, doc_title, page, excerpt
 * - Neutral message if no evidence
 */

import React, { useState } from "react";
import type { EvidencePanel, InsurerCode } from "@/lib/compare/viewModelTypes";

interface EvidenceAccordionProps {
  evidencePanels: EvidencePanel[];
}

export function EvidenceAccordion({ evidencePanels }: EvidenceAccordionProps) {
  const [openInsurers, setOpenInsurers] = useState<Set<InsurerCode>>(
    new Set()
  );

  // Group evidence by insurer
  const groupedEvidence = evidencePanels.reduce((acc, panel) => {
    if (!acc[panel.insurer]) {
      acc[panel.insurer] = [];
    }
    acc[panel.insurer].push(panel);
    return acc;
  }, {} as Record<InsurerCode, EvidencePanel[]>);

  const toggleInsurer = (insurer: InsurerCode) => {
    const newOpenInsurers = new Set(openInsurers);
    if (newOpenInsurers.has(insurer)) {
      newOpenInsurers.delete(insurer);
    } else {
      newOpenInsurers.add(insurer);
    }
    setOpenInsurers(newOpenInsurers);
  };

  if (evidencePanels.length === 0) {
    return (
      <div className="rounded-lg border bg-gray-50 p-6 text-center text-sm text-gray-500">
        근거 문서 정보 없음
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h2 className="mb-4 text-base font-semibold text-gray-700">
        근거 문서 (Evidence)
      </h2>
      {Object.entries(groupedEvidence).map(([insurer, panels]) => (
        <div key={insurer} className="rounded-lg border bg-white shadow-sm">
          <button
            onClick={() => toggleInsurer(insurer as InsurerCode)}
            className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-gray-50"
          >
            <span className="font-medium text-gray-900">
              {insurer} ({panels.length}건)
            </span>
            <svg
              className={`h-5 w-5 transform transition-transform ${
                openInsurers.has(insurer as InsurerCode) ? "rotate-180" : ""
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>

          {openInsurers.has(insurer as InsurerCode) && (
            <div className="border-t px-4 py-3">
              <div className="space-y-4">
                {panels.map((panel) => (
                  <div
                    key={panel.id}
                    className="rounded-md border bg-gray-50 p-3"
                  >
                    <div className="mb-2 flex items-start justify-between">
                      <div>
                        <span className="inline-block rounded bg-blue-100 px-2 py-1 text-xs font-medium text-blue-800">
                          {panel.doc_type}
                        </span>
                        {panel.doc_title && (
                          <span className="ml-2 text-sm text-gray-600">
                            {panel.doc_title}
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {typeof panel.page === "number"
                          ? `p.${panel.page}`
                          : panel.page}
                      </span>
                    </div>
                    <div className="text-sm leading-relaxed text-gray-700">
                      {panel.excerpt}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
