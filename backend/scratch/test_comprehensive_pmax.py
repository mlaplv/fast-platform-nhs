import asyncio
import logging
import sys
from dotenv import load_dotenv

# Setup logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("test_comprehensive_pmax")

load_dotenv()

from backend.services.ads_protection.pmax_upgrader import PMaxUpgrader
from backend.services.ads_protection.ai_strategist import ai_strategist

from datetime import datetime, UTC

async def main():
    print("=== BẮT ĐẦU KIỂM TRA TOÀN DIỆN MIGRATION AI MAX (PMAX) ===")
    
    target_campaign_id = "23875876065"
    upgrader = PMaxUpgrader()
    
    # Bước 1: Kiểm tra cấu hình và xác thực
    print("Bước 1: Kiểm tra kết nối OAuth Google Ads...")
    token = await upgrader._get_access_token()
    if not token:
        print("❌ Thất bại: Không lấy được OAuth Access Token. Vui lòng kiểm tra lại file .env!")
        return
    print("✅ Thành công: Lấy được Access Token.")
    
    # Bước 2: Tìm URL trang đích của chiến dịch DSA cũ
    print(f"Bước 2: Truy vấn Google Ads để lấy URL trang đích của chiến dịch DSA {target_campaign_id}...")
    landing_page_url = "https://xohi.vn/pages/kem-duong-phuc-hoi-body"  # Fallback
    try:
        query = f"""
            SELECT ad_group_ad.ad.final_urls 
            FROM ad_group_ad 
            WHERE campaign.id = '{target_campaign_id}' 
              AND ad_group_ad.status = 'ENABLED'
            LIMIT 1
        """
        ad_res = await upgrader._search(token, query)
        if ad_res and len(ad_res) > 0:
            urls = ad_res[0].get("adGroupAd", {}).get("ad", {}).get("finalUrls", [])
            if urls:
                landing_page_url = urls[0]
                print(f"✅ Tìm thấy landing page thực tế: {landing_page_url}")
            else:
                print(f"⚠️ Chiến dịch không có ad ENABLED. Sử dụng fallback: {landing_page_url}")
        else:
            print(f"⚠️ Không tìm thấy ad hoạt động. Sử dụng fallback: {landing_page_url}")
    except Exception as e:
        print(f"❌ Lỗi khi lấy landing page: {e}")
        
    # Bước 3: Gọi AI Strategist để phân tích landing page và sinh Asset Group
    print(f"Bước 3: Gọi AI Strategist phân tích và sinh nội dung cho {landing_page_url}...")
    try:
        assets = await ai_strategist.generate_pmax_assets(landing_page_url)
        print("✅ AI Strategist phản hồi thành công:")
        print(f" - Tiêu đề (Headlines): {assets.headlines}")
        print(f" - Mô tả (Descriptions): {assets.descriptions}")
        print(f" - Từ khóa AI (Search Themes): {assets.search_themes}")
        print(f" - Marketing Images (Landscape): {assets.marketing_images}")
        print(f" - Square Marketing Images: {assets.square_marketing_images}")
        print(f" - Logo Images: {assets.logo_images}")
    except Exception as e:
        print(f"❌ Lỗi AI Strategist: {e}")
        return

    # Bước 4: Kiểm tra tải ảnh và xử lý Pillow
    print("Bước 4: Tải ảnh từ Landing Page và xử lý crop/scale bằng Pillow...")
    try:
        og_url = await upgrader._get_og_image_url(landing_page_url)
        print(f" - Tìm thấy og:image URL: {og_url or 'Không tìm thấy, dùng màu nền fallback'}")
        
        img_landscape = await upgrader._get_real_or_fallback_image(og_url, 1200, 628, (75, 0, 130), "AI PMax")
        img_square = await upgrader._get_real_or_fallback_image(og_url, 1200, 1200, (75, 0, 130), "AI PMax Sq")
        img_logo = await upgrader._get_real_or_fallback_image(og_url, 512, 512, (255, 255, 255), "AI Logo")
        
        print(f" - Kích thước ảnh landscape (1200x628) base64 len: {len(img_landscape)}")
        print(f" - Kích thước ảnh square (1200x1200) base64 len: {len(img_square)}")
        print(f" - Kích thước ảnh logo (512x512) base64 len: {len(img_logo)}")
        print("✅ Xử lý ảnh Pillow hoàn thành.")
    except Exception as e:
        print(f"❌ Lỗi xử lý ảnh Pillow: {e}")
        return

    # Bước 5: Chạy Atomic Migration trên Google Ads API
    print("Bước 5: Bắt đầu giao dịch nguyên tử nâng cấp lên AI Max (PMax)...")
    try:
        campaign_timestamp = datetime.now(UTC).strftime('%Y%m%d%H%M')
        result = await upgrader.upgrade_dsa_to_pmax(
            dsa_campaign_id=target_campaign_id,
            budget_vnd=150000.0,
            pmax_name=f"Beppin Body - AI Max (PMax) - Test {campaign_timestamp}",
            assets=assets
        )

        if result.success:
            print("🎉 THÀNH CÔNG RỰC RỠ! 🎉")
            print(f" - Resource Name: {result.resource_name}")
            print(f" - Tin nhắn: {result.message}")
        else:
            print("❌ Thất bại khi thực hiện nâng cấp trên Google Ads API!")
            print(f" - Chi tiết lỗi: {result.message}")
            print(f" - Lỗi chi tiết gốc (Last Mutate Error): {upgrader.get_last_mutate_error()}")
    except Exception as e:
        print(f"❌ Lỗi hệ thống trong quá trình nâng cấp: {e}")

if __name__ == "__main__":
    asyncio.run(main())
