from __future__ import annotations
import logging
from typing import List, Dict, Optional
from litestar import Controller, post
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.ai_engine.diagnostic_agent import DiagnosticAgent, DiagnosticReport
from backend.services.xohi_memory import xohi_memory # type: ignore

logger = logging.getLogger("api-gateway")

class DiagnosticRequest(BaseModel):
    product_name: str
    quiz_data: List[Dict[str, object]]

class DiagnosticController(Controller):
    """Elite V2.2: AI Diagnostic Controller."""
    path = "/api/v1/client/diagnostics"

    @post("/analyze")
    async def analyze_diagnostics(
        self,
        data: DiagnosticRequest,
        db_session: AsyncSession,
    ) -> DiagnosticReport:
        """Agentic AI: Clinical Analysis for Quiz Data."""
        agent = DiagnosticAgent(redis_client=xohi_memory.client)
        res = await agent.analyze(db_session, data.product_name, data.quiz_data)
        
        if res is None:
            from litestar.exceptions import HTTPException
            raise HTTPException(status_code=503, detail="Hệ thống chẩn đoán AI hiện đang bận. Vui lòng thử lại sau giây lát.")
            
        return res
