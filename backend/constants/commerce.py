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

class CheckoutConfig:
    # [SECURITY] Giá trị đơn hàng tối thiểu sau tất cả giảm giá (bao gồm ship)
    MIN_ORDER_AMOUNT: float = 1000.0

    # [SECURITY] Giới hạn số loại sản phẩm trong 1 đơn — chặn OOM/Event Loop DDoS
    MAX_ITEMS_PER_ORDER: int = 20

    # [SECURITY] Giới hạn số voucher stack — chặn near-zero dollar exploit
    MAX_VOUCHER_STACK: int = 5

    # [SECURITY] Giới hạn custom items (yêu cầu thêm sản phẩm)
    MAX_CUSTOM_ITEMS: int = 10

    # [SECURITY] Tolerance giá sản phẩm (đồng) — cho phép sai số làm tròn
    PRICE_TOLERANCE_VND: float = 1.0

    # [SECURITY] Tolerance tổng đơn hàng (đồng)
    TOTAL_TOLERANCE_VND: float = 1.0
