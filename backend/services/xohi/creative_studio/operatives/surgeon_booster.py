import logging
from datetime import datetime, timezone
from pydantic_ai import Agent
from backend.services.xohi.creative_studio.models.schemas import SurgeonBoosterReport
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.agent_base import BaseAgentOperative
from backend.utils.text import extract_readable_text
from backend.services.xohi.prompts import composer
from backend.services.xohi.prompts.shields.service import shield_service

logger = logging.getLogger("api-gateway")


class SurgeonBooster(BaseAgentOperative):
    """
    CNS V87.0: Surgeon Booster Operative.
    Elite V2.2: Performs ad-hoc content enrichment and phẫu thuật with NPO.
    """
    agent_id_class = "surgeon_booster"

    def __init__(self, **kwargs: object):
        super().__init__(agent_id="surgeon_booster")
        self._agent = Agent(
            output_type=SurgeonBoosterReport,
            retries=2
        )

    async def chat(self, request: object, **kwargs: object) -> SurgeonBoosterReport:
        """Standard Heritage Entry."""
        content_raw = str(getattr(request, "draft_content", "")) or str(kwargs.get("content", ""))
        content = extract_readable_text(content_raw)
        topic = str(getattr(request, "topic", "")) or str(kwargs.get("topic", ""))
        campaign_id = getattr(request, "id", str(kwargs.get("campaign_id", "adhoc")))
        
        logs: list[str] = [
            f"🚀 Surgeon Booster khởi động tại {datetime.now(timezone.utc).strftime('%H:%M:%S')}...",
        ]
        await self._emit_progress(campaign_id, logs[-1])

        if not content or len(content.strip()) < 50:
            return SurgeonBoosterReport(
                patches=[],
                summary="Nội dung quá ngắn để phẫu thuật.",
                logs=logs
            )

        topic_prefix = f"[CHỦ ĐỀ]: {topic}\n\n" if topic else ""
        prompt = f"{topic_prefix}[NỘI DUNG CẦN PHẪU THUẬT]:\n{content[:10000]}"

        try:
            logs.append("🧠 Đang phân tích cấu trúc & tìm kiếm cơ hội tối ưu EEAT...")
            await self._emit_progress(campaign_id, logs[-1])
            
            logs.append("🔪 Đang thực hiện phẫu thuật nội dung bằng Neural Booster...")
            await self._emit_progress(campaign_id, logs[-1])
            
            # [CNS-V89] Resolve Context via Centralized Intelligence
            context = await self._resolve_xohi_context(request, content, "booster")
            await self._emit_progress(campaign_id, context["log_msg"])

            logs.append(f"🛡️ [ROLE] Đã xác nhận phân vai tác chiến: {context['role_assignment']}")
            await self._emit_progress(campaign_id, logs[-1])

            logs.append(f"🛡️ [SHIELD] Đã kích hoạt SGE Shield V2.1 (Anti-AI Footprint)")
            await self._emit_progress(campaign_id, logs[-1])

            is_adhoc = campaign_id == "adhoc"
            logs.append(f"🛡️ [SAFETY] Chế độ Ad-hoc Safety: {'ACTIVE' if is_adhoc else 'CAMPAIGN_MODE'}")
            await self._emit_progress(campaign_id, logs[-1])
            
            shield = shield_service.get_shield_component(seed=str(campaign_id))
            composer.register_component(shield)
            
            # ELITE V2.2: Use extra_components to maintain thread-safety
            system_prompt = composer.compose("booster_surgeon", context=context, extra_components=[shield.id])
            
            logs.append(f"📡 [CONNECT] Kết nối Neural Bridge (Role: PRO)...")
            await self._emit_progress(campaign_id, logs[-1])

            result = await trinity_bridge.run(self._agent, prompt, system_prompt=system_prompt, role="pro", timeout=90.0)
            
            # SGE Shield V2.0: Lexical Sanitizer
            if hasattr(result, "patches"):
                for patch in result.patches:
                    if hasattr(patch, "new_text"):
                        patch.new_text = shield_service.sanitize(patch.new_text)
            
            logs.append(f"✅ Hoàn tất! {len(result.patches)} thao tác phẫu thuật sẵn sàng.")
            await self._emit_progress(campaign_id, logs[-1], status="DONE")
            
            result.logs = logs
            return result
        except Exception as exc:
            logger.error(f"[SurgeonBooster] Lỗi phẫu thuật: {exc}", exc_info=True)
            err_msg = f"❌ Lỗi phẫu thuật: {str(exc)[:100]}"
            await self._emit_progress(campaign_id, err_msg, status="FAILED")
            return SurgeonBoosterReport(
                patches=[],
                summary=f"Phẫu thuật thất bại: {str(exc)[:100]}",
                logs=[*logs, err_msg]
            )

# Heritage Backdoor for legacy calls
async def run_surgeon_boost(content: str, topic: str = "") -> SurgeonBoosterReport:
    booster = SurgeonBooster()
    return await booster.chat(None, content=content, topic=topic)
