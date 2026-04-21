import asyncio
from backend.services.commerce.logic.location_resolver import location_resolver
from backend.services.commerce.logic.lead_extractor import LeadExtractor, validate_vietnam_phone, ExtractedLead

async def diagnostic():
    print("--- 🔍 DIAGNOSTIC: GHOST ADDRESS RESOLUTION ---")
    ghost_addr = "Virgin White Serum"
    resolved = location_resolver.resolve(ghost_addr)
    print(f"Address: '{ghost_addr}'")
    print(f"  - Province: {resolved.province}")
    print(f"  - Score: {resolved.score}")
    print(f"  - Is Valid: {resolved.is_valid}")
    print(f"  - Shipping Days: {resolved.shipping_days}")

    print("\n--- 🔍 DIAGNOSTIC: PHONE VALIDATION ---")
    phone = "0949901122"
    validated = validate_vietnam_phone(phone)
    print(f"Phone: '{phone}' -> Validated: '{validated}'")

    print("\n--- 🔍 DIAGNOSTIC: LEAD EXTRACTION FALLBACK ---")
    # Simulate turn 2 where user only types 10 digits
    msg = "0949901122"
    # We check if current turn has a regex fallback
    import re
    phone_re = re.compile(r"0\d{8,10}")
    match = phone_re.search(msg)
    print(f"Regex match on '{msg}': {match.group() if match else 'NONE'}")

if __name__ == "__main__":
    asyncio.run(diagnostic())
