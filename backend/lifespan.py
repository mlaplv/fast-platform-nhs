import os
import logging
import asyncio as _aio
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, delete as sql_delete
from litestar import Litestar

from backend.database import alchemy_config
from backend.database.models import VoiceProfile, ChatMessage
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.utils.security import GeminiSecurity
from backend.utils.text import normalize_vn
from backend.services.event_bus import event_bus
from backend.services.xohi_responder import setup_subscriptions
from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.utils.http_client import SharedHttpClient
from backend.services.xohi_memory import xohi_memory

logger = logging.getLogger("api-gateway")

@asynccontextmanager
async def lifespan(app: Litestar):
    # Start Proactive Nerve System
    setup_subscriptions()
    await event_bus.start()
    
    heartbeat_task = None
    purge_task = None
    
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
            
            all_keys = set()
            count = 0
            for row in profiles:
                # Load profile for cache
                await xohi_memory.cache_voice_profile(str(row.user_id), {
                    "wake_words": [normalize_vn(w) for w in (row.wake_words or [])],
                    "sleep_words": [normalize_vn(w) for w in (row.sleep_words or [])],
                    "greeting_template": row.greeting_template,
                    "capabilities": row.capabilities or {},
                })
                
                # Load & Decrypt Gemini Keys
                if row.gemini_keys_enc:
                    decrypted = GeminiSecurity.decrypt_keys(row.gemini_keys_enc)
                    all_keys.update(decrypted)
                
                count += 1
            
            if all_keys:
                key_rotator.set_keys(list(all_keys))
                logger.info(f"[Trinity Core] Recovered {len(all_keys)} Gemini keys from DB.")
            
            logger.info(f"[Trinity Core] Hot Reload Cache: {count} profiles loaded (Scalar Projection used).")

        # Zero-Cold-Start Warmups
        try:
            from backend.services.ai_engine.core.encoder_singleton import warmup_encoder
            await _aio.wait_for(warmup_encoder(), timeout=30)
            from backend.services.ai_engine.core.semantic_router import SemanticRouter
            await _aio.wait_for(SemanticRouter().warmup(), timeout=30)
            logger.info("[Trinity Core] AI warmup complete.")
        except Exception as e:
            logger.critical(f"[Trinity Core] Warmup failed: {e}")

        # Start Background Loops
        heartbeat_task = _aio.create_task(_heartbeat_loop())
        purge_task = _aio.create_task(_auto_purge_loop())
        _aio.create_task(content_factory.resume_all())

        yield
    finally:
        if heartbeat_task: heartbeat_task.cancel()
        if purge_task: purge_task.cancel()
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
        except Exception as e: logger.warning(f"[Heartbeat] Scan failed: {e}")
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
