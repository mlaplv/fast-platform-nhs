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

        return {
            shopInfo,
            vouchers: vouchersData.data || []
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
