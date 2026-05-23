import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ 
    params, 
    fetch
}: { 
    params: Record<string, string>, 
    fetch: typeof globalThis.fetch
}) => {
    const { slug } = params;
    
    try {
        // Step 1: Fetch Product & Shop Settings in Parallel
        const [prodRes, settingsRes] = await Promise.all([
            fetch(`/api/v1/client/products/slug/${slug}`, {
                signal: AbortSignal.timeout(4000)
            }),
            fetch(`/api/v1/client/settings/primary`, {
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
        const [statsRes, reviewsRes, relatedRes] = await Promise.all([
            fetch(`/api/v1/client/reviews/stats?entity_type=PRODUCT&entity_id=${product.id}`, {
                signal: AbortSignal.timeout(2000)
            }).catch(() => null),
            fetch(`/api/v1/client/reviews?entity_type=PRODUCT&entity_id=${product.id}&status=APPROVED&limit=20`, {
                signal: AbortSignal.timeout(2000)
            }).catch(() => null),
            fetch(`/api/v1/client/products/?limit=9`, {
                signal: AbortSignal.timeout(2000)
            }).catch(() => null)
        ]);

        const reviewStats = statsRes && statsRes.ok ? await statsRes.json() : null;
        const reviewsData = reviewsRes && reviewsRes.ok ? await reviewsRes.json() : { items: [] };
        
        let relatedProducts = [];
        if (relatedRes && relatedRes.ok) {
            const relData = await relatedRes.json();
            relatedProducts = (relData.data || [])
                .filter((p: any) => p.id !== product.id)
                .slice(0, 8);
        }

        let userAgent = '';
        let isMobile = false;
        if (typeof navigator !== 'undefined') {
            userAgent = navigator.userAgent;
            isMobile = window.innerWidth <= 768 || /Mobi|Android|iPhone/i.test(userAgent);
        }

        // Parse unlocked vouchers from cookies on the client side
        let unlockedVoucherIds: string[] = [];
        if (typeof document !== 'undefined') {
            unlockedVoucherIds = document.cookie.split(';')
                .map(c => c.trim())
                .filter(c => c.startsWith('elite_viral_') && c.includes('='))
                .filter(c => {
                    const parts = c.split('=');
                    return parts[1] === '1';
                })
                .map(c => c.split('=')[0].replace('elite_viral_', ''));
        }

        return {
            product,
            shopInfo,
            reviewStats,
            reviews: reviewsData.items || [],
            relatedProducts,
            unlockedVoucherIds,
            isMobile,
            effectiveIp: '127.0.0.1',
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
