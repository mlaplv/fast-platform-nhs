import logging
import base64
import asyncio
from typing import Optional, Dict, List
from datetime import datetime, timezone
from pydantic_ai import Agent
from pydantic_ai.messages import BinaryImage
from pydantic_ai.models.google import GoogleModel
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.creative_studio.models.schemas import MediaAnalysisResult
from backend.database.models import MediaRegistry
from backend.database.repositories import MediaRegistryRepository
from backend.services.event_bus import event_bus
from backend.services.xohi.prompts import composer

logger = logging.getLogger("api-gateway")

class MediaAnalyst:
    """
    Operative chuyên dụng dùng Gemini 2.0 Flash (Vision) để phân tích ảnh.
    Elite V2.2: Context-Aware with Neural Prompt Orchestration (NPO).
    """
    def __init__(self):
        # CNS V76: Global-like semaphore for Vision tasks to protect VPS RAM (2GB Limit)
        self.vision_semaphore = asyncio.Semaphore(1)
        self.agent = Agent(
            output_type=MediaAnalysisResult,
            retries=2
        )

    async def analyze_image(self, image_data: bytes, mime_type: str = "image/webp") -> MediaAnalysisResult:
        """
        Phân tích ảnh trực tiếp từ bytes.
        """
        prompt = [
            "Hãy phân tích hình ảnh này theo yêu cầu chuyên môn.",
            BinaryImage(data=image_data, media_type=mime_type)
        ]

        try:
            system_prompt = composer.compose("media_analysis")

            # R101: Using trinity_bridge for managed AI calls
            # CNS V76: Enforce ROLE_FAST for vision tasks to optimize costs
            result = await trinity_bridge.run(
                self.agent,
                prompt,
                system_prompt=system_prompt,
                role=trinity_bridge.ROLE_FAST
            )
            return result.data
        except Exception as e:
            logger.error(f"[MediaAnalyst] Vision analysis failed: {e}")
            # Fallback (Graceful Degradation R103)
            return MediaAnalysisResult(
                alt_text="Hình ảnh xohi: Tự động tối ưu.",
                tags=["minh họa", "content", "xohi"],
                description="Hệ thống đang rơi vào trạng thái Blind Crop (AI Fallback).",
                sentiment="Trung tính",
                focal_point={"x": 0.5, "y": 0.5}
            )

    async def process_registry_entry(self, entry_id: str):
        """
        Quy trình xử lý hậu kỳ cho một Registry Entry mới (Background Task).
        Sử dụng Session riêng biệt để đảm bảo an toàn Thread/Lifecycle.
        """
        import os
        import gc
        from backend.database.alchemy_config import alchemy_config
        from backend.database.repositories import MediaRegistryRepository

        session_maker = alchemy_config.create_session_maker()
        async with session_maker() as session:
            media_repo = MediaRegistryRepository(session=session)
            entry = await media_repo.get(entry_id)

            if not entry:
                logger.error(f"[MediaAnalyst] Asset {entry_id} not found in DB.")
                return

            # Giả sử entry.file_path là đường dẫn URL /v65_assets/...
            rel_path = entry.file_path.lstrip("/")
            full_path = os.path.join("frontend/static", rel_path)

            if not os.path.exists(full_path):
                logger.error(f"[MediaAnalyst] Physical file not found for analysis: {full_path}")
                return

            # CNS V76: Enforce serial processing for vision tasks to prevent RAM spikes on 2GB VPS
            async with self.vision_semaphore:
                try:
                    # Offload file reading to avoid event loop blocking
                    image_bytes = await asyncio.to_thread(self._read_file, full_path)

                    analysis = await self.analyze_image(image_bytes, entry.mime_type)

                    # Memory discipline: release bytes immediately
                    del image_bytes
                    gc.collect() # Force GC for large buffers

                    # Cập nhật metadata
                    entry.alt_text = analysis.alt_text
                    meta = dict(entry.media_metadata or {})
                    meta.update({
                        "ai_tags": analysis.tags,
                        "ai_description": analysis.description,
                        "ai_sentiment": analysis.sentiment,
                        "focal_point": analysis.focal_point,
                        "analyzed_at": datetime.now(timezone.utc).isoformat()
                    })
                    entry.media_metadata = meta

                    await media_repo.update(entry)
                    await session.commit()

                    # --- REAL-TIME NOTIFICATION (V65.0) ---
                    # Emit event to InternalBus so SSE can pick it up
                    await event_bus.emit("MEDIA_ANALYZED", {
                        "type": "MEDIA_ANALYZED",
                        "id": entry.id,
                        "campaign_id": entry.campaign_id,
                        "file_path": entry.file_path,
                        "alt_text": entry.alt_text,
                        "media_metadata": entry.media_metadata
                    })

                    logger.info(f"[MediaAnalyst] Successfully analyzed asset: {entry_id}")

                except Exception as e:
                    logger.error(f"[MediaAnalyst] Post-processing failed for {entry_id}: {e}")

    async def heuristic_analysis(self, entry_id: str):
        """
        [V2026 Viral] Phân tích nhanh bằng Heuristics khi AI Vision bị TẮT.
        Dựa vào filename, extension để tạo metadata ảo diệu lấp chỗ trống.
        """
        import os
        from backend.database.alchemy_config import alchemy_config
        from backend.database.repositories import MediaRegistryRepository

        session_maker = alchemy_config.create_session_maker()
        async with session_maker() as session:
            media_repo = MediaRegistryRepository(session=session)
            entry = await media_repo.get(entry_id)

            if not entry:
                return

            try:
                # Phân tích nhanh từ filename
                filename = entry.filename or "hình-ảnh-nội-bộ"
                base_name = os.path.splitext(filename)[0]
                clean_name = base_name.replace("-", " ").replace("_", " ").title()

                # Cập nhật metadata "Viral 2026"
                entry.alt_text = f"{clean_name} - Tối ưu hoá Neural 2026"
                
                meta = dict(entry.media_metadata or {})
                meta.update({
                    "ai_tags": ["XoHi 2026", "Viral", "Original Content", "High Quality", "Trending"],
                    "ai_description": f"Tài nguyên media hệ thống: {clean_name}. Được xử lý tốc độ cao qua luồng Heuristic Engine (Vision OFF).",
                    "ai_sentiment": "Chuyên nghiệp, Năng động",
                    "focal_point": {"x": 0.5, "y": 0.5},
                    "analyzed_at": datetime.now(timezone.utc).isoformat()
                })
                entry.media_metadata = meta

                await media_repo.update(entry)
                await session.commit()

                # --- REAL-TIME NOTIFICATION ---
                await event_bus.emit("MEDIA_ANALYZED", {
                    "type": "MEDIA_ANALYZED",
                    "id": entry.id,
                    "campaign_id": entry.campaign_id,
                    "file_path": entry.file_path,
                    "alt_text": entry.alt_text,
                    "media_metadata": entry.media_metadata
                })

                logger.info(f"[MediaAnalyst] Heuristic analysis completed instantly for: {entry_id}")

            except Exception as e:
                logger.error(f"[MediaAnalyst] Heuristic Post-processing failed for {entry_id}: {e}")

    def _read_file(self, path: str) -> bytes:
        """Internal helper for thread-safe file reading."""
        with open(path, "rb") as f:
            return f.read()
