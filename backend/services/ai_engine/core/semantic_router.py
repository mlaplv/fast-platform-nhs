import logging
import numpy as np
import asyncio
from typing import Dict, List, Tuple, Optional
from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
from backend.utils.text import normalize_vn
from backend.services.ai_engine.core.router_data import INTENT_TO_ACTION, SEMANTIC_ANCHORS

logger = logging.getLogger("api-gateway")

class SemanticRouter:
    """T1.5: Embedding-based Intent Classification (Phase 77)."""
    def __init__(self):
        self._anchor_embeddings: dict[str, np.ndarray] = {}
        self._anchor_matrix: Optional[np.ndarray] = None
        self._intent_labels: list[str] = []
        self._extra_cache: dict[str, np.ndarray] = {}
        self._is_ready = False

    def _refresh_matrix(self):
        if not self._anchor_embeddings: return
        self._intent_labels = sorted(self._anchor_embeddings.keys())
        matrix = np.stack([self._anchor_embeddings[it] for it in self._intent_labels]).astype(np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True); norms[norms == 0] = 1.0
        self._anchor_matrix = matrix / norms

    async def warmup(self):
        if self._is_ready and self._anchor_matrix is not None: return
        from backend.services.xohi_memory import xohi_memory
        try:
            stored = await xohi_memory.get_semantic_centroids()
            if stored:
                for it, blob in stored.items(): self._anchor_embeddings[it] = np.frombuffer(blob, dtype=np.float32)
                self._is_ready = True
        except Exception as e: logger.warning(f"[SemanticRouter] Redis fail: {e}")

        encoder = get_shared_encoder()
        if not encoder:
            from backend.services.ai_engine.core.encoder_singleton import warmup_encoder
            await warmup_encoder(); encoder = get_shared_encoder()

        if encoder:
            missing = [it for it in SEMANTIC_ANCHORS.keys() if it not in self._anchor_embeddings]
            if not missing: self._is_ready = True; return
            
            all_p, p_to_it = [], []
            for it in missing:
                for p in SEMANTIC_ANCHORS[it]: all_p.append(normalize_vn(p)); p_to_it.append(it)
            
            try:
                embs = await asyncio.get_event_loop().run_in_executor(None, lambda: list(encoder.embed(all_p)))
                groups = {}
                for it, emb in zip(p_to_it, embs): groups.setdefault(it, []).append(emb)
                for it, embs_list in groups.items():
                    centroid = np.mean(embs_list, axis=0).astype(np.float32)
                    self._anchor_embeddings[it] = centroid
                    await xohi_memory.update_semantic_centroid(it, centroid.tobytes())
                self._refresh_matrix(); self._is_ready = True
            except Exception as e: logger.error(f"[SemanticRouter] Warmup failed: {e}")
        if self._anchor_matrix is None: self._refresh_matrix()

    async def learn_intent(self, intent: str, text: str):
        encoder = get_shared_encoder()
        if not encoder: return
        try:
            vec = (await asyncio.get_event_loop().run_in_executor(None, lambda: list(encoder.embed([normalize_vn(text)]))))[0]
            if intent in self._anchor_embeddings:
                upd = (self._anchor_embeddings[intent] * 0.9 + vec * 0.1).astype(np.float32)
                self._anchor_embeddings[intent] = upd
                from backend.services.xohi_memory import xohi_memory
                await xohi_memory.update_semantic_centroid(intent, upd.tobytes())
                self._refresh_matrix()
        except: pass

    async def classify(self, text: str, extra_intents: Optional[dict[str, list[str]]] = None) -> tuple[str, float]:
        if not self._is_ready: await self.warmup()
        encoder = get_shared_encoder()
        if encoder is None or not self._anchor_embeddings: return "UNKNOWN", 0.0
        try:
            vec = (await asyncio.get_event_loop().run_in_executor(None, lambda: list(encoder.embed([normalize_vn(text)]))))[0].astype(np.float32)
            norm = np.linalg.norm(vec); vec = vec / norm if norm > 0 else vec
            best_it, best_s = "UNKNOWN", 0.0
            if self._anchor_matrix is not None:
                scores = np.dot(self._anchor_matrix, vec); idx = np.argmax(scores)
                best_s, best_it = float(scores[idx]), self._intent_labels[idx]
            if extra_intents:
                for it, phrases in extra_intents.items():
                    key = f"{it}:{hash(tuple(phrases))}"
                    if key in self._extra_cache: centroid = self._extra_cache[key]
                    else:
                        p_embs = await asyncio.get_event_loop().run_in_executor(None, lambda: list(encoder.embed([normalize_vn(p) for p in phrases])))
                        centroid = np.mean(p_embs, axis=0).astype(np.float32) if p_embs else None
                        if centroid is not None: self._extra_cache[key] = centroid
                        else: continue
                    score = np.dot(vec, centroid) / (np.linalg.norm(vec) * np.linalg.norm(centroid))
                    if score > best_s: best_s, best_it = float(score), it
            return best_it, best_s
        except: return "UNKNOWN", 0.0
