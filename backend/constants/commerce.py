# Elite V2.2: Commerce Configuration Constants
# Centralized source of truth for pricing engine and checkout services.

class ShippingConfig:
    STANDARD_FEE = 30000.0
    FREE_THRESHOLD = 2000000.0 # đ2,000,000 for free shipping
    EXPRESS_BASE_FEE = 50000.0

class LoyaltyConfig:
    POINT_VALUE = 1000.0 # 1 point = 1000 VND
    MAX_DISCOUNT_PERCENT = 0.01 # Max 1% of total
    EARNING_RATE_VND = 100000.0 # 1 point earned per 100k VND spent
