/**
 * ELITE V2.2 - Loyalty & Rewards Configuration
 * Synchronized with backend/constants/commerce.py
 */

export const LOYALTY_CONFIG = {
    // 1 point = 1000 VND discount
    POINT_VALUE: 1000,
    
    // 1 point earned per 100k VND spent
    EARNING_RATE_VND: 100000,
    
    // Max discount allowed (1% of total)
    MAX_DISCOUNT_PERCENT: 0.01,
    
    // Tier Thresholds (Total Spent in VND)
    TIERS: {
        SILVER: 5000000,
        GOLD: 10000000,
        PLATINUM: 20000000
    },
    
    // UI Labels
    LABELS: {
        POINTS_UNIT: "Pts",
        EARN_PREFIX: "Dự kiến tích lũy: +",
        REDEEM_LABEL: "Dùng điểm tích lũy",
        AVAILABLE_POINTS: "Số điểm khả dụng:"
    }
};
