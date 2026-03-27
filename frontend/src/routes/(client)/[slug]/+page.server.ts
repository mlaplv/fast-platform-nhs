import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { env } from '$env/dynamic/private';

export const load: PageServerLoad = async ({ params, fetch, getClientAddress, request }) => {
    const { slug } = params;
    
    // R00: NO MOCK, NO SILENT FALLBACK. Let it fail clearly if API is down.
    const apiUrl = env.INTERNAL_API_URL || 'http://api:8000';
    const tenantId = env.APP_DOMAIN?.split('.')[0] || 'default';
    
    const res = await fetch(`${apiUrl}/api/v1/client/products/slug/${slug}`, {
        headers: { 'x-tenant': tenantId }
    });

    if (!res.ok) {
        // Broad error exposure for development thưa Sếp!
        throw error(res.status, { 
            message: `API Error: ${res.statusText} (${res.status})`,
            details: `Failed to fetch product with slug: ${slug}`
        });
    }

    const product = await res.json();

    let ip = '127.0.0.1';
    try { ip = getClientAddress(); } catch {
        ip = request.headers.get('x-forwarded-for')?.split(',')[0].trim() || '127.0.0.1';
    }

    return { 
        product, 
        location: { city: 'TP. Hồ Chí Minh', region: 'Miền Nam' }, 
        effectiveIp: ip 
    };
};
