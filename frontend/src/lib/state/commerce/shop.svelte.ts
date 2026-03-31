import { setContext, getContext } from 'svelte';
import { apiClient, ApiError } from '$lib/utils/apiClient';
import { goto } from '$app/navigation';
import type { Product, ProductVariant, PromotionDeal } from '$lib/types';

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
    isRecurring: boolean;
    isTrustedDevice: boolean;
}

/** Checkout success response from stealth endpoint */
interface CheckoutSuccessResponse {
    ok: boolean;
    status?: string;
    id?: string;
    message?: string;
}

export interface DiagnosticReport {
    severity: string;
    analysis: string;
    reasoning: string;
    recommendation: string;
    suggested_products: Array<{ id: string; name: string; reason: string }>;
    quantity: number;
    promotion_label?: string;
}

/**
 * ELITE V2.2: Nanobot Store for Funnel Shop (Context-Safe Edition)
 * Handles cart state, order bump, and checkout flow.
 */
export class ShopStore {
    // Core State
    product = $state<Product | null>(null);
    variant = $state<ProductVariant | null>(null);
    quantity = $state<number>(1);

    // UI & Funnel State
    isCheckoutOpen = $state<boolean>(false);
    isSubmitting = $state<boolean>(false);
    orderSuccess = $state<boolean>(false);
    error = $state<string | null>(null);
    customerData = $state<CustomerData | null>(null);
    
    // Diagnostic State
    diagnosticResult = $state<DiagnosticReport | null>(null);
    isAnalyzing = $state<boolean>(false);

    // Scarcity Timer
    timeLeft = $state<number>(0);
    private _timerId: ReturnType<typeof setTimeout> | null = null;

    // Computed State
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
            const res = await apiClient.post<CustomerLookupResponse>('/api/v1/client/checkout/lookup', { phone });
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
            const message = err instanceof Error ? err.message : String(err);
            console.error('Identity lookup failed:', message);
        }
    }


    async submitCheckout(customer: { name: string; phone: string; address: string }): Promise<void> {
        if (!this.product) return;
        this.isSubmitting = true;
        this.error = null;

        try {
            const res = await apiClient.post<CheckoutSuccessResponse>('/api/v1/client/checkout/stealth', {
                product_id: this.product.id,
                variant_id: this.variant?.id,
                customer_name: customer.name,
                customer_phone: customer.phone,
                customer_address: customer.address,
                quantity: this.quantity
            });

            if (res.ok || res.status === 'success') {
                const orderId = res.id;
                this.closeCheckout();
                if (orderId) {
                    goto(`/checkout/success/${orderId}?phone=${encodeURIComponent(customer.phone)}`);
                }
            } else {
                this.error = res.message ?? 'Có lỗi xảy ra, vui lòng thử lại';
            }
        } catch (err: unknown) {
            this.error = err instanceof Error ? err.message : 'Không thể kết nối máy chủ';
        } finally {
            this.isSubmitting = false;
        }
    }

    async analyzeDiagnostics(quizData: Array<{q: string, a: string}>): Promise<void> {
        if (!this.product) return;
        this.isAnalyzing = true;
        this.error = null;

        const startTime = Date.now();
        try {
            const res = await apiClient.post<DiagnosticReport>('/api/v1/client/diagnostics/analyze', {
                product_name: this.product.name,
                quiz_data: quizData
            });

            // 🚀 Cinematic Experience: Min-scan duration (Elite V2.2)
            const MIN_SCAN_DURATION = 12000;
            const elapsed = Date.now() - startTime;
            if (elapsed < MIN_SCAN_DURATION) {
                await new Promise(resolve => setTimeout(resolve, MIN_SCAN_DURATION - elapsed));
            }

            if (!res) throw new Error('AI analysis returned empty');
            
            this.diagnosticResult = res;
            if (res.quantity) {
                // 🎁 Viral 2026: Auto-apply deals if AI recommends a 'buy' threshold
                const deals = this.product?.metadata?.active_deals;
                const matchingDeal = deals?.find((d: PromotionDeal) => d.buy_qty === res.quantity);
                
                if (matchingDeal) {
                    this.setQuantity(matchingDeal.buy_qty + (matchingDeal.get_qty || 0));
                } else {
                    this.setQuantity(res.quantity);
                }
            }
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : String(err);
            console.error('Diagnostic analysis failed:', message);
            
            // 🛡️ Fail-safe Fallback: Apply "Mua 2 Tặng 1" by default if AI fails
            const fallbackQty = 2;
            const deals = this.product?.metadata?.active_deals;
            const matchingDeal = deals?.find((d: PromotionDeal) => d.buy_qty === fallbackQty);
            
            this.diagnosticResult = {
                severity: "Trung bình",
                analysis: "Dựa trên các dấu hiệu bạn cung cấp, hệ thống ghi nhận tình trạng cần được xử lý sớm để tránh chuyển biến nặng.",
                reasoning: "Các biểu hiện lâm sàng cho thấy tuyến mồ hôi đang hoạt động quá mức do thay đổi nội tiết hoặc môi trường.",
                recommendation: "Sử dụng đều đặn theo liệu trình 2 lọ để đạt hiệu quả dứt điểm tốt nhất.",
                suggested_products: [],
                quantity: fallbackQty
            };
            
            if (matchingDeal) {
                this.setQuantity(matchingDeal.buy_qty + (matchingDeal.get_qty || 0));
            } else {
                this.setQuantity(fallbackQty);
            }
        } finally {
            this.isAnalyzing = false;
        }
    }
}

// 🚀 ELITE CONTEXT KEYS
const SHOP_KEY = Symbol('SHOP_STORE');

export function setShopStore() {
    return setContext(SHOP_KEY, new ShopStore());
}

export function getShopStore(): ShopStore {
    return getContext(SHOP_KEY);
}
