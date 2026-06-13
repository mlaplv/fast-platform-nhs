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
from html.parser import HTMLParser
from typing import Optional

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
_MIN_CONFIDENCE = 0.80         # Nâng độ tự tin tối thiểu lên 0.80 để tránh gán bừa bãi
_MAX_LINKS_PER_PILLAR = 1     # Giới hạn 1 link cho mỗi Pillar trỏ về để tránh nhồi nhét
_MAX_LINKS_PER_ARTICLE = 3    # Mật độ an toàn tối đa 3 link ngữ cảnh SGE cho mỗi bài viết Cluster
_AI_TIMEOUT = 25.0


# ─── PydanticAI V2 Output Schemas ────────────────────────────────────────────

class SentenceLinkSuggestion(BaseModel):
    """Output schema cho từng câu được AI phân tích."""
    sentence_index: int = Field(ge=0, description="Vị trí câu trong batch candidates")
    should_link: bool = Field(description="AI có nên chèn link không?")
    original_sentence: str = Field(description="Câu gốc (echoed back để validate)")
    anchor_text: str = Field(max_length=200, description="Cụm từ ngữ cảnh được chọn làm anchor")
    linked_sentence: str = Field(description="Câu hoàn chỉnh với <a> tag đã chèn")
    target_pillar_id: str = Field(description="ID của Pillar Node đích")
    matched_entity_type: str = Field(description="pain_point | feature | brand | ingredient | symptom")
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

    # ─── Public Entry Point ──────────────────────────────────────────────────

    async def analyze_article(
        self,
        db: AsyncSession,
        article_id: str,
        article_content: str,
        article_title: str,
    ) -> int:
        """
        Main pipeline. Chạy sau khi SeoMatchingService hoàn tất.
        Returns: số lượng suggestions đã persist.
        """
        tenant = current_tenant_id.get() or "default"
        content_hash = hashlib.md5(article_content.encode()).hexdigest()

        # Step 0: Load Pillar nodes with their entities
        pillars = await self._load_pillars_with_entities(db, tenant)
        if not pillars:
            logger.info("[ContextualLinker] No pillars found — skipping")
            return 0

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
            return 0

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
            return 0

        # Step 2: Entity pre-filter
        candidates = self._entity_prefilter(sentences, pillars, article_node)
        if not candidates:
            logger.info("[ContextualLinker] No candidate sentences after pre-filter — skipping")
            return 0

        logger.info(
            "[ContextualLinker] %d/%d sentences passed pre-filter for article %s",
            len(candidates), len(sentences), article_id
        )

        # Step 3: PydanticAI batch analysis
        all_suggestions: list[SentenceLinkSuggestion] = []
        for i in range(0, len(candidates), _BATCH_SIZE):
            batch = candidates[i:i + _BATCH_SIZE]
            try:
                batch_result = await self._ai_analyze_batch(batch, pillars)
                if batch_result:
                    all_suggestions.extend(batch_result.suggestions)
            except Exception as e:
                logger.warning("[ContextualLinker] AI batch %d failed: %s", i // _BATCH_SIZE, e)

        if not all_suggestions:
            logger.info("[ContextualLinker] AI returned 0 suggestions for article %s", article_id)
            return 0

        # Step 4: Validate + Persist
        valid_pillar_ids = {p["id"] for p in pillars}
        persisted = 0

        # Clear previous pending/rejected suggestions for this article (re-analysis)
        await db.execute(
            delete(SeoContextualLink).where(
                SeoContextualLink.source_article_id == article_id,
                SeoContextualLink.tenant_id == tenant,
                SeoContextualLink.status.in_(["pending", "rejected"]),
            )
        )

        # Track links per pillar for density constraint
        pillar_link_count: dict[str, int] = {}

        for suggestion in all_suggestions:
            if not suggestion.should_link:
                continue

            # Validate
            errors = self._validate_suggestion(suggestion, valid_pillar_ids)
            if errors:
                logger.debug("[ContextualLinker] Rejected suggestion idx=%d: %s", suggestion.sentence_index, errors)
                continue

            # Confidence gate
            if suggestion.confidence < _MIN_CONFIDENCE:
                continue

            # Density constraint: Giới hạn số lượng link trỏ đến 1 pillar, và giới hạn tổng số link cho cả bài viết
            if persisted >= _MAX_LINKS_PER_ARTICLE:
                logger.info("[ContextualLinker] Reached maximum allowed contextual links (%d) for article %s", _MAX_LINKS_PER_ARTICLE, article_id)
                break

            pid = suggestion.target_pillar_id
            count = pillar_link_count.get(pid, 0)
            if count >= _MAX_LINKS_PER_PILLAR:
                continue
            pillar_link_count[pid] = count + 1

            # Resolve target URL (entity_type-aware: products use /{slug}, articles use /{slug}.html)
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

            # Build linked_sentence with resolved URL
            final_linked = suggestion.linked_sentence
            # Replace placeholder href with actual URL if AI used pillar ID
            if pid in final_linked:
                final_linked = final_linked.replace(pid, target_url)

            link = SeoContextualLink(
                id=new_id_default(),
                source_article_id=article_id,
                target_node_id=pid,
                target_url=target_url,
                original_sentence=suggestion.original_sentence,
                linked_sentence=final_linked,
                anchor_text=suggestion.anchor_text,
                matched_entity_type=suggestion.matched_entity_type,
                matched_entity_name=suggestion.matched_entity_name,
                ai_confidence=suggestion.confidence,
                ai_reasoning=suggestion.reasoning,
                sentence_index=suggestion.sentence_index,
                status=SeoContextualLinkStatus.PENDING,
                content_hash=content_hash,
                tenant_id=tenant,
            )
            db.add(link)
            persisted += 1

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
    ) -> list[dict]:
        """
        Filter sentences: chỉ giữ những câu chứa entity trùng với Pillar nào đó.
        Enriches each candidate with matched_pillar_ids.
        """
        # Build entity → pillar_id lookup
        entity_pillar_map: dict[str, list[str]] = {}
        for p in pillars:
            entities = p.get("entities", [])
            for ent in entities:
                name = ent.get("name", "").lower().strip()
                if name and len(name) >= 3:
                    if name not in entity_pillar_map:
                        entity_pillar_map[name] = []
                    if p["id"] not in entity_pillar_map[name]:
                        entity_pillar_map[name].append(p["id"])

            # Also use pillar label/topic as entity
            label = (p.get("label") or "").lower().strip()
            topic = (p.get("pillar_topic") or "").lower().strip()
            for term in [label, topic]:
                if term and len(term) >= 3:
                    if term not in entity_pillar_map:
                        entity_pillar_map[term] = []
                    if p["id"] not in entity_pillar_map[term]:
                        entity_pillar_map[term].append(p["id"])

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
    ) -> Optional[ContextualLinkBatchResult]:
        """
        Send a batch of candidate sentences to PydanticAI for contextual analysis.
        """
        from pydantic_ai import Agent
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

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

            "QUY TẮC BẮT BUỘC (Tránh Án Phạt Spam Link của Google):\n"
            "1. CHỈ chèn link vào cụm từ mang ngữ nghĩa thực thể thực sự chất lượng mô tả: Nỗi đau cụ thể của khách hàng (pain_point), Tính năng sản phẩm độc đáo (feature), "
            "Thương hiệu (brand), Thành phần đặc trị (ingredient), hoặc Triệu chứng bệnh lý (symptom).\n"
            "2. CẤM TUYỆT ĐỐI chèn link vào từ đơn lẻ chung chung (Ví dụ: 'kem', 'serum', 'gel', 'mụn', 'da'...) hoặc đại từ (nó, họ, chúng tôi, mình, bạn...), danh từ chung chung vô nghĩa (tại đây, xem thêm, click, link, website, bài viết, sản phẩm...).\n"
            "3. Anchor text phải tự nhiên, có nghĩa đầy đủ, độ dài tối ưu từ 2 đến 8 từ. Ví dụ tốt: 'trị thâm nách Beppin', 'placenta dưỡng trắng da', 'làn da khô ráp xỉn màu'. Ví dụ xấu: 'kem', 'ở đây'.\n"
            "4. Câu linked_sentence PHẢI giữ nguyên 100% nội dung câu gốc, không được thay đổi, thêm, bớt bất kỳ ký tự hay dấu câu nào. Chỉ bọc cụm anchor_text chính xác bằng thẻ <a href='URL_CUA_PILLAR'>...</a>.\n"
            "5. Chỉ chèn tối đa 1 link duy nhất trên mỗi câu. Bỏ qua nếu câu đã có sẵn liên kết.\n"
            "6. Trong 'reasoning', giải thích cụ thể tại sao thực thể này bổ trợ ngữ nghĩa sâu sắc cho người đọc và kết nối logic với Pillar đích.\n\n"
            "Chỉ đề xuất when cực kỳ chắc chắn và độ tự tin cao. Nếu không chắc chắn, đặt should_link=false."
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
        a_tag = f'<a href="{target_url}" class="sge-contextual-link" data-sge-source="ai"{extra_attrs}>{anchor_text}</a>'

        # ── Fast path ────────────────────────────────────────────────────
        if original_sentence in content:
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
        if not sent_match:
            return content, False

        matched_html = sent_match.group(0)

        # Find anchor_text within the matched region (also tag-tolerant)
        anchor_words = anchor_text.split()
        if not anchor_words:
            return content, False

        anchor_pattern = SEP.join(re.escape(w) for w in anchor_words)
        anchor_match = re.search(anchor_pattern, matched_html)
        if not anchor_match:
            return content, False

        # Replace matched anchor region with clean <a> tag
        new_html = matched_html[:anchor_match.start()] + a_tag + matched_html[anchor_match.end():]
        return content.replace(matched_html, new_html, 1), True

    # ─── Apply Approved Links ────────────────────────────────────────────────

    async def apply_approved_links(
        self,
        db: AsyncSession,
        article_id: str,
    ) -> dict:
        """
        Apply tất cả approved links vào article.content.
        Replace từ cuối bài lên đầu để tránh lệch index.
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

        for link in links:
            # Stale check
            if link.content_hash != current_hash:
                skipped_stale += 1
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
                link.status = SeoContextualLinkStatus.APPLIED
                applied += 1

        if applied > 0:
            article.content = content
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(article, "content")

        return {"applied_count": applied, "article_id": article_id, "skipped_stale": skipped_stale}

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
