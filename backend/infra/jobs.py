import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete, update
from backend.database.alchemy_config import alchemy_config
from backend.database.models.system import UnifiedAgentTask

logger = logging.getLogger("arq-worker")

async def cleanup_old_tasks(ctx: Dict[str, object]) -> None:
    """
    Elite V2.2: Retention Policy Enforcement (3-day limit).
    Deletes tasks and logs older than 3 days to protect SSD space.
    """
    logger.info("[Cleanup] Starting 3-day retention enforcement...")
    
    from backend.constants.infra import INFRA_RETENTION_DAYS
    # Calculate cutoff (Standard Elite Retention Policy)
    cutoff = datetime.now(timezone.utc) - timedelta(days=INFRA_RETENTION_DAYS)
    
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        try:
            # Delete tasks older than 3 days
            stmt = delete(UnifiedAgentTask).where(UnifiedAgentTask.created_at < cutoff)
            result = await db.execute(stmt)
            await db.commit()
            
            count = result.rowcount
            logger.info(f"[Cleanup] Successfully purged {count} old tasks from DB.")
        except Exception as e:
            logger.error(f"[Cleanup] Failed to purge old tasks: {e}")
            await db.rollback()

async def helen_follow_up_job(ctx: Dict[str, object], session_id: str) -> None:
    """
    Elite V2.2: Proactive Support Engagement.
    Scheduled 1 hour after Helen's reply to re-engage silent users.
    """
    from backend.database.alchemy_config import alchemy_config
    from backend.database.models.system import SupportChatHistory
    from sqlalchemy import select, desc
    
    logger.info(f"🌸 [Helen Follow-up] Checking session {session_id} for proactive reminder.")
    
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        try:
            # Check last message role
            stmt = (
                select(SupportChatHistory)
                .where(SupportChatHistory.session_id == session_id)
                .order_by(desc(SupportChatHistory.created_at), desc(SupportChatHistory.id))
                .limit(1)
            )
            res = await db.execute(stmt)
            last_msg = res.scalar_one_or_none()
            
            if last_msg and last_msg.role == "assistant":
                # Helen was the last speaker, and the user hasn't responded for 1 hour
                logger.info(f"🌸 [Helen Follow-up] User silent for 1h in {session_id}. Triggering Helen...")
                
                # Late import to avoid circular dependencies
                from backend.services.commerce.operatives.support_agent import support_agent
                from backend.schemas.support import SupportRequest
                
                from backend.constants.infra import HELEN_FOLLOW_UP_TRIGGER
                # Special internal trigger message (Elite V2.2)
                trigger_req = SupportRequest(
                    message=HELEN_FOLLOW_UP_TRIGGER,
                    session_id=session_id,
                    product_slug=last_msg.product_slug
                )
                
                # Inject a 'thought' event via event_bus before processing
                from backend.services.event_bus import event_bus
                await event_bus.emit("SUPPORT_THOUGHT", {"session_id": session_id, "think": "Đang chủ động chăm sóc Quý khách..."})
                
                # This will run the AI logic (Layer 2) and emit SUPPORT_RESPONSE_READY
                await support_agent.process_brain_logic(trigger_req, db)
                await db.commit()
            else:
                logger.info(f"🌸 [Helen Follow-up] Execution skipped: User already replied or no history for {session_id}.")
        except Exception as e:
            logger.error(f"🌸 [Helen Follow-up] CRITICAL FAILURE: {e}")
            await db.rollback()

async def helen_self_learning_job(ctx: Dict[str, object]) -> None:
    """
    Elite V3.5: Arq-based batch processor for automated chat transcript distillation.
    Extracts Q&A candidate structures from recent conversations.
    """
    logger.info("🧠 [Self-Learning Job] Commencing chat transcript distillation sequence...")
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        try:
            from backend.services.commerce.self_learning import helen_self_learning
            stats = await helen_self_learning.run_auto_learning(db, limit_sessions=50)
            logger.info(f"🧠 [Self-Learning Job] Finished thưa sếp: Scanned={stats.get('scanned')}, Synthesized={stats.get('synthesized')}, Persisted={stats.get('persisted_to_sandbox')}")
        except Exception as e:
            logger.error(f"🧠 [Self-Learning Job] Distillation process failed: {e}")
            await db.rollback()

async def generate_review_kg_job(ctx: Dict[str, object], review_id: str) -> None:
    """
    Elite V2.2: Asynchronous Knowledge Graph Generation.
    Offloads heavy LLM entity extraction from HTTP transaction to background worker.
    """
    from backend.database.alchemy_config import alchemy_config
    from backend.database.models.system import SystemReview
    from backend.services.xohi.creative_studio.operatives.kg_generator import generate_knowledge_graph
    from sqlalchemy.orm.attributes import flag_modified
    
    logger.info(f"🧬 [Review KG Job] Starting entity extraction for review {review_id} in background.")
    
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        try:
            review = await db.get(SystemReview, review_id)
            if not review:
                logger.warning(f"🧬 [Review KG Job] Review {review_id} not found.")
                return
                
            # Call LLM externally without holding active HTTP transactions
            kg_data = await generate_knowledge_graph(
                content=review.content,
                topic=f"Đánh giá từ {review.customer_name} cho {review.entity_type} {review.entity_id}"
            )
            
            # Explicit update in separate transaction
            if not review.attributes:
                review.attributes = {}
            review.attributes["knowledge_graph"] = kg_data
            flag_modified(review, "attributes")
            
            await db.commit()
            logger.info(f"🧬 [Review KG Job] Successfully generated and stored Knowledge Graph for review {review_id}.")
        except Exception as e:
            logger.error(f"🧬 [Review KG Job] Failed to generate Knowledge Graph: {e}")
            await db.rollback()


async def cleanup_old_notifications(ctx: Dict[str, object]) -> None:
    """
    Elite V2.2: Retention Policy Enforcement for Notifications.
    1. Loads configuration from Redis cache (fallback to system_settings / default: 7 days soft delete, 14 days hard delete).
    2. Performs soft delete for notifications older than soft_delete_days.
    3. Performs hard delete for soft-deleted notifications older than hard_delete_days in chunks of 5000.
    """
    logger.info("[Cleanup Notifications] Starting execution...")
    
    from backend.database.models.system import SystemSetting, Notification
    
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        try:
            soft_days = 7
            hard_days = 14
            
            try:
                from backend.services.xohi_memory import xohi_memory
                import json
                cached = await xohi_memory.client.get("system:notification_retention")
                if cached:
                    config = json.loads(cached)
                    soft_days = int(config.get("soft_delete_days", 7))
                    hard_days = int(config.get("hard_delete_days", 14))
                    logger.info("[Cleanup Notifications] Loaded retention policy from Redis cache.")
                else:
                    stmt = select(SystemSetting).where(SystemSetting.key == "notification_retention")
                    setting = (await db.execute(stmt)).scalar_one_or_none()
                    if setting and isinstance(setting.value, dict):
                        soft_days = int(setting.value.get("soft_delete_days", 7))
                        hard_days = int(setting.value.get("hard_delete_days", 14))
                        await xohi_memory.client.set("system:notification_retention", json.dumps(setting.value))
            except Exception as e:
                logger.warning(f"[Cleanup Notifications] Failed to read settings from Redis, falling back to DB/Defaults: {e}")
                from sqlalchemy import select
                stmt = select(SystemSetting).where(SystemSetting.key == "notification_retention")
                setting = (await db.execute(stmt)).scalar_one_or_none()
                if setting and isinstance(setting.value, dict):
                    soft_days = int(setting.value.get("soft_delete_days", 7))
                    hard_days = int(setting.value.get("hard_delete_days", 14))
                
            logger.info(f"[Cleanup Notifications] Retention configuration: soft={soft_days} days, hard={hard_days} days.")
            
            now = datetime.now(timezone.utc)
            soft_cutoff = now - timedelta(days=soft_days)
            hard_cutoff = now - timedelta(days=hard_days)
            
            # Step 1: Soft Delete (Set deleted_at for active notifications older than soft_cutoff)
            soft_stmt = (
                update(Notification)
                .where(Notification.deleted_at == None)
                .where(Notification.created_at < soft_cutoff)
                .values(deleted_at=now)
            )
            soft_res = await db.execute(soft_stmt)
            await db.commit()
            
            # Step 2: Hard Delete (Purge soft-deleted notifications older than hard_cutoff in chunks to release locks)
            from sqlalchemy import select
            total_hard_deleted = 0
            while True:
                subq = (
                    select(Notification.id)
                    .where(Notification.deleted_at != None)
                    .where(Notification.deleted_at < hard_cutoff)
                    .limit(5000)
                    .scalar_subquery()
                )
                hard_stmt = delete(Notification).where(Notification.id.in_(subq))
                hard_res = await db.execute(hard_stmt)
                count = hard_res.rowcount
                total_hard_deleted += count
                await db.commit()
                if count < 5000:
                    break
            
            logger.info(
                f"[Cleanup Notifications] Process completed. "
                f"Soft-deleted: {soft_res.rowcount} notifications. "
                f"Hard-deleted: {total_hard_deleted} notifications."
            )
        except Exception as e:
            logger.error(f"[Cleanup Notifications] Failed during cleanup execution: {e}")
            await db.rollback()


async def expire_loyalty_points_job(ctx: Dict[str, object]) -> None:
    """
    Elite V2.2: Daily loyalty points expiration cron job.
    Executes the FIFO-based point expiration routine to prune stale points.
    """
    logger.info("[Loyalty Points Expiration Job] Commencing expiration sequence...")
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        try:
            from backend.services.commerce.loyalty import LoyaltyService
            stats = await LoyaltyService.expire_inactive_points(db)
            logger.info(f"[Loyalty Points Expiration Job] Completed. Stats: {stats}")
        except Exception as e:
            logger.error(f"[Loyalty Points Expiration Job] Execution failed: {e}")
            await db.rollback()


async def seo_nightly_reconciliation_job(ctx: Dict[str, object]) -> None:
    """
    SEO Pillar & Cluster — Nightly Orphan Cleanup.
    Soft-deletes seo_nodes whose core entity (article/product) was deleted.
    Runs at 01:00 AM daily. Can be toggled via system settings 'seo_nightly_reconciliation'.
    """
    logger.info("[SEO Reconcile Job] Starting nightly orphan cleanup...")
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        try:
            from backend.services.seo_graph_service import seo_graph_service
            result = await seo_graph_service.reconcile_orphan_nodes(db)
            await db.commit()
            logger.info(f"[SEO Reconcile Job] Done. Cleaned: {result['orphans_cleaned']} orphan node(s).")
        except Exception as e:
            logger.error(f"[SEO Reconcile Job] Failed: {e}", exc_info=True)
            await db.rollback()


async def seo_match_entity_job(
    ctx: Dict[str, object],
    entity_type: str,
    entity_id: str,
    title: str,
    excerpt: str,
    slug: str,
    tenant_id: str,
) -> None:
    """
    SEO Pillar & Cluster — On-Demand AI Matching (event-driven).
    Triggered by Event Bus when article/product is published.
    """
    logger.info(f"[SEO Match Job] Matching {entity_type}:{entity_id} tenant={tenant_id}")
    from backend.database import current_tenant_id
    token = current_tenant_id.set(tenant_id)
    session_maker = alchemy_config.create_session_maker()
    try:
        async with session_maker() as db:
            from backend.services.seo_matching_service import seo_matching_service
            result = await seo_matching_service.match_entity(
                db=db,
                entity_type=entity_type,
                entity_id=entity_id,
                title=title,
                content_excerpt=excerpt,
                slug=slug,
            )
            await db.commit()
            logger.info(f"[SEO Match Job] {entity_id}: tier={result.match_tier}, conf={result.ai_confidence}")
    except Exception as e:
        logger.error(f"[SEO Match Job] Failed for {entity_id}: {e}", exc_info=True)
        raise
    finally:
        current_tenant_id.reset(token)


async def seo_bulk_match_job(ctx: Dict[str, object], tenant_id: str) -> None:
    """
    SEO Pillar & Cluster — Bulk AI Matching (Background Job).
    Triggered by admin via HTTP endpoint to avoid gateway timeouts.
    """
    logger.info(f"[SEO Bulk Match Job] Starting background bulk matching for tenant={tenant_id}")
    from backend.database import current_tenant_id
    token = current_tenant_id.set(tenant_id)
    session_maker = alchemy_config.create_session_maker()
    try:
        async with session_maker() as db:
            from backend.services.seo_matching_service import seo_matching_service
            from backend.services.ai_engine.core.key_rotator import key_rotator
            await key_rotator.load_keys()
            result = await seo_matching_service.bulk_match_unclassified(db)
            logger.info(f"[SEO Bulk Match Job] Finished successfully: {result}")
    except Exception as e:
        logger.error(f"[SEO Bulk Match Job] Failed: {e}", exc_info=True)
        raise
    finally:
        current_tenant_id.reset(token)


async def seo_unmatch_entity_job(
    ctx: Dict[str, object],
    entity_type: str,
    entity_id: str,
    tenant_id: str,
) -> None:
    """
    SEO Pillar & Cluster — On-Demand SEO Node/Edges Deletion (event-driven).
    Triggered by Event Bus when article/product is set to draft or deleted.
    """
    logger.info(f"[SEO Unmatch Job] Unmatching/deleting {entity_type}:{entity_id} tenant={tenant_id}")
    from backend.database import current_tenant_id
    token = current_tenant_id.set(tenant_id)
    session_maker = alchemy_config.create_session_maker()
    try:
        async with session_maker() as db:
            from backend.services.seo_graph_service import seo_graph_service
            await seo_graph_service.soft_delete_node_by_entity(
                db=db,
                entity_type=entity_type,
                entity_id=entity_id,
            )
            await db.commit()
            logger.info(f"[SEO Unmatch Job] Done for {entity_type}:{entity_id}")
    except Exception as e:
        logger.error(f"[SEO Unmatch Job] Failed for {entity_id}: {e}", exc_info=True)
        raise
    finally:
        current_tenant_id.reset(token)


async def seo_contextual_link_job(
    ctx: Dict[str, object],
    article_id: str,
    tenant_id: str,
) -> None:
    """
    SGE Entity-Contextual Linking — AI Link Injection Analysis (event-driven).
    Triggered automatically after seo_match_entity_job completes for articles.
    Analyzes article content and generates contextual link suggestions.
    """
    logger.info(f"[SEO Contextual Link Job] Analyzing article {article_id} tenant={tenant_id}")
    from backend.database import current_tenant_id
    token = current_tenant_id.set(tenant_id)
    session_maker = alchemy_config.create_session_maker()
    try:
        async with session_maker() as db:
            from backend.database.models.content import Article
            from backend.services.seo_contextual_linker import seo_contextual_linker
            from sqlalchemy import select, func

            article = await db.scalar(
                select(Article).where(
                    Article.id == article_id,
                    Article.status == "PUBLISHED",
                    Article.deleted_at.is_(None),
                )
            )
            if not article or not article.content:
                logger.info(f"[SEO Contextual Link Job] Article {article_id} not found or empty — skipping")
                return

            # Tiêu chuẩn 1: Loại bỏ bài viết quá ngắn (< 250 từ) để giữ chất lượng bài viết tốt nhất
            words_count = len(article.content.split())
            if words_count < 250:
                logger.info(f"[SEO Contextual Link Job] Skipping article {article_id} because it is too short ({words_count} words)")
                return

            # Tiêu chuẩn 2: Loại bỏ bài viết đã có tối đa 3 link APPROVED hoặc APPLIED (đã đạt giới hạn SEO)
            from backend.database.models.seo import SeoContextualLink
            # [P1-FIX] Dùng COUNT(*) scalar thay vì load toàn bộ ORM objects chỉ để đếm số dòng
            # Tránh slow query do ORM hydration không cần thiết
            total_links_count = await db.scalar(
                select(func.count()).select_from(SeoContextualLink).where(
                    SeoContextualLink.source_article_id == article_id,
                    SeoContextualLink.status.in_(["approved", "applied"]),
                    SeoContextualLink.tenant_id == tenant_id
                )
            ) or 0
            if total_links_count >= 3:
                logger.info(f"[SEO Contextual Link Job] Skipping article {article_id} because it has reached the max contextual links limit ({total_links_count} links)")
                return

            count = await seo_contextual_linker.analyze_article(
                db=db,
                article_id=article_id,
                article_content=article.content,
                article_title=article.title,
            )
            await db.commit()
            logger.info(f"[SEO Contextual Link Job] Done for {article_id}: {count} suggestions created")
    except Exception as e:
        logger.error(f"[SEO Contextual Link Job] Failed for {article_id}: {e}", exc_info=True)
        raise
    finally:
        current_tenant_id.reset(token)


async def seo_pillar_auto_link_job(
    ctx: Dict[str, object],
    pillar_id: str,
    tenant_id: str,
) -> None:
    """
    Tự động đi link từ các Cluster con trỏ về Pillar node hiện tại.
    1. Tìm tất cả các Cluster con liên kết với Pillar node này (SeoEdge có source == pillar_id).
    2. Lọc ra các Cluster có entity_type == 'ARTICLE'.
    3. Với mỗi article_id:
       - Chạy quét phân tích link: seo_contextual_linker.analyze_article()
       - Lọc các đề xuất 'pending' trỏ về pillar này có ai_confidence >= 0.85.
       - Chỉ chọn đề xuất có confidence cao nhất để tự động duyệt (approved).
       - Chèn link tự động vào bài viết: seo_contextual_linker.apply_approved_links().
    """
    logger.info(f"[Pillar Auto Link] Starting auto linking job for pillar {pillar_id} tenant={tenant_id}")
    from backend.database import current_tenant_id
    token = current_tenant_id.set(tenant_id)
    session_maker = alchemy_config.create_session_maker()
    try:
        async with session_maker() as db:
            from backend.database.models.seo import SeoNode, SeoEdge, SeoContextualLink, SeoContextualLinkStatus
            from backend.database.models.content import Article
            from backend.services.seo_contextual_linker import seo_contextual_linker
            from sqlalchemy import select, func

            # Lấy thông tin Pillar Node
            pillar = await db.scalar(
                select(SeoNode).where(
                    SeoNode.id == pillar_id,
                    SeoNode.tenant_id == tenant_id,
                    SeoNode.deleted_at.is_(None)
                )
            )
            pillar_label = pillar.node_label if pillar else pillar_id

            # 1. Tìm tất cả các Cluster con liên kết với Pillar này (source_node_id == pillar_id)
            edges = (await db.execute(
                select(SeoEdge.target_node_id).where(
                    SeoEdge.source_node_id == pillar_id,
                    SeoEdge.tenant_id == tenant_id
                )
            )).scalars().all()

            if not edges:
                logger.info(f"[Pillar Auto Link] No clusters found for pillar {pillar_id}")
                return

            # 2. Lọc các nodes có entity_type là ARTICLE
            nodes = (await db.execute(
                select(SeoNode.entity_id).where(
                    SeoNode.id.in_(edges),
                    SeoNode.entity_type == "ARTICLE",
                    SeoNode.tenant_id == tenant_id,
                    SeoNode.deleted_at.is_(None)
                )
            )).scalars().all()

            article_ids = list(set(nodes))
            if not article_ids:
                logger.info(f"[Pillar Auto Link] No article clusters found for pillar {pillar_id}")
                return

            logger.info(f"[Pillar Auto Link] Found {len(article_ids)} articles to scan for pillar {pillar_id}")

            total_suggestions = 0
            for article_id in article_ids:
                try:
                    article = await db.scalar(
                        select(Article).where(
                            Article.id == article_id,
                            Article.status == "PUBLISHED",
                            Article.deleted_at.is_(None),
                        )
                    )
                    if not article or not article.content:
                        continue

                    # Tiêu chuẩn 1: Loại bỏ bài viết quá ngắn (< 250 từ) để tránh spam, giữ chất lượng cao nhất
                    words_count = len(article.content.split())
                    if words_count < 250:
                        logger.info(f"[Pillar Auto Link] Skipping article {article_id} because it is too short ({words_count} words)")
                        continue

                    # Tiêu chuẩn 2: Loại bỏ bài viết đã có link APPROVED hoặc APPLIED trỏ tới Pillar đích này rồi (tránh double link)
                    existing_link = await db.scalar(
                        select(SeoContextualLink).where(
                            SeoContextualLink.source_article_id == article_id,
                            SeoContextualLink.target_node_id == pillar_id,
                            SeoContextualLink.status.in_(["approved", "applied"]),
                            SeoContextualLink.tenant_id == tenant_id
                        )
                    )
                    if existing_link:
                        logger.info(f"[Pillar Auto Link] Skipping article {article_id} because it already has an approved/applied link to pillar {pillar_id}")
                        continue

                    # Tiêu chuẩn 3: Loại bỏ bài viết đã đạt giới hạn tối đa số link ngữ cảnh cho phép (tối đa 3 link/bài)
                    # [P1-FIX] Dùng COUNT(*) scalar thay vì load toàn bộ ORM objects chỉ để đếm số dòng
                    total_links_count = await db.scalar(
                        select(func.count()).select_from(SeoContextualLink).where(
                            SeoContextualLink.source_article_id == article_id,
                            SeoContextualLink.status.in_(["approved", "applied"]),
                            SeoContextualLink.tenant_id == tenant_id
                        )
                    ) or 0
                    if total_links_count >= 3:
                        logger.info(f"[Pillar Auto Link] Skipping article {article_id} because it has reached the max contextual links limit ({total_links_count} links)")
                        continue

                    # Quét tìm đề xuất mới cho bài viết
                    count = await seo_contextual_linker.analyze_article(
                        db=db,
                        article_id=article_id,
                        article_content=article.content,
                        article_title=article.title,
                        target_pillar_id=pillar_id,
                    )
                    total_suggestions += count
                    await db.commit()
                    logger.info(f"[Pillar Auto Link] Scanned article {article_id} for pillar {pillar_id}. Saved {count} suggestions to DB.")
                except Exception as art_ex:
                    logger.error(f"[Pillar Auto Link] Error processing article {article_id}: {art_ex}", exc_info=True)
                    await db.rollback()

            logger.info(f"[Pillar Auto Link] Completed auto linking job for pillar {pillar_id}. Total suggestions: {total_suggestions}")

            # Gửi thông báo đến hình chuông (Notification Center)
            try:
                from backend.services.signal_center import signal_center
                from backend.schemas.signal import SignalSchema, SignalSeverity

                msg = f"🧬 AI hoàn tất quét Pillar: {pillar_label}. Đã quét {len(article_ids)} bài viết Cluster, tìm thấy {total_suggestions} đề xuất link SGE chờ duyệt."
                signal = SignalSchema(
                    signal_type="SEO_AUTO_LINK_COMPLETED",
                    message=msg,
                    severity=SignalSeverity.ACTION,  # ACTION sẽ nổi chuông đỏ/vàng kèm tiếng bip & hiển thị ở chuông
                    payload={"pillar_id": pillar_id, "suggestions_count": total_suggestions},
                    persist=True
                )
                await signal_center.dispatch(
                    user_id="user_admin",
                    signal=signal,
                    tenant_id=tenant_id
                )
            except Exception as notif_ex:
                logger.error(f"[Pillar Auto Link] Failed to send completion notification to bell: {notif_ex}", exc_info=True)

    except Exception as e:
        logger.error(f"[Pillar Auto Link] Failed execution for pillar {pillar_id}: {e}", exc_info=True)
    finally:
        current_tenant_id.reset(token)


async def generate_article_embed_and_kg_job(
    ctx: Dict[str, object],
    article_id: str,
    title: str,
    content: str,
    tenant_id: str,
) -> None:
    """
    Elite V2.2: Asynchronous Article Embedding and Knowledge Graph Generation.
    Offloads heavy fastembed/LLM operations from API container to background worker.
    """
    import asyncio as _asyncio
    import gc
    import ctypes
    from backend.database.alchemy_config import alchemy_config
    from backend.database import current_tenant_id as _ctx_tenant
    from backend.services.article_vector_service import article_vector_service
    from backend.database.models.content import Article
    
    logger.info(f"🧬 [Article Embed & KG Job] Starting for article {article_id} in background.")
    
    _token = _ctx_tenant.set(tenant_id)
    try:
        # Phase 1: Embedding
        try:
            await article_vector_service.upsert_article_embedding(
                db_session=None,
                article_id=article_id,
                title=title,
                content=content
            )
            logger.info(f"[Background Worker] Embedding completed for article {article_id}")
        except Exception as e:
            logger.error(f"[Background Worker] Embedding failed for {article_id}: {e}")

        # Phase 2: Knowledge Graph
        try:
            from backend.services.xohi.creative_studio.operatives.kg_generator import generate_knowledge_graph
            from sqlalchemy.orm.attributes import flag_modified
            from sqlalchemy import select
            
            async with _asyncio.timeout(25):
                kg_data = await generate_knowledge_graph(content=content, topic=title)
            
            async with alchemy_config.create_session_maker()() as kg_session:
                res = await kg_session.execute(select(Article).where(Article.id == article_id))
                article = res.scalar_one_or_none()
                if article:
                    if not article.article_metadata:
                        article.article_metadata = {}
                    article.article_metadata["knowledge_graph"] = kg_data
                    flag_modified(article, "article_metadata")
                    await kg_session.commit()
            logger.info(f"[Background Worker] KG completed for article {article_id}")
        except _asyncio.TimeoutError:
            logger.error(f"[Background Worker] KG timed out (>25s) for {article_id}")
        except Exception as e:
            logger.error(f"[Background Worker] KG failed for {article_id}: {e}")

        # Phase 3: Release model from memory
        from backend.services.ai_engine.core.encoder_singleton import release_shared_encoder
        release_shared_encoder()
        gc.collect(generation=2)
        try:
            ctypes.CDLL("libc.so.6").malloc_trim(0)
        except Exception:
            pass
    finally:
        _ctx_tenant.reset(_token)


