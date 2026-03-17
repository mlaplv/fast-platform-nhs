import json
import logging
import base64
import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from sqlalchemy import text
from pydantic_ai import Agent
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.creative_studio.models.schemas import MediaAnalysisResult
from backend.services.event_bus import event_bus

logger = logging.getLogger("api-gateway")

MEDIA_ANALYST_PROMPT = """[ROLE] CHUYÊN GIA THỊ GIÁC AI — Hệ thống XoHi Content Factory V65.0

[NHIỆM VỤ]
Phân tích hình ảnh được cung cấp và trích xuất dữ liệu chuẩn SEO & Accessibility.

[LUẬT]
1. alt_text: Viết bằng tiếng Việt, tập trung vào hành động/đối tượng chính. CẤM dùng "Hình ảnh về...", "Ảnh chụp...".
2. tags: Trích xuất 5-8 từ khóa (tiếng Việt) về đối tượng, chất liệu, ánh sáng, bối cảnh.
3. description: Mô tả chi tiết cho người khiếm thị hoặc AI hiểu sâu.
4. sentiment: Xác định vibe của ảnh (Chuyên nghiệp, Sang trọng, Tối giản, Năng động...).
5. focal_point: Xác định toạ độ {x, y} của vật thể/vùng quan trọng nhất (như khuôn mặt, sản phẩm). Giá trị từ 0.0 đến 1.0.
6. Trả về đúng JSON schema.
"""

class MediaAnalyst:
    """
    Operative chuyên dụng dùng Gemini 2.0 Flash (Vision) để phân tích ảnh.
    """
    def __init__(self):
        # CNS V76: Global-like semaphore for Vision tasks to protect VPS RAM (2GB Limit)
        self.vision_semaphore = asyncio.Semaphore(1)
        self.agent = Agent(
            output_type=MediaAnalysisResult,
            system_prompt=MEDIA_ANALYST_PROMPT,
            retries=2
        )

    async def analyze_image(self, image_data: bytes, mime_type: str = "image/webp") -> MediaAnalysisResult:
        """
        Phân tích ảnh trực tiếp từ bytes.
        """
        prompt = [
            "Hãy phân tích hình ảnh này theo yêu cầu chuyên môn.",
            {
                "data": image_data,
                "content_type": mime_type
            }
        ]

        try:
            # R101: Using trinity_bridge for managed AI calls
            # CNS V76: Enforce ROLE_FAST for vision tasks to optimize costs
            result = await trinity_bridge.run(
                self.agent,
                prompt,
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

        session_maker = alchemy_config.create_session_maker()
        async with session_maker() as session:
            # 1. Fetch essential data (Zero-Hydration)
            stmt = text("SELECT id, file_path, mime_type, media_metadata, campaign_id FROM media_registry WHERE id = :id")
            res = await session.execute(stmt, {"id": entry_id})
            row = res.fetchone()

            if not row:
                logger.error(f"[MediaAnalyst] Asset {entry_id} not found in DB.")
                return

            asset_id = str(row[0])
            file_path = str(row[1])
            mime_type = str(row[2])
            current_meta = row[3] or {}
            campaign_id = row[4]

            # Giả sử file_path là đường dẫn URL /v65_assets/...
            rel_path = file_path.lstrip("/")
            full_path = os.path.join("frontend/static", rel_path)

            if not os.path.exists(full_path):
                logger.error(f"[MediaAnalyst] Physical file not found for analysis: {full_path}")
                return

            # CNS V76: Enforce serial processing for vision tasks to prevent RAM spikes on 2GB VPS
            async with self.vision_semaphore:
                try:
                    # Offload file reading to avoid event loop blocking
                    image_bytes = await asyncio.to_thread(self._read_file, full_path)

                    analysis = await self.analyze_image(image_bytes, mime_type)

                    # Memory discipline: release bytes immediately
                    del image_bytes
                    gc.collect() # Force GC for large buffers

                    # Prepare metadata
                    meta = dict(current_meta)
                    meta.update({
                        "ai_tags": analysis.tags,
                        "ai_description": analysis.description,
                        "ai_sentiment": analysis.sentiment,
                        "focal_point": analysis.focal_point,
                        "analyzed_at": datetime.now(timezone.utc).isoformat()
                    })

                    # 2. Update DB (Zero-Hydration)
                    await session.execute(
                        text("UPDATE media_registry SET alt_text = :alt, media_metadata = :meta, updated_at = NOW() WHERE id = :id"),
                        {
                            "alt": analysis.alt_text,
                            "meta": json.dumps(meta),
                            "id": asset_id
                        }
                    )
                    await session.commit()

                    # --- REAL-TIME NOTIFICATION (V65.0) ---
                    # Emit event to InternalBus so SSE can pick it up
                    event_bus.emit("MEDIA_ANALYZED", {
                        "type": "MEDIA_ANALYZED",
                        "id": asset_id,
                        "campaign_id": campaign_id,
                        "file_path": file_path,
                        "alt_text": analysis.alt_text,
                        "media_metadata": meta
                    })

                    logger.info(f"[MediaAnalyst] Successfully analyzed asset: {entry_id}")

                except Exception as e:
                    logger.error(f"[MediaAnalyst] Post-processing failed for {entry_id}: {e}")

    def _read_file(self, path: str) -> bytes:
        """Internal helper for thread-safe file reading."""
        with open(path, "rb") as f:
            return f.read()
