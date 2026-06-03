import asyncio
import logging
from typing import Dict
from arq import Retry
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.alchemy_config import alchemy_config
from backend.database.models.system import UnifiedAgentTask
from backend.services.ai_engine.core.agent_base import AGENT_REGISTRY
from backend.services.event_bus import event_bus
from backend.infra.arq_config import get_redis_settings
from sqlalchemy import update
from datetime import datetime, timezone

# Ensure all operatives are imported so they register themselves (R0.2)
import backend.services.commerce.operatives.support_agent
import backend.services.xohi.creative_studio.operatives.plagiarism_cop
import backend.services.xohi.creative_studio.operatives.seo_analyzer
import backend.services.xohi.creative_studio.operatives.ai_inspector
import backend.services.xohi.creative_studio.operatives.content_enricher
from backend.infra.jobs import cleanup_old_tasks, helen_follow_up_job, helen_self_learning_job, generate_review_kg_job, cleanup_old_notifications
logger = logging.getLogger("arq.worker")

async def run_agent_task(ctx: Dict[str, object], agent_id: str, task_id: str, session_id: str, payload: Dict[str, object]) -> None:
    """
    Elite V2.2: Universal Agent Task Handler (The Brain Worker).
    Runs any registered agent operative in a background process with DB persistence.
    """
    from sqlalchemy import select, update
    from backend.database import current_tenant_id
    from backend.services.ai_engine.core.semantic_cache import semantic_cache

    t0 = datetime.now(timezone.utc)
    job_try = ctx.get('job_try', 1)
    logger.info(f"🧠 [Neural Worker] Starting task {task_id} (Try {job_try}) for agent {agent_id} (S: {session_id})")
    
    session_maker = alchemy_config.create_session_maker()
    token_ctx = None

    try:
        # [R00 - DISPOSE] Check Semantic Cache BEFORE touching heavy resources
        # Elite V5.6 Fix: Do NOT cache stateful conversational agents (support_agent) 
        # because the same payload (e.g. "0949901122") must yield different responses based on DB state.
        cached_res = None
        if agent_id != "support_agent":
            cached_res = await semantic_cache.get_cached_result(agent_id, payload)
            
        if cached_res:
            async with session_maker() as cache_db:
                await cache_db.execute(
                    update(UnifiedAgentTask)
                    .where(UnifiedAgentTask.task_id == task_id)
                    .values(status="DONE", result=cached_res, completed_at=datetime.now(timezone.utc))
                )
                
                if "campaign_id" in payload:
                    from backend.database.repositories import ContentCampaignRepository
                    repo = ContentCampaignRepository(session=cache_db)
                    camp = await repo.get(str(payload["campaign_id"]))
                    if camp:
                        await event_bus.emit("CONTENT_PROGRESS", {
                            "campaign_id": str(camp.id),
                            "user_id": str(camp.user_id),
                            "message": "✅ Đã tải kết quả siêu tốc từ bộ nhớ Neural Cache.",
                            "status": "PROCESSING",
                            "data": {"gold_metadata": dict(camp.gold_metadata or {})},
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                
                await cache_db.commit()
            
            # Emit signals for cached result
            await event_bus.emit("AGENT_TASK_COMPLETED", {"task_id": task_id, "session_id": session_id, "agent_id": agent_id, "status": "DONE"})
            if agent_id == "support_agent":
                await event_bus.emit("SUPPORT_RESPONSE_READY", {
                    "session_id": session_id, 
                    "task_id": task_id, 
                    "reply": cached_res.get("reply"), 
                    "intent": cached_res.get("intent"), 
                    "status": "DONE",
                    "ui_metadata": cached_res.get("ui_metadata"),
                    "metadata": cached_res.get("metadata")
                })
            return

        # 1. Update status to RUNNING in DB and RESTORE TENANT CONTEXT
        async with session_maker() as db:
            stmt = select(UnifiedAgentTask).where(UnifiedAgentTask.task_id == task_id)
            res = await db.execute(stmt)
            task_obj = res.scalar_one_or_none()
            
            if not task_obj:
                logger.error(f"[Worker] Task {task_id} not found in DB.")
                return

            # Standardize Multi-Tenancy (Elite V2.2)
            token_ctx = current_tenant_id.set(task_obj.tenant_id or "default")
            
            task_obj.status = "RUNNING"
            await db.commit()

        # 2. Instantiate the correct operative from the Heritage Registry
        agent_cls = AGENT_REGISTRY.get(agent_id)
        if not agent_cls:
            error_msg = f"Agent {agent_id} not found in registry."
            logger.error(f"[Worker] {error_msg}")
            async with session_maker() as db:
                await db.execute(
                    update(UnifiedAgentTask)
                    .where(UnifiedAgentTask.task_id == task_id)
                    .values(status="FAILED", error=error_msg, completed_at=datetime.now(timezone.utc))
                )
                await db.commit()
            return

        # 3. Create isolated resource lifecycle (R00 - Dispose Protocol)
        async with session_maker() as db:
            agent = agent_cls(agent_id=agent_id)
            
            # Dynamic Schema Mapping (Elite V2.2 Rule R88)
            schema_cls = agent.get_schema()
            if schema_cls:
                request = schema_cls(**payload)
            else:
                request = payload if isinstance(payload, dict) else payload

            # 4. Execute the heavy AI logic
            if hasattr(agent, "process_brain_logic"):
                result = await agent.process_brain_logic(request=request, db=db)
            else:
                result = await agent.chat(request=request, db=db)

            # 5. Save results to DB (Elite V2.2: Pydantic V2 model_dump)
            if hasattr(result, "model_dump"):
                result_data = result.model_dump()
            elif hasattr(result, "dict"):
                result_data = result.dict()
            else:
                result_data = dict(result) if isinstance(result, (dict, list, tuple)) else result
            
            await db.execute(
                update(UnifiedAgentTask)
                .where(UnifiedAgentTask.task_id == task_id)
                .values(status="DONE", result=result_data, completed_at=datetime.now(timezone.utc))
            )

            # [Elite 2026] Cache successful result
            await semantic_cache.set_cached_result(agent_id, payload, result_data)

            await db.commit()

            if "campaign_id" in payload:
                from backend.database.repositories import ContentCampaignRepository
                repo = ContentCampaignRepository(session=db)
                camp = await repo.get(str(payload["campaign_id"]))
                if camp:
                    await event_bus.emit("CONTENT_PROGRESS", {
                        "campaign_id": str(camp.id),
                        "user_id": str(camp.user_id),
                        "message": "✅ Agent Task đã xử lý xong. Đang đồng bộ giao diện...",
                        "status": "PROCESSING",
                        "data": {
                            "gold_metadata": dict(camp.gold_metadata or {})
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

            # 6. Universal Completion Signal (Central Nervous System)
            await event_bus.emit("AGENT_TASK_COMPLETED", {
                "task_id": task_id,
                "session_id": session_id,
                "agent_id": agent_id,
                "status": "DONE"
            })
            
            if agent_id == "support_agent":
                await event_bus.emit("SUPPORT_RESPONSE_READY", {
                    "session_id": session_id,
                    "task_id": task_id,
                    "reply": result_data.get("reply"),
                    "intent": result_data.get("intent"),
                    "status": "DONE",
                    "ui_metadata": result_data.get("ui_metadata"),
                    "metadata": result_data.get("metadata")
                })
            
            duration = (datetime.now(timezone.utc) - t0).total_seconds()
            logger.info(f"✅ [Neural Worker] Task {task_id} completed successfully in {duration:.2f}s.")
            
    except Exception as e:
        logger.error(f"❌ [Worker] Task {task_id} failed during execution: {e}", exc_info=True)
        
        if agent_id == "support_agent":
            # Premium real-time chatbot resilience: Never retry, fall back immediately to keep UI ultra-fast
            fallback_reply = "Dạ Helen chân thành xin lỗi Anh/Chị, hệ thống đang bận xử lý thông tin chuyên sâu. Để không làm gián đoạn trải nghiệm của mình, chuyên viên tư vấn sẽ liên hệ trực tiếp hỗ trợ ngay ạ! 🌸"
            try:
                # Let's extract product slug from payload to generate a highly detailed product fallback
                product_slug = payload.get("product_slug") if isinstance(payload, dict) else getattr(payload, "product_slug", None)
                if product_slug:
                    async with session_maker() as db:
                        cur_settings = {"symbol": "đ", "thousand_separator": ".", "decimal_separator": ",", "code": "VND"}
                        from backend.services.commerce.operatives.support_agent import _fetch_product_context
                        from backend.services.commerce.operatives.handlers.consultant import ConsultantHandler
                        from backend.services.commerce.operatives.handlers.base import SupportContext
                        
                        ctx_text, p_info = await _fetch_product_context(db, product_slug, cur_settings)
                        if p_info:
                            dummy_ctx = SupportContext(
                                db=db, request=None, session_id=session_id, dna=None,
                                product_ctx=ctx_text, history_text="", knowledge_index="",
                                p_info=p_info, cart_text="", order_draft=None,
                                zalo_enabled=False, messenger_enabled=False
                            )
                            consultant = ConsultantHandler()
                            fallback_reply = consultant._generate_db_fallback(dummy_ctx)
            except Exception as fe:
                logger.error(f"[Worker] Failed to generate specialized DB fallback: {fe}")

            try:
                async with session_maker() as done_db:
                    await done_db.execute(
                        update(UnifiedAgentTask)
                        .where(UnifiedAgentTask.task_id == task_id)
                        .values(
                            status="DONE",
                            result={"reply": fallback_reply, "intent": "UNKNOWN", "fallback": True},
                            completed_at=datetime.now(timezone.utc)
                        )
                    )
                    await done_db.commit()
            except Exception as dbe:
                logger.critical(f"💀 [Worker] Could not update support task fallback to DONE: {dbe}")

            await event_bus.emit("AGENT_TASK_COMPLETED", {
                "task_id": task_id,
                "session_id": session_id,
                "agent_id": agent_id,
                "status": "DONE"
            })
            
            await event_bus.emit("SUPPORT_RESPONSE_READY", {
                "session_id": session_id,
                "task_id": task_id,
                "reply": fallback_reply,
                "intent": "UNKNOWN",
                "status": "DONE",
                "ui_metadata": {"fallback": True}
            })
            
            logger.info(f"🛡️ [Worker] Gracefully resolved failed support_agent task {task_id} with premium DB fallback.")
            return

        # Standard Offline Campaign fallback and retry
        try:
            async with session_maker() as fail_db:
                await fail_db.execute(
                    update(UnifiedAgentTask)
                    .where(UnifiedAgentTask.task_id == task_id)
                    .values(
                        status="FAILED", 
                        error=str(e), 
                        completed_at=datetime.now(timezone.utc)
                    )
                )
                await fail_db.commit()
        except Exception as dbe:
            logger.critical(f"💀 [Worker] CRITICAL: Could not update task {task_id} status to FAILED: {dbe}")

        # Emit failure signal
        await event_bus.emit("AGENT_TASK_COMPLETED", {
            "task_id": task_id,
            "session_id": session_id,
            "agent_id": agent_id,
            "status": "FAILED",
            "error": str(e)
        })
        
        # [Elite V2.2] Exponential Backoff for transient Network/API errors
        error_str = str(e).lower()
        if any(trigger in error_str for trigger in ["429", "timeout", "overloaded", "limiter"]):
            # Calc exponential backoff: 30s, 60s, 120s...
            defer_time = 15 * (2 ** (job_try - 1))
            logger.warning(f"🔄 [Worker] Retrying task {task_id} in {defer_time}s due to transient error: {e}")
            raise Retry(defer=defer_time)
    finally:
        if token_ctx:
            current_tenant_id.reset(token_ctx)

async def send_otp_email(ctx: Dict[str, object], email: str, code: str, request_id: str) -> bool:
    """
    Background Task: Sends OTP email via MailService with Live Pulse signals.
    """
    from backend.services.mail_service import mail_service
    from backend.services.event_bus import event_bus
    
    async def emit_progress(msg: str, status: str = "PROCESSING"):
        await event_bus.emit("OTP_UPDATE", {
            "session_id": request_id, 
            "event": "OTP_UPDATE",
            "message": msg,
            "status": status
        })

    await emit_progress("Đã tiếp nhận. Đang khởi tạo kết nối SMTP...")
    
    subject = f"Mã xác nhận osmo: {code}"
    body_text = f"Xin chào,\n\nMã xác nhận của bạn là: {code}\n\nMã này có hiệu lực trong 5 phút. Vui lòng không chia sẻ mã này với bất kỳ ai.\n\nTrân trọng,\nosmo Team"
    
    # Premium Branding HTML
    body_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #f0f0f0;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #ee4d2d; margin: 0;">osmo</h1>
            <p style="color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 2px;">Elite Storefront</p>
        </div>
        <div style="background: #fdf2f0; padding: 30px; text-align: center;">
            <p style="font-size: 16px; color: #333; margin-bottom: 20px;">Mã xác nhận truy cập của bạn là:</p>
            <div style="font-size: 42px; font-weight: 900; color: #ee4d2d; letter-spacing: 10px; margin-bottom: 20px;">{code}</div>
            <p style="font-size: 12px; color: #999;">Mã này có hiệu lực trong 5 phút.</p>
        </div>
        <div style="margin-top: 30px; font-size: 12px; color: #888; text-align: center;">
            <p>Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email.</p>
            <hr style="border: none; border-top: 1px solid #f0f0f0; margin: 20px 0;">
            <p>&copy; 2026 osmo. All rights reserved.</p>
        </div>
    </div>
    """
    
    await emit_progress("Đã sẵn sàng. Đang gửi dữ liệu đến Gmail...")
    
    success = await mail_service.send_email(email, subject, body_text, body_html)
    
    if success:
        await emit_progress("Thành công! Email đã được Google tiếp nhận.", status="DONE")
    else:
        await emit_progress("Thất bại. Không thể kết nối máy chủ gửi thư.", status="FAILED")
        
    return success

async def run_fraud_forensic(ctx: Dict[str, object], click_data: Dict[str, object]) -> None:
    """
    [ELITE V2.2] On-Demand Fraud Forensic Investigator.
    Runs only when explicitly queued, consuming zero CPU when idle.
    """
    from backend.database.alchemy_config import alchemy_config
    from backend.database.models.ads import ClickFraudEvent
    from backend.agents.fraud_investigator import run_forensic_analysis
    from backend.services.ads_protection.ip_intelligence_service import IPIntelligenceService
    from backend.controllers.ads_protection import _hub
    from datetime import datetime, timezone
    from sqlalchemy import update
    
    ip = click_data.get("ip")
    gclid = click_data.get("gclid")
    score = click_data.get("score", 0.0)
    
    if not ip or not gclid:
        logger.warning(f"[Fraud Forensic] Skipping task: Missing critical keys (ip={ip}, gclid={gclid})")
        return
        
    logger.info(f"🕵️ [Agentic On-Demand] Investigating Gray-Zone Click: IP={ip} Score={score}")
    
    ip_svc = IPIntelligenceService()
    session_maker = alchemy_config.create_session_maker()
    
    try:
        async with session_maker() as db:
            agent_result = await run_forensic_analysis(db, ip_svc, click_data)
            if agent_result:
                # Safe SQL Guard: explicit filters to prevent bulk updates
                stmt = update(ClickFraudEvent).where(
                    ClickFraudEvent.gclid == gclid,
                    ClickFraudEvent.ip_address == ip
                ).values(
                    verdict=agent_result.verdict,
                    fraud_score=agent_result.fraud_score,
                    reasoning=getattr(agent_result, 'reasoning', None),
                    updated_at=datetime.now(timezone.utc)
                )
                await db.execute(stmt)
                await db.commit()
                
                if agent_result.verdict == "FRAUD":
                    await _hub.broadcast({
                        "type": "NEW_CLICK",
                        "ip": ip,
                        "score": agent_result.fraud_score,
                        "verdict": agent_result.verdict,
                        "source": "AGENTIC_V3"
                    })
    except Exception as e:
        logger.error(f"❌ [Fraud Forensic] Failed during forensic investigation: {e}", exc_info=True)

async def startup(ctx: Dict[str, object]) -> None:
    logger.info("🚀 [Neural Worker] Arq Worker starting up... Elite V2.2 Protocol Active.")
    # Elite V2.2: Initialize both TrinityBridge AND Encoder in parallel.
    # Worker is a separate process — _shared_encoder is NOT shared with the API container.
    # Without warmup_encoder(), all vector/semantic searches in worker tasks return empty lists.
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    from backend.services.ai_engine.core.encoder_singleton import warmup_encoder
    
    # 🔍 Elite V2.2 Self-Healing: Auto-recovery for stalled tasks
    try:
        session_maker = alchemy_config.create_session_maker()
        async with session_maker() as recovery_db:
            # Mark all PENDING or RUNNING tasks as FAILED on startup since worker was restarted
            res = await recovery_db.execute(
                update(UnifiedAgentTask)
                .where(
                    UnifiedAgentTask.status.in_(["RUNNING", "PENDING"])
                )
                .values(
                    status="FAILED",
                    error="Worker restarted. Task aborted during execution (Self-Healing).",
                    completed_at=datetime.now(timezone.utc)
                )
            )
            await recovery_db.commit()
            if res.rowcount > 0:
                logger.info(f"🛡️ [Self-Healing] Successfully recovered {res.rowcount} orphaned/stalled background tasks.")
    except Exception as se:
        logger.warning(f"⚠️ [Self-Healing] Task auto-recovery skipped during boot: {se}")
 
    await asyncio.gather(
        trinity_bridge.initialize(),
        warmup_encoder()
    )

async def shutdown(ctx: Dict[str, object]) -> None:
    logger.info("[Worker] Arq Worker shutting down.")

from arq import cron

class WorkerSettings:
    """Arq Base Configuration (Elite V2.2)."""
    functions = [run_agent_task, helen_follow_up_job, send_otp_email, run_fraud_forensic, helen_self_learning_job, generate_review_kg_job, cleanup_old_notifications]
    redis_settings = get_redis_settings()
    on_startup = startup
    on_shutdown = shutdown
    # Tuning for 4GB VPS
    max_jobs = 20  
    job_timeout = 300
    keep_result = 3600

class WorkerHighSettings(WorkerSettings):
    """Priority Worker for Helen (Client Support)."""
    queue_name = "high"
    functions = [run_agent_task, helen_follow_up_job, send_otp_email, run_fraud_forensic, helen_self_learning_job, generate_review_kg_job, cleanup_old_notifications]
    redis_settings = get_redis_settings() # Explicitly call again to be safe
    max_jobs = 15

class WorkerDefaultSettings(WorkerSettings):
    """Standard Worker for XoHi (Creative Studio)."""
    queue_name = "default"
    functions = [run_agent_task, helen_follow_up_job, send_otp_email, run_fraud_forensic, helen_self_learning_job, generate_review_kg_job, cleanup_old_notifications]
    redis_settings = get_redis_settings() # Explicitly call again to be safe
    max_jobs = 5
    cron_jobs = [
        # Schedule self-learning scan at 2:00 AM every day
        cron(helen_self_learning_job, hour=2, minute=0),
        # Schedule cleanup at 3:00 AM every day
        cron(cleanup_old_tasks, hour=3, minute=0),
        # Schedule notification retention cleanup at 4:00 AM every day
        cron(cleanup_old_notifications, hour=4, minute=0)
    ]

