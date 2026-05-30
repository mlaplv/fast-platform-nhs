"""
ViralController — Elite Anti-Fraud Share-to-Unlock Endpoints
POST /api/v1/client/viral/share-intent
POST /api/v1/client/viral/verify-share
"""
from __future__ import annotations

import logging
from typing import Optional

from litestar import Controller, get, post, Response
from litestar.connection import Request
from litestar.exceptions import TooManyRequestsException, NotFoundException, HTTPException, NotAuthorizedException
from litestar.params import Parameter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from backend.schemas.viral import (
    ShareIntentRequest,
    ShareIntentResponse,
    VerifyShareRequest,
    VerifyShareResponse,
)
from backend.services.viral_share_service import viral_share_service


logger = logging.getLogger("api-gateway.viral")


def _extract_ip(request: Request) -> str:
    """
    Extracts the real client IP.
    Priority: x-real-ip → x-forwarded-for (first) → client host.
    """
    headers = request.headers
    real_ip = headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    forwarded_for = headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return str(request.client.host) if request.client else "unknown"


def _require_user(request: Request) -> dict:
    """Elite V2026: Enforce login for viral endpoints — same pattern as CTV controller."""
    user_state = request.scope.get("state", {}).get("user")
    if not user_state:
        raise NotAuthorizedException("Bạn cần đăng nhập để tham gia chương trình chia sẻ nhận quà!")
    return user_state


class ViralController(Controller):
    """
    Viral share endpoints — Auth required for share/verify.
    Anti-abuse handled by device fingerprint + HMAC + Redis rate limit.
    """
    path = "/api/v1/client/viral"
    tags = ["Client Viral"]

    @post("/share-intent")
    async def share_intent(
        self,
        request: Request,
        data: ShareIntentRequest,
    ) -> ShareIntentResponse:
        """
        Issue a one-time HMAC token for a share intent.
        Requires: Authenticated session (cookie).
        Rate limit: 10 req/IP/hour.

        Flow:
          1. Verify login (HttpOnly cookie JWT)
          2. Extract real IP + User-Agent + Accept-Language → fingerprint
          3. Check rate limit (Lua atomic in Redis)
          4. Sign token: HMAC-SHA256(secret, "product_id:fingerprint:timestamp")
          5. Store token in Redis with 24h TTL
          6. Return { token, fingerprint, expires_at }
        """
        user_state = _require_user(request)  # 🔒 Must be logged in
        user_id = user_state.get("id")
        ip = _extract_ip(request)
        user_agent = request.headers.get("user-agent", "")
        accept_language = request.headers.get("accept-language", "")

        result = await viral_share_service.issue_share_token(
            product_id=data.product_id,
            ip=ip,
            user_agent=user_agent,
            accept_language=accept_language,
        )

        if result is None:
            logger.warning(f"[ViralController] Rate limit hit — IP={ip}, user={user_id}, product={data.product_id}")
            raise TooManyRequestsException(
                "Bạn đã yêu cầu chia sẻ quá nhiều lần. Vui lòng thử lại sau 1 giờ."
            )

        return ShareIntentResponse(
            token=str(result["token"]),
            fingerprint=str(result["fingerprint"]),
            expires_at=int(result["expires_at"]),
        )



    @post("/verify-share")
    async def verify_share(
        self,
        request: Request,
        db_session: AsyncSession,
        data: VerifyShareRequest,
    ) -> VerifyShareResponse:
        """
        Verify the HMAC token and redeem the share reward (voucher from DB).
        Requires: Authenticated session (cookie).

        Anti-fraud layers:
          1. Login required — user_id bound to redemption
          2. Token must exist in Redis (not expired, not previously used)
          3. HMAC must match (cannot be forged without VIRAL_SECRET_KEY)
          4. social_post_id from FB.ui() — proof of actual share action
          5. Token is DELETED after first successful verify (OTT — replay-proof)
          6. Voucher is read from DB, not from page source/metadata
        """
        user_state = _require_user(request)  # 🔒 Must be logged in
        user_id = user_state.get("id")
        ip = _extract_ip(request)

        logger.info(
            f"[ViralController] Verify attempt — product={data.product_id}, "
            f"IP={ip}, FP={data.fingerprint[:16]}…, user_id={user_id}, "
            f"post_id={'YES' if data.social_post_id else 'NONE'}"
        )

        telemetry_dict = data.telemetry.model_dump() if data.telemetry else None
        if telemetry_dict is not None:
            telemetry_dict["client_ip"] = ip

        try:
            result = await viral_share_service.verify_and_redeem(
                product_id=data.product_id,
                fingerprint=data.fingerprint,
                token=data.token,
                db_session=db_session,
                voucher_id=data.voucher_id,
                telemetry_data=telemetry_dict,
                user_id=user_id,
                social_post_id=data.social_post_id,
            )
        except ValueError as val_err:
            logger.warning(
                f"[ViralController] VERIFY FAILED (ValueError) — product={data.product_id}, IP={ip}, Error={val_err}"
            )
            raise HTTPException(
                status_code=400,
                detail=str(val_err)
            )

        if result is None:
            logger.warning(
                f"[ViralController] VERIFY FAILED — product={data.product_id}, IP={ip}"
            )
            raise HTTPException(
                status_code=400,
                detail="Mã xác nhận không hợp lệ hoặc bạn chưa hoàn tất chia sẻ trên mạng xã hội. Vui lòng chia sẻ lại nhé!"
            )

        return VerifyShareResponse(
            valid=bool(result["valid"]),
            voucher_code=str(result["voucher_code"]),
            voucher_label=str(result["voucher_label"]),
            voucher_value=float(result["voucher_value"]),
            voucher_type=str(result["voucher_type"]),
            min_spend=float(result["min_spend"]),
            trust_score=float(result.get("trust_score", 0.0)),
        )

    @get("/campaign/{voucher_id:str}")
    async def get_campaign(
        self,
        db_session: AsyncSession,
        voucher_id: str,
    ) -> dict:
        """
        Public endpoint to get viral campaign metadata for a voucher.
        Used by the community progress bar to show goals/messages.
        """
        result = await viral_share_service.get_campaign_details(voucher_id, db_session)
        if not result:
            return {
                "exists": False,
                "enabled": False,
                "voucher_id": voucher_id,
                "voucher_label": "Quà tặng đặc biệt",
                "cta_text": "Chia Sẻ Nhận Quà",
                "share_text": "Nhận ngay quà tặng lan tỏa cực hot!"
            }
        return {
            "exists": True,
            "enabled": result.get("is_active", True),
            **result
        }



