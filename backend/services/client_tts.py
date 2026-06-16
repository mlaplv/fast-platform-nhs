import logging
import re
from typing import AsyncGenerator
import importlib
import inspect
import edge_tts



logger = logging.getLogger("api-gateway")


async def stream_tts_public(text: str, voice: str = "vi-VN-HoaiMyNeural") -> AsyncGenerator[bytes, None]:
    """
    Elite Master Stream (V4.1 - Guarded Output)
    Provides a single, continuous audio stream. Raises on empty output.
    """
    sanitized_text: str = _sanitize_text(text)
    if not sanitized_text:
        logger.warning("[TTS-Public] Empty text after sanitization — skipping.")
        return

    # Chỉ cho phép 2 giọng đọc chuẩn của Microsoft Edge Việt Nam để đảm bảo an toàn hệ thống
    target_voice = voice if voice in ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"] else "vi-VN-HoaiMyNeural"
    communicate = edge_tts.Communicate(sanitized_text, target_voice)
    audio_yielded: bool = False
    try:
        async for data in communicate.stream():
            if data["type"] == "audio":
                audio_yielded = True
                yield data["data"]
    except Exception as e:
        logger.error(f"[TTS-Public] Master Stream failed: {e}")

    if not audio_yielded:
        logger.error("[TTS-Public] No audio bytes received from edge-tts (Microsoft service may be unavailable).")


def _sanitize_text(text: str) -> str:
    """
    Elite Text Sanitizer (V5.0 - SECURITY LOCKDOWN).
    Prepares text for high-speed neural synthesis with hacker protection.
    """
    if not text:
        return ""
    
    # R5.0: ANTI-HACKER - Strip all potential SSML tags or control characters
    text = re.sub(r'[<>]', '', text)
    
    # 1. Clean HTML entities and hidden tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # 2. Hard-cap text length (RAM protection)
    # 20000 chars is enough for long SEO articles, safe for streaming architecture.
    text = text[:20000]
    
    # 3. Fix number-unit concatenation (e.g. '30g' -> '30 g')
    text = re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', text)
    
    # 4. Fix missing space after punctuation (only if followed by a non-punctuation word character)
    text = re.sub(r'([\.!\?,])([^\s\.!\?,])', r'\1 \2', text)
    
    # 5. Clean up excessive whitespace and control chars
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
