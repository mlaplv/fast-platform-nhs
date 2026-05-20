"""
ViralFraudAgent — PydanticAI Behavioral Share Verification (Viral 2026)

Analyzes client-side behavioral telemetry to determine if a user
genuinely shared content or attempted to game the share-to-unlock flow.

Architecture:
  - PydanticAI Agent with Structured Output (ShareVerdict)
  - Runs via TrinityBridge (key rotation, model fallback)
  - Dual-layer: Heuristic pre-filter + AI deep analysis
  - Role: "fast" (Gemini Flash) for sub-2s latency
"""
from __future__ import annotations

import logging
from typing import Literal, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("api-gateway.viral")


# ── Structured Output ─────────────────────────────────────────────────────────

class ShareVerdict(BaseModel):
    """AI-generated verdict on share authenticity."""
    trust_score: float = Field(
        ..., ge=0.0, le=100.0,
        description="0.0 = definite fraud, 100.0 = definitely legitimate"
    )
    verdict: Literal["APPROVE", "DENY", "SUSPICIOUS"] = Field(
        ..., description="Final decision"
    )
    reasoning: str = Field(
        ..., description="Brief explanation of the verdict (Vietnamese)"
    )
    block_ip: bool = Field(False, description="Flag to block the user IP immediately")


# ── Telemetry Schema ──────────────────────────────────────────────────────────

class ShareTelemetry(BaseModel):
    """Behavioral signals collected from the client during share flow."""
    time_on_page_ms: int = Field(0, description="Time spent on page before share")
    share_duration_ms: int = Field(0, description="Time from click share to verify")
    visibility_changes: int = Field(0, description="Number of tab hide/show events")
    scroll_depth_pct: float = Field(0.0, description="Scroll depth percentage 0-100")
    interaction_count: int = Field(0, description="Click/touch count before share")
    share_method: str = Field("unknown", description="native|popup|clipboard")
    popup_was_blocked: bool = Field(False, description="Was the popup blocked?")
    mouse_acceleration: float = Field(0.0, description="Mouse acceleration px/s^2")
    interaction_rhythm: float = Field(0.0, description="Interaction rhythm (variance)")
    honeypot_triggered: bool = Field(False, description="Did bot click honeypot?")
    client_ip: Optional[str] = Field(None, description="Client IP for blocking")


# ── Heuristic Pre-filter ──────────────────────────────────────────────────────

def heuristic_score(t: ShareTelemetry) -> tuple[float, str, bool]:
    """
    Fast deterministic pre-filter. Returns (score, reason, block_ip).
    Score >= 60 means likely legitimate (skip AI for speed).
    Score < 30 means definite fraud (skip AI to save cost).
    Score 30-59 means ambiguous → escalate to AI.
    """
    # Sinh trắc học hành vi & Honeypot (Tuyệt đối ưu tiên)
    if t.honeypot_triggered:
        return 0.0, "Canary Trap Triggered (Honeypot) - Definite Bot", True

    score = 50.0  # Start neutral
    reasons: list[str] = []
    block_ip = False

    # Sinh trắc học hành vi
    if t.mouse_acceleration > 10000:
        score -= 40.0
        reasons.append("Gia tốc chuột bất thường (>10,000 px/s²)")
    elif t.mouse_acceleration == 0 and t.interaction_count > 0:
        score -= 20.0
        reasons.append("Tương tác không có di chuyển chuột (Bot/Script)")
    
    if t.interaction_rhythm > 0 and t.interaction_rhythm < 10:
        score -= 30.0
        reasons.append("Nhịp điệu quá đều đặn (Rhythm variance < 10ms)")

    # Signal 1: Share duration (Elite V2.2: Hardened thresholds)
    if t.share_duration_ms < 2000:
        score -= 40.0
        reasons.append("Share cực nhanh (<2s) - Dấu hiệu gian lận")
    elif t.share_duration_ms < 4000:
        score -= 10.0
        reasons.append("Thời gian share ngắn (<4s)")
    elif t.share_duration_ms >= 5000:
        score += 20.0
        reasons.append("Thời gian share thực tế (>5s)")

    # Signal 2: Visibility changes (tab switch = likely opened share dialog)
    if t.visibility_changes >= 1:
        score += 10.0 # Reduced weight, easy to trigger
        reasons.append("Tab đã chuyển")
    else:
        score -= 30.0
        reasons.append("Tab không hề chuyển (gian lận lộ liễu)")

    # Signal 3: Web Share API (native share is strongest signal)
    if t.share_method == "native":
        score += 15.0
        reasons.append("Web Share API")
    elif t.share_method == "popup":
        if t.share_duration_ms < 3000:
            score -= 30.0
            reasons.append("Đóng popup quá nhanh (<3s)")
        elif t.share_duration_ms >= 5000:
            score += 15.0

    # Signal 4: Time on page (bots visit < 5s)
    if t.time_on_page_ms < 2000:
        score -= 10.0
        reasons.append("Thời gian trên trang quá ngắn")
    elif t.time_on_page_ms > 10000:
        score += 10.0

    # Signal 5: Scroll depth (engaged users scroll)
    if t.scroll_depth_pct > 20:
        score += 5.0

    # Signal 6: Interaction count (real users interact)
    if t.interaction_count >= 2:
        score += 5.0

    # Signal 7: Popup was blocked (user may not have shared)
    if t.popup_was_blocked:
        score -= 10.0
        reasons.append("Popup bị chặn")

    # Clamp
    score = max(0.0, min(100.0, score))
    return score, " | ".join(reasons) if reasons else "Normal", block_ip


# ── PydanticAI Agent ──────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are an Elite Vietnamese E-commerce Fraud Analyst (AI Specialist).
Your job: Rigorously analyze behavioral telemetry to detect "Share-to-Unlock" fraud.

SIGNALS & THRESHOLDS:
- share_duration_ms: Real shares take 12-25s (login + post). Anything < 8s is HIGHLY suspicious.
- visibility_changes: Expect at least 1 (opening popup / switching tabs). 0 is a RED FLAG.
- share_method: "native" is strong. "popup" requires > 10s. "clipboard" is very weak.
- scroll_depth_pct: Real users may NOT scroll if the share button is at the top of the page (0% is completely normal and acceptable). Do NOT deny based on 0% scroll depth.
- time_on_page_ms: Returning or fast-acting users might click the share button instantly (<3s). If their share_duration_ms is genuine (>10s), this is a REAL user, not a bot!
- interaction_count: Real users have at least 1-2 interactions before sharing.
- mouse_acceleration: Very high (>8000) means bot telemetry. 0 with interactions means script clicking. Normal is 50-3000.
- interaction_rhythm: Variance of time between clicks. <20ms is impossibly consistent (macro/script).

VERDICT CRITERIA:
- 90-100: Flawless behavior.
- 70-89: Likely legitimate (long share duration, even if page visit was short or didn't scroll).
- 40-69: Suspicious (rushed, low interaction, or blocked popups).
- 0-39: Definite fraud (bot-like speed, extreme rushing, rigid rhythm).

Reply with JSON: {"trust_score": float, "verdict": "APPROVE"|"DENY"|"SUSPICIOUS", "reasoning": "strict Vietnamese explanation", "block_ip": bool}
(Set block_ip to True ONLY if score is < 15 and telemetry strongly indicates an automated bot attacking the system)
"""

share_fraud_agent = Agent(
    system_prompt=_SYSTEM_PROMPT,
    output_type=ShareVerdict,
)


# ── Public API ────────────────────────────────────────────────────────────────

async def analyze_share_behavior(telemetry: ShareTelemetry) -> ShareVerdict:
    """
    Dual-layer share verification:
      1. Heuristic pre-filter (0ms, deterministic)
      2. PydanticAI deep analysis (only for ambiguous cases)

    Returns ShareVerdict with trust_score, verdict, and reasoning.
    """
    # Layer 1: Heuristic fast-path
    h_score, h_reason, h_block = heuristic_score(telemetry)

    if h_score >= 80.0:
        # Strong legitimate signals (e.g. >12s share duration + tab/window switch) → skip AI
        logger.info(f"[ViralFraud] Heuristic APPROVE (score={h_score:.0f}): {h_reason}")
        return ShareVerdict(
            trust_score=h_score,
            verdict="APPROVE",
            reasoning=f"Heuristic: {h_reason}",
            block_ip=h_block
        )

    if h_score < 10.0:
        # Definite fraud → skip AI
        logger.warning(f"[ViralFraud] Heuristic DENY (score={h_score:.0f}): {h_reason}")
        return ShareVerdict(
            trust_score=h_score,
            verdict="DENY",
            reasoning=f"Heuristic: {h_reason}",
            block_ip=h_block
        )

    # Layer 2: Ambiguous → PydanticAI deep analysis
    logger.info(f"[ViralFraud] Escalating to AI (heuristic={h_score:.0f}): {h_reason}")

    prompt = (
        f"Analyze this share behavior:\n"
        f"- share_duration_ms: {telemetry.share_duration_ms}\n"
        f"- visibility_changes: {telemetry.visibility_changes}\n"
        f"- share_method: {telemetry.share_method}\n"
        f"- time_on_page_ms: {telemetry.time_on_page_ms}\n"
        f"- scroll_depth_pct: {telemetry.scroll_depth_pct:.1f}\n"
        f"- interaction_count: {telemetry.interaction_count}\n"
        f"- mouse_acceleration: {telemetry.mouse_acceleration:.2f}\n"
        f"- interaction_rhythm: {telemetry.interaction_rhythm:.2f}\n"
        f"- popup_was_blocked: {telemetry.popup_was_blocked}\n"
        f"\nHeuristic pre-score: {h_score:.0f} ({h_reason})"
    )

    try:
        result = await trinity_bridge.run(
            agent=share_fraud_agent,
            prompt=prompt,
            role="fast",
            timeout=10.0,
        )

        if isinstance(result, ShareVerdict):
            logger.info(
                f"[ViralFraud] AI verdict: {result.verdict} "
                f"(score={result.trust_score:.0f}): {result.reasoning}"
            )
            return result

        # Fallback: parse if trinity_bridge returned raw data
        if hasattr(result, "trust_score"):
            return ShareVerdict(
                trust_score=float(getattr(result, "trust_score", h_score)),
                verdict=str(getattr(result, "verdict", "SUSPICIOUS")),
                reasoning=str(getattr(result, "reasoning", h_reason)),
                block_ip=bool(getattr(result, "block_ip", h_block))
            )

    except Exception as e:
        logger.error(f"[ViralFraud] AI analysis failed: {e}")

    # Graceful degradation: use heuristic result
    verdict = "APPROVE" if h_score >= 50 else "SUSPICIOUS" if h_score >= 30 else "DENY"
    return ShareVerdict(
        trust_score=h_score,
        verdict=verdict,
        reasoning=f"Fallback heuristic: {h_reason}",
        block_ip=h_block
    )
