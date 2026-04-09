import { setContext, getContext } from 'svelte';
import { browser } from '$app/environment';
import type { Product, ProductVariant } from '$lib/types';

export interface CartItem {
    id: string; // Unique ID (product.id + variant.id)
    product: Product;
    variant?: ProductVariant;
    quantity: number;
}

/**
 * ELITE V2.2: Global Multi-Product Cart Store
 * Powered by Svelte 5 Runes with LocalStorage Persistence
 */
export class CartStore {
    // Core State
    items = $state<CartItem[]>([]);
    isOpen = $state<boolean>(false);

    // Bắt sự kiện khởi tạo để load data từ LocalStorage
    constructor() {
        if (browser) {
            const saved = localStorage.getItem('elite_global_cart');
            if (saved) {
                try {
                    this.items = JSON.parse(saved);
                } catch (e) {
                    console.error('Failed to parse cart data', e);
                }
            }
        }
    }

    // Computed State
    totalItems = $derived(this.items.reduce((acc, item) => acc + item.quantity, 0));

    totalAmount = $derived(this.items.reduce((acc, item) => {
        const price = item.variant?.discountPrice ?? item.variant?.price ?? item.product.discountPrice ?? item.product.price ?? 0;
        return acc + (price * item.quantity);
    }, 0));

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
        } else {
            this.items.push({
                id: uniqueId,
                product,
                variant,
                quantity
            });
        }
        this.openCart();
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

    clearCart(): void {
        this.items = [];
    }

    openCart(): void {
        this.isOpen = true;
    }

    closeCart(): void {
        this.isOpen = false;
    }

    toggleCart(): void {
        this.isOpen = !this.isOpen;
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
