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
from litestar.response import ServerSentEvent, File
from litestar.exceptions import HTTPException
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
from backend.services.ads_protection.ads_fraud_manager import AdsFraudManager
from backend.services.ads_protection.pmax_upgrader import PMaxUpgrader
from backend.services.ads_protection.ai_strategist import ai_strategist
from backend.services.ads_protection.schemas import (
    AISuggestionRequest,
    AISuggestionResponse,
    CampaignOperationResult,
    CompetitorAnalysisRequest,
    CompetitorAnalysisResponse,
    PolicyShieldValidateRequest,
    PMaxUpgradeRequest,
    PMaxAssetGroupResponse,
    PolicyAuditHistoryItem,
)
from backend.services.ads_protection.policy_shield import policy_shield
from backend.database.models.ads import IPBlacklist, NegativeKeyword, AIPolicyAuditLog
from sqlalchemy import select, delete as sa_delete

from backend.services.xohi_memory import xohi_memory
from backend.core.stream_handler import RedisStreamProducer
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum

logger = logging.getLogger("api-gateway")

# Stateless singletons (chỉ khởi tạo một lần, không giữ state DB)
_fraud_svc      = ClickFraudService()
_reporter       = GoogleAdsReporter()
_campaign_mgr   = CampaignManager()
_fraud_mgr      = AdsFraudManager()
_pmax_mgr       = PMaxUpgrader()

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
            await pubsub.close()

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
    guards = [PermissionGuard(PermissionEnum.SYS_ADMIN)]

    # ------------------------------------------------------------------
    # 1. Validate click (public — gọi từ GTM landing page)
    # ------------------------------------------------------------------
    @post("/validate-click", status_code=200, guards=[])
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
        ip = (
            request.headers.get("x-real-ip")
            or request.headers.get("x-forwarded-for")
            or (request.client.host if request.client else None)
            or "127.0.0.1"
        )
        if "," in ip:
            ip = ip.split(",")[0].strip()
        data.ip_address = ip

        result = await _fraud_svc.analyze(data)

        analytics = FraudAnalyticsService(db_session)
        await analytics.record(result, data)

        # [V3.0 Fast Path] Queue Agentic Analysis (Slow Path) on-demand to arq
        # Only invoke deep agentic analysis for gray-zone cases to conserve VPS resources
        if 0.35 <= result.fraud_score <= 0.75:
            try:
                from backend.infra.arq_config import get_redis_settings
                from arq import create_pool
                redis_pool = await create_pool(get_redis_settings())
                try:
                    await redis_pool.enqueue_job(
                        "run_fraud_forensic",
                        {
                            "gclid": result.gclid,
                            "ip": result.ip_address,
                            "score": result.fraud_score,
                            "verdict": result.verdict,
                            "fingerprint": result.session_fingerprint
                        },
                        _queue_name="high"
                    )
                finally:
                    await redis_pool.aclose()
                logger.info(f"🕵️ [AdsProtection] Enqueued on-demand fraud forensic task for IP: {result.ip_address}")
            except Exception as eq:
                logger.error(f"❌ [AdsProtection] Failed to enqueue on-demand fraud forensic: {eq}")

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
                    if _fraud_mgr._has_credentials():
                        # Lệnh block IP thật trên Google Ads
                        asyncio.create_task(_fraud_mgr.block_ip(campaign_resource_name="", ip_address=result.ip_address, is_global=True))
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

    @get("/download-report/{filename:str}")
    async def download_report(self, filename: str) -> File:
        """Tải tệp báo cáo hoặc tệp CSV pháp y."""
        import os
        clean_filename = os.path.basename(filename)
        file_path = Path("reports/click_fraud") / clean_filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp báo cáo.")
        
        media_type = "text/csv" if clean_filename.endswith(".csv") else "text/plain"
        return File(
            path=file_path,
            filename=clean_filename,
            media_type=media_type
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
                "path": f"/api/v1/ads-protection/download-report/{f.name}"
            })
        return reports

    @get("/investigation-report-content/{filename:str}")
    async def get_investigation_report_content(self, filename: str) -> dict:
        """Lấy nội dung chi tiết của một báo cáo cũ."""
        file_path = Path("reports/click_fraud") / filename
        if not file_path.exists():
            return {"status": "not_found"}
        
        content = file_path.read_text(encoding="utf-8")
        
        import re
        total_fraud_clicks = 0
        estimated_wasted_vnd = 0
        
        # Parse total clicks
        click_match = re.search(r"Total suspected invalid clicks\s*:\s*(\d+)", content)
        if click_match:
            total_fraud_clicks = int(click_match.group(1))
        else:
            total_fraud_clicks = content.count("GCLID:")
            
        # Parse wasted spend
        wasted_match = re.search(r"Estimated wasted spend\s*:\s*([\d,]+)\s*VND", content)
        if wasted_match:
            estimated_wasted_vnd = int(wasted_match.group(1).replace(",", ""))
            
        return {
            "status": "ready",
            "support_message_preview": content,
            "total_fraud_clicks": total_fraud_clicks,
            "csv_path": f"/api/v1/ads-protection/download-report/{filename.replace('.txt', '.csv')}",
            "estimated_wasted_vnd": estimated_wasted_vnd
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
        """
        try:
            metrics = await _reporter.fetch_invalid_click_metrics(
                date_from=date_from, date_to=date_to
            )
            return [GoogleInvalidClickMetric(**m) for m in metrics]
        except ValueError as e:
            raise HTTPException(detail=str(e), status_code=400)
        except Exception as e:
            logger.error("GET_GOOGLE_METRICS_CONTROLLER_FAILED: %s", e)
            raise HTTPException(detail=f"Lỗi khi lấy dữ liệu từ Google Ads: {str(e)}", status_code=500)

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
        """
        try:
            return await _campaign_mgr.list_campaigns(db_session=db_session)
        except ValueError as e:
            raise HTTPException(detail=str(e), status_code=400)
        except Exception as e:
            logger.error("LIST_CAMPAIGNS_CONTROLLER_FAILED: %s", e)
            raise HTTPException(detail=f"Lỗi khi lấy danh sách chiến dịch: {str(e)}", status_code=500)

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
        try:
            resource = f"customers/{_campaign_mgr._CUSTOMER_ID}/campaigns/{campaign_id}"
            return await _campaign_mgr.list_ad_groups(resource)
        except ValueError as e:
            raise HTTPException(detail=str(e), status_code=400)
        except Exception as e:
            raise HTTPException(detail=f"Lỗi khi lấy danh sách nhóm quảng cáo: {str(e)}", status_code=500)

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
    # 13.5 Cập nhật trạng thái Responsive Search Ad
    # ------------------------------------------------------------------
    @patch("/ads/status", status_code=200)
    async def update_ad_status(
        self, data: dict
    ) -> CampaignOperationResult:
        """Cập nhật trạng thái mẫu quảng cáo (ENABLED / PAUSED / REMOVED)."""
        resource_name = data.get("resource_name")
        status = data.get("status")
        if not resource_name or not status:
            raise HTTPException(detail="Thiếu resource_name hoặc status", status_code=400)
        
        success = await _campaign_mgr.update_ad_status(resource_name, status)
        return CampaignOperationResult(
            success=success,
            resource_name=resource_name,
            operation="UPDATE",
            message=f"Mẫu quảng cáo đã được chuyển sang trạng thái {status}." if success else "Cập nhật thất bại."
        )

    # ------------------------------------------------------------------
    # 14. Danh sách Ads của một Ad Group
    # ------------------------------------------------------------------
    @get("/ad-groups/{ad_group_id:str}/ads")
    async def list_ads(
        self, ad_group_id: str
    ) -> list[AdInfo]:
        """Lấy danh sách ads của ad group với policy status."""
        try:
            resource = f"customers/{_campaign_mgr._CUSTOMER_ID}/adGroups/{ad_group_id}"
            return await _campaign_mgr.list_ads(resource)
        except ValueError as e:
            raise HTTPException(detail=str(e), status_code=400)
        except Exception as e:
            raise HTTPException(detail=f"Lỗi khi lấy danh sách mẫu quảng cáo: {str(e)}", status_code=500)

    # ------------------------------------------------------------------
    # 14.5 Danh sách Từ khóa của một Ad Group
    # ------------------------------------------------------------------
    @get("/ad-groups/{ad_group_id:str}/keywords")
    async def list_ad_group_keywords(
        self, ad_group_id: str
    ) -> list[str]:
        """Lấy danh sách các từ khóa đang hoạt động của Ad Group."""
        try:
            resource = f"customers/{_campaign_mgr._CUSTOMER_ID}/adGroups/{ad_group_id}"
            return await _campaign_mgr.list_ad_group_keywords(resource)
        except Exception as e:
            raise HTTPException(detail=f"Lỗi khi lấy từ khóa nhóm: {str(e)}", status_code=500)

    # ------------------------------------------------------------------
    # 14.6 Thêm Từ khóa vào một Ad Group
    # ------------------------------------------------------------------
    @post("/ad-groups/{ad_group_id:str}/keywords")
    async def add_ad_group_keywords(
        self, ad_group_id: str, data: dict
    ) -> CampaignOperationResult:
        """Thêm từ khóa vào Ad Group."""
        keywords = data.get("keywords", [])
        match_type = data.get("match_type", "EXACT")
        if not keywords:
            return CampaignOperationResult(
                success=False,
                operation="CREATE",
                message="Không có từ khóa nào được cung cấp."
            )
        try:
            resource = f"customers/{_campaign_mgr._CUSTOMER_ID}/adGroups/{ad_group_id}"
            success = await _campaign_mgr.add_ad_group_keywords(resource, keywords, match_type=match_type)
            err_msg = _campaign_mgr.get_last_mutate_error()
            msg = f"Đã thêm thành công {len(keywords)} từ khóa vào Ad Group." if success else (f"Thêm từ khóa thất bại: {err_msg}" if err_msg else "Thêm từ khóa thất bại.")
            return CampaignOperationResult(
                success=success,
                resource_name=resource,
                operation="CREATE",
                message=msg
            )
        except Exception as e:
            raise HTTPException(detail=f"Lỗi khi thêm từ khóa vào nhóm: {str(e)}", status_code=500)

    # ------------------------------------------------------------------
    # 14.7 Xóa Từ khóa khỏi một Ad Group
    # ------------------------------------------------------------------
    @delete("/ad-groups/{ad_group_id:str}/keywords", status_code=200)
    async def remove_ad_group_keyword(
        self, ad_group_id: str, keyword: str
    ) -> CampaignOperationResult:
        """Xóa từ khóa khỏi Ad Group."""
        if not keyword:
            return CampaignOperationResult(
                success=False,
                operation="REMOVE",
                message="Chưa cung cấp từ khóa cần xóa."
            )
        try:
            resource = f"customers/{_campaign_mgr._CUSTOMER_ID}/adGroups/{ad_group_id}"
            success = await _campaign_mgr.remove_ad_group_keyword(resource, keyword)
            err_msg = _campaign_mgr.get_last_mutate_error()
            msg = f"Đã xóa từ khóa '{keyword}' khỏi Ad Group." if success else (f"Xóa từ khóa thất bại: {err_msg}" if err_msg else "Xóa từ khóa thất bại.")
            return CampaignOperationResult(
                success=success,
                resource_name=resource,
                operation="REMOVE",
                message=msg
            )
        except Exception as e:
            raise HTTPException(detail=f"Lỗi khi xóa từ khóa: {str(e)}", status_code=500)

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
        if data.task == "RSA" and data.ad_group_resource_name:
            ad_group_kws = await _campaign_mgr.list_ad_group_keywords(data.ad_group_resource_name)
            if ad_group_kws:
                if not data.keywords:
                    data.keywords = []
                existing_kws = set(data.keywords)
                for kw in ad_group_kws:
                    if kw not in existing_kws:
                        data.keywords.append(kw)
        return await ai_strategist.suggest(data)

    # ------------------------------------------------------------------
    # 17.5 Competitor Research & Keyword Planning (Xohi Keyword Planner)
    # ------------------------------------------------------------------
    @post("/ai-competitor-research")
    async def get_competitor_research(
        self, data: CompetitorAnalysisRequest
    ) -> CompetitorAnalysisResponse:
        """
        Phân tích đối thủ, trinh sát trang đích và gợi ý từ khóa theo kế hoạch Google Ads.
        Tương đương Google Keyword Planner nhưng tích hợp AI + dữ liệu thực.
        """
        return await ai_strategist.competitor_research(data)

    # ------------------------------------------------------------------
    # 17.6 Chốt chặn kiểm duyệt AI (Policy Shield)
    # ------------------------------------------------------------------
    @post("/validate-policy-shield")
    async def validate_policy_shield(
        self,
        data: PolicyShieldValidateRequest,
        db_session: AsyncSession
    ) -> dict:
        """
        Quét chốt chặn kiểm duyệt AI cho từ khóa và ad copy.
        Tính toán điểm số tối ưu và lưu vào lịch sử audit.
        """
        policy_result = await policy_shield.validate(
            headlines=data.headlines,
            descriptions=data.descriptions,
            keywords=data.keywords,
            landing_page_url=data.landing_page_url
        )
        
        sensitive_count = len(policy_result.get("sensitive_warnings", []))
        mismatch_count = len(policy_result.get("landing_page_warnings", []))
        low_volume_count = len(policy_result.get("low_volume_warnings", []))
        violations_count = sensitive_count + mismatch_count + low_volume_count
        
        # Công thức tính điểm tối ưu hóa (Optimization Score)
        score = max(0.0, 100.0 - (sensitive_count * 15 + mismatch_count * 10 + low_volume_count * 5))
        
        policy_result["score"] = score
        policy_result["violations_count"] = violations_count
        
        # Xác định trạng thái an toàn
        if violations_count == 0:
            policy_result["status"] = "SAFE"
        elif any(v.get("severity") == "ERROR" for v in policy_result.get("sensitive_warnings", [])):
            policy_result["status"] = "DANGER"
        else:
            policy_result["status"] = "WARNING"
            
        # Lưu vào cơ sở dữ liệu
        log = AIPolicyAuditLog(
            ad_group_id=data.ad_group_id or "default_ad_group",
            landing_page_url=data.landing_page_url,
            score=score,
            violations_count=violations_count,
            sensitive_count=sensitive_count,
            mismatch_count=mismatch_count,
            low_volume_count=low_volume_count,
            details=json.dumps(policy_result, ensure_ascii=False)
        )
        db_session.add(log)
        await db_session.commit()
        
        return policy_result

    # ------------------------------------------------------------------
    # 17.7 Nâng cấp chiến dịch DSA lên AI Max (Performance Max)
    # ------------------------------------------------------------------
    @post("/campaigns/{campaign_id:str}/upgrade-to-aimax")
    async def upgrade_to_aimax(
        self,
        campaign_id: str,
        data: PMaxUpgradeRequest
    ) -> CampaignOperationResult:
        """
        Nâng cấp chiến dịch DSA lên AI Max (Performance Max).
        """
        return await _pmax_mgr.upgrade_dsa_to_pmax(
            dsa_campaign_id=campaign_id,
            budget_vnd=data.daily_budget_vnd,
            pmax_name=data.name,
            assets=data.assets
        )

    # ------------------------------------------------------------------
    # 17.7.5 Xem trước nội dung PMax AI sinh ra trước khi đăng
    # ------------------------------------------------------------------
    @get("/campaigns/{campaign_id:str}/preview-aimax-assets")
    async def preview_aimax_assets(
        self,
        campaign_id: str
    ) -> PMaxAssetGroupResponse:
        """
        Xem trước nội dung AI sinh ra cho chiến dịch PMax trước khi xác nhận đăng.
        """
        token = await _pmax_mgr._get_access_token()
        landing_page_url = "https://xohi.vn/pages/kem-duong-phuc-hoi-body" # fallback
        try:
            query = f"""
                SELECT ad_group_ad.ad.final_urls 
                FROM ad_group_ad 
                WHERE campaign.id = '{campaign_id}' 
                  AND ad_group_ad.status = 'ENABLED'
                LIMIT 1
            """
            ad_res = await _pmax_mgr._search(token, query)
            if ad_res and len(ad_res) > 0:
                urls = ad_res[0].get("adGroupAd", {}).get("ad", {}).get("finalUrls", [])
                if urls:
                    landing_page_url = urls[0]
        except Exception as e:
            logger.warning(f"Error fetching campaign final urls: {e}")
            
        return await ai_strategist.generate_pmax_assets(landing_page_url)

    # ------------------------------------------------------------------
    # 17.8 Lấy lịch sử điểm tối ưu hóa của nhóm quảng cáo
    # ------------------------------------------------------------------
    @get("/ad-groups/{ad_group_id:str}/policy-history")
    async def get_policy_history(
        self,
        ad_group_id: str,
        db_session: AsyncSession
    ) -> list[PolicyAuditHistoryItem]:
        """
        Lấy danh sách lịch sử điểm số tối ưu hóa của ad group.
        """
        stmt = select(AIPolicyAuditLog).where(
            (AIPolicyAuditLog.ad_group_id == ad_group_id) |
            (AIPolicyAuditLog.ad_group_id.like(f"%/{ad_group_id}")) |
            (AIPolicyAuditLog.ad_group_id.like(f"%{ad_group_id}%"))
        ).order_by(AIPolicyAuditLog.created_at.desc())
        res = await db_session.execute(stmt)
        logs = res.scalars().all()
        return [
            PolicyAuditHistoryItem(
                id=log.id,
                score=log.score,
                violations_count=log.violations_count,
                sensitive_count=log.sensitive_count,
                mismatch_count=log.mismatch_count,
                low_volume_count=log.low_volume_count,
                created_at=log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else ""
            ) for log in logs
        ]

    # ------------------------------------------------------------------
    # 17.8.2 Xóa lịch sử điểm tối ưu hóa của nhóm quảng cáo
    # ------------------------------------------------------------------
    @delete("/ad-groups/{ad_group_id:str}/policy-history", status_code=200)
    async def clear_policy_history(
        self,
        ad_group_id: str,
        db_session: AsyncSession
    ) -> dict:
        """
        Xóa lịch sử quét chính sách của nhóm quảng cáo.
        """
        stmt = sa_delete(AIPolicyAuditLog).where(
            (AIPolicyAuditLog.ad_group_id == ad_group_id) |
            (AIPolicyAuditLog.ad_group_id.like(f"%/{ad_group_id}")) |
            (AIPolicyAuditLog.ad_group_id.like(f"%{ad_group_id}%"))
        )
        await db_session.execute(stmt)
        await db_session.commit()
        return {"success": True, "message": "Đã xóa lịch sử quét chính sách."}



    # ------------------------------------------------------------------
    # 18. IP Blacklist Management
    # ------------------------------------------------------------------
    @get("/blacklist")
    async def list_ip_blacklist(
        self, db_session: AsyncSession
    ) -> list[dict]:
        """Lấy danh sách IP bị chặn từ Google Ads (Real-time)."""
        # 1. Lấy từ Google Ads
        google_blocked = await _fraud_mgr.list_all_blocked_ips()
        
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
            resource = f"customers/{_fraud_mgr._CUSTOMER_ID}/campaigns/{campaign_id}" if campaign_id else ""
            success_google = await _fraud_mgr.block_ip(resource, ip, is_global=is_global)
        
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
        return await _fraud_mgr.list_account_negative_keywords()

    @post("/negative-keywords")
    async def add_global_negative_keywords(self, data: dict) -> dict:
        """Thêm từ khóa phủ định vào cấp TÀI KHOẢN."""
        keywords = data.get("keywords", [])
        if not keywords:
            return {"success": False, "message": "No keywords provided"}
        
        success = await _fraud_mgr.add_account_negative_keywords(keywords)
        return {"success": success}

    @get("/campaigns/{campaign_id:str}/negative-keywords")
    async def list_negative_keywords(
        self, campaign_id: str
    ) -> list[dict]:
        """Lấy danh sách từ khóa phủ định trực tiếp từ Google Ads."""
        resource = f"customers/{_fraud_mgr._CUSTOMER_ID}/campaigns/{campaign_id}"
        return await _fraud_mgr.list_negative_keywords(resource)

    @post("/campaigns/{campaign_id:str}/negative-keywords")
    async def add_negative_keyword(
        self, campaign_id: str, data: dict
    ) -> CampaignOperationResult:
        """Thêm từ khóa phủ định lên Google Ads."""
        is_global = data.get("is_global", False)
        keywords = data.get("keywords", [])
        if not keywords:
            text = data.get("text")
            if text:
                keywords = [k.strip() for k in text.split("\n") if k.strip()]
                
        if not keywords:
            return CampaignOperationResult(success=False, operation="ADD_NEGATIVE", message="Thiếu từ khóa")
        
        resource = f"customers/{_fraud_mgr._CUSTOMER_ID}/campaigns/{campaign_id}"
        
        success_count = 0
        for kw in keywords:
            if await _fraud_mgr.add_negative_keyword(resource, kw, is_global=is_global):
                success_count += 1
        
        return CampaignOperationResult(
            success=success_count > 0,
            operation="ADD_NEGATIVE",
            message=f"Đã thêm thành công {success_count}/{len(keywords)} từ khóa phủ định." + (" (Toàn cầu)" if is_global else "")
        )

    @delete("/negative-keywords/{id:str}", status_code=200)
    async def remove_negative_keyword(self, id: str) -> CampaignOperationResult:
        """Xóa từ khóa phủ định khỏi Google Ads (hỗ trợ cả Campaign và Account level)."""
        success = await _fraud_mgr.remove_negative_keyword(id)
        return CampaignOperationResult(
            success=success,
            operation="REMOVE_NEGATIVE",
            message="Đã xóa từ khóa phủ định thành công." if success else "Xóa từ khóa phủ định thất bại."
        )
