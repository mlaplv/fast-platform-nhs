import logging
import uuid
import json
import asyncio
from typing import Dict, Union, Optional
from sqlalchemy import text
from backend.services.event_bus import event_bus
from backend.database import alchemy_config
from backend.services.anti_spam import anti_spam_service as anti_spam
from backend.services.xohi_memory import xohi_memory
from backend.services.media.media_responder import media_responder

logger = logging.getLogger("api-gateway")

class XoHiResponder:
    def __init__(self):
        self.session_maker = alchemy_config.create_session_maker()

    async def handle_order_created(self, payload: Dict[str, object]):
        """Callback for ORDER_CREATED event. Marks spam and notifies admins."""
        order_id = str(payload.get("id", ""))
        
        # Redis-based Global Deduplication Gate for ORDER_CREATED (SETNX 10s)
        from backend.services.xohi_memory import xohi_memory
        if order_id and xohi_memory._use_redis and xohi_memory.client:
            dedup_key = f"dedup:order_created:{order_id}"
            is_new = await xohi_memory.client.set(dedup_key, "1", ex=10, nx=True)
            if not is_new:
                logger.info(f"[XoHiResponder] Duplicate ORDER_CREATED ignored: {order_id}")
                return

        ip = str(payload.get("ip", "unknown"))
        ua = str(payload.get("user_agent", "unknown"))
        tenant_id = str(payload.get("tenant_id", "default"))
        total_amount = float(payload.get("total_amount", 0.0))
        phone = str(payload.get("phone", "unspecified"))
        address = str(payload.get("address", ""))

        campaign_flag = await xohi_memory.client.get("system:campaign_mode") if xohi_memory._use_redis else None
        is_campaign_mode = (campaign_flag == b"1")

        is_spam, reason, score, device_hash = await anti_spam.check_order_spam(
            ip, ua, tenant_id,
            {"total": total_amount, "phone": phone, "address": address, "items": payload.get("items", [])},
            is_campaign_mode=is_campaign_mode
        )

        async with self.session_maker() as session:
            try:
                if is_spam:
                    logger.warning(f"[Anti-Spam Shield] Detect SPAM order {order_id}: {reason}")
                    await session.execute(
                        text("UPDATE orders SET is_spam = true, spam_score = :score, device_hash = :fp, spam_reason = :reason WHERE id = :id"),
                        {"score": score, "id": order_id, "fp": device_hash, "reason": reason}
                    )

                customer = str(payload.get("customer", "Khách lạ"))
                msg = f"Đơn hàng mới từ {customer} (SĐT: {phone}, ID: {order_id[:8]}) trị giá {total_amount:,.0f}đ."
                
                from backend.schemas.signal import SignalSchema, SignalSeverity
                from backend.services.signal_center import signal_center
                
                severity = SignalSeverity.ACTION
                if is_spam:
                    if score >= 90:
                        severity = SignalSeverity.CRITICAL
                        msg = f"🚨 RED ALERT: Phát hiện tấn công Click-Fraud cực mạnh! Đơn {order_id[:8]} từ {customer} (SĐT: {phone}) trị giá {total_amount:,.0f}đ đã bị cô lập hoàn toàn. Lý do: {reason}"
                    else:
                        severity = SignalSeverity.ACTION
                        msg = f"🚩 CẢNH BÁO SPAM: Đơn hàng mới từ {customer} (SĐT: {phone}, ID: {order_id[:8]}) trị giá {total_amount:,.0f}đ - {reason}"

                # Elite V2.2: Universal Signal Dispatch (Persistence managed by SignalCenter)
                await signal_center.dispatch(
                    user_id="user_admin", # Notify admin pool (mlap)
                    signal=SignalSchema(
                        message=msg,
                        severity=severity,
                        signal_type="SECURITY" if is_spam else "ORDER",
                        payload={"order_id": order_id, "is_spam": is_spam, "score": score},
                        persist=True if not is_spam else None 
                    ),
                    db_session=session,
                    tenant_id=tenant_id
                )

                logger.info(f"[XoHiResponder] Handled ORDER_CREATED: {order_id} (is_spam={is_spam})")
            except Exception as e:
                await session.rollback()
                logger.error(f"[XoHiResponder] Atomic Order Processing failed: {e}")

    async def handle_order_cancelled(self, payload: Dict[str, object]):
        """Callback for ORDER_CANCELLED event."""
        order_id = str(payload.get("id", ""))
        
        # Redis-based Global Deduplication Gate for ORDER_CANCELLED (SETNX 10s)
        from backend.services.xohi_memory import xohi_memory
        if order_id and xohi_memory._use_redis and xohi_memory.client:
            dedup_key = f"dedup:order_cancelled:{order_id}"
            is_new = await xohi_memory.client.set(dedup_key, "1", ex=10, nx=True)
            if not is_new:
                logger.info(f"[XoHiResponder] Duplicate ORDER_CANCELLED ignored: {order_id}")
                return

        reason = str(payload.get("reason", "Không rõ lý do"))
        tenant_id = str(payload.get("tenant_id", "default"))
        msg = f"Đơn hàng {order_id[:8]} đã bị HỦY bởi khách hàng. Lý do: {reason}"

        from backend.schemas.signal import SignalSchema, SignalSeverity
        from backend.services.signal_center import signal_center

        async with self.session_maker() as session:
            try:
                # R102: Handle CTV commission rollback and penalty x2 shipping fee on order cancellation
                try:
                    from backend.services.ctv_service import CtvService
                    await CtvService.cancel_commission(session, order_id)
                except Exception as ex:
                    logger.error(f"[CTV-PENALTY] Failed to process commission rollback for cancelled order {order_id}: {ex}")

                await signal_center.dispatch(
                    user_id="user_admin",
                    signal=SignalSchema(
                        message=msg,
                        severity=SignalSeverity.ACTION,
                        signal_type="ORDER_CANCEL",
                        payload={"order_id": order_id, "reason": reason}
                    ),
                    db_session=session,
                    tenant_id=tenant_id
                )
                logger.info(f"[XoHiResponder] Handled ORDER_CANCELLED: {order_id}")
            except Exception as e:
                await session.rollback()
                logger.error(f"[XoHiResponder] Order Cancellation log failed: {e}")

    async def handle_content_step_completed(self, payload: Dict[str, object]):
        """Callback for CONTENT_STEP_COMPLETED event."""
        campaign_id = payload.get("campaign_id")
        user_id = payload.get("user_id")
        step = payload.get("step")
        status = payload.get("status")
        
        # Redis-based Global Deduplication Gate for CONTENT_STEP_COMPLETED (SETNX 10s)
        from backend.services.xohi_memory import xohi_memory
        if campaign_id and step is not None and xohi_memory._use_redis and xohi_memory.client:
            dedup_key = f"dedup:content_step:{campaign_id}:{step}:{status}"
            is_new = await xohi_memory.client.set(dedup_key, "1", ex=10, nx=True)
            if not is_new:
                logger.info(f"[XoHiResponder] Duplicate CONTENT_STEP_COMPLETED ignored: {campaign_id}:{step}:{status}")
                return

        tenant_id = payload.get("tenant_id", "default")

        msg = f"[Content] Hoàn thành Bước {step}. Đang chờ sếp duyệt."
        if status == "COMPLETED" and step == 6:
            msg = "🎉 Chúc mừng sếp! Bài viết sáng tạo đã được xuất bản thành công vào mục Bài viết. Em đã dọn dẹp bộ nhớ để hệ thống luôn mượt mà ạ!"
        elif step == 2: msg = f"[Content] Đã tìm xong bộ ảnh (Bước 2). Mời sếp chọn."
        elif step == 3: msg = f"[Content] Đàn ý Bước 3 đã sẵn sàng."
        elif step == 4: msg = f"[Content] Bản thảo Bước 4 đã hoàn tất."
        elif step == 6: msg = f"✨ Bài viết đã hoàn thành 6 bước. Sẵn sàng xuất bản!"

        try:
            async with self.session_maker() as session:
                content_payload = {
                    "text": msg, "category": "CONTENT_CREATE",
                    "campaign_id": campaign_id, "step": step, "status": status,
                }

                # UPSERT logic
                result = await session.execute(
                    text("""
                        SELECT id FROM chat_messages
                        WHERE session_id = 'account' AND user_id = :uid
                        AND content->>'category' = 'CONTENT_CREATE'
                        AND content->>'campaign_id' = :cid
                        AND content->>'step' = :step
                        ORDER BY created_at DESC LIMIT 1
                    """),
                    {"uid": user_id, "cid": campaign_id, "step": str(step)}
                )
                existing_row = result.fetchone()

                if existing_row:
                    await session.execute(
                        text("UPDATE chat_messages SET content = :content, updated_at = NOW() WHERE id = :id"),
                        {"content": json.dumps(content_payload), "id": existing_row[0]}
                    )
                else:
                    await session.execute(
                        text("""
                            INSERT INTO chat_messages (id, session_id, user_id, role, content, modality, tenant_id, created_at, updated_at)
                            VALUES (:id, 'account', :uid, 'assistant', :content, 'text', :tid, NOW(), NOW())
                        """),
                        {"id": str(uuid.uuid4()), "uid": user_id, "content": json.dumps(content_payload), "tid": tenant_id}
                    )
                await session.commit()
                logger.info(f"[XoHiResponder] UPSERT Step {step} for campaign {campaign_id}")
                
                # Elite V2.2: Dispatch Creative Studio status to Central Nervous System (SSE + DB)
                from backend.schemas.signal import SignalSchema, SignalSeverity
                from backend.services.signal_center import signal_center
                
                await signal_center.dispatch(
                    user_id="user_admin",
                    signal=SignalSchema(
                        message=msg,
                        severity=SignalSeverity.ACTION,
                        signal_type="CONTENT_CREATE",
                        payload={"campaign_id": campaign_id, "step": step, "status": status},
                        persist=True
                    ),
                    tenant_id=tenant_id
                )
        except Exception as e:
            logger.error(f"[XoHiResponder] Content log persistence/signal dispatch failed: {e}")

    async def handle_content_progress(self, payload: Dict[str, object]):
        """Callback for CONTENT_PROGRESS event. Progress is ephemeral — no DB write."""
        campaign_id = payload.get("campaign_id")
        step = payload.get("step")
        msg = payload.get("message", "")
        logger.debug(f"[XoHiResponder] Progress (ephemeral): campaign={campaign_id} step={step} msg={msg[:60]}")

    async def handle_media_uploaded(self, payload: Dict[str, object]):
        """Callback for MEDIA_UPLOADED event. Triggers AI analysis if enabled."""
        asset_id = payload.get("id")
        campaign_id = payload.get("campaign_id")
        if not asset_id:
            return

        # R107: AI Vision Toggle — default OFF. Check Redis flag before running.
        try:
            from backend.services.xohi_memory import xohi_memory
            enabled = await xohi_memory.client.get("ai:vision:enabled") if xohi_memory._use_redis else None
            if enabled != "1":
                logger.debug(f"[XoHiResponder] AI Vision is OFF — using heuristic analysis for asset {asset_id}")
                from backend.services.xohi.creative_studio.operatives.media_analyst import MediaAnalyst
                analyst = MediaAnalyst()
                asyncio.create_task(analyst.heuristic_analysis(asset_id))
                return
        except Exception as e:
            logger.warning(f"[XoHiResponder] Could not check AI Vision flag: {e}. Skipping analysis.")
            return

        # R106: Check content_mode to bypass AI if in 'normal' mode (Sếp Elite R00)
        if campaign_id:
            try:
                async with self.session_maker() as session:
                    from backend.database.models import ContentCampaign
                    from sqlalchemy import select
                    stmt = select(ContentCampaign.creation_config).where(ContentCampaign.id == campaign_id)
                    result = await session.execute(stmt)
                    config = result.scalar()
                    if config and config.get("content_mode") == "normal":
                        logger.info(f"[XoHiResponder] Bypassing AI Analysis for asset {asset_id} (Normal Mode)")
                        return
            except Exception as e:
                logger.error(f"[XoHiResponder] Failed to check campaign mode for bypass: {e}")

        from backend.services.xohi.creative_studio.operatives.media_analyst import MediaAnalyst
        analyst = MediaAnalyst()
        # Chạy phân tích trong background (Non-blocking)
        asyncio.create_task(analyst.process_registry_entry(asset_id))
        logger.info(f"[XoHiResponder] Triggered AI Analysis for asset: {asset_id}")

    async def handle_system_signal(self, payload: Dict[str, object]):
        """Subscriber callback for SYSTEM_SIGNAL events to route to Telegram (Elite V2.2)."""
        try:
            severity = str(payload.get("severity", "INFO"))
            if severity not in ["CRITICAL", "ACTION"]:
                return  # Noise-gate: Bypassed INFO/PROGRESS noise in Telegram channel

            msg = str(payload.get("message", ""))
            alert_type = str(payload.get("signal_type", "SYSTEM")).upper()
            
            # Format high-quality, professional HTML messages
            status_icon = "🚨" if severity == "CRITICAL" else "🔔"
            telegram_msg = (
                f"{status_icon} <b>[FAST-PLATFORM ALERTS - {alert_type}]</b>\n"
                f"────────────────\n"
                f"{msg}\n"
                f"────────────────\n"
                f"🕒 <i>Time: {payload.get('timestamp')}</i>"
            )
            
            from backend.services.telegram_service import telegram_service
            # Offload Telegram dispatch entirely into background task
            asyncio.create_task(telegram_service.send_alert(telegram_msg))
        except Exception as e:
            logger.error(f"❌ [XoHiResponder] Telegram alert forwarding failed: {e}")

    async def handle_support_inbox_update(self, payload: Dict[str, object]):
        """Subscriber callback to route client chat messages to Telegram (Elite V2.2)."""
        try:
            from datetime import datetime, timezone
            # We only alert on USER messages to avoid mirroring bot/admin replies back to Telegram
            role = payload.get("role")
            if role != "user":
                return

            session_id = payload.get("session_id")
            raw_message = str(payload.get("message", ""))
            
            # Bulletproof prompt instruction stripping for safety (Elite V2.2) thưa sếp
            def clean_prompt_message(msg: str) -> str:
                if not msg:
                    return ""
                msg_lower = msg.lower()
                if "[system_consult]" in msg:
                    return "Tư vấn chuyên sâu về sản phẩm"
                if "[system_skin_barrier]" in msg:
                    return "Đánh giá loại da và độ phù hợp sản phẩm"
                if "[system_checkin]" in msg:
                    return "Thực hiện điểm danh hàng ngày"
                if any(k in msg_lower for k in ["vui lòng đóng vai", "bạn là helen", "system prompt", "chỉ thị:", "prompt:", "khung hướng dẫn:"]):
                    return "Yêu cầu tư vấn thông minh"
                if len(msg) > 200 and any(k in msg_lower for k in ["skin_profile", "loại da", "chăm sóc da", "phân tích"]):
                    return "Gửi hồ sơ phân tích da và yêu cầu tư vấn"
                return msg

            message = clean_prompt_message(raw_message)
            
            # Skip empty or revoked messages
            if not message or payload.get("is_revoked"):
                return

            # Redis-based Global Deduplication Gate (SETNX with 10s TTL)
            from backend.services.xohi_memory import xohi_memory
            if xohi_memory._use_redis and xohi_memory.client:
                import hashlib
                payload_str = f"support_inbox:{session_id}:{message}"
                msg_hash = hashlib.md5(payload_str.encode("utf-8")).hexdigest()
                dedup_key = f"dedup:support_inbox:{msg_hash}"
                is_new = await xohi_memory.client.set(dedup_key, "1", ex=10, nx=True)
                if not is_new:
                    logger.info(f"[XoHiResponder] Duplicate support inbox update event ignored: {session_id}")
                    return
                
            # Formatting high-quality, professional HTML messages
            telegram_msg = (
                f"💬 <b>[HỘI THOẠI MỚI - KHÁCH CHAT]</b>\n"
                f"────────────────\n"
                f"👤 <b>Session:</b> <code>{session_id[:8]}</code>\n"
                f"💬 <b>Message:</b> {message}\n"
                f"────────────────\n"
                f"🕒 <i>Time: {datetime.now(timezone.utc).isoformat()}</i>"
            )
            
            from backend.services.telegram_service import telegram_service
            # Offload Telegram dispatch entirely into background task
            asyncio.create_task(telegram_service.send_alert(telegram_msg))

            # Elite V2.2: Dispatch signal to Central Nervous System (SSE + DB)
            from backend.schemas.signal import SignalSchema, SignalSeverity
            from backend.services.signal_center import signal_center
            
            asyncio.create_task(
                signal_center.dispatch(
                    user_id="user_admin",
                    signal=SignalSchema(
                        message=f"💬 Khách chat mới (Session: {session_id[:8]}): {message}",
                        severity=SignalSeverity.ACTION,
                        signal_type="CHAT",
                        payload={"session_id": session_id, "message": message},
                        persist=True
                    )
                )
            )
        except Exception as e:
            logger.error(f"❌ [XoHiResponder] Telegram chat/signal alert forwarding failed: {e}")


# Initialize and subscribe
xohi_responder = XoHiResponder()

def setup_subscriptions():
    """Register all proactive sensors."""
    event_bus.subscribe("ORDER_CREATED", xohi_responder.handle_order_created)
    event_bus.subscribe("ORDER_CANCELLED", xohi_responder.handle_order_cancelled)
    event_bus.subscribe("CONTENT_STEP_COMPLETED", xohi_responder.handle_content_step_completed)
    event_bus.subscribe("CONTENT_PROGRESS", xohi_responder.handle_content_progress)
    event_bus.subscribe("MEDIA_UPLOADED", xohi_responder.handle_media_uploaded)
    event_bus.subscribe("MEDIA_SYNC_REQUIRED", media_responder.handle_media_sync)
    event_bus.subscribe("SYSTEM_SIGNAL", xohi_responder.handle_system_signal)
    event_bus.subscribe("SUPPORT_INBOX_UPDATE", xohi_responder.handle_support_inbox_update)
    logger.info("[XoHiResponder] Subscriptions initialized.")


