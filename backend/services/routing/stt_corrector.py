import os
import json
import logging
import asyncio
import unicodedata
import numpy as np
from typing import Dict, Optional, Tuple, List

from rapidfuzz import fuzz
from litellm.exceptions import ServiceUnavailableError, RateLimitError, Timeout as LiteLLMTimeout, AuthenticationError, NotFoundError

from pydantic_ai import Agent, RunContext
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.utils.text import normalize_vn
from backend.services.xohi_memory import xohi_memory
from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("api-gateway")

@dataclass
class STTCorrectorDeps:
    """Dependencies for STT Corrector."""
    user_dictionary: Dict[str, str] = field(default_factory=dict)

class STTCorrectionItem(BaseModel):
    wrong_word: str = Field(description="The misspelled or misheard word exactly as it appeared in the input transcript.")
    right_word: str = Field(description="The correct target word.")

class STTCorrectionOutput(BaseModel):
    cleaned_text: str = Field(description="The corrected transcript. If no correction is needed, return the original.")
    suspected_correction: Optional[List[STTCorrectionItem]] = Field(
        default=None, 
        description="If you made a correction that is NOT in the user's dictionary and you are not 100% sure, return a list of correction pairs."
    )

# We are using an extremely focused prompt.
# It MUST NOT answer the user's question. 
# It ONLY corrects the vocabulary based on the context of an e-commerce admin system.
STT_CORRECTOR_PROMPT = """[ROLE] STT PRE-PROCESSOR (Hệ thống E-commerce Admin)
Nhiệm vụ của bạn là nhận một câu văn bản (transcript) được chuyển từ giọng nói (Speech-to-Text),
phát hiện và sửa lỗi chính tả/từ vựng do quá trình nhận diện giọng nói gây ra,
MÀ KHÔNG thay đổi ý nghĩa hay trả lời câu hỏi đó.

[NGỮ CẢNH HỆ THỐNG]
Người dùng là một "Sếp" (Quản trị viên) đang dùng giọng nói để ra lệnh cho hệ thống quản lý bán hàng (SmartShop).
Các khái niệm có trong hệ thống:
- Doanh thu, doanh số, tiền, thu nhập
- Đơn hàng, bill, hóa đơn
- Sản phẩm, hàng hóa, tồn kho, kho
- Khách hàng, người dùng, user, nhân viên, tài khoản
- Bài viết, tin tức, danh mục

[QUY TẮC CỐT LÕI]
1. NHẬN DIỆN LỖI PHÁT ÂM: STT Tiếng Việt hay sai những từ nghe giống nhau trong ngữ cảnh bán hàng.
   Ví dụ về các cặp từ dễ nhầm lẫn (Hãy nghi ngờ và đề xuất sửa):
   - "dân số", "nhân số" -> "doanh số"
   - "doanh tu" -> "doanh thu"
   - "đau hàng" -> "đơn hàng"
   - "sang phẩm" -> "sản phẩm"

2. CHỈ SỬA LỖI, KHÔNG TRẢ LỜI: Nếu input là "doanh số tháng này bao nhiêu", output CHỈ LÀ "doanh số tháng này bao nhiêu". Không được thêm câu trả lời.

3. GIỮ NGUYÊN NẾU KHÔNG CÓ LỖI: Nếu câu nghe có vẻ đã đúng chuyên ngành, xuất lại y nguyên.

5. SỬ DỤNG TỪ ĐIỂN CỦA SẾP: Ưu tiên tuyệt đối các từ trong [USER_DICTIONARY_CONTEXT] nếu có.

6. FLAG NGHI VẤN (QUAN TRỌNG): Nếu bạn sửa một từ/cụm từ mà bạn không chắc chắn 100%, hoặc nó KHÔNG CÓ TRONG [USER_DICTIONARY_CONTEXT], hãy điền cặp đó vào trường `suspected_correction`.
   LƯU Ý:
   - Phải dùng CHÍNH XÁC từ xuất hiện trong INPUT cho phần từ sai (Ví dụ: Trả về {"dân số": "doanh số"} nếu input có chữ "dân số"). KHÔNG tự ý chế từ mới.
   - Phải trả về ĐẦY ĐỦ CỤM TỪ CÓ NGHĨA (Ví dụ: "doanh số" thay vì chỉ "doanh").
   Hệ thống sẽ dùng thông tin này để hỏi lại Sếp và tự học cho lần sau.

7. TRẢ VỀ JSON: Kết quả bắt buộc dưới định dạng JSON theo schema đã chỉ định.
"""

# --- Phase 76.3: Zero-Allocation Constants ---
NAV_PATTERNS = {
    "mo bieu do", "xem bieu do", "doanh so thang nay", "doanh thu hom nay",
    "xem don hang", "danh sach san pham", "ok", "dung", "vang", "phai", "thoat",
    "mo danh muc", "vao danh muc", "mo tin tuc", "vao tin tuc", "mo cai dat",
    "chao", "xin chao", "tam biet", "bye", "hẹn gặp lại"
}
# Pre-normalize for fast lookup
NORM_NAV_PATTERNS = {normalize_vn(p) for p in NAV_PATTERNS}

SOUND_ALIKES = {
    "dân số": "doanh số",
    "nhân số": "doanh số",
    "doanh tu": "doanh thu",
    "đau hàng": "đơn hàng",
    "sang phẩm": "sản phẩm",
}
# Pre-normalize keys for robust matching
NORM_SOUND_ALIKES = {normalize_vn(k): v for k, v in SOUND_ALIKES.items()}

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

    async def _ensure_encoder(self):
        if self.encoder is None:
            loop = asyncio.get_event_loop()
            self.encoder = await loop.run_in_executor(None, get_shared_encoder)

    def _cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    async def correct(self, transcript: str, user_dict: Dict[str, str]) -> Tuple[str, float]:
        """
        Semantic match with Phonetic Sieve (2026 Optimization).
        Skips embedding for windows that don't pass a lightweight fuzzy pre-filter.
        """
        if not user_dict:
            return transcript, 0.0

        await self._ensure_encoder()
        if self.encoder is None:
            return transcript, 0.0

        loop = asyncio.get_event_loop()

        # 1. Update/Prune embedding cache (Neural Aging)
        self._cache_access_count += 1
        dict_hash = hash(frozenset(user_dict.items()))

        if self._cache_access_count > 50 or len(self._embedding_cache) > 200:
            self._cache_access_count = 0
            # Keep only keys present in current user_dict to avoid leaks
            active_keys = set(user_dict.keys())
            self._embedding_cache = {k: v for k, v in self._embedding_cache.items() if k in active_keys}
            self._norm_key_cache = {k: v for k, v in self._norm_key_cache.items() if k in active_keys}

        # 76.3: Avoid redundant sorting
        if self._sorted_keys_cache[1] == dict_hash:
            sorted_keys = self._sorted_keys_cache[0]
        else:
            sorted_keys = sorted(user_dict.keys(), key=len, reverse=True)
            self._sorted_keys_cache = (sorted_keys, dict_hash)

        new_keys = [k for k in sorted_keys if k not in self._embedding_cache]
        if new_keys:
            try:
                embeddings = await loop.run_in_executor(None, lambda: list(self.encoder.embed(new_keys)))
                for k, v in zip(new_keys, embeddings):
                    self._embedding_cache[k] = v
            except Exception as e:
                logger.error(f"[Neural Local] Embedding failed: {e}")
                return transcript, 0.0

        current_text = transcript
        words = transcript.split()
        max_total_score = 0.0
        applied_corrections = False
        hit_keys = set()
        norm_cache = {}

        # 2. Sliding window (up to 3 words)
        for n in range(min(3, len(words)), 0, -1):
            for i in range(len(words) - n + 1):
                window = " ".join(words[i : i + n])
                if not window.strip(): continue

                if window not in norm_cache:
                    norm_cache[window] = normalize_vn(window)
                norm_window = norm_cache[window]

                potential_keys = []
                for key in sorted_keys:
                    # Quick length filter
                    if abs(len(key.split()) - n) > 1: continue

                    if key not in self._norm_key_cache:
                        self._norm_key_cache[key] = normalize_vn(key)
                    norm_key = self._norm_key_cache[key]

                    # Phonetic similarity (Levenshtein based)
                    thresh = 75 if len(norm_window) < 5 else 60
                    if fuzz.ratio(norm_window, norm_key) >= thresh:
                        potential_keys.append((key, norm_key))

                if not potential_keys:
                    continue

                # Embed window ONLY for candidates
                try:
                    window_vec = (await loop.run_in_executor(None, lambda: list(self.encoder.embed([window]))))[0]
                except Exception: continue

                for key, norm_key in potential_keys:
                    key_vec = self._embedding_cache[key]
                    score = self._cosine_similarity(window_vec, key_vec)
                    fuzzy_score = fuzz.ratio(norm_window, norm_key)

                    if score >= 0.85 or fuzzy_score >= 90:
                        replacement = user_dict[key]
                        if window in current_text:
                            current_text = current_text.replace(window, replacement)
                            applied_corrections = True
                            hit_keys.add(key)

                        composite_score = max(score, fuzzy_score / 100.0)
                        max_total_score = max(max_total_score, composite_score)
                        logger.debug(f"[Neural Local] HIT: '{window}' ~ '{key}' (sem={score:.2f}, fuzz={fuzzy_score}%)")

        # 3. Frequency Tracking (Async heartbeat)
        if applied_corrections:
            for k in hit_keys:
                asyncio.create_task(xohi_memory.increment_stt_usage(k))

        return current_text, (max_total_score if applied_corrections else 0.0)

# --- Phase 76.3: Stopwords Cache ---
_STOPWORDS_CACHE = {"raw": [], "norm": set(), "last_update": 0}

class STTCorrector:
    """
    Intelligent layer that runs BEFORE router.
    Cleans transcript using LLM to fix Vietnamese homophone/STT issues (e.g. "nhân số" -> "doanh số").
    """
    def __init__(self):
        # Kill GOOGLE_API_KEY immediately — LiteLLM prefers it over GEMINI_API_KEY
        os.environ.pop("GOOGLE_API_KEY", None)
        self.rotator = key_rotator
        self.neural_corrector = NeuralLocalCorrector()

        self.agent = Agent(
            deps_type=STTCorrectorDeps,
            output_type=STTCorrectionOutput,
            system_prompt=STT_CORRECTOR_PROMPT
        )

        @self.agent.system_prompt
        def inject_user_dict(ctx: RunContext[STTCorrectorDeps]) -> str:
            if ctx.deps.user_dictionary:
                return f"\n[USER_DICTIONARY_CONTEXT]\n{json.dumps(ctx.deps.user_dictionary, ensure_ascii=False)}"
            return "\n[USER_DICTIONARY_CONTEXT]\n{}"

    async def _get_cached_stopwords(self) -> set:
        """Fetch and normalize stopwords with 5-minute TTL cache."""
        now = time.time()
        if now - _STOPWORDS_CACHE["last_update"] > 300:
            stopwords = await xohi_memory.get_system_stt_stopwords()
            _STOPWORDS_CACHE["raw"] = stopwords
            _STOPWORDS_CACHE["norm"] = {normalize_vn(sw) for sw in stopwords}
            _STOPWORDS_CACHE["last_update"] = now
        return _STOPWORDS_CACHE["norm"]

    async def _ensure_aging_task(self):
        """Lazy start for Neural Aging background task."""
        if not hasattr(self, "_aging_task") or self._aging_task is None or self._aging_task.done():
            try:
                self._aging_task = asyncio.create_task(self._neural_aging_loop())
            except RuntimeError:
                pass # Still no loop (unit tests?)

    async def _neural_aging_loop(self):
        """Periodic background pruning of old/unused synapses."""
        while True:
            await asyncio.sleep(3600) # Every hour
            try:
                await xohi_memory.prune_stt_overrides(max_size=300)
            except Exception: pass

    async def smart_learn(self, user_id: str, wrong: str, right: str, is_global: bool = True):
        """
        Smart Learning (2026 Thinking):
        Consolidates mistakes if they are semantically identical to a known one.
        """
        norm_wrong = normalize_vn(wrong.strip())
        
        # 1. Look up existing overrides
        overrides = await xohi_memory.get_system_stt_overrides() if is_global else await xohi_memory.get_stt_dictionary(user_id)
        
        # 2. Check for semantic dups
        if norm_wrong in overrides:
            return # Already exactly known
            
        # 3. Use Neural Corrector to see if we "already know" this mistake pattern
        # If score is very high (>= 0.95), it's just a slight spelling variation of a known wrong word.
        # We don't add a new entry, we just increment usage of the "root" mistake.
        await self.neural_corrector._ensure_encoder()
        loop = asyncio.get_event_loop()
        try:
            w_vec = (await loop.run_in_executor(None, lambda: list(self.neural_corrector.encoder.embed([norm_wrong]))))[0]
            for existing_wrong, existing_right in overrides.items():
                if existing_right == right:
                    # Same correction target, check if mistake is similar
                    e_vec = self.neural_corrector._embedding_cache.get(existing_wrong)
                    if e_vec is not None:
                        score = self.neural_corrector._cosine_similarity(w_vec, e_vec)
                        if score >= 0.95:
                            logger.info(f"[Neural Thinker] Consolidated '{norm_wrong}' into existing root '{existing_wrong}'")
                            await xohi_memory.increment_stt_usage(existing_wrong, is_global)
                            return
        except Exception: pass

        # 4. If not consolidated, learn normally
        await xohi_memory.learn_stt_correction(user_id, wrong, right, is_global)

    async def correct(self, transcript: str, user_dictionary: Optional[Dict[str, str]] = None, norm_query: Optional[str] = None) -> Tuple[str, Optional[Dict[str, str]]]:
        """
        Takes raw STT transcript, returns (cleaned transcript, suspected_corrections).
        Flow: Normalize -> Stopwords -> Neural Local -> Global Patterns -> Trinity Fallback.
        """
        # 0. Background tasks
        await self._ensure_aging_task()

        # Phase 76.3: Assume transcript is already NFC normalized by Orchestrator
        if not transcript: return "", None

        # 2026 SPEED OPTIMIZATION: If transcript is extremely short (1-2 words),
        # it's likely a command or greeting. Bypass heavy processing immediately.
        words_count = len(transcript.split())
        if words_count <= 2:
             logger.debug(f"[STT Corrector] Ultra-Fast Bypass for short phrase: '{transcript}'")
             return transcript, None

        if words_count <= 4:
            # Check for very common patterns that don't need correction
            if any(kw in transcript.lower() for kw in ["bài viết", "sản phẩm", "đơn hàng", "doanh thu", "biểu đồ", "mở", "xem"]):
                logger.debug(f"[STT Corrector] Fast-Bypass for simple context: '{transcript}'")
                return transcript, None

        # 0.5 STOPWORDS
        norm_stopwords = await self._get_cached_stopwords()
        if norm_stopwords:
            words = transcript.split()
            # 76.3: Local cache to avoid redundant normalize_vn on duplicate words in same transcript
            word_norm_map = {}
            filtered_words = []
            for w in words:
                w_lower = w.lower()
                if w_lower not in word_norm_map:
                    word_norm_map[w_lower] = normalize_vn(w_lower)
                if word_norm_map[w_lower] not in norm_stopwords:
                    filtered_words.append(w)

            # Zero-Allocation: Only join if words were actually removed
            if len(filtered_words) < len(words):
                transcript = " ".join(filtered_words)
                if not transcript: return "", None

        # 1. NEURAL LOCAL CORRECTION (Sub-20ms)
        # 2026 Strategy: Use local embeddings to bypass cloud
        system_overrides = await xohi_memory.get_system_stt_overrides()
        effective_dict = {**system_overrides, **(user_dictionary or {})}

        neural_cleaned, score = await self.neural_corrector.correct(transcript, effective_dict)
        if score >= 0.70:
            logger.info(f"[STT Corrector] Neural HIT (score={score:.2f}): '{neural_cleaned}'")
            return neural_cleaned, None

        # 2. PATTERN BYPASS (High-Speed Local Bypass)
        if norm_query is None:
            norm_query = normalize_vn(transcript)

        # Bypass for explicit nav patterns
        if norm_query in NORM_NAV_PATTERNS:
            return transcript, None

        # 3. NEURAL SWITCH (Sound-alike Fallback - 2026 Strategy)
        # Low-latency check for common Vietnamese STT mistakes that sound like protected keywords.
        lower_transcript = transcript.lower()
        new_transcript = transcript
        applied_switch = False
        for wrong, right in NORM_SOUND_ALIKES.items():
            if wrong in lower_transcript:
                logger.info(f"[STT Corrector] Neural Switch AUTO-FIX: '{wrong}' -> '{right}'")
                # Phase 76.3: Auto-fix common errors to eliminate confirmation UI lag
                new_transcript = new_transcript.replace(wrong, right)
                applied_switch = True

        if applied_switch:
            return new_transcript, None

        # 4. TRINITY DISPATCHER (Cloud Fallback)
        deps = STTCorrectorDeps(user_dictionary=user_dictionary or {})

        try:
            result = await trinity_bridge.run(self.agent, transcript, deps=deps)
            out_suspected = None
            if result.output.suspected_correction:
                out_suspected = {}
                for item in result.output.suspected_correction:
                    out_suspected[item.wrong_word.lower()] = item.right_word
            return result.output.cleaned_text, out_suspected
        except Exception as e:
            logger.error(f"[STT Corrector] Trinity failure: {e}")
            return transcript, None

stt_corrector = STTCorrector()
