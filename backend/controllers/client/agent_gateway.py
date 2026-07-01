"""
AI Agent Gateway — A2A Commerce Integration (Elite V2.2)
=========================================================
Public routes for AI discovery & integration:
- serving `/.well-known/ai-plugin.json`  (OpenAI GPT Actions)
- serving `/.well-known/mcp.json`        (MCP Discovery)
- 9 consumer MCP tools:
    search_products, search_articles, get_product_detail, get_article_detail,
    get_promotions, get_loyalty_policy, preview_pricing, stealth_checkout,
    chat_with_helen
- order status webhook registration & callback
- agent metrics telemetry & IP management
"""
from __future__ import annotations
import logging
import os
import json
import asyncio
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


from litestar import Controller, get, post, Response, Request, MediaType
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.schemas.client.checkout import StealthCheckoutSchema, CheckoutPreviewRequest
from backend.services.commerce.checkout import CheckoutService
from backend.services.commerce.logic.pricing_engine import PricingEngine
from backend.services.xohi_memory import xohi_memory
from backend.utils.uid import new_id

logger = logging.getLogger("agent-gateway")

class WebhookRegisterRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    order_id: str = Field(..., description="ID of the order to track")
    callback_url: str = Field(..., pattern=r"^https?://.*", description="Webhook callback URL starting with http/https")

class ToolCallRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str
    arguments: Dict[str, Any]

class IPBlockRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    ip: str
    duration: int = 86400

class AgentGatewayController(Controller):
    path = ""

    # ── 1. AI Plugin Specification ───────────────────────────────────────────
    @get("/.well-known/ai-plugin.json", media_type=MediaType.JSON, guards=[])
    async def get_ai_plugin_manifest(self) -> Dict[str, Any]:
        """Expose OpenAI Plugin specification manifest for GPT Actions discovery."""
        app_domain = os.getenv("APP_DOMAIN", "osmo.vn")
        api_url = f"https://api.{app_domain}"
        site_url = f"https://{app_domain}"
        
        return {
            "schema_version": "v1",
            "name_for_human": "Osmo AI Commerce Gateway",
            "name_for_model": "osmo_ai_commerce",
            "description_for_human": "Browse products, calculate checkout prices, and purchase items on Osmo.",
            "description_for_model": "Plugin for external AI agents to search products, preview pricing details, and execute guest checkouts.",
            "auth": {
                "type": "none"
            },
            "api": {
                "type": "openapi",
                "url": f"{api_url}/schema"
            },
            "logo_url": f"{site_url}/favicon.svg",
            "contact_email": "tech@osmo.vn",
            "legal_info_url": f"{site_url}/terms"
        }

    # ── 2. MCP Discovery Specification ───────────────────────────────────────
    @get("/.well-known/mcp.json", media_type=MediaType.JSON, guards=[])
    async def get_mcp_manifest(self) -> Dict[str, Any]:
        """Expose Model Context Protocol (MCP) Server description."""
        app_domain = os.getenv("APP_DOMAIN", "osmo.vn")
        api_url = f"https://api.{app_domain}"
        
        return {
            "mcp_version": "2024-11-05",
            "name": "Osmo Commerce Public MCP",
            "version": "1.0.0",
            "description": "Public MCP server endpoints for discovering products, previewing pricing, and placing orders.",
            "transport": {
                "type": "sse",
                "endpoint": f"{api_url}/api/v1/client/mcp/sse"
            },
            "capabilities": {
                "tools": {
                    "list": await self._get_public_tools_metadata()
                }
            }
        }

    # ── 3. Public Consumer MCP endpoints ──────────────────────────────────────
    @get("/api/v1/client/mcp/tools", media_type=MediaType.JSON, guards=[])
    async def list_public_tools(self) -> List[Dict[str, Any]]:
        """List consumer-safe MCP tools available for external AI agents."""
        return await self._get_public_tools_metadata()

    @post("/api/v1/client/mcp/call", media_type=MediaType.JSON, guards=[])
    async def call_public_tool(
        self,
        db_session: AsyncSession,
        request: Request,
        data: ToolCallRequest
    ) -> Dict[str, Any]:
        """Execute a consumer-safe MCP tool safely."""
        # ── [SECURITY] Layer 0: Global LLM Budget Shutdown Check ─────────
        from backend.services.agent_monitor import AgentMonitor
        if await AgentMonitor.is_shutdown():
            return {
                "status": "error",
                "message": "Cổng A2A đã tạm đóng do vượt hạn mức ngân sách LLM hàng ngày."
            }

        # Military-Grade Blacklist & Cryptographic Signature Check for public tools
        from backend.services.commerce.security.input_guard import input_guard
        await input_guard.check_military_blacklist(request)
        body_bytes = await request.body()
        await input_guard.verify_request_signature(request, body_bytes)

        name = data.name
        args = data.arguments
        ip = request.client.host if request.client else "unknown"
        if forwarded_for := request.headers.get("x-forwarded-for"):
            ip = forwarded_for.split(",")[0].strip()
        
        # Security check: Limit to public-safe tools only
        allowed_tools = {
            "search_products", "search_articles", "preview_pricing", "stealth_checkout",
            "get_product_detail", "get_article_detail", "get_promotions",
            "get_loyalty_policy", "chat_with_helen",
        }
        if name not in allowed_tools:
            await input_guard.record_security_infraction(ip)
            return {"status": "error", "message": f"Tool '{name}' is restricted or unauthorized for public agents."}

        # ── [SECURITY] Layer 2: Rate Limiting per tool per IP ────────────
        rate_block = await self._check_tool_rate_limit(ip, name)
        if rate_block:
            return rate_block

        # ── [SECURITY] Layer 3: Input Sanitization & Injection Scan ──────
        sanitize_err = self._sanitize_agent_args(args, name)
        if sanitize_err:
            await input_guard.record_security_infraction(ip)
            return sanitize_err

        # ── [SECURITY] Layer 4: Prompt Injection Scan (text-heavy fields) ─
        injection_err = await self._scan_prompt_injection(args, name, ip)
        if injection_err:
            return injection_err

        try:
            if name == "search_products":
                from backend.services.commerce.product_vector import ProductVectorService
                q = str(args.get("query", ""))
                limit = int(args.get("limit", 5))
                vector_service = ProductVectorService()
                results = await vector_service.search_semantic(db_session=db_session, query=q, limit=limit)
                return {"status": "success", "results": results}

            elif name == "search_articles":
                from backend.services.article_vector_service import ArticleVectorService
                q = str(args.get("query", ""))
                limit = int(args.get("limit", 5))
                vector_service = ArticleVectorService()
                results = await vector_service.search_semantic(db_session=db_session, query=q, limit=limit)
                return {"status": "success", "results": results}

            elif name == "preview_pricing":
                # Reuse pricing preview logic
                from backend.database.models.commerce import ProductBase, ProductVariant, UserLoyalty
                from backend.schemas.pricing import PricingInputItem
                from backend.constants.commerce import ShippingConfig
                
                items_payload = args.get("items", [])
                pricing_items: list[PricingInputItem] = []
                for it in items_payload:
                    p_id = it.get("product_id")
                    v_id = it.get("variant_id")
                    qty = int(it.get("quantity", 1))
                    
                    if v_id:
                        row = await db_session.execute(
                            select(ProductVariant.price).where(ProductVariant.id == v_id)
                        )
                        db_price = row.scalar_one_or_none()
                    else:
                        row = await db_session.execute(
                            select(ProductBase.price).where(ProductBase.id == p_id)
                        )
                        db_price = row.scalar_one_or_none()
                        
                    unit_price = float(db_price) if db_price is not None else float(it.get("price", 0))
                    pricing_items.append(PricingInputItem(
                        product_id=p_id,
                        quantity=qty,
                        unit_price=unit_price
                    ))
                
                user_payload = request.scope.get("state", {}).get("user")
                user_id = user_payload.get("id") if user_payload else None
                
                # Fetch combo deals
                from backend.services.commerce.promotion import PromotionService
                combo_deals = await PromotionService.get_active_combo_deals(db_session)
                
                if user_id:
                    # 1. Delegated User Flow: Auto-Optimize pricing
                    row = await db_session.execute(
                        select(UserLoyalty.available_points).where(UserLoyalty.user_id == user_id)
                    )
                    user_points = row.scalar_one_or_none() or 0
                    
                    from backend.database.models.promotion import Voucher
                    from backend.database import current_tenant_id
                    from datetime import datetime, timezone
                    
                    now = datetime.now(timezone.utc)
                    vouchers_stmt = select(Voucher).where(
                        Voucher.is_active == True,
                        Voucher.tenant_id == (current_tenant_id.get() or "default"),
                        (Voucher.start_date == None) | (Voucher.start_date <= now),
                        (Voucher.end_date == None) | (Voucher.end_date >= now)
                    )
                    v_res = await db_session.execute(vouchers_stmt)
                    all_vouchers = list(v_res.scalars().all())
                    
                    # Baseline calculation: No vouchers, redeem points
                    breakdown = PricingEngine.calculate(
                        items=pricing_items,
                        vouchers=[],
                        combo_deals=combo_deals,
                        points_to_redeem=user_points,
                        available_points=user_points,
                        base_shipping_fee=ShippingConfig.STANDARD_FEE
                    )
                    
                    # Try each voucher to find the absolute lowest final payable price
                    for v in all_vouchers:
                        # Pre-check minimum spend condition
                        subtotal_val = sum(it.quantity * it.unit_price for it in pricing_items)
                        working_items = [{"id": it.product_id, "qty": it.quantity, "unit_price": it.unit_price} for it in pricing_items]
                        combo_discount = PromotionService.calculate_combo_discount(working_items, combo_deals)
                        amount_after_combo = max(0.0, subtotal_val - combo_discount)
                        
                        if amount_after_combo >= v.min_spend:
                            if v.usage_limit is None or v.used_count < v.usage_limit:
                                test_breakdown = PricingEngine.calculate(
                                    items=pricing_items,
                                    vouchers=[v],
                                    combo_deals=combo_deals,
                                    points_to_redeem=user_points,
                                    available_points=user_points,
                                    base_shipping_fee=ShippingConfig.STANDARD_FEE
                                )
                                if test_breakdown.final_payable < breakdown.final_payable:
                                    breakdown = test_breakdown
                else:
                    # 2. Guest/Anonymous Flow: Standard calculation with args
                    breakdown = PricingEngine.calculate(
                        items=pricing_items,
                        vouchers=[],
                        combo_deals=combo_deals,
                        points_to_redeem=int(args.get("points_to_redeem", 0)),
                        available_points=int(args.get("available_points", 0)),
                        base_shipping_fee=ShippingConfig.STANDARD_FEE
                    )
                    
                return {"status": "success", "pricing": breakdown.model_dump()}

            elif name == "stealth_checkout":
                from litestar.exceptions import ValidationException, NotFoundException, PermissionDeniedException
                from backend.controllers.client.checkout import _map_error
                from backend.services.agent_monitor import AgentMonitor
                
                # Expose order checkout endpoint logic to MCP
                checkout_payload = StealthCheckoutSchema(**args)
                ip = request.client.host if request.client else "unknown"
                ua = request.headers.get("user-agent", "unknown")
                
                user_payload = request.scope.get("state", {}).get("user")
                user_id = user_payload.get("id") if user_payload else None
                
                try:
                    res = await CheckoutService.create_stealth_order(
                        db_session, checkout_payload, ip, ua, user_id=user_id
                    )
                    
                    if res["ok"]:
                        await AgentMonitor.record_order(is_sandbox=getattr(checkout_payload, "sandbox", False))
                        await AgentMonitor.record_ip(ip)
                        
                        # Check for webhook callback url registered in context
                        callback_url = args.get("callback_url")
                        if callback_url and res["id"]:
                            await self._register_webhook_url(res["id"], callback_url)
                            
                        return {"status": "success", "order_id": res["id"], "message": res["message"]}
                    else:
                        return {"status": "error", "message": res.get("message", "Order creation failed")}
                except (ValidationException, NotFoundException, PermissionDeniedException) as exc:
                    detail = str(getattr(exc, "detail", str(exc)))
                    code, retry, retry_after = _map_error(detail)
                    await AgentMonitor.record_error(code.value)
                    await AgentMonitor.record_ip(ip)
                    return {"status": "error", "code": code.value, "message": detail}

            elif name == "get_product_detail":
                from backend.services.commerce.product import ProductService
                from backend.services.commerce.seo_service import SeoService
                slug = str(args.get("slug", ""))
                product_id = str(args.get("product_id", ""))
                svc = ProductService()
                if slug:
                    prod = await svc.get_product_by_slug(db_session, slug, is_public=True)
                elif product_id:
                    prod = await svc.get_product(db_session, product_id, is_public=True)
                else:
                    return {"status": "error", "message": "slug or product_id is required"}
                if not prod:
                    return {"status": "error", "message": "Product not found"}
                prod_dict = prod.model_dump(by_alias=True)
                # [SECURITY] Strip admin-only & sensitive fields from agent response
                for sensitive_key in (
                    "description",       # Heavy HTML — agent uses shortDescription
                    "seo_meta",          # Internal SEO data
                    "ctv_rate_override",  # CTV commission rate (financial secret)
                    "ctvRateOverride",    # alias of above
                    "analysis_report",    # Internal AI analysis report
                    "is_ai_featured",     # Admin curation flag
                    "isAiFeatured",       # alias of above
                    "market_data",        # Internal market intelligence
                    "marketData",         # alias of above
                    "last_market_sync",   # Internal sync timestamp
                    "lastMarketSync",     # alias of above
                ):
                    prod_dict.pop(sensitive_key, None)
                return {"status": "success", "product": prod_dict}

            elif name == "get_article_detail":
                from backend.services.article_service import ArticleService
                slug = str(args.get("slug", ""))
                article_id = str(args.get("article_id", ""))
                svc = ArticleService()
                if slug:
                    art = await svc.get_article_by_slug(db_session, slug)
                elif article_id:
                    art = await svc.get_article(db_session, article_id)
                else:
                    return {"status": "error", "message": "slug or article_id is required"}
                if not art or art.status != "PUBLISHED":
                    return {"status": "error", "message": "Article not found or not published"}
                art_dict = art.model_dump(by_alias=True)
                # [SECURITY] Strip internal/admin-only fields from agent response
                for sensitive_key in (
                    "content",           # Heavy HTML — agent uses excerpt
                    "seo_meta",          # Internal SEO data
                    "seoTitle",          # Admin SEO config
                    "seoDescription",    # Admin SEO config
                    "seoKeywords",       # Admin SEO config
                ):
                    art_dict.pop(sensitive_key, None)
                return {"status": "success", "article": art_dict}

            elif name == "get_promotions":
                from backend.services.commerce.promotion import PromotionService
                from backend.database.models.promotion import Voucher
                from backend.database import current_tenant_id
                now = datetime.now(timezone.utc)
                # Active combo deals
                combo_deals = await PromotionService.get_active_combo_deals(db_session)
                combos_out = []
                for cd in combo_deals:
                    combos_out.append({
                        "id": str(cd.id), "type": cd.type, "name": cd.name,
                        "condition": cd.condition_payload, "reward": cd.reward_payload,
                        "start_date": cd.start_date.isoformat() if cd.start_date else None,
                        "end_date": cd.end_date.isoformat() if cd.end_date else None,
                    })
                # Active public vouchers (hide internal codes)
                v_stmt = select(Voucher).where(
                    Voucher.is_active == True,
                    Voucher.tenant_id == (current_tenant_id.get() or "default"),
                    (Voucher.start_date == None) | (Voucher.start_date <= now),
                    (Voucher.end_date == None) | (Voucher.end_date >= now),
                )
                v_res = await db_session.execute(v_stmt)
                vouchers_out = []
                for v in v_res.scalars().all():
                    remaining = (v.usage_limit - v.used_count) if v.usage_limit else None
                    if remaining is not None and remaining <= 0:
                        continue
                    vouchers_out.append({
                        "id": str(v.id), "type": v.type, "value": v.value,
                        "min_spend": v.min_spend, "max_discount": v.max_discount,
                        "remaining_uses": remaining,
                        "end_date": v.end_date.isoformat() if v.end_date else None,
                    })
                return {"status": "success", "combo_deals": combos_out, "vouchers": vouchers_out}

            elif name == "get_loyalty_policy":
                from backend.constants.commerce import LoyaltyConfig, ShippingConfig
                return {
                    "status": "success",
                    "loyalty": {
                        "point_value_vnd": LoyaltyConfig.POINT_VALUE,
                        "earning_rate": f"1 điểm / {int(LoyaltyConfig.EARNING_RATE_VND):,}đ chi tiêu",
                        "max_discount_percent": LoyaltyConfig.MAX_DISCOUNT_PERCENT,
                        "tiers": {
                            "STANDARD": "< 5 triệu",
                            "SILVER": f">= {int(LoyaltyConfig.TIER_SILVER_THRESHOLD):,}đ",
                            "GOLD": f">= {int(LoyaltyConfig.TIER_GOLD_THRESHOLD):,}đ",
                            "PLATINUM": f">= {int(LoyaltyConfig.TIER_PLATINUM_THRESHOLD):,}đ",
                        },
                    },
                    "shipping": {
                        "standard_fee": ShippingConfig.STANDARD_FEE,
                        "free_threshold": ShippingConfig.FREE_THRESHOLD,
                    },
                }

            elif name == "chat_with_helen":
                from backend.schemas.support import SupportRequest, SupportIntent
                from backend.services.commerce.operatives.support_agent import support_agent
                message = str(args.get("message", ""))
                if not message:
                    return {"status": "error", "message": "message is required"}
                product_slug = args.get("product_slug")
                session_id = args.get("session_id") or str(new_id())
                chat_req = SupportRequest(
                    message=message,
                    session_id=session_id,
                    product_slug=product_slug,
                    customer_name=args.get("customer_name", "AI Agent"),
                    customer_phone=args.get("customer_phone"),
                    is_agent=True,
                )
                resp = await support_agent.chat(request=chat_req, db=db_session)
                return {
                    "status": "success",
                    "reply": resp.reply,
                    "intent": resp.intent.value if resp.intent else "UNKNOWN",
                    "session_id": session_id,
                    "product_info": resp.product_info.model_dump() if resp.product_info else None,
                    "processed_order_id": resp.processed_order_id,
                }

        except Exception as e:
            logger.error(f"[Agent MCP] Public tool execution error ({name}): {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

        return {"status": "error", "message": "Unhandled public tool call"}

    # ── 4. Order Webhook callback registration ───────────────────────────────
    @post("/api/v1/client/checkout/webhook/register", media_type=MediaType.JSON, guards=[])
    async def register_order_webhook(self, data: WebhookRegisterRequest) -> Dict[str, Any]:
        """Register a callback URL to receive real-time updates for an order."""
        await self._register_webhook_url(data.order_id, data.callback_url)
        
        # Fire background task to simulate a ping verification test
        import asyncio
        asyncio.create_task(self._simulate_webhook_ping(data.order_id, data.callback_url))
        
        return {
            "status": "success",
            "message": f"Webhook registered for order {data.order_id}. Verification ping sent.",
            "order_id": data.order_id
        }

    # ── Security Helpers ──────────────────────────────────────────────────────

    # [SECURITY] Max argument sizes per field type — chống OOM / log injection
    _ARG_LIMITS = {
        "query": 500, "message": 2000, "slug": 200, "product_id": 64,
        "article_id": 64, "variant_id": 64, "product_slug": 200,
        "session_id": 128, "customer_name": 100, "customer_phone": 15,
        "customer_address": 500, "callback_url": 500, "idempotency_key": 64,
    }

    # [SECURITY] Allowed chars for ID/slug fields — blocks SQL/path traversal
    _SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_\-\.]+$")
    _SAFE_SLUG_RE = re.compile(r"^[a-z0-9\-]+$")

    @staticmethod
    def _sanitize_agent_args(args: Dict[str, Any], tool_name: str) -> Optional[Dict[str, Any]]:
        """
        [SECURITY] Sanitize all string arguments before tool execution.
        Returns error dict if validation fails, None if clean.
        """
        import re as _re

        for key, value in args.items():
            if not isinstance(value, str):
                continue

            # 1. Length cap
            max_len = AgentGatewayController._ARG_LIMITS.get(key, 1000)
            if len(value) > max_len:
                return {"status": "error", "message": f"Argument '{key}' exceeds maximum length ({max_len} chars)."}

            # 2. ID fields — strict alphanum + dash + underscore only
            if key in ("product_id", "article_id", "variant_id", "session_id", "idempotency_key"):
                if value and not AgentGatewayController._SAFE_ID_RE.match(value):
                    return {"status": "error", "message": f"Argument '{key}' contains invalid characters."}

            # 3. Slug fields — lowercase alphanum + dash only
            if key in ("slug", "product_slug"):
                if value and not AgentGatewayController._SAFE_SLUG_RE.match(value):
                    return {"status": "error", "message": f"Argument '{key}' contains invalid slug characters."}

            # 4. URL fields — must start with https://
            if key in ("callback_url",):
                if value and not value.startswith("https://"):
                    return {"status": "error", "message": f"Argument '{key}' must use HTTPS protocol."}

            # 5. Block null bytes / control chars in ALL string args
            if "\x00" in value or any(ord(c) < 32 and c not in ("\n", "\r", "\t") for c in value):
                return {"status": "error", "message": f"Argument '{key}' contains forbidden control characters."}

        return None

    @staticmethod
    async def _scan_prompt_injection(args: Dict[str, Any], tool_name: str, ip: str) -> Optional[Dict[str, Any]]:
        """
        [SECURITY] Scan text-heavy arguments for prompt injection attacks.
        Uses InputGuard regex + Dual-LLM Guardrail for chat/search tools.
        """
        from backend.services.commerce.security.input_guard import input_guard

        # Only scan tools that accept free-text user input
        scan_fields: Dict[str, list[str]] = {
            "search_products": ["query"],
            "search_articles": ["query"],
            "chat_with_helen": ["message"],
        }
        fields_to_scan = scan_fields.get(tool_name, [])
        if not fields_to_scan:
            return None

        for field in fields_to_scan:
            text = args.get(field)
            if not text or not isinstance(text, str):
                continue

            # Regex fast-path scan (InputGuard.validate)
            is_safe, reason = input_guard.validate(text)
            if not is_safe:
                await input_guard.record_security_infraction(ip)
                logger.warning(
                    "[A2A-Security] Prompt injection blocked. Tool=%s Field=%s Reason=%s IP=%s",
                    tool_name, field, reason, ip
                )
                return {
                    "status": "error",
                    "code": "PROMPT_INJECTION_BLOCKED",
                    "message": "Input bị từ chối do phát hiện nội dung vi phạm quy tắc bảo mật.",
                }

            # Dual-LLM Guardrail deep scan for chat tool (higher risk)
            if tool_name == "chat_with_helen" and len(text) >= 30:
                is_safe_async, reason_async = await input_guard.validate_async(text)
                if not is_safe_async:
                    await input_guard.record_security_infraction(ip)
                    logger.warning(
                        "[A2A-Security] LLM Guardrail blocked prompt injection. Tool=%s Reason=%s IP=%s",
                        tool_name, reason_async, ip
                    )
                    return {
                        "status": "error",
                        "code": "PROMPT_INJECTION_BLOCKED",
                        "message": "Input bị từ chối do phát hiện hành vi tấn công AI.",
                    }

        return None

    @staticmethod
    async def _check_tool_rate_limit(ip: str, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        [SECURITY] Per-tool rate limiting via Redis sliding window.
        Prevents brute-force enumeration and DDoS on individual tools.
        """
        try:
            r = xohi_memory.client
            if not r:
                return None

            # Tool-specific rate limits (requests per 60s window)
            limits = {
                "stealth_checkout": 5,
                "chat_with_helen": 20,
                "preview_pricing": 30,
                "search_products": 60,
                "search_articles": 60,
                "get_product_detail": 60,
                "get_article_detail": 60,
                "get_promotions": 30,
                "get_loyalty_policy": 30,
            }
            max_calls = limits.get(tool_name, 60)
            rate_key = f"agent:rate:{ip}:{tool_name}"

            count = await r.incr(rate_key)
            if count == 1:
                await r.expire(rate_key, 60)

            if count > max_calls:
                logger.warning("[A2A-RateLimit] IP=%s exceeded %d calls/min for tool=%s", ip, max_calls, tool_name)
                return {
                    "status": "error",
                    "code": "RATE_LIMITED",
                    "message": f"Quá giới hạn {max_calls} lần gọi/phút cho tool '{tool_name}'. Vui lòng chờ.",
                    "retry_after": 60,
                }
        except Exception as e:
            logger.warning("[A2A-RateLimit] Rate limit check failed (passing through): %s", e)

        return None

    # ── Helpers ──────────────────────────────────────────────────────────────
    async def _get_public_tools_metadata(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "search_products",
                "description": "Tìm kiếm sản phẩm bằng ngôn ngữ tự nhiên thông qua Vector Search (RAG).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Từ khóa hoặc mô tả nhu cầu tìm sản phẩm"},
                        "limit": {"type": "integer", "default": 5, "description": "Số kết quả tối đa"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_articles",
                "description": "Tìm kiếm bài viết, hướng dẫn, chính sách bán hàng bằng ngôn ngữ tự nhiên.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Câu hỏi hoặc nội dung cần tra cứu"},
                        "limit": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "preview_pricing",
                "description": "Tính toán báo giá đơn hàng trước khi mua (áp dụng điểm loyalty, ship fee).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "product_id": {"type": "string"},
                                    "variant_id": {"type": "string"},
                                    "quantity": {"type": "integer"}
                                },
                                "required": ["product_id"]
                            }
                        },
                        "points_to_redeem": {"type": "integer", "default": 0},
                        "available_points": {"type": "integer", "default": 0}
                    },
                    "required": ["items"]
                }
            },
            {
                "name": "stealth_checkout",
                "description": "Tạo đơn hàng mua sắm tự động không cần tài khoản (guest checkout).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_name": {"type": "string"},
                        "customer_phone": {"type": "string"},
                        "customer_address": {"type": "string"},
                        "total_amount": {"type": "number"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "product_id": {"type": "string"},
                                    "variant_id": {"type": "string"},
                                    "quantity": {"type": "integer"},
                                    "price": {"type": "number"}
                                },
                                "required": ["product_id", "price"]
                            }
                        },
                        "idempotency_key": {"type": "string"},
                        "sandbox": {"type": "boolean"},
                        "callback_url": {"type": "string", "description": "Webhook URL nhận trạng thái đơn"}
                    },
                    "required": ["customer_name", "customer_phone", "customer_address", "total_amount", "items"]
                }
            },
            {
                "name": "get_product_detail",
                "description": "Lấy thông tin chi tiết sản phẩm: giá, variants (combo tiers), stock, FAQs, thành phần, đánh giá.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "slug": {"type": "string", "description": "URL slug của sản phẩm"},
                        "product_id": {"type": "string", "description": "UUID của sản phẩm"}
                    }
                }
            },
            {
                "name": "get_article_detail",
                "description": "Lấy chi tiết bài viết/tin tức: tiêu đề, tóm tắt, metadata, FAQs, tags.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "slug": {"type": "string", "description": "URL slug của bài viết"},
                        "article_id": {"type": "string", "description": "UUID của bài viết"}
                    }
                }
            },
            {
                "name": "get_promotions",
                "description": "Xem danh sách khuyến mãi đang hoạt động: combo deals (mua X tặng Y, bundle) và voucher giảm giá.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_loyalty_policy",
                "description": "Xem chính sách tích điểm, hạng thành viên (Silver/Gold/Platinum), quy đổi điểm, phí ship.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "chat_with_helen",
                "description": "Chat với Helen AI — tư vấn sản phẩm, hỏi chính sách, đặt hàng qua hội thoại tự nhiên.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Nội dung tin nhắn"},
                        "product_slug": {"type": "string", "description": "Slug sản phẩm đang xem (optional context)"},
                        "session_id": {"type": "string", "description": "Session ID để duy trì cuộc hội thoại"},
                        "customer_name": {"type": "string"},
                        "customer_phone": {"type": "string"}
                    },
                    "required": ["message"]
                }
            }
        ]

    async def _register_webhook_url(self, order_id: str, callback_url: str) -> None:
        if xohi_memory.client:
            redis_key = f"order:webhook:{order_id}"
            await xohi_memory.client.set(redis_key, callback_url, ex=7 * 86400) # 7 ngày TTL
            logger.info(f"[Webhook] Registered callback for order {order_id} -> {callback_url}")

    async def _simulate_webhook_ping(self, order_id: str, callback_url: str) -> None:
        """Simulate sending a validation ping to the client's webhook."""
        await asyncio.sleep(2)
        import httpx
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                payload = {
                    "event": "webhook_verified",
                    "order_id": order_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                resp = await client.post(callback_url, json=payload)
                logger.info(f"[Webhook] Verification ping to {callback_url} returned status {resp.status_code}")
        except Exception as e:
            logger.warning(f"[Webhook] Verification ping failed to {callback_url}: {e}")

    @get("/api/v1/client/mcp/metrics", media_type=MediaType.JSON, guards=[])
    async def get_agent_metrics(self, request: Request) -> Dict[str, Any]:
        """Expose real-time agent metrics telemetry for verified agents and admins."""
        from litestar.exceptions import PermissionDeniedException
        is_agent = request.scope.get("state", {}).get("is_agent", False)
        is_admin = False
        user = request.scope.get("state", {}).get("user")
        if user and any(role in ["ADMIN", "SUPER_ADMIN", "OPERATIVE"] for role in user.get("roles", [])):
            is_admin = True
            
        if not is_agent and not is_admin:
            raise PermissionDeniedException("Bạn không có quyền truy cập dữ liệu metrics của AI Agent.")
            
        from backend.services.agent_monitor import AgentMonitor
        stats = await AgentMonitor.get_stats()
        return {"status": "success", "metrics": stats}

    @post("/api/v1/client/mcp/blacklist", media_type=MediaType.JSON, guards=[])
    async def block_ip(self, request: Request, data: IPBlockRequest) -> Dict[str, Any]:
        """Manually blacklist an IP address."""
        from litestar.exceptions import PermissionDeniedException
        is_admin = False
        user = request.scope.get("state", {}).get("user")
        if user and any(role in ["ADMIN", "SUPER_ADMIN", "OPERATIVE"] for role in user.get("roles", [])):
            is_admin = True
            
        if not is_admin:
            raise PermissionDeniedException("Bạn không có quyền quản trị để thực hiện hành động này.")
            
        if not xohi_memory.client:
            return {"status": "error", "message": "Redis is not available"}
            
        ip = data.ip.strip()
        if not ip:
            return {"status": "error", "message": "IP address cannot be empty"}
            
        blacklist_key = f"support:blacklist:{ip}"
        infraction_key = f"support:security_infractions:{ip}"
        
        await xohi_memory.client.set(blacklist_key, "1", ex=data.duration)
        await xohi_memory.client.delete(infraction_key)
        
        logger.info(f"[Military-Security] Admin manually blacklisted IP {ip} for {data.duration} seconds.")
        return {"status": "success", "message": f"Đã chặn IP {ip} thành công trong {data.duration} giây."}

    @post("/api/v1/client/mcp/whitelist", media_type=MediaType.JSON, guards=[])
    async def unblock_ip(self, request: Request, data: IPBlockRequest) -> Dict[str, Any]:
        """Manually remove an IP address from blacklist and infractions."""
        from litestar.exceptions import PermissionDeniedException
        is_admin = False
        user = request.scope.get("state", {}).get("user")
        if user and any(role in ["ADMIN", "SUPER_ADMIN", "OPERATIVE"] for role in user.get("roles", [])):
            is_admin = True
            
        if not is_admin:
            raise PermissionDeniedException("Bạn không có quyền quản trị để thực hiện hành động này.")
            
        if not xohi_memory.client:
            return {"status": "error", "message": "Redis is not available"}
            
        ip = data.ip.strip()
        if not ip:
            return {"status": "error", "message": "IP address cannot be empty"}
            
        blacklist_key = f"support:blacklist:{ip}"
        infraction_key = f"support:security_infractions:{ip}"
        
        await xohi_memory.client.delete(blacklist_key)
        await xohi_memory.client.delete(infraction_key)
        
        logger.info(f"[Military-Security] Admin manually whitelisted IP {ip}.")
        return {"status": "success", "message": f"Đã mở chặn IP {ip} thành công."}

    @post("/api/v1/client/mcp/reopen", media_type=MediaType.JSON, guards=[])
    async def reopen_gateway(self, request: Request) -> Dict[str, Any]:
        """Manually reopen the A2A Gateway after a budget lock."""
        from litestar.exceptions import PermissionDeniedException
        is_admin = False
        user = request.scope.get("state", {}).get("user")
        if user and any(role in ["ADMIN", "SUPER_ADMIN", "OPERATIVE"] for role in user.get("roles", [])):
            is_admin = True
            
        if not is_admin:
            raise PermissionDeniedException("Bạn không có quyền quản trị để thực hiện hành động này.")
            
        from backend.services.agent_monitor import AgentMonitor
        await AgentMonitor.reset_shutdown()
        
        logger.info("[Military-Security] Admin manually reopened the A2A Gateway after budget lock.")
        return {"status": "success", "message": "Đã mở lại cổng A2A và thiết lập lại bộ đếm ngân sách."}


