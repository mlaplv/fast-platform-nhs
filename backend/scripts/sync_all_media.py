import asyncio
import logging
import sys
from sqlalchemy import select
from backend.database import alchemy_config
from backend.database.models import ProductBase, Article, Banner, SystemSetting, ChatMessage
from backend.database.repositories import MediaRegistryRepository
from backend.services.media.media_service import media_service
from backend.utils.media import extract_media_urls

# Cấu hình logging chuyên sâu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("media-sync-tool")

async def sync_all_entities():
    """
    Elite V2.2: Neural System Re-sync (Direct & Chat-Aware).
    Quét và đồng bộ trực tiếp trạng thái Media cho toàn bộ hệ thống bao gồm cả Chat.
    """
    logger.info("🚀 Bắt đầu chiến dịch Full System Media Re-sync (Direct & Chat-Aware)...")
    
    async_session_maker = alchemy_config.create_session_maker()
    
    async with async_session_maker() as session:
        try:
            repo = MediaRegistryRepository(session=session)
            
            # 1. Đồng bộ Sản phẩm
            logger.info("📦 Đang quét Sản phẩm...")
            stmt_products = select(ProductBase).where(ProductBase.deleted_at == None)
            products = (await session.execute(stmt_products)).scalars().all()
            for p in products:
                data = {
                    "images": p.images,
                    "mobile_images": p.mobile_images,
                    "tier_variations": p.tier_variations,
                    "metadata": p.product_metadata,
                    "description": p.description
                }
                urls = extract_media_urls(data)
                if urls:
                    await media_service.sync_links(repo, str(p.id), "product", list(urls))
            logger.info(f"✅ Đã đồng bộ {len(products)} sản phẩm.")

            # 2. Đồng bộ Bài viết/Tin tức
            logger.info("📰 Đang quét Bài viết/Tin tức...")
            stmt_articles = select(Article).where(Article.deleted_at == None)
            articles = (await session.execute(stmt_articles)).scalars().all()
            for a in articles:
                data = {
                    "featured_image": a.featured_image,
                    "seo_og_image": a.seo_og_image,
                    "content": a.content
                }
                urls = extract_media_urls(data)
                if urls:
                    await media_service.sync_links(repo, str(a.id), "news", list(urls))
            logger.info(f"✅ Đã đồng bộ {len(articles)} bài viết.")

            # 3. Đồng bộ Banners
            logger.info("🚩 Đang quét Banners...")
            stmt_banners = select(Banner).where(Banner.deleted_at == None)
            banners = (await session.execute(stmt_banners)).scalars().all()
            for b in banners:
                urls = extract_media_urls(b.image_url)
                if urls:
                    await media_service.sync_links(repo, str(b.id), "banner", list(urls))
            logger.info(f"✅ Đã đồng bộ {len(banners)} banners.")

            # 4. Đồng bộ Chat Gemini (Ảnh từ AI tạo ra)
            logger.info("🤖 Đang quét Chat Messages (Gemini Expert)...")
            stmt_chats = select(ChatMessage).where(ChatMessage.deleted_at == None)
            chats = (await session.execute(stmt_chats)).scalars().all()
            for c in chats:
                # Chat message có thể chứa URL ảnh trong content (markdown) hoặc metadata
                urls = extract_media_urls(c.content)
                if urls:
                    await media_service.sync_links(repo, str(c.id), "chat_message", list(urls))
            logger.info(f"✅ Đã đồng bộ {len(chats)} tin nhắn chat.")

            # 5. Đồng bộ Cấu hình Hệ thống
            logger.info("⚙️ Đang quét Cấu hình Hệ thống...")
            stmt_settings = select(SystemSetting).where(SystemSetting.key == "primary_config")
            setting = (await session.execute(stmt_settings)).scalars().first()
            if setting:
                urls = extract_media_urls(setting.value)
                if urls:
                    await media_service.sync_links(repo, "primary_config", "system_settings", list(urls))
                logger.info("✅ Đã đồng bộ cấu hình hệ thống.")

            # [POINT TRIỆU ĐÔ] Commit thay đổi
            await session.commit()
            logger.info("🏁 Hoàn tất chiến dịch giải cứu Media! Dữ liệu đã được LƯU VĨNH VIỄN.")

        except Exception as e:
            logger.error(f"❌ Lỗi trong quá trình đồng bộ: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(sync_all_entities())
