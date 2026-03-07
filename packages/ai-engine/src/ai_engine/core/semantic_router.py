"""
Tier 1.5 — Semantic Router (Embedding-Based Intent Classification)
===================================================================
Rule R7: Small Model First — dùng fastembed (sentence-transformers)
để phân loại intent bằng cosine similarity TRƯỚC KHI gọi Cloud LLM.

Model: paraphrase-multilingual-MiniLM-L12-v2 (hỗ trợ tiếng Việt native).
Latency: ~50ms first call, ~10ms cached.
"""
import asyncio
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger("api-gateway")

# Lazy-loaded singleton — V56.0: now uses shared encoder
# Import before class to avoid circular deps
from ai_engine.core.encoder_singleton import get_shared_encoder
_model_instance = None  # Will be set to shared encoder on first use
_intent_vectors: Optional[np.ndarray] = None
_intent_labels: list[str] = []

# ═══════════════════════════════════════════════════════════════════
# INTENT CORPUS: Mẫu câu đại diện cho từng intent (Vi + En)
# Mỗi intent cần ít nhất 4-6 câu mẫu để centroid chính xác.
# ═══════════════════════════════════════════════════════════════════
INTENT_DEFINITIONS: dict[str, list[str]] = {
    # --- DATA QUERY (COUNT/SUM) ---
    "data_revenue": [
        "doanh thu tháng này", "tổng doanh thu", "doanh số bán hàng",
        "báo cáo doanh thu", "revenue report", "doanh thu hôm nay",
        "doanh số tháng này bao nhiêu", "thu nhập hôm nay",
        "tiền vào tháng này", "doanh thu tuần này",
    ],
    "data_order": [
        "có bao nhiêu đơn hàng", "tổng số đơn hàng", "số đơn hàng hôm nay",
        "đơn hàng tháng này", "bao nhiêu bill", "count orders",
        "đơn hàng chưa xử lý", "đơn hàng mới",
    ],
    "data_product": [
        "có bao nhiêu sản phẩm", "tổng số sản phẩm", "số lượng sản phẩm",
        "sản phẩm trong kho", "tồn kho bao nhiêu", "count products",
        "hàng còn bao nhiêu", "sản phẩm hết hàng",
    ],
    "data_user": [
        "có bao nhiêu khách hàng", "tổng số người dùng", "số nhân viên",
        "bao nhiêu tài khoản", "count users", "khách mới hôm nay",
    ],

    # --- UI NAVIGATION ---
    "nav_revenue": [
        "mở biểu đồ doanh thu", "xem biểu đồ", "show revenue chart",
        "mở báo cáo", "xem doanh thu", "hiển thị biểu đồ",
    ],
    "nav_order": [
        "mở đơn hàng", "xem đơn hàng", "quản lý đơn hàng",
        "vào trang đơn hàng", "show orders", "mở quản lý đơn",
    ],
    "nav_product": [
        "mở sản phẩm", "xem sản phẩm", "quản lý sản phẩm",
        "vào trang sản phẩm", "show products", "mở danh sách hàng",
    ],
    "nav_user": [
        "mở người dùng", "xem nhân viên", "quản lý tài khoản",
        "vào trang người dùng", "show users", "mở danh sách nhân viên",
    ],
    "nav_news": [
        "mở tin tức", "xem bài viết", "quản lý tin tức",
        "vào trang bài viết", "show articles", "mở danh sách bài viết",
    ],
    "nav_category": [
        "mở danh mục", "xem danh mục", "quản lý danh mục",
        "vào trang danh mục", "show categories",
    ],
    "nav_settings": [
        "cài đặt giọng nói", "mở cài đặt", "voice settings",
        "chỉnh cài đặt xohi", "cấu hình giọng nói", "mở giọng nói",
        "cấu hình xohi", "voice setting", "mở voice setting",
    ],

    # --- MUTATION ---
    "mutate": [
        "tạo sản phẩm mới", "thêm nhân viên", "xóa sản phẩm",
        "sửa đơn hàng", "cập nhật thông tin", "tạo bài viết mới",
        "thêm danh mục", "xóa tài khoản", "create new product",
        "thêm sản phẩm tên là", "tạo nhân viên mới",
    ],

    # --- DEEP ANALYSIS ---
    "analyze": [
        "phân tích xu hướng bán hàng", "đánh giá hiệu suất",
        "so sánh doanh thu tháng trước", "tư vấn chiến lược kinh doanh",
        "analyze sales trend", "sản phẩm nào bán chạy nhất",
        "tại sao doanh thu giảm", "đề xuất cải thiện",
    ],

    # --- GREETING / CHITCHAT ---
    "greeting": [
        "chào em", "xin chào", "khỏe không", "hello",
        "chào xohi", "hi em", "em ơi", "hey",
    ],

    # --- SESSION CONTROL ---
    "session_wake": [
        "xohi", "hey xohi", "một hai ba", "1 2 3",
        "xô hi", "xo hi ơi", "hey sếp",
    ],
    "session_sleep": [
        "tạm biệt", "bye", "cút", "thoát", "ngủ đi",
        "tắt đi", "goodbye", "hẹn gặp lại",
    ],
}

# ═══════════════════════════════════════════════════════════════════
# INTENT → C.O.R.E MAPPING
# ═══════════════════════════════════════════════════════════════════
INTENT_TO_ACTION = {
    "data_revenue":  {"intent_type": "DATA_QUERY", "action": "COUNT", "target": "revenue"},
    "data_order":    {"intent_type": "DATA_QUERY", "action": "COUNT", "target": "order"},
    "data_product":  {"intent_type": "DATA_QUERY", "action": "COUNT", "target": "product"},
    "data_user":     {"intent_type": "DATA_QUERY", "action": "COUNT", "target": "user"},
    "nav_revenue":   {"intent_type": "UI_NAV", "action": "READ", "target": "revenue", "ui_action": "show_revenue_chart"},
    "nav_order":     {"intent_type": "UI_NAV", "action": "READ", "target": "order", "ui_action": "show_order_management"},
    "nav_product":   {"intent_type": "UI_NAV", "action": "READ", "target": "product", "ui_action": "show_product_management"},
    "nav_user":      {"intent_type": "UI_NAV", "action": "READ", "target": "user", "ui_action": "show_user_management"},
    "nav_news":      {"intent_type": "UI_NAV", "action": "READ", "target": "news", "ui_action": "show_news_management"},
    "nav_category":  {"intent_type": "UI_NAV", "action": "READ", "target": "category", "ui_action": "show_category_management"},
    "nav_settings":  {"intent_type": "UI_NAV", "action": "READ", "target": "none", "ui_action": "show_voice_settings"},
    "mutate":        {"intent_type": "MUTATE", "action": "MUTATE", "target": "none"},
    "analyze":       {"intent_type": "DEEP_ANALYSIS", "action": "ANALYZE", "target": "none"},
    "greeting":      {"intent_type": "DEEP_ANALYSIS", "action": "ANALYZE", "target": "none"},
    "session_wake":  {"intent_type": "SESSION_CTRL", "action": "READ", "target": "none", "category": "SESSION_CTRL"},
    "session_sleep": {"intent_type": "SESSION_CTRL", "action": "HARDWARE_SLEEP", "target": "none", "category": "SESSION_CTRL", "message": "Hẹn gặp lại sếp."},
}


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


class SemanticRouter:
    """
    Embedding-based Intent Classifier (T1.5).
    Uses fastembed with multilingual model for Vietnamese support.
    Lazy-loads model on first call (singleton pattern).
    """

    def __init__(self) -> None:
        self._ready = False

    async def warmup(self) -> None:
        """Pre-load model at server startup for zero latency on first request."""
        await self._ensure_model()
        logger.info("[T1.5 SemanticRouter] Warmed up and ready.")

    async def _ensure_model(self) -> None:
        """Lazy-load fastembed model and pre-compute intent centroid vectors."""
        global _model_instance, _intent_vectors, _intent_labels

        if self._ready and _model_instance is not None:
            return

        # V56.0: Use shared encoder singleton instead of creating own TextEmbedding
        if _model_instance is None:
            loop = asyncio.get_event_loop()
            _model_instance = await loop.run_in_executor(None, get_shared_encoder)
            logger.info("[T1.5 SemanticRouter] Using shared multilingual model.")

        if _intent_vectors is None:
            labels: list[str] = []
            centroids: list[np.ndarray] = []

            for intent_name, examples in INTENT_DEFINITIONS.items():
                loop = asyncio.get_event_loop()
                embeddings = await loop.run_in_executor(
                    None,
                    lambda ex=examples: list(_model_instance.embed(ex)),
                )
                centroid = np.mean(embeddings, axis=0)
                labels.append(intent_name)
                centroids.append(centroid)

            _intent_labels = labels
            _intent_vectors = np.array(centroids)
            logger.info(f"[T1.5 SemanticRouter] {len(labels)} intent centroids computed.")

        self._ready = True

    async def classify(self, query: str, extra_intents: Optional[dict[str, list[str]]] = None) -> tuple[str, float]:
        """
        Classify a query into an intent using cosine similarity.
        Supports dynamic extra_intents (e.g. user-specific wake words).
        Returns (intent_name, confidence_score) where score ∈ [0, 1].
        """
        await self._ensure_model()

        loop = asyncio.get_event_loop()
        query_embedding_list = await loop.run_in_executor(
            None,
            lambda: list(_model_instance.embed([query])),
        )
        query_vec = query_embedding_list[0]

        best_intent = "unknown"
        best_score = 0.0

        # Check standard intents
        for i, intent_label in enumerate(_intent_labels):
            score = _cosine_similarity(query_vec, _intent_vectors[i])
            if score > best_score:
                best_score = score
                best_intent = intent_label

        # Check dynamic extra intents (CTO R2.1: Semantic Wake Triggers)
        if extra_intents:
            for intent_name, examples in extra_intents.items():
                if not examples: continue
                # On-the-fly embedding for small sample sets (Wake Words)
                # For production scalability, these should be cached per-user in Redis.
                extra_embeddings = await loop.run_in_executor(
                    None,
                    lambda ex=examples: list(_model_instance.embed(ex)),
                )
                extra_centroid = np.mean(extra_embeddings, axis=0)
                score = _cosine_similarity(query_vec, extra_centroid)
                if score > best_score:
                    best_score = score
                    best_intent = intent_name

        return best_intent, best_score
