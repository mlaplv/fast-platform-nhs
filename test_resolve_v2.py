import asyncio
from backend.services.commerce.logic.location_resolver import location_resolver

async def test():
    # Test HCM code
    res = location_resolver.resolve("hcm")
    print(f"Resolve 'hcm': {res.province}, Valid: {res.is_valid}")
    
    # Test Hồ Chí Minh (short name)
    res = location_resolver.resolve("Ho Chi Minh")
    print(f"Resolve 'Ho Chi Minh': {res.province}, Valid: {res.is_valid}")
    
    # Test the problematic case: Phú Lâm + HCM
    res = location_resolver.resolve("336/28/19 nguyễn văn luông, phú lâm, hcm")
    print(f"Resolve complex: {res.province}, Ward: {res.ward}, Valid: {res.is_valid}")

asyncio.run(test())
