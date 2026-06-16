import logging
import re
from typing import AsyncGenerator
import importlib
import inspect
import edge_tts



logger = logging.getLogger("api-gateway")


async def stream_tts_public(text: str, voice: str = "vi-VN-HoaiMyNeural") -> AsyncGenerator[bytes, None]:
    """
    Elite Master Stream (V4.2 - Guarded Output with Robust Auto-Retry & Backoff)
    Provides a single, continuous audio stream. Retries on connection failure.
    """
    import asyncio
    sanitized_text: str = _sanitize_text(text)
    if not sanitized_text:
        logger.warning("[TTS-Public] Empty text after sanitization — skipping.")
        return

    # Chỉ cho phép 2 giọng đọc chuẩn của Microsoft Edge Việt Nam để đảm bảo an toàn hệ thống
    target_voice = voice if voice in ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"] else "vi-VN-HoaiMyNeural"
    
    max_attempts = 4
    audio_yielded: bool = False
    
    for attempt in range(1, max_attempts + 1):
        try:
            communicate = edge_tts.Communicate(sanitized_text, target_voice)
            async for data in communicate.stream():
                if data["type"] == "audio":
                    audio_yielded = True
                    yield data["data"]
            # Nếu chạy thành công toàn bộ vòng lặp và đã nhận được âm thanh, kết thúc
            if audio_yielded:
                break
        except Exception as e:
            logger.warning(f"[TTS-Public] Attempt {attempt} failed: {e}")
            if attempt == max_attempts:
                logger.error(f"[TTS-Public] Master Stream failed after {max_attempts} attempts: {e}")
            else:
                # Exponential backoff (đợi 0.2s, 0.4s, 0.8s trước khi thử lại)
                await asyncio.sleep(0.2 * (2 ** (attempt - 1)))
                
        if audio_yielded:
            # Nếu đã phát âm thanh nhưng giữa chừng bị ngắt kết nối, không thử lại để tránh trùng lặp dữ liệu âm thanh đã phát
            break

    if not audio_yielded:
        logger.error("[TTS-Public] No audio bytes received from edge-tts after multiple attempts.")


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
