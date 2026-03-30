from __future__ import annotations
import logging
from litestar import Controller, post, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.client.checkout import (
    StealthCheckoutSchema, 
    CustomerLookupSchema,
    CustomerLookupResponseSchema,
    StealthCheckoutSchema, 
    CustomerLookupSchema,
    CustomerLookupResponseSchema
)
from backend.schemas.common import SuccessResponse
from backend.services.commerce.checkout import CheckoutService

logger = logging.getLogger("api-gateway")

class CheckoutController(Controller):
    """Elite V2.2: specialized controller for Silent Assassin Funnel."""
    path = "/api/v1/client/checkout"

    @post("/stealth", guards=[])  # PUBLIC: Silent Assassin Checkout
    async def create_stealth_order(
        self,
        request: Request,
        db_session: AsyncSession,
        data: StealthCheckoutSchema
    ) -> SuccessResponse:
        """PUBLIC: Handle stealth checkout with Anti-Fraud integration."""
        # Extract IP and User-Agent
        ip = request.client.host if request.client else "unknown"
        # Check for Forwarded-For (Rule R00: Zero-Mock IP)
        if forwarded_for := request.headers.get("x-forwarded-for"):
            ip = forwarded_for.split(",")[0].strip()

        ua = request.headers.get("user-agent", "unknown")

        res = await CheckoutService.create_stealth_order(db_session, data, ip, ua)
        return SuccessResponse(id=res["id"], ok=res["ok"])

    @post("/lookup", guards=[])  # PUBLIC: Identity Lookup
    async def lookup_customer(
        self,
        db_session: AsyncSession,
        data: CustomerLookupSchema
    ) -> CustomerLookupResponseSchema:
        """Lookup previous identity by phone. Returns ONLY recognition status (Identity Shield)."""
        res = await CheckoutService.lookup_customer(db_session, data.phone, data.fingerprint)
        return CustomerLookupResponseSchema(**res)

