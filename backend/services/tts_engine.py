import logging
import edge_tts

logger = logging.getLogger("api-gateway")


async def stream_tts(text: str):
    """
    Module 1: THE LUNGS (BACKEND EDGE-TTS STREAMING)
    Generates audio chunks via edge-tts and yields them immediately.
    R2 Rule 2: try...finally for graceful shutdown on client disconnect.
    """
    text = text.strip()
    if not text:
        logger.warning("[TTS] Received empty text to synthesize. Aborting.")
        return

    communicate = edge_tts.Communicate(text, "vi-VN-HoaiMyNeural")
    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
    except edge_tts.exceptions.NoAudioReceived:
        logger.warning(f"[TTS] NoAudioReceived from Edge TTS for text: '{text}'")
    except GeneratorExit:
        logger.info("[TTS] Client disconnected — stream aborted gracefully")
    except Exception as e:
        logger.error(f"[TTS] Streaming failed: {e}")
    finally:
        logger.debug("[TTS] Stream cleanup complete")
