/**
 * Normalize user selections to CompileInput.
 *
 * Constitutional Principles:
 * - No inference/recommendation
 * - User selections only
 * - Deterministic transformation
 */

import type { UserSelections, CompileInput, CompileOptions } from "./types";

export function normalizeToCompileInput(
  query: string,
  selections: UserSelections
): CompileInput {
  const options: CompileOptions = {};

  if (selections.surgery_method) {
    options.surgery_method = selections.surgery_method;
  }

  if (selections.cancer_subtypes && selections.cancer_subtypes.length > 0) {
    options.cancer_subtypes = selections.cancer_subtypes;
  }

  if (selections.comparison_focus) {
    options.comparison_focus = selections.comparison_focus;
  }

  return {
    user_query: query,
    selected_insurers: selections.insurers,
    selected_comparison_basis: selections.comparison_basis,
    options: Object.keys(options).length > 0 ? options : undefined,
  };
}
