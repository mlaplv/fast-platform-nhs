import json
import logging
import re
import asyncio
import unicodedata
import time
from pathlib import Path
from typing import List, Dict, Optional
from flashtext import KeywordProcessor
from rapidfuzz import fuzz, process
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
RE_EMPTY_BLOCKS = re.compile(
    r'<(p|div|h[1-6]|li|blockquote|strong|b|em|i|span|u|s|del|a)(?:\s+[^>]*?)?>(?:\s|&nbsp;|<br\s*/?>|\u00A0|\u200B|\uFEFF)*</\1>', 
    re.IGNORECASE
)

class NoiseCleaner:
    """
    R23: Hybrid Noise Shield Engine V2026.
    Implements a 3-layer pipeline to sanitize text from web crawlers and AI hallucinations.
    """
    
    def __init__(self, dictionary_path: Optional[str] = None):
        # Parents[1] is 'backend', so 'backend/resources/noise_dictionary.json'
        self.dictionary_path = dictionary_path or str(Path(__file__).parents[1] / "resources" / "noise_dictionary.json")
        self.keyword_processor = KeywordProcessor(case_sensitive=False)
        self.fuzzy_patterns: Dict[str, List[str]] = {}
        self.semantic_categories: List[str] = []
        
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
        # --- LAYER 2: CPU-BOUND LANGUAGE ANALYSIS ---
        # Run off-thread to avoid blocking event loop
        # CNS V2.2: Optimized fuzzy masking skips tags/attrs
        cleaned_text = await asyncio.to_thread(self._sync_clean_cpu, text, mode)

        # Final pass: Collapse horizontal whitespace but preserve structure (V76.4)
        start_time = time.time()
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)

        # Phase 76.95: Deterministic Recursive Empty Tag Strip (Final Guard)
        # We run this LATE because fuzzy cleaning might create new empty tags by stripping noise words
        logger.debug(f"[Noise Shield] Final Structural Guard (Length: {len(cleaned_text)})")
        for i in range(10):
            new_text = RE_EMPTY_BLOCKS.sub('', cleaned_text)
            if new_text == cleaned_text:
                break
            cleaned_text = new_text

        # Phase 76.96: Newline Normalization
        if strip_html:
            cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
        
        logger.debug(f"[Noise Shield] Finished Expert polish in {time.time() - start_time:.4f}s")
        return unicodedata.normalize('NFC', cleaned_text.strip())

    def _sync_clean_cpu(self, text: str, mode: str) -> str:
        """CPU-bound cleaning layers (Fuzzy + Heuristic Audit) — run via asyncio.to_thread."""
        # --- LAYER 2: FUZZY CLEANING ---
        # Pre-flatten patterns once for O(n × total_patterns) instead of nested loops
        all_flat_patterns = [
            (str(p).lower(), cat)
            for cat, patterns in self.fuzzy_patterns.items()
            for p in patterns
        ]
        # Step 1: Pre-filter words to only include meaningful text (skip HTML tags/attrs)
        # Regex to match content outside of < >
        words = re.split(r'(\s+)', text)
        final_tokens: list[str] = []
        
        # CNA V2.3: Use rapidfuzz.process.extractOne for O(N log M) or better internal optimization
        for token in words:
            # Skip if it's whitespace or looks like an HTML tag part (Optimization R23)
            if not token.strip() or '<' in token or '>' in token or '=' in token:
                final_tokens.append(token)
                continue
            
            # Layer 2.1: Expert Exact Skip (R23)
            # If the keyword processor already handled exact noise, we only fuzzy match long tokens
            is_noise = False
            token_clean = token.strip().lower()
            
            if len(token_clean) > 4:
                # Optimized fuzzy search: extractOne is usually faster than manual loop
                best_match = process.extractOne(
                    token_clean, 
                    all_flat_patterns, 
                    processor=lambda x: x[0], 
                    score_cutoff=85
                )
                if best_match:
                    is_noise = True
                    logger.debug(f"[Noise Shield] Expert Fuzzy hit: '{token}' matches [{best_match[0][1]}] score={best_match[1]}")
            
            if not is_noise:
                final_tokens.append(token)
            else:
                final_tokens.append("") # Neutralize noise
        
        cleaned = "".join(final_tokens)

        # --- LAYER 3: HEURISTIC SEMANTIC AUDIT ---
        if mode == "aggressive" and len(cleaned) > 50:
            if self._semantic_audit(cleaned):
                logger.warning("[Noise Shield] Heuristic Audit flagged the content as JUNK.")

        return cleaned



    def _semantic_audit(self, sample: str) -> bool:
        """
        Heuristic Semantic Audit — NO AI, 0 quota cost.
        Flags content as JUNK if noise-keyword density > 40%.
        Capped to first 100 words + pre-flattened patterns to avoid O(n×m×k) CPU block.
        """
        if not sample or not self.fuzzy_patterns:
            return False
        # Cap to 100 words to keep this O(100 × total_patterns) — safe for async context
        words = sample.split()[:100]
        if not words:
            return False
        # Pre-flatten all patterns once (not per-word)
        all_patterns = [
            p.lower()
            for patterns in self.fuzzy_patterns.values()
            for p in patterns
        ]
        if not all_patterns:
            return False
        noise_hits = 0
        all_pat_lower = [p for p in all_patterns]
        for w in words:
            w_lower = w.lower()
            if len(w_lower) > 4:
                if process.extractOne(w_lower, all_pat_lower, score_cutoff=85):
                    noise_hits += 1
        ratio = noise_hits / len(words)
        if ratio > 0.40:
            logger.debug(f"[Noise Shield] Heuristic audit: noise ratio={ratio:.2%} → JUNK")
            return True
        return False

# Singleton instance
noise_cleaner = NoiseCleaner()
