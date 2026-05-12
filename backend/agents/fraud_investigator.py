from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic_ai import Agent, RunContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.ads import ClickFraudEvent, IPBlacklist
from backend.services.ads_protection.schemas import ClickFraudResult, FraudSignal

logger = logging.getLogger("fast_platform.agents.fraud")

@dataclass
class ForensicDeps:
    db: AsyncSession
    ip_intel_svc: Any  # IPIntelligenceService
    knowledge_base: Optional[Any] = None

import os
from pydantic_ai.models.test import TestModel
from pydantic_ai.models.openai import OpenAIModel

# Lựa chọn model thông minh (Elite V3.0 Resilience)
def get_model():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-...":
        logger.warning("⚠️ [ForensicAgent] OPENAI_API_KEY missing. Using TestModel (Mock).")
        return TestModel()
    return OpenAIModel('gpt-4o', api_key=api_key)

# Định nghĩa Agent Pháp y (Elite V3.0)
fraud_investigator = Agent(
    get_model(),
    deps_type=ForensicDeps,
    output_type=ClickFraudResult,
    system_prompt=(
        "Bạn là Chuyên gia Pháp y Kỹ thuật của Xohi AI (Phiên bản v3.0 Agentic)."
        "Nhiệm vụ của bạn là phân tích sâu các click nghi vấn từ Google Ads."
        "Hãy sử dụng các công cụ được cung cấp để truy xuất lịch sử IP, kiểm tra danh sách đen "
        "và đối soát với các mẫu tấn công (Attack Patterns) trong cơ sở kiến thức."
        "Nếu phát hiện gian lận, hãy đưa ra bản án 'FRAUD' kèm theo các tín hiệu (signals) chi tiết."
        "Nếu là khách hàng thật đang tìm hiểu sản phẩm (High-intent), hãy ưu tiên bản án 'CLEAN'."
    )
)

@fraud_investigator.tool
async def check_ip_history(ctx: RunContext[ForensicDeps], ip: str) -> List[Dict[str, Any]]:
    """Truy xuất lịch sử click của IP này trong 7 ngày qua."""
    stmt = select(ClickFraudEvent).where(ClickFraudEvent.ip_address == ip).limit(50)
    result = await ctx.deps.db.execute(stmt)
    events = result.scalars().all()
    return [
        {"timestamp": e.created_at.isoformat(), "verdict": e.verdict, "score": e.fraud_score}
        for e in events
    ]

@fraud_investigator.tool
async def check_knowledge_base(ctx: RunContext[ForensicDeps], pattern_query: str) -> str:
    """Tra cứu các mẫu tấn công botnet hoặc hành vi bot đã biết từ Obsidian KB."""
    if not ctx.deps.knowledge_base:
        return "Cơ sở kiến thức hiện không khả dụng."
    # Giả lập RAG fetch
    return f"Mẫu '{pattern_query}': Thường liên quan đến headless browser hoặc click farm từ vùng Đông Nam Á."

@fraud_investigator.tool
async def get_advanced_ip_intel(ctx: RunContext[ForensicDeps], ip: str) -> Dict[str, Any]:
    """Lấy thông tin tình báo chuyên sâu về IP (ASN, ISP, Proxy, VPN)."""
    return await ctx.deps.ip_intel_svc.analyze(ip)

async def run_forensic_analysis(
    db: AsyncSession, 
    ip_svc: Any, 
    click_data: Dict[str, Any]
) -> ClickFraudResult:
    """Hàm wrapper để chạy Agentic Analysis."""
    deps = ForensicDeps(db=db, ip_intel_svc=ip_svc)
    
    # Kích hoạt đặc vụ thẩm vấn
    # Chú ý: Trong thực tế sẽ truyền click_data vào để Agent bắt đầu phân tích
    message = f"Phân tích click này: IP={click_data.get('ip')}, GCLID={click_data.get('gclid')}, Score hiện tại={click_data.get('score')}"
    
    try:
        result = await fraud_investigator.run(message, deps=deps)
        return result.data
    except Exception as e:
        logger.error(f"AGENT_ERROR: {e}")
        # Fallback về kết quả cũ nếu Agent lỗi
        return ClickFraudResult(
            gclid=click_data.get('gclid'),
            ip_address=click_data.get('ip'),
            fraud_score=click_data.get('score', 0.0),
            verdict=click_data.get('verdict', 'SUSPICIOUS'),
            signals=[],
            timestamp=None
        )
