import json
import logging
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from flashtext import KeywordProcessor
from rapidfuzz import fuzz
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from pydantic_ai import Agent

logger = logging.getLogger("api-gateway")

# Phase 76.3: Advanced Deterministic Artifact Stripper (HFS)
# Exported for use in sibling operatives (V76.3)
RE_HTML_TAGS = re.compile(r'<[^>]+>')
RE_IMAGE_PLACEHOLDERS = re.compile(r'\[IMAGE_\d+\]')
RE_WHITESPACE = re.compile(r'\s+')

RE_MARKDOWN_CLEAN = [
    (re.compile(r'\*\*'), ''),           # Bold **
    (re.compile(r'__'), ''),             # Bold __
    (re.compile(r'#{1,6}\s+'), ''),     # Headings
    (re.compile(r'!\[.*?\]\(.*?\)\s*'), ''), # Images
    (re.compile(r'\[.*?\]\(.*?\)\s*'), ''),   # Links
    (re.compile(r'`{1,3}.*?`{1,3}', re.DOTALL), ''), # Inline code / fences
    (re.compile(r'^\s*[-*+]\s+', re.MULTILINE), ''), # List bullets
    (re.compile(r'^\s*\d+\.\s+', re.MULTILINE), ''), # Numbered lists
]

# Phase 76.9: Deterministic HTML Artifact Strippers
RE_CODE_ARTIFACTS = re.compile(r'<(pre|code|script|style)[^>]*>.*?</\1>', re.DOTALL | re.IGNORECASE)
RE_ROGUE_LINKS = re.compile(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.IGNORECASE)

# Phase 76.9: Advanced AI Preamble & Postamble Strippers (Viral 2026)
RE_AI_CONVERSATION = re.compile(
    r'(?i)^(vâng|dưới đây là|chắc chắn rồi|đây là|tôi đã|hy vọng|sau đây là|bài viết của bạn).*?(\n|:)',
    re.MULTILINE
)
RE_AI_POSTAMBLES = re.compile(
    r'(?i)(hy vọng bài viết|chúc bạn|nếu cần thêm|liên hệ với tôi|đây là bản thảo).*$',
    re.DOTALL
)
RE_MARKDOWN_FENCES = re.compile(r'```[a-z]*|```', re.IGNORECASE)

class NoiseCleaner:
    """
    R23: Hybrid Noise Shield Engine V2026.
    Implements a 3-layer pipeline to sanitize text from web crawlers and AI hallucinations.
    """
    
    def __init__(self, dictionary_path: Optional[str] = None):
        self.dictionary_path = dictionary_path or str(Path(__file__).parents[2] / "resources" / "noise_dictionary.json")
        self.keyword_processor = KeywordProcessor(case_sensitive=False)
        self.fuzzy_patterns: Dict[str, List[str]] = {}
        self.semantic_categories: List[str] = []
        
        # SLM Agent for Layer 3 (Semantic Audit)
        self._audit_agent = Agent(
            system_prompt="Bạn là một chuyên gia lọc nhiễu văn bản. Hãy xác định xem đoạn văn sau có chứa thông tin rác (quảng cáo, mã lỗi, boilerplate) hay không. Chỉ trả về label: CLEAN hoặc JUNK.",
        )

        # Phase 76.9: Viral 2026 Polish Agent
        self._polish_agent = Agent(
            system_prompt="""[ROLE] VIRAL CONTENT ARCHITECT — Fast Platform 2026
[NHIỆM VỤ]
Làm sạch và tối ưu bài viết HTML/Text sau đây để đạt chuẩn "Viral 2026".

[QUY TẮC CỨNG - TUYỆT ĐỐI TUÂN THỦ]
1. XÓA BỎ: Các đoạn mã code dư thừa (js, css, html comment), link rác không liên quan đến nội dung chính.
2. XÓA BỎ: Các câu lặp ý, nội dung boilerplate (ví dụ: "Click here", "Read more", "Copyright by...").
3. TỐI ƯU: Nếu là HTML, giữ nguyên các thẻ cấu trúc (h1, h2, p, figure).
4. TỐI ƯU: Đảm bảo nhịp điệu (pacing) nhanh, lôi cuốn. Không thêm bớt ý chính của sếp.
5. CẤM: Không thêm lời dẫn giải "Đây là bài viết đã làm sạch...". Chỉ trả về nội dung đã tối ưu.
""",
        )

        # R105: Semaphore to protect 2GB VPS RAM from concurrent LLM cleaning
        self._semaphore = asyncio.Semaphore(1)

        self._load_dictionary()

    def _load_dictionary(self):
        """Loads static and fuzzy rules from JSON."""
        try:
            with open(self.dictionary_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Layer 1: Flashtext Initialization
            static = data.get("static_keywords", {})
            for category, keywords in static.items():
                for kw in keywords:
                    # Replace keywords with empty string (Noise reduction)
                    self.keyword_processor.add_keyword(kw, "")
            
            # Layer 2: Fuzzy Patterns
            self.fuzzy_patterns = data.get("fuzzy_patterns", {})
            
            # Layer 3: Semantic Metadata
            self.semantic_categories = data.get("semantic_categories", [])
            
            logger.info(f"[Noise Shield] Dictionary loaded from {self.dictionary_path}")
        except Exception as e:
            logger.error(f"[Noise Shield] Failed to load dictionary: {e}")

    async def clean(self, text: str, mode: str = "aggressive", strip_markdown: bool = True, strip_html: bool = False) -> str:
        """
        Executes the 4-layer cleaning pipeline.
        
        Layers:
        0. HTML/Artifact Stripping (Deterministic)
        1. Markdown Stripping (HFS)
        2. Static Keywords (Flashtext)
        3. Fuzzy Keywords (RapidFuzz)
        4. Semantic Audit (AI)
        """
        if not text:
            return ""

        # --- LAYER 0: HTML & PLACEHOLDERS ---
        # Viral 2026: Stripping AI Preambles, Postambles & Markdown Fences
        text = RE_AI_CONVERSATION.sub('', text)
        text = RE_AI_POSTAMBLES.sub('', text)
        text = RE_MARKDOWN_FENCES.sub('', text)

        if strip_html:
            text = RE_HTML_TAGS.sub(' ', text)
            text = RE_IMAGE_PLACEHOLDERS.sub('', text)
        else:
            # Deterministic Artifact Stripping (Viral 2026)
            # Remove raw code blocks and scripts that shouldn't be in viral articles
            text = RE_CODE_ARTIFACTS.sub('', text)

            # Simple Link Density Mitigation: If a line/paragraph is just a link, it's often an artifact
            # We unwrap links that look like boilerplate
            def unwrap_spam_links(match):
                url = match.group(1)
                anchor = match.group(2)
                # If anchor is just the URL or generic "click here" / "read more"
                if url.strip('/') in anchor.strip('/') or any(kw in anchor.lower() for kw in ["click", "xem thêm", "read more", "tại đây"]):
                    return anchor
                return match.group(0)

            text = RE_ROGUE_LINKS.sub(unwrap_spam_links, text)

        # --- LAYER 1: DETERMINISTIC MARKDOWN (HFS) ---
        if strip_markdown:
            for pattern, subst in RE_MARKDOWN_CLEAN:
                text = pattern.sub(subst, text)
        
        cleaned_text = text
        
        # --- LAYER 2: FUZZY CLEANING ---
        # Split into tokens for fuzzy checking (limited to identified risky areas)
        # To avoid performance hit on large texts, we only fuzzy-check words > 5 chars
        words = cleaned_text.split()
        final_words = []
        
        for word in words:
            is_noise = False
            if len(word) > 4:
                word_lower = str(word).lower()
                for category, patterns in self.fuzzy_patterns.items():
                    for pattern in patterns:
                        if fuzz.ratio(word_lower, str(pattern).lower()) > 85:
                            is_noise = True
                            logger.debug(f"[Noise Shield] Fuzzy hit: '{word}' resembles '{pattern}'")
                            break
                    if is_noise: break
            
            if not is_noise:
                final_words.append(str(word))
        
        cleaned_text = " ".join(final_words)

        # --- LAYER 3: SEMANTIC AUDIT (OPTIONAL) ---
        # Only trigger for suspicious segments if mode is "aggressive"
        if mode == "aggressive" and len(cleaned_text) > 50:
            # We audit large chunks or the whole thing if it seems too noisy
            # For draft generation, we usually clean the whole output.
            noise_detected = await self._semantic_audit(cleaned_text)
            if noise_detected:
                # If the AI thinks it's pure junk, we might need a redo signal
                # For now, we just log it and return the best-effort clean text.
                logger.warning("[Noise Shield] Semantic Audit flagged the content as JUNK.")
        
        # Final pass: Collapse horizontal whitespace but preserve structure (V76.4)
        import unicodedata
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text) # Normalize paragraph breaks
        return unicodedata.normalize('NFC', cleaned_text.strip())

    async def viral_polish(self, content: str) -> str:
        """
        Phase 76.9: Viral 2026 Semantic Polish.
        Uses AI to surgically remove remaining noise and optimize for viral engagement.
        """
        if not content or len(content) < 50:
            return content

        async with self._semaphore:
            try:
                # Phase 76.9: Use TrinityBridge for the polish task with dedicated agent
                result = await trinity_bridge.run(
                    self._polish_agent,
                    content[:4000], # Limit context for speed and safety
                    model="gemini-2.0-flash"
                )

                polished = str(result.output).strip()

                # Sanitization pass: Remove markdown fences if the AI accidentally adds them
                if polished.startswith("```"):
                    polished = re.sub(r'^```[a-z]*\n', '', polished)
                    polished = re.sub(r'\n```$', '', polished)

                return polished if len(polished) > 10 else content
            except Exception as e:
                logger.error(f"[Noise Shield] Viral Polish failed: {e}")
                return content

    async def _semantic_audit(self, sample: str) -> bool:
        """Asks AI if the content is predominantly junk."""
        try:
            # Only audit first 500 chars to save tokens
            check_sample = sample[:500]
            result = await trinity_bridge.run(self._audit_agent, check_sample)
            verdict = str(result.output).strip().upper()
            return "JUNK" in verdict
        except Exception as e:
            logger.error(f"[Noise Shield] Semantic Audit error: {e}")
            return False

# Singleton instance
noise_cleaner = NoiseCleaner()
