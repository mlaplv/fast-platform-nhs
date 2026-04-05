import logging
import asyncio
import os
import time
import random
from typing import Optional
from fastembed import TextEmbedding

logger = logging.getLogger("api-gateway")

# Elite V2.2: Fresh surgical cache to bypass Docker Volume symlink issues
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
CACHE_DIR = os.getenv("FASTEMBED_CACHE_DIR", os.path.join(_project_root, "backend/cache/fastembed_surgical"))

# Force disable symlinks to avoid common Docker/NTFS/OverlayFS issues
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

_shared_encoder: Optional[TextEmbedding] = None
_lock: Optional[asyncio.Lock] = None
_init_in_progress = False

def _check_model_health() -> bool:
    """Verifies if the model exists and seems complete in the cache (Old or New folder structure)."""
    # [ELITE 2.2] Support regular and Qdrant-repo-style folder names
    model_paths = [
        os.path.join(CACHE_DIR, "paraphrase-multilingual-MiniLM-L12-v2"),
        os.path.join(CACHE_DIR, "models--qdrant--paraphrase-multilingual-MiniLM-L12-v2-onnx-Q")
    ]
    required_files = ["model_optimized.onnx", "config.json"]
    
    for path in model_paths:
        if all(os.path.exists(os.path.join(path, f)) for f in required_files):
            # Double check size for model file (> 100MB) to ensure it's not a git-lfs pointer
            model_file = os.path.join(path, "model_optimized.onnx")
            if os.path.getsize(model_file) > 100 * 1024 * 1024:
                return True
    return False

async def warmup_encoder(max_retries: int = 5):
    """
    [TRINITY BOOT] Pre-loads the embedding model into memory with RETRY logic.
    (Elite V2.2: Resilient to network 'Connection reset by peer' errors)
    """
    global _shared_encoder, _lock, _init_in_progress
    if _lock is None:
        _lock = asyncio.Lock()
        
    async with _lock:
        if _shared_encoder is not None:
            return
        
        if _init_in_progress:
            return

        _init_in_progress = True
        logger.info(f"[Encoder] Initializing fastembed in {CACHE_DIR} (Max retries: {max_retries})...")
        
        try:
            model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            os.makedirs(CACHE_DIR, exist_ok=True)
            
            # Check if directory is writable
            if not os.access(CACHE_DIR, os.W_OK):
                logger.error(f"[Encoder] CACHE_DIR {CACHE_DIR} is NOT WRITABLE!")
            
            for attempt in range(1, max_retries + 1):
                try:
                    # [ELITE V2.2] Intelligent Offline & Surgical Download logic
                    is_cached = _check_model_health()
                    if is_cached:
                        logger.info("[Encoder] Model found in cache. Using offline mode.")
                        os.environ["HF_HUB_OFFLINE"] = "1"
                    else:
                        logger.info(f"[Encoder] Attempt {attempt}: Model missing. Initiating Surgical Download via curl...")
                        os.environ.pop("HF_HUB_OFFLINE", None)
                        
                        # [RESILIENCE] Use curl for high-speed, reliable download (Bypassing Python's unstable downloader)
                        import subprocess
                        SHA = "faf4aa4225822f3bc6376869cb1164e8e3feedd0"
                        SNAPSHOT_DIR = os.path.join(CACHE_DIR, f"models--qdrant--paraphrase-multilingual-MiniLM-L12-v2-onnx-Q/snapshots/{SHA}")
                        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
                        
                        BASE_URL = "https://huggingface.co/qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q/resolve/main"
                        files = ["model_optimized.onnx", "config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"]
                        
                        for file in files:
                            dest = os.path.join(SNAPSHOT_DIR, file)
                            if not os.path.exists(dest) or (file == "model_optimized.onnx" and os.path.getsize(dest) < 100 * 1024 * 1024):
                                logger.info(f"[Encoder] Fetching {file} via curl...")
                                subprocess.run([
                                    "curl", "-L", "--retry", "5", "--retry-delay", "2", 
                                    "-o", dest, f"{BASE_URL}/{file}"
                                ], check=True, capture_output=True)

                    def _init():
                        return TextEmbedding(
                            model_name=model_name,
                            cache_dir=CACHE_DIR,
                            local_files_only=os.getenv("HF_HUB_OFFLINE") == "1"
                        )

                    loop = asyncio.get_running_loop()
                    _shared_encoder = await loop.run_in_executor(None, _init)
                    logger.info("[Encoder] fastembed initialized successfully.")
                    break # Success!
                except Exception as e:
                    error_msg = str(e)
                    is_network_error = any(kw in error_msg.lower() for kw in ["connection reset", "104", "timeout", "network", "remote end closed"])
                    
                    if is_network_error and attempt < max_retries:
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"[Encoder] Network error during initialization (Attempt {attempt}/{max_retries}): {e}. Retrying in {wait_time:.2f}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"[Encoder] Critical failure initializing fastembed: {e}")
                        if attempt == max_retries:
                            # Final failure
                            break
        finally:
            _init_in_progress = False

def get_shared_encoder() -> Optional[TextEmbedding]:
    """
    Returns the pre-loaded encoder. 
    (Elite V2.2: Note - if None, service should trigger warmup or handle 503)
    """
    return _shared_encoder

# REMOVED: get_encoder() synchronous blocking helper to prevent startup hangs.
# Services should use get_shared_encoder() and handle None or use a lazy property.
