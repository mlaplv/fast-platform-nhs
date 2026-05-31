import logging
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy import select, func, and_
from backend.schemas.support import SupportIntent
from backend.database.models.system import SupportChatHistory
from backend.services.commerce.operatives.handlers.base import SupportContext, BaseHandler
from backend.services.commerce.operatives.handlers.guardrail import GuardrailHandler
from backend.services.commerce.operatives.handlers.order import OrderHandler
from backend.services.commerce.operatives.handlers.consultant import ConsultantHandler
from backend.services.commerce.operatives.handlers.greeting import GreetingHandler

logger = logging.getLogger("api-gateway")

class SupportRouter:
    """
    The Specialized Orchestrator (Elite V2.5 Architecture).
    Coordinates specialists to handle 5 Zones of Interaction.
    """
    
    def __init__(self):
        # The Strategic Pipeline Sequence (Elite V2.2: The Ultimate Protocol)
        self.handlers: List[BaseHandler] = [
            GuardrailHandler(),   # Priority 1: Safety/Rejection (Can terminate)
            OrderHandler(),       # Priority 2: Order Closing (SALE-FIRST: Capture conversion immediately)
            GreetingHandler(),    # Priority 3: Persona Greeting (Fast Heuristic)
            ConsultantHandler(),  # Priority 4: Knowledge Advice (L0/L1)
        ]
        
    async def process(self, ctx: SupportContext) -> SupportContext:
        """Execute the pipeline of specialists based on priority hierarchy."""

        # 1. Chống Spammer bằng cách đếm tin nhắn trong 2 phút gần nhất tại Database (Anti-DoS Shield)
        try:
            two_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=2)
            stmt = select(func.count(SupportChatHistory.id)).where(
                and_(
                    SupportChatHistory.session_id == ctx.session_id,
                    SupportChatHistory.created_at >= two_mins_ago,
                    SupportChatHistory.role == "user"
                )
            )
            recent_count = (await ctx.db.execute(stmt)).scalar() or 0
            if recent_count > 8:
                logger.warning(f"[SupportRouter] Spammer Loop Guard Triggered! SID: {ctx.session_id} | count={recent_count}")
                reply = "Dạ hệ thống Helen nhận thấy mình đang cần hỗ trợ gấp với nhiều câu hỏi liên tục. Để phục vụ tốt nhất, em xin phép chuyển tiếp cuộc gọi đến Chuyên viên Tư vấn con người hỗ trợ trực tiếp cho mình ngay nhé! 🌸 [z0]"
                ctx.replies.clear()
                ctx.replies.append(reply)
                ctx.intent = SupportIntent.ESCALATE
                return ctx
        except Exception as e:
            logger.warning(f"[SupportRouter] Spammer check failed: {e}")

        for handler in self.handlers:
            # 2. Turn-level Loop Guard trong Turn xử lý hiện tại (Phase 2 Loop Limitation)
            if ctx.tool_calls_count > 3:
                logger.warning(f"[SupportRouter] Turn Loop Guard Triggered! SID: {ctx.session_id} | calls={ctx.tool_calls_count}")
                reply = "Dạ Helen xin lỗi, câu hỏi đang yêu cầu quá nhiều bước xử lý phức tạp. Em xin phép chuyển hướng đến chuyên viên hỗ trợ trực tiếp để phục vụ mình tốt nhất nhé! 🙏 [z0]"
                ctx.replies.clear()
                ctx.replies.append(reply)
                ctx.intent = SupportIntent.ESCALATE
                return ctx

            try:
                # If a handler returns True, it has 'consumed' the logic and stops further specialists.
                if await handler.handle(ctx):
                    logger.debug(f"[SupportRouter] Pipeline consumed by {handler.__class__.__name__}")
                    break
            except Exception as e:
                logger.error(f"[SupportRouter] Critical error in {handler.__class__.__name__}: {e}")
                continue # Try the next handler if one fails
                
        # Final Post-Processing logic can go here (formatting, etc.)
        return ctx
