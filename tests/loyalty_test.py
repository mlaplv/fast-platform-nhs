import math

def test_loyalty_math():
    subtotal = 1_000_000 # 1 million VND
    points_to_redeem = 1
    point_value = 1000
    
    # Sếp Rule: 0,01% htr
    max_point_discount = subtotal * 0.0001
    proposed_discount = points_to_redeem * point_value
    
    print(f"Subtotal: {subtotal:,} VND")
    print(f"Max allowed discount (0.01%): {max_point_discount:,} VND")
    print(f"Proposed discount (1 point): {proposed_discount:,} VND")
    
    if proposed_discount > max_point_discount:
        print("FAIL: Cannot even redeem 1 point for a 1M order.")
    else:
        print("SUCCESS: 1 point redemption allowed.")

if __name__ == "__main__":
    test_loyalty_math()
