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

RE_MARKDOWN_CLEAN = [
    (re.compile(r'\*\*'), ''),
    (re.compile(r'__'), ''),
    (re.compile(r'#{1,6}\s+'), ''),
    (re.compile(r'!\[.*?\]\(.*?\)\s*'), ''),
    (re.compile(r'\[.*?\]\(.*?\)\s*'), ''),
    (re.compile(r'`{1,3}.*?`{1,3}', re.DOTALL), ''),
]

RE_CODE_ARTIFACTS = re.compile(r'<(pre|code|script|style)[^>]*>.*?</\1>', re.DOTALL | re.IGNORECASE)
RE_HTML_TAGS = re.compile(r'<[^>]+>')
RE_IMAGE_PLACEHOLDERS = re.compile(r'\[IMAGE_\d+\]')
RE_MARKDOWN_FENCES = re.compile(r'```[a-z]*|```', re.IGNORECASE)

class NoiseCleaner:
    """
    R23: Hybrid Noise Shield Engine V2026.
    Implements a 3-layer pipeline to sanitize text from web crawlers and AI hallucinations.
    """

    def __init__(self, dictionary_path: Optional[str] = None) -> None:
        self.dictionary_path: str = dictionary_path or str(Path(__file__).parents[1] / "resources" / "noise_dictionary.json")
        self.keyword_processor: KeywordProcessor = KeywordProcessor(case_sensitive=False)
        self.fuzzy_patterns: Dict[str, List[str]] = {}
        self.all_flat_patterns: List[tuple[str, str]] = []
        self.all_pat_lower: List[str] = []
        self.semantic_categories: List[str] = []
        self._fuzzy_cache: Dict[str, bool] = {}
        self._load_dictionary()

    def _load_dictionary(self) -> None:
        try:
            with open(self.dictionary_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            static = data.get("static_keywords", {})
            for keywords in static.values():
                for kw in keywords:
                    self.keyword_processor.add_keyword(kw, " ")

            self.fuzzy_patterns = data.get("fuzzy_patterns", {})
            self.all_flat_patterns = [
                (str(p).lower(), cat)
                for cat, patterns in self.fuzzy_patterns.items()
                for p in patterns
            ]
            self.all_pat_lower = [p for p, _ in self.all_flat_patterns]
            self.semantic_categories = data.get("semantic_categories", [])
            logger.info(f"[Noise Shield] Dictionary loaded from {self.dictionary_path}")
        except Exception as e:
            logger.error(f"[Noise Shield] Failed to load dictionary: {e}")

    async def clean(
        self,
        text: str,
        mode: str = "aggressive",
        strip_markdown: bool = True,
        strip_html: bool = False,
        options: Optional[Dict[str, bool]] = None
    ) -> str:
        if not text:
            return ""

        text = RE_MARKDOWN_FENCES.sub('', text)
        if strip_markdown:
            for pattern, replacement in RE_MARKDOWN_CLEAN:
                text = pattern.sub(replacement, text)

        if strip_html:
            text = RE_HTML_TAGS.sub(' ', text)
            text = RE_IMAGE_PLACEHOLDERS.sub('', text)
        else:
            text = RE_CODE_ARTIFACTS.sub('', text)

        cleaned_text = await asyncio.to_thread(self._sync_clean_cpu, text, mode)
        start_time = time.time()
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)

        if not strip_html and ('<' in cleaned_text and '>' in cleaned_text):
            cleaned_text = self._global_artifact_dedup(cleaned_text)
            cleaned_text = await asyncio.to_thread(self._structural_tree_pruning, cleaned_text, options)
            if options is None or options.get("validateHtml5", True):
                cleaned_text = await asyncio.to_thread(self._validate_and_sanitize_html5, cleaned_text)

        if strip_html:
            cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
        else:
            cleaned_text = re.sub(r'(?i)(<br\s*/?>\s*){2,}', '<br>', cleaned_text)

        logger.debug(f"[Noise Shield] Finished Expert polish in {time.time() - start_time:.4f}s")
        return unicodedata.normalize('NFC', cleaned_text.strip())

    def _global_artifact_dedup(self, html_str: str) -> str:
        BLOCK_TAGS = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'figcaption', 'td', 'th', 'dt', 'dd', 'figure'}
        MEDIA_TAGS = {'img', 'video', 'audio', 'iframe', 'canvas', 'svg', 'picture'}

        def _has_media(el: html.HtmlElement) -> bool:
            return any(el.find('.//' + tag) is not None for tag in MEDIA_TAGS)

        def _extract_text(el: html.HtmlElement) -> str:
            return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip().lower()

        try:
            root = html.fragment_fromstring(f"<div>{html_str}</div>", create_parent=False)
        except Exception:
            return html_str

        seen: set[str] = set()
        to_drop: list[html.HtmlElement] = []

        for el in root.getchildren():
            if _has_media(el):
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
        return re.sub(r'^<div>(.*)</div>$', r'\1', result, flags=re.DOTALL)

    def _structural_tree_pruning(self, html_content: str, options: Optional[Dict[str, bool]] = None) -> str:
        try:
            opts = options or {}
            strip_font = opts.get("stripFont", True)
            strip_align = opts.get("stripAlign", True)
            strip_redundant = opts.get("stripRedundantWrappers", True)
            strip_empty = opts.get("stripEmpty", True)
            dedup = opts.get("deduplicateContent", True)
            strip_links = opts.get("stripLinks", True)

            containers = {
                'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote',
                'strong', 'b', 'em', 'i', 'span', 'u', 's', 'del', 'a', 'section',
                'article', 'nav', 'footer', 'header', 'table', 'tr', 'td', 'th',
                'thead', 'tbody', 'tfoot', 'ul', 'ol', 'figure'
            }
            whitelisted = {
                'img', 'iframe', 'embed', 'video', 'audio', 'canvas', 'svg',
                'input', 'button', 'hr', 'br'
            }

            fragment = html.fragment_fromstring(f"<div>{html_content}</div>", create_parent=False)

            for element in reversed(list(fragment.iter())):
                if element == fragment:
                    continue

                tag = (element.tag or '').lower()
                if not tag:
                    continue

                if strip_font or strip_align:
                    style = element.get('style')
                    if style:
                        parts = [
                            s.strip() for s in style.split(';')
                            if s.strip() and not (
                                (strip_font and s.strip().lower().startswith('font-family')) or
                                (strip_align and s.strip().lower().startswith('text-align'))
                            )
                        ]
                        if parts:
                            element.set('style', '; '.join(parts))
                        else:
                            element.attrib.pop('style', None)

                if strip_links and tag == 'a':
                    element.drop_tag()
                    continue

                if strip_redundant and tag in ('span', 'div') and not element.attrib:
                    element.drop_tag()
                    continue

                has_content = False
                text = (element.text or "").replace('\u00A0', '').replace('\u200B', '').replace('\uFEFF', '').replace('&nbsp;', '')
                if re.sub(r'\s+', '', text):
                    has_content = True
                else:
                    if len(element) > 0:
                        has_content = any(c.tag in whitelisted or c.tag in containers for c in element)
                    elif tag in whitelisted:
                        has_content = True

                if tag in containers:
                    is_effectively_empty = not re.sub(r'\s+', '', text)
                    if is_effectively_empty:
                        for child in element:
                            if child.tag in whitelisted and child.tag != 'br':
                                is_effectively_empty = False
                                break
                            elif child.tag in containers and child.getparent() == element:
                                is_effectively_empty = False
                                break
                            tail = (child.tail or "").replace('\u00A0', '').replace('\u200B', '').replace('\uFEFF', '').replace('&nbsp;', '')
                            if re.sub(r'\s+', '', tail):
                                is_effectively_empty = False
                                break
                        if is_effectively_empty:
                            has_content = False

                if not has_content and strip_empty:
                    parent = element.getparent()
                    if parent is not None:
                        if element.tail:
                            prev = element.getprevious()
                            if prev is not None:
                                prev.tail = (prev.tail or "") + element.tail
                            else:
                                parent.text = (parent.text or "") + element.tail
                        parent.remove(element)

            if dedup:
                for block in fragment.iter():
                    if block.tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'figure', 'figcaption'):
                        to_remove = []
                        last_child = None
                        for child in block:
                            if child.tag == 'br':
                                continue
                            if last_child is not None and child.tag == last_child.tag and child.tag not in ('img', 'iframe', 'video', 'audio'):
                                curr_text = "".join(child.itertext()).strip()
                                prev_text = "".join(last_child.itertext()).strip()
                                if len(curr_text) > 30 and curr_text == prev_text:
                                    to_remove.append(child)
                                    prev = child.getprevious()
                                    while prev is not None and prev != last_child:
                                        if prev.tag == 'br':
                                            to_remove.append(prev)
                                        prev = prev.getprevious()
                                    continue
                            last_child = child
                        for el in to_remove:
                            if el.getparent() is not None:
                                el.drop_tree()

            if dedup:
                dedup_tags = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div', 'blockquote', 'figure', 'figcaption'}
                blocks = [
                    el for el in fragment.iter()
                    if el.tag in dedup_tags and not any(child.tag in dedup_tags for child in el.iterdescendants())
                ]
                signatures = [(el.tag, re.sub(r'\s+', ' ', "".join(el.itertext()).strip().lower())) for el in blocks]
                to_drop = set()

                seen_long = []
                for i, (tag, text) in enumerate(signatures):
                    if len(text) > 30:
                        is_dup = False
                        for seen in seen_long:
                            if text == seen:
                                is_dup = True
                                break
                            elif len(text) > 150 and len(seen) > 150:
                                if fuzz.ratio(text, seen) >= 90 or fuzz.partial_ratio(text, seen) >= 90:
                                    is_dup = True
                                    break
                        if is_dup:
                            logger.info(f"🛡️ [Noise Shield] Dropping duplicate: {text[:50]}...")
                            to_drop.add(blocks[i])
                        else:
                            seen_long.append(text)

                seen_seqs = set()
                for i in range(len(signatures) - 1):
                    tag1, t1 = signatures[i]
                    tag2, t2 = signatures[i+1]
                    if not t1 or not t2:
                        continue
                    seq = ((tag1, t1), (tag2, t2))
                    if seq in seen_seqs:
                        logger.info(f"🛡️ [Noise Shield] Dropping sequence duplicate: {t1[:30]}...")
                        to_drop.add(blocks[i])
                    else:
                        seen_seqs.add(seq)

                for el in to_drop:
                    if el.getparent() is not None:
                        el.drop_tree()

            if strip_empty or dedup:
                for element in reversed(list(fragment.iter())):
                    if element == fragment:
                        continue
                    if element.tag in ('ul', 'ol', 'li', 'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                        has_text = bool((element.text or "").replace('\u00A0', '').strip())
                        if not has_text and len(element) == 0:
                            element.drop_tree()

            result = html.tostring(fragment, encoding='unicode', method='html')
            return result[5:-6] if result.startswith('<div>') and result.endswith('</div>') else result
        except Exception as e:
            logger.error(f"[Noise Shield] Structural pruning failed: {e}", exc_info=True)
            return html_content

    def _validate_and_sanitize_html5(self, html_content: str) -> str:
        """
        Phase 91.0: HTML5 Parser & Validator (CNS Elite V2.5).
        Parses HTML content, detects syntax/nesting errors, and returns valid HTML5.
        """
        if not html_content or '<' not in html_content:
            return html_content

        try:
            parser = html.HTMLParser(recover=True, remove_blank_text=False)
            root = html.fragment_fromstring(f"<div>{html_content}</div>", parser=parser)
            
            if parser.error_log:
                for error in parser.error_log:
                    logger.warning(f"[HTML5 Validator] Parser recovered on line {error.line}, col {error.column}: {error.message}")
            
            BLOCK_TAGS = {
                'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li',
                'blockquote', 'section', 'article', 'nav', 'footer', 'header',
                'table', 'thead', 'tbody', 'tr', 'td', 'th', 'figure', 'figcaption'
            }
            INLINE_TAGS = {'span', 'strong', 'b', 'em', 'i', 'u', 's', 'del', 'a', 'small'}

            changed = True
            pass_count = 0
            while changed and pass_count < 5:
                changed = False
                pass_count += 1
                
                for element in reversed(list(root.iter())):
                    if element == root:
                        continue
                    tag = (element.tag or '').lower()
                    if not tag:
                        continue

                    if tag in INLINE_TAGS:
                        if any((c.tag or '').lower() in BLOCK_TAGS for c in element.iterchildren()):
                            logger.info(f"[HTML5 Validator] Fixing block nested inside inline <{tag}>")
                            element.drop_tag()
                            changed = True
                            break

                    if tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
                        if any((c.tag or '').lower() in BLOCK_TAGS for c in element.iterchildren()):
                            logger.info(f"[HTML5 Validator] Fixing block nested inside heading <{tag}>")
                            element.drop_tag()
                            changed = True
                            break

                    if tag == 'p':
                        if any((c.tag or '').lower() in BLOCK_TAGS for c in element.iterchildren()):
                            logger.info(f"[HTML5 Validator] Converting nested block <p> to <div>")
                            element.tag = 'div'
                            changed = True
                            break
                            
            result = html.tostring(root, encoding='unicode', method='html')
            return result[5:-6] if result.startswith('<div>') and result.endswith('</div>') else result
        except Exception as e:
            logger.error(f"[HTML5 Validator] Validation failed: {e}", exc_info=True)
            return html_content

    def _sync_clean_cpu(self, text: str, mode: str) -> str:
        parts = re.split(r'(<[^>]+>)', text)
        for i in range(len(parts)):
            segment = parts[i]
            if not segment or i % 2 != 0:
                continue

            segment = self.keyword_processor.replace_keywords(segment)
            tokens = re.split(r'(\s+)', segment)
            final_tokens: list[str] = []

            for token in tokens:
                if not token.strip():
                    final_tokens.append(token)
                    continue

                token_clean = token.strip().lower()
                if token_clean in self._fuzzy_cache:
                    final_tokens.append("" if self._fuzzy_cache[token_clean] else token)
                    continue

                is_noise = False
                if len(token_clean) > 4:
                    best_match = process.extractOne(token_clean, self.all_pat_lower, score_cutoff=85)
                    if best_match:
                        is_noise = True
                        logger.debug(f"[Noise Shield] Expert Fuzzy hit: '{token}' matches '{best_match[0]}' score={best_match[1]}")

                self._fuzzy_cache[token_clean] = is_noise
                if len(self._fuzzy_cache) > 2000:
                    self._fuzzy_cache.clear()

                final_tokens.append("" if is_noise else token)

            parts[i] = "".join(final_tokens)

        cleaned = "".join(parts)
        if mode == "aggressive" and len(cleaned) > 50:
            if self._semantic_audit(cleaned):
                logger.warning("[Noise Shield] Heuristic Audit flagged the content as JUNK.")
        return cleaned

    def _semantic_audit(self, sample: str) -> bool:
        if not sample or not self.fuzzy_patterns or not self.all_pat_lower:
            return False
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
