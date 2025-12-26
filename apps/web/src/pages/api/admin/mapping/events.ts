/**
 * Next.js API route proxy for /admin/mapping/events
 */

import type { NextApiRequest, NextApiResponse } from 'next';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const { page, page_size, state, insurer } = req.query;

    const params = new URLSearchParams();
    if (page) params.append('page', page as string);
    if (page_size) params.append('page_size', page_size as string);
    if (state) params.append('state', state as string);
    if (insurer) params.append('insurer', insurer as string);

    const url = `${API_BASE_URL}/admin/mapping/events?${params.toString()}`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    return res.status(200).json(data);
  } catch (error: any) {
    console.error('Admin mapping events proxy error:', error);
    return res.status(500).json({ error: error.message });
  }
}
