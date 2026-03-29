import { apiClient, ApiError } from '$lib/utils/apiClient';
import type { Product, ProductVariant } from '$lib/types';
import type { GenericResponse } from '$lib/state/types';

/**
 * ELITE V2.2: Nanobot Store for Funnel Shop
 * Handles cart state, order bump, and checkout flow.
 */
class ShopStore {
    // 1. Core State ($state)
    product = $state<Product | null>(null);
    variant = $state<ProductVariant | null>(null);
    quantity = $state<number>(1);
    hasOrderBump = $state<boolean>(false);

    // UI State
    isCheckoutOpen = $state<boolean>(false);
    isSubmitting = $state<boolean>(false);
    orderSuccess = $state<boolean>(false);
    error = $state<string | null>(null);

    // 2. Computed State ($derived)
    totalAmount = $derived.by((): number => {
        const basePrice = this.currentPrice;
        // Gỡ bỏ hardcode: Lấy giá order bump từ metadata sản phẩm (mặc định 0 nếu không có)
        const orderBumpPrice = this.hasOrderBump ? (this.product?.metadata?.order_bump_price || 0) : 0;
        return (basePrice * this.quantity) + orderBumpPrice;
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
        // Mặc định chọn variant đầu tiên nếu có
        if (productData?.variants && productData.variants.length > 0) {
            this.variant = productData.variants[0];
        }
    }

    /**
     * Đồng bộ với MobileBottomSheet: Thêm vào giỏ hàng và mở Checkout
     */
    addItem(productData: Product): void {
        this.init(productData);
        this.openCheckout();
    }

    selectVariant(v: ProductVariant): void {
        this.variant = v;
    }

    selectVariantByTier(indices: number[]): void {
        if (!this.product?.variants) return;
        const found = this.product.variants.find(v => 
            v.tierIndex.length === indices.length && 
            v.tierIndex.every((val, idx) => val === indices[idx])
        );
        if (found) {
            this.variant = found;
        }
    }

    setQuantity(q: number): void {
        if (q < 1) return;
        this.quantity = q;
    }

    toggleOrderBump(): void {
        this.hasOrderBump = !this.hasOrderBump;
    }

    openCheckout(): void {
        this.isCheckoutOpen = true;
    }

    closeCheckout(): void {
        this.isCheckoutOpen = false;
        this.orderSuccess = false;
        this.error = null;
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
                has_order_bump: this.hasOrderBump,
                quantity: this.quantity
            });

            if (res.ok || res.status === 'success') {
                this.orderSuccess = true;
                // Auto-close after 3s on success
                setTimeout(() => {
                    this.closeCheckout();
                }, 3000);
            } else {
                this.error = res.message ?? 'Có lỗi xảy ra, vui lòng thử lại';
            }
        } catch (err: unknown) {
            this.error = err instanceof ApiError ? err.message : 'Không thể kết nối máy chủ';
            if (err instanceof Error) {
                console.error('[ShopStore] Checkout Error:', err.message);
            }
        } finally {
            this.isSubmitting = false;
        }
    }
}

// Export singleton
export const shopStore = new ShopStore();
