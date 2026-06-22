"""
Vietnamese Elite NLP Guard — Tầng 3: Neural Spell Corrector.
Sử dụng BARTpho (bmd1905/vietnamese-correction-v2) cho spell correction context-aware.

Thiết kế:
- Lazy-loading singleton: Chỉ load model khi gọi lần đầu (~400MB)
- Thread-safe: Dùng threading.Lock() cho concurrent access
- Auto-unload: Giải phóng model sau 5 phút idle để tiết kiệm RAM
- Graceful fallback: Nếu model không load được → trả về text gốc
"""

import time
import logging
import threading
from typing import Optional

logger = logging.getLogger("api-gateway")

_MODEL_NAME = "bmd1905/vietnamese-correction-v2"
_IDLE_TIMEOUT_SECONDS = 300  # 5 phút
_MAX_INPUT_LENGTH = 512

# Map hỗ trợ đổi kiểu gõ dấu (Hòa Bình vs Quốc Tế) để khớp với vocabulary của BARTpho
_NEW_TO_OLD_MAP = {
    "òa": "oà", "óa": "oá", "ỏa": "oả", "õa": "oã", "ọa": "oạ",
    "òe": "oè", "óe": "oé", "ỏe": "oẻ", "õe": "oẽ", "ọe": "oẹ",
    "ùy": "uỳ", "úy": "uý", "ủy": "uỷ", "ũy": "uỹ", "ụy": "uỵ",
    "Òa": "Oà", "Óa": "Oá", "Ỏa": "Oả", "Õa": "Oã", "Ọa": "Oạ",
    "Òe": "Oè", "Óe": "Oé", "Ỏe": "Oẻ", "Õe": "Oẽ", "Ọe": "Oẹ",
    "Ùy": "Uỳ", "Úy": "Uý", "Ủy": "Uỷ", "Ũy": "Uỹ", "Ụy": "Uỵ",
}
_OLD_TO_NEW_MAP = {v: k for k, v in _NEW_TO_OLD_MAP.items()}


def _to_old_style(text: str) -> str:
    for k, v in _NEW_TO_OLD_MAP.items():
        text = text.replace(k, v)
    return text


def _to_new_style(text: str) -> str:
    for k, v in _OLD_TO_NEW_MAP.items():
        text = text.replace(k, v)
    return text


class VietnameseSpellCorrector:
    """
    Lazy-loading singleton cho BARTpho spell correction.
    Load model lần đầu gọi, cache trong memory.
    Auto-unload sau 5 phút idle để tiết kiệm RAM trên VPS 4GB.
    """
    _instance: Optional["VietnameseSpellCorrector"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._model: Optional[object] = None
        self._tokenizer: Optional[object] = None
        self._last_used: float = 0.0
        self._model_lock: threading.Lock = threading.Lock()
        self._cleanup_timer: Optional[threading.Timer] = None

    @classmethod
    def get_instance(cls) -> "VietnameseSpellCorrector":
        """Thread-safe singleton getter."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _ensure_loaded(self) -> bool:
        """Load model nếu chưa có. Returns True nếu model sẵn sàng."""
        if self._model is not None:
            self._last_used = time.monotonic()
            return True

        with self._model_lock:
            if self._model is not None:
                self._last_used = time.monotonic()
                return True

            try:
                from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
                logger.info(f"[SpellCorrector] Loading model {_MODEL_NAME}...")
                self._tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
                self._model = AutoModelForSeq2SeqLM.from_pretrained(_MODEL_NAME)
                
                # Cấu hình CPU evaluation mode
                self._model.eval() # type: ignore[attr-defined]
                
                self._last_used = time.monotonic()
                self._schedule_cleanup()
                logger.info(f"[SpellCorrector] Model loaded successfully.")
                return True
            except ImportError:
                logger.warning("[SpellCorrector] transformers/torch not installed. Tầng 3 disabled.")
                return False
            except Exception as e:
                logger.error(f"[SpellCorrector] Failed to load model: {e}")
                return False

    def _schedule_cleanup(self) -> None:
        """Đặt timer tự giải phóng model sau IDLE_TIMEOUT."""
        if self._cleanup_timer is not None:
            self._cleanup_timer.cancel()

        self._cleanup_timer = threading.Timer(
            _IDLE_TIMEOUT_SECONDS,
            self._maybe_unload,
        )
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()

    def _maybe_unload(self) -> None:
        """Giải phóng model nếu đã idle quá lâu."""
        elapsed = time.monotonic() - self._last_used
        if elapsed >= _IDLE_TIMEOUT_SECONDS and self._model is not None:
            with self._model_lock:
                self._model = None
                self._tokenizer = None
                logger.info(f"[SpellCorrector] Model unloaded after {elapsed:.0f}s idle.")
        elif self._model is not None:
            # Chưa hết timeout, schedule lại
            self._schedule_cleanup()

    def correct(self, text: str) -> tuple[str, list[dict[str, str]]]:
        """
        Sửa lỗi chính tả tiếng Việt bằng BARTpho.
        
        Args:
            text: Văn bản cần kiểm tra
            
        Returns:
            (corrected_text, changes) trong đó changes là list dict:
            [{"original": "fẩm", "corrected": "phẩm", "context": "Sản fẩm này..."}]
        """
        if not text or not text.strip():
            return text, []

        if not self._ensure_loaded():
            return text, []  # Graceful fallback

        # Cắt input và đổi sang kiểu gõ dấu cũ (Hòa Bình) cho khớp với model vocab
        truncated = _to_old_style(text[:_MAX_INPUT_LENGTH])

        try:
            import torch
            # Tokenize input
            inputs = self._tokenizer(truncated, return_tensors="pt") # type: ignore[operator]
            
            with torch.no_grad():
                outputs = self._model.generate( # type: ignore[attr-defined]
                    **inputs,
                    max_length=_MAX_INPUT_LENGTH,
                    num_beams=1,  # Greedy decode cho tốc độ
                )
            
            corrected_old: str = self._tokenizer.decode(outputs[0], skip_special_tokens=True) # type: ignore[index, operator]
            # Đổi kết quả về kiểu gõ dấu mới để so khớp và trả về
            corrected = _to_new_style(corrected_old)
        except Exception as e:
            logger.warning(f"[SpellCorrector] Correction failed: {e}")
            return text, []

        self._last_used = time.monotonic()
        self._schedule_cleanup()

        # Diff để tìm các thay đổi cụ thể
        changes = self._extract_changes(text, corrected)

        # Nếu model trả về text quá khác biệt (>30% thay đổi), reject
        if len(changes) > 0:
            change_ratio = sum(len(c["original"]) for c in changes) / max(len(text), 1)
            if change_ratio > 0.3:
                logger.warning(
                    f"[SpellCorrector] Over-correction detected ({change_ratio:.0%}). Rejecting."
                )
                return text, []

        return corrected if changes else text, changes

    def _extract_changes(
        self, original: str, corrected: str
    ) -> list[dict[str, str]]:
        """So sánh original vs corrected để trích xuất danh sách thay đổi."""
        if original.strip() == corrected.strip():
            return []

        changes: list[dict[str, str]] = []

        # Tách thành từng từ để diff
        orig_words = original.split()
        corr_words = corrected.split()

        # Simple word-level diff
        max_len = min(len(orig_words), len(corr_words))
        for i in range(max_len):
            if orig_words[i] != corr_words[i]:
                # Lấy context xung quanh
                ctx_start = max(0, i - 2)
                ctx_end = min(len(orig_words), i + 3)
                context = " ".join(orig_words[ctx_start:ctx_end])

                changes.append({
                    "original": orig_words[i],
                    "corrected": corr_words[i],
                    "context": context,
                })

        return changes

    def is_loaded(self) -> bool:
        """Kiểm tra model đã được load chưa."""
        return self._model is not None
