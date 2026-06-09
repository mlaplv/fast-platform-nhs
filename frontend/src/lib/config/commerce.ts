/**
 * ELITE V2.2: Commerce Configuration Constants
 * Centralized source of truth to avoid hardcoding in components.
 */

export const SHIPPING_CONFIG = {
  STANDARD_FEE: 30000,
  FREE_THRESHOLD: 2000000, // đ2,000,000 for free shipping
  EXPRESS_BASE_FEE: 50000,
};

export const LOYALTY_CONFIG = {
  POINT_VALUE: 10000, // 1 point = 10000 VND
  MAX_DISCOUNT_PERCENT: 0.01, // Max 1% of total
  EARNING_RATE_VND: 100000,
  LABELS: {
    POINTS_UNIT: "điểm",
    EARN_PREFIX: "Dự kiến tích lũy: +",
    REDEEM_LABEL: "Dùng điểm tích lũy",
    AVAILABLE_POINTS: "Số điểm khả dụng:"
  }
};

export const LOYALTY_TIERS = {
  SILVER: 5000000,
  GOLD: 10000000,
  PLATINUM: 20000000, // Elite tier
};

