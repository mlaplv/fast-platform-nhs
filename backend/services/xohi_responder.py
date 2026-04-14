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
                msg = f"Liệu trình mới từ {customer} (ID: {order_id[:8]})"
                
                from backend.schemas.signal import SignalSchema, SignalSeverity
                from backend.services.signal_center import signal_center
                
                severity = SignalSeverity.INFO
                if is_spam:
                    if score >= 90:
                        severity = SignalSeverity.CRITICAL
                        msg = f"🚨 RED ALERT: Phát hiện tấn công Click-Fraud cực mạnh! Đơn {order_id[:8]} đã bị cô lập hoàn toàn. Lý do: {reason}"
                    else:
                        severity = SignalSeverity.ACTION
                        msg = f"🚩 CẢNH BÁO SPAM: {msg} - {reason}"

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
        reason = str(payload.get("reason", "Không rõ lý do"))
        tenant_id = str(payload.get("tenant_id", "default"))
        msg = f"Khách đã HỦY liệu trình {order_id[:8]}. Lý do: {reason}"

        from backend.schemas.signal import SignalSchema, SignalSeverity
        from backend.services.signal_center import signal_center

        async with self.session_maker() as session:
            try:
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
        except Exception as e:
            logger.error(f"[XoHiResponder] Content log persistence failed: {e}")

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
    logger.info("[XoHiResponder] Subscriptions initialized.")
