import logging
import numpy as np
import asyncio
from typing import Dict, List, Tuple, Optional
from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
from backend.utils.text import normalize_vn

logger = logging.getLogger("api-gateway")

# --- Phase 77: Deep Semantic Intent Mapping ---
# Maps semantic clusters to system actions.
INTENT_TO_ACTION = {
    "revenue_query": {
        "intent_type": "DATA_QUERY",
        "target": "revenue",
        "action": "COUNT",
        "message": "Dạ sếp, đây là biểu đồ doanh thu ạ."
    },
    "order_query": {
        "intent_type": "DATA_QUERY",
        "target": "order",
        "action": "COUNT",
        "message": "Dạ, em đang thống kê đơn hàng cho sếp."
    },
    "product_query": {
        "intent_type": "DATA_QUERY",
        "target": "product",
        "action": "COUNT",
        "message": "Dạ, đây là tình hình kho hàng và sản phẩm ạ."
    },
    "news_create": {
        "intent_type": "CONTENT_CREATE",
        "target": "news",
        "action": "CONTENT_CREATE",
        "ui_action": "show_content_factory",
        "message": "Dạ sếp, em bắt đầu lên ý tưởng bài viết ngay đây."
    },
    "ui_navigation": {
        "intent_type": "UI_NAV",
        "target": "none",
        "action": "READ",
        "message": "Dạ, em chuyển trang cho sếp đây ạ."
    },
    "session_sleep": {
        "intent_type": "SESSION_CTRL",
        "target": "none",
        "action": "HARDWARE_SLEEP",
        "category": "SESSION_CTRL",
        "message": "Hẹn gặp lại sếp ạ."
    },
    "session_wake": {
        "intent_type": "SESSION_CTRL",
        "target": "none",
        "action": "WAKE_ROUTINE",
        "category": "SESSION_CTRL",
        "message": "Dạ, em nghe đây sếp."
    },
    "learn_command": {
        "intent_type": "LEARN_COMMAND",
        "target": "none",
        "action": "MUTATE",
        "message": ""
    }
}

# --- Anchor Phrases for Semantic Matching (Zero-Allocation Strategy) ---
SEMANTIC_ANCHORS = {
    "revenue_query": [
        "doanh thu hôm nay thế nào", "xem báo cáo tài chính", "tiền về bao nhiêu rồi",
        "tình hình doanh số", "biểu đồ tăng trưởng", "doanh thu tháng này"
    ],
    "order_query": [
        "có bao nhiêu đơn hàng", "kiểm tra đơn mới", "danh sách hóa đơn",
        "tình trạng vận chuyển", "bill hôm nay", "đơn hàng thành công"
    ],
    "product_query": [
        "còn bao nhiêu hàng trong kho", "sản phẩm nào bán chạy", "kiểm tra tồn kho",
        "danh sách sản phẩm", "giá của mặt hàng này"
    ],
    "news_create": [
        "viết cho tôi bài báo", "sáng tác nội dung viral", "tạo bài viết mới",
        "lên kế hoạch content", "viết bài đăng facebook", "soạn thảo tin tức"
    ],
    "ui_navigation": [
        "mở cài đặt", "vào trang chủ", "xem danh mục", "đi tới trang quản trị",
        "mở mục khách hàng", "vào phần báo cáo"
    ],
    "session_sleep": [
        "cút đi", "ngủ đi", "tạm biệt", "hẹn gặp lại", "tắt máy", "thoát"
    ],
    "session_wake": [
        "xohi ơi", "dậy đi", "alo xohi", "nghe này", "bắt đầu làm việc"
    ],
    "learn_command": [
        "học lệnh 'vào camp' là mở chiến dịch", "dạy em khi nói X thì mở Y",
        "nhớ nhé sếp bảo Z là mở K", "học lệnh mới", "dạy XoHi học lệnh",
        "nhớ nhé sếp bảo 'về nhà' là mở trang chủ", "học 'biến' là 'tạm biệt'"
    ]
}

class SemanticRouter:
    """
    T1.5: Embedding-based Intent Classification (Phase 77).
    Uses local fastembed to classify intents in <30ms without cloud LLMs.
    """
    def __init__(self):
        self._anchor_embeddings: Dict[str, np.ndarray] = {}
        self._anchor_matrix: Optional[np.ndarray] = None
        self._intent_labels: List[str] = []
        self._extra_cache: Dict[str, np.ndarray] = {} # Phase 77: Cache for dynamic/user intents
        self._is_ready = False

    def _refresh_matrix(self):
        """Builds and pre-normalizes the anchor matrix for zero-allocation matching."""
        if not self._anchor_embeddings:
            return

        self._intent_labels = sorted(self._anchor_embeddings.keys())
        # Stack all centroids into a single Matrix (M x D)
        matrix = np.stack([self._anchor_embeddings[it] for it in self._intent_labels]).astype(np.float32)

        # L2 Normalization: M = M / ||M||
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        # Avoid division by zero
        norms[norms == 0] = 1.0
        self._anchor_matrix = matrix / norms
        logger.debug(f"[SemanticRouter] Matrix refreshed: {self._anchor_matrix.shape}")

    async def warmup(self):
        """Initializes encoder and pre-calculates anchor embeddings."""
        if self._is_ready and self._anchor_matrix is not None:
            return

        from backend.services.xohi_memory import xohi_memory

        # 1. Try loading from Redis first (Zero-Allocation Boot)
        try:
            stored_centroids = await xohi_memory.get_semantic_centroids()
            if stored_centroids:
                logger.info(f"[SemanticRouter] Loading {len(stored_centroids)} centroids from Redis...")
                for intent, blob in stored_centroids.items():
                    # Redis stores bytes, we need to convert back to float32 numpy array
                    self._anchor_embeddings[intent] = np.frombuffer(blob, dtype=np.float32)
                self._is_ready = True
                # Fall through to check if we need to calculate missing ones
        except Exception as e:
            logger.warning(f"[SemanticRouter] Redis load failed, falling back to calculation: {e}")

        encoder = get_shared_encoder()
        if encoder is None:
            logger.warning("[SemanticRouter] Encoder not warmed up. Attempting sync load...")
            from backend.services.ai_engine.core.encoder_singleton import warmup_encoder
            await warmup_encoder()
            encoder = get_shared_encoder()

        if encoder:
            # Check if we have all core intents. If not, calculate.
            missing_intents = [it for it in SEMANTIC_ANCHORS.keys() if it not in self._anchor_embeddings]

            if not missing_intents:
                self._is_ready = True
                return

            logger.info(f"[SemanticRouter] Calculating centroids for {len(missing_intents)} intents...")
            loop = asyncio.get_event_loop()

            all_phrases = []
            phrase_to_intent = []
            for intent in missing_intents:
                phrases = SEMANTIC_ANCHORS[intent]
                for p in phrases:
                    all_phrases.append(normalize_vn(p))
                    phrase_to_intent.append(intent)

            try:
                embeddings = await loop.run_in_executor(None, lambda: list(encoder.embed(all_phrases)))

                intent_groups = {}
                for intent, emb in zip(phrase_to_intent, embeddings):
                    if intent not in intent_groups:
                        intent_groups[intent] = []
                    intent_groups[intent].append(emb)

                for intent, embs in intent_groups.items():
                    centroid = np.mean(embs, axis=0).astype(np.float32)
                    self._anchor_embeddings[intent] = centroid
                    # Persist to Redis for next boot
                    await xohi_memory.update_semantic_centroid(intent, centroid.tobytes())

                self._refresh_matrix()
                self._is_ready = True
                logger.info("[SemanticRouter] Warmup complete. All centroids synchronized.")
            except Exception as e:
                logger.error(f"[SemanticRouter] Warmup failed: {e}")

        # Final safety check
        if self._anchor_matrix is None:
            self._refresh_matrix()

    def _cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    async def learn_intent(self, intent: str, text: str):
        """Phase 77: Dynamic Intent Learning from user feedback."""
        encoder = get_shared_encoder()
        if not encoder: return

        norm_text = normalize_vn(text)
        loop = asyncio.get_event_loop()
        try:
            new_vec = (await loop.run_in_executor(None, lambda: list(encoder.embed([norm_text]))))[0]

            if intent in self._anchor_embeddings:
                # Bayesian Update (Moving Average) - Weight existing 0.9, new 0.1
                old_vec = self._anchor_embeddings[intent]
                updated_vec = (old_vec * 0.9 + new_vec * 0.1).astype(np.float32)
                self._anchor_embeddings[intent] = updated_vec

                from backend.services.xohi_memory import xohi_memory
                await xohi_memory.update_semantic_centroid(intent, updated_vec.tobytes())
                self._refresh_matrix()
                logger.debug(f"[SemanticRouter] Learned/Refined intent '{intent}' from: '{text}'")
        except Exception as e:
            logger.error(f"[SemanticRouter] Learning failed: {e}")

    async def classify(self, text: str, extra_intents: Optional[Dict[str, List[str]]] = None) -> Tuple[str, float]:
        """
        Classifies input text against anchor centroids.
        Returns (intent_name, score).
        """
        if not self._is_ready:
            await self.warmup()

        encoder = get_shared_encoder()
        if encoder is None or not self._anchor_embeddings:
            return "UNKNOWN", 0.0

        norm_text = normalize_vn(text)
        loop = asyncio.get_event_loop()

        try:
            # Embed the query
            query_vec = (await loop.run_in_executor(None, lambda: list(encoder.embed([norm_text]))))[0]
            query_vec = query_vec.astype(np.float32)

            # Pre-normalize query vector for cosine similarity via dot product
            q_norm = np.linalg.norm(query_vec)
            if q_norm > 0:
                query_vec = query_vec / q_norm

            best_intent = "UNKNOWN"
            best_score = 0.0

            # 1. Vectorized Matrix-Vector Multiplication for Core Anchors
            if self._anchor_matrix is not None:
                scores = np.dot(self._anchor_matrix, query_vec)
                idx = np.argmax(scores)
                best_score = float(scores[idx])
                best_intent = self._intent_labels[idx]

            # 2. Check dynamic extra_intents (e.g., custom wake/sleep words)
            if extra_intents:
                for intent, phrases in extra_intents.items():
                    # Phase 77: Zero-Allocation Cache for Extra Intents
                    cache_key = f"{intent}:{hash(tuple(phrases))}"
                    if cache_key in self._extra_cache:
                        centroid = self._extra_cache[cache_key]
                    else:
                        norm_phrases = [normalize_vn(p) for p in phrases]
                        p_embs = await loop.run_in_executor(None, lambda: list(encoder.embed(norm_phrases)))
                        if p_embs:
                            centroid = np.mean(p_embs, axis=0).astype(np.float32)
                            self._extra_cache[cache_key] = centroid
                        else:
                            continue

                    score = self._cosine_similarity(query_vec, centroid)
                    if score > best_score:
                        best_score = score
                        best_intent = intent

            return best_intent, float(best_score)
        except Exception as e:
            logger.error(f"[SemanticRouter] Classification failed: {e}")
            return "UNKNOWN", 0.0
