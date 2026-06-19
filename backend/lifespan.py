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
from backend.services.viral_share_service import viral_share_service as _viral_svc

logger = logging.getLogger("api-gateway")


def _setup_seo_subscriptions() -> None:
    """
    SEO Pillar & Cluster — Event Bus hooks.
    Listens for ARTICLE_PUBLISHED, PRODUCT_PUBLISHED, ARTICLE_UNPUBLISHED, and PRODUCT_UNPUBLISHED events
    and queues jobs via ARQ to the high-priority queue for immediate background processing.
    """
    import asyncio
    from backend.database import current_tenant_id

    async def _on_entity_published(payload: dict) -> None:
        try:
            from backend.infra.arq_config import get_redis_settings
            from arq import create_pool
            entity_type = payload.get("entity_type", "article")
            redis = await create_pool(get_redis_settings())
            tenant_id = str(payload.get("tenant_id") or current_tenant_id.get() or "default")
            entity_id = str(payload.get("entity_id", ""))

            await redis.enqueue_job(
                "seo_match_entity_job",
                entity_type=entity_type,
                entity_id=entity_id,
                title=str(payload.get("title", "")),
                excerpt=str(payload.get("excerpt", ""))[:400],
                slug=str(payload.get("slug", "")),
                tenant_id=tenant_id,
                _queue_name="high",
            )
            logger.info(f"[SEO] Queued seo_match_entity_job (high queue) for {entity_type}:{entity_id}")

            # Auto-trigger contextual link analysis for articles (deferred 30s to allow match job to complete)
            if entity_type.lower() == "article":
                from datetime import timedelta
                await redis.enqueue_job(
                    "seo_contextual_link_job",
                    article_id=entity_id,
                    tenant_id=tenant_id,
                    _queue_name="high",
                    _defer_by=timedelta(seconds=30),
                )
                logger.info(f"[SEO] Queued seo_contextual_link_job (high queue, deferred 30s) for article:{entity_id}")
        except Exception as e:
            logger.warning(f"[SEO] Failed to queue seo jobs: {e}")

    async def _on_entity_unpublished(payload: dict) -> None:
        try:
            from backend.infra.arq_config import get_redis_settings
            from arq import create_pool
            entity_type = payload.get("entity_type", "article")
            redis = await create_pool(get_redis_settings())
            await redis.enqueue_job(
                "seo_unmatch_entity_job",
                entity_type=entity_type,
                entity_id=str(payload.get("entity_id", "")),
                tenant_id=str(payload.get("tenant_id") or current_tenant_id.get() or "default"),
                _queue_name="high",
            )
            logger.info(f"[SEO] Queued seo_unmatch_entity_job (high queue) for {entity_type}:{payload.get('entity_id')}")
        except Exception as e:
            logger.warning(f"[SEO] Failed to queue seo_unmatch_entity_job: {e}")

    event_bus.subscribe("ARTICLE_PUBLISHED", _on_entity_published)
    event_bus.subscribe("PRODUCT_PUBLISHED", _on_entity_published)
    event_bus.subscribe("ARTICLE_UNPUBLISHED", _on_entity_unpublished)
    event_bus.subscribe("PRODUCT_UNPUBLISHED", _on_entity_unpublished)
    logger.info("[SEO] Event Bus subscriptions registered (PUBLISHED & UNPUBLISHED for ARTICLE & PRODUCT)")

@asynccontextmanager
async def lifespan(app: Litestar):
    # 1. Start Infrastructure & AI Core (V76.2)
    setup_subscriptions()
    _setup_seo_subscriptions()
    
    # [Elite V2.2] Test Environment Optimization: Skip heavy AI & DB pre-load
    if os.getenv("FAST_PLATFORM_TEST") == "true":
        logger.info("🧪 [Trinity Core] Test environment detected. Skipping heavy AI/DB warmup.")
        await event_bus.start()
        yield
        await event_bus.stop()
        return

    await _aio.gather(
        event_bus.start(),
        trinity_bridge.initialize()
    )
    logger.info("🧠 [Trinity Core] API Gateway loaded. Encoder deferred to on-demand lazy initialization.")

    # Bind shared Redis client to viral_share_service (lazy init pattern)
    _viral_svc._redis = xohi_memory.client
    logger.info("🔐 [ViralEngine] Redis bound to ViralShareService.")

    gc_task = None
    heartbeat_task = None
    purge_task = None
    media_cleanup_task = None
    resume_task = None
    autopilot_task = None
    model_health_task = None

    try:
        # 2. Pre-load Data into Hot Cache (R76: Scalar Projection Optimization)
        async with alchemy_config.create_session_maker()() as session:
            # [Elite V2.2] Auto-Sync RBAC on Boot
            from backend.services.user_service import user_service
            await user_service.sync_rbac(session)
            await session.commit()

            # Auto-Migrate SEO fields on Boot
            try:
                from sqlalchemy import text
                await session.execute(text("ALTER TABLE seo_contextual_links ADD COLUMN IF NOT EXISTS link_title VARCHAR(255);"))
                await session.execute(text("ALTER TABLE seo_contextual_links ADD COLUMN IF NOT EXISTS link_target VARCHAR(20);"))
                await session.commit()
                logger.info("✓ [SEO Auto-Migrate] Added link_title and link_target columns if they did not exist.")
            except Exception as migrate_ex:
                logger.warning(f"⚠️ [SEO Auto-Migrate] Failed to run alter table: {migrate_ex}")
                await session.rollback()

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
        model_health_task = _aio.create_task(_model_health_sync_loop()) # Periodic LLM Tier Watchdog

        yield
    finally:
        if gc_task: gc_task.cancel()
        if heartbeat_task: heartbeat_task.cancel()
        if purge_task: purge_task.cancel()
        if media_cleanup_task: media_cleanup_task.cancel()
        if resume_task: resume_task.cancel()
        if autopilot_task: autopilot_task.cancel()
        if model_health_task: model_health_task.cancel()
        await event_bus.stop()
        await SharedHttpClient.close()
        logger.info("[Trinity Core] Shutdown complete.")

async def _heartbeat_loop():
    from backend.services.anomaly_detector import AnomalyDetector
    detector = AnomalyDetector()
    interval = int(os.getenv("ANOMALY_SCAN_INTERVAL", "120"))
    await _aio.sleep(60)
    while True:
        try:
            await detector.scan()
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
    import json
    from backend.database.models import Appointment, Article
    from backend.services.xohi_memory import xohi_memory
    
    # Wait for system to stabilize
    await _aio.sleep(30)
    
    while True:
        try:
            # Check if current time is between configured hours (Vietnamese timezone UTC+7)
            from datetime import timezone, timedelta
            
            # Fetch config from Redis with fallback
            start_hour_str = await xohi_memory.client.get("system:autopilot:scan_start_hour")
            end_hour_str = await xohi_memory.client.get("system:autopilot:scan_end_hour")
            
            start_hour = int(start_hour_str) if start_hour_str else 2
            end_hour = int(end_hour_str) if end_hour_str else 4
            
            tz_vn = timezone(timedelta(hours=7))
            now_vn = datetime.now(tz_vn)
            
            if start_hour <= end_hour:
                is_active_hour = start_hour <= now_vn.hour < end_hour
            else:  # Overnight span, e.g. 22:00 to 02:00
                is_active_hour = now_vn.hour >= start_hour or now_vn.hour < end_hour
                
            if not is_active_hour:
                await _aio.sleep(60)
                continue

            now = datetime.now(timezone.utc)
            async with alchemy_config.create_session_maker()() as session:
                # 1. Fetch due appointments (UPCOMING and start_time <= now)
                # [P1-FIX] Thêm deleted_at filter để tránh scan soft-deleted rows
                stmt = select(Appointment).where(
                    Appointment.status == "UPCOMING",
                    Appointment.start_time <= now,
                    Appointment.deleted_at == None,
                )
                result = await session.execute(stmt)
                due_apps = result.scalars().all()
                
                if due_apps:
                    logger.info(f"🚀 [Autopilot] Found {len(due_apps)} due appointments. Processing...")
                
                for app in due_apps:
                    campaign_id = app.campaign_id
                    metadata = app.metadata_json or {}
                    
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except Exception:
                            metadata = {}
                            
                    action = metadata.get("action")
                    article_id = metadata.get("article_id")
                    
                    # Process based on type
                    if action == "publish_article" and article_id:
                        try:
                            stmt_article = select(Article).where(Article.id == article_id)
                            article_result = await session.execute(stmt_article)
                            article = article_result.scalar_one_or_none()
                            
                            if article:
                                article.status = "PUBLISHED"
                                logger.info(f"📰 [Autopilot] Published article: '{article.title}' (ID: {article_id})")
                            else:
                                logger.warning(f"⚠️ [Autopilot] Article ID {article_id} not found for appointment {app.id}")
                        except Exception as ex:
                            logger.error(f"❌ [Autopilot] Failed to publish article {article_id}: {ex}")
                    elif campaign_id:
                        # Trigger the Factory (Starting from Step 1)
                        # We use create_task to ensure non-blocking execution of the pipeline
                        _aio.create_task(content_factory.engine.trigger_step(campaign_id, force_step=1))
                    
                    # Handle Recurrence or Completion
                    if app.recurring_type and app.recurring_type != "none":
                        # Reschedule for next occurrence
                        delta = timedelta(days=1)
                        if app.recurring_type == "weekly": delta = timedelta(days=7)
                        elif app.recurring_type == "monthly": delta = timedelta(days=30)
                        
                        app.start_time += delta
                        app.end_time += delta
                        logger.info(f"📅 [Autopilot] Rescheduled job {app.id} for {app.start_time}")
                    else:
                        app.status = "COMPLETED"
                        logger.info(f"✅ [Autopilot] Job completed for appointment {app.id}")
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"❌ [Autopilot Loop] Fatal error: {e}")
            
        # Scan frequency: 1 minute for precision
        await _aio.sleep(60)


async def _model_health_sync_loop():
    """
    [Elite Engine] Periodic Model Integrity Watchdog.
    Runs every 12 hours. Performs lightweight background connectivity checks (ping)
    for all active models in the waterfall pool. Instantly blacklists and purges
    any model returning 404/400 (deprecated/killed by Google).
    """
    import httpx
    # Chờ 3 phút sau khởi động để tránh dồn tải lúc boot
    await _aio.sleep(180)
    while True:
        try:
            logger.info("🛰️ [ModelWatchdog] Running periodic model health synchronization...")
            # 1. Fetch all discovered & config models to test
            discovered = await trinity_bridge.models_helper.discover_available()
            
            # Extract key for probing
            try:
                # Use gemini-2.0-flash to get key
                key = await key_rotator.get_key(model_name="gemini-2.0-flash")
            except Exception:
                logger.warning("[ModelWatchdog] No valid keys available for testing models.")
                await _aio.sleep(3600) # Thử lại sau 1 tiếng
                continue
                
            if not key:
                await _aio.sleep(3600)
                continue
                
            async with httpx.AsyncClient(timeout=10.0) as client:
                for model in list(discovered):
                    # Skip statically blacklisted ones
                    if trinity_bridge.models_helper.is_blacklisted(model):
                        continue
                        
                    # Connectivity check
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                    try:
                        resp = await client.post(url, json={"contents": [{"parts":[{"text": "ping"}]}]}, timeout=5.0)
                        
                        # 404 Model Not Found or 400 Bad Request if model is deleted/deprecated
                        if resp.status_code in [400, 404]:
                            logger.error(f"🚨 [ModelWatchdog] Model {model} returned HTTP {resp.status_code}. Deprecation detected!")
                            await trinity_bridge.models_helper.add_to_persistent_blacklist(model, reason=f"HTTP_{resp.status_code}")
                            
                    except httpx.HTTPStatusError as hse:
                        if hse.response.status_code in [400, 404]:
                            logger.error(f"🚨 [ModelWatchdog] Model {model} failed with {hse.response.status_code}. Blacklisting...")
                            await trinity_bridge.models_helper.add_to_persistent_blacklist(model, reason=f"HTTP_{hse.response.status_code}")
                    except Exception as e:
                        # Timeout or general networking failure — do NOT blacklist immediately to avoid false positives
                        logger.debug(f"[ModelWatchdog] Lightweight ping failed for {model}: {e}")
                        
                    # Tránh gửi request dồn dập
                    await _aio.sleep(2.0)
                    
            logger.info("✅ [ModelWatchdog] Periodic model integrity check completed.")
        except Exception as e:
            logger.exception(f"❌ [ModelWatchdog] Loop cycle failed: {e}")
            
        # Chạy lại sau mỗi 12 tiếng (43200 giây)
        await _aio.sleep(43200)
