import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { ServerEnv } from '$lib/server/env';

export const GET: RequestHandler = async ({ url, fetch }) => {
    const categorySlug = url.searchParams.get('category_slug');
    const limit = url.searchParams.get('limit') || '48';
    const offset = url.searchParams.get('offset') || '0';
    const status = url.searchParams.get('status') || 'ACTIVE';

    const apiUrl = ServerEnv.INTERNAL_API_URL;
    const tenantId = ServerEnv.TENANT_ID;

    // Construct backend URL
    const targetUrl = new URL(`${apiUrl}/api/v1/client/products/`);
    if (categorySlug) targetUrl.searchParams.set('category_slug', categorySlug);
    targetUrl.searchParams.set('limit', limit);
    targetUrl.searchParams.set('offset', offset);
    targetUrl.searchParams.set('status', status);

    try {
        const res = await fetch(targetUrl.toString(), {
            headers: { 'x-tenant': tenantId }
        });

        if (!res.ok) {
            return json({ error: 'Backend error' }, { status: res.status });
        }

        const data = await res.json();
        return json(data);
    } catch (e) {
        console.error('[API PROXY FAILED]', e);
        return json({ error: 'Internal server error' }, { status: 500 });
    }
};
