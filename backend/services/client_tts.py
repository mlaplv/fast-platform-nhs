import logging
import re
from typing import AsyncGenerator
import edge_tts

logger = logging.getLogger("api-gateway")


async def stream_tts_public(text: str) -> AsyncGenerator[bytes, None]:
    """
    Elite Master Stream (V4.0 - Professional Mastery)
    Provides a single, continuous audio stream for the entire text.
    Zero-gap, zero-fragmentation.
    """
    sanitized_text: str = _sanitize_text(text)
    if not sanitized_text:
        return

    # Process everything in one high-performance stream
    # R4.0: Zero-Hydration safety, direct binary stream
    communicate = edge_tts.Communicate(sanitized_text, "vi-VN-HoaiMyNeural")
    try:
        async for data in communicate.stream():
            if data["type"] == "audio":
                yield data["data"]
    except Exception as e:
        logger.error(f"[TTS-Public] Master Stream failed: {e}")


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
    # 3000 chars is approx 10 min of audio, safe for 4GB RAM environment.
    text = text[:3000]
    
    # 3. Fix number-unit concatenation (e.g. '30g' -> '30 g')
    text = re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', text)
    
    # 4. Fix missing space after punctuation
    text = re.sub(r'([\.!\?,])([^\s])', r'\1 \2', text)
    
    # 5. Clean up excessive whitespace and control chars
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
