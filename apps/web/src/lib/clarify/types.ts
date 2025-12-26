/**
 * Types for Clarify Panel (STEP NEXT-6)
 *
 * Constitutional Principles:
 * - No recommendation/inference
 * - Presentation only (selection UI)
 * - User-driven choices only
 */

export type SurgeryMethod = "da_vinci" | "robot" | "laparoscopic" | "any";

export type CancerSubtype = "제자리암" | "경계성종양" | "유사암" | "일반암";

export type ComparisonFocus = "amount" | "definition" | "condition";

export interface CompileOptions {
  surgery_method?: SurgeryMethod;
  cancer_subtypes?: CancerSubtype[];
  comparison_focus?: ComparisonFocus;
}

export interface CompileInput {
  user_query: string;
  selected_insurers: string[];
  selected_comparison_basis?: string;
  options?: CompileOptions;
}

export interface CompilerDebug {
  rule_version: string;
  resolved_coverage_codes?: string[];
  selected_slots: Record<string, any>;
  decision_trace: string[];
  warnings: string[];
}

export interface CompileOutput {
  compiled_request: Record<string, any>;
  compiler_debug: CompilerDebug;
}

export interface ClarificationRequirement {
  type: string;
  reason: string;
  options?: string[];
  detected?: string[];
  min_required?: number;
}

export interface ClarificationNeeded {
  clarification_needed: boolean;
  required_selections: ClarificationRequirement[];
}

export interface UserSelections {
  insurers: string[];
  comparison_basis?: string;
  surgery_method?: SurgeryMethod;
  cancer_subtypes?: CancerSubtype[];
  comparison_focus?: ComparisonFocus;
}
