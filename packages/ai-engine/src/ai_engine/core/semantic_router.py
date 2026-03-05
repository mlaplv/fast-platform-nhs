"""
Tier 2A — Semantic Router (Phễu Lọc Tầng 2 - Phân loại Ngữ nghĩa)
===================================================================
Rule R7: Small Model First — dùng fastembed (Qdrant) để phân loại intent
bằng cosine similarity trước khi gọi Cloud LLM.
"""
import asyncio
import numpy as np
from typing import Optional

# Lazy-loaded singleton to avoid heavy import at startup
_model_instance = None
_intent_vectors: Optional[np.ndarray] = None
_intent_labels: list[str] = []

# Intent corpus: mẫu câu đại diện cho từng intent
INTENT_DEFINITIONS: dict[str, list[str]] = {
    "revenue": [
        "doanh thu tháng này",
        "tổng doanh thu",
        "revenue report",
        "monthly revenue",
        "doanh số bán hàng",
        "báo cáo doanh thu",
    ],
    "count_product": [
        "có bao nhiêu sản phẩm",
        "tổng số sản phẩm",
        "how many products",
        "count products",
        "số lượng sản phẩm",
    ],
    "count_order": [
        "có bao nhiêu đơn hàng",
        "tổng số đơn hàng",
        "how many orders",
        "count orders",
        "số đơn hàng",
    ],
    "stock": [
        "tồn kho",
        "hết hàng",
        "sắp hết hàng",
        "inventory status",
        "out of stock products",
        "stock check",
    ],
    "order_status": [
        "trạng thái đơn hàng",
        "order status",
        "đơn hàng đang giao",
        "kiểm tra trạng thái",
        "tracking order",
    ],
    "product_search": [
        "tìm sản phẩm",
        "search product",
        "tìm kiếm sản phẩm theo tên",
        "product lookup",
        "sản phẩm nào bán chạy",
    ],
    "create_draft": [
        "tạo sản phẩm mới",
        "thêm sản phẩm",
        "create new product",
        "cập nhật giá",
        "sửa thông tin đơn hàng",
        "xóa sản phẩm",
    ],
    "analyze": [
        "phân tích xu hướng bán hàng",
        "analyze sales trend",
        "đánh giá hiệu suất",
        "so sánh doanh thu",
        "business analysis",
        "tư vấn chiến lược kinh doanh",
    ],
    "article_search": [
        "chính sách cửa hàng",
        "quy định đổi trả",
        "vận chuyển thế nào",
        "địa chỉ cửa hàng ở đâu",
        "tin tức khuyến mãi",
        "shipping policy",
        "return policy",
        "store locations",
    ],
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
    Phân loại intent bằng fastembed (BGE-small-en-v1.5, 33M params).
    Lazy-load model on first call (singleton).
    """

    def __init__(self) -> None:
        self._ready = False

    async def _ensure_model(self) -> None:
        """Lazy-load fastembed model and pre-compute intent vectors."""
        global _model_instance, _intent_vectors, _intent_labels

        if self._ready and _model_instance is not None:
            return

        # Import fastembed lazily to avoid startup cost
        from fastembed import TextEmbedding

        if _model_instance is None:
            # Run blocking model init in thread pool (R3: Async First)
            loop = asyncio.get_event_loop()
            _model_instance = await loop.run_in_executor(
                None,
                lambda: TextEmbedding(model_name="BAAI/bge-small-en-v1.5"),
            )

        if _intent_vectors is None:
            # Build centroid vector for each intent from its example sentences
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

        self._ready = True

    async def classify(self, query: str) -> tuple[str, float]:
        """
        Classify a query into an intent.
        Returns (intent_name, confidence_score) where score ∈ [0, 1].
        """
        await self._ensure_model()

        # Embed the query
        loop = asyncio.get_event_loop()
        query_embedding_list = await loop.run_in_executor(
            None,
            lambda: list(_model_instance.embed([query])),
        )
        query_vec = query_embedding_list[0]

        # Compare against all intent centroids
        best_intent = "unknown"
        best_score = 0.0

        for i, intent_label in enumerate(_intent_labels):
            score = _cosine_similarity(query_vec, _intent_vectors[i])
            if score > best_score:
                best_score = score
                best_intent = intent_label

        return best_intent, best_score
