import uuid
import logging
import asyncio
import time
import traceback
from datetime import datetime, timezone
from typing import Dict, Union, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.campaign_service import campaign_service
from backend.services.xohi.creative_studio.models.schemas import AgentResponse, AgentSignal
from backend.services.xohi.creative_studio.registry import registry
from backend.services.event_bus import event_bus
from backend.constants.agentic import STEP_ARTIFICIAL_LATENCY_SECONDS
from backend.database.alchemy_config import alchemy_config

logger = logging.getLogger("api-gateway")

class ExecutionEngine:
    def __init__(self, orchestrator: "ContentOrchestrator"):
        self.orchestrator = orchestrator

    async def trigger_step(self, campaign_id: str, force_step: Optional[int] = None):
        await asyncio.sleep(0.05)
        async with self.orchestrator.semaphore:
            session_maker = alchemy_config.create_session_maker()
            async with session_maker() as session:
                await self._execute_step(campaign_id, session, force_step=force_step)
                await session.commit()

    async def _execute_step(self, campaign_id: str, session: AsyncSession, force_step: Optional[int] = None):
        campaign = await campaign_service.get_campaign(session, campaign_id)
        if not campaign: return

        step = force_step if force_step is not None else campaign["current_step"]
        start_time = time.time()
        logger.info(f"[Content Factory] Executing Step {step} for {campaign_id}")

        await asyncio.sleep(STEP_ARTIFICIAL_LATENCY_SECONDS)
        if campaign["current_step"] != step:
            await campaign_service.update_campaign(session, campaign_id, {"current_step": step})

        try:
            messages = {1: "✍️ Đang phân tích chủ đề...", 2: "🔍 Đang tìm ảnh...", 3: "📝 Lập dàn ý...", 4: "🖋️ AI đang viết...", 5: "🛡️ Đang kiểm tra đạo văn...", 6: "📦 Đang hoàn thiện..."}
            await self._emit_progress(campaign_id, step, messages.get(step, "Đang xử lý..."), user_id=campaign["user_id"])

            # Phase 73: Retrieve operative from registry for steps 1-4 and 6
            operative = registry.get_operative(step)

            # Phase 76.5: Neural Streaming Waterfall (Step 4 Special Handling)
            if step == 4 and hasattr(operative, "stream_draft"):
                # Ensure we have the latest campaign state
                campaign = await campaign_service.get_campaign(session, campaign_id)
                # Clear stale content
                await campaign_service.update_campaign(session, campaign_id, {"draft_content": ""})

                full_content = ""
                async for chunk in operative.stream_draft(campaign):
                    if chunk["type"] == "chunk":
                        text = chunk["text"]
                        full_content += text
                        # Emit chunk to event bus for real-time UI updates
                        await event_bus.emit("CONTENT_CHUNK", {
                            "campaign_id": campaign_id,
                            "text": text,
                            "step": 4
                        })
                    elif chunk["type"] == "final":
                        # Step 4 logic completion
                        await campaign_service.update_campaign(session, campaign_id, {"draft_content": chunk["content"]})
                        response = AgentResponse(
                            signal=AgentSignal.PROCEED_NEXT,
                            message="Draft content generated — Viral 2026 Edition.",
                            data={"content": chunk["content"]}
                        )
                        break
                    elif chunk["type"] == "error":
                        await self._log_error(campaign, session, "ERROR", chunk["message"])
                        return

                # Mock a finished task for the existing logic below
                response_task = asyncio.Future()
                response_task.set_result(response)
            else:
                response_task = asyncio.create_task(operative.execute(campaign_id, session, step=step))

            # Phase 76: Zero-Latency Heartbeat (V76)
            pulse_count = 0
            while not response_task.done():
                try:
                    done, pending = await asyncio.wait([response_task], timeout=10.0)
                except Exception:
                    if response_task.done(): break
                    raise

                if not response_task.done():
                    pulse_count += 1
                    logger.debug(f"[Content Factory] Pulse {pulse_count}: Step {step} still working for {campaign_id}")

                    msg = messages.get(step, "Đang xử lý...")
                    if step == 4:
                        sub_msgs = [
                            "Đang phân tích và nhào nặn tiêu đề...",
                            "Đang xây dựng nội dung chi tiết theo dàn ý...",
                            "Đang căn chỉnh mật độ từ khóa chuẩn SEO...",
                            "Đang tối ưu hóa hình ảnh và thẻ figure...",
                            "Đang kiểm tra tính nhất quán của văn phong...",
                            "Đang hoàn thiện những bước cuối cùng..."
                        ]
                        idx = min(pulse_count - 1, len(sub_msgs) - 1)
                        msg = sub_msgs[idx]

                    await self._emit_progress(campaign_id, step, msg, user_id=campaign["user_id"])

            response = await response_task
            if not isinstance(response, AgentResponse):
                response = AgentResponse(signal=AgentSignal.PROCEED_NEXT, message="Legacy success", data={"raw": response})

            update_fields = {}
            # Phase 73: Sync metadata from response if present
            if response.data and "gold_metadata" in response.data:
                update_fields["gold_metadata"] = response.data["gold_metadata"]

            if response.signal == AgentSignal.REDO_PREVIOUS:
                if await self._handle_backtrack(campaign, session, step):
                    return

            if response.signal == AgentSignal.FAIL_GRACEFULLY:
                await self._log_error(campaign, session, "ERROR", f"Agent Escalation: {response.message}")
                return

            # Update campaign data from response (Specific step fields)
            if response.data:
                if step == 1:
                    update_fields["topic_data"] = response.data
                    update_fields["gold_metadata"] = response.data # First seal
                elif step == 2:
                    raw_assets = response.data.get("assets", response.data) if isinstance(response.data, dict) else response.data
                    update_fields["assets_data"] = raw_assets
                elif step == 3:
                    update_fields["outline_data"] = response.data.get("outline", response.data) if isinstance(response.data, dict) else response.data
                elif step == 4:
                    if "content" in response.data:
                        update_fields["draft_content"] = response.data["content"]
                elif step == 5:
                    if "score" in response.data:
                        update_fields["unique_score"] = response.data["score"]
                elif step == 6:
                    if "final_html" in response.data:
                        update_fields["final_html"] = response.data["final_html"]
                    if "assets" in response.data:
                        update_fields["assets_data"] = response.data["assets"]

            # Phase 73: Always set to WAITING_FOR_REVIEW after an automated step completes
            update_fields["status"] = "WAITING_FOR_REVIEW"
            if step == 2:
                update_fields["search_count"] = (campaign.get("search_count") or 0) + 1

            # Perform the update
            await campaign_service.update_campaign(session, campaign_id, update_fields)

            # Construct payload for event bus (need fresh data for some steps)
            # Fetch fresh dict if needed or use update_fields
            final_campaign = await campaign_service.get_campaign(session, campaign_id)

            payload: Dict[str, object] = {
                "campaign_id": campaign_id,
                "step": step,
                "status": final_campaign["status"],
                "data": {}
            }
            payload_data = payload["data"]
            if step == 1:
                td = final_campaign["topic_data"]
                payload_data["topic_data"] = td
                payload_data["keywords"] = td
            elif step == 2:
                payload_data["assets"] = final_campaign["assets_data"]
            elif step == 3:
                payload_data["outline"] = final_campaign["outline_data"]
            elif step == 4:
                payload_data["draft_content"] = final_campaign["draft_content"]
            elif step == 5:
                payload_data["unique_score"] = final_campaign["unique_score"]
            elif step == 6:
                payload_data["assets"] = final_campaign["assets_data"]
                payload_data["final_html"] = final_campaign["final_html"]

            payload_data["gold_metadata"] = final_campaign["gold_metadata"]

            await event_bus.emit("CONTENT_STEP_COMPLETED", payload)
            logger.info(f"[Content Factory] Step {step} SUCCESS in {time.time() - start_time:.2f}s")

        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"[Content Factory] Step {step} FAILED for {campaign_id}:\n{error_trace}")
            await self._log_error(campaign, session, "ERROR", str(e))

    async def _handle_backtrack(self, campaign: Dict, session: AsyncSession, step: int) -> bool:
        count = await campaign_service.get_event_count(session, campaign["id"], "BACKTRACK", step)

        if count < 2:
            await campaign_service.add_event(
                session, campaign["id"], "BACKTRACK",
                {"step": step, "count": count + 1},
                campaign["tenant_id"]
            )
            new_step = max(1, step - 1)
            await campaign_service.update_campaign(session, campaign["id"], {
                "current_step": new_step,
                "status": "PROCESSING"
            })
            asyncio.create_task(self.trigger_step(campaign["id"], force_step=new_step))
            return True
        return False

    async def _log_error(self, campaign: Dict, session: AsyncSession, status: str, error_msg: str):
        await campaign_service.update_campaign(session, campaign["id"], {"status": status})
        await campaign_service.add_event(
            session, campaign["id"], "ERROR",
            {"step": campaign["current_step"], "error": error_msg},
            campaign["tenant_id"]
        )

