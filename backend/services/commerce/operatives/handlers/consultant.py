from __future__ import annotations
import os
if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = "mock_key_for_import_compliance"
import asyncio
import logging
import traceback
from typing import Optional, cast
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.agent_base import MedicalShieldMixin
from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext
from backend.schemas.support import SupportIntent
from backend.services.xohi.prompts import composer
from backend.database.repositories import SupportKnowledgeRepository
from backend.services.commerce.support_knowledge import SupportKnowledgeService

# Import helpers
from backend.services.commerce.operatives.handlers.consultant_helpers import (
    _try_db_product_direct,
    _generate_db_fallback,
    _wrap_prefix
)

# Elite V2.2: Context-aware Dependencies for Tool Injection
class ConsultantDeps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    db: AsyncSession
    dynamic_prompt: str = ""

ConsultantDeps.model_rebuild()

logger = logging.getLogger("arq.worker")

class ConsultantResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    reply: str
    intent: str
    ui_component: Optional[str] = None

# Elite V2.2: Module-level Singleton Agents (GC & RAM Optimization)
_consultant_agent: Agent[ConsultantDeps, ConsultantResponse] = Agent(
    "gemini-2.5-flash",
    output_type=ConsultantResponse,
    deps_type=ConsultantDeps
)

_consultant_no_tool_agent: Agent[ConsultantDeps, ConsultantResponse] = Agent(
    "gemini-2.5-flash",
    output_type=ConsultantResponse,
    deps_type=ConsultantDeps
)

@_consultant_agent.system_prompt
def _dynamic_system_prompt(ctx: RunContext[ConsultantDeps]) -> str:
    """Thread-safe dynamic prompt injection via Context deps."""
    return ctx.deps.dynamic_prompt

@_consultant_no_tool_agent.system_prompt
def _dynamic_system_prompt_no_tool(ctx: RunContext[ConsultantDeps]) -> str:
    """Thread-safe dynamic prompt injection for no-tool agent."""
    return ctx.deps.dynamic_prompt


class ConsultantHandler(BaseHandler, MedicalShieldMixin):
    """
    ZONE 2: Pathology and Product Knowledge Specialist.
    Focus: Scientific explanation, trust building, and soft closing.
    """
    
    async def handle(self, ctx: SupportContext) -> bool:
        try:
            return await self._handle_internal(ctx)
        except Exception as e:
            error_details = f"CRASH in ConsultantHandler: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_details)
            # Safe fall-through to the next handler
            return False

    async def _handle_internal(self, ctx: SupportContext) -> bool:
        """ZONE 2: Consultant Specialist (Depth & Advice)."""
        ctx.tool_calls_count += 1
        msg_norm = ctx.request.message.lower().strip()
        
        # 🚀 Elite V2.5: Order Safeguard (Triple-Lock)
        has_phone = sum(1 for c in msg_norm if c.isdigit()) >= 9
        has_address_signals = any(kw in msg_norm for kw in ["đường", "phố", "quận", "huyện", "phường", "xã", "tỉnh", "tp", "thành phố", "ngõ", "ngách", "/", ":"])
        buying_intent = any(kw in msg_norm for kw in ["mua", "đặt", "lấy", "ship", "giao", "ok", "chốt", "đơn", "lên đơn", "cho 1 đơn", "cho đơn", "về :"])
        
        if "[system_consult]" in msg_norm or "[system_skin_barrier]" in msg_norm:
            pass
        elif (has_phone or has_address_signals) and buying_intent:
            logger.info(f"🔇 [Consultant Silenced] Yielding to Order Flow: {msg_norm}")
            return False

        # --- 🚀 [ELITE V4.2] DATA SYNC GUARD ---
        if ctx.lead_data:
            logger.info(f"🛡️ [ConsultantHandler] V4.2 Sync Guard: Found existing lead_data (Phone: {bool(ctx.lead_data.customer_phone)}, Addr: {bool(ctx.lead_data.customer_address)})")
            if ctx.lead_data.customer_phone and ctx.lead_data.customer_address and ctx.lead_data.items:
                logger.info("🛡️ [ConsultantHandler] V4.2 Sync Guard: Order complete. Yielding for final chốt đơn.")

        # ═══════════════════════════════════════════════════════
        # [DB-FIRST LAYER] Kiểm tra dữ liệu sản phẩm trong DB
        # ═══════════════════════════════════════════════════════
        db_direct = await _try_db_product_direct(ctx, msg_norm)
        if db_direct:
            logger.info("✅ [DB-First] Trả kết quả trực tiếp từ DB — AI bypass hoàn toàn")
            ctx.replies.append(db_direct)
            ctx.intent = SupportIntent.PRODUCT_QUERY
            return True

        # [ELITE V6.0] Layer 0: Knowledge Base Fast-Path
        repo: SupportKnowledgeRepository = SupportKnowledgeRepository(session=ctx.db)
        kb_service: SupportKnowledgeService = SupportKnowledgeService(repo=repo)

        is_short_query: bool = len(ctx.request.message.strip()) < 25
        threshold: float = 0.85 if is_short_query else 0.92
        raw_matches: list[dict[str, object]] = await kb_service.search_relevant_knowledge_raw(ctx.db, ctx.request.message, limit=1)
        
        if not raw_matches:
            logger.warning("⚠️ [KB Health-Check] Knowledge base returned 0 results for semantic search. "
                          "Possible causes: empty KB, encoder not loaded, or missing embeddings.")
        
        if not raw_matches or float(raw_matches[0].get("match_score", 0)) <= threshold:
            if is_short_query:
                keyword_matches = await kb_service.search_relevant_knowledge_keyword(ctx.db, ctx.request.message, limit=1)
                if keyword_matches and str(keyword_matches[0].get("answer", "")).strip():
                    keyword_matches[0]["match_score"] = 1.0
                    raw_matches = keyword_matches

        if raw_matches and not ctx.request.cart_items:
            match: dict[str, object] = raw_matches[0]
            score: float = float(match.get("match_score", 0))
            ans = str(match.get("answer", "")).strip()
            if score > threshold and ans:
                logger.info(f"✨ [L0 KB Fast-Path] Short-circuiting (Score: {score} / Req: {threshold})")
                ctx.replies.append(ans)
                ctx.intent = SupportIntent.PRODUCT_QUERY
                return True
            else:
                logger.debug(f"⚠️ [KB Check Fail] score={score} < threshold={threshold} or empty answer")
        else:
            masked_msg = (ctx.request.message[:15] + "...") if len(ctx.request.message) > 20 else ctx.request.message
            logger.debug(f"🔍 [L0 KB] No match for: '{masked_msg}'")

        # RAG Pre-Retrieval
        pre_retrieved_ctx = ""
        try:
            from sqlalchemy import select, and_, or_, text
            from backend.database import current_tenant_id
            from backend.database.models.commerce import ProductBase
            from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
            
            tid = (current_tenant_id.get() or "default")
            msg_clean = ctx.request.message.replace("[system_consult]", "").strip()
            
            if len(msg_clean) > 2:
                p_rows = []
                encoder = get_shared_encoder()
                if encoder:
                    try:
                        vecs = list(encoder.embed([msg_clean]))
                        if vecs:
                            vec_str = f"[{','.join(map(str, vecs[0]))}]"
                            sql = text("""
                                SELECT p.id, p.name, p.short_description, p.description,
                                       p.product_metadata, p.price, p.discount_price, p.stock, p.slug,
                                       pe.embedding <=> CAST(:v AS vector) AS dist
                                FROM product_bases p
                                JOIN product_embeddings pe ON p.id = pe.product_base_id
                                WHERE p.deleted_at IS NULL
                                  AND p.status = 'ACTIVE'
                                  AND p.tenant_id = :tid
                                ORDER BY dist ASC
                                LIMIT 3
                            """)
                            res = await ctx.db.execute(sql, {"v": vec_str, "tid": tid})
                            p_rows = res.fetchall()
                    except Exception as p_err:
                        logger.debug(f"[ConsultantPreRetrieve] Product vector search failed: {p_err}")
                
                if not p_rows:
                    kw = f"%{msg_clean}%"
                    stmt = (
                        select(
                            ProductBase.id,
                            ProductBase.name,
                            ProductBase.short_description,
                            ProductBase.description,
                            ProductBase.product_metadata,
                            ProductBase.price,
                            ProductBase.discount_price,
                            ProductBase.stock,
                            ProductBase.slug,
                        )
                        .where(
                            and_(
                                ProductBase.deleted_at.is_(None),
                                ProductBase.status == "ACTIVE",
                                ProductBase.tenant_id == tid,
                                or_(
                                    ProductBase.name.ilike(kw),
                                    ProductBase.short_description.ilike(kw),
                                )
                            )
                        )
                        .limit(3)
                    )
                    p_rows = (await ctx.db.execute(stmt)).fetchall()

                if p_rows:
                    pre_retrieved_ctx += "\n[DỮ LIỆU TÌM KIẾM HỆ THỐNG - SẢN PHẨM KHẢ QUAN]:\n"
                    for idx, r in enumerate(p_rows):
                        price_display = int(r.discount_price or r.price or 0)
                        formatted = f"{price_display:,}đ".replace(",", ".")
                        stock_txt = f"{r.stock} còn" if r.stock else "Hết hàng"
                        pre_retrieved_ctx += f"  {idx+1}. {r.name} (Slug: {r.slug}) | Giá: {formatted} | Tồn: {stock_txt}\n"
                        if r.short_description:
                            pre_retrieved_ctx += f"     Mô tả: {r.short_description[:120]}\n"
                        meta = getattr(r, 'product_metadata', {}) or {}
                        if meta.get("ingredients"):
                            pre_retrieved_ctx += f"     Thành phần: {str(meta['ingredients'])[:150]}\n"
                        if meta.get("origin"):
                            pre_retrieved_ctx += f"     Xuất xứ: {meta['origin']}\n"
                
                kb_res = await kb_service.search_relevant_knowledge_raw(ctx.db, msg_clean, limit=2)
                if not kb_res:
                    kb_res = await kb_service.search_relevant_knowledge_keyword(ctx.db, msg_clean, limit=2)
                if kb_res:
                    pre_retrieved_ctx += "\n[DỮ LIỆU TÌM KIẾM HỆ THỐNG - TRI THỨC VÀ CHÍNH SÁCH CHUNG]:\n"
                    for idx, k in enumerate(kb_res):
                        pre_retrieved_ctx += f"  - Vấnref: {k.get('question')} | Hướng giải quyết: {k.get('answer')}\n"

                try:
                    import re as _re
                    import asyncio as _asyncio
                    from backend.database.models.content import Article
                    
                    _CTV_KEYWORDS = ["ctv", "cộng tác viên", "tuyển dụng", "affiliate", "đại lý", "chiết khấu"]
                    _POLICY_KEYWORDS = ["chính sách", "bảo hành", "đổi trả", "hoàn tiền", "vận chuyển", "giao hàng"]
                    
                    msg_lower = msg_clean.lower()
                    art_search_kw = msg_clean
                    if any(kw in msg_lower for kw in _CTV_KEYWORDS):
                        art_search_kw = "tuyển dụng cộng tác viên"
                    elif any(kw in msg_lower for kw in _POLICY_KEYWORDS):
                        art_search_kw = "chính sách"
                    
                    art_rows = []
                    try:
                        from backend.services.article_vector_service import article_vector_service
                        art_rows = await _asyncio.wait_for(
                            article_vector_service.search_semantic(ctx.db, art_search_kw, limit=2),
                            timeout=3.0
                        )
                    except Exception:
                        pass
                    
                    if not art_rows:
                        art_kw = f"%{art_search_kw}%"
                        art_stmt = (
                            select(Article.id, Article.title, Article.excerpt, Article.content, Article.slug, Article.category)
                            .where(and_(
                                Article.deleted_at.is_(None), Article.status == "PUBLISHED", Article.tenant_id == tid,
                                or_(Article.title.ilike(art_kw), Article.excerpt.ilike(art_kw)),
                            ))
                            .order_by(Article.views.desc()).limit(2)
                        )
                        art_rows = (await ctx.db.execute(art_stmt)).fetchall()
                    
                    if art_rows:
                        try:
                            if any(kw in msg_norm for kw in ["ctv", "cộng tác viên", "tuyển dụng", "affiliate", "đại lý", "chính sách"]):
                                logger.info("✨ [RAG Fast-Path] Short-circuiting using pre-retrieved article")
                                best_art = art_rows[0]
                                
                                r_title = best_art.get("title") if isinstance(best_art, dict) else getattr(best_art, "title", "")
                                r_excerpt = best_art.get("excerpt") if isinstance(best_art, dict) else getattr(best_art, "excerpt", "")
                                r_content = best_art.get("content") if isinstance(best_art, dict) else getattr(best_art, "content", "")
                                
                                ans_parts = [
                                    f"Dạ Helen xin gửi chị đẹp thông tin chính thức về **{r_title}** ạ: 🌸"
                                ]
                                
                                if r_content:
                                    html_text = str(r_content)
                                    html_text = _re.sub(r'</?(p|div|h1|h2|h3|h4|h5|h6|li|ul|ol|blockquote)>', '\n', html_text)
                                    html_text = _re.sub(r'<br\s*/?>', '\n', html_text)
                                    plain = _re.sub(r'<[^>]+>', '', html_text)
                                    
                                    lines = [line.strip() for line in plain.split('\n') if line.strip()]
                                    
                                    core_lines = []
                                    curr_len = 0
                                    for line in lines:
                                        core_lines.append(line)
                                        curr_len += len(line)
                                        if curr_len > 800:
                                            core_lines.append("...")
                                            break
                                    ans_parts.append("\n".join(core_lines))
                                elif r_excerpt:
                                    ans_parts.append(r_excerpt.strip())
                                    
                                ans_parts.append(
                                    "Để nhận được hướng dẫn chi tiết hoặc đăng ký làm đối tác, "
                                    "chị đẹp vui lòng liên hệ trực tiếp qua số Hotline hoặc các kênh hỗ trợ chính thức của thương hiệu nhé! 💖"
                                )
                                ctx.replies.append("\n\n".join(ans_parts))
                                ctx.intent = SupportIntent.PRODUCT_QUERY
                                return True
                        except Exception as fast_path_err:
                            logger.error(f"[RAGFastPath] Error: {fast_path_err}")

                        pre_retrieved_ctx += "\n[DỮ LIỆU TÌM KIẾM HỆ THỐNG - BÀI VIẾT & CHÍNH SÁCH]:\n"
                        for r in art_rows:
                            r_title = r.get("title") if isinstance(r, dict) else getattr(r, "title", "")
                            r_category = r.get("category") if isinstance(r, dict) else getattr(r, "category", "")
                            r_excerpt = r.get("excerpt") if isinstance(r, dict) else getattr(r, "excerpt", "")
                            r_content = r.get("content") if isinstance(r, dict) else getattr(r, "content", "")

                            pre_retrieved_ctx += f"  📰 **{r_title}** (Danh mục: {r_category})\n"
                            if r_excerpt:
                                pre_retrieved_ctx += f"     Tóm tắt: {r_excerpt[:300]}\n"
                            elif r_content:
                                plain = _re.sub(r'<[^>]+>', '', str(r_content))[:500]
                                pre_retrieved_ctx += f"     Nội dung: {plain}\n"
                except Exception as art_err:
                    logger.debug(f"[ConsultantPreRetrieve] Article pre-search failed: {art_err}")

        except Exception as e:
            logger.warning(f"[ConsultantPreRetrieve] Failed pre-retrieval: {e}")

        # Assemble prompt context
        lead_alert = ""
        if ctx.lead_data:
            if ctx.lead_data.customer_phone and ctx.lead_data.customer_address:
                lead_alert = "\n[SYSTEM ALERT: Khách đã để lại SĐT và Địa chỉ. Hãy xác nhận và chốt đơn ngay!]\n"
            elif ctx.lead_data.customer_phone:
                lead_alert = f"\n[SYSTEM ALERT: Đã có SĐT {ctx.lead_data.customer_phone}, hãy khéo léo xin Địa chỉ để giao hàng.]\n"

        integration_ctx = f"\n[CHẾ ĐỘ TÍCH HỢP]\nZalo OA: {'BẬT' if ctx.zalo_enabled else 'TẮT'}\nMessenger: {'BẬT' if ctx.messenger_enabled else 'TẮT'}\n"
        if not ctx.zalo_enabled:
            integration_ctx += "LƯU Ý: Không gửi link Zalo hoặc nhắc tới Zalo trong hội thoại.\n"
        if not ctx.messenger_enabled:
            integration_ctx += "LƯU Ý: Không nhắc tới Messenger trong hội thoại.\n"

        fomo_ctx = ""
        if ctx.product_stock and ctx.product_stock > 0:
            fomo_ctx = f"\n[CHỈ SỐ THỰC TẾ]\n[ĐANG XEM]: {ctx.active_visitors} người\n[TỒN KHO]: {ctx.product_stock} sản phẩm\n"

        loyalty_ctx = ""
        if ctx.dna.available_points > 0:
            loyalty_ctx = f"\n[LOYALTY DNA]\nKhách này là {ctx.dna.segment}. Có {ctx.dna.available_points} điểm. (Mức giảm điểm tối đa đã được tính sẵn trong [CART] bên dưới, tuyệt đối không tự tính lại).\n"

        clean_msg = ctx.request.message.replace("[system_consult]", "").strip()
        is_skin_barrier_session = "[system_skin_barrier]" in ctx.request.message or "kiểm tra sản phẩm có phù hợp cho da của tôi không?" in ctx.history_text.lower()
        is_system_consult = "[system_consult]" in ctx.request.message

        composer_context = {
            "point_value": ctx.dna.point_value_vnd or 1000,
            "clean_msg": clean_msg,
            "product_ctx": ctx.product_ctx,
            "history_text": ctx.history_text,
            "cart_text": ctx.cart_text
        }

        if is_skin_barrier_session:
            if "[system_skin_barrier]" in ctx.request.message:
                clean_msg = "Sản phẩm này có an toàn cho da của tôi không? Xin hãy kiểm tra giúp."
                composer_context["clean_msg"] = clean_msg
                base_prompt = composer.compose("helen_consultant_skin_barrier", context=composer_context)
            else:
                base_prompt = composer.compose("helen_consultant_skin_barrier_analysis", context=composer_context)
        elif is_system_consult:
            clean_msg = "Hãy tư vấn chuyên sâu về sản phẩm này giúp tôi."
            composer_context["clean_msg"] = clean_msg
            base_prompt = composer.compose("helen_system_consultation", context=composer_context)
        else:
            base_prompt = composer.compose("helen_consultant_premium", context=composer_context)

        marketing_block = ""
        if ctx.p_info:
            from backend.services.commerce.operatives.handlers.consultant_helpers import build_marketing_benefits_block
            marketing_block = await build_marketing_benefits_block(ctx.db, ctx.p_info, ctx.dna)

        full_prompt = (
            f"{base_prompt}\n"
            f"{integration_ctx}\n"
            f"{fomo_ctx}\n"
            f"{loyalty_ctx}\n"
            f"{lead_alert}\n"
        )
        if marketing_block:
            full_prompt += f"\n[CHƯƠNG TRÌNH MARKETING ĐANG ÁP DỤNG CHO SẢN PHẨM]\n{marketing_block}\n"
            
        full_prompt += (
            f"\n[DỮ LIỆU TÌM KIẾM HỆ THỐNG (GROUND TRUTH)]\n{pre_retrieved_ctx or 'Không tìm thấy kết quả bổ sung.'}\n"
            f"\n[MỤC LỤC TRI THỨC HỆ THỐNG - LAYER 1]\n{ctx.knowledge_index}\n"
            f"\nCHỈ THỊ TƯ VẤN:\n"
            f"- ƯU TIÊN TUYỆT ĐỐI dữ liệu trong [DỮ LIỆU TÌM KIẾM HỆ THỐNG (GROUND TRUTH)], [PRODUCT] và [CHƯƠNG TRÌNH MARKETING ĐANG ÁP DỤNG CHO SẢN PHẨM] để trả lời ngay.\n"
            f"- CẤM TUYỆT ĐỐI gọi các Tool tìm kiếm nếu thông tin cần trả lời đã nằm trong ngữ cảnh trên.\n"
        )

        try:
            masked_msg = await self._mask_sensitive_medical_terms(clean_msg)
            masked_prompt = await self._mask_sensitive_medical_terms(full_prompt)

            logger.info(f"🟢 [ConsultantHandler] SYSTEM PROMPT:\n{masked_prompt}")
            logger.info(f"🟢 [ConsultantHandler] USER MESSAGE: {masked_msg}")

            deps = ConsultantDeps(db=ctx.db, dynamic_prompt=masked_prompt)

            res = await asyncio.wait_for(
                trinity_bridge.run(
                    _consultant_no_tool_agent,
                    masked_msg,
                    deps=deps,
                    role=trinity_bridge.ROLE_BRAIN,
                    safety_none=True,
                    timeout=15.0,
                    per_model_timeout=8.0
                ),
                timeout=15.0
            )
            res_data = cast(Optional[ConsultantResponse], res)
            
            logger.info(f"🟢 [ConsultantHandler] RAW AI RESPONSE: {res_data}")

            if res_data and hasattr(res_data, 'reply') and res_data.reply:
                final_reply = res_data.reply
                if not final_reply.startswith("[z2]"):
                    final_reply = f"[z2] {final_reply}"
                ctx.replies.append(final_reply)
                valid_intents = {i.value for i in SupportIntent}
                ctx.intent = SupportIntent(res_data.intent) if res_data.intent in valid_intents else SupportIntent.PRODUCT_QUERY
                ctx.ui_component = res_data.ui_component
                return True

            logger.warning(f"⚠️ [ConsultantHandler] AI returned invalid data: {type(res)}")
            db_fallback = _generate_db_fallback(ctx)
            if db_fallback:
                ctx.replies.append(db_fallback)
                ctx.intent = SupportIntent.PRODUCT_QUERY
                return True
            return False

        except asyncio.TimeoutError:
            logger.warning("⚠️ [ConsultantHandler] AI vượt 10s — Kích hoạt Smart DB Fallback")
            db_fallback = _generate_db_fallback(ctx)
            if db_fallback:
                ctx.replies.append(db_fallback)
                ctx.intent = SupportIntent.PRODUCT_QUERY
                return True
            return False

        except Exception as e:
            logger.error(f"[ConsultantHandler] Sweep Failure: {e}")
            db_fallback = _generate_db_fallback(ctx)
            if db_fallback:
                ctx.replies.append(db_fallback)
                ctx.intent = SupportIntent.PRODUCT_QUERY
                return True
            return False

# Import tool registry dynamically to avoid circular import issues
import backend.services.commerce.operatives.handlers.consultant_tools
