import { browser } from '$app/environment';
import type { Product, ProductVariant, Voucher } from '$lib/types';
import { getContext, setContext } from 'svelte';

export interface CartItem {
    id: string; // Unique ID (product.id + variant.id)
    product: Product;
    variant?: ProductVariant;
    quantity: number;
    selected: boolean;
}

export interface GiftInfo {
    sender_name: string;
    sender_phone: string;
    message?: string;
    packaging?: string;
    scheduled_at?: string;
    recurring_type?: string;
    recurring_metadata?: Record<string, unknown>;
}

/**
 * ELITE V2.2: Global Multi-Product Cart Store
 * Powered by Svelte 5 Runes with LocalStorage Persistence
 */
export class CartStore {
    // Core State
    items = $state<CartItem[]>([]);
    vouchers = $state<Voucher[]>([]);
    selectedVoucherIds = $state<string[]>([]);
    giftInfo = $state<GiftInfo | null>(null);
    isGiftModalOpen = $state<boolean>(false);

    // Bắt sự kiện khởi tạo để load data từ LocalStorage
    constructor() {
        if (browser) {
            const saved = localStorage.getItem('elite_global_cart');
            if (saved) {
                try {
                    const parsed = JSON.parse(saved) as { items?: Partial<CartItem>[], giftInfo?: GiftInfo };
                    if (parsed.items) {
                        this.items = (parsed.items)
                            .filter((i): i is CartItem => !!(i.id && i.product))
                            .map((item) => ({
                                ...item,
                                selected: item.selected ?? true
                            } as CartItem));
                    }
                    if (parsed.giftInfo) {
                        this.giftInfo = parsed.giftInfo;
                    }
                } catch (e) {
                    console.error('Failed to parse cart data', e);
                }
            }
        }
    }

    // Computed State
    totalItems = $derived(this.items.reduce((acc, item) => acc + item.quantity, 0));
    selectedItemsCount = $derived(this.items.filter(item => item.selected).reduce((acc, item) => acc + item.quantity, 0));

    // Discount Mapping
    totalDiscount = $derived.by(() => {
        if (this.selectedVoucherIds.length === 0 || this.vouchers.length === 0) return 0;
        
        let total = 0;
        for (const id of this.selectedVoucherIds) {
            const v = this.vouchers.find(v => v.id === id);
            if (!v) continue;
            
            if (v.type === 'FIXED' && this.totalAmountWithoutDiscount >= (v.min_spend || 0)) {
                total += v.value;
            } else if (v.type === 'PERCENT' && this.totalAmountWithoutDiscount >= (v.min_spend || 0)) {
                total += (this.totalAmountWithoutDiscount * v.value) / 100;
            }
        }
        return total;
    });

    totalAmountWithoutDiscount = $derived(
        this.items.filter(item => item.selected).reduce((acc, item) => {
            const price = item.variant?.discountPrice ?? item.variant?.price ?? item.product.discountPrice ?? item.product.price ?? 0;
            const deals = item.product?.metadata?.active_deals as import('$lib/types').PromotionDeal[] | undefined;
            if (deals && deals.length > 0) {
                const sortedDeals = [...deals].sort((a, b) => (b.buy_qty + (b.get_qty || 0)) - (a.buy_qty + (a.get_qty || 0)));
                for (const deal of sortedDeals) {
                    const totalInBundle = deal.buy_qty + (deal.get_qty || 0);
                    if (item.quantity >= totalInBundle) {
                        const bundleCount = Math.floor(item.quantity / totalInBundle);
                        const remainder = item.quantity % totalInBundle;
                        return acc + ((bundleCount * deal.fixed_price) + (remainder * price));
                    }
                }
            }
            return acc + (price * item.quantity);
        }, 0)
    );

    totalAmount = $derived(
        Math.max(0, this.totalAmountWithoutDiscount - this.totalDiscount)
    );

    // Side-effects (Persistence)
    syncToStorage = $effect.root(() => {
        $effect(() => {
            if (browser) {
                localStorage.setItem('elite_global_cart', JSON.stringify({
                    items: this.items,
                    giftInfo: this.giftInfo
                }));
            }
        });
    });

    // Actions
    setGiftInfo(info: GiftInfo | null): void {
        this.giftInfo = info;
    }

    addItem(product: Product, variant?: ProductVariant, quantity: number = 1): void {
        const uniqueId = variant ? `${product.id}_${variant.id}` : product.id;
        const existingItem = this.items.find(item => item.id === uniqueId);

        if (existingItem) {
            existingItem.quantity += quantity;
            existingItem.selected = true; // Auto select when adding
        } else {
            this.items.push({
                id: uniqueId,
                product,
                variant,
                quantity,
                selected: true
            });
        }
    }

    updateQuantity(id: string, quantity: number): void {
        if (quantity <= 0) {
            this.removeItem(id);
            return;
        }
        const item = this.items.find(i => i.id === id);
        if (item) item.quantity = quantity;
    }

    removeItem(id: string): void {
        this.items = this.items.filter(item => item.id !== id);
    }

    toggleItemSelection(id: string): void {
        const item = this.items.find(i => i.id === id);
        if (item) item.selected = !item.selected;
    }

    toggleAll(selected: boolean): void {
        this.items.forEach(item => item.selected = selected);
    }

    clearCart(): void {
        this.items = [];
        this.giftInfo = null;
        this.isGiftModalOpen = false;
    }

    toggleGiftModal(open?: boolean): void {
        this.isGiftModalOpen = open ?? !this.isGiftModalOpen;
    }

    buyNow(product: Product, variant?: ProductVariant, quantity: number = 1): void {
        // Elite V2.2 Cumulative: Add to selection instead of isolating
        this.addItem(product, variant, quantity);
        // addItem handles finding/updating and setting selected = true
    }

    setVouchers(data: Voucher[]): void {
        this.vouchers = data || [];
    }

    toggleVoucher(id: string): void {
        const voucher = this.vouchers.find(v => v.id === id);
        if (!voucher) return;

        if (this.selectedVoucherIds.includes(id)) {
            this.selectedVoucherIds = this.selectedVoucherIds.filter(v => v !== id);
        } else {
            // 🛡️ Elite V2.2: Exclusive Selection Logic (1 Ship + 1 Discount)
            if (voucher.type === 'SHIPPING') {
                const others = this.selectedVoucherIds.filter(vId => {
                    const v = this.vouchers.find(v => v.id === vId);
                    return v?.type !== 'SHIPPING';
                });
                this.selectedVoucherIds = [...others, id];
            } else {
                const others = this.selectedVoucherIds.filter(vId => {
                    const v = this.vouchers.find(v => v.id === vId);
                    return v?.type === 'SHIPPING';
                });
                this.selectedVoucherIds = [...others, id];
            }
        }
    }
}

// 🚀 ELITE CONTEXT KEYS
const CART_KEY = Symbol('CART_STORE');

export function setCartStore() {
    return setContext(CART_KEY, new CartStore());
}

export function getCartStore(): CartStore {
    return getContext<CartStore>(CART_KEY);
}
