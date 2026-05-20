"""
Ads Protection Controller — Litestar (production pattern)
Dùng db_session: AsyncSession inject theo chuẩn project (banner.py pattern)
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, UTC
from typing import AsyncGenerator, Optional, Annotated

from litestar import Controller, get, post, patch, delete, Request
from litestar.response import ServerSentEvent
from litestar.params import Parameter
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.ads_protection.schemas import (
    ClickEvent,
    ClickFraudResult,
    FraudSummary,
    OptimizationInsight,
    InvestigationReportRequest,
    InvestigationReportResult,
    GoogleInvalidClickMetric,
    # Campaign Manager
    CampaignCreateRequest,
    CampaignStatusUpdate,
    CampaignBudgetUpdate,
    CampaignInfo,
    CampaignOperationResult,
    AdGroupCreateRequest,
    AdGroupInfo,
    AdInfo,
    ResponsiveSearchAdCreate,
    KeywordSuggestion,
    PolicyCheckResult,
)
from backend.services.ads_protection.click_fraud_service import ClickFraudService
from backend.services.ads_protection.fraud_analytics_service import FraudAnalyticsService
from backend.services.ads_protection.google_ads_reporter import GoogleAdsReporter
from backend.services.ads_protection.campaign_manager import CampaignManager
from backend.services.ads_protection.ai_strategist import ai_strategist
from backend.services.ads_protection.schemas import AISuggestionRequest, AISuggestionResponse, CampaignOperationResult
from backend.database.models.ads import IPBlacklist, NegativeKeyword
from sqlalchemy import select, delete as sa_delete

from backend.services.xohi_memory import xohi_memory
from backend.core.stream_handler import RedisStreamProducer

logger = logging.getLogger("api-gateway")

# Stateless singletons (chỉ khởi tạo một lần, không giữ state DB)
_fraud_svc      = ClickFraudService()
_reporter       = GoogleAdsReporter()
_campaign_mgr   = CampaignManager()

# HUB cho Real-time Analytics (SSE)
_stream_producer = RedisStreamProducer(xohi_memory.client)

class LiveStreamHub:
    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []
        self._redis = xohi_memory.client
        self._channel = "ads:events"
        self._listen_task: Optional[asyncio.Task] = None

    async def start_listener(self):
        """Lắng nghe sự kiện từ Redis để phát qua SSE (hỗ trợ đa tiến trình)."""
        if self._listen_task: return
        self._listen_task = asyncio.create_task(self._redis_listener())
        logger.info("📡 [LiveStreamHub] Redis Listener Started.")

    async def _redis_listener(self):
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(self._channel)
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    # Phát cho các subscribers tại tiến trình này
                    for q in self._subscribers:
                        await q.put(data)
        except Exception as e:
            logger.error(f"[LiveStreamHub] Listener Error: {e}")
        finally:
            await pubsub.unsubscribe(self._channel)

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self._subscribers.append(q)
        logger.info("📡 ADS_DASHBOARD_CONNECTED (Total: %d)", len(self._subscribers))
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._subscribers:
            self._subscribers.remove(q)
            logger.info("🔌 ADS_DASHBOARD_DISCONNECTED (Total: %d)", len(self._subscribers))

    async def broadcast(self, data: dict):
        """Phát tán sự kiện qua Redis (Global Broadcast)."""
        await self._redis.publish(self._channel, json.dumps(data))

_hub = LiveStreamHub()


class AdsProtectionController(Controller):
    path = "/api/v1/ads-protection"
    tags = ["Ads Protection"]

    # ------------------------------------------------------------------
    # 1. Validate click (public — gọi từ GTM landing page)
    # ------------------------------------------------------------------
    @post("/validate-click", status_code=200)
    async def validate_click(
        self,
        db_session: AsyncSession,
        request: Request,
        data: ClickEvent,
    ) -> ClickFraudResult:
        """
        Nhận fingerprint từ client-side script, phân tích fraud, persist vào DB.
        Trả về verdict để client quyết định có fire conversion pixel không.
        """
        # Extract client IP
        ip = request.headers.get("x-real-ip") or request.headers.get("x-forwarded-for") or request.connection.ip
        if "," in ip:
            ip = ip.split(",")[0].strip()
        data.ip_address = ip

        result = await _fraud_svc.analyze(data)

        analytics = FraudAnalyticsService(db_session)
        await analytics.record(result, data)

        # [V3.0 Fast Path] Push to stream for Agentic Analysis (Slow Path)
        await _stream_producer.produce(
            data={
                "gclid": result.gclid,
                "ip": result.ip_address,
                "score": result.fraud_score,
                "verdict": result.verdict,
                "fingerprint": result.session_fingerprint
            }
        )

        if result.verdict == "FRAUD":
            logger.warning(
                "FRAUD_DETECTED ip=%s gclid=%s score=%.2f signals=%s",
                result.ip_address,
                result.gclid,
                result.fraud_score,
                [s.name for s in result.signals if s.triggered],
            )
            # [Elite V3.5] Auto-block IP in local DB and Google Ads
            try:
                # Check if already blacklisted
                stmt = select(IPBlacklist).where(IPBlacklist.ip_address == result.ip_address)
                existing = (await db_session.execute(stmt)).scalar_one_or_none()
                if not existing:
                    new_bl = IPBlacklist(
                        ip_address=result.ip_address,
                        reason=f"Auto-blocked: Click Fraud detected (score={result.fraud_score}, gclid={result.gclid or 'N/A'})",
                        fraud_score=result.fraud_score
                    )
                    db_session.add(new_bl)
                    await db_session.commit()
                    logger.info("🛡️ [Auto-Block] IP %s blacklisted locally", result.ip_address)
                    
                    # Async block in Google Ads if customer_id is configured
                    if _campaign_mgr._has_credentials():
                        # run in background task to avoid blocking response latency
                        asyncio.create_task(_campaign_mgr.block_ip(campaign_resource_name="", ip_address=result.ip_address, is_global=True))
            except Exception as ex:
                logger.error("Auto-block IP failed for %s: %s", result.ip_address, ex)

        # Đẩy dữ liệu thời gian thực cho Dashboard qua SSE
        await _hub.broadcast({
            "type": "NEW_CLICK",
            "verdict": result.verdict,
            "ip": result.ip_address,
            "score": result.fraud_score,
            "timestamp": result.timestamp.isoformat()
        })

        return result

    # ------------------------------------------------------------------
    # 2. Real-time Stream (SSE)
    # ------------------------------------------------------------------
    @get("/stream")
    async def stream_analytics(self) -> ServerSentEvent:
        """Kênh truyền dữ liệu thời gian thực cho Admin Dashboard."""
        await _hub.start_listener()
        q = _hub.subscribe()

        async def _gen() -> AsyncGenerator[str, None]:
            try:
                # Gửi heartbeat định kỳ để giữ kết nối
                while True:
                    try:
                        data = await asyncio.wait_for(q.get(), timeout=30.0)
                        yield json.dumps(data)
                    except asyncio.TimeoutError:
                        yield json.dumps({"type": "HEARTBEAT"})
            finally:
                _hub.unsubscribe(q)

        return ServerSentEvent(_gen())

    # ------------------------------------------------------------------
    # 3. Dashboard summary
    # ------------------------------------------------------------------
    @get("/summary")
    async def get_summary(
        self,
        db_session: AsyncSession,
        hours: Annotated[int, Parameter(ge=1, le=720)] = 24,
        date_from: Annotated[Optional[str], Parameter(required=False)] = None,
        date_to: Annotated[Optional[str], Parameter(required=False)] = None,
    ) -> FraudSummary:
        """Thống kê fraud tổng hợp với CPC thực tế từ Google Ads."""
        try:
            # 1. Xác định khoảng thời gian cho Google Ads API
            if not date_from or not date_to:
                now = datetime.now(UTC)
                dt_from = now - timedelta(hours=hours)
                date_from = dt_from.strftime("%Y-%m-%d")
                date_to = now.strftime("%Y-%m-%d")

            # 2. Lấy Average CPC thực tế và Totals từ Google Ads
            avg_cpc = 5000.0 # fallback
            google_all = 0
            google_invalid = 0
            google_wasted = 0.0
            
            try:
                google_metrics = await _reporter.fetch_invalid_click_metrics(
                    date_from=date_from, date_to=date_to
                )
                if google_metrics:
                    google_all = sum(m["clicks"] for m in google_metrics)
                    google_invalid = sum(m["invalid_clicks"] for m in google_metrics)
                    google_wasted = sum(m["cost_vnd"] for m in google_metrics)
                    
                    if google_invalid > 0:
                        avg_cpc = google_wasted / google_invalid
            except Exception as e:
                logger.warning("FETCH_GOOGLE_TOTALS_FAILED: %s", e)

            # 3. Trả về summary với real CPC và Google Totals
            analytics = FraudAnalyticsService(db_session)
            return await analytics.get_summary(
                hours=hours, 
                date_from=date_from, 
                date_to=date_to,
                avg_cpc=avg_cpc,
                google_all=google_all,
                google_invalid=google_invalid,
                google_wasted=google_wasted
            )
        except Exception as e:
            logger.error("GET_SUMMARY_CRITICAL_FAILURE: %s", e, exc_info=True)
            # Fallback tối thượng để không bao giờ chết dashboard
            analytics = FraudAnalyticsService(db_session)
            return await analytics.get_summary(hours=hours)

    # ------------------------------------------------------------------
    # 4. Optimization insights
    # ------------------------------------------------------------------
    @get("/insights")
    async def get_insights(
        self, 
        db_session: AsyncSession,
        date_from: Annotated[Optional[str], Parameter(required=False)] = None,
        date_to: Annotated[Optional[str], Parameter(required=False)] = None,
    ) -> list[OptimizationInsight]:
        """Phân tích patterns theo khoảng thời gian và đề xuất tối ưu campaign."""
        analytics = FraudAnalyticsService(db_session)
        return await analytics.get_optimization_insights(
            date_from=date_from, 
            date_to=date_to
        )

    # ------------------------------------------------------------------
    # 5. Generate Investigation Report (Manual refund request)
    # ------------------------------------------------------------------
    @post("/generate-investigation-report")
    async def generate_investigation_report(
        self,
        db_session: AsyncSession,
        data: InvestigationReportRequest,
    ) -> InvestigationReportResult:
        """
        Tổng hợp fraud events theo khoảng thời gian →
        tạo CSV bằng chứng + email template gửi Google Ads Support.
        """
        analytics = FraudAnalyticsService(db_session)
        return await analytics.build_weekly_investigation_package(
            date_from=data.date_from,
            date_to=data.date_to,
            avg_cpc_vnd=data.avg_cpc_vnd,
            force_rebuild=data.force
        )

    @get("/investigation-reports")
    async def list_investigation_reports(self) -> list[dict[str, str]]:
        """Lấy danh sách các tệp báo cáo pháp y đã tạo trong quá khứ."""
        report_dir = Path("reports/click_fraud")
        if not report_dir.exists():
            return []
        
        reports = []
        # Chỉ lấy file .txt (investigation report summary)
        for f in sorted(report_dir.glob("investigation_*.txt"), reverse=True):
            reports.append({
                "name": f.name,
                "date": f.name.replace("investigation_", "").replace(".txt", ""),
                "path": f"/reports/click_fraud/{f.name}"
            })
        return reports

    @get("/investigation-report-content/{filename:str}")
    async def get_investigation_report_content(self, filename: str) -> dict:
        """Lấy nội dung chi tiết của một báo cáo cũ."""
        file_path = Path("reports/click_fraud") / filename
        if not file_path.exists():
            return {"status": "not_found"}
        
        content = file_path.read_text()
        return {
            "status": "ready",
            "support_message_preview": content,
            "total_fraud_clicks": content.count("GCLID:"),
            "csv_path": f"/reports/click_fraud/{filename.replace('.txt', '.csv')}",
            "estimated_wasted_vnd": 0
        }

    # ------------------------------------------------------------------
    # 6. Google Ads Invalid Click Metrics (cần env GOOGLE_ADS_* credentials)
    # ------------------------------------------------------------------
    @get("/google-metrics")
    async def get_google_metrics(
        self,
        date_from: Annotated[str, Parameter(description="Từ ngày (YYYY-MM-DD)")],
        date_to:   Annotated[str, Parameter(description="Đến ngày (YYYY-MM-DD)")],
    ) -> list[GoogleInvalidClickMetric]:
        """
        Lấy invalid click metrics trực tiếp từ Google Ads Reporting API v24.
        Trả list rỗng nếu chưa cấu hình hoặc API lỗi.
        """
        try:
            metrics = await _reporter.fetch_invalid_click_metrics(
                date_from=date_from, date_to=date_to
            )
            return [GoogleInvalidClickMetric(**m) for m in metrics]
        except Exception as e:
            logger.error("GET_GOOGLE_METRICS_CONTROLLER_FAILED: %s", e)
            return []

    # ══════════════════════════════════════════════════════════════════
    # CAMPAIGN MANAGER — Google Ads API v24
    # ══════════════════════════════════════════════════════════════════

    # ------------------------------------------------------------------
    # 7. Danh sách Campaigns
    # ------------------------------------------------------------------
    @get("/campaigns")
    async def list_campaigns(
        self, db_session: AsyncSession
    ) -> list[CampaignInfo]:
        """
        Lấy danh sách campaigns với metrics 30 ngày gần nhất.
        Trả list rỗng nếu chưa cấu hình credentials.
        """
        return await _campaign_mgr.list_campaigns(db_session=db_session)

    # ------------------------------------------------------------------
    # 8. Tạo Campaign mới (Policy validation bắt buộc)
    # ------------------------------------------------------------------
    @post("/campaigns", status_code=201)
    async def create_campaign(
        self, data: CampaignCreateRequest
    ) -> CampaignOperationResult:
        """
        Tạo campaign mới. Luôn tạo ở trạng thái PAUSED để an toàn.
        Policy validation tự động — trả lỗi chi tiết nếu vi phạm.
        """
        return await _campaign_mgr.create_campaign(data)

    # ------------------------------------------------------------------
    # 9. Cập nhật trạng thái Campaign (ENABLED / PAUSED / REMOVED)
    # ------------------------------------------------------------------
    @patch("/campaigns/{campaign_id:str}/status")
    async def update_campaign_status(
        self,
        campaign_id: str,
        data: CampaignStatusUpdate,
    ) -> CampaignOperationResult:
        """Bật, Tắt hoặc Xóa campaign theo resource name."""
        resource = f"customers/{_campaign_mgr._CUSTOMER_ID}/campaigns/{campaign_id}"
        return await _campaign_mgr.update_status(resource, data)

    # ------------------------------------------------------------------
    # 10. Cập nhật ngân sách Campaign
    # ------------------------------------------------------------------
    @patch("/campaigns/{campaign_id:str}/budget")
    async def update_campaign_budget(
        self,
        campaign_id: str,
        data: CampaignBudgetUpdate,
    ) -> CampaignOperationResult:
        """Cập nhật ngân sách ngày của campaign (đơn vị VNĐ)."""
        resource = f"customers/{_campaign_mgr._CUSTOMER_ID}/campaigns/{campaign_id}"
        return await _campaign_mgr.update_budget(resource, data)

    # ------------------------------------------------------------------
    # 11. Danh sách Ad Groups của một Campaign
    # ------------------------------------------------------------------
    @get("/campaigns/{campaign_id:str}/ad-groups")
    async def list_ad_groups(
        self, campaign_id: str
    ) -> list[AdGroupInfo]:
        """Lấy danh sách ad groups với metrics."""
        resource = f"customers/{_campaign_mgr._CUSTOMER_ID}/campaigns/{campaign_id}"
        return await _campaign_mgr.list_ad_groups(resource)

    # ------------------------------------------------------------------
    # 12. Tạo Ad Group + Keywords
    # ------------------------------------------------------------------
    @post("/ad-groups", status_code=201)
    async def create_ad_group(
        self, data: AdGroupCreateRequest
    ) -> CampaignOperationResult:
        """Tạo ad group với danh sách keywords. Match type: BROAD | PHRASE | EXACT."""
        return await _campaign_mgr.create_ad_group(data)

    # ------------------------------------------------------------------
    # 13. Tạo Responsive Search Ad (Policy validation bắt buộc)
    # ------------------------------------------------------------------
    @post("/ads", status_code=201)
    async def create_ad(
        self, data: ResponsiveSearchAdCreate
    ) -> CampaignOperationResult:
        """
        Tạo Responsive Search Ad.
        Tự động kiểm tra 15 quy tắc chính sách Google Ads trước khi submit.
        """
        return await _campaign_mgr.create_responsive_search_ad(data)

    # ------------------------------------------------------------------
    # 14. Danh sách Ads của một Ad Group
    # ------------------------------------------------------------------
    @get("/ad-groups/{ad_group_id:str}/ads")
    async def list_ads(
        self, ad_group_id: str
    ) -> list[AdInfo]:
        """Lấy danh sách ads của ad group với policy status."""
        resource = f"customers/{_campaign_mgr._CUSTOMER_ID}/adGroups/{ad_group_id}"
        return await _campaign_mgr.list_ads(resource)

    # ------------------------------------------------------------------
    # 15. Gợi ý từ khóa (Keyword Planner)
    # ------------------------------------------------------------------
    @post("/keyword-suggestions")
    async def get_keyword_suggestions(
        self, data: dict[str, list[str]]
    ) -> list[KeywordSuggestion]:
        """
        Gợi ý từ khóa từ Google Keyword Planner.
        Body: {"keywords": ["serum trắng da", "mỹ phẩm Nhật"]}
        """
        seeds = data.get("keywords", [])
        return await _campaign_mgr.get_keyword_suggestions(seeds)

    # ------------------------------------------------------------------
    # 16. Kiểm tra Policy (không submit — chỉ validate)
    # ------------------------------------------------------------------
    @post("/validate-policy")
    async def validate_ad_policy(
        self, data: ResponsiveSearchAdCreate
    ) -> PolicyCheckResult:
        """
        Kiểm tra 15 quy tắc chính sách Google Ads cho một Responsive Search Ad.
        Không cần credentials — hoạt động hoàn toàn offline.
        """
        return _campaign_mgr.validate_ad_policy(data)

    # ------------------------------------------------------------------
    # 17. AI Suggestion (Xohi Engine)
    # ------------------------------------------------------------------
    @post("/ai-suggest")
    async def get_ai_suggestion(
        self, data: AISuggestionRequest
    ) -> AISuggestionResponse:
        """
        Gợi ý chiến lược quảng cáo từ Xohi AI.
        Thực hiện trinh sát đối thủ và tối ưu theo luật Google 2026.
        """
        return await ai_strategist.suggest(data)
    # ------------------------------------------------------------------
    # 18. IP Blacklist Management
    # ------------------------------------------------------------------
    @get("/blacklist")
    async def list_ip_blacklist(
        self, db_session: AsyncSession
    ) -> list[dict]:
        """Lấy danh sách IP bị chặn từ Google Ads (Real-time)."""
        # 1. Lấy từ Google Ads
        google_blocked = await _campaign_mgr.list_all_blocked_ips()
        
        # 2. Lấy thêm từ local DB để đối soát
        stmt = select(IPBlacklist).order_by(IPBlacklist.created_at.desc())
        result = await db_session.execute(stmt)
        local_ips = result.scalars().all()
        
        # Merge kết quả (Ưu tiên Google Ads)
        merged = []
        for g in google_blocked:
            merged.append({
                "ip": g["ip"],
                "reason": f"Chặn trên chiến dịch: {g['campaign_name']}",
                "fraud_score": 1.0,
                "blocked_at": "Real-time",
                "hits": "N/A"
            })
            
        for i in local_ips:
            if not any(m["ip"] == i.ip_address for m in merged):
                merged.append({
                    "ip": i.ip_address,
                    "reason": i.reason,
                    "fraud_score": i.fraud_score,
                    "blocked_at": i.created_at.isoformat(),
                    "hits": 1
                })
        return merged

    @post("/blacklist")
    async def block_ip(
        self, db_session: AsyncSession, data: dict
    ) -> CampaignOperationResult:
        """Chặn IP: Submit lên Google Ads (Campaign mặc định) và lưu local."""
        ip = data.get("ip")
        reason = data.get("reason", "Manual block")
        campaign_id = data.get("campaign_id") # Optional
        
        if not ip:
            return CampaignOperationResult(success=False, operation="BLOCK", message="Thiếu địa chỉ IP")

        is_global = data.get("is_global", False)

        # 1. Submit lên Google Ads (Nếu có campaign_id hoặc Global)
        success_google = False
        if campaign_id or is_global:
            resource = f"customers/{_campaign_mgr._CUSTOMER_ID}/campaigns/{campaign_id}" if campaign_id else ""
            success_google = await _campaign_mgr.block_ip(resource, ip, is_global=is_global)
        
        # 2. Lưu vào local DB để quản lý tập trung
        new_bl = IPBlacklist(ip_address=ip, reason=reason, fraud_score=1.0)
        db_session.add(new_bl)
        await db_session.commit()
        
        return CampaignOperationResult(
            success=success_google,
            operation="BLOCK",
            message=f"Đã chặn IP {ip} trên hệ thống." + (" (Đã đồng bộ Google)" if success_google else " (Lỗi đồng bộ Google)")
        )

    @delete("/blacklist/{ip:str}", status_code=200)
    async def unblock_ip(
        self, db_session: AsyncSession, ip: str
    ) -> CampaignOperationResult:
        """Gỡ chặn IP khỏi local DB."""
        stmt = sa_delete(IPBlacklist).where(IPBlacklist.ip_address == ip)
        await db_session.execute(stmt)
        await db_session.commit()
        return CampaignOperationResult(success=True, operation="UNBLOCK", message=f"Đã gỡ chặn IP {ip}")

    # ------------------------------------------------------------------
    # 19. Negative Keywords Management
    # ------------------------------------------------------------------
    @get("/negative-keywords")
    async def list_global_negative_keywords(self) -> list[dict]:
        """Lấy danh sách từ khóa phủ định cấp tài khoản từ Google Ads."""
        return await _campaign_mgr.list_account_negative_keywords()

    @post("/negative-keywords")
    async def add_global_negative_keywords(self, data: dict) -> dict:
        """Thêm từ khóa phủ định vào cấp TÀI KHOẢN."""
        keywords = data.get("keywords", [])
        if not keywords:
            return {"success": False, "message": "No keywords provided"}
        
        success = await _campaign_mgr.add_account_negative_keywords(keywords)
        return {"success": success}

    @get("/campaigns/{campaign_id:str}/negative-keywords")
    async def list_negative_keywords(
        self, campaign_id: str
    ) -> list[dict]:
        """Lấy danh sách từ khóa phủ định trực tiếp từ Google Ads."""
        resource = f"customers/{_campaign_mgr._CUSTOMER_ID}/campaigns/{campaign_id}"
        return await _campaign_mgr.list_negative_keywords(resource)

    @post("/campaigns/{campaign_id:str}/negative-keywords")
    async def add_negative_keyword(
        self, campaign_id: str, data: dict
    ) -> CampaignOperationResult:
        """Thêm từ khóa phủ định lên Google Ads."""
        text = data.get("text")
        is_global = data.get("is_global", False)
        if not text:
            return CampaignOperationResult(success=False, operation="ADD_NEGATIVE", message="Thiếu từ khóa")
        
        resource = f"customers/{_campaign_mgr._CUSTOMER_ID}/campaigns/{campaign_id}"
        # Tách danh sách nếu Sếp nhập nhiều dòng
        keywords = [k.strip() for k in text.split("\n") if k.strip()]
        
        success_count = 0
        for kw in keywords:
            # Lưu ý: CampaignManager hiện tại nhận campaign_id thay vì resource
            if await _campaign_mgr.add_negative_keyword(campaign_id, kw, is_global=is_global):
                success_count += 1
        
        return CampaignOperationResult(
            success=success_count > 0,
            operation="ADD_NEGATIVE",
            message=f"Đã thêm thành công {success_count}/{len(keywords)} từ khóa phủ định." + (" (Toàn cầu)" if is_global else "")
        )
