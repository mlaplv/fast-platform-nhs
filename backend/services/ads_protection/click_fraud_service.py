"""
Click Fraud Detection Service — Core Engine
Phân tích hành vi + IP + fingerprint để tính fraud_score
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field

from .ip_intelligence_service import IPIntelligenceService, IPReport

logger = logging.getLogger("ads_protection.click_fraud")


from .schemas import ClickEvent, FraudSignal, ClickFraudResult, IPReport


# ---------------------------------------------------------------------------
# In-memory rate limiter (thay bằng Redis khi scale)
# ---------------------------------------------------------------------------

class _ClickRateLimiter:
    """Đếm số lần click theo IP/GCLID trong sliding window."""

    def __init__(self, window_seconds: int = 3600, max_clicks: int = 5) -> None:
        self._window = window_seconds
        self._max = max_clicks
        self._store: dict[str, list[float]] = defaultdict(list)

    def record_and_check(self, key: str) -> bool:
        """True = vượt giới hạn (fraud signal)."""
        now = time.monotonic()
        cutoff = now - self._window
        clicks = [t for t in self._store[key] if t > cutoff]
        clicks.append(now)
        self._store[key] = clicks
        return len(clicks) > self._max


# ---------------------------------------------------------------------------
# Main Service
# ---------------------------------------------------------------------------

class ClickFraudService:
    """
    Engine phát hiện click fraud cho Google Ads.
    Tích hợp: behavioral analysis + IP intelligence + rate limiting.
    """

    # Ngưỡng quyết định
    THRESHOLD_SUSPICIOUS = 0.35
    THRESHOLD_FRAUD      = 0.65

    def __init__(self) -> None:
        self._ip_svc   = IPIntelligenceService()
        self._ip_limiter   = _ClickRateLimiter(window_seconds=3600, max_clicks=5)
        self._gclid_limiter = _ClickRateLimiter(window_seconds=3600, max_clicks=3)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    async def analyze(self, event: ClickEvent) -> ClickFraudResult:
        """Phân tích một click event và trả về FraudResult (Elite V3.0)."""
        ip_report: IPReport = await self._ip_svc.analyze(event.ip_address)

        signals = self._evaluate_signals(event, ip_report)
        fraud_score = self._compute_score(signals)
        
        # [Elite V3.5] Honeypot Canary Trap instant block
        if event.honeypot_triggered:
            fraud_score = 1.0
            # Ensure the honeypot signal in the list is marked as triggered
            for s in signals:
                if s.name == "honeypot_triggered":
                    s.triggered = True
            logger.warning("🚨 [Canary Trap] Honeypot triggered by IP: %s", event.ip_address)

        # [V3.0] Conversion Insurance (High-Intent Bypass)
        if event.is_high_intent:
            logger.info("💎 [Insurance] High-intent detected for %s. Reducing fraud_score.", event.ip_address)
            fraud_score *= 0.5

        # [V3.0] PoW Challenge Logic
        challenge_id = None
        verdict = self._verdict(fraud_score)

        if 0.3 < fraud_score < 0.7 and not event.pow_solution:
            verdict = "CHALLENGE"
            challenge_id = hashlib.md5(f"{event.ip_address}{event.gclid}".encode()).hexdigest()
            logger.info("🛡️ [PoW] Challenge issued to %s", event.ip_address)
        elif event.pow_solution and event.pow_solution.startswith("pow_result_"):
            logger.info("✅ [PoW] Challenge solved by %s. Reducing score.", event.ip_address)
            fraud_score *= 0.7
            verdict = self._verdict(fraud_score)

        fingerprint = self._make_fingerprint(event)

        return ClickFraudResult(
            gclid=event.gclid,
            ip_address=event.ip_address,
            fraud_score=round(fraud_score, 4),
            verdict=verdict,
            challenge_id=challenge_id,
            signals=signals,
            ip_report=ip_report,
            timestamp=datetime.now(UTC),
            session_fingerprint=fingerprint,
        )

    # -----------------------------------------------------------------------
    # Signal evaluation — mỗi signal có weight riêng
    # -----------------------------------------------------------------------

    def _evaluate_signals(
        self, event: ClickEvent, ip: IPReport
    ) -> list[FraudSignal]:
        s = event  # shorthand

        # --- IP-based ---
        ip_exceed = self._ip_limiter.record_and_check(s.ip_address)
        gclid_exceed = (
            self._gclid_limiter.record_and_check(s.gclid)
            if s.gclid else False
        )

        signals: list[FraudSignal] = [
            FraudSignal(
                name="ip_is_datacenter",
                triggered=ip["is_datacenter"],
                weight=0.40,
                description="IP thuộc datacenter/hosting (AWS, GCP, Azure…)",
            ),
            FraudSignal(
                name="ip_is_vpn",
                triggered=ip["is_vpn"],
                weight=0.25,
                description="IP là VPN exit node",
            ),
            FraudSignal(
                name="ip_is_tor",
                triggered=ip["is_tor"],
                weight=0.30,
                description="IP là Tor exit node",
            ),
            FraudSignal(
                name="ip_is_proxy",
                triggered=ip["is_proxy"],
                weight=0.20,
                description="IP là proxy công khai",
            ),
            FraudSignal(
                name="ip_rate_exceeded",
                triggered=ip_exceed,
                weight=0.35,
                description=f"IP click >5 lần trong 1 giờ",
            ),
            FraudSignal(
                name="gclid_rate_exceeded",
                triggered=gclid_exceed,
                weight=0.40,
                description=f"GCLID click >3 lần trong 1 giờ (same ad click)",
            ),
            # --- Behavioral ---
            FraudSignal(
                name="instant_bounce",
                triggered=s.session_duration_ms < 2500,
                weight=0.20,
                description="Thời gian trên trang <2.5 giây",
            ),
            FraudSignal(
                name="zero_scroll",
                triggered=s.scroll_depth_percent == 0.0 and s.session_duration_ms > 1000,
                weight=0.15,
                description="Không scroll sau >1 giây — bot pattern",
            ),
            FraudSignal(
                name="no_mouse_or_touch",
                triggered=(s.mouse_events_count == 0 and s.touch_events_count == 0),
                weight=0.18,
                description="Không có sự kiện chuột/chạm — headless browser",
            ),
            FraudSignal(
                name="webdriver_detected",
                triggered=s.webdriver_detected,
                weight=0.45,
                description="navigator.webdriver=true — Selenium/Playwright",
            ),
            FraudSignal(
                name="no_plugins",
                triggered=(s.plugins_count is not None and s.plugins_count == 0),
                weight=0.15,
                description="Trình duyệt không có plugin — headless signature",
            ),
            FraudSignal(
                name="abnormal_resolution",
                triggered=(
                    s.screen_width is not None
                    and s.screen_height is not None
                    and (s.screen_width == 0 or s.screen_height == 0
                         or s.screen_width > 7680)  # 8K+
                ),
                weight=0.20,
                description="Độ phân giải màn hình bất thường",
            ),
            FraudSignal(
                name="cookies_disabled",
                triggered=not s.cookie_enabled,
                weight=0.10,
                description="Cookie bị tắt — thường là bot/crawler",
            ),
            FraudSignal(
                name="non_vn_ip",
                triggered=(ip["country"] not in ("VN", "unknown", "")),
                weight=0.25,
                description=f"IP không thuộc Việt Nam (country={ip['country']})",
            ),
            # --- Biometric / Canary Trap Extensions (V3.5) ---
            FraudSignal(
                name="honeypot_triggered",
                triggered=s.honeypot_triggered,
                weight=0.90,
                description="Bẫy Canary / Honeypot bị kích hoạt",
            ),
            FraudSignal(
                name="robotic_mouse_movement",
                triggered=bool(s.mouse_events_count > 0 and (s.mouse_acceleration == 0.0 or s.mouse_acceleration > 10000.0)),
                weight=0.25,
                description="Gia tốc chuột bất thường (bằng 0 hoặc quá nhanh)",
            ),
            FraudSignal(
                name="robotic_click_rhythm",
                triggered=bool((s.mouse_events_count > 1 or s.touch_events_count > 1) and (0 < s.interaction_rhythm < 50.0)),
                weight=0.20,
                description="Nhịp tương tác quá cơ học (phân sai click gần 0)",
            ),
        ]

        return signals

    # -----------------------------------------------------------------------

    @staticmethod
    def _compute_score(signals: list[FraudSignal]) -> float:
        """
        Additive weighted score, cap tại 1.0.
        Chỉ cộng signal khi triggered=True.
        """
        total_weight = sum(s.weight for s in signals)
        earned = sum(s.weight for s in signals if s.triggered)
        if total_weight == 0:
            return 0.0
        return min(earned / total_weight, 1.0)

    def _verdict(self, score: float) -> str:
        if score >= self.THRESHOLD_FRAUD:
            return "FRAUD"
        if score >= self.THRESHOLD_SUSPICIOUS:
            return "SUSPICIOUS"
        return "CLEAN"

    @staticmethod
    def _make_fingerprint(event: ClickEvent) -> str:
        data = f"{event.ip_address}|{event.user_agent}|{event.screen_width}x{event.screen_height}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
