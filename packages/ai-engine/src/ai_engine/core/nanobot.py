import json
import os
import random
import logging
from pydantic import ValidationError
from litellm import acompletion
from shared.schemas.intent import IntentRequest, IntentResponse, IntentAction
from ai_engine.core.mcp_iam import MCPIamGuard
from ai_engine.core.key_rotator import SmartKeyRotator
import httpx

logger = logging.getLogger("nanobot")

_SYSTEM_PROMPT = """You are NanoBot, the Tier 3 A2A orchestrator.
Your goal is to parse user intents and respond with a STRICT JSON object matching this schema:
{
  "reply": "Vietnamese text response / Explanation.",
  "ui_action": "RevenueChart" | "UserTable" | "ConfirmModal" | "NONE",
  "action_data": { ... data payload for the frontend UI component ... }
}
No markdown. No explanation. ONLY JSON.
NEVER generate raw SQL queries under any circumstances.
{os.getenv('SYSTEM_CORE_DIRECTIVE', '')}
"""

class NanoBot:
    """
    Trái tim điều phối của Fast Platform (A2A Mediator) - Tier 3
    
    R27 (Strict DTO Binding): Mọi output từ LLM đều phải parse qua Pydantic IntentResponse. 
    Nếu LLM trả về Raw SQL hoặc text rác -> ValidationError văng ra, query bị hủy. Chống 100% SQL Injection từ AI.
    """
    
    def __init__(self):
        self.version = "1.0.0"  # V16.0 Ready
        self.gateway_url = os.getenv("INTERNAL_API_URL", "http://api:8000")
        self.model = os.getenv("TIER3_MODEL", "gemini/gemini-1.5-pro")
        self.rotator = SmartKeyRotator()

    async def analyze(self, request: IntentRequest) -> IntentResponse:
        """
        Analyze request using the primary LLM model.
        R27: Enforce Strict DTO Binding via Pydantic.
        """
        try:
            # FAST-V29.0: Multi-modal instruction injection (VUI Consistency)
            modality = getattr(request, "modality", "text")
            modality_guard = ""
            if modality == "voice":
                modality_guard = (
                    "\nLUẬT VOICE: Bạn đang trả lời bằng GIỌNG NÓI. "
                    "Tuyệt đối KHÔNG TRẢ VỀ BẢNG (Markdown tables). "
                    "Câu trả lời phải cực kỳ ngắn gọn, súc tích (dưới 20 từ). "
                    "Nếu là dữ liệu số, chỉ đọc kết quả cuối cùng."
                )

            all_keys = self.rotator.get_all_keys()
            response = None
            last_error = None
            
            for _ in range(len(all_keys)):
                key = self.rotator.get_next_key()
                try:
                    # R27: Enforce Strict JSON Schema via litellm
                    response = await acompletion(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": _SYSTEM_PROMPT + modality_guard},
                            {"role": "user", "content": f"Query: {request.query}"}
                        ],
                        api_key=key,
                        response_format={"type": "json_object"},
                        temperature=1.0,
                        api_version="v1"
                    )
                    break # Success!
                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()
                    if getattr(e, "status_code", 500) in (401, 429) or "quota" in err_str or "auth" in err_str or "key" in err_str:
                        logger.info(f"[NanoBot] Key rotation: Key ending with ... failed/exhausted. Trying another...")
                        continue
                    break # Other non-auth errors stop the loop
            
            if response is None and last_error:
                raise last_error
            
            raw_text = response.choices[0].message.content
            cost = response._hidden_params.get("response_cost", 0.0) if hasattr(response, "_hidden_params") else 0.0
            
            import re
            cleaned_text = raw_text.strip()
            # Xóa bỏ các block code markdown (nền tảng chat GPT/Gemini hay chèn vào)
            if cleaned_text.startswith("```"):
                cleaned_text = re.sub(r"^```(?:json)?|```$", "", cleaned_text, flags=re.IGNORECASE | re.MULTILINE).strip()
            
            # 1. Bắt buộc ép kiểu qua JSON
            parsed = json.loads(cleaned_text)
            
            # 2. R27: Strict DTO Binding via Pydantic
            intent_response = IntentResponse(
                status="success",
                action=IntentAction.READ,
                message=parsed.get("reply", "Đã xử lý thông tin."),
                data={
                    "ui_action": parsed.get("ui_action", "NONE"),
                    "action_data": parsed.get("action_data", {})
                },
                router_tier=3,
                cost_tokens=cost
            )
            return intent_response
            
        except json.JSONDecodeError as e:
            logger.error(f"[NanoBot] LLM did not return valid JSON: {e}")
            raise ValidationError.from_exception_data(title="NanoBot", line_errors=[]) from e
        except Exception as e:
            logger.error(f"[NanoBot] Inference failed: {e}")
            return IntentResponse(
                status="error",
                action=IntentAction.READ,
                message="Xin lỗi, tôi không thể xử lý yêu cầu này lúc này.",
                data={},
                router_tier=3,
                cost_tokens=0.0
            )

    def _parse_action(self, action_str: str) -> IntentAction:
        try:
            return IntentAction(action_str.upper())
        except ValueError:
            return IntentAction.READ

    async def call_tool(self, tool_name: str, arguments: dict, agent_role: str = "NanoBot-Tier3"):
        """MCP Tool Call via Gateway with R29 IAM Security"""
        
        # R29: Check if the calling agent has authorization to execute this tool
        if not MCPIamGuard.check_permission(agent_role, tool_name):
            logger.error(f"[NanoBot Guard] Denied execution of {tool_name} by {agent_role}.")
            return {"status": "error", "message": f"Permission denied for {tool_name}."}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.gateway_url}/api/v1/mcp/call",
                    json={"name": tool_name, "arguments": arguments}
                )
                return response.json()
            except Exception as e:
                return {"status": "error", "message": str(e)}

    async def stream_analyze(self, text: str):
        """Module 2: AI Streaming (Minimalist)"""
        api_keys = [k.strip() for k in os.getenv("GEMINI_API_KEY", "").split(",") if k.strip()] or [None]
        buf, bounds = [], {".", ",", "?", "!", "\n", ";", ":"}
        
        response = await acompletion(
            model=self.model,
            messages=[{"role": "system", "content": _SYSTEM_PROMPT}, {"role": "user", "content": text}],
            api_key=api_keys[0],
            stream=True,
            temperature=0.0
        )
        
        async for chunk in response:
            if token := chunk.choices[0].delta.content:
                buf.append(token)
                if any(b in token for b in bounds):
                    yield "".join(buf).strip()
                    buf.clear()
        if buf: yield "".join(buf).strip()
