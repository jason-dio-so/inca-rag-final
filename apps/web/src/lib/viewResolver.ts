/**
 * Contract-driven View Resolver (STEP 28)
 *
 * Maps Backend Contract states to UI View components.
 *
 * Constitutional Rules:
 * - Uses SSOT: apps/web/src/contracts/uiStateMap.ts
 * - State key format: {comparison_result}:{next_action}:{ux_message_code}
 * - Unknown states → FALLBACK_STATE (never throw)
 * - View names are contract (immutable)
 *
 * Flow:
 * 1. API Response → extractStateKey()
 * 2. State Key → resolveUIState() → UIStateConfig
 * 3. UIStateConfig.view → Render corresponding View component
 */

import {
  resolveUIState,
  extractStateKey,
  UIStateConfig,
  ViewType,
} from '../contracts/uiStateMap';
import type { CompareResponse } from './api/compareClient';

/**
 * Resolve View from API Response
 *
 * @param response - Compare API response
 * @returns UI State Configuration
 *
 * @example
 * ```tsx
 * const config = resolveView(apiResponse);
 * // config.view = "CompareResult"
 * // config.primaryCta = "compare"
 * ```
 */
export function resolveView(response: CompareResponse): UIStateConfig {
  const stateKey = extractStateKey(response);
  const uiState = resolveUIState(
    response.comparison_result,
    response.next_action,
    response.ux_message_code
  );

  return uiState;
}

/**
 * Get View Component Name
 *
 * Helper to extract view type from UI state.
 *
 * @param response - Compare API response
 * @returns View type string
 */
export function getViewType(response: CompareResponse): ViewType {
  const config = resolveView(response);
  return config.view;
}

/**
 * Check if state is comparable
 *
 * @param response - Compare API response
 * @returns True if state allows comparison
 */
export function isComparable(response: CompareResponse): boolean {
  return response.comparison_result === 'comparable';
}

/**
 * Check if state requires user input
 *
 * @param response - Compare API response
 * @returns True if additional input required
 */
export function requiresInput(response: CompareResponse): boolean {
  const config = resolveView(response);
  return config.requiresInput;
}

/**
 * Get severity level for UI styling
 *
 * @param response - Compare API response
 * @returns Severity level (success, info, warning, error)
 */
export function getSeverity(response: CompareResponse): string {
  const config = resolveView(response);
  return config.severity;
}
