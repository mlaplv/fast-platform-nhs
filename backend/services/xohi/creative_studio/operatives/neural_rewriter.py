import logging
from datetime import datetime, timezone
from pydantic_ai import Agent
from backend.services.ai_engine.core.agent_base import BaseAgentOperative, XoHiProgressMixin
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("api-gateway")

_NEURAL_REWRITE_PROMPT = """[ROLE] SENIOR NEURAL CREATIVE — XoHi Elite V2.2
Nhiệm vụ: Viết lại toàn bộ bài viết dựa trên các luận điểm phản biện (Copyright Verdict) để đạt 100% Unique và Viral Edge.

[QUY TẮC TÁC CHIẾN — ELITE PROTOCOL]
1. 🔪 TRIỆT ĐỂ: Không chỉ sửa lỗi. Hãy đập đi xây lại cấu trúc nếu cần để bài viết mang bản sắc riêng, không còn dấu vết của đối thủ.
2. 💉 INFORMATION GAIN: Tiêm thêm dữ liệu thực tế, số liệu, hoặc góc nhìn chuyên sâu (EEAT) vào các đoạn bị phản biện là "thiếu muối" hoặc "xào nấu".
3. ⚡ VIRAL EDGE: Sử dụng ngôn ngữ sắc bén, tiêu đề giật gân nhưng chuyên nghiệp, cấu trúc kể chuyện (Storytelling) để giữ chân người đọc.
4. 🛡️ HTML PRESERVATION: Giữ lại các thẻ HTML quan trọng (<h1>, <h2>, <ul>, <img>) nhưng có thể thay đổi nội dung bên trong một cách sáng tạo.
5. 🚫 KHÔNG GIẢI THÍCH: Trả về kết quả là bài viết hoàn chỉnh dưới dạng HTML thuần.

[THÔNG TIN PHẢN BIỆN]:
{feedback}
"""

class NeuralRewriter(BaseAgentOperative, XoHiProgressMixin):
    """
    CNS V88.5: Neural Creative Rewriter.
    Handles full article rewriting based on analysis feedback.
    """
    agent_id_class = "neural_rewriter"

    def __init__(self, **kwargs: object):
        super().__init__(agent_id="neural_rewriter")
        # We use str output type because it returns the whole HTML article
        self._agent = Agent(
            output_type=str,
            retries=2
        )

    async def chat(self, request: object, **kwargs: object) -> str:
        """Standard Heritage Entry."""
        content = str(kwargs.get("content", ""))
        topic = str(kwargs.get("topic", ""))
        feedback = str(kwargs.get("feedback", ""))
        campaign_id = str(kwargs.get("campaign_id", "adhoc"))
        
        logs: list[str] = [
            f"🚀 Neural Creative Rewrite khởi động cho chủ đề: '{topic}'...",
        ]
        await self._emit_progress(campaign_id, logs[-1])

        if not content:
            return "Nội dung trống, không thể viết lại."

        system_prompt = _NEURAL_REWRITE_PROMPT.format(feedback=feedback)
        prompt = f"[CHỦ ĐỀ]: {topic}\n\n[NỘI DUNG GỐC]:\n{content[:15000]}"

        try:
            logs.append("🧠 Đang giải mã luận điểm phản biện & lập kế hoạch sáng tạo...")
            await self._emit_progress(campaign_id, logs[-1])
            
            logs.append("🖋️ Xohi đang múa bút sáng tạo bài viết mới...")
            await self._emit_progress(campaign_id, logs[-1])
            
            # Using trinity_bridge.run directly for simple string return
            response = await trinity_bridge.run(
                self._agent, 
                prompt, 
                system_prompt=system_prompt,
                role="pro", 
                timeout=120.0
            )
            
            # If response is an object with 'data' attribute, extract it
            final_text = getattr(response, "data", str(response))
            
            logs.append("✅ Phẫu thuật sáng tạo hoàn tất! Bài viết mới đã sẵn sàng.")
            await self._emit_progress(campaign_id, logs[-1], status="DONE")
            
            return final_text
        except Exception as exc:
            logger.error(f"[NeuralRewriter] Lỗi viết lại: {exc}", exc_info=True)
            err_msg = f"❌ Lỗi Neural Creative: {str(exc)[:100]}"
            await self._emit_progress(campaign_id, err_msg, status="FAILED")
            return content # Fallback to original content

# Heritage Backdoor
async def run_neural_rewrite(content: str, topic: str = "", feedback: str = "", campaign_id: str = "adhoc") -> str:
    rewriter = NeuralRewriter()
    return await rewriter.chat(None, content=content, topic=topic, feedback=feedback, campaign_id=campaign_id)
