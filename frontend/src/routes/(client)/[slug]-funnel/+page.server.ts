import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { ServerEnv } from '$lib/server/env';
import { isMobileDevice } from '$lib/utils/device';

export const load: PageServerLoad = async ({ 
    params, 
    fetch, 
    request,
    cookies
}: { 
    params: Record<string, string>, 
    fetch: typeof globalThis.fetch, 
    request: Request,
    cookies: import('@sveltejs/kit').Cookies
}) => {
    const { slug } = params;
    
    // R00: NO MOCK, NO SILENT FALLBACK. Let it fail clearly if API is down.
    const apiUrl = ServerEnv.INTERNAL_API_URL;
    const tenantId = ServerEnv.TENANT_ID;
    
    try {
        // Step 1: Fetch Product & Shop Settings in Parallel
        const [prodRes, settingsRes] = await Promise.all([
            fetch(`${apiUrl}/api/v1/client/products/slug/${slug}`, {
                headers: { 'x-tenant': tenantId },
                signal: AbortSignal.timeout(4000)
            }),
            fetch(`${apiUrl}/api/v1/client/settings/primary`, {
                headers: { 'x-tenant': tenantId },
                signal: AbortSignal.timeout(3000)
            }).catch(() => null)
        ]);

        if (!prodRes.ok) {
            throw error(prodRes.status, { 
                message: `API Error: ${prodRes.statusText} (${prodRes.status})`,
                details: `Failed to fetch product with slug: ${slug}`
            });
        }

        const product = await prodRes.json() as import('$lib/types').Product;
        const shopInfo = settingsRes && settingsRes.ok ? await settingsRes.json() : null;

        // Step 2: Fetch Supplemental Data (Reviews, Stats, Related) in Parallel
        // This ensures the landing page modules (VerifiedReviews, OfferGrid) have data immediately
        const [statsRes, reviewsRes, relatedRes] = await Promise.all([
            fetch(`${apiUrl}/api/v1/client/reviews/stats?entity_type=PRODUCT&entity_id=${product.id}`, {
                headers: { 'x-tenant': tenantId },
                signal: AbortSignal.timeout(2000)
            }).catch(() => null),
            fetch(`${apiUrl}/api/v1/client/reviews?entity_type=PRODUCT&entity_id=${product.id}&status=APPROVED&limit=20`, {
                headers: { 'x-tenant': tenantId },
                signal: AbortSignal.timeout(2000)
            }).catch(() => null),
            fetch(`${apiUrl}/api/v1/client/products/?limit=9`, {
                headers: { 'x-tenant': tenantId },
                signal: AbortSignal.timeout(2000)
            }).catch(() => null)
        ]);

        // Parse Supplemental Data
        const reviewStats = statsRes && statsRes.ok ? await statsRes.json() : null;
        const reviewsData = reviewsRes && reviewsRes.ok ? await reviewsRes.json() : { items: [] };
        
        let relatedProducts = [];
        if (relatedRes && relatedRes.ok) {
            const relData = await relatedRes.json();
            relatedProducts = (relData.data || [])
                .filter((p: any) => p.id !== product.id)
                .slice(0, 8);
        }

        const userAgent = request.headers.get('user-agent') || '';
        const isMobile = isMobileDevice(userAgent);
        const effectiveIp = request.headers.get('cf-connecting-ip') || '127.0.0.1';

        // Elite V2.2: Military-Grade Security - Read HTTP-Only Cookies for unlocked vouchers
        const unlockedVoucherIds = cookies.getAll()
            .filter(c => c.name.startsWith('elite_viral_') && c.value === '1')
            .map(c => c.name.replace('elite_viral_', ''));

        return {
            product,
            shopInfo,
            reviewStats,
            reviews: reviewsData.items || [],
            relatedProducts,
            unlockedVoucherIds,
            isMobile,
            effectiveIp,
            metadata: {
                timestamp: new Date().toISOString(),
                userAgent,
                isMobile
            }
        };
    } catch (err: any) {
        if (err.status) throw err;
        console.error(`[FUNNEL LOAD FAILED]`, err);
        throw error(503, { message: "Dịch vụ tạm thời không khả dụng" });
    }
};
