import asyncio
from backend.services.commerce.logic.location_resolver import location_resolver

async def test():
    print("Testing HCM...")
    res1 = location_resolver.resolve("336/28/19 nguyễn văn luông, phú lâm, HCM")
    print(res1)
    
    print("\nTesting hcm...")
    res2 = location_resolver.resolve("336/28/19 nguyễn văn luông, phú lâm, hcm")
    print(res2)

asyncio.run(test())
