"""
Fraud Analytics Service (v2 — PostgreSQL-backed)
Persist ClickFraudEvent vào DB + cung cấp data cho dashboard
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, case, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.ads import ClickFraudEvent
from backend.services.ads_protection.google_ads_reporter import (
    GoogleAdsReporter,
    InvalidClickRecord,
)

logger = logging.getLogger("ads_protection.analytics")


from .schemas import (
    ClickFraudResult,
    FraudSummary,
    FraudSummaryTotals,
    FraudBudgetInfo,
    OffendingIP,
    OptimizationInsight,
    InvestigationReportResult,
    HourlyFraudStat,
)

class FraudAnalyticsService:
    """
    Analytics service dùng AsyncSession (Postgres).
    Inject session qua Litestar DI tại mỗi request.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._reporter = GoogleAdsReporter()

    # -----------------------------------------------------------------------
    # Persist
    # -----------------------------------------------------------------------

    async def record(self, result: ClickFraudResult) -> ClickFraudEvent:
        """Lưu kết quả phân tích vào Postgres."""
        ip = result.ip_report
        triggered = [s.name for s in result.signals if s.triggered]

        event = ClickFraudEvent(
            gclid=result.gclid,
            ip_address=result.ip_address,
            is_datacenter=ip.is_datacenter,
            is_vpn=ip.is_vpn,
            is_tor=ip.is_tor,
            is_proxy=ip.is_proxy,
            ip_country=ip.country,
            ip_org=ip.org[:128],
            fraud_score=result.fraud_score,
            verdict=result.verdict,
            triggered_signals=json.dumps(triggered),
            session_fingerprint=result.session_fingerprint,
        )
        self._session.add(event)
        await self._session.commit()
        await self._session.refresh(event)
        return event

    # -----------------------------------------------------------------------
    # Dashboard summary
    # -----------------------------------------------------------------------

    async def get_summary(
        self, 
        hours: int = 24, 
        date_from: str | None = None, 
        date_to: str | None = None,
        avg_cpc: float | None = None,
        google_all: int = 0,
        google_invalid: int = 0,
        google_wasted: float = 0.0
    ) -> FraudSummary:
        try:
            if date_from and date_to:
                # Parse YYYY-MM-DD
                start_dt = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=UTC)
                # To end of day
                end_dt = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=UTC)
            else:
                end_dt = datetime.now(UTC)
                start_dt = end_dt - timedelta(hours=hours)

            # 1. Tổng counts theo verdict
            stmt = (
                select(ClickFraudEvent.verdict, func.count().label("cnt"))
                .where(ClickFraudEvent.created_at.between(start_dt, end_dt))
                .group_by(ClickFraudEvent.verdict)
            )
            rows = (await self._session.execute(stmt)).all()

            totals_map: dict[str, int] = {"FRAUD": 0, "SUSPICIOUS": 0, "CLEAN": 0}
            for row in rows:
                verdict, cnt = row
                if verdict in totals_map:
                    totals_map[verdict] = int(cnt)
            
            total_all = sum(totals_map.values())

            # 2. Top IPs
            ip_stmt = (
                select(ClickFraudEvent.ip_address, func.count().label("cnt"))
                .where(
                    ClickFraudEvent.created_at.between(start_dt, end_dt),
                    ClickFraudEvent.verdict == "FRAUD",
                )
                .group_by(ClickFraudEvent.ip_address)
                .order_by(func.count().desc())
                .limit(10)
            )
            top_ips = [
                OffendingIP(ip=str(row[0]), click_count=int(row[1]))
                for row in (await self._session.execute(ip_stmt)).all()
            ]

            # 3. Budget estimate (default 5,000₫ if not provided)
            cpc_to_use = avg_cpc if avg_cpc and avg_cpc > 0 else 5000.0
            wasted = totals_map["FRAUD"] * cpc_to_use

            # 4. Hourly breakdown for charts
            trunc_expr = func.date_trunc("hour", ClickFraudEvent.created_at)
            hourly_stmt = (
                select(
                    trunc_expr.label("hr"),
                    func.count(ClickFraudEvent.id).label("total"),
                    func.coalesce(func.sum(case((ClickFraudEvent.verdict == "FRAUD", 1), else_=0)), 0).label("fraud_cnt")
                )
                .where(ClickFraudEvent.created_at.between(start_dt, end_dt))
                .group_by(trunc_expr)
                .order_by(trunc_expr)
            )
            hourly_rows = (await self._session.execute(hourly_stmt)).all()
            hourly_breakdown = [
                HourlyFraudStat(
                    hour=row[0],
                    total_clicks=int(row[1]),
                    fraud_rate=round(int(row[2]) / max(int(row[1]), 1), 4)
                )
                for row in hourly_rows
            ]

            return FraudSummary(
                period_hours=hours,
                generated_at=datetime.now(UTC),
                totals=FraudSummaryTotals(
                    all_clicks=total_all,
                    fraud=totals_map["FRAUD"],
                    suspicious=totals_map["SUSPICIOUS"],
                    clean=totals_map["CLEAN"],
                    fraud_rate_pct=round(totals_map["FRAUD"] / max(total_all, 1) * 100, 2),
                    suspected_rate_pct=round(
                        (totals_map["FRAUD"] + totals_map["SUSPICIOUS"]) / max(total_all, 1) * 100, 2
                    ),
                    google_all_clicks=google_all,
                    google_invalid_clicks=google_invalid,
                ),
                budget=FraudBudgetInfo(
                    avg_cpc_vnd=cpc_to_use,
                    estimated_wasted_vnd=wasted,
                    estimated_wasted_usd=round(wasted / 25000, 2),
                    google_estimated_wasted_vnd=google_wasted,
                ),
                top_offending_ips=top_ips,
                hourly_breakdown=hourly_breakdown,
                insights=await self.get_optimization_insights(date_from=date_from, date_to=date_to)
            )
        except Exception as e:
            logger.error("FAILED_GET_SUMMARY: %s", e, exc_info=True)
            raise

    # -----------------------------------------------------------------------
    # Weekly investigation package
    # -----------------------------------------------------------------------

    async def build_weekly_investigation_package(
        self, 
        date_from: str | None = None, 
        date_to: str | None = None,
        avg_cpc_vnd: float = 5000.0, 
        force_rebuild: bool = False
    ) -> InvestigationReportResult:
        """
        Gom các event FRAUD theo khoảng thời gian.
        Nếu không có date_from/to, mặc định lấy 7 ngày qua.
        """
        filters = [ClickFraudEvent.verdict == "FRAUD"]
        
        if date_from and date_to:
            try:
                dt_from = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=UTC)
                dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=UTC)
                filters.append(ClickFraudEvent.created_at.between(dt_from, dt_to))
            except ValueError:
                # Fallback to default if invalid date
                cutoff = datetime.now(UTC) - timedelta(days=7)
                filters.append(ClickFraudEvent.created_at >= cutoff)
        else:
            cutoff = datetime.now(UTC) - timedelta(days=7)
            filters.append(ClickFraudEvent.created_at >= cutoff)

        if not force_rebuild:
            filters.append(ClickFraudEvent.reported_to_google.is_(False))

        stmt = select(ClickFraudEvent).where(*filters).order_by(ClickFraudEvent.created_at.desc()).limit(2000)
        events = list((await self._session.execute(stmt)).scalars().all())

        if not events:
            return InvestigationReportResult(status="no_fraud_events_this_week")

        records = []
        for e in events:
            try:
                sig_list = json.loads(e.triggered_signals or "[]")
            except (json.JSONDecodeError, TypeError):
                sig_list = []
                
            records.append(InvalidClickRecord(
                gclid=e.gclid,
                ip_address=e.ip_address,
                user_agent=e.user_agent or "unknown",
                timestamp=e.created_at.isoformat(),
                fraud_score=e.fraud_score,
                signals=sig_list,
                campaign_id=e.campaign_id,
                keyword=e.keyword,
            ))

        # Fallback strings for report if not provided
        if not date_from or not date_to:
            date_from = cutoff.strftime("%Y-%m-%d")
            date_to = datetime.now(UTC).strftime("%Y-%m-%d")

        campaign_name = events[0].campaign_id or "Campaign Management"
        landing_url = events[0].landing_url or "https://osmo.vn"

        report = await self._reporter.generate_investigation_report(
            records=records,
            date_from=date_from,
            date_to=date_to,
            avg_cpc_vnd=avg_cpc_vnd,
            campaign_name=campaign_name,
            landing_url=landing_url,
        )

        # Mark as reported
        for e in events:
            e.reported_to_google = True
            e.investigation_batch_id = f"batch_{date_from}_{date_to}"
        await self._session.commit()

        return InvestigationReportResult(
            status="ready",
            date_from=date_from,
            date_to=date_to,
            total_fraud_clicks=report.total_suspected_clicks,
            estimated_wasted_vnd=report.estimated_wasted_budget_vnd,
            csv_path=report.csv_path,
            support_message_preview=report.support_message[:600] + "...",
        )

    # -----------------------------------------------------------------------
    # Optimization insights (DB-backed)
    # -----------------------------------------------------------------------

    async def get_optimization_insights(
        self, date_from: str | None = None, date_to: str | None = None
    ) -> list[OptimizationInsight]:
        """
        Phân tích patterns theo khoảng thời gian.
        Nếu không có dates, mặc định 48h.
        """
        if date_from and date_to:
            try:
                dt_from = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=UTC)
                dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=UTC)
            except ValueError:
                dt_from = datetime.now(UTC) - timedelta(hours=48)
                dt_to = datetime.now(UTC)
        else:
            dt_from = datetime.now(UTC) - timedelta(hours=48)
            dt_to = datetime.now(UTC)

        stmt = select(ClickFraudEvent).where(ClickFraudEvent.created_at.between(dt_from, dt_to)).limit(500)
        events = list((await self._session.execute(stmt)).scalars().all())

        insights: list[OptimizationInsight] = []
        if not events:
            return []

        total = len(events)

        # 1. Instant bounce -> Quality Score & SGE Threat
        bounces = [e for e in events if e.session_duration_ms < 2500]
        bounce_rate = len(bounces) / max(total, 1)
        if bounce_rate > 0.30:
            insights.append(OptimizationInsight(
                type="landing_page", priority="HIGH",
                title=f"NGUY CƠ RỚT ĐIỂM CHẤT LƯỢNG ({bounce_rate:.0%})",
                detail="Tỷ lệ thoát trang tức thì cao. Google Ads sẽ đánh tụt Quality Score và SGE ranking.",
                action="Yêu cầu Xohi AI trinh sát trang đích ngay để tối ưu H1/LCP và đồng bộ SGE.",
                estimated_saving_pct=15.0,
            ))
        
        # 2. Datacenter / Bot traffic
        dc = [e for e in events if e.is_datacenter]
        if len(dc) / max(total, 1) > 0.05:
            insights.append(OptimizationInsight(
                type="ip_exclusion", priority="MEDIUM",
                title="PHÁT HIỆN LƯU LƯỢNG BOT GIẢ MẠO",
                detail=f"{len(dc)} clicks từ các Datacenter IPs không xác định (Bot/Scraper).",
                action="Kích hoạt chặn dải IP Datacenter để bảo vệ ngân sách Google Ads.",
                estimated_saving_pct=8.0,
            ))

        # 3. Non-VN traffic
        non_vn = [e for e in events if e.ip_country not in ("VN", "", None)]
        if len(non_vn) / max(total, 1) > 0.10:
            insights.append(OptimizationInsight(
                type="geo_targeting", priority="HIGH",
                title="SAI LỆCH MỤC TIÊU ĐỊA LÝ",
                detail=f"{len(non_vn)}/{total} clicks đến từ ngoài lãnh thổ Việt Nam.",
                action="Điều chỉnh lại 'Location options' trong Google Ads: chọn 'Presence: People IN your locations'.",
                estimated_saving_pct=10.0,
            ))

        return insights
