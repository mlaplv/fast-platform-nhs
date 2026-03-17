import logging
import hashlib
import copy
from datetime import datetime, timezone
from typing import List, Dict, Union, Optional
from uuid import UUID

logger = logging.getLogger("api-gateway")
from litestar import Controller, get, post, put, patch, delete, Request
from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.schemas.campaign import (
    ContentCampaign as CampaignSchema,
    CampaignStep,
    AgentResponse,
    CampaignListResponse,
    GenericResponse
)
from backend.services.campaign_service import campaign_service
from backend.services.content_service import content_service
from backend.services.xohi.creative_studio.models.schemas import AgentSignal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from litestar.di import Provide

class ContentController(Controller):
    path = "/api/v1/content"

    @get("/campaigns")
    async def list_campaigns(
        self,
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0
    ) -> CampaignListResponse:
        """Lấy danh sách các chiến dịch hỗ trợ phân trang (Elite V2.2 Zero-Hydration)."""
        from sqlalchemy import text

        # 1. Total Count (Surgical)
        total = await db_session.scalar(text("SELECT COUNT(*) FROM content_campaigns WHERE deleted_at IS NULL")) or 0

        # 2. Paged results (Zero-Hydration)
        sql = text("""
            SELECT id, topic_data, status, current_step, created_at, user_id
            FROM content_campaigns
            WHERE deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        result = await db_session.execute(sql, {"limit": limit, "offset": offset})

        items = [
            {
                "id": str(row[0]),
                "topic_data": row[1] or {},
                "status": row[2],
                "current_step": row[3],
                "created_at": row[4].isoformat() if row[4] else "",
                "user_id": str(row[5]) if row[5] else None
            }
            for row in result
        ]

        return CampaignListResponse(
            items=items,
            total=total,
            has_more=(offset + limit) < total,
            limit=limit,
            offset=offset
        )

    @get("/campaigns/{campaign_id:uuid}")
    async def get_campaign(self, campaign_id: UUID, db_session: AsyncSession) -> CampaignSchema:
        """Lấy thông tin chi tiết một chiến dịch (Zero-Hydration)."""
        campaign = await campaign_service.get_campaign(db_session, str(campaign_id))
        if not campaign:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Campaign {campaign_id} not found")

        return CampaignSchema.model_validate(campaign)

    @post("/campaigns/{campaign_id:uuid}/approve")
    async def approve_step(self, campaign_id: UUID, request: Request, db_session: AsyncSession) -> GenericResponse:
        """User phê duyệt bước sáng tạo hiện tại."""
        data: Dict[str, object] = await request.json()
        return await content_factory.approve_step(str(campaign_id), data, db_session)

    @post("/campaigns/{campaign_id:uuid}/retry")
    async def retry_step(self, campaign_id: UUID, db_session: AsyncSession) -> GenericResponse:
        """Chạy lại bước sáng tạo hiện tại."""
        return await content_factory.retry_step(str(campaign_id), db_session)

    @post("/campaigns/{campaign_id:uuid}/publish")
    async def publish_campaign(self, campaign_id: UUID, db_session: AsyncSession) -> GenericResponse:
        """Xuất bản và địa phương hóa toàn bộ tài nguyên (Zero-Hydration)."""
        campaign = await campaign_service.get_campaign(db_session, str(campaign_id))
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")

        from backend.services.xohi.creative_studio.formatters.media_compressor import MediaCompressor
        compressor = MediaCompressor()

        # 1. Localize assets and update registry (Internal Logic uses raw SQL)
        await compressor.execute(str(campaign_id), db_session)

        # 2. Final Status Update (Surgical)
        await campaign_service.update_campaign(db_session, str(campaign_id), {"status": "COMPLETED"})

        await db_session.commit()
        return GenericResponse(status="success", message="Campaign published and registered.")

    @put("/campaigns/{campaign_id:uuid}/metadata")
    async def update_metadata(self, campaign_id: UUID, request: Request, db_session: AsyncSession) -> GenericResponse:
        """Cập nhật dữ liệu chiến dịch (keywords, assets...)."""
        data: Dict[str, object] = await request.json()
        return await content_factory.update_metadata(str(campaign_id), data, db_session)

    @patch("/campaigns/{campaign_id:uuid}")
    async def patch_campaign(self, campaign_id: UUID, request: Request, db_session: AsyncSession) -> GenericResponse:
        """RESTful Alias cho update_metadata."""
        data: Dict[str, object] = await request.json()
        return await content_factory.update_metadata(str(campaign_id), data, db_session)

    @delete("/campaigns/{campaign_id:uuid}", status_code=200)
    async def delete_campaign(self, campaign_id: UUID, db_session: AsyncSession) -> GenericResponse:
        """Xóa chiến dịch, toàn bộ file vật lý và log liên quan (Full Surgical Purge - Elite V2.2)."""
        try:
            import os
            cid_str = str(campaign_id)

            # 0. Get essential info (Zero-Hydration)
            campaign = await campaign_service.get_campaign(db_session, cid_str)
            if not campaign:
                return GenericResponse(status="error", message="Campaign not found")
            user_id = campaign.get("user_id")

            # 1. PHYSICAL FILE PURGE (Raw SQL Projection)
            media_sql = text("SELECT file_path FROM media_registry WHERE campaign_id = :cid")
            media_result = await db_session.execute(media_sql, {"cid": cid_str})
            assets = media_result.all()

            files_purged = 0
            for row in assets:
                file_path = row[0]
                # Chuyển path từ /v65_assets/... thành path vật lý
                rel_path = file_path.lstrip("/")
                full_path = os.path.join("frontend/static", rel_path)

                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                        files_purged += 1
                    except Exception as fe:
                        logger.warning(f"[Purge] Failed to remove physical file {full_path}: {fe}")

            # 2. SURGICAL DB PURGE (Atomic SQL)
            # 2.1 Media Registry
            await db_session.execute(text("DELETE FROM media_registry WHERE campaign_id = :cid"), {"cid": cid_str})

            # 2.2 Chat Messages (Neural Logs)
            await db_session.execute(
                text("DELETE FROM chat_messages WHERE (content->>'campaign_id') = :cid"),
                {"cid": cid_str}
            )

            # 2.3 Campaign Events
            await db_session.execute(text("DELETE FROM campaign_events WHERE campaign_id = :cid"), {"cid": cid_str})

            # 3. Cache Eviction (V76.5 Recovery)
            if user_id:
                from backend.services.xohi_memory import xohi_memory
                cache_key = f"xohi:chat:{user_id}"
                if getattr(xohi_memory, "_use_redis", False):
                    await xohi_memory.client.delete(cache_key)
                    logger.info(f"[Purge] Evicted Redis cache for user {user_id}: {cache_key}")

            # 4. Delete the campaign itself
            await db_session.execute(text("DELETE FROM content_campaigns WHERE id = :cid"), {"cid": cid_str})

            # 5. SSE POISON PILL (V65.0 Cleanup)
            from backend.services.event_bus import event_bus
            event_bus.emit("CAMPAIGN_PURGED", {
                "campaign_id": cid_str,
                "type": "TERMINATE",
                "action": "PURGE"
            })

            await db_session.commit()

            logger.info(f"[Purge] Campaign {cid_str} wiped. Files removed: {files_purged}")
            return GenericResponse(
                status="success",
                message=f"Campaign wiped. {files_purged} assets and neural logs purged."
            )
        except Exception as e:
            logger.error(f"[ContentController] Purge failed for {campaign_id}: {str(e)}")
            return GenericResponse(status="error", message=str(e))

    @post("/campaigns/{campaign_id:uuid}/analyze/copyright")
    async def analyze_copyright(self, campaign_id: UUID, db_session: AsyncSession, force: bool = False) -> GenericResponse:
        """
        On-demand: ĐẠO VĂN & BẢN QUYỀN (Zero-Hydration).
        """
        from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
        campaign = await campaign_service.get_campaign(db_session, str(campaign_id))
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")

        draft_text = campaign.get("draft_content") or ""
        if not draft_text:
            return GenericResponse(status="error", message="Chưa có nội dung để kiểm tra.")

        cop = PlagiarismCop()

        # Expert Optimizer (V71.30): Content Fingerprinting
        content_hash = hashlib.sha256(draft_text.encode('utf-8')).hexdigest()
        gold = dict(campaign.get("gold_metadata") or {})
        cache = gold.get("analysis_cache", {})

        if not force and cache.get("copyright", {}).get("hash") == content_hash:
            return GenericResponse(status="success", data=cache["copyright"]["data"])

        try:
            result = await cop.analyze(campaign, db_session)
            result_data = result.model_dump()

            # Archiving & Metrics
            cache["copyright"] = {"hash": content_hash, "data": result_data, "at": datetime.now(timezone.utc).isoformat()}
            metrics = gold.get("analysis_metrics", {})
            metrics.update({
                "unique_score": result.uniqueness_score,
                "copyright_risk": result.risk_level,
                "last_analyzed": datetime.now(timezone.utc).isoformat()
            })

            # SURGICAL UPDATE (R1.5)
            await campaign_service.update_campaign(db_session, str(campaign_id), {
                "gold_metadata": {**gold, "analysis_cache": cache, "analysis_metrics": metrics},
                "unique_score": result.uniqueness_score
            })

            await db_session.commit()

            logger.info(f"[Copyright] Returning success for campaign {campaign_id}")
            return GenericResponse(status="success", data=result_data)
        except Exception as e:
            logger.error(f"[ContentController] Copyright analysis failed: {str(e)}", exc_info=True)
            return GenericResponse(status="error", message=str(e))

    @post("/campaigns/{campaign_id:uuid}/analyze/seo")
    async def analyze_seo(self, campaign_id: UUID, db_session: AsyncSession, force: bool = False) -> GenericResponse:
        """
        On-demand: PHÂN TÍCH SEO (Zero-Hydration).
        """
        from backend.services.xohi.creative_studio.operatives.seo_analyzer import SeoAnalyzer
        campaign = await campaign_service.get_campaign(db_session, str(campaign_id))
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")

        draft_text = campaign.get("draft_content") or ""
        if not draft_text:
            return GenericResponse(status="error", message="Chưa có nội dung để phân tích.")

        analyzer = SeoAnalyzer()

        # Expert Optimizer (V71.30): Content Fingerprinting
        content_hash = hashlib.sha256(draft_text.encode('utf-8')).hexdigest()
        gold = dict(campaign.get("gold_metadata") or {})
        cache = gold.get("analysis_cache", {})

        if not force and cache.get("seo", {}).get("hash") == content_hash:
            return GenericResponse(status="success", data=cache["seo"]["data"])

        try:
            result = await analyzer.analyze(campaign, db_session)
            result_data = result.model_dump()

            # Archiving & Metrics
            cache["seo"] = {"hash": content_hash, "data": result_data, "at": datetime.now(timezone.utc).isoformat()}
            metrics = gold.get("analysis_metrics", {})
            metrics.update({
                "seo_score": result.total_score,
                "seo_grade": result.grade,
                "last_analyzed": datetime.now(timezone.utc).isoformat()
            })

            # SURGICAL UPDATE (R1.5)
            await campaign_service.update_campaign(db_session, str(campaign_id), {
                "gold_metadata": {**gold, "analysis_cache": cache, "analysis_metrics": metrics}
            })

            await db_session.commit()
            return GenericResponse(status="success", data=result_data)
        except Exception as e:
            logger.error(f"[ContentController] SEO analysis failed: {str(e)}")
            return GenericResponse(status="error", message=str(e))

    @post("/campaigns/{campaign_id:uuid}/analyze/ai-inspect")
    async def analyze_ai_readiness(self, campaign_id: UUID, db_session: AsyncSession, force: bool = False) -> GenericResponse:
        """
        On-demand: AI READINESS INSPECTOR (Zero-Hydration).
        """
        from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector
        campaign = await campaign_service.get_campaign(db_session, str(campaign_id))
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")

        draft_text = campaign.get("draft_content") or ""
        if not draft_text:
            return GenericResponse(status="error", message="Chưa có nội dung để phân tích AI Readiness.")

        inspector = AiInspector()
        # Expert Optimizer (V71.30): Content Fingerprinting
        content_hash = hashlib.sha256(draft_text.encode('utf-8')).hexdigest()
        gold = dict(campaign.get("gold_metadata") or {})
        cache = gold.get("analysis_cache", {})

        if not force and cache.get("ai_inspect", {}).get("hash") == content_hash:
            return GenericResponse(status="success", data=cache["ai_inspect"]["data"])

        try:
            result = await inspector.analyze(campaign, db_session)
            result_data = result.model_dump()

            # Archiving & Metrics
            cache["ai_inspect"] = {"hash": content_hash, "data": result_data, "at": datetime.now(timezone.utc).isoformat()}
            metrics = gold.get("analysis_metrics", {})
            metrics.update({
                "ai_ready_score": result.geo_score,
                "last_analyzed": datetime.now(timezone.utc).isoformat()
            })

            # SURGICAL UPDATE (R1.5)
            await campaign_service.update_campaign(db_session, str(campaign_id), {
                "gold_metadata": {**gold, "analysis_cache": cache, "analysis_metrics": metrics}
            })

            await db_session.commit()
            return GenericResponse(status="success", data=result_data)
        except Exception as e:
            logger.error(f"AI Inspector error: {e}")
            return GenericResponse(status="error", message=str(e))

    @post("/campaigns/{campaign_id:uuid}/analyze/auto-fix")
    async def analyze_auto_fix(self, campaign_id: UUID, request: Request, db_session: AsyncSession) -> GenericResponse:
        """
        On-Demand Surgical Auto-Fix (Zero-Hydration)
        """
        try:
            from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector, AutoFixRequest
            campaign = await campaign_service.get_campaign(db_session, str(campaign_id))
            if not campaign:
                return GenericResponse(status="error", message="Campaign not found")

            if not campaign.get("draft_content"):
                return GenericResponse(status="error", message="Chưa có nội dung để biên tập.")

            inspector = AiInspector()
            data = await request.json()
            fix_req = AutoFixRequest(**data)

            result = await inspector.auto_fix(campaign, fix_req, db_session)
            return GenericResponse(status="success", data=result.model_dump())
        except Exception as e:
            logger.error(f"Auto-Fix error: {e}")
            return GenericResponse(status="error", message=str(e))

    @post("/campaigns/{campaign_id:uuid}/analyze/bulk-fix")
    async def analyze_bulk_fix(self, campaign_id: UUID, request: Request, db_session: AsyncSession) -> GenericResponse:
        """
        On-Demand Bulk Surgical Rewrite (Zero-Hydration).
        """
        try:
            from backend.services.xohi.creative_studio.models.schemas import BulkFixRequest
            from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector
            from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop

            campaign = await campaign_service.get_campaign(db_session, str(campaign_id))
            if not campaign:
                return GenericResponse(status="error", message="Campaign not found")

            draft_content = campaign.get("draft_content") or ""
            if not draft_content:
                return GenericResponse(status="error", message="Chưa có nội dung để biên tập.")

            data = await request.json()
            fix_req = BulkFixRequest(**data)

            operative = PlagiarismCop() if fix_req.category == "copyright" else AiInspector()
            result = await operative.bulk_fix(campaign, fix_req, db_session)

            # ✅ Surgical Update if content changed
            if result.new_content and result.new_content != draft_content:
                await campaign_service.update_campaign(db_session, str(campaign_id), {"draft_content": result.new_content})
                await db_session.commit()
                logger.info(f"[BulkFix] Persisted new_content for campaign {campaign_id}")

            return GenericResponse(status="success", data=result.model_dump())
        except Exception as e:
            logger.error(f"Bulk-Fix error: {e}")
            return GenericResponse(status="error", message=str(e))


    @post("/clean")
    async def clean_content(self, request: Request) -> GenericResponse:
        """
        Phase 76.9: Viral 2026 Semantic Polishing.
        Làm sạch chuyên sâu: xóa link rác, code thừa, và tối ưu nhịp điệu bài viết.
        """
        try:
            from backend.utils.noise_cleaner import noise_cleaner
            data = await request.json()
            content = data.get("content", "")
            if not content:
                return GenericResponse(status="error", message="Không có nội dung để làm sạch")

            # Layer 1: Deterministic & Fuzzy Clean (Viral 2026 - Zero AI Cost)
            cleaned = await noise_cleaner.clean(content, mode="aggressive")

            return GenericResponse(status="success", data={"content": cleaned})
        except Exception as e:
            logger.error(f"[ContentController] Viral Clean Error: {e}")
            return GenericResponse(status="error", message=str(e))

