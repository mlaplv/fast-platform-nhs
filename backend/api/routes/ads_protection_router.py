"""
Ads Protection Router — Litestar endpoints
Expose API cho client-side script + admin dashboard
"""
from __future__ import annotations

import logging
from typing import Annotated, Any

from litestar import Controller, Router, get, post
from litestar.di import Provide
from litestar.params import Body

from backend.services.ads_protection.click_fraud_service import (
    ClickEvent,
    ClickFraudResult,
    ClickFraudService,
)
from backend.services.ads_protection.fraud_analytics_service import FraudAnalyticsService
from backend.services.ads_protection.google_ads_reporter import GoogleAdsReporter

logger = logging.getLogger("api.ads_protection")

# ---------------------------------------------------------------------------
# Singletons
# ---------------------------------------------------------------------------
_fraud_svc    = ClickFraudService()
_reporter     = GoogleAdsReporter()
# FraudAnalyticsService requires a session, so we instantiate it per-request in the methods


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class AdsProtectionController(Controller):
    path = "/ads-protection"

    # ------------------------------------------------------------------
    # 1. Click validation — được gọi từ landing page JS / GTM
    # ------------------------------------------------------------------

    @post("/validate-click", status_code=200)
    async def validate_click(
        self,
        data: Annotated[ClickEvent, Body(media_type="application/json")],
    ) -> ClickFraudResult:
        """
        Endpoint chính: nhận fingerprint từ client, trả về fraud verdict.
        Client dùng verdict để quyết định có fire conversion pixel không.
        """
        result = await _fraud_svc.analyze(data)
        _analytics.record(result)

        if result.verdict == "FRAUD":
            logger.warning(
                "FRAUD_DETECTED ip=%s gclid=%s score=%.2f",
                result.ip_address, result.gclid, result.fraud_score,
            )

        return result

    # ------------------------------------------------------------------
    # 2. Dashboard summary — cho Admin panel
    # ------------------------------------------------------------------

    @get("/summary")
    async def get_summary(self, hours: int = 24) -> dict[str, Any]:
        """
        Thống kê tổng hợp fraud trong `hours` giờ gần nhất.
        Trả về data cho biểu đồ real-time dashboard.
        """
        # NOTE: This router is legacy. Real implementation is in backend/controllers/ads_protection.py
        # Here we mock the behavior to prevent crash
        return {"status": "legacy_route_use_new_controller"}

    # ------------------------------------------------------------------
    # 3. Optimization insights
    # ------------------------------------------------------------------

    @get("/insights")
    async def get_insights(self) -> list[dict[str, Any]]:
        """
        Phân tích patterns và trả về danh sách đề xuất tối ưu campaign.
        """
        return [] # Legacy placeholder

    # ------------------------------------------------------------------
    # 4. Tạo Investigation Report gửi Google
    # ------------------------------------------------------------------

    @post("/generate-investigation-report")
    async def generate_investigation_report(
        self, avg_cpc_vnd: float = 5000.0
    ) -> dict[str, Any]:
        """
        Tổng hợp fraud events trong 7 ngày → tạo CSV + email template.
        Admin download CSV và gửi email cho Google Ads Support.
        """
        return await _analytics.build_weekly_investigation_package(
            avg_cpc_vnd=avg_cpc_vnd
        )

    # ------------------------------------------------------------------
    # 5. Fetch invalid click metrics từ Google Ads API
    # ------------------------------------------------------------------

    @get("/google-metrics")
    async def get_google_invalid_metrics(
        self, date_from: str, date_to: str
    ) -> list[dict[str, Any]]:
        """
        Lấy dữ liệu invalid clicks trực tiếp từ Google Ads Reporting API.
        Cần env vars: GOOGLE_ADS_* được cấu hình.
        """
        return await _reporter.fetch_invalid_click_metrics(
            date_from=date_from, date_to=date_to
        )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

ads_protection_router = Router(
    path="/api/v1",
    route_handlers=[AdsProtectionController],
    tags=["ads-protection"],
)
