#!/usr/bin/env python3
"""Test STEP 3.12 immutability - verify STEP 3.11 results never change"""

import sys
sys.path.insert(0, 'scripts')
from step311_comparison_engine import ProposalFactComparisonEngine
from step312_explanation_layer import PRIMEExplanationLayer

# Test that STEP 3.11 result is immutable
comparison_engine = ProposalFactComparisonEngine()
explanation_layer = PRIMEExplanationLayer()

# Get STEP 3.11 result
result_311 = comparison_engine.compare(
    insurers=['KB', 'LOTTE'],
    coverage_query='뇌졸중진단비'
)

# Store original states
original_states = dict(result_311.state_summary)

# Add explanation layer
result_312 = explanation_layer.explain(result_311, '뇌졸중진단비')

# Verify states unchanged
print('=' * 80)
print('IMMUTABILITY CHECK')
print('=' * 80)
print('\nOriginal STEP 3.11 states:')
for insurer, state in original_states.items():
    print(f'  {insurer}: {state.value}')

print('\nAfter STEP 3.12 (from comparison_result):')
for insurer, state in result_312.comparison_result.state_summary.items():
    print(f'  {insurer}: {state.value}')

print('\nState changes:')
changes = 0
for insurer in original_states:
    if original_states[insurer] != result_312.comparison_result.state_summary[insurer]:
        print(f'  ❌ {insurer}: {original_states[insurer].value} → {result_312.comparison_result.state_summary[insurer].value}')
        changes += 1

if changes == 0:
    print('  ✅ NO CHANGES - IMMUTABILITY VERIFIED')
else:
    print(f'  ❌ FAILED - {changes} states changed')

print('\n' + '=' * 80)
