import { authStore } from '../authStore.svelte';
import { apiClient } from '$lib/utils/apiClient';
import { LOYALTY_TIERS } from '$lib/config/commerce';

export interface PointTransaction {
    id: string;
    amount: number;
    transaction_type: string;
    status: string;
    notes?: string;
    created_at: string;
}

export interface LoyaltyData {
    tier: string;
    available_points: number;
    pending_points: number;
    total_spent: number;
    tier_updated_at?: string;
    history: PointTransaction[];
}

class LoyaltyStore {
    data = $state<LoyaltyData | null>(null);
    loading = $state(false);
    error = $state<string | null>(null);

    async fetchLoyalty() {
        if (!authStore.user) return;
        
        this.loading = true;
        this.error = null;
        try {
            const res = await apiClient.get<LoyaltyData>('/api/v1/client/user/loyalty');
            this.data = res;
        } catch (err: unknown) {
            console.error("[Loyalty] Sync error:", err);
            this.error = err instanceof Error ? err.message : 'Lỗi khi tải dữ liệu tích điểm';
        } finally {
            this.loading = false;
        }
    }

    get tierName() {
        switch (this.data?.tier) {
            case 'SILVER': return 'Hạng Silver';
            case 'GOLD': return 'Hạng Gold';
            case 'PLATINUM': return 'Hạng Platinum (Elite)';
            default: return 'Thành viên Standard';
        }
    }

    get nextTierProgress() {
        if (!this.data) return 0;
        const total = this.data.total_spent;
        if (total < LOYALTY_TIERS.SILVER) return (total / LOYALTY_TIERS.SILVER) * 100;
        if (total < LOYALTY_TIERS.GOLD) return ((total - LOYALTY_TIERS.SILVER) / (LOYALTY_TIERS.GOLD - LOYALTY_TIERS.SILVER)) * 100;
        if (total < LOYALTY_TIERS.PLATINUM) return ((total - LOYALTY_TIERS.GOLD) / (LOYALTY_TIERS.PLATINUM - LOYALTY_TIERS.GOLD)) * 100;
        return 100;
    }
}

export const loyaltyStore = new LoyaltyStore();

