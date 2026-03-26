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
from lxml import html

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
        # Parents[1] is 'backend', so 'backend/resources/noise_dictionary.json'
        self.dictionary_path = dictionary_path or str(Path(__file__).parents[1] / "resources" / "noise_dictionary.json")
        self.keyword_processor = KeywordProcessor(case_sensitive=False)
        self.fuzzy_patterns: Dict[str, List[str]] = {}
        self.all_flat_patterns: List[tuple[str, str]] = []
        self.all_pat_lower: List[str] = []
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
                    # Replace keywords with space (Noise reduction)
                    # Note: Using "" (empty string) in Flashtext often causes it to skip replacement.
                    self.keyword_processor.add_keyword(kw, " ")

            # Layer 2: Fuzzy Patterns
            self.fuzzy_patterns = data.get("fuzzy_patterns", {})

            # Pre-flatten patterns for O(n) lookup instead of repeated flattening (Elite V2.2 Optimization)
            self.all_flat_patterns = [
                (str(p).lower(), cat)
                for cat, patterns in self.fuzzy_patterns.items()
                for p in patterns
            ]
            self.all_pat_lower = [p for p, _ in self.all_flat_patterns]

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

        # Phase 76.95: Deterministic Structural Tree Pruning (NASP - Elite V2.2)
        # Replacing legacy regex loops with high-performance DOM pruning
        # Run in thread to avoid blocking event loop on large HTML (Optimization R23)
        if not strip_html and ('<' in cleaned_text and '>' in cleaned_text):
            cleaned_text = await asyncio.to_thread(self._structural_tree_pruning, cleaned_text)

        # Phase 76.96: Newline Normalization
        if strip_html:
            cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)

        logger.debug(f"[Noise Shield] Finished Expert polish in {time.time() - start_time:.4f}s")
        return unicodedata.normalize('NFC', cleaned_text.strip())

    def _structural_tree_pruning(self, html_content: str) -> str:
        """
        NASP (Neural-Agnostic Structural Pruner) - Elite V2.2
        Linear-time structural pruning using lxml C-backend.
        Removes all empty nodes (including nested) in a single bottom-up pass.
        """
        try:
            # Container tags that should be removed if they are effectively empty
            containers = {
                'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote',
                'strong', 'b', 'em', 'i', 'span', 'u', 's', 'del', 'a', 'section',
                'article', 'nav', 'footer', 'header', 'table', 'tr', 'td', 'th',
                'thead', 'tbody', 'tfoot'
            }
            # Tags that always count as content (void tags or media)
            whitelisted = {
                'img', 'iframe', 'embed', 'video', 'audio', 'canvas', 'svg',
                'input', 'button', 'hr', 'br'
            }

            # Wrap in a div to handle fragments correctly
            fragment = html.fragment_fromstring(f"<div>{html_content}</div>", create_parent=False)

            # Bottom-up traversal to prune empty nodes
            for element in reversed(list(fragment.iter())):
                # Skip the root div we added
                if element == fragment:
                    continue

                tag = element.tag
                if not isinstance(tag, str):
                    continue
                tag = tag.lower()

                # Check if element is effectively empty
                has_content = False

                # 1. Check text content (ignoring whitespace and invisible noise)
                if element.text:
                    clean_text = element.text.strip().replace('\u00A0', '').replace('\u200B', '').replace('\uFEFF', '')
                    if clean_text:
                        has_content = True

                # 2. Check for meaningful children
                # If we have children that are not in the 'whitelisted' list of empty-but-meaningful tags,
                # we consider them as content.
                if not has_content:
                    if len(element) > 0:
                        for child in element:
                            # A child is meaningful if:
                            # a) It's in the whitelist (like <img> or <br>)
                            # b) It's a container that wasn't pruned (meaning it had content)
                            if child.tag in whitelisted or child.tag in containers:
                                # Wait, if it's a container that wasn't pruned, it means it HAS content.
                                # If it was a container and it IS still here in reversed order,
                                # it means it HAS content (otherwise it would have been pruned already).
                                has_content = True
                                break
                    elif tag in whitelisted:
                        has_content = True

                # Special case: If it's a container, it MUST have either real text
                # or meaningful children (not just <br>/<hr>).
                if tag in containers:
                    # Re-evaluate for containers: ignore <br>/<hr> as meaningful children
                    # for the purpose of pruning the container itself.
                    is_effectively_empty = False

                    # Check text again
                    text_exists = False
                    if element.text:
                        if element.text.strip().replace('\u00A0', '').replace('\u200B', '').replace('\uFEFF', ''):
                            text_exists = True

                    if not text_exists:
                        # Check if it has any children OTHER than <br> or <hr>
                        has_real_child = False
                        for child in element:
                            if child.tag not in ('br', 'hr'):
                                has_real_child = True
                                break
                        if not has_real_child:
                            is_effectively_empty = True

                    if is_effectively_empty:
                        has_content = False

                if not has_content:
                    parent = element.getparent()
                    if parent is not None:
                        # Preserve tail text when removing element
                        if element.tail:
                            prev = element.getprevious()
                            if prev is not None:
                                prev.tail = (prev.tail or "") + element.tail
                            else:
                                parent.text = (parent.text or "") + element.tail
                        parent.remove(element)

            # Convert back to string and remove our wrapper div
            result = html.tostring(fragment, encoding='unicode', method='html')
            if result.startswith('<div>'):
                result = result[5:]
            if result.endswith('</div>'):
                result = result[:-6]
            return result
        except Exception as e:
            logger.error(f"[Noise Shield] Structural pruning failed: {e}")
            return html_content

    def _sync_clean_cpu(self, text: str, mode: str) -> str:
        """CPU-bound cleaning layers (Fuzzy + Heuristic Audit) — run via asyncio.to_thread."""
        # --- LAYER 2: HYBRID EXACT & FUZZY CLEANING ---
        # Phase 84.1: Split by HTML tags to protect attributes (Elite V2.2)
        # Content segments are at even indices, Tags at odd indices
        parts = re.split(r'(<[^>]+>)', text)

        for i in range(len(parts)):
            segment = parts[i]
            if not segment or i % 2 != 0: # Skip empty or HTML tags
                continue

            # Layer 2.1: Expert Exact Skip (Flashtext - O(N))
            # Removes multi-word exact matches efficiently
            segment = self.keyword_processor.replace_keywords(segment)

            # Layer 2.2: Expert Fuzzy Search (RapidFuzz - O(N log M))
            # Splitting by whitespace to check individual tokens for fuzzy noise
            tokens = re.split(r'(\s+)', segment)
            final_tokens: list[str] = []

            for token in tokens:
                if not token.strip():
                    final_tokens.append(token)
                    continue

                is_noise = False
                token_clean = token.strip().lower()

                # Only fuzzy match long tokens to avoid false positives (R23)
                if len(token_clean) > 4:
                    best_match = process.extractOne(
                        token_clean,
                        self.all_flat_patterns,
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

            parts[i] = "".join(final_tokens)

        cleaned = "".join(parts)

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
        if not sample or not self.fuzzy_patterns or not self.all_pat_lower:
            return False
        # Cap to 100 words to keep this O(100 × total_patterns) — safe for async context
        words = sample.split()[:100]
        if not words:
            return False

        noise_hits = 0
        for w in words:
            w_lower = w.lower()
            if len(w_lower) > 4:
                if process.extractOne(w_lower, self.all_pat_lower, score_cutoff=85):
                    noise_hits += 1
        ratio = noise_hits / len(words)
        if ratio > 0.40:
            logger.debug(f"[Noise Shield] Heuristic audit: noise ratio={ratio:.2%} → JUNK")
            return True
        return False

# Singleton instance
noise_cleaner = NoiseCleaner()
