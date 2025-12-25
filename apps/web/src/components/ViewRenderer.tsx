/**
 * View Renderer (STEP 28)
 *
 * Contract-driven component that renders appropriate View based on Backend Contract state.
 *
 * Flow:
 * 1. Receive CompareResponse
 * 2. Resolve UI state via viewResolver
 * 3. Render corresponding View component
 * 4. Unknown states → UnknownStateView (graceful degradation)
 */

import React from 'react';
import type { CompareResponse } from '@/lib/api/compareClient';
import { resolveView } from '@/lib/viewResolver';
import {
  ComparableView,
  UnmappedView,
  PolicyRequiredView,
  OutOfUniverseView,
  UnknownStateView,
} from './views';

interface ViewRendererProps {
  response: CompareResponse;
  onAction: (action: string, data?: any) => void;
}

export function ViewRenderer({ response, onAction }: ViewRendererProps) {
  const uiState = resolveView(response);

  // Resolve View component based on contract
  switch (uiState.view) {
    case 'CompareResult':
      return (
        <ComparableView
          response={response}
          onCompare={() => onAction('compare', response)}
          onSearchAgain={() => onAction('search_again')}
        />
      );

    case 'GenericMessage':
      // GenericMessage view is used for unmapped and out_of_universe
      if (response.comparison_result === 'unmapped') {
        return (
          <UnmappedView
            response={response}
            onSearchAgain={() => onAction('search_again')}
            onContactSupport={() => onAction('contact_support')}
          />
        );
      } else if (response.comparison_result === 'out_of_universe') {
        return (
          <OutOfUniverseView
            response={response}
            onSearchAgain={() => onAction('search_again')}
            onSelectInsurer={() => onAction('select_insurer')}
          />
        );
      }
      // Fallback for other GenericMessage states
      return (
        <UnknownStateView
          response={response}
          onRetry={() => onAction('retry')}
          onContactSupport={() => onAction('contact_support')}
        />
      );

    case 'PolicyVerificationView':
      return (
        <PolicyRequiredView
          response={response}
          onViewPolicy={() => onAction('view_policy', response.policy_evidence_a)}
          onContinueComparison={() => onAction('continue_comparison', response)}
        />
      );

    case 'UnknownState':
    default:
      return (
        <UnknownStateView
          response={response}
          onRetry={() => onAction('retry')}
          onContactSupport={() => onAction('contact_support')}
        />
      );
  }
}
