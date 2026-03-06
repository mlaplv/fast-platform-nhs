"""
Encoder Singleton — Single Source of Truth for fastembed TextEmbedding.
=====================================================================
V56.0: Merges 3 separate encoder instances (vector_memory, semantic_router,
embedding_indexer) into ONE shared singleton. ~90MB RAM for 1 model instead
of ~270MB for 3.

Usage:
    from ai_engine.core.encoder_singleton import get_shared_encoder, warmup_encoder
"""
import asyncio
import logging
from typing import Optional

logger = logging.getLogger("ai-engine")

_shared_encoder = None


def get_shared_encoder():
    """Get or lazily create the shared TextEmbedding model instance."""
    global _shared_encoder
    if _shared_encoder is None:
        from fastembed import TextEmbedding
        model = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        logger.info(f"[Encoder] Loading shared model: {model}")
        _shared_encoder = TextEmbedding(model_name=model)
        logger.info("[Encoder] Shared model loaded successfully.")
    return _shared_encoder


async def warmup_encoder():
    """Pre-load model in executor thread at startup for zero cold-start."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, get_shared_encoder)
    logger.info("[Encoder] Shared model warmed up and ready.")
