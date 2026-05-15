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
    
    private static instance: CartStore | null = null;
    private static cleanup: (() => void) | null = null;

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
                    if (parsed.selectedVoucherIds) {
                        this.selectedVoucherIds = parsed.selectedVoucherIds;
                    }
                } catch (e) {
                    console.error('Failed to parse cart data', e);
                }
            }
        }

        // Auto-save on state change
        if (browser) {
            $effect.root(() => {
                $effect(() => {
                    this.save();
                });
            });
        }
    }

    // Computed State
    totalItems = $derived(this.items.reduce((acc, item) => acc + item.quantity, 0));
    selectedItemsCount = $derived(this.items.filter(item => item.selected).reduce((acc, item) => acc + item.quantity, 0));

    // Discount Mapping
    totalDiscount = $derived.by(() => {
        if (this.selectedVoucherIds.length === 0 || this.vouchers.length === 0) return 0;
        
        let total = 0;
        const subtotal = this.totalAmountWithoutDiscount;

        for (const id of this.selectedVoucherIds) {
            const v = this.vouchers.find(v => v.id === id);
            if (!v) continue;
            
            if (subtotal < (v.min_spend || 0)) continue;

            if (v.type === 'FIXED') {
                total += v.value;
            } else if (v.type === 'PERCENT') {
                total += (subtotal * v.value) / 100;
            }
            // Elite V2.2: Shipping vouchers are EXCLUDED from product subtotal discount.
            // They are handled separately in the checkout layout.
        }
        return total;
    });

    totalAmountWithoutDiscount = $derived.by(() => {
        const selectedItems = this.items.filter(item => item.selected);
        if (selectedItems.length === 0) return 0;

        // Group by product to calculate total quantity per product for tier resolution
        const productStats = new Map<string, { totalQty: number, product: Product }>();
        selectedItems.forEach(item => {
            const stats = productStats.get(item.product.id) || { totalQty: 0, product: item.product };
            stats.totalQty += item.quantity;
            productStats.set(item.product.id, stats);
        });

        let total = 0;
        for (const item of selectedItems) {
            const stats = productStats.get(item.product.id)!;
            const totalQtyForProduct = stats.totalQty;
            
            const effectiveUnitPrice = this.getEffectiveItemPrice(item.id);

            total += (effectiveUnitPrice * item.quantity);
        }
        return total;
    });

    totalAmount = $derived(
        Math.max(0, this.totalAmountWithoutDiscount - this.totalDiscount)
    );

    /**
     * ELITE V5.0: Unified Pricing Breakdown (Ground Truth)
     * This is the authoritative pricing state shared between UI and AI.
     */
    breakdown = $derived.by(() => {
        const subtotal = this.totalAmountWithoutDiscount;
        const voucherDiscount = this.totalDiscount;
        
        // Items with resolved unit prices (Tier/Combo aware)
        const pricingItems = this.items.filter(i => i.selected).map(item => {
            const unitPrice = this.getEffectiveItemPrice(item.id);
            return {
                product_id: item.product.id,
                name: item.product.name,
                quantity: item.quantity,
                unit_price: unitPrice,
                total_price: unitPrice * item.quantity
            };
        });

        // Heuristic combo discount (for reporting)
        // In Elite V2.2, originalSubtotal is the sum of base prices.
        const originalSubtotal = this.items
            .filter(i => i.selected)
            .reduce((acc, item) => acc + ((item.variant?.price ?? item.product.price ?? 0) * item.quantity), 0);
        
        const comboDiscount = Math.max(0, originalSubtotal - subtotal);

        return {
            items: pricingItems,
            subtotal: originalSubtotal,
            combo_discount: comboDiscount,
            voucher_discount: voucherDiscount,
            base_shipping_fee: 0, // Will be updated by Checkout page if needed
            shipping_discount: 0, 
            final_shipping_fee: 0,
            max_point_discount_allowed: subtotal * 0.01,
            points_redeemed: 0,
            point_discount_amount: 0,
            final_payable: this.totalAmount,
            points_to_earn: Math.floor(this.totalAmount / 100000),
            applied_voucher_ids: this.selectedVoucherIds,
            applied_combo_ids: [] // Future extension
        };
    });

    // Side-effects (Persistence)
    save(): void {
        if (browser) {
            localStorage.setItem('elite_global_cart', JSON.stringify({
                items: this.items,
                selectedVoucherIds: this.selectedVoucherIds,
                giftInfo: this.giftInfo
            }));
        }
    }

    // Actions
    setGiftInfo(info: GiftInfo | null): void {
        this.giftInfo = info;
    }

    addItem(product: Product, variant?: ProductVariant, quantity: number = 1, voucherIds?: string[]): void {
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

        // ELITE V7.4: Sync vouchers if provided
        if (voucherIds && voucherIds.length > 0) {
            this.selectedVoucherIds = voucherIds;
        }
        
        this.save();
    }

    updateQuantity(id: string, quantity: number): void {
        if (quantity <= 0) {
            this.removeItem(id);
            return;
        }
        const item = this.items.find(i => i.id === id);
        if (item) {
            item.quantity = quantity;
            this.save();
        }
    }

    /**
     * ELITE V2.2: Tier-Aware Unit Price Resolution
     * Handles both 'combo_qty' and 'comboQty' and 'gifts' metadata.
     */
    getEffectiveItemPrice(itemId: string): number {
        const item = this.items.find(i => i.id === itemId);
        if (!item) return 0;
        
        // Use aggregate product quantity for tier resolution across all selected lines of same product
        const selectedItems = this.items.filter(i => i.selected);
        const totalQtyForProduct = selectedItems
            .filter(i => i.product.id === item.product.id)
            .reduce((acc, i) => acc + i.quantity, 0);
            
        // Elite V2.2: Standardized attribute resolution
        const getQty = (attrs: NonNullable<ProductVariant['attributes']>): number => 
            Number(attrs?.combo_qty ?? attrs?.comboQty ?? 0);

        const comboVariants = item.product?.variants?.filter(v => {
            if (!v.attributes) return false;
            return getQty(v.attributes) > 0;
        }) || [];
        
        if (comboVariants.length > 0) {
            const sortedTiers = [...comboVariants].sort((a, b) => 
                getQty(b.attributes as NonNullable<ProductVariant['attributes']>) - 
                getQty(a.attributes as NonNullable<ProductVariant['attributes']>)
            );
            const bestTier = sortedTiers.find(v => 
                getQty(v.attributes as NonNullable<ProductVariant['attributes']>) <= totalQtyForProduct
            );
            
            const resolvedVariant = bestTier || item.variant || item.product.variants?.[0];
            return resolvedVariant?.discountPrice ?? item.product.discountPrice ?? resolvedVariant?.price ?? item.product.price ?? 0;
        }
        
        return item.variant?.discountPrice ?? item.variant?.price ?? item.product.discountPrice ?? item.product.price ?? 0;
    }

    removeItem(id: string): void {
        this.items = this.items.filter(item => item.id !== id);
        this.save();
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
        this.save();
    }

    toggleGiftModal(open?: boolean): void {
        this.isGiftModalOpen = open ?? !this.isGiftModalOpen;
    }

    buyNow(product: Product, variant?: ProductVariant, quantity: number = 1, voucherIds?: string[]): void {
        // Elite V7.4: Pass vouchers to ensure price syncs with product page
        this.addItem(product, variant, quantity, voucherIds);
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
        this.save();
    }
}

// 🚀 ELITE CONTEXT KEYS
const CART_KEY = Symbol('CART_STORE');

let _globalCartInstance: CartStore | null = null;

export function setCartStore() {
    if (_globalCartInstance) return setContext(CART_KEY, _globalCartInstance);
    _globalCartInstance = new CartStore();
    return setContext(CART_KEY, _globalCartInstance);
}

export function getCartStore(): CartStore {
    return getContext<CartStore>(CART_KEY);
}
