/**
 * CompareViewModelRenderer - Main Entry Component
 * Renders ViewModel JSON with 3-Block ChatGPT-style layout
 *
 * Constitution:
 * 1. Fact-only: Display ViewModel data as-is, no modification
 * 2. No Recommendation: No interpretation/judgment/inference text
 * 3. Presentation Only: No sorting/filtering/scoring
 * 4. Debug Non-UI: Never render debug section
 *
 * BLOCK 0: ChatHeader (user query)
 * BLOCK 1: CoverageSnapshot (per-insurer summary)
 * BLOCK 2: FactTable (comparison table)
 * BLOCK 3: EvidenceAccordion (collapsible evidence)
 */

import React from "react";
import type { CompareViewModel } from "@/lib/compare/viewModelTypes";
import { ChatHeader } from "./ChatHeader";
import { CoverageSnapshot } from "./CoverageSnapshot";
import { FactTable } from "./FactTable";
import { EvidenceAccordion } from "./EvidenceAccordion";

interface CompareViewModelRendererProps {
  viewModel: CompareViewModel;
}

export function CompareViewModelRenderer({
  viewModel,
}: CompareViewModelRendererProps) {
  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      {/* BLOCK 0: ChatHeader */}
      <ChatHeader header={viewModel.header} />

      {/* BLOCK 1: CoverageSnapshot */}
      <CoverageSnapshot snapshot={viewModel.snapshot} />

      {/* BLOCK 2: FactTable */}
      <FactTable factTable={viewModel.fact_table} />

      {/* BLOCK 3: EvidenceAccordion */}
      <EvidenceAccordion evidencePanels={viewModel.evidence_panels} />

      {/* Debug section: NEVER render (Constitutional prohibition) */}
    </div>
  );
}
