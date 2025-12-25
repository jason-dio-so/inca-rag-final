/**
 * Premium API Proxy Route - Onepage Compare (STEP 32-κ)
 *
 * Source: docs/api/upstream/premium_onepage_compare_spec.txt
 * Upstream: GET https://new-prod.greenlight.direct/public/prdata/prDetail
 *
 * Constitutional Principles:
 * - Server-side proxy (NO client-side API key exposure)
 * - basePremium = monthlyPremSum (ONLY)
 * - Does NOT affect /compare contract
 */

import { NextRequest, NextResponse } from 'next/server';
import type { OnepagePremiumRequest, UpstreamPremiumResponse } from '@/lib/api/premium/types';
import { adaptPremiumResponse } from '@/lib/api/premium/adapter';

// STEP 33-β-1b: Module load guarantee
console.log('🚨 [premium:onepage-compare] module loaded');

/**
 * POST /api/premium/onepage-compare
 *
 * Proxies request to upstream Premium API (한장비교)
 * NOTE: Our route accepts POST, but upstream uses GET with query params
 */
export async function POST(request: NextRequest) {
  // STEP 33-β-1b: Handler entry guarantee
  console.log('🚨 [premium:onepage-compare] handler entered');

  try {
    // Parse request body
    const body: OnepagePremiumRequest = await request.json();

    // STEP 33-β-1b: Log parsed body
    console.log('[Premium Onepage] body:', body);

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

    const upstreamFullUrl = `${upstreamUrl}/public/prdata/prDetail?${params.toString()}`;

    // STEP 33-β-1b: Log params and URL
    console.log('[Premium Onepage] params:', params.toString());
    console.log('[Premium Onepage] upstreamFullUrl:', upstreamFullUrl);

    // Call upstream Premium API (GET with query params)
    const upstreamResponse = await fetch(upstreamFullUrl, {
      method: 'GET',
      signal: AbortSignal.timeout(10000), // 10s timeout
    });

    // STEP 33-β-1e: Log upstream response meta (success or failure)
    const responseMeta = {
      status: upstreamResponse.status,
      statusText: upstreamResponse.statusText,
      url: upstreamResponse.url,
      contentType: upstreamResponse.headers.get('content-type'),
      contentLength: upstreamResponse.headers.get('content-length'),
      server: upstreamResponse.headers.get('server'),
      date: upstreamResponse.headers.get('date'),
    };

    if (!upstreamResponse.ok) {
      const errorBody = await upstreamResponse.text();

      console.error('[Premium Onepage] Upstream Error Meta:', {
        ...responseMeta,
        bodyLen: errorBody.length,
      });
      console.error('[Premium Onepage] Upstream Error Body (first 800):', errorBody.slice(0, 800));

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

    // Success case: log meta
    console.log('[Premium Onepage] Upstream OK Meta:', responseMeta);

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
