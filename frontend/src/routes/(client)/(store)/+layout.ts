import type { LayoutLoad } from './$types';
import { error } from '@sveltejs/kit';

export const load: LayoutLoad = async ({ fetch }) => {
    try {
        const [shopResp, voucherResp] = await Promise.all([
            fetch('/api/v1/client/settings/primary'),
            fetch('/api/v1/client/home/vouchers')
        ]);

        if (!shopResp.ok) {
            throw error(shopResp.status, {
                message: "Không thể tải cấu hình cửa hàng (API Failure)",
                details: "Hệ thống yêu cầu Shop Settings để khởi tạo layout."
            });
        }

        const shopInfo = await shopResp.json();
        const vouchersData = voucherResp.ok ? await voucherResp.json() : { data: [] };

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

        // Detect device on the client side
        let isMobile = false;
        if (typeof window !== 'undefined') {
            isMobile = window.innerWidth <= 768 || /Mobi|Android|iPhone/i.test(navigator.userAgent);
        }

        return {
            shopInfo,
            vouchers: vouchersData.data || [],
            unlockedVoucherIds,
            isMobile
        };
    } catch (e: unknown) {
        const err = e as { status?: number };
        if (err.status) throw e;
        throw error(503, {
            message: "Dịch vụ tạm thời không khả dụng",
            details: "Không thể kết nối tới Backend Service."
        });
    }
};
