import re
from typing import List, Optional, Tuple

def validate_vietnam_phone(phone: str) -> Optional[str]:
    if not phone: return None
    p = re.sub(r"[\s\.\-\+]", "", str(phone))
    if p.startswith("84"): p = "0" + p[2:]
    if len(p) == 10 and p.startswith("0"): return p
    return None

class OrderDraft:
    def __init__(self, items=None, customer_phone=None, customer_address=None):
        self.items = items or []
        self.customer_phone = customer_phone
        self.customer_address = customer_address
    
    @property
    def missing_slots(self):
        missing = []
        if not self.items: missing.append("Sản phẩm")
        if not self.customer_phone: missing.append("Số điện thoại")
        if not self.customer_address: missing.append("Địa chỉ cụ thể")
        return missing

def simulate_order_handler(msg, draft):
    msg = msg.lower().strip()
    missing = draft.missing_slots
    draft_filled = False
    lead_data_phone = None
    lead_data_address = None
    
    # Simulate lines 122-142
    if missing:
        # Phone check
        if "Số điện thoại" in missing:
            digits_only = re.sub(r"\D", "", msg)
            phone_match = re.search(r"0\d{9}", digits_only)
            if phone_match:
                validated_phone = validate_vietnam_phone(phone_match.group())
                if validated_phone:
                    draft.customer_phone = validated_phone
                    draft_filled = True
                    print(f"DEBUG: Phone filled: {validated_phone}")
        
        # Address check
        if "Địa chỉ cụ thể" in missing and not draft_filled:
            has_addr_signal = "/" in msg or any(kw in msg for kw in ["đường", "phố", "phường", "quận"])
            has_digits = any(c.isdigit() for c in msg)
            if has_addr_signal or (len(msg) > 15 and has_digits):
                draft.customer_address = msg
                draft_filled = True
                print(f"DEBUG: Address filled: {msg}")

    # Simulate lead_data synthesis (lines 168-177)
    if draft_filled:
        lead_data_phone = draft.customer_phone
        lead_data_address = draft.customer_address
        print(f"DEBUG: lead_data synthesized: phone={lead_data_phone}, address={lead_data_address}")

    # Decision Engine (lines 237-259)
    is_address_resolved = bool(lead_data_address) # Simplified
    
    if not lead_data_phone or not is_address_resolved:
        if not lead_data_phone and not is_address_resolved:
            return "ASK_BOTH"
        elif not lead_data_phone:
            return "ASK_PHONE"
        else:
            return "ASK_ADDRESS"
    return "SUCCESS"

# Test Case
test_msg = "0949901122, 336/28/19 Nguyễn Văn Luông, Phú Lâm"
test_draft = OrderDraft(items=[{"name": "test"}]) # missing phone and address

result = simulate_order_handler(test_msg, test_draft)
print(f"Result: {result}")
