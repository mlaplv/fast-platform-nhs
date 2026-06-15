"""
Support Agent Operative — SUPPORT_NAME_CLIENT (Architect's Edition)
==================================================================
Elite V5.5: Zero-Hydration, Full Async I/O, 100% Static Typing.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Optional, cast, Union, Dict, Type
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.uid import new_id
from backend.database.models.commerce import ProductBase, ProductVariant
from backend.database.models.promotion import Voucher
from backend.database.repositories import SupportKnowledgeRepository
from backend.services.commerce.support_knowledge import SupportKnowledgeService
from backend.schemas.support import SupportIntent, SupportRequest, SupportResponse
from backend.schemas.order import OrderDraft
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.agent_base import BaseAgentOperative
from backend.constants.infra import HELEN_FOLLOW_UP_TRIGGER
from backend.database.alchemy_config import alchemy_config
from backend.services.event_bus import event_bus
from backend.services.xohi_memory import xohi_memory

from backend.services.commerce.operatives.handlers.base import NeuralDNA, SupportContext
from backend.services.commerce.operatives.router import SupportRouter

# Re-export and delegate utilities to utils.py
from backend.services.commerce.operatives.utils import (
    _support_ai_agent,
    _fast_intent_agent,
    search_knowledge_base,
    _is_definite_greeting,
    _fetch_product_context,
    _validate_grounding,
    _sanitize_response,
    _sanitize_for_notification,
    FastIntentDeps
)

# Re-export and delegate sync order helper
from backend.services.commerce.operatives.sync_order_helper import (
    _try_heuristic_sync,
    _try_sync_order_fast_path,
    _try_sync_slot_fill
)

# Context Helper functions
from backend.services.commerce.operatives.context_helper import (
    _fetch_chat_context,
    _fetch_neural_dna,
    _prepare_pricing_breakdown,
    _get_currency_settings,
    _trim_context_to_budget,
    _render_cart_report,
    _generate_fomo_instructions,
    _try_db_first_fast_path
)

logger = logging.getLogger("arq.worker")

class SupportAgentOperative(BaseAgentOperative):
    """Refined Architect-level Operative."""
    agent_id_class = "support_agent"

    def __init__(self, agent_id: str = "support_agent") -> None:
        super().__init__(agent_id=agent_id)
        self.router = SupportRouter()
        self._arq_pool: Optional[object] = None
        self._background_tasks: set[asyncio.Task[object]] = set()

    async def _get_arq_pool(self) -> object:
        if self._arq_pool is None:
            from arq import create_pool
            from backend.infra.arq_config import get_redis_settings
            self._arq_pool = await create_pool(get_redis_settings())
        return self._arq_pool

    def get_schema(self) -> Optional[Type[BaseModel]]:
        return SupportRequest

    # Expose helper proxies for handlers / modules that call them on SupportAgentOperative instance
    async def _get_currency_settings(self) -> Dict[str, str]:
        return await _get_currency_settings()

    async def _fetch_neural_dna(
        self, db: AsyncSession, session_id: str, lead_phone: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> NeuralDNA:
        return await _fetch_neural_dna(db, session_id, lead_phone, user_id)

    async def _save_history(
        self, db: AsyncSession, session_id: str, user_msg: str, assistant_reply: Optional[str],
        intent: SupportIntent, product_slug: Optional[str], customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None
    ) -> None:
        try:
            if user_msg != HELEN_FOLLOW_UP_TRIGGER:
                clean_msg = user_msg
                if "[system_consult]" in clean_msg:
                    clean_msg = "Tư vấn chuyên sâu về sản phẩm này"
                elif "[system_skin_barrier]" in clean_msg:
                    clean_msg = "Kiểm tra sản phẩm có phù hợp cho da của tôi không?"
                from backend.utils.security import GeminiSecurity
                from backend.database.models.system import SupportChatHistory
                enc_user_msg = GeminiSecurity.encrypt(clean_msg)
                msg_user = SupportChatHistory(
                    session_id=session_id, role="user", content=enc_user_msg,
                    intent=intent.value, product_slug=product_slug,
                    customer_name=customer_name, customer_phone=customer_phone
                )
                db.add(msg_user)

            if assistant_reply is not None:
                from backend.utils.security import GeminiSecurity
                from backend.database.models.system import SupportChatHistory
                enc_assistant_reply = GeminiSecurity.encrypt(assistant_reply)
                msg_ai = SupportChatHistory(
                    session_id=session_id, role="assistant", content=enc_assistant_reply,
                    intent=intent.value, product_slug=product_slug,
                    customer_name=customer_name, customer_phone=customer_phone
                )
                db.add(msg_ai)
            await db.flush()
            
            if user_msg != HELEN_FOLLOW_UP_TRIGGER:
                try:
                    redis = await self._get_arq_pool()
                    await redis.enqueue_job(
                        "helen_follow_up_job", session_id=session_id,
                        _defer_by=3600, _job_id=f"followup:{session_id}:{int(time.time())}",
                        _queue_name="high"
                    )
                except Exception as arqe:
                    logger.warning("[SupportAgent] Follow-up scheduling failed: %s", arqe)
        except Exception as exc:
            logger.warning("[SupportAgent] Saving failed: %s", exc)
            await db.rollback()

    async def _emit_inbox_update(self, session_id: str, raw_msg: str) -> None:
        safe_msg = _sanitize_for_notification(raw_msg)
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {
            "session_id": session_id,
            "role": "user",
            "message": safe_msg,
        })

    async def process_brain_logic(self, request: SupportRequest, db: AsyncSession) -> SupportResponse:
        session_id = request.session_id or new_id()

        from backend.services.commerce.security.input_guard import input_guard
        _is_safe, _guard_reason = await input_guard.validate_async(request.message)
        if not _is_safe:
            logger.warning("[SupportAgent/Brain] InputGuard rejected background task. Reason: %s", _guard_reason)
            _rejection_reply = "Dạ Helen xin lỗi, em chỉ có thể hỗ trợ các thông tin sản phẩm và dịch vụ của osmo. Rất mong Anh/Chị thông cảm ạ! 🙏"
            return SupportResponse(ok=False, reply=_rejection_reply, intent=SupportIntent.UNKNOWN, session_id=session_id, status="REJECTED")

        await event_bus.emit("SUPPORT_THOUGHT", {"session_id": session_id, "think": "Đang chuẩn bị context Senior Beauty Architect..."})
        
        cur_settings, raw_draft = await asyncio.gather(
            _get_currency_settings(),
            xohi_memory.get_order_draft(session_id),
        )
        order_draft = OrderDraft.model_validate(raw_draft) if raw_draft else None

        # Check if the message is a cart checkout intent
        msg_lower = request.message.lower()
        is_cart_checkout = any(kw in msg_lower for kw in ["tính tiền", "tinh tien", "thanh toán", "thanh toan", "checkout"])

        if not is_cart_checkout and request.product_slug:
            # Direct Product Flow: If there is an existing draft, check if it's for a different product
            if order_draft and order_draft.items:
                stmt = select(ProductBase.id, ProductBase.slug).where(ProductBase.slug == request.product_slug)
                curr_p = (await db.execute(stmt)).first()
                if curr_p:
                    curr_p_id, curr_p_slug = str(curr_p.id), str(curr_p.slug)
                    different = False
                    for item in order_draft.items:
                        item_id = str(item.get("product_id") or item.get("id") or "")
                        # If the item ID does not match current product ID and doesn't contain the slug
                        if item_id != curr_p_id and curr_p_slug not in item_id:
                            different = True
                            break
                    if different:
                        logger.info(f"🔄 [SupportAgent/Brain] Product mismatch: Resetting order_draft from previous page in RAM and Redis.")
                        order_draft = None
                        await xohi_memory.clear_order_draft(session_id)

        hist_text = await _fetch_chat_context(db, session_id)
        dna = await _fetch_neural_dna(db, session_id, lead_phone=request.customer_phone, user_id=request.user_id)
        ctx_text, p_info = await _fetch_product_context(db, request.product_slug, cur_settings)

        try:
            repo = SupportKnowledgeRepository(session=db)
            kb_service = SupportKnowledgeService(repo=repo)
            kb_index = await kb_service.get_knowledge_index(db)
        except Exception as e:
            logger.warning("[SupportAgent] KnowledgeIndex fetch failed: %s", e)
            kb_index = ""

        p_ids: list[str] = []
        v_ids: list[str] = []
        if request.cart_items:
            for item in request.cart_items:
                p_id = item.get("product", {}).get("id")
                v_id = item.get("variant", {}).get("id")
                if p_id:
                    p_ids.append(str(p_id))
                if v_id:
                    v_ids.append(str(v_id))

        p_map: Dict[str, ProductBase] = {}
        v_map: Dict[str, ProductVariant] = {}
        if p_ids:
            p_rows = (await db.execute(select(ProductBase).where(ProductBase.id.in_(p_ids)))).scalars().all()
            p_map = {str(p.id): p for p in p_rows}
        if v_ids:
            v_rows = (await db.execute(select(ProductVariant).where(ProductVariant.id.in_(v_ids)))).scalars().all()
            v_map = {str(v.id): v for v in v_rows}

        pb = await _prepare_pricing_breakdown(db, request, dna, p_map=p_map, v_map=v_map)
        cart_text = _render_cart_report(request, p_map, v_map, pb, ctx_text, cur_settings)
        
        from backend.database import current_tenant_id
        from sqlalchemy import or_
        all_vouchers = (await db.execute(
            select(Voucher).where(
                Voucher.is_active == True,
                Voucher.deleted_at.is_(None),
                or_(Voucher.is_viral == False, Voucher.is_viral.is_(None)),
                Voucher.tenant_id == (current_tenant_id.get() or "default")
            )
        )).scalars().all()
        fomo_text = _generate_fomo_instructions(pb, all_vouchers, cur_settings)
        if fomo_text:
            cart_text += fomo_text

        zalo_on, msg_on = False, False
        try:
            raw_cfg = await xohi_memory.client.get("system:settings:primary_config")
            if raw_cfg:
                cfg_data = json.loads(raw_cfg)
                zalo_on = cfg_data.get("integrations", {}).get("zalo", {}).get("enabled", False)
                msg_on = cfg_data.get("integrations", {}).get("messenger", {}).get("enabled", False)
        except Exception as _ce:
            logger.warning("[SupportAgent] Integration config fetch failure: %s", _ce)

        cart_text, ctx_text, hist_text, kb_index = _trim_context_to_budget(
            cart_text, ctx_text, hist_text, kb_index
        )

        ctx = SupportContext(
            db=db, request=request, session_id=session_id, dna=dna,
            product_ctx=ctx_text, history_text=hist_text, knowledge_index=kb_index,
            p_info=p_info, cart_text=cart_text, order_draft=order_draft,
            zalo_enabled=zalo_on, messenger_enabled=msg_on
        )
        
        try:
            ctx = await self.router.process(ctx)
        except Exception as pe:
            logger.error(f"[SupportAgent] Router Failed: {pe}")
            await db.rollback()
        
        final_reply = " ".join(ctx.replies).strip() if ctx.replies else "[fallback] Dạ Helen đang kết nối lại, Anh/Chị thông cảm nhé! 🌸"
        
        if ctx.order_draft and not ctx.order_draft.is_complete and ctx.intent != SupportIntent.PURCHASE:
            if not ctx.replies:
                missing = ctx.order_draft.missing_slots
                if missing:
                    hook = f"\n\n(Dạ em vẫn đang chờ {', '.join(missing)} để hoàn tất đơn hàng ạ! 🌸)"
                    if hook not in final_reply:
                        final_reply += hook

        if not ctx.ui_metadata:
            ctx.ui_metadata = {}
        if ctx.order_draft:
            ctx.ui_metadata.update({
                "order_draft": ctx.order_draft.model_dump(mode='json'),
                "missing_slots": ctx.order_draft.missing_slots,
                "is_definite": ctx.lead_data.is_definite_purchase if ctx.lead_data else False
            })
        
        # 🚀 Elite V7.2: Bidirectional Cart Sync with Epoch-based locking
        incoming_cart = request.cart_items or []
        draft_items = ctx.order_draft.items if ctx.order_draft else []
        
        # Check differences
        incoming_map = {}
        for item in incoming_cart:
            prod = item.get("product") or {}
            var = item.get("variant") or {}
            p_id = str(var.get("id") or prod.get("id") or "")
            qty = int(item.get("quantity") or 1)
            if p_id:
                incoming_map[p_id] = qty
                
        draft_map = {}
        for item in draft_items:
            p_id = str(item.get("variant_id") or item.get("product_id") or item.get("id") or "")
            qty = int(item.get("quantity") or 1)
            if p_id:
                draft_map[p_id] = item
        
        has_changes = len(incoming_map) != len(draft_map)
        if not has_changes:
            for p_id, qty in incoming_map.items():
                if p_id not in draft_map or int(draft_map[p_id].get("quantity") or 1) != qty:
                    has_changes = True
                    break
        
        should_clear_cart = bool(ctx.processed_order_id)
        
        if has_changes or should_clear_cart:
            new_epoch = (request.cart_epoch or 0) + 1
            if should_clear_cart:
                ctx.ui_metadata["update_cart"] = {
                    "items": [],
                    "epoch": new_epoch
                }
            else:
                updated_items = []
                for p_id, d_item in draft_map.items():
                    variant_obj = v_map.get(p_id)
                    product_obj = None
                    if variant_obj:
                        product_obj = p_map.get(str(variant_obj.product_id))
                    else:
                        product_obj = p_map.get(p_id)
                    
                    if not product_obj and not variant_obj:
                        try:
                            var_res = (await db.execute(select(ProductVariant).where(ProductVariant.id == p_id))).scalar_one_or_none()
                            if var_res:
                                variant_obj = var_res
                                product_obj = (await db.execute(select(ProductBase).where(ProductBase.id == var_res.product_id))).scalar_one_or_none()
                            else:
                                product_obj = (await db.execute(select(ProductBase).where(ProductBase.id == p_id))).scalar_one_or_none()
                        except Exception as fe:
                            logger.warning(f"[SupportAgent] Sync db fetch failed for ID {p_id}: {fe}")
                    
                    prod_dict = {}
                    if product_obj:
                        prod_dict = {
                            "id": str(product_obj.id),
                            "name": str(product_obj.name),
                            "price": float(product_obj.price or 0),
                            "discountPrice": float(product_obj.discount_price or product_obj.price or 0),
                            "slug": str(product_obj.slug or "")
                        }
                    else:
                        prod_dict = {
                            "id": p_id,
                            "name": d_item.get("name", "Sản phẩm"),
                            "price": float(d_item.get("price") or 0),
                            "discountPrice": float(d_item.get("price") or 0),
                            "slug": ""
                        }
                        
                    var_dict = None
                    if variant_obj:
                        var_dict = {
                            "id": str(variant_obj.id),
                            "sku": str(variant_obj.sku or ""),
                            "price": float(variant_obj.price or 0),
                            "discountPrice": float(variant_obj.discount_price or variant_obj.price or 0),
                            "tierIndex": variant_obj.tier_index or []
                        }
                        
                    updated_items.append({
                        "id": p_id,
                        "product": prod_dict,
                        "variant": var_dict,
                        "quantity": int(d_item.get("quantity") or 1),
                        "selected": True
                    })
                
                ctx.ui_metadata["update_cart"] = {
                    "items": updated_items,
                    "epoch": new_epoch
                }
        
        ctx.ui_metadata["is_optimal_price"] = ctx.cart_text.find("[XÁC NHẬN]: Khách đã dùng mã tối ưu") != -1
        grounded_reply = _validate_grounding(final_reply, ctx)
        safe_reply = _sanitize_response(grounded_reply)
        
        if not safe_reply:
            from backend.services.commerce.operatives.handlers.consultant import ConsultantHandler
            consultant = ConsultantHandler()
            safe_reply = consultant._generate_db_fallback(ctx)

        final_intent = ctx.intent or SupportIntent.UNKNOWN
        if ctx.ui_component == "PRODUCT_CARD" and p_info:
            if not ctx.ui_metadata:
                ctx.ui_metadata = {}
            ctx.ui_metadata.update({"type": "PRODUCT_CARD", "data": p_info.model_dump()})

        await self._save_history(
            db, session_id, request.message, safe_reply, final_intent,
            request.product_slug, dna.customer_name or request.customer_name,
            ctx.lead_data.customer_phone if ctx.lead_data else None
        )
        await self._emit_inbox_update(session_id, request.message)
        await db.flush()
        
        return SupportResponse(
            ok=True, reply=safe_reply, intent=final_intent, session_id=session_id,
            product_info=p_info, status="DONE", ui_metadata=ctx.ui_metadata,
            processed_order_id=ctx.processed_order_id
        )

    async def chat(self, request: Union[SupportRequest, dict], **kwargs: object) -> SupportResponse:
        if isinstance(request, dict):
            request = SupportRequest.model_validate(request)
        db = cast(Optional[AsyncSession], kwargs.get("db"))
        if not db:
            session_maker = alchemy_config.create_session_maker()
            async with session_maker() as standalone_db:
                res = await self._chat_internal(request, standalone_db)
                await standalone_db.commit()
                return res
        return await self._chat_internal(request, db)

    async def _chat_internal(self, request: SupportRequest, db: AsyncSession) -> SupportResponse:
        session_id = request.session_id or new_id()

        from backend.services.commerce.security.input_guard import input_guard
        _is_safe, _guard_reason = await input_guard.validate_async(request.message)
        if not _is_safe:
            logger.warning("[SupportAgent] InputGuard rejected at entry. Reason: %s", _guard_reason)
            _rejection_reply = "Dạ Helen xin lỗi, em chỉ có thể hỗ trợ các thông tin sản phẩm và dịch vụ của osmo. Rất mong Anh/Chị thông cảm ạ! 🙏"
            return SupportResponse(ok=False, reply=_rejection_reply, intent=SupportIntent.UNKNOWN, session_id=session_id, status="REJECTED")

        dna = await _fetch_neural_dna(db, session_id, lead_phone=request.customer_phone, user_id=request.user_id)
        c_name = dna.customer_name or request.customer_name or "Quý khách"
        if c_name in ["Khách ẩn danh", "Sếp"]:
            c_name = "Quý khách"
        msg_clean = request.message.strip().lower()

        if xohi_memory._use_redis and xohi_memory.client:
            try:
                await xohi_memory.client.sadd("support:unread_sessions", session_id)
            except Exception as exc:
                logger.error(f"[SupportAgent] Failed to mark unread in Redis Set: {exc}")

        if "[chat_inbox]" in msg_clean:
            await xohi_memory.client.set(f"support:takeover:{session_id}", "0", ex=86400 * 3)
            await self._emit_inbox_update(session_id, request.message)
            reply_text = (
                "Dạ vâng ạ! Helen đã mời chuyên viên tư vấn trực tiếp vào cuộc trò chuyện này. "
                "Anh/Chị vui lòng chờ trong giây lát — chuyên viên sẽ phản hồi ngay tại đây ạ! 🤝\n\n"
                "*(Helen tạm dừng để nhường chỗ cho chuyên viên)*"
            )
            await self._save_history(db, session_id, request.message, reply_text, SupportIntent.ESCALATE, request.product_slug, c_name, request.customer_phone)
            await db.flush()
            return SupportResponse(ok=True, reply=reply_text, intent=SupportIntent.ESCALATE, session_id=session_id, status="DONE")

        if "[zalo_oa]" in msg_clean or any(k in msg_clean for k in ["kết nối trực tiếp với chuyên viên", "yêu cầu kết nối chuyên viên", "gặp tư vấn viên"]):
            from backend.services.core.zalo_service import zalo_service
            task = asyncio.create_task(
                zalo_service.push_support_notification(
                    customer_name=c_name, message=request.message, session_id=session_id
                )
            )
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            await xohi_memory.client.set(f"support:takeover:{session_id}", "0", ex=86400 * 3)
            await self._emit_inbox_update(session_id, request.message)

            reply_text = (
                "Dạ vâng ạ! Helen đã mở kết nối Zalo OA cho Anh/Chị và thông báo cho chuyên viên tư vấn. "
                "Chuyên viên sẽ theo dõi và có thể tiếp tục hỗ trợ ngay tại đây ạ! 💙\n\n"
                "*(Helen tạm dừng để nhường chỗ cho chuyên viên)*"
            )
            await self._save_history(db, session_id, request.message, reply_text, SupportIntent.ESCALATE, request.product_slug, c_name, request.customer_phone)
            await db.flush()
            return SupportResponse(ok=True, reply=reply_text, intent=SupportIntent.ESCALATE, session_id=session_id, status="DONE")

        helen_on = await xohi_memory.client.get("system:helen_enabled")
        if helen_on == "0":
            from backend.services.core.zalo_service import zalo_service
            task = asyncio.create_task(
                zalo_service.push_support_notification(
                    customer_name=c_name, message=request.message, session_id=session_id
                )
            )
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            offline_msg = await xohi_memory.client.get("system:helen_offline_msg")
            reply_text = offline_msg or "Dược sĩ tư vấn sẽ sớm phản hồi Quý khách qua Zalo OA. Vui lòng để lại lời nhắn ạ. 🌸"
            await self._save_history(db, session_id, request.message, reply_text, SupportIntent.UNKNOWN, request.product_slug, c_name, request.customer_phone)
            await self._emit_inbox_update(session_id, request.message)
            await db.flush()
            return SupportResponse(ok=True, reply=reply_text, intent=SupportIntent.UNKNOWN, session_id=session_id, status="DONE")
        
        takeover_val = await xohi_memory.client.get(f"support:takeover:{session_id}")
        if takeover_val == "0":
            await self._save_history(db, session_id, request.message, None, SupportIntent.UNKNOWN, request.product_slug, c_name, request.customer_phone)
            await self._emit_inbox_update(session_id, request.message)
            await db.flush()
            return SupportResponse(ok=True, reply="", intent=SupportIntent.UNKNOWN, session_id=session_id, status="TAKEOVER")
        
        cur_settings, raw_draft = await asyncio.gather(
            _get_currency_settings(),
            xohi_memory.get_order_draft(session_id),
        )
        order_draft = OrderDraft.model_validate(raw_draft) if raw_draft else None

        # Check if the message is a cart checkout intent
        msg_lower = request.message.lower()
        is_cart_checkout = any(kw in msg_lower for kw in ["tính tiền", "tinh tien", "thanh toán", "thanh toan", "checkout"])

        if not is_cart_checkout and request.product_slug:
            # Direct Product Flow: If there is an existing draft, check if it's for a different product
            if order_draft and order_draft.items:
                stmt = select(ProductBase.id, ProductBase.slug).where(ProductBase.slug == request.product_slug)
                curr_p = (await db.execute(stmt)).first()
                if curr_p:
                    curr_p_id, curr_p_slug = str(curr_p.id), str(curr_p.slug)
                    different = False
                    for item in order_draft.items:
                        item_id = str(item.get("product_id") or item.get("id") or "")
                        # If the item ID does not match current product ID and doesn't contain the slug
                        if item_id != curr_p_id and curr_p_slug not in item_id:
                            different = True
                            break
                    if different:
                        logger.info(f"🔄 [SupportAgent] Product mismatch: Resetting order_draft from previous page in RAM and Redis.")
                        order_draft = None
                        await xohi_memory.clear_order_draft(session_id)

        ctx_text, p_info = await _fetch_product_context(db, request.product_slug, cur_settings)
        is_system_prompt = request.message.strip().startswith("[system_")

        # ══ SYNC DB-FIRST FAST-PATH ══
        db_first_res = await _try_db_first_fast_path(db, request, p_info, c_name, cur_settings, ctx_text, dna=dna)
        if db_first_res:
            await self._save_history(
                db, session_id, request.message, db_first_res.reply,
                db_first_res.intent, request.product_slug, c_name,
                request.customer_phone
            )
            await self._emit_inbox_update(session_id, request.message)
            await db.flush()
            return db_first_res

        # Early exit for greeting trie
        if not is_system_prompt and not request.cart_items and _is_definite_greeting(request.message):
            _c = c_name if c_name not in ["Quý khách"] else ""
            greeting_reply = (
                f"Xin chào{f' {_c}' if _c else ''}! 🌸 Helen rất vui được hỗ trợ Anh/Chị. "
                "Anh/Chị cần tư vấn về sản phẩm, đơn hàng hay bất kỳ điều gì, cứ nhắn Helen nhé! ✨"
            )
            await self._save_history(db, session_id, request.message, greeting_reply, SupportIntent.GENERAL_ADVICE, request.product_slug, c_name, request.customer_phone)
            await self._emit_inbox_update(session_id, request.message)
            await db.flush()
            return SupportResponse(ok=True, reply=greeting_reply, intent=SupportIntent.GENERAL_ADVICE, session_id=session_id, status="DONE")

        if not is_system_prompt:
            try:
                masked_msg = await self._mask_sensitive_medical_terms(request.message)
                fast_res = await asyncio.wait_for(
                    trinity_bridge.run(
                        _fast_intent_agent, masked_msg,
                        deps=FastIntentDeps(customer_name=c_name, product_name=p_info.name if p_info else None),
                        role=trinity_bridge.ROLE_FAST, timeout=12.0, per_model_timeout=5.0
                    ), timeout=13.0
                )
                f_data = cast(BaseModel, fast_res)
                f_intent = getattr(f_data, "intent", "OTHER")
                f_reply = getattr(f_data, "quick_reply", None)
                if f_intent == "GREETING" and f_reply and not request.cart_items:
                    await self._save_history(db, session_id, request.message, str(f_reply), SupportIntent.GENERAL_ADVICE, request.product_slug, c_name, request.customer_phone)
                    await db.flush()
                    return SupportResponse(ok=True, reply=str(f_reply), intent=SupportIntent.GENERAL_ADVICE, session_id=session_id, status="DONE")
            except Exception:
                pass

        heuristic_res = await _try_heuristic_sync(self, request, db, session_id, p_info, c_name)
        if heuristic_res:
            return heuristic_res

        order_fp = await _try_sync_order_fast_path(self, request, db, session_id, p_info, c_name)
        if order_fp:
            return order_fp

        if order_draft:
            slot_fp = await _try_sync_slot_fill(self, request, db, session_id, order_draft, c_name)
            if slot_fp:
                return slot_fp

        enqueue_data = request.model_dump()
        enqueue_data["message"] = request.message

        if xohi_memory._use_redis and xohi_memory.client:
            await xohi_memory.client.delete(f"pulse:{session_id}:cache")
        task_id = await self.enqueue_chat(request_data=enqueue_data, session_id=session_id)
        return SupportResponse(ok=True, reply="Helen đang xử lý...", intent=SupportIntent.UNKNOWN, session_id=session_id, task_id=task_id, status="PROCESSING")

support_agent = SupportAgentOperative()
