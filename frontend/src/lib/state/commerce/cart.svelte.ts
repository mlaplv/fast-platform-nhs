import { setContext, getContext } from 'svelte';
import { browser } from '$app/environment';
import type { Product, ProductVariant } from '$lib/types';

export interface CartItem {
    id: string; // Unique ID (product.id + variant.id)
    product: Product;
    variant?: ProductVariant;
    quantity: number;
    selected: boolean;
}

/**
 * ELITE V2.2: Global Multi-Product Cart Store
 * Powered by Svelte 5 Runes with LocalStorage Persistence
 */
export class CartStore {
    // Core State
    items = $state<CartItem[]>([]);
    selectedVoucherIds = $state<string[]>([]);

    // Bắt sự kiện khởi tạo để load data từ LocalStorage
    constructor() {
        if (browser) {
            const saved = localStorage.getItem('elite_global_cart');
            if (saved) {
                try {
                    const parsed = JSON.parse(saved) as Partial<CartItem>[];
                    this.items = parsed
                        .filter((i): i is CartItem => !!(i.id && i.product))
                        .map((item) => ({
                            ...item,
                            selected: item.selected ?? true
                        } as CartItem));
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
        if (this.selectedVoucherIds.length === 0) return 0;
        
        let total = 0;
        for (const id of this.selectedVoucherIds) {
            if (id === 'SALE30K' && this.totalAmountWithoutDiscount >= 150000) total += 30000;
            if (id === 'SALE60K' && this.totalAmountWithoutDiscount >= 300000) total += 60000;
            // SHIPPING vouchers currently handle 0 discount here as they act on shipping fee in UI
        }
        return total;
    });

    totalAmountWithoutDiscount = $derived(
        this.items.filter(item => item.selected).reduce((acc, item) => {
            const price = item.variant?.discountPrice ?? item.variant?.price ?? item.product.discountPrice ?? item.product.price ?? 0;
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
                localStorage.setItem('elite_global_cart', JSON.stringify(this.items));
            }
        });
    });

    // Actions
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
    }

    buyNow(product: Product, variant?: ProductVariant, quantity: number = 1): void {
        // Elite V2.2 Cumulative: Add to selection instead of isolating
        this.addItem(product, variant, quantity);
        // addItem handles finding/updating and setting selected = true
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
