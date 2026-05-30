from __future__ import annotations
import logging
import time
from typing import List, Dict, Optional
from litestar import Controller, post, Request
from litestar.exceptions import HTTPException, TooManyRequestsException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.ai_engine.diagnostic_agent import DiagnosticAgent, DiagnosticReport
from backend.services.xohi_memory import xohi_memory # type: ignore
from backend.services.commerce.security.input_guard import input_guard

logger = logging.getLogger("api-gateway")

class DiagnosticRequest(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=150)
    quiz_data: List[Dict[str, object]] = Field(..., min_length=1, max_length=30)

class DiagnosticController(Controller):
    """Elite V2.2: AI Diagnostic Controller."""
    path = "/api/v1/client/diagnostics"

    @post("/analyze")
    async def analyze_diagnostics(
        self,
        request: Request,
        data: DiagnosticRequest,
        db_session: AsyncSession,
    ) -> DiagnosticReport:
        """Agentic AI: Clinical Analysis for Quiz Data."""
        # A. Kiểm tra Military-Grade Blacklist trước tiên
        await input_guard.check_military_blacklist(request)

        ip = (
            request.headers.get("x-real-ip")
            or (request.client.host if request.client else None)
            or "unknown"
        )

        # 1. Giới hạn, cấm dùng công cụ hay tool (cấm bot / API clients)
        user_agent = request.headers.get("user-agent", "").strip().lower()
        if not user_agent:
            await input_guard.record_security_infraction(ip)
            raise HTTPException(status_code=403, detail="Yêu cầu bị từ chối do thiếu định dạng User-Agent hợp lệ.")
        
        bot_keywords = [
            "headless", "selenium", "puppeteer", "playwright", "python-requests", 
            "curl", "wget", "httpclient", "postman", "scrapy", "urllib", 
            "axios", "got", "node-fetch", "pycurl", "perl", "java", "go-http"
        ]
        if any(bot in user_agent for bot in bot_keywords):
            await input_guard.record_security_infraction(ip)
            raise HTTPException(status_code=403, detail="Truy cập tự động thông qua công cụ API bị nghiêm cấm.")

        # Rate limiting: Tấn công tài nguyên token (diagnostics)
        try:
            redis = xohi_memory.client
            if redis:
                now_minute = int(time.time() // 60)
                diag_key = f"support:diagnostics:ip:{ip}:{now_minute}"
                count = await redis.incr(diag_key)
                if count == 1:
                    await redis.expire(diag_key, 90)
                
                # Giới hạn tối đa 3 lần chẩn đoán mỗi phút để tránh cạn kiệt tài nguyên
                if count > 3:
                    await input_guard.record_security_infraction(ip)
                    raise TooManyRequestsException(detail="Bạn đã yêu cầu chẩn đoán quá nhiều lần trong thời gian ngắn. Vui lòng đợi 1 phút.")
        except TooManyRequestsException:
            raise
        except Exception as exc:
            logger.warning("[DiagnosticsController] Rate limit check failed (skipping): %s", exc)

        # 2 & 3. Chống tấn công tài nguyên (Token) & Prompt Injection
        # A. Kiểm tra tên sản phẩm
        is_safe_p, _ = input_guard.validate(data.product_name)
        if not is_safe_p:
            logger.warning("[DiagnosticsController] Prompt injection detected in product name: %s", data.product_name)
            await input_guard.record_security_infraction(ip)
            raise HTTPException(status_code=400, detail="Phát hiện hành vi không hợp lệ trong tên sản phẩm.")

        # B. Kiểm tra dữ liệu khảo sát quiz_data
        for q in data.quiz_data:
            for k, v in q.items():
                str_k = str(k)
                str_v = str(v)
                
                # Giới hạn độ dài chuỗi để chống cạn kiệt tài nguyên (tối đa 100 ký tự key, 500 ký tự value)
                if len(str_k) > 100 or len(str_v) > 500:
                    await input_guard.record_security_infraction(ip)
                    raise HTTPException(status_code=400, detail="Nội dung câu hỏi khảo sát vượt quá độ dài tối đa cho phép.")
                
                # Chống prompt injection
                is_safe_k, _ = input_guard.validate(str_k)
                is_safe_v, _ = input_guard.validate(str_v)
                if not is_safe_k or not is_safe_v:
                    logger.warning("[DiagnosticsController] Prompt injection detected in quiz data: k=%s, v=%s", str_k, str_v)
                    await input_guard.record_security_infraction(ip)
                    raise HTTPException(status_code=400, detail="Phát hiện hành vi không hợp lệ trong nội dung khảo sát.")

        agent = DiagnosticAgent(redis_client=xohi_memory.client)
        res = await agent.analyze(db_session, data.product_name, data.quiz_data)
        
        if res is None:
            raise HTTPException(status_code=503, detail="Hệ thống chẩn đoán AI hiện đang bận. Vui lòng thử lại sau giây lát.")
            
        return res
