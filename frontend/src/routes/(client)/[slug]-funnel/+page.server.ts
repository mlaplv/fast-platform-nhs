import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { ServerEnv } from '$lib/server/env';
import { isMobileDevice } from '$lib/utils/device';

export const load: PageServerLoad = async ({ 
    params, 
    fetch, 
    request 
}: { 
    params: Record<string, string>, 
    fetch: typeof globalThis.fetch, 
    request: Request 
}) => {
    const { slug } = params;
    
    // R00: NO MOCK, NO SILENT FALLBACK. Let it fail clearly if API is down.
    const apiUrl = ServerEnv.INTERNAL_API_URL;
    const tenantId = ServerEnv.TENANT_ID;
    const targetUrl = `${apiUrl}/api/v1/client/products/slug/${slug}`;
    
    let res;
    try {
        res = await fetch(targetUrl, {
            headers: { 'x-tenant': tenantId },
            signal: AbortSignal.timeout(5000)
        });
    } catch (e: any) {
        const isTimeout = e.name === 'TimeoutError' || e.message?.includes('timeout');
        console.error(`[FUNNEL FETCH FAILED] ${isTimeout ? 'TIMEOUT' : 'CONNECTION ERROR'}`);
        console.error(`URL: ${targetUrl}`);
        
        throw error(isTimeout ? 504 : 503, {
            message: isTimeout 
                ? "Hệ thống đang phản hồi chậm (Backend Timeout)" 
                : "Dịch vụ tạm thời không khả dụng (Backend Connection Failed)",
            details: isTimeout 
                ? "Vui lòng chờ giây lát và thử lại (Request timed out after 5s)."
                : `Failed to reach API at ${apiUrl}. Please check infra config.`
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

    // ELITE V2.2: Global Settings Synchronization
    // Fetch primary shop metadata to replace hardcoded fallback values in child components
    let shopInfo = null;
    try {
        const settingsRes = await fetch(`${apiUrl}/api/v1/client/settings/primary`, {
            headers: { 'x-tenant': tenantId },
            signal: AbortSignal.timeout(3000)
        });
        if (settingsRes.ok) {
            shopInfo = await settingsRes.json();
        }
    } catch (e) {
        console.error("[SHOP INFO FETCH FAILED]", e);
        // We don't throw here to allow the product page to load even if global settings are down
    }

    // Tối ưu lấy IP thực tế (Elite V2.2 Protocol)
    const effectiveIp = request.headers.get('cf-connecting-ip') ||
                      request.headers.get('x-real-ip') ||
                      request.headers.get('x-forwarded-for')?.split(',')[0].trim() ||
                      '127.0.0.1';

    const userAgent = request.headers.get('user-agent') || '';
    const isMobile = isMobileDevice(userAgent);

    return {
        product,
        shopInfo,
        effectiveIp,
        metadata: {
            timestamp: new Date().toISOString(),
            userAgent,
            isMobile
        }
    };
};
