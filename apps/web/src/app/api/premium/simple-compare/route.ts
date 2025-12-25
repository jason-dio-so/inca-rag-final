/**
 * Premium API Proxy Route - Simple Compare (STEP 32)
 *
 * Constitutional Principles:
 * - Server-side proxy (NO client-side API key exposure)
 * - Calls upstream Premium API (간편비교_api.txt spec)
 * - Adapts response to PremiumProxyResponse
 * - Does NOT affect /compare contract
 */

import { NextRequest, NextResponse } from 'next/server';
import type { SimplePremiumRequest, UpstreamPremiumResponse } from '@/lib/api/premium/types';
import { adaptPremiumResponse } from '@/lib/api/premium/adapter';

/**
 * POST /api/premium/simple-compare
 *
 * Proxies request to upstream Premium API (간편비교)
 */
export async function POST(request: NextRequest) {
  try {
    // Parse request body
    const body: SimplePremiumRequest = await request.json();

    // Get upstream API config from env
    const upstreamUrl = process.env.PREMIUM_API_BASE_URL;
    const apiKey = process.env.PREMIUM_API_KEY;

    if (!upstreamUrl) {
      return NextResponse.json(
        {
          ok: false,
          reason: 'UNAUTHORIZED',
          message: 'Premium API not configured',
          items: [],
        },
        { status: 500 }
      );
    }

    // Call upstream Premium API
    const upstreamResponse = await fetch(`${upstreamUrl}/simple-compare`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(apiKey && { 'X-API-Key': apiKey }),
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(10000), // 10s timeout
    });

    if (!upstreamResponse.ok) {
      return NextResponse.json(
        {
          ok: false,
          reason: 'UPSTREAM_ERROR',
          message: `Upstream returned ${upstreamResponse.status}`,
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
