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


# ── Heuristic Pre-filter ──────────────────────────────────────────────────────

def heuristic_score(t: ShareTelemetry) -> tuple[float, str]:
    """
    Fast deterministic pre-filter. Returns (score, reason).
    Score >= 60 means likely legitimate (skip AI for speed).
    Score < 30 means definite fraud (skip AI to save cost).
    Score 30-59 means ambiguous → escalate to AI.
    """
    score = 50.0  # Start neutral
    reasons: list[str] = []

    # Signal 1: Share duration (minimum 2s for genuine share)
    if t.share_duration_ms < 1000:
        score -= 20.0
        reasons.append("Share quá nhanh (<1s)")
    elif t.share_duration_ms >= 2000:
        score += 15.0

    # Signal 2: Visibility changes (tab switch = likely opened share dialog)
    if t.visibility_changes >= 1:
        score += 20.0
        reasons.append("Tab đã chuyển (share dialog mở)")
    else:
        score -= 10.0
        reasons.append("Tab không chuyển")

    # Signal 3: Web Share API (native share is strongest signal)
    if t.share_method == "native":
        score += 25.0
        reasons.append("Web Share API (native)")
    elif t.share_method == "popup":
        if t.share_duration_ms < 5000:
            score -= 20.0
            reasons.append("Đóng popup quá nhanh, chưa kịp đăng nhập/share")
        else:
            score += 10.0

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
    return score, " | ".join(reasons) if reasons else "Normal"


# ── PydanticAI Agent ──────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a Vietnamese E-commerce Fraud Analyst specialized in Share-to-Unlock promotions.

Your job: Analyze behavioral telemetry from a user who clicked "Share" on a product page.
Determine if they GENUINELY shared the content to social media, or if they're trying to game the system.

SIGNALS TO ANALYZE:
- share_duration_ms: How long between clicking Share and verification. Real shares take 3-10s+.
- visibility_changes: Number of tab switches. At least 1 is expected (share dialog opens).
- share_method: "native" (Web Share API) is strongest proof. "popup" is good. "clipboard" is weakest.
- time_on_page_ms: Time on page before sharing. Bots are fast (<3s). Real users browse (>10s).
- scroll_depth_pct: How far they scrolled. Engaged users scroll past 20%.
- interaction_count: Clicks/taps before sharing. Real users interact.
- popup_was_blocked: If true, user likely did NOT share.

SCORING GUIDE:
- 80-100: Clearly legitimate (multiple strong signals)
- 60-79: Likely legitimate (benefit of the doubt)
- 30-59: Suspicious (some red flags)
- 0-29: Likely fraud (multiple red flags)

Reply with a JSON object: {"trust_score": float, "verdict": "APPROVE"|"DENY"|"SUSPICIOUS", "reasoning": "brief Vietnamese explanation"}
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
    h_score, h_reason = heuristic_score(telemetry)

    if h_score >= 70.0:
        # Strong legitimate signals → skip AI (save cost + latency)
        logger.info(f"[ViralFraud] Heuristic APPROVE (score={h_score:.0f}): {h_reason}")
        return ShareVerdict(
            trust_score=h_score,
            verdict="APPROVE",
            reasoning=f"Heuristic: {h_reason}"
        )

    if h_score < 10.0:
        # Definite fraud → skip AI
        logger.warning(f"[ViralFraud] Heuristic DENY (score={h_score:.0f}): {h_reason}")
        return ShareVerdict(
            trust_score=h_score,
            verdict="DENY",
            reasoning=f"Heuristic: {h_reason}"
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
            )

    except Exception as e:
        logger.error(f"[ViralFraud] AI analysis failed: {e}")

    # Graceful degradation: use heuristic result
    verdict = "APPROVE" if h_score >= 50 else "SUSPICIOUS" if h_score >= 30 else "DENY"
    return ShareVerdict(
        trust_score=h_score,
        verdict=verdict,
        reasoning=f"Fallback heuristic: {h_reason}"
    )
