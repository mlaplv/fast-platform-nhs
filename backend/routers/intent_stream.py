# backend/api/v1/controllers/intent_stream.py
"""SSE Streaming Intent Endpoint — Real-time phased response (Elite V2.2 Proxy).
Rule 01 compliance: Moved implementation to .intent.core
"""
import logging
from litestar import Controller, post, Request
from backend.routers.intent_core import IntentStreamCore
from litestar.di import Provide
from litestar.response import Stream

from backend.schemas.intent import IntentRequest
from backend.database.repositories import (
    UserRepository, ChatMessageRepository, VoiceProfileRepository,
    AgentTelemetryLogRepository, OrderRepository, ProductBaseRepository,
    ContentCampaignRepository,
    provide_user_repo, provide_chat_repo, provide_voice_repo,
    provide_telemetry_repo, provide_order_repo, provide_product_repo,
    provide_campaign_repo
)
from backend.constants.permissions import PermissionEnum
from backend.guards import PermissionGuard

logger = logging.getLogger("api-gateway")

class IntentStreamController(Controller):
    guards = [PermissionGuard(PermissionEnum.SYS_ADMIN)]
    """SSE streaming version of IntentController — phased real-time response."""
    path = "/api/v1/intent"
    dependencies = {
        "user_repo": Provide(provide_user_repo),
        "chat_repo": Provide(provide_chat_repo),
        "profile_repo": Provide(provide_voice_repo),
        "telemetry_repo": Provide(provide_telemetry_repo),
        "order_repo": Provide(provide_order_repo),
        "product_repo": Provide(provide_product_repo),
        "campaign_repo": Provide(provide_campaign_repo),
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.core = IntentStreamCore()

    @post("/stream", status_code=200)
    async def stream_intent(
        self,
        request: Request,
        data: IntentRequest,
        user_repo: UserRepository,
        chat_repo: ChatMessageRepository,
        profile_repo: VoiceProfileRepository,
        telemetry_repo: AgentTelemetryLogRepository,
        order_repo: OrderRepository,
        product_repo: ProductBaseRepository,
        campaign_repo: ContentCampaignRepository,
    ) -> Stream:
        """Stream intent processing phases via SSE."""
        return await self.core.handle_stream(
            request=request,
            data=data,
            user_repo=user_repo,
            chat_repo=chat_repo,
            profile_repo=profile_repo,
            telemetry_repo=telemetry_repo,
            order_repo=order_repo,
            product_repo=product_repo,
            campaign_repo=campaign_repo
        )
