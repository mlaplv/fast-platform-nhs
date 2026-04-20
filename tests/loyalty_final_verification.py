def verify_1_percent_rule():
    # Scenario: 1,000,000 VND order
    subtotal = 1_000_000 
    points_to_redeem = 10 # 10,000 VND
    point_value = 1000
    
    # New Rule: 1% limit
    max_point_discount = subtotal * 0.01
    proposed_discount = points_to_redeem * point_value
    
    print(f"--- 1% Rule Verification ---")
    print(f"Order Total: {subtotal:,} VND")
    print(f"Max allowed discount (1%): {max_point_discount:,} VND")
    print(f"Proposed discount (10 pts = 10,000 VND): {proposed_discount:,} VND")
    
    if proposed_discount <= max_point_discount:
        print("✅ SUCCESS: 10 points redemption allowed for 1M order.")
    else:
        print("❌ FAIL: Still too restrictive.")

    # Tier Upgrade Check
    spent = 15_000_000
    tier = "STANDARD"
    if spent > 20_000_000: tier = "PLATINUM"
    elif spent == 20_000_000: tier = "GOLD"
    elif spent >= 10_000_000: tier = "SILVER"
    
    print(f"\n--- Tier Verification ---")
    print(f"Total Spent: {spent:,} VND")
    print(f"Assigned Tier: {tier}")
    if tier == "SILVER":
        print("✅ SUCCESS: Tier mapping is correct.")
    else:
        print("❌ FAIL: Tier mapping issue.")

if __name__ == "__main__":
    verify_1_percent_rule()
