import asyncio
import httpx

async def test_api_filter():
    # Use verify=False to bypass SSL check on self-signed certs
    async with httpx.AsyncClient(verify=False) as client:
        # Test exact space "White Label"
        url1 = "https://127.0.0.1/api/v1/client/products?brand=White%20Label"
        res1 = await client.get(url1, headers={"Host": "osmo.vn", "x-tenant": "default"})
        if res1.status_code == 200:
            data = res1.json()
            products = data.get("data", [])
            print(f"Query: 'brand=White%20Label' | Status: 200 | Count: {len(products)}")
            for p in products:
                print(f"- {p['name']} | brand: {p.get('attributes', {}).get('brand')} | Thương hiệu: {p.get('attributes', {}).get('Thương hiệu')}")
        else:
            print(f"URL1 failed: {res1.status_code}")

        # Test with plus "White+Label"
        url2 = "https://127.0.0.1/api/v1/client/products?brand=White+Label"
        res2 = await client.get(url2, headers={"Host": "osmo.vn", "x-tenant": "default"})
        if res2.status_code == 200:
            data = res2.json()
            products2 = data.get("data", [])
            print(f"\nQuery: 'brand=White+Label' | Status: 200 | Count: {len(products2)}")
            for p in products2:
                print(f"- {p['name']} | brand: {p.get('attributes', {}).get('brand')} | Thương hiệu: {p.get('attributes', {}).get('Thương hiệu')}")
        else:
            print(f"URL2 failed: {res2.status_code}")

if __name__ == "__main__":
    asyncio.run(test_api_filter())
