import type { LayoutServerLoad } from './$types';
import { ServerEnv } from '$lib/server/env';

export const load: LayoutServerLoad = async ({ fetch }) => {
    const apiUrl = ServerEnv.INTERNAL_API_URL;
    try {
        const response = await fetch(`${apiUrl}/api/v1/client/settings/primary`, {
            signal: AbortSignal.timeout(5000)
        });
        const shopInfo = await response.json();

        return {
            shopInfo
        };
    } catch (e) {
        console.error("Failed to load shop info:", e);
        return {
            shopInfo: {
                name: "Micsmo Elite",
                slogan: "Bật tông trắng sáng",
                description: "Nền tảng mỹ phẩm Elite hàng đầu Việt Nam.",
                hotline: "1800-MICSMO",
                email: "legal@micsmo.com",
                address: "Bitexco Financial Tower, Quận 1, TP. Hồ Chí Minh"
            }
        };
    }
};
