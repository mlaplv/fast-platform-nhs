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
from litestar.exceptions import TooManyRequestsException, NotFoundException, HTTPException
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


class ViralController(Controller):
    """
    Public viral share endpoints — no auth required.
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
        Rate limit: 10 req/IP/hour.

        Flow:
          1. Extract real IP + User-Agent + Accept-Language → fingerprint
          2. Check rate limit (Lua atomic in Redis)
          3. Sign token: HMAC-SHA256(secret, "product_id:fingerprint:timestamp")
          4. Store token in Redis with 24h TTL
          5. Return { token, fingerprint, expires_at }
        """
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
            logger.warning(f"[ViralController] Rate limit hit — IP={ip}, product={data.product_id}")
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

        Anti-fraud layers:
          1. Token must exist in Redis (not expired, not previously used)
          2. HMAC must match (cannot be forged without VIRAL_SECRET_KEY)
          3. Token is DELETED after first successful verify (OTT — replay-proof)
          4. Voucher is read from DB, not from page source/metadata

        Returns voucher details on success, 401 on any failure.
        """
        ip = _extract_ip(request)
        user_state = request.scope.get("state", {}).get("user", {})
        user_id = user_state.get("id")

        logger.info(
            f"[ViralController] Verify attempt — product={data.product_id}, "
            f"IP={ip}, FP={data.fingerprint[:16]}…, user_id={user_id}"
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



