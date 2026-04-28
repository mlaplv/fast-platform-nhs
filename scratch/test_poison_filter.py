import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from backend.services.commerce.price_agent import normalize_vn_price, is_poisoned_context

def test_poisoning():
    print("--- Testing Poison Context Detection ---")
    text1 = "Nhận ngay voucher 50.000đ khi mua hàng tại Miccosmo"
    price_str = "50.000đ"
    start_idx = text1.find(price_str)
    poisoned = is_poisoned_context(text1, start_idx, start_idx + len(price_str))
    print(f"Text: '{text1}'")
    print(f"Price: {price_str}, Poisoned: {poisoned} (Expected: True)")

    text2 = "Giá bán: 550.000đ. Miễn phí ship cho đơn từ 500k."
    price_str2 = "550.000đ"
    start_idx2 = text2.find(price_str2)
    poisoned2 = is_poisoned_context(text2, start_idx2, start_idx2 + len(price_str2))
    print(f"Text: '{text2}'")
    print(f"Price: {price_str2}, Poisoned: {poisoned2} (Expected: False)")

    print("\n--- Testing Normalize VN Price (Multi-match + Poison Filter) ---")
    snippet = "Kem dưỡng vùng cổ Miccosmo - Voucher 50.000đ - Giá gốc 650.000đ"
    # Should pick 650k because 50k is poisoned by 'voucher'
    price = normalize_vn_price(snippet, prefer_higher=True)
    print(f"Snippet: '{snippet}'")
    print(f"Extracted Price: {price:,.0f} VND (Expected: 650,000)")

    snippet2 = "Mua ngay nhận mã giảm 100k. Giá sản phẩm: 450.000đ"
    price2 = normalize_vn_price(snippet2, prefer_higher=True)
    print(f"Snippet: '{snippet2}'")
    print(f"Extracted Price: {price2:,.0f} VND (Expected: 450,000)")

    snippet3 = "Phí ship 30.000đ. Giá: 350.000đ"
    price3 = normalize_vn_price(snippet3, prefer_higher=True)
    print(f"Snippet: '{snippet3}'")
    print(f"Extracted Price: {price3:,.0f} VND (Expected: 350,000)")

if __name__ == "__main__":
    test_poisoning()
