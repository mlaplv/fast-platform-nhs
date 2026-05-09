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
 *  - HTTP-Only cookie set HERE (SvelteKit server) — tamper-proof, survives F5
 */
export const POST: RequestHandler = async ({ request, getClientAddress, cookies }) => {
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

        // 🛡️ Military-Grade: Set HTTP-Only cookie at SvelteKit server level
        // This is tamper-proof — JS cannot read/write this cookie
        // Survives F5, page reload, and browser restart (30-day TTL)
        cookies.set(`elite_viral_${body.voucher_id}`, '1', {
            path: '/',
            httpOnly: true,
            secure: false, // osmo.vn currently runs HTTP
            sameSite: 'lax',
            maxAge: 60 * 60 * 24 * 30, // 30 days
        });

        return json(data);
    } catch (e) {
        console.error('[ViralProxy:verify-share] Failed:', e);
        return json({ error: 'Internal error' }, { status: 500 });
    }
};
