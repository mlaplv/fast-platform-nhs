import { setContext, getContext } from 'svelte';
import { apiClient, ApiError } from '$lib/utils/apiClient';
import { goto } from '$app/navigation';
import type { Product, ProductVariant, PromotionDeal } from '$lib/types';
import type { GenericResponse } from '$lib/state/types';

/** Identity Shield API response types (must match backend schema) */
interface CustomerLookupResponse {
    is_recurring: boolean;
    is_trusted_device: boolean;
    name_masked: string | null;
    address_masked: string | null;
}
/** Domain model for auto-fill state */
interface CustomerData {
    nameMasked?: string;
    addressMasked?: string;
    fullName?: string;
    address?: string;
    isRecurring: boolean;
    isTrustedDevice: boolean;
}

/**
 * ELITE V2.2: Nanobot Store for Funnel Shop (Context-Safe Edition)
 * Handles cart state, order bump, and checkout flow.
 */
export class ShopStore {
    // 1. Core State ($state)
    product = $state<Product | null>(null);
    variant = $state<ProductVariant | null>(null);
    quantity = $state<number>(1);

    // UI & Funnel State
    isCheckoutOpen = $state<boolean>(false);
    isSubmitting = $state<boolean>(false);
    orderSuccess = $state<boolean>(false);
    error = $state<string | null>(null);
    customerData = $state<CustomerData | null>(null);

    // Scarcity Timer (Elite V2.2)
    timeLeft = $state<number>(0);
    private _timerId: ReturnType<typeof setTimeout> | null = null;

    // 2. Computed State ($derived)
    // ... logic remains identical ...
    totalAmount = $derived.by((): number => {
        let baseTotal = this.currentPrice * this.quantity;
        const deals = this.product?.metadata?.active_deals;
        if (deals && deals.length > 0) {
            const sortedDeals = [...deals].sort((a, b) => (b.buy_qty + (b.get_qty || 0)) - (a.buy_qty + (a.get_qty || 0)));
            for (const deal of sortedDeals) {
                const totalInBundle = deal.buy_qty + (deal.get_qty || 0);
                if (this.quantity >= totalInBundle) {
                    const bundleCount = Math.floor(this.quantity / totalInBundle);
                    const remainder = this.quantity % totalInBundle;
                    baseTotal = (bundleCount * deal.fixed_price) + (remainder * this.currentPrice);
                    break;
                }
            }
        }
        return baseTotal;
    });

    appliedDeal = $derived.by((): PromotionDeal | null => {
        const deals = this.product?.metadata?.active_deals;
        if (!deals) return null;
        const sortedDeals = [...deals].sort((a, b) => (b.buy_qty + (b.get_qty || 0)) - (a.buy_qty + (a.get_qty || 0)));
        for (const deal of sortedDeals) {
            const totalInBundle = deal.buy_qty + (deal.get_qty || 0);
            if (this.quantity >= totalInBundle) return deal;
        }
        return null;
    });

    nextDeal = $derived.by((): { deal: PromotionDeal; missing: number; priceDiff: number } | null => {
        const deals = this.product?.metadata?.active_deals;
        if (!deals || !this.product) return null;
        const currentPriceTotal = this.currentPrice * this.quantity;
        const sortedDeals = [...deals].sort((a, b) => (a.buy_qty + (a.get_qty || 0)) - (b.buy_qty + (b.get_qty || 0)));
        for (const deal of sortedDeals) {
            const totalInBundle = deal.buy_qty + (deal.get_qty || 0);
            if (this.quantity < totalInBundle) {
                return { 
                    deal, 
                    missing: totalInBundle - this.quantity,
                    priceDiff: deal.fixed_price - currentPriceTotal
                };
            }
        }
        return null;
    });

    currentPrice = $derived.by((): number => {
        if (!this.product) return 0;
        return this.variant?.discountPrice ?? this.product.discountPrice ??
               this.variant?.price ?? this.product.price ?? 0;
    });

    originalPrice = $derived.by((): number => {
        if (!this.product) return 0;
        return this.variant?.price ?? this.product.price ?? 0;
    });

    // 3. Actions
    init(productData: Product): void {
        this.product = productData;
        this.timeLeft = productData.metadata?.scarcity_seconds ?? 1800;
        this.startTimer();
        if (!this.variant && productData?.variants && productData.variants.length > 0) {
            this.variant = productData.variants[0];
        }
    }

    startTimer(): void {
        if (this._timerId) clearInterval(this._timerId);
        this._timerId = setInterval(() => {
            if (this.timeLeft > 0) {
                this.timeLeft--;
            } else {
                this.stopTimer();
            }
        }, 1000);
    }

    stopTimer(): void {
        if (this._timerId) {
            clearInterval(this._timerId);
            this._timerId = null;
        }
    }

    dispose(): void {
        this.stopTimer();
    }

    addItem(productData: Product): void {
        this.init(productData);
        this.openCheckout();
    }

    selectVariant(v: ProductVariant): void {
        this.variant = v;
    }

    selectVariantByTier(indices: number[]): void {
        if (!this.product?.variants) return;
        const found = this.product.variants.find((v: ProductVariant) => 
            v.tierIndex.length === indices.length && 
            v.tierIndex.every((val: number, idx: number) => val === indices[idx])
        );
        if (found) {
            this.variant = found;
            this.quantity = 1; // Reset to 1!
        }
    }

    setQuantity(q: number): void {
        if (q < 1) return;
        this.quantity = q;
    }

    openCheckout(): void {
        this.isCheckoutOpen = true;
    }

    closeCheckout(): void {
        this.isCheckoutOpen = false;
        this.orderSuccess = false;
        this.error = null;
        this.customerData = null;
    }

    async lookupCustomer(phone: string): Promise<void> {
        if (phone.length < 10) return;
        try {
            const fingerprint = this.getFingerprint();
            const res = await apiClient.post<CustomerLookupResponse>('/api/v1/client/checkout/lookup', { phone, fingerprint });
            if (res?.is_recurring) {
                this.customerData = {
                    nameMasked: res.name_masked ?? undefined,
                    addressMasked: res.address_masked ?? undefined,
                    isRecurring: true,
                    isTrustedDevice: res.is_trusted_device
                };
            } else {
                this.customerData = null;
            }
        } catch (err: unknown) {
            console.error('Identity lookup failed:', err instanceof ApiError ? err.message : err);
        }
    }


    async submitCheckout(customer: { name: string; phone: string; address: string }): Promise<void> {
        if (!this.product) return;
        this.isSubmitting = true;
        this.error = null;

        try {
            const res = await apiClient.post<GenericResponse<unknown>>('/api/v1/client/checkout/stealth', {
                product_id: this.product.id,
                variant_id: this.variant?.id,
                customer_name: customer.name,
                customer_phone: customer.phone,
                customer_address: customer.address,
                quantity: this.quantity
            });

            if (res.ok || res.status === 'success') {
                const orderId = (res as any).id;
                this.closeCheckout();
                if (orderId) {
                    goto(`/checkout/success/${orderId}?phone=${encodeURIComponent(customer.phone)}`);
                }
            } else {
                this.error = res.message ?? 'Có lỗi xảy ra, vui lòng thử lại';
            }
        } catch (err: unknown) {
            this.error = err instanceof ApiError ? err.message : 'Không thể kết nối máy chủ';
        } finally {
            this.isSubmitting = false;
        }
    }

    private getFingerprint(): string {
        return getFingerprint();
    }
}

/** ELITE V2.2: Device Fingerprinting Utility */
export function getFingerprint(): string {
    if (typeof window === 'undefined') return 'server';
    const nav = window.navigator;
    const screen = window.screen;
    const str = `${nav.userAgent}|${nav.language}|${screen.width}x${screen.height}|${screen.colorDepth}`;
    // Simple hash (not cryptographic but enough for a "fingerprint" label in UI)
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(16);
}

// 🚀 ELITE CONTEXT KEYS (Elite V2.2)
const SHOP_KEY = Symbol('SHOP_STORE');

export function setShopStore() {
    return setContext(SHOP_KEY, new ShopStore());
}

export function getShopStore(): ShopStore {
    return getContext(SHOP_KEY);
}

/** 
 * 🛡️ ELITE V2.2: Safety Export (Legacy Patch)
 * This is a dummy export to prevent ESM SyntaxErrors in case of cached imports 
 * or legacy components still referencing 'shopStore' directly.
 */
export const shopStore = {
    getFingerprint: () => getFingerprint()
};
