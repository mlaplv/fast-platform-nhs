import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { ServerEnv } from '$lib/server/env';

/**
 * POST /api/client/viral/share-intent
 * Proxy to backend ViralController — issues HMAC One-Time Token.
 *
 * This server-side proxy:
 *  1. Hides the internal backend URL (Zero-Trust)
 *  2. Injects real client IP from x-forwarded-for / x-real-ip
 *  3. Forwards User-Agent and Accept-Language for fingerprinting
 */
export const POST: RequestHandler = async ({ request, getClientAddress }) => {
    const body = await request.json().catch(() => null);
    if (!body?.product_id) {
        return json({ error: 'Missing product_id' }, { status: 400 });
    }

    const apiUrl = ServerEnv.INTERNAL_API_URL;
    const tenantId = ServerEnv.TENANT_ID;

    // Inject real IP — SvelteKit's getClientAddress() respects trust-proxy config
    const clientIp = getClientAddress();

    try {
        const res = await fetch(`${apiUrl}/api/v1/client/viral/share-intent`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-tenant': tenantId,
                'x-real-ip': clientIp,
                'user-agent': request.headers.get('user-agent') || '',
                'accept-language': request.headers.get('accept-language') || '',
            },
            body: JSON.stringify({ product_id: body.product_id }),
        });

        const data = await res.json();

        if (!res.ok) {
            return json(data, { status: res.status });
        }

        return json(data);
    } catch (e) {
        console.error('[ViralProxy:share-intent] Failed:', e);
        return json({ error: 'Internal error' }, { status: 500 });
    }
};
