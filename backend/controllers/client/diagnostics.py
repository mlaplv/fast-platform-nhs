from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional
from litestar import Controller, post
from pydantic import BaseModel
from backend.services.ai_engine.diagnostic_agent import DiagnosticAgent, DiagnosticReport
from backend.services.xohi_memory import xohi_memory # type: ignore

logger = logging.getLogger("api-gateway")

class DiagnosticRequest(BaseModel):
    product_name: str
    quiz_data: List[Dict[str, Any]]

class DiagnosticController(Controller):
    """Elite V2.2: AI Diagnostic Controller."""
    path = "/api/v1/client/diagnostics"

    @post("/analyze")
    async def analyze_diagnostics(
        self,
        data: DiagnosticRequest
    ) -> Optional[DiagnosticReport]:
        """Agentic AI: Clinical Analysis for Quiz Data."""
        agent = DiagnosticAgent(redis_client=xohi_memory.client)
        return await agent.analyze(data.product_name, data.quiz_data)
