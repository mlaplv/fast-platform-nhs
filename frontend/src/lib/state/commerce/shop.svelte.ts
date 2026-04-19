import { setContext, getContext } from 'svelte';
import { browser } from '$app/environment';
import { apiClient, ApiError } from '$lib/utils/apiClient';
import type { Product, ProductVariant, PromotionDeal, Voucher } from '$lib/types';

/** Domain model for auto-fill state (used by identity shield) */
interface CustomerData {
    nameMasked?: string;
    addressMasked?: string;
    isRecurring: boolean;
    isTrustedDevice: boolean;
}

export interface GiftInfo {
    sender_name: string;
    sender_phone: string;
    message?: string;
    packaging?: string;
    scheduled_at?: string;
    recurring_type?: string;
    recurring_metadata?: { daysOfWeek: number[]; dayOfMonth: number };
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
    error = $state<string | null>(null);
    customerData = $state<CustomerData | null>(null);
    giftInfo = $state<GiftInfo | null>(null);
    isGiftModalOpen = $state<boolean>(false);
    
    // Diagnostic State
    diagnosticResult = $state<DiagnosticReport | null>(null);
    isAnalyzing = $state<boolean>(false);
    
    // Vouchers (Elite V2.2)
    vouchers = $state<Voucher[]>([]);
    selectedVoucherIds = $state<string[]>([]);
    
    // ⚡ Elite V2.2: Mini-Sheet Transient State
    voucherSortOrder = $state<'none' | 'desc' | 'asc'>('none');
    activeOfferTab = $state<Record<number, 'vouchers' | 'gifts'>>({});

    // 🛡️ Elite V2.2: Privacy & Stealth Features
    isStealthMode = $state<boolean>(true); // Default to protected

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
        
        // 🚀 ELITE V2.2: Apply Selected Vouchers
        let discount = 0;
        for (const vId of this.selectedVoucherIds) {
            const v = this.vouchers.find(v => v.id === vId);
            if (!v) continue;
            
            if (v.type === 'FIXED') {
                discount += v.value;
            } else if (v.type === 'PERCENT') {
                discount += (baseTotal * v.value) / 100;
            }
        }
        
        return Math.max(0, baseTotal - discount);
    });

    toggleVoucher(id: string): void {
        const voucher = this.vouchers.find(v => v.id === id);
        if (!voucher) return;

        if (this.selectedVoucherIds.includes(id)) {
            this.selectedVoucherIds = this.selectedVoucherIds.filter(v => v !== id);
        } else {
            // Group-based exclusive selection (Elite V2.2 Standard)
            if (voucher.type === 'SHIPPING') {
                const otherTypes = this.selectedVoucherIds.filter(vId => {
                    const existing = this.vouchers.find(v => v.id === vId);
                    return existing?.type !== 'SHIPPING';
                });
                this.selectedVoucherIds = [...otherTypes, id];
            } else {
                const otherTypes = this.selectedVoucherIds.filter(vId => {
                    const existing = this.vouchers.find(v => v.id === vId);
                    return existing?.type === 'SHIPPING';
                });
                this.selectedVoucherIds = [...otherTypes, id];
            }
        }
    }

    toggleVoucherSort(): void {
        if (this.voucherSortOrder === 'none') this.voucherSortOrder = 'desc';
        else if (this.voucherSortOrder === 'desc') this.voucherSortOrder = 'asc';
        else this.voucherSortOrder = 'none';
    }

    setOfferTab(idx: number, tab: 'vouchers' | 'gifts'): void {
        this.activeOfferTab[idx] = tab;
    }

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

    /** ELITE V2.2: Computed sorting for mini-sheet */
    productVouchers = $derived.by(() => {
        const raw = this.vouchers || [];
        let mapped = raw.map((v: Voucher) => ({
            id: v.id,
            label: v.id || v.title || 'ƯU ĐÃI',
            sub: v.type === 'SHIPPING' ? 'SHIPPING 0Đ' : (v.type === 'PERCENT' ? `${v.value}%` : `${v.value?.toLocaleString()}đ`),
            type: v.type === 'SHIPPING' ? 'ship' : 'discount',
            value: v.value || 0
        }));

        if (this.voucherSortOrder === 'desc') return [...mapped].sort((a, b) => b.value - a.value);
        if (this.voucherSortOrder === 'asc') return [...mapped].sort((a, b) => a.value - b.value);
        return mapped;
    });

    /**
     * ELITE V2.2: Helper to calculate what-if price for any variant with current vouchers
     * Used by Grid to show live price updates on all cards simultaneously.
     */
    calculateAdjustedPrice(v: ProductVariant, q: number = 1, selectedIds: string[] = this.selectedVoucherIds): { final: number, voucherDiscount: number } {
        const basePrice = v.discountPrice || v.price || 0;
        let baseTotal = basePrice * q;
        
        let voucherDiscount = 0;
        for (const vId of selectedIds) {
            const voucher = this.vouchers.find(item => item.id === vId);
            if (!voucher) continue;
            
            if (voucher.type === 'FIXED') {
                voucherDiscount += voucher.value;
            } else if (voucher.type === 'PERCENT') {
                voucherDiscount += (baseTotal * voucher.value) / 100;
            }
        }
        
        return {
            final: Math.max(0, baseTotal - voucherDiscount),
            voucherDiscount
        };
    }

    // 3. Actions
    init(productData: Product): void {
        this.product = productData;
        this.timeLeft = productData.metadata?.scarcity_seconds ?? 1800;
        this.startTimer();
        if (!this.variant && productData?.variants && productData.variants.length > 0) {
            this.variant = productData.variants.length > 1 ? productData.variants[1] : productData.variants[0];
            this.quantity = 1;
        }
        
        if (browser) {
            const saved = localStorage.getItem('elite_shop_gift');
            if (saved) {
                try {
                    this.giftInfo = JSON.parse(saved);
                } catch (e) {
                    console.error('Failed to parse shop gift info', e);
                }
            }
        }
    }

    setVouchers(data: Voucher[]): void {
        this.vouchers = data || [];
        if (this.selectedVoucherIds.length === 0) {
            const shipVoucher = this.vouchers.find(v => v.type === 'SHIPPING');
            if (shipVoucher) {
                this.selectedVoucherIds = [shipVoucher.id];
            }
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
            this.quantity = 1;
        }
    }

    toggleStealthMode(): void {
        this.isStealthMode = !this.isStealthMode;
    }

    setQuantity(q: number): void {
        if (q < 1) return;
        this.quantity = q;
    }

    closeCheckout(): void {
        this.error = null;
        this.giftInfo = null;
        if (browser) localStorage.removeItem('elite_shop_gift');
        this.isGiftModalOpen = false;
    }

    setGiftInfo(info: GiftInfo | null): void {
        this.giftInfo = info;
    }

    toggleGiftModal(open?: boolean): void {
        this.isGiftModalOpen = open ?? !this.isGiftModalOpen;
    }

    syncToStorage = $effect.root(() => {
        $effect(() => {
            if (browser && this.giftInfo) {
                localStorage.setItem('elite_shop_gift', JSON.stringify(this.giftInfo));
            }
        });
    });



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

            const MIN_SCAN_DURATION = 12000;
            const elapsed = Date.now() - startTime;
            if (elapsed < MIN_SCAN_DURATION) {
                await new Promise(resolve => setTimeout(resolve, MIN_SCAN_DURATION - elapsed));
            }

            if (!res) throw new Error('AI analysis returned empty');
            
            this.diagnosticResult = res;
            if (res.quantity) {
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
