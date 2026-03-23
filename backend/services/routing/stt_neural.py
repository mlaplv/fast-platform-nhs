import logging
import asyncio
import numpy as np
import re
from typing import Dict, Optional, Tuple, List, Any
from rapidfuzz import fuzz
from backend.utils.text import normalize_vn
from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
from backend.services.xohi_memory import xohi_memory
from .stt_utils import get_norm

logger = logging.getLogger("api-gateway")
RE_DIGIT = re.compile(r'\d+')

class NeuralLocalCorrector:
    """
    T1.2 - Local Neural Sieve (2026 Viral Strategy).
    Uses multilingual embeddings to match transcripts against learned 'wrong' words semantically.
    """
    def __init__(self):
        self.encoder = None
        self._embedding_cache = {} # { "wrong_phrase": vector }
        self._norm_key_cache = {} # { "raw_key": "norm_key" }
        self._cache_access_count = 0
        self._sorted_keys_cache = ([], 0) # (keys, hash_of_dict)

    async def _ensure_encoder(self) -> None:
        if self.encoder is None:
            loop = asyncio.get_event_loop()
            self.encoder = await loop.run_in_executor(None, get_shared_encoder)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    async def correct(self, transcript: str, user_dict: Dict[str, str]) -> Tuple[str, float]:
        if not user_dict: return transcript, 0.0
        await self._ensure_encoder()
        if self.encoder is None: return transcript, 0.0

        loop = asyncio.get_event_loop()
        self._cache_access_count += 1
        dict_hash = hash(frozenset(user_dict.items()))

        if self._cache_access_count > 50 or len(self._embedding_cache) > 200:
            self._cache_access_count = 0
            active_keys = set(user_dict.keys())
            self._embedding_cache = {k: v for k, v in self._embedding_cache.items() if k in active_keys}
            self._norm_key_cache = {k: v for k, v in self._norm_key_cache.items() if k in active_keys}

        if self._sorted_keys_cache[1] == dict_hash:
            sorted_keys: List[str] = list(self._sorted_keys_cache[0])
        else:
            sorted_keys = sorted(user_dict.keys(), key=len, reverse=True)
            self._sorted_keys_cache = (sorted_keys, dict_hash)

        new_keys = [k for k in sorted_keys if k not in self._embedding_cache]
        if new_keys and self.encoder:
            try:
                def _get_embeddings(): return list(self.encoder.embed(new_keys))
                embeddings = await loop.run_in_executor(None, _get_embeddings)
                for k, v in zip(new_keys, embeddings): self._embedding_cache[k] = v
            except Exception as e:
                logger.error(f"[Neural Local] Embedding failed: {e}")
                return transcript, 0.0

        current_text = transcript; words_list = transcript.split(); max_total_score = 0.0
        applied_corrections = False; hit_keys = set()

        for n in range(min(3, len(words_list)), 0, -1):
            for i in range(len(words_list) - n + 1):
                window = " ".join(words_list[i : i + n])
                if not window.strip(): continue
                norm_window = get_norm(window)

                potential_keys = []
                for key in sorted_keys:
                    if abs(len(key.split()) - n) > 1: continue
                    if key not in self._norm_key_cache: self._norm_key_cache[key] = normalize_vn(key)
                    norm_key = str(self._norm_key_cache.get(key, ""))
                    thresh = 75 if len(norm_window) < 5 else 60
                    if fuzz.ratio(norm_window, norm_key) >= thresh: potential_keys.append((key, norm_key))

                if not potential_keys: continue
                try:
                    def _embed_window(): return list(self.encoder.embed([window]))
                    window_vec = (await loop.run_in_executor(None, _embed_window))[0]
                except Exception: continue

                for key, norm_key in potential_keys:
                    key_vec = self._embedding_cache[key]
                    score = self._cosine_similarity(window_vec, key_vec)
                    fuzzy_score = fuzz.ratio(norm_window, norm_key)
                    if score >= 0.85 or fuzzy_score >= 90:
                        if window in current_text:
                            current_text = current_text.replace(window, user_dict[key])
                            applied_corrections = True; hit_keys.add(key)
                        max_total_score = max(max_total_score, max(score, fuzzy_score / 100.0))

        if applied_corrections:
            for k in hit_keys: asyncio.create_task(xohi_memory.increment_stt_usage(k))
        return current_text, (max_total_score if applied_corrections else 0.0)
