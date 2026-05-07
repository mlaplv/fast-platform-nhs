import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { ServerEnv } from '$lib/server/env';

/**
 * POST /api/client/viral/verify-share
 * Proxy to backend ViralController — verifies HMAC OTT and returns DB voucher.
 *
 * Security:
 *  - Voucher code is NEVER exposed in the page source (only returned here after verify)
 *  - Backend deletes the token after first successful verify (replay-proof)
 */
export const POST: RequestHandler = async ({ request, getClientAddress }) => {
    const body = await request.json().catch(() => null);

    if (!body?.product_id || !body?.fingerprint || !body?.token || !body?.voucher_id) {
        return json({ error: 'Missing required fields' }, { status: 400 });
    }

    const apiUrl = ServerEnv.INTERNAL_API_URL;
    const tenantId = ServerEnv.TENANT_ID;
    const clientIp = getClientAddress();

    try {
        const res = await fetch(`${apiUrl}/api/v1/client/viral/verify-share`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-tenant': tenantId,
                'x-real-ip': clientIp,
                'user-agent': request.headers.get('user-agent') || '',
                'accept-language': request.headers.get('accept-language') || '',
            },
            body: JSON.stringify({
                product_id: body.product_id,
                fingerprint: body.fingerprint,
                token: body.token,
                voucher_id: body.voucher_id,
            }),
        });

        const data = await res.json();

        if (!res.ok) {
            // Forward structured error from backend (e.g. "Mã đã hết hạn")
            return json(data, { status: res.status });
        }

        return json(data);
    } catch (e) {
        console.error('[ViralProxy:verify-share] Failed:', e);
        return json({ error: 'Internal error' }, { status: 500 });
    }
};
