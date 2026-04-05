import os
import logging
import asyncio as _aio
import gc
import psutil
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, delete as sql_delete
from litestar import Litestar

from backend.database import alchemy_config
from backend.database.models import VoiceProfile, ChatMessage
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.services.xohi_memory import xohi_memory
from backend.utils.security import GeminiSecurity
from backend.utils.text import normalize_vn
from backend.services.event_bus import event_bus
from backend.services.xohi_responder import setup_subscriptions
from backend.services.commerce import order_notifier
from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.http_client import SharedHttpClient
from backend.services.ai_engine.core.encoder_singleton import warmup_encoder

logger = logging.getLogger("api-gateway")

@asynccontextmanager
async def lifespan(app: Litestar):
    # 1. Start Infrastructure & AI Core (V76.2)
    setup_subscriptions()
    
    # [Elite V2.2] Test Environment Optimization: Skip heavy AI & DB pre-load
    if os.getenv("FAST_PLATFORM_TEST") == "true":
        logger.info("🧪 [Trinity Core] Test environment detected. Skipping heavy AI/DB warmup.")
        await event_bus.start()
        yield
        await event_bus.stop()
        return

    await _aio.gather(
        event_bus.start(),
        trinity_bridge.initialize(),
        warmup_encoder()
    )

    gc_task = None
    heartbeat_task = None
    purge_task = None
    media_cleanup_task = None
    resume_task = None
    autopilot_task = None

    try:
        # 2. Pre-load Data into Hot Cache (R76: Scalar Projection Optimization)
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
            logger.info(f"🔑 [Trinity Core] Keys hot-reloaded ({key_rotator.get_count()} keys).")
    except Exception as e:
        logger.error(f"❌ [Trinity Core] Startup data load failed: {e}")

    try:
        # 3. [GHOST MODE] Start GC Watchdog first
        gc.set_threshold(700, 10, 5) # Chống rác tích tụ lâu
        gc_task = _aio.create_task(_gc_watchdog_loop())

        # 4. Start Background Loops
        heartbeat_task = _aio.create_task(_heartbeat_loop())
        purge_task = _aio.create_task(_auto_purge_loop())
        media_cleanup_task = _aio.create_task(_media_cleanup_loop())
        resume_task = _aio.create_task(content_factory.resume_all())
        autopilot_task = _aio.create_task(_autopilot_scheduler_loop()) # CNS V82.1: Neural Autopilot Engine

        yield
    finally:
        if gc_task: gc_task.cancel()
        if heartbeat_task: heartbeat_task.cancel()
        if purge_task: purge_task.cancel()
        if media_cleanup_task: media_cleanup_task.cancel()
        if resume_task: resume_task.cancel()
        if autopilot_task: autopilot_task.cancel()
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
    from backend.services.media.media_service import media_service
    from backend.database.repositories import MediaRegistryRepository
    from backend.database import alchemy_config

    # Chờ 10p sau khi khởi động để tránh làm nặng hệ thống lúc boot
    await _aio.sleep(600)
    while True:
        try:
            # 1. Dọn dẹp file tạm (ZIP/Cache) và tài nguyên đã xóa mềm > 30 ngày
            await media_service.cleanup_temp_files()

            # 2. Elite V2.2: Dọn dẹp tài nguyên mồ côi (không có liên kết) > 24h
            async with alchemy_config.create_session_maker()() as session:
                repo = MediaRegistryRepository(session=session)
                await media_service.cleanup_orphaned_assets(repo)

        except Exception as e:
            logger.warning(f"[MediaCleanup] Cycle failed: {e}")
        # 12 giờ = 43200 giây
        await _aio.sleep(43200)

async def _gc_watchdog_loop():
    """
    [GHOST MODE] Vệ binh giải phóng RAM.
    Theo dõi mức độ sử dụng RAM và chủ động gọi bộ dọn rác (GC) 
    khi có dấu hiệu RAM bị chiếm dụng bất thường hoặc sau chu kỳ 10 phút.
    """
    process = psutil.Process(os.getpid())
    while True:
        try:
            # 1. Định kỳ 10 phút dọn rác một lần bất kể trạng thái
            await _aio.sleep(600) 
            
            ram_mb = process.memory_info().rss / (1024 * 1024)
            # Threshold adjusted to 1.2GB (V2.2: Accommodates fastembed + Litestar)
            if ram_mb > 1200:
                logger.warning(f"[GhostMode] RAM usage high ({ram_mb:.1f}MB). Forcing aggressive GC...")
                gc.collect(generation=2) # Dọn rác ở tầng sâu nhất
            elif ram_mb > 800:
                gc.collect() # Dọn rác thông thường khi vượt 800MB
                
        except Exception as e:
            logger.error(f"[GhostMode] Watchdog error: {e}")

async def _autopilot_scheduler_loop():
    """
    [Elite Engine] CNS V82.1: Neural Autopilot Coordinator.
    Scans for due appointments and triggers automated content factory pipelines.
    """
    from backend.database.models import Appointment
    from backend.database.repositories import ContentCampaignRepository
    
    # Wait for system to stabilize
    await _aio.sleep(30)
    
    while True:
        try:
            now = datetime.now(timezone.utc)
            async with alchemy_config.create_session_maker()() as session:
                # 1. Fetch due appointments
                stmt = select(Appointment).where(
                    Appointment.status == "UPCOMING",
                    Appointment.start_time <= now,
                    Appointment.campaign_id.is_not(None)
                )
                result = await session.execute(stmt)
                due_apps = result.scalars().all()
                
                if due_apps:
                    logger.info(f"🚀 [Autopilot] Found {len(due_apps)} due appointments. Launching Neural Factory...")
                
                for app in due_apps:
                    campaign_id = app.campaign_id
                    
                    # 2. Trigger the Factory (Starting from Step 1)
                    # We use create_task to ensure non-blocking execution of the pipeline
                    _aio.create_task(content_factory.engine.trigger_step(campaign_id, force_step=1))
                    
                    # 3. Handle Recurrence or Completion
                    if app.recurring_type and app.recurring_type != "none":
                        # Reschedule for next occurrence
                        delta = timedelta(days=1)
                        if app.recurring_type == "weekly": delta = timedelta(days=7)
                        elif app.recurring_type == "monthly": delta = timedelta(days=30)
                        
                        app.start_time += delta
                        app.end_time += delta
                        logger.info(f"📅 [Autopilot] Rescheduled campaign {campaign_id} for {app.start_time}")
                    else:
                        app.status = "COMPLETED"
                        logger.info(f"✅ [Autopilot] Job completed for {campaign_id}")
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"❌ [Autopilot Loop] Fatal error: {e}")
            
        # Scan frequency: 1 minute for precision
        await _aio.sleep(60)
