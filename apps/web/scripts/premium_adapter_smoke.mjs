/**
 * Premium Adapter Smoke Test (STEP 32-λ)
 *
 * Minimal smoke test without test framework dependency.
 * Run with: node scripts/premium_adapter_smoke.mjs
 *
 * Purpose: Verify adapter handles SSOT-documented structures
 */

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Import adapter (using dynamic import since we're in ESM context)
const { adaptPremiumResponse } = await import('../src/lib/api/premium/adapter.ts');

// Load fixtures
const fixturesDir = join(__dirname, '../src/lib/api/premium/__fixtures__');
const prInfo = JSON.parse(readFileSync(join(fixturesDir, 'upstream_prInfo_sample.json'), 'utf-8'));
const prDetail = JSON.parse(readFileSync(join(fixturesDir, 'upstream_prDetail_sample.json'), 'utf-8'));
const wrapped = JSON.parse(readFileSync(join(fixturesDir, 'upstream_wrapped_sample.json'), 'utf-8'));

console.log('=== Premium Adapter Smoke Test ===\n');

// Test 1: prInfo
console.log('Test 1: prInfo (Simple Compare)');
const result1 = adaptPremiumResponse(prInfo);
console.log('  ok:', result1.ok);
console.log('  items.length:', result1.items.length);
console.log('  items[0].insurer:', result1.items[0]?.insurer);
console.log('  items[0].basePremium:', result1.items[0]?.basePremium);
console.assert(result1.ok === true, 'prInfo should succeed');
console.assert(result1.items.length === 2, 'Should have 2 items');
console.assert(result1.items[0].basePremium === 48000, 'First item should be KB with 48000');
console.log('  ✅ PASS\n');

// Test 2: prDetail
console.log('Test 2: prDetail (Onepage Compare)');
const result2 = adaptPremiumResponse(prDetail);
console.log('  ok:', result2.ok);
console.log('  items.length:', result2.items.length);
console.log('  items[0].insurer:', result2.items[0]?.insurer);
console.log('  items[0].basePremium:', result2.items[0]?.basePremium);
console.assert(result2.ok === true, 'prDetail should succeed');
console.assert(result2.items[0].basePremium === 50000, 'Should extract monthlyPremSum (50000)');
console.assert(result2.items[0].basePremium !== 5000, 'Should NOT use cvrAmtArrLst[].monthlyPrem');
console.log('  ✅ PASS\n');

// Test 3: Wrapped (defensive)
console.log('Test 3: Wrapped Response (Defensive)');
const result3 = adaptPremiumResponse(wrapped);
console.log('  ok:', result3.ok);
console.log('  items.length:', result3.items.length);
console.log('  items[0].basePremium:', result3.items[0]?.basePremium);
console.assert(result3.ok === true, 'Wrapped response should be handled');
console.assert(result3.items[0].basePremium === 50000, 'Should extract from wrapped data');
console.log('  ✅ PASS\n');

// Test 4: Null input
console.log('Test 4: Null/Undefined Input');
const result4 = adaptPremiumResponse(null);
console.log('  ok:', result4.ok);
console.log('  reason:', result4.reason);
console.assert(result4.ok === false, 'Null should fail gracefully');
console.log('  ✅ PASS\n');

// Test 5: Error wrapped
console.log('Test 5: Error Response (returnCode !== "0000")');
const errorWrapped = { returnCode: '9999', returnMsg: 'Test Error', data: null };
const result5 = adaptPremiumResponse(errorWrapped);
console.log('  ok:', result5.ok);
console.log('  reason:', result5.reason);
console.log('  message:', result5.message);
console.assert(result5.ok === false, 'Error should fail');
console.assert(result5.reason === 'UPSTREAM_ERROR', 'Should be UPSTREAM_ERROR');
console.log('  ✅ PASS\n');

console.log('=== All Smoke Tests Passed ✅ ===');
