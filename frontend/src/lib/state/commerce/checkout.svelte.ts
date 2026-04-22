/**
 * ELITE V2.2: Global Checkout Synchronization Store
 * Synchronizes real-time pricing breakdown between the Checkout UI and Helen AI.
 */

export interface CheckoutBreakdown {
    subtotal: number;
    combo_discount: number;
    voucher_discount: number;
    shipping_fee: number;
    total_amount: number;
    points_redeemed: number;
    point_discount: number;
    shipping_discount: number;
    final_total: number;
    applied_vouchers?: { id: string, name: string, type: string }[];
}

class CheckoutState {
    /** 
     * The current ground truth pricing breakdown. 
     * Null if not on the checkout page or data not yet initialized.
     */
    breakdown = $state<CheckoutBreakdown | null>(null);
    
    /** Resets the state when leaving checkout */
    reset() {
        this.breakdown = null;
    }
}

export const checkoutState = new CheckoutState();
