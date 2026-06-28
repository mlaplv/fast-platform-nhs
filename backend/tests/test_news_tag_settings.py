import asyncio
import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ["FAST_PLATFORM_TEST"] = "true"

from backend.database import async_session_maker, engine
from backend.services.settings_service import settings_service
from backend.services.xohi_memory import xohi_memory
from backend.schemas.system_settings import SystemSettingsPayload, NewsTagSettings

async def run_settings_test():
    print("🚀 === STARTING SYSTEM SETTINGS & NEWS TAGS VERIFICATION TEST ===")
    
    # 1. Ensure Redis is online
    if not xohi_memory._use_redis:
        print("❌ Redis is offline. Test cannot proceed.")
        sys.exit(1)
        
    async with async_session_maker() as session:
        # 2. Get current system settings
        print("[*] Retrieving current system settings...")
        settings_response = await settings_service.get_general_settings(session)
        original_settings = settings_response.settings
        
        print(f"[+] Current settings retrieved successfully.")
        print(f"    - Site Name: {original_settings.basic_info.site_name}")
        print(f"    - Current News Tags map count: {len(original_settings.news_tags.tags_map)}")
        
        # 3. Create test news tags settings mapping
        test_tags_map = {
            "TEST_CHO_TAY": ["hotdog", "hamburger", "ketchup"],
            "TEST_DUONG_DA": ["vitaminc", "sunscreen", "collagen"],
            "CẢM HỨNG": ["story", "inspiration"]
        }
        
        print("[*] Updating news tags settings payload...")
        # Deep copy original settings and update news_tags
        payload_data = original_settings.model_dump()
        payload_data["news_tags"] = {"tags_map": test_tags_map}
        
        update_payload = SystemSettingsPayload(**payload_data)
        
        # 4. Save settings
        print("[*] Calling settings_service.update_general_settings...")
        update_response = await settings_service.update_general_settings(session, update_payload)
        await session.commit()
        assert update_response.ok, "Failed to update settings"
        print("[+] Settings updated successfully in database.")
        
        # 5. Check Redis cache synchronization
        print("[*] Verifying Redis synchronization...")
        cached_tags_raw = await xohi_memory.client.get("system:news_tags")
        assert cached_tags_raw is not None, "system:news_tags key not found in Redis!"
        
        cached_tags = json.loads(cached_tags_raw.decode("utf-8") if isinstance(cached_tags_raw, bytes) else cached_tags_raw)
        print(f"[+] Cached tags mapping in Redis: {json.dumps(cached_tags, ensure_ascii=False)}")
        
        assert "TEST_CHO_TAY" in cached_tags, "TEST_CHO_TAY missing from Redis tags!"
        assert cached_tags["TEST_CHO_TAY"] == ["hotdog", "hamburger", "ketchup"], "Keywords mismatch in Redis!"
        print("[+] Redis cache assertions PASSED successfully!")
        
        # 6. Test Article classification logic with the dynamic mapping
        print("[*] Testing dynamic article classification matching logic...")
        # Simulate article keyword matching based on dynamic tags mapping
        def get_article_tags(title: str, content: str, tags_map: dict[str, list[str]]) -> list[str]:
            matched_tags = []
            text_to_search = f"{title} {content}".lower()
            for tag, keywords in tags_map.items():
                for kw in keywords:
                    if kw.lower() in text_to_search:
                        matched_tags.append(tag)
                        break
            return matched_tags

        matched1 = get_article_tags("Cách chọn hotdog ngon nhất", "Tôi rất thích ăn hotdog chấm ketchup", cached_tags)
        print(f"    - Matched tags for hotdog article: {matched1}")
        assert "TEST_CHO_TAY" in matched1, "Classification failed!"
        
        matched2 = get_article_tags("Dưỡng da mùa hè", "Sử dụng vitaminc mỗi ngày", cached_tags)
        print(f"    - Matched tags for skin care article: {matched2}")
        assert "TEST_DUONG_DA" in matched2, "Classification failed!"
        
        print("[+] Dynamic article classification matching assertions PASSED successfully!")
        
        # 7. Restore original settings to keep DB and cache pristine
        print("[*] Restoring original settings...")
        restore_payload = SystemSettingsPayload(**original_settings.model_dump())
        restore_response = await settings_service.update_general_settings(session, restore_payload)
        await session.commit()
        assert restore_response.ok, "Failed to restore settings"
        print("[+] Original settings restored.")
        
    await engine.dispose()
    print("✨ === ALL VERIFICATION TESTS COMPLETED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(run_settings_test())
