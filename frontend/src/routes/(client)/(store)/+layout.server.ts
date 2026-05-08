import type { LayoutServerLoad } from './$types';
import { error } from '@sveltejs/kit';
import { ServerEnv } from '$lib/server/env';
import { isMobileDevice } from '$lib/utils/device';

export const load: LayoutServerLoad = async ({ fetch, request, setHeaders }) => {
    const apiUrl = ServerEnv.INTERNAL_API_URL;
    const userAgent = request.headers.get('user-agent') || '';
    const isMobile = isMobileDevice(userAgent);

    // Elite Performance Fix P2.1: Cache layout data for 60s
    // Tránh re-fetch shopInfo + vouchers trên mỗi lần click sản phẩm
    setHeaders({
        'cache-control': 'public, max-age=60, s-maxage=60'
    });

    try {
        // Elite V2.2: Parallel Fetch for Zero-Hydration Performance
        const [shopResp, voucherResp] = await Promise.all([
            fetch(`${apiUrl}/api/v1/client/settings/primary`),
            fetch(`${apiUrl}/api/v1/client/home/vouchers`)
        ]);

        if (!shopResp.ok) {
            throw error(shopResp.status, {
                message: "Không thể tải cấu hình cửa hàng (API Failure)",
                details: "Hệ thống yêu cầu Shop Settings để khởi tạo layout."
            });
        }

        const shopInfo = await shopResp.json();
        const vouchersData = voucherResp.ok ? await voucherResp.json() : { data: [] };

        return {
            shopInfo,
            vouchers: vouchersData.data || [],
            isMobile
        };
    } catch (e: unknown) {
        const err = e as { status?: number; message?: string };
        if (err.status) throw e; // Pass through SvelteKit errors
        throw error(503, {
            message: "Dịch vụ tạm thời không khả dụng",
            details: "Không thể kết nối tới Backend Service."
        });
    }
};
