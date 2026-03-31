import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { env } from '$env/dynamic/private';
import { isMobileDevice } from '$lib/utils/device';

export const load: PageServerLoad = async ({ 
    params, 
    fetch, 
    getClientAddress, 
    request 
}: { 
    params: Record<string, string>, 
    fetch: any, // Fallback for IDE generation issues, better than 'any' if we could import correct type
    getClientAddress: () => string, 
    request: Request 
}) => {
    const { slug } = params;
    
    // R00: NO MOCK, NO SILENT FALLBACK. Let it fail clearly if API is down.
    const apiUrl = env.INTERNAL_API_URL || 'http://api:8000';
    const tenantId = env.APP_DOMAIN?.split('.')[0] || 'default';
    const targetUrl = `${apiUrl}/api/v1/client/products/slug/${slug}`;
    
    let res;
    try {
        res = await fetch(targetUrl, {
            headers: { 'x-tenant': tenantId }
        });
    } catch (e: unknown) {
        const err = e as Error;
        console.error(`[FETCH FAILED], không thể kết nối tới Backend!`);
        console.error(`URL: ${targetUrl}`);
        console.error(`Error: ${err.message}`);
        console.error(`Hint: Kiểm tra INTERNAL_API_URL (${apiUrl}) và trạng thái container 'api'`);
        
        throw error(503, {
            message: "Dịch vụ tạm thời không khả dụng (Backend Connection Failed)",
            details: `Failed to reach API at ${apiUrl}. Please check infra config.`
        });
    }

    if (!res.ok) {
        // Broad error exposure for development!
        throw error(res.status, { 
            message: `API Error: ${res.statusText} (${res.status})`,
            details: `Failed to fetch product with slug: ${slug} from ${targetUrl}`
        });
    }

    const product = await res.json() as import('$lib/types').Product;

    // Tối ưu lấy IP thực tế (Elite V2.2 Protocol)
    const effectiveIp = request.headers.get('cf-connecting-ip') ||
                      request.headers.get('x-real-ip') ||
                      request.headers.get('x-forwarded-for')?.split(',')[0].trim() ||
                      '127.0.0.1';

    const userAgent = request.headers.get('user-agent') || '';
    const isMobile = isMobileDevice(userAgent);

    return {
        product,
        effectiveIp,
        metadata: {
            timestamp: new Date().toISOString(),
            userAgent,
            isMobile
        }
    };
};
