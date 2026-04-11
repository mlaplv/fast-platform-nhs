import type { LayoutServerLoad } from './$types';
import { ServerEnv } from '$lib/server/env';

export const load: LayoutServerLoad = async ({ fetch }) => {
    const apiUrl = ServerEnv.INTERNAL_API_URL;
    try {
        const response = await fetch(`${apiUrl}/api/v1/client/settings/primary`, {
            signal: AbortSignal.timeout(5000)
        });
        if (!response.ok) {
            throw error(response.status, {
                message: "Không thể tải cấu hình cửa hàng (API Failure)",
                details: "Hệ thống yêu cầu Shop Settings để khởi tạo layout."
            });
        }
        const shopInfo = await response.json();

        return {
            shopInfo
        };
    } catch (e: any) {
        if (e.status) throw e; // Pass through SvelteKit errors
        throw error(503, {
            message: "Dịch vụ tạm thời không khả dụng",
            details: "Không thể kết nối tới Backend Service."
        });
    }
};
