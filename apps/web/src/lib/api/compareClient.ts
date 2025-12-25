/**
 * Compare API Client (STEP 28)
 *
 * Supports:
 * - Real API calls to Backend (POST /compare)
 * - DEV_MOCK_MODE: Load golden snapshots directly
 * - Error handling: Network errors vs Contract states
 *
 * Constitutional Rules:
 * - All 200 responses are valid contract states (never throw)
 * - Network/500 errors are system errors (toast/retry UX)
 * - Mock mode uses golden snapshots as SSOT
 */

export interface CompareRequest {
  query: string;
  insurer_a?: string;
  insurer_b?: string;
  include_policy_evidence?: boolean;
}

export interface CompareResponse {
  query: string;
  comparison_result: string;
  next_action: string;
  ux_message_code: string;
  coverage_a: CoverageItem | null;
  coverage_b: CoverageItem | null;
  policy_evidence_a: PolicyEvidence | null;
  policy_evidence_b: PolicyEvidence | null;
  message: string;
  debug?: {
    canonical_code_resolved: string | null;
    raw_name_used: string | null;
    universe_lock_enforced: boolean;
  };
}

export interface CoverageItem {
  insurer: string;
  proposal_id: string;
  coverage_name_raw: string;
  canonical_coverage_code: string | null;
  mapping_status: string;
  amount_value: number | null;
  disease_scope_raw: string | null;
  disease_scope_norm: {
    include_group_id: string | null;
    exclude_group_id: string | null;
  } | null;
  source_confidence: string | null;
}

export interface PolicyEvidence {
  group_name: string;
  insurer: string;
  member_count: number;
}

export type ScenarioId = 'A' | 'B' | 'C' | 'D' | 'E' | 'UNKNOWN';

/**
 * Golden Snapshot Mock Data (DEV_MOCK_MODE)
 */
const GOLDEN_SNAPSHOTS: Record<ScenarioId, CompareResponse> = {
  // Loaded from tests/snapshots/compare/*.golden.json at build time
  // For now, we'll inline minimal versions (production would load files)
  A: {
    query: '일반암진단비',
    comparison_result: 'comparable',
    next_action: 'COMPARE',
    ux_message_code: 'COVERAGE_MATCH_COMPARABLE',
    coverage_a: {
      insurer: 'SAMSUNG',
      proposal_id: 'PROP_SAMSUNG_001',
      coverage_name_raw: '일반암진단금',
      canonical_coverage_code: 'CA_DIAG_GENERAL',
      mapping_status: 'MAPPED',
      amount_value: 50000000,
      disease_scope_raw: '일반암',
      disease_scope_norm: null,
      source_confidence: 'proposal_confirmed',
    },
    coverage_b: {
      insurer: 'MERITZ',
      proposal_id: 'PROP_MERITZ_001',
      coverage_name_raw: '암진단금(일반암)',
      canonical_coverage_code: 'CA_DIAG_GENERAL',
      mapping_status: 'MAPPED',
      amount_value: 30000000,
      disease_scope_raw: '일반암',
      disease_scope_norm: null,
      source_confidence: 'proposal_confirmed',
    },
    policy_evidence_a: null,
    policy_evidence_b: null,
    message: 'Both insurers have CA_DIAG_GENERAL',
  },
  B: {
    query: '매핑안된담보',
    comparison_result: 'unmapped',
    next_action: 'REQUEST_MORE_INFO',
    ux_message_code: 'COVERAGE_UNMAPPED',
    coverage_a: {
      insurer: 'KB',
      proposal_id: 'PROP_KB_001',
      coverage_name_raw: '매핑안된담보',
      canonical_coverage_code: null,
      mapping_status: 'UNMAPPED',
      amount_value: 1000000,
      disease_scope_raw: null,
      disease_scope_norm: null,
      source_confidence: null,
    },
    coverage_b: null,
    policy_evidence_a: null,
    policy_evidence_b: null,
    message: '매핑안된담보 is not mapped to canonical coverage code',
  },
  C: {
    query: '유사암진단금',
    comparison_result: 'policy_required',
    next_action: 'VERIFY_POLICY',
    ux_message_code: 'DISEASE_SCOPE_VERIFICATION_REQUIRED',
    coverage_a: {
      insurer: 'SAMSUNG',
      proposal_id: 'PROP_SAMSUNG_001',
      coverage_name_raw: '유사암진단금',
      canonical_coverage_code: 'CA_DIAG_SIMILAR',
      mapping_status: 'MAPPED',
      amount_value: 5000000,
      disease_scope_raw: '유사암 (갑상선암, 제자리암, 경계성종양)',
      disease_scope_norm: {
        include_group_id: null,
        exclude_group_id: null,
      },
      source_confidence: 'policy_required',
    },
    coverage_b: null,
    policy_evidence_a: {
      group_name: '삼성 유사암 (Seed)',
      insurer: 'SAMSUNG',
      member_count: 6,
    },
    policy_evidence_b: null,
    message: 'Disease scope verification required for 유사암진단금',
  },
  D: {
    query: '일반암진단비',
    comparison_result: 'comparable',
    next_action: 'COMPARE',
    ux_message_code: 'COVERAGE_MATCH_COMPARABLE',
    coverage_a: {
      insurer: 'KB',
      proposal_id: 'PROP_KB_001',
      coverage_name_raw: '일반암 진단비',
      canonical_coverage_code: 'CA_DIAG_GENERAL',
      mapping_status: 'MAPPED',
      amount_value: 40000000,
      disease_scope_raw: '일반암',
      disease_scope_norm: null,
      source_confidence: 'proposal_confirmed',
    },
    coverage_b: {
      insurer: 'MERITZ',
      proposal_id: 'PROP_MERITZ_001',
      coverage_name_raw: '암진단금(일반암)',
      canonical_coverage_code: 'CA_DIAG_GENERAL',
      mapping_status: 'MAPPED',
      amount_value: 30000000,
      disease_scope_raw: '일반암',
      disease_scope_norm: null,
      source_confidence: 'proposal_confirmed',
    },
    policy_evidence_a: null,
    policy_evidence_b: null,
    message: 'Both insurers have CA_DIAG_GENERAL',
  },
  E: {
    query: '다빈치 수술비',
    comparison_result: 'out_of_universe',
    next_action: 'REQUEST_MORE_INFO',
    ux_message_code: 'COVERAGE_NOT_IN_UNIVERSE',
    coverage_a: null,
    coverage_b: null,
    policy_evidence_a: null,
    policy_evidence_b: null,
    message: "'다빈치 수술비' coverage not found in SAMSUNG proposal universe",
  },
  UNKNOWN: {
    query: 'test',
    comparison_result: 'unknown_result',
    next_action: 'UNKNOWN_ACTION',
    ux_message_code: 'UNKNOWN_CODE',
    coverage_a: null,
    coverage_b: null,
    policy_evidence_a: null,
    policy_evidence_b: null,
    message: 'Test unknown state',
  },
};

/**
 * Compare API Client
 */
export class CompareClient {
  private baseUrl: string;
  private isMockMode: boolean;

  constructor() {
    this.baseUrl = process.env.API_BASE_URL || 'http://localhost:8000';
    this.isMockMode = process.env.DEV_MOCK_MODE === '1';
  }

  /**
   * Call Compare API
   *
   * @param request - Compare request
   * @returns Compare response (always returns, never throws for valid contract states)
   */
  async compare(request: CompareRequest): Promise<CompareResponse> {
    if (this.isMockMode) {
      return this.mockCompare(request);
    }

    try {
      const response = await fetch(`${this.baseUrl}/compare`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        // Network/server error (500, 404, etc.)
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const data: CompareResponse = await response.json();

      // All 200 responses are valid contract states
      return data;
    } catch (error) {
      // Re-throw network/server errors (handled by UI as SystemError toast)
      throw error;
    }
  }

  /**
   * Mock Compare (DEV_MOCK_MODE)
   *
   * Returns golden snapshot data based on query heuristics.
   */
  private async mockCompare(request: CompareRequest): Promise<CompareResponse> {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 300));

    // Simple heuristics to match query to scenario
    const query = request.query.toLowerCase();

    if (query.includes('일반암')) {
      return GOLDEN_SNAPSHOTS.A;
    } else if (query.includes('매핑')) {
      return GOLDEN_SNAPSHOTS.B;
    } else if (query.includes('유사암')) {
      return GOLDEN_SNAPSHOTS.C;
    } else if (query.includes('다빈치')) {
      return GOLDEN_SNAPSHOTS.E;
    }

    // Default to scenario A
    return GOLDEN_SNAPSHOTS.A;
  }

  /**
   * Load Golden Snapshot by ID (DEV_MOCK_MODE only)
   *
   * Used by ScenarioSwitcher component.
   */
  async loadScenario(scenarioId: ScenarioId): Promise<CompareResponse> {
    if (!this.isMockMode) {
      throw new Error('loadScenario only available in DEV_MOCK_MODE');
    }

    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 200));

    return GOLDEN_SNAPSHOTS[scenarioId];
  }

  /**
   * Get available scenarios (DEV_MOCK_MODE only)
   */
  getAvailableScenarios(): ScenarioId[] {
    return Object.keys(GOLDEN_SNAPSHOTS) as ScenarioId[];
  }
}

// Export singleton instance
export const compareClient = new CompareClient();
