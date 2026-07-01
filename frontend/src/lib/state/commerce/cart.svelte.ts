import { browser } from '$app/environment';
import type { Product, ProductVariant, Voucher } from '$lib/types';
import { getContext, setContext, untrack } from 'svelte';
import { authStore } from '../authStore.svelte';

export interface CartItem {
    id: string; // Unique ID: product.id + tier_index signature (e.g. "prod_abc_0,1")
    product: Product;
    classification?: { tier_index: number[] }; // The user's chosen option (e.g. [0] = "Dứt điểm")
    variant?: ProductVariant; // Kept for compatibility — NOT used as the cart key
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
    epoch = $state<number>(0);
    
    // Performance Lookup Indexes (Elite V2.2)
    voucherIndexMap = new Map<string, Voucher>();
    private cachedUnlockedViralVouchers: Voucher[] | null = null;
    
    private static instance: CartStore | null = null;
    private static cleanup: (() => void) | null = null;

    get storageKey() {
        const userId = authStore.user?.id;
        return userId ? `osmo:storefront:${userId}:cart` : 'osmo:storefront:guest:cart';
    }

    // Bắt sự kiện khởi tạo để load data từ LocalStorage
    constructor() {
        if (browser) {
            $effect.root(() => {
                $effect(() => {
                    // Watch authStore.user?.id to reactively reload the cart on login/logout
                    const _ = authStore.user?.id;
                    this.cachedUnlockedViralVouchers = null; // Reset performance cache on auth state change
                    this.loadFromStorage();
                });

                $effect(() => {
                    // Watch cart items, selectedVoucherIds, giftInfo to auto-save to the current storageKey
                    const key = this.storageKey;
                    const dataToSave = {
                        items: this.items,
                        selectedVoucherIds: this.selectedVoucherIds,
                        giftInfo: this.giftInfo
                    };
                    localStorage.setItem(key, JSON.stringify(dataToSave));
                    untrack(() => {
                        this.epoch++;
                    });
                });
            });
        }
    }

    loadFromStorage(): void {
        if (!browser) return;
        const key = this.storageKey;
        const saved = localStorage.getItem(key);
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                if (parsed.items) {
                    const rawItems = (parsed.items as Partial<CartItem>[] || [])
                        .filter((i): i is CartItem => !!(i?.id && i?.product));

                    // ELITE V3.0: One-time migration from old variant.id-keyed IDs to tier_index-keyed IDs.
                    // Old format: "product_id_variant_uuid" → New: "product_id_0,1"
                    const mergedMap = new Map<string, CartItem>();
                    for (const raw of rawItems) {
                        const migratedItem: CartItem = { ...raw, selected: raw.selected ?? true };

                        // Rebuild correct classification and id to align with current logic
                        const idx = this.getClassificationIndex(migratedItem.product, migratedItem.variant);
                        migratedItem.classification = idx.length > 0 ? { tier_index: idx } : undefined;
                        migratedItem.id = this.getUniqueId(migratedItem.product, migratedItem.variant);

                        // Merge duplicate rows that map to the same new id
                        const existing = mergedMap.get(migratedItem.id);
                        if (existing) {
                            existing.quantity += migratedItem.quantity;
                        } else {
                            mergedMap.set(migratedItem.id, migratedItem);
                        }
                    }
                    this.items = Array.from(mergedMap.values());
                } else {
                    this.items = [];
                }
                this.giftInfo = parsed.giftInfo || null;
                this.selectedVoucherIds = parsed.selectedVoucherIds || [];
            } catch (e) {
                console.error('Failed to parse cart data', e);
            }
        } else {
            // Migrating legacy global key if available and no user-specific key exists
            const legacyKey = 'elite_global_cart';
            const legacySaved = localStorage.getItem(legacyKey);
            if (legacySaved) {
                try {
                    const parsed = JSON.parse(legacySaved);
                    if (parsed.items) {
                        this.items = (parsed.items as Partial<CartItem>[])
                            .filter((i): i is CartItem => !!(i?.id && i?.product))
                            .map((item) => ({
                                ...item,
                                selected: item.selected ?? true
                            } as CartItem));
                    }
                    this.giftInfo = parsed.giftInfo || null;
                    this.selectedVoucherIds = parsed.selectedVoucherIds || [];
                    localStorage.removeItem(legacyKey);
                } catch (e) {
                    console.error('Failed to parse legacy cart data', e);
                }
            } else {
                this.items = [];
                this.giftInfo = null;
                this.selectedVoucherIds = [];
            }
        }
        // Elite V2.2: Vouchers are NOT loaded from storage.
        // They are sourced exclusively from the layout API via cart.setVouchers(data.vouchers).
        // DO NOT call setVouchers here — it would wipe API-loaded vouchers on auth state changes.
    }

    /**
     * Helper to identify which dimensions in the product's tier_index are combo/quantity dimensions.
     * Dimensions are classified as combo dimensions if:
     * 1. Their name/label in tier_variations contains keywords like "combo", "khuyến mãi", "số lượng".
     * 2. Or if varying that dimension changes the combo_qty attribute of the variants.
     */
    private getComboDimensions(product: Product): Set<number> {
        const comboDims = new Set<number>();
        const variants = product.variants || [];
        
        // 1. Semantic check of tier names
        const comboKeywords = ['combo', 'khuyến mãi', 'khuyen mai', 'số lượng', 'so luong', 'quà tặng', 'qua tang'];
        const tierVariations = product.tier_variations ?? product.tierVariations ?? [];
        tierVariations.forEach((tier, d) => {
            const nameLower = String(tier.name || '').toLowerCase();
            if (comboKeywords.some(kw => nameLower.includes(kw))) {
                comboDims.add(d);
            }
        });

        if (variants.length <= 1) return comboDims;

        const getQty = (v: ProductVariant) => Number(v.attributes?.combo_qty ?? v.attributes?.comboQty ?? 1);

        // Find max tier_index length
        let maxLen = 0;
        for (const v of variants) {
            const vi = v.tier_index ?? v.tierIndex;
            if (Array.isArray(vi) && vi.length > maxLen) {
                maxLen = vi.length;
            }
        }

        // 2. Attribute-based check: find dimensions where combo_qty varies
        for (let d = 0; d < maxLen; d++) {
            for (let i = 0; i < variants.length; i++) {
                for (let j = i + 1; j < variants.length; j++) {
                    const v1 = variants[i];
                    const v2 = variants[j];
                    const vi1 = v1.tier_index ?? v1.tierIndex;
                    const vi2 = v2.tier_index ?? v2.tierIndex;

                    if (!Array.isArray(vi1) || !Array.isArray(vi2)) continue;
                    if (vi1.length !== vi2.length) continue;

                    let diffCount = 0;
                    let onlyDiffAtD = true;
                    for (let k = 0; k < vi1.length; k++) {
                        if (vi1[k] !== vi2[k]) {
                            diffCount++;
                            if (k !== d) {
                                onlyDiffAtD = false;
                                break;
                            }
                        }
                    }

                    if (diffCount === 1 && onlyDiffAtD) {
                        if (getQty(v1) !== getQty(v2)) {
                            comboDims.add(d);
                            break;
                        }
                    }
                }
                if (comboDims.has(d)) break;
            }
        }

        return comboDims;
    }

    /**
     * Get the classification signature of a variant (returns original tier_index number array).
     */
    private getClassificationIndex(product: Product, variant?: ProductVariant): number[] {
        const idx = variant?.tier_index ?? variant?.tierIndex;
        if (!Array.isArray(idx)) return [];
        return idx;
    }

    /**
     * ELITE V3.0: Canonical Cart Item ID.
     * Key = product.id + tier_index of chosen classification, where combo dimensions are replaced by '_'.
     * E.g. "prod_abc_0,_" or "prod_abc__" if all dimensions are combo/quantity tiers.
     * This guarantees that items of the same core classification merge into a single row.
     */
    private getUniqueId(product: Product, variant?: ProductVariant): string {
        const idx = this.getClassificationIndex(product, variant);
        if (idx.length > 0) {
            const comboDims = this.getComboDimensions(product);
            return `${product.id}_${idx.map((v, d) => comboDims.has(d) ? '_' : v).join(',')}`;
        }
        return product.id;
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
            const v = this.voucherIndexMap.get(id);
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
            localStorage.setItem(this.storageKey, JSON.stringify({
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
        // ELITE V3.0: ID based on tier_index classification, NOT variant.id.
        // This guarantees same-classification items (combo or single) always merge into one row.
        const uniqueId = this.getUniqueId(product, variant);
        const existingItem = this.items.find(item => item.id === uniqueId);

        const tierIndex = this.getClassificationIndex(product, variant);

        if (existingItem) {
            existingItem.quantity += quantity;
            existingItem.selected = true;
            // Update variant reference to latest selection (for gift/attributes metadata lookup)
            if (variant) existingItem.variant = variant;
            this.items = [...this.items];
        } else {
            this.items.push({
                id: uniqueId,
                product,
                classification: tierIndex.length > 0
                    ? { tier_index: tierIndex }
                    : undefined,
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
        
        const resolvedVariant = this.getEffectiveVariant(itemId);
        return Number(resolvedVariant?.discountPrice) || Number(item.product.discountPrice) || Number(resolvedVariant?.price) || Number(item.product.price) || 0;
    }

    /**
     * ELITE V3.0: Tier-Aware Variant Resolution.
     * Uses classification.tier_index to scope variants to the user's chosen option group,
     * then selects the best combo tier based on total quantity in the cart.
     */
    getEffectiveVariant(itemId: string): ProductVariant | undefined {
        const item = this.items.find(i => i.id === itemId);
        if (!item) return undefined;

        // Total quantity for THIS specific item row (not all variants of the same product)
        const totalQty = item.quantity;

        const getQty = (v: ProductVariant): number =>
            Number(v.attributes?.combo_qty ?? v.attributes?.comboQty ?? 1);

        const allVariants = item.product?.variants?.filter(v => v.is_active !== false) || [];

        // --- 1. Scope to classification (tier_index) ---
        // classification.tier_index identifies the user's chosen option, ignoring combo dimensions
        const classIdx = item.classification?.tier_index
            ?? this.getClassificationIndex(item.product, item.variant);

        let candidates: ProductVariant[];
        if (Array.isArray(classIdx) && classIdx.length > 0) {
            const comboDims = this.getComboDimensions(item.product);
            // Filter variants that match the classification dimensions, ignoring combo dimensions
            candidates = allVariants.filter(v => {
                const vi = v.tier_index ?? v.tierIndex;
                if (!Array.isArray(vi)) return false;
                return classIdx.every((val, i) => comboDims.has(i) || vi[i] === val);
            });
        } else {
            candidates = allVariants;
        }

        if (candidates.length === 0) {
            return item.variant ?? allVariants[0];
        }

        // --- 2. Find the best eligible combo tier within scoped candidates ---
        const sorted = [...candidates].sort((a, b) => getQty(b) - getQty(a));
        const eligible = sorted.filter(v => getQty(v) <= totalQty);

        if (eligible.length > 0) return eligible[0];

        // Fallback: return the base (smallest qty) variant in the classification
        return sorted[sorted.length - 1] ?? item.variant;
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
        // ELITE V3.0: "Mua Ngay" semantics.
        // Clear the cart only if the existing items in the cart are for a DIFFERENT product.
        // If it's the same product, we keep the items to allow automatic quantity merging.
        const hasDifferentProduct = this.items.some(item => item.product.id !== product.id);
        if (hasDifferentProduct) {
            this.items = [];
        }
        this.addItem(product, variant, quantity, voucherIds);
    }

    loadUnlockedViralVouchers(): Voucher[] {
        if (!browser) return [];
        if (this.cachedUnlockedViralVouchers !== null) {
            return this.cachedUnlockedViralVouchers;
        }

        const viralVouchersMap = new Map<string, { voucher: Voucher, productIds: Set<string | number> }>();
        try {
            const userId = authStore.user?.id;
            if (!userId) return []; // CẤM nạp voucher khi chưa đăng nhập!

            const prefix = `viral_unlocked_${userId}_`;
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key && key.startsWith(prefix)) {
                    const productId = key.replace(prefix, '');
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
            this.cachedUnlockedViralVouchers = result;
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

        // Build performance lookup index map
        this.voucherIndexMap.clear();
        for (const v of allVouchers) {
            this.voucherIndexMap.set(v.id, v);
        }
    }

    toggleVoucher(id: string): void {
        const voucher = this.voucherIndexMap.get(id);
        if (!voucher) return;

        if (this.selectedVoucherIds.includes(id)) {
            this.selectedVoucherIds = this.selectedVoucherIds.filter(v => v !== id);
        } else {
            // 🛡️ Elite V2.2: Exclusive Selection Logic (1 Ship + 1 Discount)
            if (voucher.type === 'SHIPPING') {
                const others = this.selectedVoucherIds.filter(vId => {
                    const v = this.voucherIndexMap.get(vId);
                    return v?.type !== 'SHIPPING';
                });
                this.selectedVoucherIds = [...others, id];
            } else {
                const others = this.selectedVoucherIds.filter(vId => {
                    const v = this.voucherIndexMap.get(vId);
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

        const getQty = (attrs: ProductVariant['attributes']): number => Number(attrs?.combo_qty ?? attrs?.comboQty ?? 0);
        
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
            const giftStrings = gifts.map((g: { name: string; qty?: number; quantity?: number }) => {
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
    try {
        const store = getContext<CartStore>(CART_KEY);
        if (store) return store;
    } catch (e) {}
    
    // Elite V2.2: Singleton Fallback (Safety Net)
    if (_globalCartInstance) return _globalCartInstance;
    _globalCartInstance = new CartStore();
    return _globalCartInstance;
}

export function getGlobalCart(): CartStore {
    if (!_globalCartInstance) {
        _globalCartInstance = new CartStore();
    }
    return _globalCartInstance;
}
