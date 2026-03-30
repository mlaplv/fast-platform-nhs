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
        response: Response,
        db_session: AsyncSession,
        data: StealthCheckoutSchema
    ) -> SuccessResponse:
        """Handle stealth checkout with anti-fraud integration."""
        ip = request.client.host if request.client else "unknown"
        if forwarded_for := request.headers.get("x-forwarded-for"):
            ip = forwarded_for.split(",")[0].strip()

        ua = request.headers.get("user-agent", "unknown")

        res = await CheckoutService.create_stealth_order(db_session, data, ip, ua)
        
        if res["ok"] and res["id"]:
            cookie = Cookie(
                key="__ox",
                value=res["id"],
                max_age=86400, # 24h
                httponly=True,
                secure=True,
                samesite="lax",
                path="/"
            )
            response.set_cookie(cookie)

        return SuccessResponse(id=res["id"], ok=res["ok"])

    @post("/lookup", guards=[])
    async def lookup_customer(
        self,
        request: Request,
        db_session: AsyncSession,
        data: CustomerLookupSchema
    ) -> CustomerLookupResponseSchema:
        ox_cookie = request.cookies.get("__ox")
        res = await CheckoutService.lookup_customer(db_session, data.phone, ox_cookie=ox_cookie)
        return CustomerLookupResponseSchema(**res)

