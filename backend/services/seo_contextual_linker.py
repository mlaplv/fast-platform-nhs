"""
SEO Contextual Linker — SGE Entity-Contextual Link Injection
=============================================================
Phân tích bài viết Cluster, tìm các câu chứa entity liên quan đến Pillar,
và gợi ý chèn link ngữ cảnh (<a> tag) vào đúng cụm từ mang ngữ nghĩa thực thể.

Pipeline 3 bước:
  1. Sentence Split (Pure Python — ZERO AI cost)
  2. Entity Pre-filter (Substring match — ZERO AI cost)
  3. PydanticAI Batch Analysis (Chi phí AI chỉ cho candidates)

Design:
- Chạy tự động sau SeoMatchingService via Event Bus
- Kết quả lưu vào seo_contextual_links (status=pending)
- Admin review trên Dashboard trước khi apply vào article.content
"""
import asyncio
import hashlib
import logging
import re
import string
from html.parser import HTMLParser
from typing import Optional, Literal

from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.seo import (
    SeoNode, SeoContextualLink, SeoContextualLinkStatus,
)
from backend.database import current_tenant_id
from backend.utils.uid import new_id_default

logger = logging.getLogger("api-gateway")

_BATCH_SIZE = 5                # Số câu gửi AI mỗi lần
_MIN_CONFIDENCE = 0.85         # Nâng lên 0.85 để giảm noise — chỉ giữ gợi ý chất lượng cao
_MAX_LINKS_PER_PILLAR = 1     # Giới hạn 1 link cho mỗi Pillar trỏ về để tránh nhồi nhét
_MAX_LINKS_PER_ARTICLE = 2    # Giảm xuống 2 cho mật độ an toàn hơn, tránh link spam
_MAX_TOTAL_LINKS_IN_ARTICLE = 4  # Cluster đã có >= 4 link nội bộ → KHÔNG thêm nữa
_AI_TIMEOUT = 60.0


# ─── PydanticAI V2 Output Schemas ────────────────────────────────────────────

class SentenceLinkSuggestion(BaseModel):
    """Output schema cho từng câu được AI phân tích."""
    sentence_index: int = Field(ge=0, description="Vị trí câu trong batch candidates")
    should_link: bool = Field(description="AI có nên chèn link không?")
    original_sentence: str = Field(description="Câu gốc (echoed back để validate)")
    anchor_text: str = Field(max_length=200, description="Cụm từ ngữ cảnh được chọn làm anchor")
    linked_sentence: str = Field(description="Câu hoàn chỉnh với <a> tag đã chèn")
    target_pillar_id: str = Field(description="ID của Pillar Node đích")
    matched_entity_type: Literal["pain_point", "feature", "brand", "ingredient", "symptom"] = Field(description="pain_point | feature | brand | ingredient | symptom")
    matched_entity_name: str = Field(description="Tên entity cụ thể đã match")
    confidence: float = Field(ge=0.0, le=1.0, description="Độ tin cậy")
    reasoning: str = Field(description="Lý do chọn anchor phrase này — phải hợp ngữ cảnh câu văn")


class ContextualLinkBatchResult(BaseModel):
    """Output schema cho batch response."""
    suggestions: list[SentenceLinkSuggestion]
    skipped_indices: list[int] = Field(default_factory=list, description="Index các câu AI quyết định không link")


class SeoSafeTextExtractor(HTMLParser):
    """
    Parser an toàn trích xuất văn bản từ HTML.
    Tuyệt đối bỏ qua các thẻ tiêu đề (h1-h6), link hiện có (a), bảng (table),
    code (code, pre), blockquote, figcaption, script, style, button...
    Để tránh chèn link đè lên nhau hoặc chèn vào tiêu đề vi phạm quy tắc SEO/SGE.
    Đồng thời tự động gộp các thẻ inline styling (strong, em, span, b, i) để tránh câu bị ngắt đoạn.
    """
    def __init__(self):
        super().__init__()
        self.ignored_tags = {
            "h1", "h2", "h3", "h4", "h5", "h6", "a", "button", 
            "script", "style", "code", "pre", "blockquote", "figcaption", 
            "table", "thead", "tfoot", "tr", "th"
        }
        self.block_tags = {
            "p", "div", "li", "ul", "ol", "br", "hr", "section", "article", "aside"
        }
        self.current_path = []
        self.text_fragments = []
        self.current_buffer = []

    def flush_buffer(self):
        if self.current_buffer:
            text = " ".join(self.current_buffer).strip()
            # Chuẩn hóa khoảng trắng
            text = re.sub(r'\s+', ' ', text)
            if text:
                self.text_fragments.append(text)
            self.current_buffer = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        self.current_path.append(tag_lower)
        if tag_lower in self.ignored_tags or tag_lower in self.block_tags:
            self.flush_buffer()

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.ignored_tags or tag_lower in self.block_tags:
            self.flush_buffer()
            
        if self.current_path and self.current_path[-1] == tag_lower:
            self.current_path.pop()
        elif tag_lower in self.current_path:
            self.current_path.remove(tag_lower)

    def handle_data(self, data):
        # Nếu đang nằm trong bất kỳ tag nào bị ignored, bỏ qua
        if any(tag in self.ignored_tags for tag in self.current_path):
            return
        
        self.current_buffer.append(data)

    def close(self):
        self.flush_buffer()
        super().close()


# ─── Service ──────────────────────────────────────────────────────────────────

class SeoContextualLinker:
    """
    Orchestrates the 3-step contextual linking pipeline:
    Sentence Split → Entity Pre-filter → PydanticAI Batch → Validation → Persist.
    """

    @staticmethod
    def _count_existing_links(html_content: str) -> int:
        """Đếm số lượng link (<a> tag) đã có trong nội dung bài viết Cluster."""
        return len(re.findall(r'<a\s', html_content, re.IGNORECASE))

    # ─── Public Entry Point ──────────────────────────────────────────────────

    async def analyze_article(
        self,
        db: AsyncSession,
        article_id: str,
        article_content: str,
        article_title: str,
        target_pillar_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> int | list[dict]:
        """
        Main pipeline. Chạy sau khi SeoMatchingService hoàn tất.
        Returns: số lượng suggestions đã persist (nếu không phải dry_run) hoặc danh sách đề xuất (nếu dry_run).
        """
        import os
        is_dry_run = dry_run or os.getenv("SEO_LINKER_DRY_RUN", "false").lower() == "true"
        tenant = current_tenant_id.get() or "default"
        content_hash = hashlib.md5(article_content.encode()).hexdigest()

        if not is_dry_run:
            # Clear previous pending/rejected suggestions for this article immediately to prevent stale data
            stmt = delete(SeoContextualLink).where(
                SeoContextualLink.source_article_id == article_id,
                SeoContextualLink.tenant_id == tenant,
                SeoContextualLink.status.in_([
                    SeoContextualLinkStatus.PENDING,
                    SeoContextualLinkStatus.REJECTED
                ]),
            )
            if target_pillar_id:
                stmt = stmt.where(SeoContextualLink.target_node_id == target_pillar_id)
            await db.execute(stmt)
            await db.commit()
            logger.info("[ContextualLinker] Cleared previous pending/rejected suggestions for article %s (pillar: %s)", article_id, target_pillar_id)

        # Load user configured brand keywords, generic exclusions, and intent keywords from System Settings
        brand_keywords_config = None
        generic_exclusions_config = None
        intent_keywords_config = None
        try:
            from backend.services.settings_service import settings_service
            settings_res = await settings_service.get_general_settings(db)
            if settings_res and settings_res.settings and hasattr(settings_res.settings, "seo_contextual_links"):
                seo_settings = settings_res.settings.seo_contextual_links
                if seo_settings.brand_keywords:
                    brand_keywords_config = [w.lower().strip() for w in seo_settings.brand_keywords if w.strip()]
                if seo_settings.generic_exclusions:
                    generic_exclusions_config = {w.lower().strip() for w in seo_settings.generic_exclusions if w.strip()}
                if hasattr(seo_settings, "intent_keywords") and seo_settings.intent_keywords:
                    intent_keywords_config = [w.lower().strip() for w in seo_settings.intent_keywords if w.strip()]
        except Exception as e:
            logger.warning("[ContextualLinker] Failed to load system settings for contextual linking: %s", e)

        # Step 0: Load Pillar nodes with their entities
        pillars = await self._load_pillars_with_entities(db, tenant)
        if not pillars:
            logger.info("[ContextualLinker] No pillars found — skipping")
            return [] if is_dry_run else 0

        if target_pillar_id:
            pillars = [p for p in pillars if p["id"] == target_pillar_id]
            if not pillars:
                logger.info(f"[ContextualLinker] Target pillar {target_pillar_id} not found — skipping")
                return [] if is_dry_run else 0

        # Lọc bỏ các pillars đã có sẵn link trỏ đến trong article_content để tránh Double Link (Google Link Spam Penalty)
        active_pillars = []
        for p in pillars:
            slug = p.get("slug")
            url = p.get("url")
            already_linked = False
            
            if slug:
                escaped_slug = re.escape(slug)
                # Tìm thẻ <a> có href chứa /slug hoặc /slug.html
                pattern = rf'href=["\'](?:https?://[^"\']*)?/{escaped_slug}(?:\.html)?(?:[?#][^"\']*)?["\']'
                if re.search(pattern, article_content):
                    already_linked = True
            
            if not already_linked and url:
                escaped_url = re.escape(url)
                pattern = rf'href=["\'](?:https?://[^"\']*)?{escaped_url}(?:[?#][^"\']*)?["\']'
                if re.search(pattern, article_content):
                    already_linked = True
                    
            if not already_linked:
                active_pillars.append(p)
            else:
                logger.info("[ContextualLinker] Skipping pillar %s for article %s because it is already linked in the content.", p['label'], article_id)
        
        pillars = active_pillars
        if not pillars:
            logger.info("[ContextualLinker] All pillars are already linked in this article — skipping")
            return [] if is_dry_run else 0

        # Step 0c: Topical relevance gate — chỉ giữ Pillar có topic cốt lõi xuất hiện trong bài viết
        content_lower = article_content.lower()
        topically_relevant = []
        for p in pillars:
            topic = (p.get("pillar_topic") or "").lower().strip()
            if topic:
                # Tất cả từ khóa của topic phải xuất hiện trong bài viết
                topic_words = [w for w in topic.split() if len(w) >= 2]
                if topic_words and all(w in content_lower for w in topic_words):
                    topically_relevant.append(p)
                    continue
            # Fallback: kiểm tra entities_json có entity nào >= 6 ký tự xuất hiện trong bài không
            entities = p.get("entities", [])
            has_relevant_entity = any(
                (ent.get("name") or "").lower().strip() in content_lower
                for ent in entities
                if len((ent.get("name") or "").strip()) >= 6
            )
            if has_relevant_entity:
                topically_relevant.append(p)
            else:
                logger.debug(
                    "[ContextualLinker] Pillar '%s' not topically relevant to article %s — skipped",
                    p['label'], article_id,
                )

        pillars = topically_relevant
        if not pillars:
            logger.info("[ContextualLinker] No topically relevant pillars for article %s — skipping", article_id)
            return [] if is_dry_run else 0

        # Step 0d: Link density gate — Cluster đã có đủ link nội bộ → không thêm nữa
        existing_link_count = self._count_existing_links(article_content)
        available_slots = _MAX_TOTAL_LINKS_IN_ARTICLE - existing_link_count
        if available_slots <= 0:
            logger.info(
                "[ContextualLinker] Article %s already has %d internal links (max %d) — skipping",
                article_id, existing_link_count, _MAX_TOTAL_LINKS_IN_ARTICLE,
            )
            return [] if is_dry_run else 0

        # Điều chỉnh số link tối đa cho bài viết này dựa trên slots còn trống
        effective_max = min(_MAX_LINKS_PER_ARTICLE, available_slots)
        logger.info(
            "[ContextualLinker] Article %s: %d existing links, %d slots available, effective max = %d",
            article_id, existing_link_count, available_slots, effective_max,
        )

        # Step 0b: Load article's own entities from seo_nodes
        article_node = await db.scalar(
            select(SeoNode).where(
                SeoNode.entity_id == article_id,
                SeoNode.entity_type == "ARTICLE",
                SeoNode.tenant_id == tenant,
                SeoNode.deleted_at.is_(None),
            )
        )

        # Step 1: Sentence splitting
        sentences = self._split_sentences(article_content)
        if not sentences:
            logger.info("[ContextualLinker] No sentences found — skipping")
            return [] if is_dry_run else 0

        # Step 2: Entity pre-filter
        candidates = self._entity_prefilter(
            sentences, 
            pillars, 
            article_node, 
            stop_words_config=generic_exclusions_config,
            brand_keywords_config=brand_keywords_config
        )
        if not candidates:
            logger.info("[ContextualLinker] No candidate sentences after pre-filter — skipping")
            return [] if is_dry_run else 0

        logger.info(
            "[ContextualLinker] %d/%d sentences passed pre-filter for article %s",
            len(candidates), len(sentences), article_id
        )

        # Close the active database session before starting heavy AI/network tasks
        try:
            await db.commit()
            await db.close()
            logger.info(f"[ContextualLinker] Released active DB connection to pool before AI calls for article {article_id}.")
        except Exception as db_err:
            logger.warning(f"[ContextualLinker] Failed to release DB connection: {db_err}")

        # Step 3: PydanticAI batch analysis
        all_suggestions: list[SentenceLinkSuggestion] = []
        for i in range(0, len(candidates), _BATCH_SIZE):
            batch = candidates[i:i + _BATCH_SIZE]
            try:
                batch_result = await self._ai_analyze_batch(
                    batch, 
                    pillars,
                    brand_keywords_config=brand_keywords_config
                )
                if batch_result:
                    all_suggestions.extend(batch_result.suggestions)
            except Exception as e:
                logger.warning("[ContextualLinker] AI batch %d failed: %s", i // _BATCH_SIZE, e)

        if not all_suggestions:
            logger.info("[ContextualLinker] AI returned 0 suggestions for article %s", article_id)
            return [] if is_dry_run else 0

        # Step 4: Validate + Persist
        valid_pillar_ids = {p["id"] for p in pillars}

        # Normalize entity type for all suggestions to prevent misclassification
        for suggestion in all_suggestions:
            pid = suggestion.target_pillar_id
            pillar_label = ""
            for p in pillars:
                if p["id"] == pid:
                    pillar_label = p.get("label") or ""
                    break
            suggestion.matched_entity_type = self._normalize_entity_type(
                suggestion.matched_entity_type,
                suggestion.matched_entity_name,
                pillar_label,
                brand_keywords_config=brand_keywords_config
            )

        # Apply Brand-Relevance Multiplier and Keyword Affinity Filter
        for suggestion in all_suggestions:
            multiplier = self._calculate_brand_relevance_multiplier(
                suggestion,
                pillars,
                brand_keywords_config=brand_keywords_config,
                generic_exclusions_config=generic_exclusions_config
            )
            original_conf = suggestion.confidence
            suggestion.confidence = round(suggestion.confidence * multiplier, 4)
            if multiplier < 1.0:
                logger.info(
                    "[ContextualLinker] Penalized confidence for anchor '%s' (type: %s): %.2f -> %.2f (multiplier: %.2f)",
                    suggestion.anchor_text,
                    suggestion.matched_entity_type,
                    original_conf,
                    suggestion.confidence,
                    multiplier
                )

        persisted = 0
        dry_run_results = []

        if is_dry_run:
            # Track links per pillar for density constraint
            pillar_link_count: dict[str, int] = {}
            for suggestion in all_suggestions:
                if not suggestion.should_link:
                    continue
                errors = self._validate_suggestion(suggestion, valid_pillar_ids)
                if errors:
                    continue
                if suggestion.confidence < _MIN_CONFIDENCE:
                    continue
                eas_score = self._calculate_eas(suggestion, pillars, article_content, brand_keywords_config=brand_keywords_config, generic_exclusions_config=generic_exclusions_config, intent_keywords_config=intent_keywords_config)
                if eas_score < 0.6:
                    logger.info("[ContextualLinker] Suggestion '%s' filtered out due to low EAS score: %.2f", suggestion.anchor_text, eas_score)
                    continue
                if persisted >= effective_max:
                    break
                pid = suggestion.target_pillar_id
                count = pillar_link_count.get(pid, 0)
                if count >= _MAX_LINKS_PER_PILLAR:
                    continue
                pillar_link_count[pid] = count + 1

                target_url = ""
                for p in pillars:
                    if p["id"] == pid:
                        entity_type = p.get("entity_type", "ARTICLE")
                        slug = p.get("slug", "")
                        if entity_type == "PRODUCT":
                            url_val = p.get("url") or f"/{slug}"
                            if url_val.endswith(".html"):
                                url_val = url_val[:-5]
                            target_url = url_val
                        else:
                            url_val = p.get("url") or f"/{slug}"
                            if not url_val.endswith(".html"):
                                url_val = f"{url_val}.html"
                            target_url = url_val
                        break

                final_linked = suggestion.linked_sentence
                if pid in final_linked:
                    final_linked = final_linked.replace(pid, target_url)

                dry_run_results.append({
                    "id": new_id_default(),
                    "source_article_id": article_id,
                    "target_node_id": pid,
                    "target_url": target_url,
                    "original_sentence": suggestion.original_sentence,
                    "linked_sentence": final_linked,
                    "anchor_text": suggestion.anchor_text,
                    "matched_entity_type": suggestion.matched_entity_type.value if hasattr(suggestion.matched_entity_type, 'value') else suggestion.matched_entity_type,
                    "matched_entity_name": suggestion.matched_entity_name,
                    "ai_confidence": suggestion.confidence,
                    "ai_reasoning": suggestion.reasoning,
                    "sentence_index": suggestion.sentence_index,
                    "status": "pending",
                    "content_hash": content_hash,
                })
                persisted += 1
            return dry_run_results
        else:
            # Persistent mode: Open a fresh short-lived session just for the write operations
            from backend.database.alchemy_config import alchemy_config
            from sqlalchemy.dialects.postgresql import insert as pg_insert

            session_maker = alchemy_config.create_session_maker()
            async with session_maker() as new_db:
                # Pre-load target_node_ids already APPROVED/APPLIED for this article from DB
                # to enforce strict 1-link-per-pillar-per-article at write time (not just in-memory)
                existing_applied_targets_res = await new_db.execute(
                    select(SeoContextualLink.target_node_id).where(
                        SeoContextualLink.source_article_id == article_id,
                        SeoContextualLink.tenant_id == tenant,
                        SeoContextualLink.status.in_([
                            SeoContextualLinkStatus.APPROVED,
                            SeoContextualLinkStatus.APPLIED
                        ]),
                    ).distinct()
                )
                existing_applied_targets: set[str] = set(existing_applied_targets_res.scalars().all())

                # Track links per pillar for density constraint (in-memory for this run)
                pillar_link_count: dict[str, int] = {}
                for suggestion in all_suggestions:
                    if not suggestion.should_link:
                        continue
                    errors = self._validate_suggestion(suggestion, valid_pillar_ids)
                    if errors:
                        continue
                    if suggestion.confidence < _MIN_CONFIDENCE:
                        continue
                    eas_score = self._calculate_eas(suggestion, pillars, article_content, brand_keywords_config=brand_keywords_config, generic_exclusions_config=generic_exclusions_config, intent_keywords_config=intent_keywords_config)
                    if eas_score < 0.6:
                        logger.info("[ContextualLinker] Suggestion '%s' filtered out due to low EAS score: %.2f", suggestion.anchor_text, eas_score)
                        continue
                    if persisted >= effective_max:
                        break
                    pid = suggestion.target_pillar_id

                    # Anti-spam: skip nếu pillar này đã có link APPLIED/APPROVED trong bài viết (DB check)
                    if pid in existing_applied_targets:
                        logger.info(
                            "[ContextualLinker] Skipping suggestion for pillar %s in article %s — already has approved/applied link (anti-double-link)",
                            pid, article_id,
                        )
                        continue

                    count = pillar_link_count.get(pid, 0)
                    if count >= _MAX_LINKS_PER_PILLAR:
                        continue
                    pillar_link_count[pid] = count + 1

                    target_url = ""
                    for p in pillars:
                        if p["id"] == pid:
                            entity_type = p.get("entity_type", "ARTICLE")
                            slug = p.get("slug", "")
                            if entity_type == "PRODUCT":
                                url_val = p.get("url") or f"/{slug}"
                                if url_val.endswith(".html"):
                                    url_val = url_val[:-5]
                                target_url = url_val
                            else:
                                url_val = p.get("url") or f"/{slug}"
                                if not url_val.endswith(".html"):
                                    url_val = f"{url_val}.html"
                                target_url = url_val
                            break

                    final_linked = suggestion.linked_sentence
                    if pid in final_linked:
                        final_linked = final_linked.replace(pid, target_url)

                    entity_type_val = suggestion.matched_entity_type.value if hasattr(suggestion.matched_entity_type, 'value') else suggestion.matched_entity_type

                    # Use ON CONFLICT DO NOTHING to gracefully skip duplicate sentence+target combinations.
                    # This handles force_scan re-analysis where approved/applied links may already exist
                    # for the same (source_article_id, sentence_index, target_node_id) unique key.
                    stmt = pg_insert(SeoContextualLink.__table__).values(
                        id=new_id_default(),
                        source_article_id=article_id,
                        target_node_id=pid,
                        target_url=target_url,
                        original_sentence=suggestion.original_sentence,
                        linked_sentence=final_linked,
                        anchor_text=suggestion.anchor_text,
                        matched_entity_type=entity_type_val,
                        matched_entity_name=suggestion.matched_entity_name,
                        ai_confidence=suggestion.confidence,
                        ai_reasoning=suggestion.reasoning,
                        sentence_index=suggestion.sentence_index,
                        status=SeoContextualLinkStatus.PENDING,
                        content_hash=content_hash,
                        tenant_id=tenant,
                    ).on_conflict_do_nothing(
                        constraint="uq_seo_ctx_link_sentence_target"
                    )
                    await new_db.execute(stmt)
                    persisted += 1
                await new_db.commit()

        if is_dry_run:
            logger.info(
                "[ContextualLinker] [DRY RUN] Generated %d suggestions for article %s (no DB writes)",
                len(dry_run_results), article_id
            )
            return dry_run_results

        logger.info(
            "[ContextualLinker] Persisted %d/%d suggestions for article %s",
            persisted, len(all_suggestions), article_id
        )
        return persisted

    # ─── Step 1: Sentence Splitting ──────────────────────────────────────────

    def _split_sentences(self, html_content: str) -> list[dict]:
        """
        Trích xuất văn bản từ vùng an toàn (safe zones) thông qua HTMLParser,
        sau đó chia câu để đảm bảo không dính vào các thẻ bị cấm (h1-h6, table, a, pre...).
        """
        extractor = SeoSafeTextExtractor()
        try:
            extractor.feed(html_content)
            extractor.close()
            fragments = extractor.text_fragments
        except Exception as e:
            logger.warning("[ContextualLinker] HTML parsing error: %s. Falling back to regex strip.", e)
            # Fallback thô sơ nếu parse HTML lỗi
            text_strip = re.sub(r'<[^>]+>', ' ', html_content)
            text_strip = re.sub(r'\s+', ' ', text_strip).strip()
            fragments = [text_strip]

        result = []
        sentence_idx = 0
        for frag in fragments:
            # Tách các câu dựa trên dấu chấm, chấm hỏi, chấm than
            raw_sentences = re.split(r'(?<=[.!?])\s+', frag)
            for sent in raw_sentences:
                sent = sent.strip()
                # Skip fragments quá ngắn (< 20 ký tự) hoặc chỉ chứa số
                if len(sent) < 20 or sent.isdigit():
                    continue
                # Bỏ qua các câu kết thúc bằng dấu hai chấm (thường là tiêu đề danh mục hoặc intro list)
                if sent.endswith(":"):
                    continue
                result.append({"index": sentence_idx, "text": sent})
                sentence_idx += 1

        return result

    # ─── Step 2: Entity Pre-filter ───────────────────────────────────────────

    def _entity_prefilter(
        self,
        sentences: list[dict],
        pillars: list[dict],
        article_node: Optional[SeoNode],
        stop_words_config: Optional[set[str]] = None,
        brand_keywords_config: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Filter sentences: chỉ giữ những câu chứa entity trùng với Pillar nào đó.
        Enriches each candidate with matched_pillar_ids.
        """
        if stop_words_config is not None:
            stop_words = stop_words_config
        else:
            from backend.schemas.system_settings import SeoContextualLinksSettings
            defaults = SeoContextualLinksSettings()
            stop_words = {w.lower().strip() for w in defaults.generic_exclusions if w.strip()}

        # Load brand keywords dynamically for prefix stripping
        brand_keywords = brand_keywords_config
        if brand_keywords is None:
            from backend.schemas.system_settings import SeoContextualLinksSettings
            defaults = SeoContextualLinksSettings()
            brand_keywords = [w.lower().strip() for w in defaults.brand_keywords if w.strip()]
        
        # Sort brand keywords by length descending to match longest prefixes first
        sorted_brands = sorted(brand_keywords, key=len, reverse=True)

        # Build entity → pillar_id lookup
        entity_pillar_map: dict[str, list[str]] = {}
        for p in pillars:
            entities = p.get("entities", [])
            for ent in entities:
                name = ent.get("name", "").lower().strip()
                if name and len(name) >= 4:
                    # Check if the name matches or contains any stop word/phrase as a whole word
                    is_excluded = False
                    has_brand = any(brand in name for brand in brand_keywords)
                    if not has_brand:
                        for sw in stop_words:
                            if sw == name:
                                is_excluded = True
                                break
                            if len(sw) >= 3 and re.search(r'\b' + re.escape(sw) + r'\b', name):
                                is_excluded = True
                                break
                    if not is_excluded:
                        if name not in entity_pillar_map:
                            entity_pillar_map[name] = []
                        if p["id"] not in entity_pillar_map[name]:
                            entity_pillar_map[name].append(p["id"])

            # Chỉ dùng pillar_topic + tên sản phẩm cốt lõi (full phrase)
            # CẤM tách bigram/trigram — gây noise match bừa bãi ("rich gold", "gold gel"...)
            label = p.get("label") or ""
            topic = p.get("pillar_topic")
            
            additional_terms: list[str] = []
            if topic:
                additional_terms.append(topic.lower().strip())
            
            # Split by common delimiters and clean weight/volume suffixes
            parts = re.split(r'[-—|/(~]', label)
            core = parts[0].strip()
            core_cleaned = re.sub(r'\s*\d+(?:\.\d+)?\s*(?:g|gr|ml|l|kg|oz)\b.*$', '', core, flags=re.IGNORECASE).strip()
            
            if len(core_cleaned) >= 5:
                additional_terms.append(core_cleaned.lower())
                
                # Strip common brand prefixes dynamically
                lower_core = core_cleaned.lower()
                for brand in sorted_brands:
                    if lower_core.startswith(brand):
                        suffix = core_cleaned[len(brand):].strip()
                        if len(suffix) >= 5:
                            additional_terms.append(suffix.lower())
                        break
            
            for t in additional_terms:
                t_clean = t.strip()
                if len(t_clean) >= 6 and t_clean not in stop_words:
                    if t_clean not in entity_pillar_map:
                        entity_pillar_map[t_clean] = []
                    if p["id"] not in entity_pillar_map[t_clean]:
                        entity_pillar_map[t_clean].append(p["id"])

        if not entity_pillar_map:
            return []

        candidates = []
        for sent in sentences:
            text_lower = sent["text"].lower()
            matched_pillars: set[str] = set()
            matched_entities: list[dict] = []

            for entity_name, pillar_ids in entity_pillar_map.items():
                if entity_name in text_lower:
                    matched_pillars.update(pillar_ids)
                    matched_entities.append({
                        "name": entity_name,
                        "pillar_ids": pillar_ids,
                    })

            if matched_pillars:
                candidates.append({
                    **sent,
                    "matched_pillar_ids": list(matched_pillars),
                    "matched_entities": matched_entities,
                })

        return candidates

    # ─── Step 3: PydanticAI Batch Analysis ───────────────────────────────────

    async def _ai_analyze_batch(
        self,
        candidates: list[dict],
        pillars: list[dict],
        brand_keywords_config: Optional[list[str]] = None,
    ) -> Optional[ContextualLinkBatchResult]:
        """
        Send a batch of candidate sentences to PydanticAI for contextual analysis.
        """
        from pydantic_ai import Agent
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

        # Load brand keywords dynamically if not provided
        brand_keywords = brand_keywords_config
        if brand_keywords is None:
            from backend.schemas.system_settings import SeoContextualLinksSettings
            defaults = SeoContextualLinksSettings()
            brand_keywords = [w.lower().strip() for w in defaults.brand_keywords if w.strip()]

        brand_keywords_str = ", ".join(f"'{kw}'" for kw in brand_keywords)

        # Build pillar context for prompt
        pillar_context = "\n".join(
            f"- ID: {p['id']} | Tên: {p['label']} | Topic: {p.get('pillar_topic', 'N/A')} | URL: {p.get('url') or '/' + p.get('slug', '')}"
            for p in pillars[:20]
        )

        # Build sentence list for prompt
        sentence_list = "\n".join(
            f"[{c['index']}] {c['text']}"
            for c in candidates
        )

        system_prompt = (
            "Bạn là chuyên gia SEO thực thể (Entity SEO) chuyên tối ưu hóa cho Google SGE/AI Overviews.\n"
            "Nhiệm vụ: Phân tích từng câu trong danh sách và đề xuất chèn hyperlink nội bộ trỏ tới Pillar Page thích hợp nhất.\n\n"

            "QUY TẮC BẮT BUỘC (Tránh Án Phạt Spam Link của Google và Đảm bảo Trọng tâm): \n"
            "1. CHỈ chèn link vào cụm từ mang ngữ nghĩa thực thể thực sự chất lượng và liên quan trực tiếp đến Pillar Page đích. \n"
            f"2. Đảm bảo tính liên kết chặt chẽ (Topical Alignment): KHÔNG được chèn link từ các cụm từ chung chung về nỗi đau (ví dụ: 'làn da khô', 'thâm sạm') vào trang sản phẩm cụ thể trừ khi câu gốc hoặc anchor text có chứa tên sản phẩm/thương hiệu đó (Danh sách thương hiệu hợp lệ: {brand_keywords_str}) hoặc thành phần chủ đạo độc quyền của sản phẩm.\n"
            "3. Anchor text phải là danh từ riêng, tên thương hiệu, tên sản phẩm hoặc cụm từ khóa có chứa thành phần/tính năng độc quyền của sản phẩm. Tuyệt đối không dùng các từ khóa chung chung làm anchor để trỏ về trang bán sản phẩm cụ thể. Ví dụ tốt: 'tinh chất Placenta Miccosmo', 'kem trị thâm nách Beppin'. Ví dụ xấu: 'làn da vẫn khô khốc', 'dưỡng ẩm', 'trị thâm'.\n"
            "4. CẤM TUYỆT ĐỐI chèn link vào từ đơn lẻ chung chung (Ví dụ: 'kem', 'serum', 'gel', 'mụn', 'da'...) hoặc đại từ (nó, họ, chúng tôi, mình, bạn...), danh từ chung chung vô nghĩa (tại đây, xem thêm, click, link, website, bài viết, sản phẩm...).\n"
            "5. Anchor text phải tự nhiên, có nghĩa đầy đủ, độ dài tối ưu từ 2 đến 8 từ.\n"
            "6. Câu linked_sentence PHẢI giữ nguyên 100% nội dung câu gốc, không được thay đổi, thêm, bớt bất kỳ ký tự hay dấu câu nào. Chỉ bọc cụm anchor_text chính xác bằng thẻ <a href='URL_CUA_PILLAR'>...</a>.\n"
            "7. Chỉ chèn tối đa 1 link duy nhất trên mỗi câu. Bỏ qua nếu câu đã có sẵn liên kết.\n"
            "8. Trong 'reasoning', giải thích cụ thể tại sao thực thể này bổ trợ ngữ nghĩa sâu sắc cho người đọc và kết nối logic với Pillar đích.\n"
            f"9. CẢNH BÁO BẮT BUỘC: Đối với các sản phẩm (ví dụ: kem dưỡng cổ, kem mắt, mặt nạ...), nếu trong câu KHÔNG đề cập rõ ràng đến thương hiệu/tên sản phẩm cụ thể (ví dụ thuộc danh sách: {brand_keywords_str}), tuyệt đối KHÔNG được chèn link vào các cụm từ chung chung như 'kem dưỡng cổ', 'kem trị thâm mắt' hay 'chăm sóc da'. Hãy đặt should_link=false. Vi phạm sẽ bị phạt nặng vì hạ thấp E-E-A-T của trang web.\n"
            "10. Độ tự tin (confidence) PHẢI bị hạ thấp dưới 0.85 (ví dụ: 0.5 - 0.7) nếu cụm từ neo (anchor text) chỉ là các triệu chứng chung chung (symptom), tính năng chung chung (feature) hoặc thành phần không độc quyền mà không đi kèm tên thương hiệu/tên sản phẩm rõ ràng.\n"
            "11. Anchor text tuyệt đối KHÔNG được chứa các dấu phân cách như dấu gạch ngang '-', dấu gạch đứng '|', hoặc phần mô tả công dụng đi kèm sau dấu phân cách (ví dụ: '- Sữa rửa mặt sạch sâu...'). Anchor text chỉ được chọn phần tên thương hiệu và tên sản phẩm cốt lõi (tối đa 8 từ). Ví dụ: chọn 'Miccosmo White Label Premium Placenta Wash 110g' làm anchor thay vì chọn cả cụm 'Miccosmo White Label Premium Placenta Wash 110g - Sữa rửa mặt sạch sâu, làm dịu da'.\n\n"
            "Chỉ đề xuất khi cực kỳ chắc chắn và độ tự tin cao. Nếu không chắc chắn, đặt should_link=false."
        )

        user_msg = (
            f"DANH SÁCH PILLAR PAGES (đích link):\n{pillar_context}\n\n"
            f"CÁC CÂU CẦN PHÂN TÍCH:\n{sentence_list}\n\n"
            "Phân tích từng câu và trả về gợi ý chèn link. "
            "Mỗi suggestion phải có linked_sentence chứa thẻ <a href='URL_PILLAR'> bọc quanh anchor_text."
        )

        agent: Agent[None, ContextualLinkBatchResult] = Agent(
            system_prompt=system_prompt,
            output_type=ContextualLinkBatchResult,
        )

        result = await trinity_bridge.run(agent, user_msg, timeout=_AI_TIMEOUT)
        return result

    # ─── Step 4: Validation ──────────────────────────────────────────────────

    def _validate_suggestion(
        self,
        s: SentenceLinkSuggestion,
        valid_pillar_ids: set[str],
    ) -> list[str]:
        """
        Run 7-rule validation pipeline. Returns list of error strings (empty = valid).
        """
        errors: list[str] = []

        # Rule 1: Sentence Echo Validation
        stripped = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', s.linked_sentence)
        if stripped.strip() != s.original_sentence.strip():
            errors.append(f"Echo mismatch: linked_sentence content differs from original")

        # Rule 2: Anchor Existence Validation
        if s.anchor_text not in s.original_sentence:
            errors.append(f"Anchor '{s.anchor_text}' not found in original sentence")

        # Rule 3: HTML Structural Validation
        a_tags = re.findall(r'<a[^>]*>.*?</a>', s.linked_sentence)
        if len(a_tags) != 1:
            errors.append(f"Expected exactly 1 <a> tag, found {len(a_tags)}")
        elif a_tags:
            # Check anchor content matches
            inner = re.search(r'<a[^>]*>(.*?)</a>', s.linked_sentence)
            if inner and inner.group(1).strip() != s.anchor_text.strip():
                errors.append(f"<a> content '{inner.group(1)}' != anchor_text '{s.anchor_text}'")
            # Check href exists
            if 'href=' not in a_tags[0] and 'href =' not in a_tags[0]:
                errors.append("No href attribute in <a> tag")

        # Rule 4: Target Pillar ID Validation
        if s.target_pillar_id not in valid_pillar_ids:
            errors.append(f"Invalid target_pillar_id: {s.target_pillar_id}")

        # Rule 5: Matched entity type validation
        valid_types = {"pain_point", "feature", "brand", "ingredient", "symptom"}
        if s.matched_entity_type not in valid_types:
            errors.append(f"Invalid matched_entity_type: {s.matched_entity_type}")

        # Rule 6: Anchor text word count validation (2-8 words for optimal context, no single word link spam)
        anchor_words = [w for w in s.anchor_text.strip().split() if w]
        if len(anchor_words) < 2:
            errors.append(f"Anchor text '{s.anchor_text}' is too short (must be at least 2 words to establish entity context)")
        elif len(anchor_words) > 8:
            errors.append(f"Anchor text '{s.anchor_text}' is too long (max 8 words to avoid link over-optimization)")

        # Rule 7: Prevent generic, low-quality, pronoun, or non-contextual Vietnamese keywords
        bad_anchors = {
            "tại đây", "xem thêm", "click", "click vào đây", "đọc thêm", "truy cập",
            "link", "liên kết", "website", "trang web", "bài viết", "sản phẩm",
            "chúng tôi", "shop", "cửa hàng", "mua ngay", "ở đây", "nó", "họ", "chúng ta",
            "các bạn", "mình", "bạn", "tôi", "em", "anh", "chị", "kem", "serum", "gel", "tinh chất"
        }
        anchor_lower = s.anchor_text.strip().lower()
        if anchor_lower in bad_anchors:
            errors.append(f"Anchor text '{s.anchor_text}' is a generic or low-quality SEO keyword")

        return errors

    def _calculate_brand_relevance_multiplier(
        self,
        suggestion: SentenceLinkSuggestion,
        pillars: list[dict[str, object]],
        brand_keywords_config: Optional[list[str]] = None,
        generic_exclusions_config: Optional[set[str]] = None,
    ) -> float:
        """
        Calculates the Brand-Relevance Multiplier (Keyword Affinity Filter).
        If the target is a PRODUCT but the anchor text lacks explicit brand/product name tokens,
        penalizes the suggestion depending on its entity type to prevent generic keyword spam.
        """
        pid = suggestion.target_pillar_id
        target_pillar = None
        for p in pillars:
            if p["id"] == pid:
                target_pillar = p
                break

        if not target_pillar:
            return 1.0

        entity_type = target_pillar.get("entity_type", "ARTICLE")
        if entity_type != "PRODUCT":
            return 1.0

        # Load brand keywords
        brand_keywords = brand_keywords_config
        if brand_keywords is None:
            from backend.schemas.system_settings import SeoContextualLinksSettings
            defaults = SeoContextualLinksSettings()
            brand_keywords = [w.lower().strip() for w in defaults.brand_keywords if w.strip()]

        anchor_lower = (suggestion.anchor_text or "").lower()
        has_brand_token = any(kw in anchor_lower for kw in brand_keywords)

        if has_brand_token:
            return 1.0

        # No brand token found in anchor text -> generic link injection!
        ent_type = suggestion.matched_entity_type
        if hasattr(ent_type, "value"):
            ent_type = ent_type.value
        elif isinstance(ent_type, str):
            ent_type = ent_type.lower()
        else:
            ent_type = str(ent_type).lower()

        # Apply specific penalties based on the matched entity type
        if ent_type in ["brand", "product"]:
            return 0.2
        elif ent_type in ["symptom", "pain_point", "feature"]:
            return 0.4
        elif ent_type == "ingredient":
            return 0.6
        else:
            return 0.4

    def _calculate_eas(
        self,
        suggestion: SentenceLinkSuggestion,
        pillars: list[dict[str, object]],
        article_content: Optional[str] = None,
        brand_keywords_config: Optional[list[str]] = None,
        generic_exclusions_config: Optional[set[str]] = None,
        intent_keywords_config: Optional[list[str]] = None,
    ) -> float:
        """
        Calculate Entity Alignment Score (EAS V2) under Google CTO-level strictness.
        """
        pid = suggestion.target_pillar_id
        target_pillar = None
        for p in pillars:
            if p["id"] == pid:
                target_pillar = p
                break

        if not target_pillar:
            return 0.0

        entity_type = target_pillar.get("entity_type", "ARTICLE")

        # 1. Gate_brand
        gate_brand = 1.0
        if entity_type == "PRODUCT":
            # Check if anchor text contains brand keywords
            brand_keywords = brand_keywords_config
            if brand_keywords is None:
                from backend.schemas.system_settings import SeoContextualLinksSettings
                defaults = SeoContextualLinksSettings()
                brand_keywords = [w.lower().strip() for w in defaults.brand_keywords if w.strip()]
            
            anchor_lower = (suggestion.anchor_text or "").lower()
            has_brand_token = any(kw in anchor_lower for kw in brand_keywords)
            if not has_brand_token:
                gate_brand = 0.0

        # 2. Gate_intent
        gate_intent = 1.0
        sentence_lower = (suggestion.original_sentence or "").lower()
        
        # Load configured intent keywords (verbs/action terms) from config or fallback defaults
        action_verbs = intent_keywords_config
        if action_verbs is None:
            from backend.schemas.system_settings import SeoContextualLinksSettings
            defaults = SeoContextualLinksSettings()
            action_verbs = [w.lower().strip() for w in defaults.intent_keywords if w.strip()]
        
        # Dynamically load configured product types/benefits from settings exclusions list
        settings_exclusions = generic_exclusions_config or set()
        
        has_intent = any(verb in sentence_lower for verb in action_verbs) or any(exc in sentence_lower for exc in settings_exclusions)
        if not has_intent:
            gate_intent = 0.5

        # 3. Base Score
        ent_type = suggestion.matched_entity_type
        if hasattr(ent_type, "value"):
            ent_type = ent_type.value
        elif isinstance(ent_type, str):
            ent_type = ent_type.lower()
        else:
            ent_type = str(ent_type).lower()

        s_type = 0.2
        if ent_type in ["brand", "ingredient", "feature", "product"]:
            s_type = 1.0

        s_context = suggestion.confidence

        base_score = 0.6 * s_type + 0.4 * s_context
        eas = gate_brand * gate_intent * base_score

        # 4. Paragraph-Level Density Gate
        if article_content:
            paragraphs = []
            if "<p>" in article_content:
                paragraphs = re.split(r'</?p>', article_content)
            else:
                paragraphs = article_content.split("\n")
            
            for p_text in paragraphs:
                if suggestion.original_sentence in p_text:
                    existing_a_tags = len(re.findall(r'<a\b[^>]*>', p_text))
                    if existing_a_tags > 0:
                        word_count = len(p_text.split())
                        if word_count < 100:
                            eas *= 0.5
                    break

        return eas

    def _normalize_entity_type(
        self,
        entity_type: str,
        entity_name: str,
        target_pillar_label: str,
        brand_keywords_config: Optional[list[str]] = None
    ) -> str:
        """
        Normalize entity type based on entity name to prevent obvious classification mismatches.
        """
        e_type = entity_type.lower().strip()
        e_name = entity_name.lower().strip()
        p_label = target_pillar_label.lower().strip()
        
        if e_type == "product":
            e_type = "brand"
        
        # Brand and product keywords
        brand_keywords = brand_keywords_config
        if brand_keywords is None:
            from backend.schemas.system_settings import SeoContextualLinksSettings
            defaults = SeoContextualLinksSettings()
            brand_keywords = [w.lower().strip() for w in defaults.brand_keywords if w.strip()]
        
        # If the matched entity name contains any brand names, or is highly similar to the pillar label:
        is_brand_or_product = (
            any(brand in e_name for brand in brand_keywords) or
            e_name in p_label or
            p_label in e_name
        )
        
        if is_brand_or_product:
            if e_type in ["symptom", "pain_point"]:
                e_type = "brand"
                
        return e_type

    @staticmethod
    def _is_inside_anchor(content: str, index: int) -> bool:
        prefix = content[:index].lower()
        last_a = prefix.rfind('<a')
        if last_a == -1:
            return False
        
        # Check boundary
        if last_a + 2 < len(prefix):
            next_char = prefix[last_a + 2]
            if next_char not in (' ', '\t', '\n', '\r', '>'):
                return False
                
        last_close_a = prefix.rfind('</a>')
        return last_a > last_close_a

    # ─── HTML-Tolerant Link Injection ───────────────────────────────────────

    @staticmethod
    def _inject_link_into_html(
        content: str,
        original_sentence: str,
        anchor_text: str,
        target_url: str,
        extra_attrs: str,
    ) -> tuple[str, bool]:
        """
        Inject <a> tag into HTML content.
        Fast-path: direct string match (no inline tags breaking sentence).
        Slow-path: regex tolerating inline HTML tags between words.
        Returns (new_content, success).
        """
        # ── Goal 2: Validate non-empty anchor text and target URL ──
        if not anchor_text or not anchor_text.strip() or not target_url or not target_url.strip():
            return content, False

        # Prevent duplicate injection: check if this target URL is already linked in the content
        url_escaped = re.escape(target_url.strip())
        if re.search(rf'href=["\']{url_escaped}["\']', content, re.IGNORECASE):
            return content, False

        a_tag = f'<a href="{target_url}" class="sge-contextual-link" data-sge-source="ai"{extra_attrs}>{anchor_text}</a>'

        # ── Fast path ────────────────────────────────────────────────────
        if original_sentence in content:
            sentence_index = content.find(original_sentence)
            anchor_in_sentence_index = original_sentence.find(anchor_text)
            if anchor_in_sentence_index != -1:
                anchor_global_index = sentence_index + anchor_in_sentence_index
                if SeoContextualLinker._is_inside_anchor(content, anchor_global_index):
                    return content, False
            new_sentence = original_sentence.replace(anchor_text, a_tag, 1)
            return content.replace(original_sentence, new_sentence, 1), True

        # ── Slow path: regex tolerant of inline HTML tags ────────────────
        # Pattern segment: one or more (HTML tag | whitespace char)
        SEP = r'(?:<[^>]*>|\s)+'

        sent_words = original_sentence.split()
        if not sent_words:
            return content, False

        sent_pattern = SEP.join(re.escape(w) for w in sent_words)
        sent_match = re.search(sent_pattern, content)

        # Fallback: cho phép inline HTML tags nằm sát từ (zero-width separator)
        if not sent_match:
            FLEX_SEP = r'(?:<[^>]*>|\s)*'
            flex_pattern = FLEX_SEP.join(re.escape(w) for w in sent_words)
            sent_match = re.search(flex_pattern, content)

        if sent_match:
            matched_html = sent_match.group(0)
            sentence_global_start = sent_match.start()

            # Find anchor_text within the matched region (also tag-tolerant)
            anchor_words = anchor_text.split()
            if not anchor_words:
                return content, False

            anchor_pattern = SEP.join(re.escape(w) for w in anchor_words)
            anchor_match = re.search(anchor_pattern, matched_html)

            # Flex anchor fallback
            if not anchor_match:
                flex_anchor = r'(?:<[^>]*>|\s)*'.join(re.escape(w) for w in anchor_words)
                anchor_match = re.search(flex_anchor, matched_html)

            if anchor_match:
                anchor_start = anchor_match.start()
                anchor_end = anchor_match.end()
                anchor_global_start = sentence_global_start + anchor_start

                if SeoContextualLinker._is_inside_anchor(content, anchor_global_start):
                    return content, False

                # Replace matched anchor region with clean <a> tag
                new_html = matched_html[:anchor_start] + a_tag + matched_html[anchor_end:]
                return content.replace(matched_html, new_html, 1), True

        # ── Final fallback: tìm anchor_text trực tiếp trong content (bỏ qua sentence) ──
        # Anchor text đã qua Rule 6 validation (2-8 từ), đủ đặc thù để tránh false match
        anchor_words = anchor_text.split()
        if anchor_words:
            direct_anchor_pat = r'(?:<[^>]*>|\s)*'.join(re.escape(w) for w in anchor_words)
            direct_match = re.search(direct_anchor_pat, content)
            if direct_match:
                matched_anchor = direct_match.group(0)
                anchor_global_start = direct_match.start()

                if SeoContextualLinker._is_inside_anchor(content, anchor_global_start):
                    return content, False

                new_content = content.replace(matched_anchor, a_tag, 1)
                logger.info("[ContextualLinker] Used direct anchor fallback for: %s", anchor_text)
                return new_content, True

        logger.warning(
            "[ContextualLinker] All injection paths failed. anchor='%s', sentence='%s'",
            anchor_text, original_sentence[:80],
        )
        return content, False

    # ─── Apply Approved Links ────────────────────────────────────────────────

    async def apply_approved_links(
        self,
        db: AsyncSession,
        article_id: str,
        reviewer_id: Optional[str] = None,
    ) -> dict:
        """
        Apply tất cả approved links vào article.content (JIT frontend rendering).
        Cập nhật trạng thái link đề xuất thành APPLIED, ghi nhận người duyệt, nhưng giữ nguyên nội dung gốc bài viết.
        """
        from backend.database.models.content import Article

        tenant = current_tenant_id.get() or "default"

        article = await db.scalar(
            select(Article).where(
                Article.id == article_id,
                Article.deleted_at.is_(None),
            )
        )
        if not article or not article.content:
            return {"applied_count": 0, "article_id": article_id, "skipped_stale": 0}

        current_hash = hashlib.md5(article.content.encode()).hexdigest()

        # Load approved links, sorted by sentence_index DESC (replace from bottom up)
        links = (await db.execute(
            select(SeoContextualLink).where(
                SeoContextualLink.source_article_id == article_id,
                SeoContextualLink.tenant_id == tenant,
                SeoContextualLink.status == SeoContextualLinkStatus.APPROVED,
            ).order_by(SeoContextualLink.sentence_index.desc())
        )).scalars().all()

        if not links:
            return {"applied_count": 0, "article_id": article_id, "skipped_stale": 0}

        content = article.content
        applied = 0
        skipped_stale = 0
        skipped_inject_fail = 0
        applied_targets: set[str] = set()  # Guard: 1 target_url per article max (anti-spam)

        for link in links:
            # Anti-spam: skip nếu target này đã được chèn vào bài viết trong lần apply này
            if link.target_node_id in applied_targets:
                logger.warning(
                    "[ContextualLinker] Skipping duplicate target %s for article %s (already applied in this session) — anti-spam guard",
                    link.target_node_id, article_id,
                )
                continue

            attrs = []
            if link.link_rel and link.link_rel.strip().lower() not in ["", "dofollow"]:
                attrs.append(f'rel="{link.link_rel.strip()}"')
            if link.link_title:
                attrs.append(f'title="{link.link_title.strip()}"')
            if link.link_target:
                attrs.append(f'target="{link.link_target.strip()}"')

            valid_attrs = " " + " ".join(attrs) if attrs else ""

            new_content, success = self._inject_link_into_html(
                content,
                link.original_sentence,
                link.anchor_text,
                link.target_url,
                valid_attrs,
            )
            if success:
                content = new_content
                applied_targets.add(link.target_node_id)
                link.status = SeoContextualLinkStatus.APPLIED
                link.content_hash = current_hash  # Auto-heal the hash in registry!
                if reviewer_id:
                    link.reviewed_by = reviewer_id
                applied += 1
            else:
                if link.content_hash and link.content_hash != current_hash:
                    skipped_stale += 1
                else:
                    skipped_inject_fail += 1
                logger.warning(
                    "[ContextualLinker] Inject fail for link %s in article %s: sentence not found in HTML",
                    link.id, article_id,
                )

        if applied > 0:
            logger.info(
                "[ContextualLinker] Marked %d links as APPLIED in database registry for article %s",
                applied, article_id,
            )

        return {
            "applied_count": applied,
            "article_id": article_id,
            "skipped_stale": skipped_stale,
            "skipped_inject_fail": skipped_inject_fail,
        }

    # ─── Helpers ─────────────────────────────────────────────────────────────

    async def _load_pillars_with_entities(
        self,
        db: AsyncSession,
        tenant: str,
    ) -> list[dict]:
        """Load all active Pillar nodes with their entities_json."""
        rows = (await db.execute(
            select(SeoNode).where(
                SeoNode.is_pillar == True,
                SeoNode.tenant_id == tenant,
                SeoNode.deleted_at.is_(None),
            )
        )).scalars().all()

        return [
            {
                "id": n.id,
                "label": n.node_label,
                "slug": n.node_slug,
                "url": n.node_url,
                "entity_type": n.entity_type if isinstance(n.entity_type, str) else n.entity_type.value,
                "pillar_topic": n.pillar_topic,
                "entities": n.entities_json or [],
            }
            for n in rows
        ]


# ─── Singleton ────────────────────────────────────────────────────────────────

seo_contextual_linker = SeoContextualLinker()
