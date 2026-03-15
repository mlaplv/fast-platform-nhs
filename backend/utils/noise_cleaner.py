import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional
from flashtext import KeywordProcessor
from rapidfuzz import fuzz
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from pydantic_ai import Agent

logger = logging.getLogger("api-gateway")

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

    async def clean(self, text: str, mode: str = "aggressive") -> str:
        """
        Executes the 3-layer cleaning pipeline.
        
        Layers:
        1. Flashtext (O(n) Direct Match)
        2. RapidFuzz (Similarity check for keyword variations)
        3. Semantic Proxy (AI evaluation for linguistic junk)
        """
        if not text:
            return ""

        # --- LAYER 1: DIRECT MATCH (FLASHTEXT) ---
        cleaned_text = self.keyword_processor.replace_keywords(text)
        
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
        
        # Final Regex pass for multiple whitespaces (V76.3)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        return cleaned_text

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
