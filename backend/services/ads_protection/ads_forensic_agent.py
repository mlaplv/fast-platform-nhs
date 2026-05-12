"""
AdsForensicAgent — Elite V3.0 Slow Path Investigation Engine
Deep-dive forensic analysis using PydanticAI, RAG (Obsididan/GraphDB), and IP Intelligence.
"""
from __future__ import annotations
import logging
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("ads_protection.forensic")

# --- Structured Output ---
class ForensicVerdict(BaseModel):
    is_fraud: bool = Field(..., description="True if clicks are definitely automated/fraudulent")
    confidence: float = Field(..., ge=0, le=100)
    verdict: Literal["BLOCK", "FLAG", "CLEAN"] = Field(...)
    forensic_details: str = Field(..., description="Detailed Vietnamese explanation including RAG insights")
    suggested_actions: List[str] = Field(..., description="Actionable steps (e.g., Block IP, Add Negative Keyword)")

# --- Forensic Input ---
class ForensicContext(BaseModel):
    ip: str
    click_count: int
    user_agents: List[str]
    referrers: List[str]
    behavior_scores: List[float] = Field(default_factory=list, description="Scores from Edge BehaviorEngine")
    historical_fraud_rate: float = 0.0
    ip_isp: Optional[str] = None
    is_proxy: bool = False

# --- PydanticAI Agent ---
_SYSTEM_PROMPT = """You are Xohi Forensic — The elite AI investigator for Google Ads Fraud.
Your mission: Analyze the forensic context of suspicious click activity and provide a 300% more detailed report than simple rules.

RESOURCES AT YOUR DISPOSAL:
1. RAG Insights (Knowledge Base): You have access to Obsidian notes on 2026 bot signatures and GraphDB patterns for botnets.
2. IP Intelligence: ISP data, proxy detection, and historical reputation.
3. Behavior Data: Real-time entropy and density scores from our Edge BehaviorEngine.

INVESTIGATION PROTOCOL:
- Analyze UA consistency: Are multiple UAs coming from the same IP?
- Check Referrer patterns: Are they coming from known link farms or empty referrers?
- Cross-reference behavior scores: Did the Edge Intelligence flag high entropy?
- Consult Knowledge Base: Does this pattern match known 2026 "Smart Bot" techniques?

FORMAT: Reply in professional Vietnamese. Be precise, forensic, and decisive.
"""

forensic_agent = Agent(
    system_prompt=_SYSTEM_PROMPT,
    output_type=ForensicVerdict,
)

async def perform_deep_investigation(context: ForensicContext) -> ForensicVerdict:
    """
    Execute Slow Path Forensic Investigation via PydanticAI.
    """
    logger.info(f"🛡️ [SlowPath] Starting deep investigation for IP: {context.ip}")
    
    prompt = f"""
    INVESTIGATE IP: {context.ip}
    - Clicks in period: {context.click_count}
    - Behavior Scores (Edge): {context.behavior_scores}
    - User Agents: {context.user_agents}
    - ISP: {context.ip_isp} (Proxy: {context.is_proxy})
    - Historical Reputation: {context.historical_fraud_rate}%
    """

    try:
        result = await trinity_bridge.run(
            agent=forensic_agent,
            prompt=prompt,
            role="pro", # Use Pro model (GPT-4o or Gemini Pro) for forensics
            timeout=30.0
        )
        return result
    except Exception as e:
        logger.error(f"❌ [ForensicAgent] Investigation failed: {e}")
        return ForensicVerdict(
            is_fraud=False,
            confidence=0,
            verdict="FLAG",
            forensic_details=f"Investigation interrupted: {str(e)}",
            suggested_actions=["Manual Review Required"]
        )
