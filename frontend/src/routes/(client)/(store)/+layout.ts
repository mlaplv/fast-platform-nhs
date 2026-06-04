import type { LayoutLoad } from './$types';
import { error } from '@sveltejs/kit';

export const load: LayoutLoad = async ({ fetch }) => {
    let shopInfo = null;
    let vouchers = [];

    // 1. Elite V2.2: Cache-First Strategy — check sessionStorage for zero-latency boot
    if (typeof window !== 'undefined') {
        try {
            const cachedShop = sessionStorage.getItem('primary_config');
            if (cachedShop) shopInfo = JSON.parse(cachedShop);

            const cachedVouchers = sessionStorage.getItem('vouchers_config');
            if (cachedVouchers) vouchers = JSON.parse(cachedVouchers);
        } catch (e) {
            console.warn("[Cache-First] Failed to parse cached configuration:", e);
        }
    }

    // 2. Elite V2.2: Zero-Latency return with asynchronous background synchronization
    if (shopInfo) {
        Promise.all([
            fetch('/api/v1/client/settings/primary'),
            fetch('/api/v1/client/home/vouchers')
        ]).then(async ([shopResp, voucherResp]) => {
            if (shopResp.ok) {
                const freshShop = await shopResp.json();
                sessionStorage.setItem('primary_config', JSON.stringify(freshShop));
                
                // Reactive sync back to UI state store (Nanobot)
                const { getClientUi } = await import('$lib/state/commerce/ui.svelte');
                getClientUi().settings = freshShop;
            }
            if (voucherResp.ok) {
                const freshVouchersData = await voucherResp.json();
                const freshVouchers = freshVouchersData.data || [];
                sessionStorage.setItem('vouchers_config', JSON.stringify(freshVouchers));
                
                // Reactive sync back to Cart state store
                const { getGlobalCart } = await import('$lib/state/commerce/cart.svelte');
                getGlobalCart().setVouchers(freshVouchers);
            }
        }).catch(e => console.warn("[Background Sync Failed]", e));

        return {
            shopInfo,
            vouchers
        };
    }

    // 3. Fallback: Cold start fetch (Synchronous block only on first load)
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

        const freshShop = await shopResp.json();
        const vouchersData = voucherResp.ok ? await voucherResp.json() : { data: [] };
        const freshVouchers = vouchersData.data || [];

        if (typeof window !== 'undefined') {
            try {
                sessionStorage.setItem('primary_config', JSON.stringify(freshShop));
                sessionStorage.setItem('vouchers_config', JSON.stringify(freshVouchers));
            } catch (e) {}
        }

        return {
            shopInfo: freshShop,
            vouchers: freshVouchers
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
