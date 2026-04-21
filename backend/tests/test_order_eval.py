import re

msg = "cho 1 miccosmo white label premium placenta wash 110g"
staff_patterns = ["cho 1 đơn", "cho đơn", "về :", "về:", "lên đơn", "gửi đơn"]
potential_keywords = ["mua", "đặt", "lấy", "ship", "giao", "ok", "chốt", "đơn", "cho"]

has_digits = any(char.isdigit() for char in msg)
has_standalone_phone = bool(re.search(r"0\d{8,10}", msg))
is_staff_order = any(sp in msg for sp in staff_patterns) and has_digits
has_buying_intent = any(kw in msg for kw in potential_keywords)

is_strong_intent = has_digits and (has_buying_intent or is_staff_order or has_standalone_phone)

print("has_digits:", has_digits)
print("has_buying_intent:", has_buying_intent)
print("is_strong_intent:", is_strong_intent)

msg2 = "0949901122"
has_digits2 = any(char.isdigit() for char in msg2)
has_standalone_phone2 = bool(re.search(r"0\d{8,10}", msg2))
is_staff_order2 = any(sp in msg2 for sp in staff_patterns) and has_digits2
has_buying_intent2 = any(kw in msg2 for kw in potential_keywords)
is_strong_intent2 = has_digits2 and (has_buying_intent2 or is_staff_order2 or has_standalone_phone2)

print("has_digits 2:", has_digits2)
print("has_standalone_phone 2:", has_standalone_phone2)
print("is_strong_intent 2:", is_strong_intent2)
