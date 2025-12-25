/**
 * UI State Map - SSOT for Frontend UI Behavior (STEP 27)
 *
 * Constitutional Rules:
 * - State keys are immutable (tied to Backend Contract STEP 24/26)
 * - View names, CTA IDs are contract (cannot change without approval)
 * - Text content (title, message) is NOT contract (i18n free)
 * - Unknown states must use fallback (no runtime errors)
 *
 * State Key Format: "{comparison_result}:{next_action}:{ux_message_code}"
 *
 * Backend Contract Sources:
 * - comparison_result: apps/api/app/contracts/compare_codes.py (STEP 24)
 * - next_action: apps/api/app/contracts/compare_codes.py (STEP 24)
 * - ux_message_code: apps/api/app/contracts/ux_message_codes.py (STEP 26)
 *
 * Version: 1.0.0
 * Date: 2025-12-25
 */

/**
 * UI State Configuration
 */
export interface UIStateConfig {
  /** View component to render (contract) */
  view: ViewType;

  /** Primary CTA identifier (contract) */
  primaryCta: CtaId;

  /** Secondary CTA identifier (contract, optional) */
  secondaryCta?: CtaId;

  /** UI severity/state indicator (contract) */
  severity: SeverityLevel;

  /** Title text (non-contract, i18n key) */
  title: string;

  /** Description text (non-contract, i18n key) */
  description: string;

  /** Whether additional user input is required (contract) */
  requiresInput: boolean;

  /** Data display configuration (contract) */
  displayConfig: DisplayConfig;
}

/**
 * View Types (Contract)
 */
export type ViewType =
  | "CompareResult"          // Successful comparison view
  | "GenericMessage"          // Generic message/status view
  | "PolicyVerificationView"  // Policy verification required view
  | "UnknownState";          // Fallback for unknown states

/**
 * CTA Identifiers (Contract)
 */
export type CtaId =
  | "compare"               // Navigate to detailed comparison
  | "search_again"          // Return to search input
  | "view_policy"           // Show policy evidence
  | "continue_comparison"   // Proceed with warnings
  | "select_insurer"        // Return to insurer selection
  | "contact_support"       // Open support contact
  | "notify_ready"          // Request notification when ready
  | "retry";                // Retry last action

/**
 * Severity Levels (Contract)
 */
export type SeverityLevel =
  | "success"   // Green - comparison available
  | "info"      // Blue - informational state
  | "warning"   // Yellow - requires attention
  | "error";    // Red - action blocked

/**
 * Display Configuration (Contract)
 */
export interface DisplayConfig {
  /** Show coverage A details */
  showCoverageA: boolean;

  /** Show coverage B details */
  showCoverageB: boolean;

  /** Show amount comparison */
  showAmountComparison: boolean;

  /** Show policy evidence */
  showPolicyEvidence: boolean;

  /** Show mapping status badge */
  showMappingStatus: boolean;

  /** Show universe lock badge */
  showUniverseLock: boolean;
}

/**
 * UI State Map - SSOT (Contract)
 *
 * Coverage: Golden Snapshot Scenarios A, B, C, E
 */
export const UI_STATE_MAP: Record<string, UIStateConfig> = {
  /**
   * State: comparable:COMPARE:COVERAGE_MATCH_COMPARABLE
   * Scenarios: A, D
   */
  "comparable:COMPARE:COVERAGE_MATCH_COMPARABLE": {
    view: "CompareResult",
    primaryCta: "compare",
    secondaryCta: "search_again",
    severity: "success",
    title: "비교 가능",
    description: "두 보험사 모두 동일한 담보를 보유하고 있습니다",
    requiresInput: false,
    displayConfig: {
      showCoverageA: true,
      showCoverageB: true,
      showAmountComparison: true,
      showPolicyEvidence: false,
      showMappingStatus: true,
      showUniverseLock: false,
    },
  },

  /**
   * State: unmapped:REQUEST_MORE_INFO:COVERAGE_UNMAPPED
   * Scenario: B
   */
  "unmapped:REQUEST_MORE_INFO:COVERAGE_UNMAPPED": {
    view: "GenericMessage",
    primaryCta: "search_again",
    secondaryCta: "contact_support",
    severity: "warning",
    title: "담보 매핑 실패",
    description: "해당 담보는 아직 신정원 코드로 매핑되지 않았습니다",
    requiresInput: true,
    displayConfig: {
      showCoverageA: true,
      showCoverageB: false,
      showAmountComparison: false,
      showPolicyEvidence: false,
      showMappingStatus: true,
      showUniverseLock: false,
    },
  },

  /**
   * State: policy_required:VERIFY_POLICY:DISEASE_SCOPE_VERIFICATION_REQUIRED
   * Scenario: C
   */
  "policy_required:VERIFY_POLICY:DISEASE_SCOPE_VERIFICATION_REQUIRED": {
    view: "PolicyVerificationView",
    primaryCta: "view_policy",
    secondaryCta: "continue_comparison",
    severity: "info",
    title: "약관 확인 필요",
    description: "담보의 질병 범위를 확인하려면 약관 검증이 필요합니다",
    requiresInput: false,
    displayConfig: {
      showCoverageA: true,
      showCoverageB: false,
      showAmountComparison: true,
      showPolicyEvidence: true,
      showMappingStatus: true,
      showUniverseLock: false,
    },
  },

  /**
   * State: out_of_universe:REQUEST_MORE_INFO:COVERAGE_NOT_IN_UNIVERSE
   * Scenario: E
   */
  "out_of_universe:REQUEST_MORE_INFO:COVERAGE_NOT_IN_UNIVERSE": {
    view: "GenericMessage",
    primaryCta: "search_again",
    secondaryCta: "select_insurer",
    severity: "info",
    title: "담보 없음",
    description: "해당 담보는 선택한 보험사의 가입설계서에 존재하지 않습니다",
    requiresInput: true,
    displayConfig: {
      showCoverageA: false,
      showCoverageB: false,
      showAmountComparison: false,
      showPolicyEvidence: false,
      showMappingStatus: false,
      showUniverseLock: true,
    },
  },

  /**
   * Extended State: comparable_with_gaps:VERIFY_POLICY:COVERAGE_COMPARABLE_WITH_GAPS
   * Future use case: Partial data comparison
   */
  "comparable_with_gaps:VERIFY_POLICY:COVERAGE_COMPARABLE_WITH_GAPS": {
    view: "PolicyVerificationView",
    primaryCta: "view_policy",
    secondaryCta: "continue_comparison",
    severity: "warning",
    title: "부분 비교 가능",
    description: "비교가 가능하나 일부 정보 확인이 필요합니다",
    requiresInput: false,
    displayConfig: {
      showCoverageA: true,
      showCoverageB: true,
      showAmountComparison: true,
      showPolicyEvidence: true,
      showMappingStatus: true,
      showUniverseLock: false,
    },
  },

  /**
   * Extended State: non_comparable:REQUEST_MORE_INFO:COVERAGE_TYPE_MISMATCH
   * Future use case: Different canonical codes
   */
  "non_comparable:REQUEST_MORE_INFO:COVERAGE_TYPE_MISMATCH": {
    view: "GenericMessage",
    primaryCta: "search_again",
    severity: "info",
    title: "비교 불가",
    description: "서로 다른 담보 유형입니다",
    requiresInput: true,
    displayConfig: {
      showCoverageA: true,
      showCoverageB: true,
      showAmountComparison: false,
      showPolicyEvidence: false,
      showMappingStatus: true,
      showUniverseLock: false,
    },
  },

  /**
   * Extended State: comparable:COMPARE:COVERAGE_FOUND_SINGLE_INSURER
   * Future use case: Single insurer query
   */
  "comparable:COMPARE:COVERAGE_FOUND_SINGLE_INSURER": {
    view: "CompareResult",
    primaryCta: "select_insurer",
    secondaryCta: "search_again",
    severity: "info",
    title: "담보 확인",
    description: "선택한 보험사의 담보 정보입니다",
    requiresInput: false,
    displayConfig: {
      showCoverageA: true,
      showCoverageB: false,
      showAmountComparison: false,
      showPolicyEvidence: false,
      showMappingStatus: true,
      showUniverseLock: false,
    },
  },
};

/**
 * Fallback State (Contract)
 *
 * Used when Backend returns unknown state combination.
 * NOT an error - ensures graceful degradation.
 */
export const FALLBACK_STATE: UIStateConfig = {
  view: "UnknownState",
  primaryCta: "retry",
  secondaryCta: "contact_support",
  severity: "warning",
  title: "처리 중",
  description: "요청하신 담보 정보를 확인하고 있습니다",
  requiresInput: false,
  displayConfig: {
    showCoverageA: false,
    showCoverageB: false,
    showAmountComparison: false,
    showPolicyEvidence: false,
    showMappingStatus: false,
    showUniverseLock: false,
  },
};

/**
 * Resolve UI State from Backend Response
 *
 * @param comparisonResult - From Backend Contract (STEP 24)
 * @param nextAction - From Backend Contract (STEP 24)
 * @param uxMessageCode - From Backend Contract (STEP 26)
 * @returns UI State Configuration
 *
 * @example
 * ```typescript
 * const state = resolveUIState("comparable", "COMPARE", "COVERAGE_MATCH_COMPARABLE");
 * // Returns: UI_STATE_MAP["comparable:COMPARE:COVERAGE_MATCH_COMPARABLE"]
 * ```
 */
export function resolveUIState(
  comparisonResult: string,
  nextAction: string,
  uxMessageCode: string
): UIStateConfig {
  const stateKey = `${comparisonResult}:${nextAction}:${uxMessageCode}`;

  // Lookup in state map
  const state = UI_STATE_MAP[stateKey];

  // Return state or fallback (never throw error)
  if (state) {
    return state;
  }

  // Log unknown state for monitoring (contract drift detection)
  console.warn(
    `[UI Contract Drift] Unknown state: ${stateKey}. Using fallback.`,
    {
      comparisonResult,
      nextAction,
      uxMessageCode,
      timestamp: new Date().toISOString(),
    }
  );

  return FALLBACK_STATE;
}

/**
 * Get All Registered State Keys (Contract)
 *
 * Used for validation and testing.
 *
 * @returns Array of state keys
 */
export function getRegisteredStateKeys(): string[] {
  return Object.keys(UI_STATE_MAP);
}

/**
 * Check if State is Registered (Contract)
 *
 * @param stateKey - State key to check
 * @returns True if state is registered
 */
export function isStateRegistered(stateKey: string): boolean {
  return stateKey in UI_STATE_MAP;
}

/**
 * Extract State Key from Backend Response (Helper)
 *
 * @param response - Backend API response
 * @returns State key string
 */
export function extractStateKey(response: {
  comparison_result: string;
  next_action: string;
  ux_message_code: string;
}): string {
  return `${response.comparison_result}:${response.next_action}:${response.ux_message_code}`;
}
