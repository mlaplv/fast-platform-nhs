import os
import logging
import asyncio as _aio
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, delete as sql_delete
from litestar import Litestar

from backend.database import alchemy_config
from backend.database.models import VoiceProfile, ChatMessage
from backend.services.ai_engine.key_rotator import key_rotator
from backend.services.xohi_memory import xohi_memory
from backend.utils.security import GeminiSecurity
from backend.utils.text import normalize_vn
from backend.services.event_bus import event_bus
from backend.services.xohi_responder import setup_subscriptions
from backend.services.creative_studio.orchestrator import content_factory
from backend.services.ai_engine.trinity_bridge import trinity_bridge
from backend.utils.http_client import SharedHttpClient

logger = logging.getLogger("api-gateway")

@asynccontextmanager
async def lifespan(app: Litestar):
    # Start Proactive Nerve System
    setup_subscriptions()
    await event_bus.start()

    # Initialize AI Bridge (V76)
    await trinity_bridge.initialize()

    heartbeat_task = None
    purge_task = None
    media_cleanup_task = None

    try:
        # Pre-load Voice Profiles into Hot Cache (R76: Scalar Projection Optimization)
        async with alchemy_config.create_session_maker()() as session:
            # R76: Return only necessary columns to reduce RAM hydration
            stmt = select(
                VoiceProfile.user_id, 
                VoiceProfile.wake_words, 
                VoiceProfile.sleep_words, 
                VoiceProfile.greeting_template, 
                VoiceProfile.capabilities,
                VoiceProfile.gemini_keys_enc
            )
            results = await session.execute(stmt)
            profiles = results.all()
            
            count = len(profiles)
            
            # Load profile for cache
            for row in profiles:
                await xohi_memory.cache_voice_profile(str(row.user_id), {
                    "wake_words": [normalize_vn(w) for w in (row.wake_words or [])],
                    "sleep_words": [normalize_vn(w) for w in (row.sleep_words or [])],
                    "greeting_template": row.greeting_template,
                    "capabilities": row.capabilities or {},
                })

            # Load & Decrypt Gemini Keys (Unified V72.0)
            await key_rotator.load_keys()
            logger.info(f"[Trinity Core] Hot Reload Cache: {count} profiles and all keys loaded.")

        # Zero-Cold-Start Warmups
        try:
            from backend.services.ai_engine.encoder_singleton import warmup_encoder
            await _aio.wait_for(warmup_encoder(), timeout=30)
            from backend.services.ai_engine.semantic_router import SemanticRouter
            await _aio.wait_for(SemanticRouter().warmup(), timeout=30)
            logger.info("[Trinity Core] AI warmup complete.")
        except Exception as e:
            logger.critical(f"[Trinity Core] Warmup failed: {e}")

        # Start Background Loops
        purge_task = _aio.create_task(_auto_purge_loop())
        media_cleanup_task = _aio.create_task(_media_cleanup_loop())
        _aio.create_task(content_factory.resume_all())

        yield
    finally:
        if purge_task: purge_task.cancel()
        if media_cleanup_task: media_cleanup_task.cancel()
        await event_bus.stop()
        await SharedHttpClient.close()
        logger.info("[Trinity Core] Shutdown complete.")

async def _heartbeat_loop():
    from backend.services.anomaly_detector import AnomalyDetector
    detector = AnomalyDetector()
    interval = int(os.getenv("ANOMALY_SCAN_INTERVAL", "900"))
    await _aio.sleep(60)
    while True:
        try:
            async with alchemy_config.create_session_maker()() as session:
                await detector.scan(session)
        except Exception as e: 
            logger.exception(f"[Heartbeat] Scan failed: {e}")
        await _aio.sleep(interval)

async def _auto_purge_loop():
    interval = int(os.getenv("CHAT_PURGE_INTERVAL", "21600"))
    await _aio.sleep(300)
    while True:
        try:
            async with alchemy_config.create_session_maker()() as session:
                profiles = (await session.execute(select(VoiceProfile.user_id, VoiceProfile.chat_settings))).all()
                for row in profiles:
                    days = (row.chat_settings or {}).get("auto_purge_days", 30)
                    if days > 0:
                        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
                        await session.execute(sql_delete(ChatMessage).where(ChatMessage.user_id == row.user_id, ChatMessage.created_at < cutoff))
                await session.commit()
        except Exception as e: logger.warning(f"[AutoPurge] Cycle failed: {e}")
        await _aio.sleep(interval)

async def _media_cleanup_loop():
    """V76: Media Cleanup Cycle - Chạy mỗi 12h."""
    from backend.services.media_service import media_service
    # Chờ 10p sau khi khởi động để tránh làm nặng hệ thống lúc boot
    await _aio.sleep(600)
    while True:
        try:
            await media_service.cleanup_temp_files()
        except Exception as e:
            logger.warning(f"[MediaCleanup] Cycle failed: {e}")
        # 12 giờ = 43200 giây
        await _aio.sleep(43200)
