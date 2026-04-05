import logging
import asyncio
import os
from typing import Optional
from fastembed import TextEmbedding

logger = logging.getLogger("api-gateway")

# Elite V2.2: Centralized Model Cache to avoid Docker permission issues and redundant downloads
# Uses project-relative path
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
# [GHOST MODE] Ensure absolute path and handle Docker volume mapping
CACHE_DIR = os.getenv("FASTEMBED_CACHE_DIR", os.path.join(_project_root, "backend/cache/fastembed"))

# Force disable symlinks to avoid common Docker/NTFS/OverlayFS issues
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

# [ELITE V2.2] Intelligent Offline Mode (R00: Reliability)
# Only force offline if the model file is actually found in cache
_model_file = os.path.join(CACHE_DIR, "paraphrase-multilingual-MiniLM-L12-v2", "model_optimized.onnx")
if os.path.exists(_model_file):
    os.environ["HF_HUB_OFFLINE"] = "1"
else:
    # Ensure offline is NOT forced if we need a download
    os.environ.pop("HF_HUB_OFFLINE", None)

_shared_encoder: Optional[TextEmbedding] = None
_lock: Optional[asyncio.Lock] = None

async def warmup_encoder():
    """
    [TRINITY BOOT] Pre-loads the embedding model into memory.
    Must be called during application lifespan.
    """
    global _shared_encoder, _lock
    if _lock is None:
        _lock = asyncio.Lock()
        
    async with _lock:
        if _shared_encoder is None:
            logger.info(f"[Encoder] Initializing fastembed in {CACHE_DIR}...")
            try:
                # model_name must match the one baked in Docker or desired for RAG
                model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                
                os.makedirs(CACHE_DIR, exist_ok=True)
                
                # Check if directory is writable (R00: Security & Stability)
                if not os.access(CACHE_DIR, os.W_OK):
                    logger.error(f"[Encoder] CACHE_DIR {CACHE_DIR} is NOT WRITABLE!")
                
                def _init():
                    # [ELITE V2.2] Sync local_files_only with our Intelligent Offline logic (R00)
                    return TextEmbedding(
                        model_name=model_name,
                        cache_dir=CACHE_DIR,
                        local_files_only=os.getenv("HF_HUB_OFFLINE") == "1"
                    )

                loop = asyncio.get_running_loop()
                _shared_encoder = await loop.run_in_executor(None, _init)
                logger.info("[Encoder] fastembed initialized successfully.")
            except Exception as e:
                logger.error(f"[Encoder] Failed to initialize fastembed: {e}")
                # We do NOT raise here to allow the rest of the app to boot, 
                # but services using it will need to handle None.

def get_shared_encoder() -> Optional[TextEmbedding]:
    """Returns the pre-loaded encoder. Returns None if not warmed up."""
    return _shared_encoder

# REMOVED: get_encoder() synchronous blocking helper to prevent startup hangs.
# Services should use get_shared_encoder() and handle None or use a lazy property.
