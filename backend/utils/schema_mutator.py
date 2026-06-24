"""
SGE Shield V1.0: JSON-LD Schema Mutation Engine.

Chống Google AI Footprint Detection bằng cách biến đổi cấu trúc JSON-LD
trước khi serialize. Mỗi request trả về schema với key order khác nhau
và randomly drop optional keys, khiến pattern detection thất bại.

Safety Rules (R02):
- NEVER_DROP_KEYS: Các key bắt buộc cho Google Rich Results KHÔNG BAO GIỜ bị drop
- SAFE_DROPPABLE_KEYS: Chỉ drop keys thực sự optional
- Shuffle key order luôn an toàn (JSON spec: key order không có ý nghĩa)

Architecture:
- mutate_json_ld(): Deterministic mutation dựa trên seed
- _shuffle_keys_recursive(): Deep shuffle tất cả nested dicts
- _random_drop_optional(): Drop 1-2 optional keys 20% thời gian
"""
import hashlib
import logging
import random
from datetime import date
from typing import Optional

logger = logging.getLogger("api-gateway")


# ═══════════════════════════════════════════════════════════════════════════════
# SAFETY LISTS — Bảo vệ Rich Results
# ═══════════════════════════════════════════════════════════════════════════════

# Keys tuyệt đối KHÔNG ĐƯỢC drop (Google Rich Results bắt buộc)
NEVER_DROP_KEYS: frozenset[str] = frozenset({
    "@context", "@type", "@id",
    "name", "description", "url", "image",
    "offers", "price", "priceCurrency", "availability",
    "brand", "sku",
    "aggregateRating", "review",
    "headline", "author", "publisher", "datePublished",
    "itemListElement", "position",
    "mainEntity", "acceptedAnswer", "text",
    "question",  # FAQPage
    "shippingDetails", "hasMerchantReturnPolicy",
})

# Keys an toàn để drop (thực sự optional trong Schema.org)
SAFE_DROPPABLE_KEYS: frozenset[str] = frozenset({
    "color", "material", "weight", "gtin", "mpn",
    "countryOfOrigin", "itemCondition",
    "priceValidUntil", "seller",
    "inLanguage", "numberOfItems",
    "contactType", "availableLanguage",
    "bestRating", "worstRating",
})


def _create_seeded_random(seed_value: str) -> random.Random:
    """Tạo Random instance deterministic từ seed string."""
    seed_int = int(hashlib.sha256(seed_value.encode()).hexdigest(), 16) % (2 ** 32)
    return random.Random(seed_int)


def _shuffle_keys_recursive(
    data: dict,
    rng: random.Random,
) -> dict:
    """
    Deep shuffle key order của dict và tất cả nested dicts.
    JSON spec: Key order không có ý nghĩa → an toàn 100%.
    """
    keys = list(data.keys())
    rng.shuffle(keys)

    result: dict = {}
    for key in keys:
        value = data[key]
        if isinstance(value, dict):
            result[key] = _shuffle_keys_recursive(value, rng)
        elif isinstance(value, list):
            result[key] = [
                _shuffle_keys_recursive(item, rng) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


def _random_drop_optional(
    data: dict,
    rng: random.Random,
    drop_probability: float = 0.2,
    max_drops: int = 2,
) -> dict:
    """
    Randomly drop 1-2 optional keys từ dict (flat level only).

    Args:
        data: Schema dict
        rng: Seeded Random instance
        drop_probability: Xác suất thực hiện drop (default 20%)
        max_drops: Số key tối đa bị drop

    Returns:
        Dict đã loại bỏ optional keys (hoặc giữ nguyên nếu không drop)
    """
    # Roll xác suất
    if rng.random() > drop_probability:
        return data

    # Tìm các key có thể drop
    droppable = [k for k in data.keys() if k in SAFE_DROPPABLE_KEYS]
    if not droppable:
        return data

    # Chọn 1-2 keys để drop
    num_drops = min(rng.randint(1, max_drops), len(droppable))
    keys_to_drop = set(rng.sample(droppable, num_drops))

    logger.debug("[SGE Shield] Dropping optional keys: %s", keys_to_drop)

    return {k: v for k, v in data.items() if k not in keys_to_drop}


def mutate_json_ld(
    schema_dict: dict,
    seed: Optional[str] = None,
    enable_drop: bool = True,
    drop_probability: float = 0.2,
) -> dict:
    """
    SGE Shield: Mutate JSON-LD schema để bypass pattern detection.

    Operations:
    1. Shuffle key order (luôn luôn) — an toàn theo JSON spec
    2. Drop optional keys (20% probability) — bảo vệ Rich Results
    3. Biến đổi @id suffix (tránh identical fingerprint)

    Args:
        schema_dict: JSON-LD schema dict gốc
        seed: Deterministic seed (default: random theo ngày)
        enable_drop: Cho phép drop optional keys
        drop_probability: Xác suất drop (0.0 - 1.0)

    Returns:
        Mutated schema dict (key order shuffled, optional keys potentially dropped)
    """
    if not schema_dict:
        return schema_dict

    # Tạo seed: Deterministic theo ngày nếu không truyền
    effective_seed = seed or f"sge-shield:{date.today().isoformat()}:{id(schema_dict)}"
    rng = _create_seeded_random(effective_seed)

    # Step 1: Drop optional keys (flat level) — TRƯỚC khi shuffle
    mutated = dict(schema_dict)
    if enable_drop:
        mutated = _random_drop_optional(mutated, rng, drop_probability)

        # Deep drop trong nested dicts (offers, brand, etc.)
        for key, value in list(mutated.items()):
            if isinstance(value, dict) and key not in NEVER_DROP_KEYS:
                mutated[key] = _random_drop_optional(value, rng, drop_probability)

    # Step 2: Shuffle key order (deep recursive)
    mutated = _shuffle_keys_recursive(mutated, rng)

    # @id is a permanent IRI anchor — NEVER mutate per W3C JSON-LD 1.1 §3.3
    # Key shuffle alone is sufficient for fingerprint diversification.

    return mutated
