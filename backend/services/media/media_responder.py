import logging
from typing import Dict, List, Any
from backend.services.event_bus import event_bus
from backend.database import alchemy_config
from backend.database.repositories import MediaRegistryRepository
from backend.services.media.media_service import media_service

logger = logging.getLogger("media-responder")

class MediaResponder:
    """
    Elite V2.2: Neural Media Responder.
    Lắng nghe và thực thi các yêu cầu đồng bộ Media từ toàn hệ thống.
    """
    def __init__(self):
        self.session_maker = alchemy_config.create_session_maker()

    async def handle_media_sync(self, payload: Dict[str, Any]):
        """
        Xử lý sự kiện MEDIA_SYNC_REQUIRED.
        Đảm bảo việc đồng bộ ảnh diễn ra trong background, không chặn main request.
        """
        entity_id = payload.get("entity_id")
        entity_type = payload.get("entity_type")
        urls = payload.get("urls", [])

        if not entity_id or not entity_type:
            logger.warning("[MediaResponder] Missing entity_id or entity_type in payload.")
            return

        logger.debug(f"[MediaResponder] Syncing {entity_type}:{entity_id} with {len(urls)} URLs")

        async with self.session_maker() as session:
            try:
                repo = MediaRegistryRepository(session=session)
                await media_service.sync_links(
                    repo=repo,
                    entity_id=entity_id,
                    entity_type=entity_type,
                    current_urls=urls
                )
                # Note: sync_links handles commit/rollback internally
            except Exception as e:
                logger.error(f"[MediaResponder] Sync failed for {entity_type}:{entity_id}: {e}")

# Global instance
media_responder = MediaResponder()
