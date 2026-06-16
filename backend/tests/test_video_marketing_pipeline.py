import asyncio
import os
import sys

# Set test environment flag
os.environ["FAST_PLATFORM_TEST"] = "true"

from litestar.testing import AsyncTestClient
from backend.main import app

async def run_test():
    print("=== STARTING VIDEO MARKETING PIPELINE API TEST ===")
    
    async with AsyncTestClient(app=app) as client:
        # 1. Fetching styles to make sure metadata endpoint is active
        print("1. Fetching video styles...")
        response = await client.get("/api/v1/video/styles")
        print(f"Status: {response.status_code}")
        assert response.status_code == 200, "Styles listing failed"
        styles_data = response.json()
        print(f"Styles response preview: {styles_data.get('data', [])[:1]}\n")

        # 2. Listing video scripts
        print("2. Listing video scripts...")
        response = await client.get("/api/v1/video/scripts?limit=5&offset=0")
        print(f"Status: {response.status_code}")
        assert response.status_code == 200, "Scripts listing failed"
        scripts_data = response.json()
        print(f"Total scripts: {scripts_data.get('total', 0)}")
        
        scripts_list = scripts_data.get("data", [])
        print(f"Scripts returned: {len(scripts_list)}")
        if scripts_list:
            print(f"First script preview: {scripts_list[0]}\n")

            # 3. Search query test
            first_title = scripts_list[0]['title']
            print(f"3. Searching for script with title: '{first_title}'...")
            search_response = await client.get(f"/api/v1/video/scripts?search={first_title}")
            assert search_response.status_code == 200, "Search request failed"
            search_data = search_response.json()
            print(f"Found scripts: {len(search_data.get('data', []))}")
            assert len(search_data.get('data', [])) > 0, "Search didn't find the script"

            # 4. Soft Delete test
            target_id = scripts_list[0]['id']
            print(f"4. Soft-deleting script ID: {target_id}...")
            delete_response = await client.delete(f"/api/v1/video/script/{target_id}")
            print(f"Delete Status: {delete_response.status_code}")
            assert delete_response.status_code == 200, "Delete failed"
            print("Soft-delete successful!")
            
            # 5. Verify it's not in subsequent list
            print("5. Listing scripts again to check if soft-deleted script is hidden...")
            post_delete_response = await client.get("/api/v1/video/scripts")
            post_delete_data = post_delete_response.json()
            remaining_ids = [s['id'] for s in post_delete_data.get("data", [])]
            assert target_id not in remaining_ids, "Soft-deleted script still returned in listing!"
            print("Verified! Soft-deleted script is no longer visible.")
        else:
            print("No existing scripts found to test search and delete functionality. Skipping search/delete tests.")

    print("\n✅ === VIDEO MARKETING PIPELINE API TEST SUCCESSFUL ===")

if __name__ == "__main__":
    asyncio.run(run_test())
