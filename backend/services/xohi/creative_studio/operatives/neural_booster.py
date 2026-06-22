import asyncio
import logging
import re
from datetime import datetime, timezone
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from typing import List, Optional
from backend.services.xohi.creative_studio.models.schemas import NeuralBoosterReport, ClinicalSource, ClinicalDataTable, KeyStat
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.agent_base import BaseAgentOperative, SearchKeyMixin
from backend.utils.text import extract_readable_text
from backend.services.xohi.prompts import composer
from backend.services.xohi.prompts.shields.service import shield_service
from backend.services.prompt_entropy import build_entropy_system_prompt
from backend.utils.http_client import get_http_client

logger = logging.getLogger("api-gateway")

# ══════════════════════════════════════════════════════════════
# CNS V92.0: JAPAN CLINICAL EVIDENCE CONSTANTS
# ══════════════════════════════════════════════════════════════
# Nguồn uy tín được target theo thứ tự ưu tiên:
# 1. J-STAGE   — Cơ sở dữ liệu KH&CN Nhật Bản (JST)
# 2. PubMed    — NIH/NLM (Mỹ, tài liệu JP đăng quốc tế)
# 3. WHO       — Tổ chức Y tế Thế giới
# 4. PMDA      — Cơ quan Dược phẩm & Thiết bị Y tế Nhật Bản
# 5. JSCC      — Hiệp hội Hóa mỹ phẩm Nhật Bản
_CLINICAL_SEARCH_TIMEOUT = 6.0   # 6s per query — tránh treo event loop
_MAX_SNIPPETS_PER_QUERY = 4       # Lấy tối đa 4 snippets mỗi query

# Các miền uy tín để filter và display
_TRUSTED_DOMAINS = {
    # Nhật Bản (Cốt lõi)
    "jstage.jst.go.jp": "J-STAGE (Nhật Bản)",
    "pmda.go.jp": "PMDA (Nhật Bản)",
    "nihs.go.jp": "NIHS (Nhật Bản)",
    "cosme.net": "Cosme (Nhật Bản)",
    "jcia-net.or.jp": "JCIA (Nhật Bản)",
    
    # Tổ chức Y tế & Quản lý Y tế toàn cầu
    "who.int": "WHO (Tổ chức Y tế Thế giới)",
    "fda.gov": "FDA (Cục quản lý Thực phẩm và Dược phẩm Mỹ)",
    "cdc.gov": "CDC (Trung tâm kiểm soát và phòng ngừa dịch bệnh Mỹ)",
    "ema.europa.eu": "EMA (Cơ quan Quản lý Dược phẩm Châu Âu)",
    "nhs.uk": "NHS (Dịch vụ Y tế Quốc gia Anh)",
    "echa.europa.eu": "ECHA (Cơ quan Hóa chất Châu Âu)",
    "ec.europa.eu": "European Commission (Ủy ban Châu Âu)",
    "tga.gov.au": "TGA (Cục Quản lý Hàng hóa Trị liệu Úc)",
    "health.gov": "U.S. Department of Health and Human Services",
    
    # Thư viện Y học & Cơ sở dữ liệu khoa học uy tín toàn cầu
    "pubmed.ncbi.nlm.nih.gov": "PubMed",
    "ncbi.nlm.nih.gov": "PubMed / NCBI",
    "europepmc.org": "Europe PMC",
    "sciencedirect.com": "ScienceDirect",
    "nature.com": "Nature",
    "springer.com": "Springer",
    "mdpi.com": "MDPI",
    "wiley.com": "Wiley Online Library",
    "onlinelibrary.wiley.com": "Wiley Online Library",
    "tandfonline.com": "Taylor & Francis Online",
    "plos.org": "PLOS",
    "frontiersin.org": "Frontiers",
    "cell.com": "Cell Press",
    "academic.oup.com": "Oxford Academic",
    "cambridge.org": "Cambridge Core",
    
    # Y khoa / Lâm sàng danh tiếng
    "thelancet.com": "The Lancet",
    "nejm.org": "NEJM (New England Journal of Medicine)",
    "jamanetwork.com": "JAMA Network",
    "bmj.com": "The BMJ (British Medical Journal)",
    "cochranelibrary.com": "Cochrane Library",
    "mayoclinic.org": "Mayo Clinic",
    
    # Da liễu & Mỹ phẩm / Thành phần hóa chất chuyên sâu
    "cir-safety.org": "Cosmetic Ingredient Review (CIR)",
    "ewg.org": "EWG (Environmental Working Group)",
    "cosmeticsandtoiletries.com": "Cosmetics & Toiletries",
    "cosmeticsdesign.com": "Cosmetics Design",
    "chemicalsafetyfacts.org": "Chemical Safety Facts",
    
    # Các trang tin khoa học & cộng đồng nghiên cứu
    "sciencedaily.com": "ScienceDaily",
    "researchgate.net": "ResearchGate",
    "scholar.google.com": "Google Scholar",
}


class _EnrichedSnippet(BaseModel):
    """CNS V93.0: Schema nội bộ để AI translate JP/EN → VI và extract số liệu định lượng."""
    title_vi: str = Field(description="Tiêu đề dịch sang tiếng Việt tự nhiên, chuyên nghiệp")
    snippet_vi: str = Field(description="Trích đoạn dịch sang tiếng Việt — chính xác, không thêm thắt")
    year: str = Field(default="N/A", description="Năm công bố nếu có trong văn bản (YYYY), nếu không rõ trả về 'N/A'")
    relevance: str = Field(description="1-2 câu giải thích tại sao nghiên cứu này liên quan đến chủ đề đang xét")
    key_stats: List[dict] = Field(
        default_factory=list,
        description=(
            "Tối đa 3 số liệu/chỉ số ĐỊNH LƯỢNG cụ thể trích từ nghiên cứu. "
            "Mỗi item là dict gồm: label (str), value (str), unit (str, có thể rỗng), note (str, có thể rỗng). "
            "VD: {\"label\": \"Hiệu quả giảm nếp nhăn\", \"value\": \"43%\", \"unit\": \"\", \"note\": \"RCT, n=120, 8 tuần\"}. "
            "Chỉ lấy số liệu CÓ TRONG TEXT, không bịa đặt. Nếu không có số liệu, trả về []"
        )
    )


class NeuralBooster(BaseAgentOperative, SearchKeyMixin):
    """
    CNS V92.0: Neural Booster Operative với Japan Clinical Evidence Search.
    Elite V2.2: Tìm kiếm 4 nguồn uy tín quốc tế, dịch thuần Việt, cite minh bạch.
    """
    agent_id_class = "neural_booster"

    def __init__(self) -> None:
        super().__init__(agent_id="neural_booster")
        self._agent = Agent(
            output_type=NeuralBoosterReport,
            retries=2
        )
        # Lazy singleton Agent dịch thuật — nhỏ gọn, dùng role "fast"
        self._translate_agent: Agent[None, _EnrichedSnippet] | None = None

    def _get_translate_agent(self) -> Agent[None, _EnrichedSnippet]:
        if self._translate_agent is None:
            self._translate_agent = Agent(
                output_type=_EnrichedSnippet,
                system_prompt=(
                    "Bạn là chuyên gia dịch thuật & phân tích khoa học Nhật-Anh → Việt. "
                    "NHIỆM VỤ KÉP: (1) Dịch CHÍNH XÁC title và snippet — không diễn giải thêm. "
                    "(2) Trích xuất tối đa 3 số liệu ĐỊNH LƯỢNG cụ thể (%, mg, mmHg, n=...) "
                    "thực sự có trong text. Chỉ lấy số liệu đã được đo lường, KHÔNG bịa đặt. "
                    "Giữ thuật ngữ chuyên ngành, dùng tiếng Việt chuyên nghiệp chuẩn học thuật. "
                    "QUY TẮC KHOẢNG TRẮNG: Tuyệt đối KHÔNG viết dính liền chữ tiếng Việt với từ tiếng Anh, số, phần trăm (%) hoặc ký tự đóng/mở ngoặc đơn (Ví dụ: KHÔNG viết '31.4%là', 'biểu bìThấp', '(PubMed)Sodium'). Luôn dùng khoảng trắng đúng chuẩn chính tả."
                ),
                retries=1
            )
        return self._translate_agent

    # ────────────────────────────────────────────────────────────
    # PHASE 1: CLINICAL EVIDENCE SEARCH
    # ────────────────────────────────────────────────────────────
    async def _fetch_one_query(self, query: str) -> list[dict]:
        """Thực hiện 1 Google Custom Search query, trả về raw items."""
        self._ensure_search_keys()
        pair = await self._get_search_pair()
        if not pair:
            return []
        try:
            client = await get_http_client()
            resp = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": pair["key"],
                    "cx": pair["cx"],
                    "q": query,
                    "num": _MAX_SNIPPETS_PER_QUERY,
                    "gl": "jp",   # Ưu tiên kết quả Nhật Bản
                    "hl": "ja",
                }
            )
            if resp.status_code == 200:
                return resp.json().get("items", [])
            else:
                logger.warning(f"[NeuralBooster] Search returned {resp.status_code} for: {query[:50]}")
                return []
        except Exception as e:
            logger.warning(f"[NeuralBooster] Search error: {e}")
            return []

    def _build_clinical_queries(self, topic: str) -> list[str]:
        """
        Xây dựng 4 query chiến lược targeting nguồn lâm sàng & bài báo uy tín.
        Relaxed constraints để tìm được dữ liệu cho cả sản phẩm cụ thể.
        """
        return [
            # Q1: J-STAGE & NIHS — Nghiên cứu khoa học, thành phần, hiệu quả (Nhật Bản)
            f"{topic} 研究 OR 論文 OR 効果 OR 評価 site:jstage.jst.go.jp OR site:nihs.go.jp",
            # Q2: PubMed & ScienceDirect — Báo cáo y khoa / da liễu / bài báo uy tín
            f"{topic} dermatology OR cosmetics OR research OR review",
            # Q3: Chuyên trang đánh giá / y tế uy tín Nhật Bản & Quốc tế
            f"{topic} chuyên gia đánh giá OR báo cáo uy tín OR review cosmetics",
            # Q4: Cơ quan quản lý Nhật (PMDA, JCIA) & Cosme (nguồn uy tín Nhật)
            f"{topic} 成分 OR 安全性 OR 口コミ site:pmda.go.jp OR site:jcia-net.or.jp OR site:cosme.net",
        ]

    def _get_domain_label(self, url: str) -> str:
        """Ánh xạ URL → tên nguồn uy tín hiển thị."""
        for domain, label in _TRUSTED_DOMAINS.items():
            if domain in url:
                return label
        # Fallback: extract domain
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else "Nguồn quốc tế"

    async def _enrich_snippet(
        self, title: str, snippet: str, url: str, topic: str
    ) -> _EnrichedSnippet | None:
        """CNS V93.0: Dịch title + snippet JP/EN → VI và extract key_stats định lượng."""
        if not title and not snippet:
            return None
        prompt = (
            f"[CHỦ ĐỀ PHÂN TÍCH]: {topic}\n"
            f"[TIÊU ĐỀ GỐC]: {title}\n"
            f"[TRÍCH ĐOẠN GỐC]: {snippet}\n"
            f"[URL NGUỒN]: {url}\n\n"
            "Nhiệm vụ: (1) Dịch tiêu đề và trích đoạn sang tiếng Việt CHUẨN HỌC THUẬT. "
            "(2) Trích xuất tối đa 3 số liệu ĐỊNH LƯỢNG có trong text (%, n=, mg, etc.). "
            "(3) Cho biết mức độ liên quan đến chủ đề."
        )
        try:
            agent = self._get_translate_agent()
            result = await trinity_bridge.run(agent, prompt, role="fast", timeout=15.0)
            if result is None or not isinstance(result, _EnrichedSnippet):
                return None
            return result
        except Exception as e:
            logger.warning(f"[NeuralBooster] Enrich failed for '{title[:30]}': {e}")
            return None

    async def _search_clinical_evidence(self, topic: str, campaign_id: str) -> list[ClinicalSource]:
        """
        CNS V93.0: Parallel search 4 queries → enrich (translate + extract stats) → ClinicalSource list.
        """
        queries = self._build_clinical_queries(topic)

        fetch_tasks = [
            asyncio.wait_for(self._fetch_one_query(q), timeout=_CLINICAL_SEARCH_TIMEOUT)
            for q in queries
        ]

        raw_batches: list[list[dict]] = []
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, list):
                raw_batches.append(r)
            else:
                logger.warning(f"[NeuralBooster] A search query failed/timed-out: {r}")
                raw_batches.append([])

        # Gom + dedup theo URL
        seen_urls: set[str] = set()
        raw_items: list[dict] = []
        for batch in raw_batches:
            for item in batch:
                url = item.get("link", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    raw_items.append(item)

        # ── TRUSTED DOMAIN FILTER ──────────────────────────────────────────
        def _is_trusted(u: str) -> bool:
            return any(domain in u for domain in _TRUSTED_DOMAINS)

        trusted_items = [item for item in raw_items if _is_trusted(item.get("link", ""))]
        rejected_count = len(raw_items) - len(trusted_items)
        if rejected_count > 0:
            logger.info(
                f"[NeuralBooster] Trusted-domain filter: kept {len(trusted_items)}/{len(raw_items)} "
                f"(rejected {rejected_count} non-whitelisted URLs)"
            )
        raw_items = trusted_items
        # ──────────────────────────────────────────────────────────────────

        if not raw_items:
            logger.info("[NeuralBooster] No clinical search results found (or all filtered out).")
            return []

        logger.info(f"[NeuralBooster] Found {len(raw_items)} unique clinical sources. Enriching...")

        # Parallel enrich: dịch + extract stats (max 8)
        enrich_tasks = [
            self._enrich_snippet(
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                url=item.get("link", ""),
                topic=topic
            )
            for item in raw_items[:8]
        ]
        enriched = await asyncio.gather(*enrich_tasks, return_exceptions=True)

        clinical_sources: list[ClinicalSource] = []
        for item, enc in zip(raw_items[:8], enriched):
            if enc is None or not isinstance(enc, _EnrichedSnippet):
                continue
            url = item.get("link", "")

            # Parse key_stats từ list[dict] → list[KeyStat]
            key_stats: list[KeyStat] = []
            for ks in (enc.key_stats or []):
                if isinstance(ks, dict) and ks.get("label") and ks.get("value"):
                    try:
                        key_stats.append(KeyStat(
                            label=str(ks.get("label", "")),
                            value=str(ks.get("value", "")),
                            unit=str(ks.get("unit", "")),
                            note=str(ks.get("note", ""))
                        ))
                    except Exception:
                        pass

            source = ClinicalSource(
                title_vi=enc.title_vi or item.get("title", ""),
                title_original=item.get("title", ""),
                source_domain=self._get_domain_label(url),
                source_url=url,
                year=enc.year or "N/A",
                snippet_vi=enc.snippet_vi or item.get("snippet", ""),
                relevance=enc.relevance or "",
                key_stats=key_stats
            )
            clinical_sources.append(source)

        logger.info(f"[NeuralBooster] Enriched {len(clinical_sources)} clinical sources.")
        return clinical_sources

    # ────────────────────────────────────────────────────────────
    # PHASE 2.5: SYNTHESIZE DATA TABLES
    # ────────────────────────────────────────────────────────────
    async def _synthesize_data_tables(
        self, sources: list[ClinicalSource], topic: str, campaign_id: str
    ) -> list[ClinicalDataTable]:
        """
        CNS V93.0: Tổng hợp bảng số liệu có cấu trúc từ key_stats của nhiều nguồn.
        Dùng 1 LLM call nhỏ — cap 2 bảng để tránh latency.
        """
        # Chỉ tổng hợp khi có ≥2 nguồn có số liệu
        sources_with_stats = [s for s in sources if s.key_stats]
        if len(sources_with_stats) < 2:
            logger.info("[NeuralBooster] Not enough key_stats for table synthesis.")
            return []

        # Build context để gửi cho LLM
        stats_context_lines = [f"[CHỦ ĐỀ]: {topic}\n"]
        for src in sources_with_stats[:6]:  # Max 6 nguồn
            stats_context_lines.append(
                f"\n[NGUỒN: {src.source_domain}, {src.year}]\n"
                f"Tiêu đề: {src.title_vi}\n"
            )
            for ks in src.key_stats:
                unit_str = f" {ks.unit}" if ks.unit else ""
                note_str = f" ({ks.note})" if ks.note else ""
                stats_context_lines.append(f"  - {ks.label}: {ks.value}{unit_str}{note_str}")

        stats_context = "\n".join(stats_context_lines)

        _table_agent: Agent[None, list[ClinicalDataTable]] = Agent(
            output_type=list[ClinicalDataTable],  # type: ignore[arg-type]
            system_prompt=(
                "Bạn là chuyên gia tổng hợp dữ liệu khoa học. "
                "Từ các số liệu nghên cứu được cung cấp, tạo TỐI ĐA 2 bảng số liệu có cấu trúc. "
                "Mỗi bảng phải có headers rõ ràng và rows với dữ liệu thực tế. "
                "Bảng 1: hiệu quả lâm sàng (efficacy). Bảng 2: bảng so sánh các nghên cứu (comparison). "
                "Tiêu đề và caption bất buộc tiếng Việt. source_citation theo format '(Tên, Năm)'. "
                "CHỈ DÙNG số liệu ĐÃ CÓ trong context, không bịa đặt."
            ),
            retries=1
        )

        try:
            tables = await trinity_bridge.run(
                _table_agent,
                stats_context,
                role="fast",
                timeout=20.0
            )
            if not isinstance(tables, list):
                return []
            # Validate và filter bảng hợp lệ
            valid: list[ClinicalDataTable] = []
            for t in tables:
                if isinstance(t, ClinicalDataTable) and t.headers and t.rows:
                    valid.append(t)
            logger.info(f"[NeuralBooster] Synthesized {len(valid)} data table(s).")
            return valid[:2]  # Cap 2 bảng
        except Exception as e:
            logger.warning(f"[NeuralBooster] Table synthesis failed: {e}")
            return []

    # ────────────────────────────────────────────────────────────
    # MAIN ENTRY
    # ────────────────────────────────────────────────────────────
    async def chat(self, request: object, **kwargs: object) -> NeuralBoosterReport:
        """Standard Heritage Entry."""
        content_raw = str(getattr(request, "draft_content", "")) or str(kwargs.get("content", ""))
        content = extract_readable_text(content_raw)
        topic = str(getattr(request, "topic", "")) or str(kwargs.get("topic", ""))
        campaign_id = getattr(request, "id", str(kwargs.get("campaign_id", "adhoc")))
        # CNS V92.1: Nhận content_type từ kwargs — phân biệt "product" vs "article"
        content_type = str(kwargs.get("content_type", "") or "")

        logs: list[str] = [
            f"🚀 Neural Booster khởi động tại {datetime.now(timezone.utc).strftime('%H:%M:%S')}...",
        ]
        await self._emit_progress(campaign_id, logs[-1])

        if not content or len(content.strip()) < 50:
            return NeuralBoosterReport(
                patches=[],
                summary="Nội dung quá ngắn để tinh chỉnh.",
                logs=logs,
                clinical_sources=[]
            )

        # ── PHASE 1: Tìm kiếm bằng chứng lâm sàng (song song với thông báo) ──
        logs.append("🔬 Đang trinh sát bằng chứng lâm sàng từ J-STAGE, PubMed, WHO, PMDA...")
        await self._emit_progress(campaign_id, logs[-1])

        # Chạy song song: search + resolve context (không block nhau)
        clinical_task = asyncio.create_task(
            self._search_clinical_evidence(topic, campaign_id)
        )
        context_task = asyncio.create_task(
            # CNS V92.1: Truyền content_type để resolve đúng vai (product/article)
            self._resolve_xohi_context(request, content, "booster", content_type=content_type)
        )

        clinical_sources, context = await asyncio.gather(clinical_task, context_task)

        if clinical_sources:
            stats_count = sum(len(s.key_stats) for s in clinical_sources)
            logs.append(f"✅ Trinh sát hoàn tất: Tìm được {len(clinical_sources)} nguồn uy tín — {stats_count} số liệu định lượng ({', '.join(set(s.source_domain for s in clinical_sources[:3]))}...)")
        else:
            logs.append("⚠️ Không tìm được nguồn lâm sàng từ Google (tiếp tục với AI thuần).")
        await self._emit_progress(campaign_id, logs[-1])

        # ── PHASE 2.5: Tổng hợp bảng số liệu (song song với build prompt) ──
        logs.append("📊 Đang tổng hợp bảng số liệu lâm sàng có cấu trúc...")
        await self._emit_progress(campaign_id, logs[-1])

        # ── PHASE 2 + 2.5: Build prompt và tổng hợp bảng song song ──
        await self._emit_progress(campaign_id, context["log_msg"])
        logs.append(f"🛡️ [ROLE] Đã xác nhận phân vai tác chiến: {context['role_assignment']}")
        await self._emit_progress(campaign_id, logs[-1])

        logs.append("🛡️ [SHIELD] Đã kích hoạt SGE Shield V2.1 (Anti-AI Footprint)")
        await self._emit_progress(campaign_id, logs[-1])

        # Chạy song song: table synthesis + context block build
        table_task = asyncio.create_task(
            self._synthesize_data_tables(clinical_sources, topic, campaign_id)
        )

        # Build clinical evidence context block để inject vào prompt
        clinical_context_block = self._build_clinical_context_block(clinical_sources, topic)

        topic_prefix = f"[CHỦ ĐỀ]: {topic}\n\n" if topic else ""
        prompt = (
            f"{topic_prefix}"
            f"{clinical_context_block}"
            f"[NỘI DUNG CẦN TINH CHỈNH]:\n{content[:10000]}"
        )

        # Đợi table synthesis hoàn tất
        data_tables = await table_task
        if data_tables:
            logs.append(f"📊 Tổng hợp hoàn tất: {len(data_tables)} bảng số liệu lâm sàng đã sẵn sàng.")
        else:
            logs.append("⚠️ Chưa đủ số liệu định lượng để tổng hợp bảng (tiếp tục với cite text).")
        await self._emit_progress(campaign_id, logs[-1])

        is_adhoc = campaign_id == "adhoc"
        logs.append(f"🛡️ [SAFETY] Chế độ Ad-hoc Safety: {'ACTIVE' if is_adhoc else 'CAMPAIGN_MODE'}")
        await self._emit_progress(campaign_id, logs[-1])

        shield = shield_service.get_shield_component(seed=str(campaign_id))
        composer.register_component(shield)

        # ELITE V2.2: Use extra_components to maintain thread-safety
        system_prompt = composer.compose("booster_refiner", context=context, extra_components=[shield.id])
        # SGE Shield V2.0: Inject tone + structure entropy
        system_prompt = build_entropy_system_prompt(system_prompt, product_id=str(campaign_id))

        logs.append("📡 [CONNECT] Kết nối Neural Bridge (Role: PRO)...")
        await self._emit_progress(campaign_id, logs[-1])

        try:
            result = await trinity_bridge.run(
                self._agent, prompt,
                system_prompt=system_prompt,
                role="pro",
                timeout=90.0
            )

            # SGE Shield V2.0: Lexical Sanitizer
            if hasattr(result, "patches"):
                for patch in result.patches:
                    if hasattr(patch, "replacement_string"):
                        patch.replacement_string = shield_service.sanitize(patch.replacement_string)

            logs.append(f"✅ Hoàn tất! {len(result.patches)} phân đoạn tinh chỉnh sẵn sàng.")
            if clinical_sources:
                stats_total = sum(len(s.key_stats) for s in clinical_sources)
                logs.append(
                    f"📚 Đính kèm {len(clinical_sources)} nguồn lâm sàng ({stats_total} số liệu) "
                    f"+ {len(data_tables)} bảng cấu trúc để verify."
                )
            await self._emit_progress(campaign_id, logs[-1], status="DONE")

            result.logs = logs
            result.clinical_sources = clinical_sources
            result.data_tables = data_tables
            return result

        except Exception as exc:
            logger.error(f"[NeuralBooster] Lỗi tinh chỉnh: {exc}", exc_info=True)
            err_msg = f"❌ Lỗi tinh chỉnh: {str(exc)[:100]}"
            await self._emit_progress(campaign_id, err_msg, status="FAILED")
            return NeuralBoosterReport(
                patches=[],
                summary=f"Tinh chỉnh thất bại: {str(exc)[:100]}",
                logs=[*logs, err_msg],
                clinical_sources=clinical_sources,
                data_tables=data_tables  # Vẫn trả về bảng đã tổng hợp được
            )

    def _build_clinical_context_block(
        self, sources: list[ClinicalSource], topic: str
    ) -> str:
        """Build block context bằng chứng lâm sàng để inject vào AI prompt."""
        if not sources:
            return ""

        lines = [
            "═══════════════════════════════════════════════════════════",
            "📚 BẰNG CHỨNG LÂM SÀNG & BÀI BÁO UY TÍN ĐÃ TRINH SÁT",
            "   Nguồn: J-STAGE / PubMed / Chuyên gia / Nguồn Nhật Bản uy tín",
            "═══════════════════════════════════════════════════════════",
        ]
        for i, src in enumerate(sources, 1):
            lines += [
                f"\n[NGHIÊN CỨU #{i}]",
                f"📰 Tiêu đề (VI): {src.title_vi}",
                f"📝 Tiêu đề gốc: {src.title_original}",
                f"🏛️ Nguồn: {src.source_domain} | Năm: {src.year}",
                f"🔗 URL gốc: {src.source_url}",
                f"📖 Nội dung: {src.snippet_vi}",
                f"🎯 Liên quan: {src.relevance}",
            ]
        lines += [
            "\n═══════════════════════════════════════════════════════════",
            "⚠️  QUAN TRỌNG: Khi bổ sung dữ liệu từ các nghiên cứu trên,",
            "   PHẢI cite đúng theo format: (Tên nguồn, Năm) — hoàn toàn tiếng Việt.",
            "   KHÔNG bịa đặt nguồn. Chỉ dùng các nghiên cứu đã được cung cấp.",
            "   CẤM TUYỆT ĐỐI nhúng URL vào bài dưới dạng <a href> hoặc hyperlink.",
            "   URL chỉ dùng để tham chiếu nội bộ — KHÔNG xuất hiện trong nội dung bài viết.",
            "═══════════════════════════════════════════════════════════\n",
        ]
        return "\n".join(lines) + "\n\n"


# CNS V92.0: Module-level singleton (tránh tạo instance mới mỗi legacy call)
_neural_booster_singleton: NeuralBooster | None = None

def _get_booster_singleton() -> NeuralBooster:
    global _neural_booster_singleton
    if _neural_booster_singleton is None:
        _neural_booster_singleton = NeuralBooster()
    return _neural_booster_singleton

# Heritage Backdoor for legacy calls
async def run_surgeon_boost(content: str, topic: str = "", content_type: str = "article") -> NeuralBoosterReport:
    return await _get_booster_singleton().chat(None, content=content, topic=topic, content_type=content_type)

# Heritage Backdoor (original name kept for backward compat)
async def run_neural_boost(content: str, topic: str = "", content_type: str = "article") -> NeuralBoosterReport:
    return await _get_booster_singleton().chat(None, content=content, topic=topic, content_type=content_type)
