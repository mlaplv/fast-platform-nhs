import logging
import asyncio
from typing import Optional
from fastembed import TextEmbedding

logger = logging.getLogger("api-gateway")

_shared_encoder: Optional[TextEmbedding] = None
_lock = asyncio.Lock()

async def warmup_encoder():
    """Pre-loads the embedding model into memory."""
    global _shared_encoder
    async with _lock:
        if _shared_encoder is None:
            logger.info("[Encoder] Initializing fastembed (sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)...")
            # We use a multilingual model for Vietnamese support
            # This model is ~420MB and fits comfortably in 2GB RAM with other services
            try:
                # Running in executor to not block the event loop during model loading
                loop = asyncio.get_event_loop()
                _shared_encoder = await loop.run_in_executor(
                    None,
                    lambda: TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
                )
                logger.info("[Encoder] fastembed initialized successfully.")
            except Exception as e:
                logger.error(f"[Encoder] Failed to initialize fastembed: {e}")

def get_shared_encoder() -> Optional[TextEmbedding]:
    """Returns the pre-loaded encoder. Should be warmed up first."""
    return _shared_encoder

def get_encoder() -> TextEmbedding:
    """Synchronous getter. Warning: will initialize if None (blocks thread)."""
    global _shared_encoder
    if _shared_encoder is None:
        logger.warning("[Encoder] Synchronous initialization triggered. Use warmup_encoder() at boot.")
        _shared_encoder = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return _shared_encoder
