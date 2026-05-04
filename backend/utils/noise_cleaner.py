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
RE_MARKDOWN_CLEAN = [
    (re.compile(r'\*\*'), ''),           # Bold **
    (re.compile(r'__'), ''),             # Bold __
    (re.compile(r'#{1,6}\s+'), ''),     # Headings
    (re.compile(r'!\[.*?\]\(.*?\)\s*'), ''), # Images
    (re.compile(r'\[.*?\]\(.*?\)\s*'), ''),   # Links
    (re.compile(r'`{1,3}.*?`{1,3}', re.DOTALL), ''), # Inline code / fences
]

# Phase 76.9: Deterministic HTML Artifact Strippers
RE_CODE_ARTIFACTS = re.compile(r'<(pre|code|script|style)[^>]*>.*?</\1>', re.DOTALL | re.IGNORECASE)
RE_HTML_TAGS = re.compile(r'<[^>]+>')
RE_IMAGE_PLACEHOLDERS = re.compile(r'\[IMAGE_\d+\]')
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
        self._fuzzy_cache: Dict[str, bool] = {} # Phase 84.1: Expert Fuzzy Cache (O(1) repeat hits)

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

    async def clean(self, text: str, mode: str = "aggressive", strip_markdown: bool = True, strip_html: bool = False, options: Optional[Dict] = None) -> str:
        """
        Executes the 4-layer cleaning pipeline.

        Layers:
        0. HTML/Artifact Stripping (Deterministic)
        1. Markdown Stripping (HFS)
        2. Static Keywords (Flashtext)
        3. Fuzzy Keywords (RapidFuzz)
        4. Semantic Audit (AI)
        """
        # Phase 0: Validate
        if not text:
            return ""

        # DEBUG DUMP
        try:
            with open('/app/backend/scratch/noise_clean_input.html', 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception:
            pass

        # --- LAYER 0: ARTIFACT STRIPPING ---
        text = RE_MARKDOWN_FENCES.sub('', text)

        if strip_markdown:
            for pattern, replacement in RE_MARKDOWN_CLEAN:
                text = pattern.sub(replacement, text)

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
            cleaned_text = self._global_artifact_dedup(cleaned_text)
            cleaned_text = await asyncio.to_thread(self._structural_tree_pruning, cleaned_text, options)

        # Phase 76.96: Newline Normalization
        if strip_html:
            cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
        else:
            # Collapse consecutive <br> tags left by pruning
            cleaned_text = re.sub(r'(?i)(<br\s*/?>\s*){2,}', '<br>', cleaned_text)

        logger.debug(f"[Noise Shield] Finished Expert polish in {time.time() - start_time:.4f}s")
        return unicodedata.normalize('NFC', cleaned_text.strip())

    def _global_artifact_dedup(self, html_str: str) -> str:
        """
        Phase 88.7: Global DOM-Level Artifact Deduplication (Elite V2.3).
        Uses lxml DOM traversal to accurately find and drop duplicate text blocks
        regardless of their wrapping tag (figcaption, p, div, etc.).
        Media elements (img, video, iframe) are NEVER removed.
        """
        BLOCK_TAGS = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                      'li', 'blockquote', 'figcaption', 'td', 'th', 'dt', 'dd', 'figure'}
        MEDIA_TAGS = {'img', 'video', 'audio', 'iframe', 'canvas', 'svg', 'picture'}

        def _has_media(el) -> bool:
            for tag in MEDIA_TAGS:
                if el.find('.//' + tag) is not None:
                    return True
            return False

        def _extract_text(el) -> str:
            return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip().lower()

        try:
            # Wrap in a div to ensure we can iterate over top-level fragments
            root = html.fragment_fromstring(f"<div>{html_str}</div>", create_parent=False)
        except Exception:
            return html_str

        seen: set = set()
        to_drop: list = []

        # Iterate ONLY over top-level children of our wrapper
        for el in root.getchildren():
            # Never touch elements containing media at this level
            if _has_media(el):
                # Still register their text to catch downstream duplicates
                txt = _extract_text(el)
                if len(txt) > 30:
                    seen.add(txt)
                continue

            tag = el.tag if isinstance(el.tag, str) else ''
            if tag not in BLOCK_TAGS:
                continue

            txt = _extract_text(el)
            if len(txt) <= 30:
                continue

            if txt in seen:
                logger.info(f"🛡️ [Noise Shield] Dropping DOM artifact: {txt[:60]}...")
                to_drop.append(el)
            else:
                seen.add(txt)

        for el in to_drop:
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)

        result = html.tostring(root, encoding='unicode')
        # Strip the wrapper <div> we added
        result = re.sub(r'^<div>(.*)</div>$', r'\1', result, flags=re.DOTALL)
        return result

    def _structural_tree_pruning(self, html_content: str, options: Optional[Dict] = None) -> str:
        """
        NASP (Neural-Agnostic Structural Pruner) - Elite V2.2
        Linear-time structural pruning using lxml C-backend.
        Removes all empty nodes (including nested) in a single bottom-up pass.
        Now natively integrates Neural Clean Checklist (V88.5).
        """
        try:
            opts = options or {}
            strip_font = opts.get("stripFont", True)
            strip_align = opts.get("stripAlign", True)
            strip_redundant = opts.get("stripRedundantWrappers", True)
            strip_empty = opts.get("stripEmpty", True)
            dedup = opts.get("deduplicateContent", True)
            # Container tags that should be removed if they are effectively empty
            containers = {
                'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote',
                'strong', 'b', 'em', 'i', 'span', 'u', 's', 'del', 'a', 'section',
                'article', 'nav', 'footer', 'header', 'table', 'tr', 'td', 'th',
                'thead', 'tbody', 'tfoot', 'ul', 'ol', 'figure'
            }
            # Tags that always count as content (void tags or media)
            whitelisted = {
                'img', 'iframe', 'embed', 'video', 'audio', 'canvas', 'svg',
                'input', 'button', 'hr', 'br'
            }
            # Note: 'br' is now in whitelisted to prevent line breaks from being stripped, 
            # but we explicitly ignore it when checking if a container is effectively empty.

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

                # Special case for BR: We only keep BR if it's NOT the only thing in a container,
                # or if it's at the top level. But actually, in NASP, we prune it if it's "empty content".
                # Actually, Tiptap uses <br> for empty lines.
                # If we prune <br>, we might lose formatting.
                # However, the user wants <h1><strong><br></strong></h1> GONE.

                # 0. Strip Styles (Checklist)
                if strip_font or strip_align:
                    style = element.get('style')
                    if style:
                        new_style = []
                        for s in style.split(';'):
                            s = s.strip()
                            if not s: continue
                            if strip_font and s.lower().startswith('font-family'): continue
                            if strip_align and s.lower().startswith('text-align'): continue
                            new_style.append(s)
                        if new_style:
                            element.set('style', '; '.join(new_style))
                        else:
                            element.attrib.pop('style', None)

                # 0.5. Prune Redundant Tags (Checklist)
                if strip_redundant and tag in ('span', 'div') and not element.attrib:
                    element.drop_tag()
                    continue

                # Check if element is effectively empty
                has_content = False

                # 1. Check text content (ignoring whitespace and invisible noise)
                if element.text:
                    # Thorough strip of all known invisible characters
                    clean_text = element.text.replace('\u00A0', '').replace('\u200B', '').replace('\uFEFF', '').replace('&nbsp;', '')
                    clean_text = re.sub(r'\s+', '', clean_text)
                    if clean_text:
                        has_content = True

                # 2. Check for meaningful children
                if not has_content:
                    if len(element) > 0:
                        for child in element:
                            # A child is meaningful if it's in the whitelist OR it's a container that survived pruning
                            if child.tag in whitelisted or child.tag in containers:
                                has_content = True
                                break
                    elif tag in whitelisted:
                        has_content = True

                # 3. Aggressive Container Guard: If it's a container, and it ONLY contains <br> or whitespace, prune it.
                if tag in containers:
                    # Check if it has any REAL content (not just BR)
                    is_effectively_empty = True

                    # Text check
                    text = (element.text or "").replace('\u00A0', '').replace('\u200B', '').replace('\uFEFF', '').replace('&nbsp;', '')
                    if re.sub(r'\s+', '', text):
                        is_effectively_empty = False

                    # Children check
                    if is_effectively_empty:
                        for child in element:
                            if child.tag in whitelisted and child.tag != 'br':
                                is_effectively_empty = False
                                break
                            elif child.tag in containers and child.getparent() == element:
                                # If the child is a container, it must have survived pruning (meaning it has content)
                                is_effectively_empty = False
                                break
                            if child.tail and re.sub(r'\s+', '', child.tail.replace('\u00A0', '').replace('\u200B', '').replace('\uFEFF', '').replace('&nbsp;', '')):
                                is_effectively_empty = False
                                break

                    if is_effectively_empty:
                        has_content = False

                if not has_content and strip_empty:
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

            # 3.5 Intra-Block Duplicate Child Pruner (Fix for 5x copies of inline tags)
            if dedup:
                for block in fragment.iter():
                    if block.tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'figure', 'figcaption'):
                        to_remove = []
                        last_child = None
                        for child in block:
                            if child.tag == 'br': continue
                            
                            if last_child is not None and child.tag == last_child.tag and child.tag not in ('img', 'iframe', 'video', 'audio'):
                                curr_text = "".join(child.itertext()).strip()
                                prev_text = "".join(last_child.itertext()).strip()
                                
                                if len(curr_text) > 30 and curr_text == prev_text:
                                    to_remove.append(child)
                                    # Find any <br> between last_child and child
                                    prev = child.getprevious()
                                    while prev is not None and prev != last_child:
                                        if prev.tag == 'br': to_remove.append(prev)
                                        prev = prev.getprevious()
                                    continue
                            last_child = child
                            
                        for el in to_remove:
                            if el.getparent() is not None:
                                el.drop_tree()

            # 4. Neural Deduplication (Checklist)
            if dedup:
                dedup_tags = ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div', 'blockquote', 'figure', 'figcaption')
                all_blocks = [el for el in list(fragment.iter()) if el.tag in dedup_tags]
                
                blocks = []
                for el in all_blocks:
                    has_block_child = any(child.tag in dedup_tags for child in el.iterdescendants())
                    if not has_block_child:
                        blocks.append(el)

                signatures = []
                for el in blocks:
                    text = "".join(el.itertext()).strip().lower()
                    text = re.sub(r'\s+', ' ', text)
                    signatures.append((el.tag, text))

                to_drop = set()
                
                # Rule 1: Single-element dedup (for long paragraphs > 30 chars)
                seen_long = []
                for i, (tag, text) in enumerate(signatures):
                    if len(text) > 30:
                        is_dup = False
                        for seen in seen_long:
                            if text == seen:
                                is_dup = True
                                break
                            # Fuzzy matching for large paragraphs to catch 90% similar modified copies
                            elif len(text) > 150 and len(seen) > 150:
                                if fuzz.ratio(text, seen) >= 90 or fuzz.partial_ratio(text, seen) >= 90:
                                    is_dup = True
                                    break
                                
                        if is_dup:
                            logger.info(f"🛡️ [Noise Shield] Dropping single-element duplicate: {text[:50]}...")
                            to_drop.add(blocks[i])
                        else:
                            seen_long.append(text)

                # Rule 2: Sequence-level dedup (Window size 2) for structure
                seen_seqs = set()
                for i in range(len(signatures) - 1):
                    tag1, t1 = signatures[i]
                    tag2, t2 = signatures[i+1]
                    if not t1 or not t2: continue
                    seq = ((tag1, t1), (tag2, t2))
                    if seq in seen_seqs:
                        logger.info(f"🛡️ [Noise Shield] Dropping sequence duplicate: {t1[:30]}... / {t2[:30]}...")
                        to_drop.add(blocks[i])
                        to_drop.add(blocks[i+1])
                    else:
                        seen_seqs.add(seq)

                for el in to_drop:
                    if el.getparent() is not None:
                        el.drop_tree()
                        
            # 5. Final Empty Prune (Cleanup wrappers left empty by dedup)
            if strip_empty or dedup:
                for element in reversed(list(fragment.iter())):
                    if element == fragment: continue
                    if element.tag in ('ul', 'ol', 'li', 'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                        has_text = bool((element.text or "").replace('\u00A0', '').strip())
                        if not has_text and len(element) == 0:
                            element.drop_tree()

            # Convert back to string and remove our wrapper div
            result = html.tostring(fragment, encoding='unicode', method='html')
            # Surgical removal of wrapper div to preserve whatever was inside
            if result.startswith('<div>'):
                result = result[5:]
            if result.endswith('</div>'):
                result = result[:-6]
            return result
        except Exception as e:
            logger.error(f"[Noise Shield] Structural pruning failed: {e}", exc_info=True)
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

                token_clean = token.strip().lower()

                # Phase 84.1: Expert Fuzzy Cache (O(1) repeat hits)
                if token_clean in self._fuzzy_cache:
                    if self._fuzzy_cache[token_clean]:
                        final_tokens.append("")
                    else:
                        final_tokens.append(token)
                    continue

                is_noise = False

                # Only fuzzy match long tokens to avoid false positives (R23)
                if len(token_clean) > 4:
                    best_match = process.extractOne(
                        token_clean,
                        self.all_pat_lower,
                        score_cutoff=85
                    )
                    if best_match:
                        is_noise = True
                        logger.debug(f"[Noise Shield] Expert Fuzzy hit: '{token}' matches '{best_match[0]}' score={best_match[1]}")

                # Update cache
                self._fuzzy_cache[token_clean] = is_noise

                # Cleanup cache if too large to prevent memory leak
                if len(self._fuzzy_cache) > 2000:
                    self._fuzzy_cache.clear()

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
