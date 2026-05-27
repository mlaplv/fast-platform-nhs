from __future__ import annotations
import logging
from litestar import Controller, post, Request, Response
from litestar.datastructures import Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.client.checkout import (
    StealthCheckoutSchema, 
    CustomerLookupSchema,
    CustomerLookupResponseSchema
)
from backend.schemas.common import SuccessResponse
from backend.services.commerce.checkout import CheckoutService

logger = logging.getLogger("api-gateway")

class CheckoutController(Controller):
    path = "/api/v1/client/checkout"

    @post("/stealth", guards=[])
    async def create_stealth_order(
        self,
        request: Request,
        db_session: AsyncSession,
        data: StealthCheckoutSchema
    ) -> Response:
        """Handle stealth checkout with CTV attribution + anti-fraud integration."""
        ip = request.client.host if request.client else "unknown"
        if forwarded_for := request.headers.get("x-forwarded-for"):
            ip = forwarded_for.split(",")[0].strip()

        ua = request.headers.get("user-agent", "unknown")
        user_id = request.scope.get("state", {}).get("user", {}).get("id")

        # CTV Attribution: Cookie __ctv (priority) > payload.ctv_code (manual input)
        ctv_code: str | None = None
        attribution_source: str | None = None
        cookie_ctv = request.cookies.get("__ctv")
        payload_ctv = getattr(data, "ctv_code", None)

        if cookie_ctv:
            ctv_code = cookie_ctv.strip()   # Do NOT upper() — encrypted tokens are case-sensitive
            attribution_source = "cookie"
        elif payload_ctv:
            ctv_code = payload_ctv.strip()  # normalize in validate_ctv_code
            attribution_source = "manual"

        res = await CheckoutService.create_stealth_order(
            db_session, data, ip, ua,
            user_id=user_id,
            ctv_code=ctv_code,
            attribution_source=attribution_source,
        )

        response = Response(
            content=SuccessResponse(id=res["id"], ok=res["ok"])
        )

        if res["ok"] and res["id"]:
            cookie = Cookie(
                key="__ox",
                value=res["id"],
                max_age=86400,  # 24h
                httponly=True,
                secure=True,
                samesite="lax",
                path="/"
            )
            response.set_cookie(cookie)

        return response

    @post("/lookup", guards=[])
    async def lookup_customer(
        self,
        request: Request,
        db_session: AsyncSession,
        data: CustomerLookupSchema
    ) -> CustomerLookupResponseSchema:
        ox_cookie = request.cookies.get("__ox")
        user_id = request.scope.get("state", {}).get("user", {}).get("id")
        res = await CheckoutService.lookup_customer(db_session, data.phone, ox_cookie=ox_cookie, user_id=user_id)
        return CustomerLookupResponseSchema(**res)

