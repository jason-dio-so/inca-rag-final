/**
 * Premium API Proxy Route - Simple Compare (STEP 32-κ)
 *
 * Source: docs/api/upstream/premium_simple_compare_spec.txt
 * Upstream: GET https://new-prod.greenlight.direct/public/prdata/prInfo
 *
 * Constitutional Principles:
 * - Server-side proxy (NO client-side API key exposure)
 * - basePremium = outPrList[].monthlyPrem (ONLY)
 * - Does NOT affect /compare contract
 */

import { NextRequest, NextResponse } from 'next/server';
import type { SimplePremiumRequest, UpstreamPremiumResponse } from '@/lib/api/premium/types';
import { adaptPremiumResponse } from '@/lib/api/premium/adapter';

// STEP 33-β-1b: Module load guarantee
console.log('🚨 [premium:simple-compare] module loaded');

/**
 * POST /api/premium/simple-compare
 *
 * Proxies request to upstream Premium API (간편비교)
 * NOTE: Our route accepts POST, but upstream uses GET with query params
 */
export async function POST(request: NextRequest) {
  // STEP 33-β-1b: Handler entry guarantee
  console.log('🚨 [premium:simple-compare] handler entered');

  try {
    // Parse request body
    const body: SimplePremiumRequest = await request.json();

    // STEP 33-β-1b: Log parsed body
    console.log('[Premium Simple] body:', body);

    // Get upstream API config from env
    const upstreamUrl = process.env.PREMIUM_API_BASE_URL || 'https://new-prod.greenlight.direct';

    // Build query string from request body
    const params = new URLSearchParams({
      baseDt: body.baseDt,
      birthday: body.birthday,
      customerNm: body.customerNm,
      sex: body.sex,
      age: body.age,
    });

    const upstreamFullUrl = `${upstreamUrl}/public/prdata/prInfo?${params.toString()}`;

    // STEP 33-β-1b: Log params and URL
    console.log('[Premium Simple] params:', params.toString());
    console.log('[Premium Simple] upstreamFullUrl:', upstreamFullUrl);

    // Call upstream Premium API (GET with query params)
    const upstreamResponse = await fetch(upstreamFullUrl, {
      method: 'GET',
      signal: AbortSignal.timeout(10000), // 10s timeout
    });

    if (!upstreamResponse.ok) {
      // STEP 33-β-1b: Capture upstream error body (full text)
      const errorBody = await upstreamResponse.text();
      console.error('[Premium Simple] upstream error body:', errorBody);
      console.error('[Premium Simple] Upstream Error:', {
        status: upstreamResponse.status,
        statusText: upstreamResponse.statusText,
      });

      const clipped = errorBody.slice(0, 500);

      return NextResponse.json(
        {
          ok: false,
          reason: 'UPSTREAM_ERROR',
          message: `Upstream returned ${upstreamResponse.status}: ${clipped}`,
          items: [],
        },
        { status: upstreamResponse.status }
      );
    }

    const upstreamData: UpstreamPremiumResponse = await upstreamResponse.json();

    // Adapt upstream response to PremiumProxyResponse
    const adapted = adaptPremiumResponse(upstreamData);

    return NextResponse.json(adapted);
  } catch (error) {
    if (error instanceof Error && error.name === 'TimeoutError') {
      return NextResponse.json(
        {
          ok: false,
          reason: 'TIMEOUT',
          message: 'Upstream API timeout',
          items: [],
        },
        { status: 504 }
      );
    }

    return NextResponse.json(
      {
        ok: false,
        reason: 'UPSTREAM_ERROR',
        message: error instanceof Error ? error.message : 'Unknown error',
        items: [],
      },
      { status: 500 }
    );
  }
}
