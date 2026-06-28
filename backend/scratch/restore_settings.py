import asyncio
import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database import async_session_maker, engine
from backend.services.settings_service import settings_service
from backend.schemas.system_settings import SystemSettingsPayload

# Original settings JSON from the June 9th backup
BACKUP_JSON = {
    "basic_info": {
        "site_name": "osmo.vn",
        "slogan": "Top 10 Mỹ phẩm Nhật Bản",
        "subslogan": "Tinh hoa Mỹ phẩm Nội địa chuẩn Nhật Bản",
        "description": "Mỹ phẩm Cao Cấp Nội địa chuẩn Nhật Bản",
        "logo_desktop": None,
        "logo_mobile": None,
        "favicon": None
    },
    "contact_info": {
        "company_name": "HKD VALA",
        "tax_id": "",
        "business_license": "066082007605, do UBND Phường Phú Lâm cấp ngày 28/4/2026",
        "phone": "0978785079",
        "hotline": "094990112",
        "email": "contact@osmo.vn",
        "address": "336/28/19 Nguyễn Văn Luông, Phú Lâm, HCM",
        "working_hours": "8:00 - 22:00"
    },
    "currency": {
        "symbol": "₫",
        "position": "suffix",
        "decimal_separator": ".",
        "thousand_separator": ".",
        "show_symbol": True
    },
    "social_media": [
        {"platform": "Facebook", "url": "https://facebook.com/osmo.vn", "icon_url": None},
        {"platform": "Zalo", "url": "https://zalo.me/osmo.vn", "icon_url": None},
        {"platform": "TikTok", "url": "https://tiktok.com/@osmo.vn", "icon_url": None}
    ],
    "seo_analytics": {
        "meta_title": "Mỹ Phẩm Miccosmo | Phục Hồi & Bảo Vệ Da Nhạy Cảm",
        "meta_description": "Mỹ Phẩm xu hướng chăm da Miccosmo tại Osmo.vn. Giải pháp dưỡng da lành tính, không kích ứng giúp củng cố hàng rào bảo vệ, an toàn cho da nhạy cảm.",
        "meta_keywords": "Mỹ phầm Miccosmo, dưỡng da lành tính, không kích ứng, thành phần tự nhiên, công nghệ dưỡng da",
        "google_analytics_id": "",
        "facebook_pixel_id": "",
        "google_tag_manager_id": "GTM-WDJQ5S2F",
        "google_search_console_id": ""
    },
    "google_maps": {
        "map_iframe": "",
        "api_key": ""
    },
    "maintenance": {
        "is_enabled": False,
        "message": "Hệ thống đang bảo trì để nâng cấp Core AI. Vui lòng quay lại sau."
    },
    "support_bot": {
        "helen_enabled": True,
        "offline_message": "Dạ chào Anh/Chị. Anh/Chị cần hỗ trợ thông tin gì ạ!",
        "zalo_integration_enabled": True,
        "messenger_integration_enabled": True
    },
    "conversions": {
        "fomo_enabled": True
    },
    "entropy": {
        "enabled": True,
        "tone_override": None,
        "structure_override": None,
        "schema_drop_probability": 0.2,
        "lexical_sanitizer_enabled": True
    },
    # Preserve news_tags we set up in this session
    "news_tags": {
        "tags_map": {
            "DƯỠNG DA": ["skin", "aging", "cleansing", "hydration", "da", "dưỡng", "rửa", "cổ"],
            "CẢM HỨNG": ["inspiration", "story", "cảm hứng", "hành trình", "chia sẻ", "lối sống"],
            "XU HƯỚNG": ["trend", "strategies", "future", "xu hướng", "2026", "mới", "lão hóa"],
            "ƯU ĐÃI": ["deal", "discount", "voucher", "ưu đãi", "khuyến mãi", "quà"],
            "MẸO HAY": ["tips", "fundamentals", "how to", "mẹo", "hướng dẫn", "nguyên tắc", "cách"],
            "SỨC KHỎE": ["health", "healthy", "sức khỏe", "lão hóa", "dinh dưỡng"]
        }
    }
}

async def restore():
    print("[*] Instantiating SystemSettingsPayload from backup dict...")
    # Pydantic will auto-populate defaults (like seo_contextual_links) if they are missing from BACKUP_JSON
    payload = SystemSettingsPayload(**BACKUP_JSON)
    
    async with async_session_maker() as session:
        print("[*] Saving restored settings payload...")
        res = await settings_service.update_general_settings(session, payload)
        await session.commit()
        if res.ok:
            print("[+] Settings restored successfully in Database & Redis.")
        else:
            print("[-] Update settings returned unsuccessful status.")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(restore())
