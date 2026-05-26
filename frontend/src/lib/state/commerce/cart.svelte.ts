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
            this.setVouchers([]);
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
    get totalItems() {
        return this.items.reduce((acc, item) => acc + (Number(item.quantity) || 0), 0);
    }

    get selectedItemsCount() {
        return this.items.filter(item => item.selected).reduce((acc, item) => acc + (Number(item.quantity) || 0), 0);
    }

    // Discount Mapping
    totalDiscount = $derived.by(() => {
        if (this.selectedVoucherIds.length === 0 || this.vouchers.length === 0) return 0;
        
        let total = 0;
        for (const id of this.selectedVoucherIds) {
            const v = this.vouchers.find(v => v.id === id);
            if (!v) continue;
            
            if (!this.isVoucherEligible(v)) continue;

            const targetSubtotal = this.getEligibleSubtotal(v);

            if (v.type === 'FIXED') {
                total += Math.min(v.value, targetSubtotal);
            } else if (v.type === 'PERCENT') {
                const discount = (targetSubtotal * v.value) / 100;
                total += v.max_discount ? Math.min(discount, v.max_discount) : discount;
            }
            // Elite V2.2: Shipping vouchers are EXCLUDED from product subtotal discount.
            // They are handled separately in the checkout layout.
        }
        return total;
    });

    getEligibleSubtotal(v: Voucher): number {
        const applicableIds = v.metadata_json?.applicable_product_ids || [];
        if (!applicableIds || applicableIds.length === 0) {
            return this.totalAmountWithoutDiscount;
        }

        let eligibleSubtotal = 0;
        for (const item of this.items) {
            if (item.selected) {
                const pId = item.product.id;
                const pSlug = item.product.slug;
                if (applicableIds.includes(pId) || applicableIds.includes(pSlug)) {
                    eligibleSubtotal += this.getEffectiveItemPrice(item.id) * item.quantity;
                }
            }
        }
        return eligibleSubtotal;
    }

    isVoucherEligible(v: Voucher): boolean {
        const applicableIds = v.metadata_json?.applicable_product_ids || [];
        let targetSubtotal = this.totalAmountWithoutDiscount;

        if (applicableIds && applicableIds.length > 0) {
            targetSubtotal = 0;
            let hasApplicableItem = false;
            for (const item of this.items) {
                if (item.selected) {
                    const pId = item.product.id;
                    const pSlug = item.product.slug;
                    if (applicableIds.includes(pId) || applicableIds.includes(pSlug)) {
                        hasApplicableItem = true;
                        targetSubtotal += this.getEffectiveItemPrice(item.id) * item.quantity;
                    }
                }
            }
            if (!hasApplicableItem) return false;
        }

        return targetSubtotal >= (v.min_spend || 0);
    }


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
            .reduce((acc, item) => acc + ((Number(item.variant?.price) || Number(item.product.price) || 0) * item.quantity), 0);
        
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
            this.items = [...this.items];
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
            this.items = [...this.items];
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
            return Number(resolvedVariant?.discountPrice) || Number(item.product.discountPrice) || Number(resolvedVariant?.price) || Number(item.product.price) || 0;
        }
        
        return Number(item.variant?.discountPrice) || Number(item.variant?.price) || Number(item.product.discountPrice) || Number(item.product.price) || 0;
    }

    /**
     * ELITE V2.2: Retrieve the resolved active variant based on combo quantity levels
     */
    getEffectiveVariant(itemId: string): ProductVariant | undefined {
        const item = this.items.find(i => i.id === itemId);
        if (!item) return undefined;

        const selectedItems = this.items.filter(i => i.selected);
        const totalQtyForProduct = selectedItems
            .filter(i => i.product.id === item.product.id)
            .reduce((acc, i) => acc + i.quantity, 0);

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

            return bestTier || item.variant || item.product.variants?.[0];
        }

        return item.variant || item.product.variants?.[0];
    }

    /**
     * ELITE V2.2: Resolve human-readable variant option name from tier_index and tier_variations
     */
    getVariantName(product: Product, variant?: ProductVariant): string {
        if (!variant) return '';

        const tierIndex = variant.tier_index ?? variant.tierIndex;
        const tierVariations = product.tier_variations ?? product.tierVariations;

        if (tierIndex && tierVariations && tierIndex.length > 0) {
            const names: string[] = [];
            tierIndex.forEach((tIdx, i) => {
                const tier = tierVariations[i];
                if (tier && tier.options && tIdx < tier.options.length) {
                    names.push(String(tier.options[tIdx]));
                }
            });
            if (names.length > 0) return names.join(' - ');
        }

        return variant.sku || '';
    }

    removeItem(id: string): void {
        this.items = this.items.filter(item => item.id !== id);
        this.save();
    }

    toggleItemSelection(id: string): void {
        const item = this.items.find(i => i.id === id);
        if (item) {
            item.selected = !item.selected;
            this.items = [...this.items];
        }
    }

    toggleAll(selected: boolean): void {
        this.items.forEach(item => item.selected = selected);
        this.items = [...this.items];
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

    loadUnlockedViralVouchers(): Voucher[] {
        if (!browser) return [];
        const viralVouchersMap = new Map<string, { voucher: Voucher, productIds: Set<string | number> }>();
        try {
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key && key.startsWith('viral_unlocked_')) {
                    const productId = key.replace('viral_unlocked_', '');
                    const saved = localStorage.getItem(key);
                    if (saved) {
                        const parsed = JSON.parse(saved);
                        if (parsed && parsed.code) {
                            const code = parsed.code;
                            const existing = viralVouchersMap.get(code);
                            
                            const pIds = existing ? existing.productIds : new Set<string | number>();
                            if (productId) {
                                pIds.add(String(productId));
                                if (!isNaN(Number(productId))) {
                                    pIds.add(Number(productId));
                                }
                            }
                            
                            const v: Voucher = {
                                id: code,
                                title: parsed.label || 'Voucher Đặc Quyền',
                                desc: 'Mã lan tỏa đã mở khóa',
                                type: parsed.type || 'FIXED',
                                value: parsed.value || 0,
                                min_spend: parsed.min_spend || 0,
                                category: 'DISCOUNT',
                                is_default: false,
                                priority: 1000,
                                is_viral: true,
                                metadata_json: {
                                    applicable_product_ids: []
                                }
                            } as unknown as Voucher;
                            
                            viralVouchersMap.set(code, { voucher: v, productIds: pIds });
                        }
                    }
                }
            }
            
            const result: Voucher[] = [];
            for (const entry of viralVouchersMap.values()) {
                entry.voucher.metadata_json = {
                    applicable_product_ids: Array.from(entry.productIds)
                };
                result.push(entry.voucher);
            }
            return result;
        } catch (e) {
            console.error('Failed to load unlocked viral vouchers from localStorage', e);
        }
        return [];
    }

    setVouchers(data: Voucher[]): void {
        const baseVouchers = data || [];
        const unlockedViral = this.loadUnlockedViralVouchers();
        
        // Dedup: prioritize the unlocked viral vouchers
        const allVouchers = [...unlockedViral];
        for (const v of baseVouchers) {
            if (!allVouchers.some(x => x.id === v.id)) {
                allVouchers.push(v);
            }
        }
        
        this.vouchers = allVouchers;
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

    /**
     * ELITE V2.2: Unified Promotion & Gift Advice Engine
     * Dynamically resolved from Variant/Product metadata and attributes.
     */
    getPromotionAdvice(product: Product, currentQty: number) {
        if (!product) {
            return { text: '', hasGift: false, nextTier: null, nextComboName: '', gap: 0 };
        }

        const getQty = (attrs: any): number => Number(attrs?.combo_qty ?? attrs?.comboQty ?? 0);
        
        const comboVariants = product.variants?.filter(v => {
            if (!v.attributes) return false;
            return getQty(v.attributes) > 0;
        }) || [];

        if (comboVariants.length === 0) {
            return {
                text: "Cơ hội sở hữu liệu trình chuyên sâu với ưu đãi độc quyền. Hãy chọn số lượng phù hợp để tối ưu kết quả.",
                hasGift: false,
                nextTier: null,
                nextComboName: '',
                gap: 0
            };
        }

        const sortedTiers = [...comboVariants].sort((a, b) => 
            getQty(a.attributes) - getQty(b.attributes)
        );

        // Find currently reached tier
        const reachedTier = [...sortedTiers]
            .reverse()
            .find(t => getQty(t.attributes) <= currentQty);

        // Find next tier
        const nextTier = sortedTiers.find(t => getQty(t.attributes) > currentQty);

        if (!nextTier) {
            const currentGifts = reachedTier?.attributes?.gifts?.length 
                ? reachedTier.attributes.gifts 
                : reachedTier?.gifts?.length 
                    ? reachedTier.gifts 
                    : [];
            
            return {
                text: "Chúc mừng bạn! Bạn đã đạt hạng combo ưu đãi cao nhất và nhận được mức giá tốt nhất cùng quà tặng độc quyền!",
                hasGift: currentGifts.length > 0,
                nextTier: null,
                nextComboName: '',
                gap: 0
            };
        }

        const gap = nextTier.attributes ? (getQty(nextTier.attributes) - currentQty) : 0;
        const nextComboName = this.getVariantName(product, nextTier);

        // Check gifts on next tier variant
        const gifts = nextTier.attributes?.gifts?.length 
            ? nextTier.attributes.gifts 
            : nextTier.gifts?.length 
                ? nextTier.gifts 
                : [];
        
        const hasGift = gifts.length > 0;

        // Calculate saving/discount
        const currentUnitPrice = reachedTier 
            ? (Number(reachedTier.discountPrice) || Number(reachedTier.price) || 0)
            : (Number(product.discountPrice) || Number(product.price) || 0);

        const nextUnitPrice = Number(nextTier.discountPrice) || Number(nextTier.price) || 0;
        const savingsPerUnit = Math.max(0, currentUnitPrice - nextUnitPrice);

        const benefitParts: string[] = [];
        if (savingsPerUnit > 0) {
            benefitParts.push(`tiết kiệm thêm ${savingsPerUnit.toLocaleString('vi-VN')}đ/sản phẩm`);
        }

        if (hasGift) {
            const giftStrings = gifts.map((g: any) => {
                const gQty = g.qty || g.quantity || 1;
                return `${gQty} ${g.name}`;
            });
            benefitParts.push(`tặng thêm ${giftStrings.join(', ')} MIỄN PHÍ`);
        }

        let text = `Thêm ${gap} sp ${product.name} để thăng hạng lên combo "${nextComboName}".`;
        if (benefitParts.length > 0) {
            text += ` Nhận ngay ưu đãi ${benefitParts.join(" và ")}!`;
        } else {
            text += ` Hãy thăng hạng để nhận thêm ưu đãi đặc quyền!`;
        }

        return {
            text,
            hasGift,
            nextTier,
            nextComboName,
            gap
        };
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
    const store = getContext<CartStore>(CART_KEY);
    if (store) return store;
    
    // Elite V2.2: Singleton Fallback (Safety Net)
    if (_globalCartInstance) return _globalCartInstance;
    _globalCartInstance = new CartStore();
    return _globalCartInstance;
}
