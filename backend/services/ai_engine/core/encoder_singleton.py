import logging
import asyncio
import os
from typing import Optional
from fastembed import TextEmbedding

logger = logging.getLogger("api-gateway")

# Elite V2.2: Centralized Model Cache to avoid Docker permission issues and redundant downloads
# Uses project-relative path (5 levels up from core/ to reach fast-platform-core/)
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
CACHE_DIR = os.getenv("FASTEMBED_CACHE_DIR", os.path.join(_project_root, "backend/cache/fastembed"))
os.makedirs(CACHE_DIR, exist_ok=True)

_shared_encoder: Optional[TextEmbedding] = None
_lock = asyncio.Lock()

async def warmup_encoder():
    """Pre-loads the embedding model into memory using project-local cache."""
    global _shared_encoder
    async with _lock:
        if _shared_encoder is None:
            logger.info(f"[Encoder] Initializing fastembed in {CACHE_DIR}...")
            try:
                loop = asyncio.get_event_loop()
                _shared_encoder = await loop.run_in_executor(
                    None,
                    lambda: TextEmbedding(
                        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                        cache_dir=CACHE_DIR
                    )
                )
                logger.info("[Encoder] fastembed initialized successfully.")
            except Exception as e:
                logger.error(f"[Encoder] Failed to initialize fastembed: {e}")

def get_shared_encoder() -> Optional[TextEmbedding]:
    """Returns the pre-loaded encoder."""
    return _shared_encoder

def get_encoder() -> TextEmbedding:
    """Synchronous getter for services. Warning: will initialize if None."""
    global _shared_encoder
    if _shared_encoder is None:
        logger.warning("[Encoder] Synchronous initialization triggered.")
        _shared_encoder = TextEmbedding(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            cache_dir=CACHE_DIR
        )
    return _shared_encoder
