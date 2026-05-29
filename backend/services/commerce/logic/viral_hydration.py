import logging
import contextvars
import json
from typing import Dict, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import current_tenant_id
from backend.database.models.promotion import Voucher
from backend.services.xohi_memory import xohi_memory

logger = logging.getLogger("api-gateway")

class CachedVoucher:
    def __init__(self, id: str, title: Optional[str], metadata_json: Optional[dict]):
        self.id = id
        self.title = title
        self.metadata_json = metadata_json

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "metadata_json": self.metadata_json
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CachedVoucher":
        return cls(
            id=data["id"],
            title=data.get("title"),
            metadata_json=data.get("metadata_json")
        )

# L1 Request-Scoped Cache: Thread- & Async-safe context variables (0ns latency)
# Maps tenant_id -> CachedVoucher (or False to represent positive validation of non-existence)
_request_voucher_cache = contextvars.ContextVar("_request_voucher_cache", default=None)

def _get_l1_cache(tenant: str) -> Tuple[bool, Optional[CachedVoucher]]:
    cache_dict = _request_voucher_cache.get()
    if cache_dict is not None and tenant in cache_dict:
        val = cache_dict[tenant]
        return True, (val if val is not False else None)
    return False, None

def _set_l1_cache(tenant: str, voucher: Optional[CachedVoucher]) -> None:
    cache_dict = _request_voucher_cache.get()
    if cache_dict is None:
        cache_dict = {}
        _request_voucher_cache.set(cache_dict)
    cache_dict[tenant] = voucher if voucher is not None else False

# L2 Redis Distributed Cache: Handles shared cache across clustered API replicas (1ms latency)
async def _get_l2_cache(tenant: str) -> Tuple[bool, Optional[CachedVoucher]]:
    if not xohi_memory._use_redis or not xohi_memory.client:
        return False, None
    try:
        key = f"cache:v2.2:viral_voucher:{tenant}"
        raw_val = await xohi_memory.client.get(key)
        if raw_val:
            if raw_val == "NONE":
                return True, None
            data = json.loads(raw_val)
            return True, CachedVoucher.from_dict(data)
    except Exception as e:
        logger.debug(f"🧬 [ViralHydration] L2 Cache read failed: {e}")
    return False, None

async def _set_l2_cache(tenant: str, voucher: Optional[CachedVoucher]) -> None:
    if not xohi_memory._use_redis or not xohi_memory.client:
        return
    try:
        key = f"cache:v2.2:viral_voucher:{tenant}"
        if voucher is None:
            await xohi_memory.client.set(key, "NONE", ex=60)
        else:
            await xohi_memory.client.set(key, json.dumps(voucher.to_dict(), ensure_ascii=False), ex=60)
    except Exception as e:
        logger.debug(f"🧬 [ViralHydration] L2 Cache write failed: {e}")

async def hydrate_viral_config_logic(db_session: AsyncSession, row_dict: Dict) -> None:
    """
    Elite V2.2: Dynamic hydration from the Promotion system (Isolated Logic).
    Uses the 'Single-Active-Viral' voucher as the Global Source of Truth (SSOT).
    Tự động kích hoạt chiến dịch cho tất cả sản phẩm được áp dụng mà không cần cấu hình thủ công ở từng sản phẩm.
    """
    metadata = row_dict.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        
    tenant = current_tenant_id.get()
    if not tenant:
        tenant = str(row_dict.get("tenant_id", "osmo.vn"))
        
    # --- DOUBLE-LAYER CACHING ENGINE (L1 Memory + L2 Redis) ---
    
    # 1. Try L1 Request-Scoped Cache (0ns)
    has_l1, voucher = _get_l1_cache(tenant)
    if not has_l1:
        # 2. Try L2 Redis Distributed Cache (1ms)
        has_l2, voucher = await _get_l2_cache(tenant)
        if not has_l2:
            # 3. Fallback to L3 Database Query
            stmt = select(Voucher).where(
                Voucher.is_viral == True,
                Voucher.is_active == True,
                Voucher.tenant_id == tenant
            ).limit(1)
            res = await db_session.execute(stmt)
            db_voucher = res.scalar_one_or_none()
            
            if not db_voucher:
                stmt = select(Voucher).where(Voucher.is_viral == True, Voucher.is_active == True).limit(1)
                res = await db_session.execute(stmt)
                db_voucher = res.scalar_one_or_none()
                
            if db_voucher:
                voucher = CachedVoucher(
                    id=db_voucher.id,
                    title=db_voucher.title,
                    metadata_json=db_voucher.metadata_json
                )
            else:
                voucher = None
                
            # Populate L2 Distributed Cache
            await _set_l2_cache(tenant, voucher)
            
        # Populate L1 Request-scoped Cache
        _set_l1_cache(tenant, voucher)
        
    # --- END CACHING ENGINE ---

    if not voucher:
        logger.debug(f"🧬 [ViralHydration] No active master viral voucher found for tenant {tenant} (Normal if campaign is disabled)")
        return

    # 2. Kiểm tra phạm vi áp dụng của Voucher
    v_metadata = voucher.metadata_json or {}
    applicable_ids = v_metadata.get("applicable_product_ids")
    
    product_id = str(row_dict.get("id", ""))
    
    # Nếu voucher chỉ định áp dụng cho một số sản phẩm và sản phẩm này không nằm trong đó -> bỏ qua
    if applicable_ids and isinstance(applicable_ids, list) and len(applicable_ids) > 0:
        if product_id not in applicable_ids:
            return

    # 3. Tự động kích hoạt & Hydrate dữ liệu chiến dịch từ Voucher
    v_config = v_metadata.get("viral_suite", {})
    master_id = str(voucher.id)
    
    metadata["viral_suite"] = {
        "enabled": True,
        "voucher_id": master_id,
        "share_target": v_config.get("share_target", 10),
        "share_reward_label": v_config.get("voucher_label") or voucher.title or "QUÀ TẶNG LAN TỎA",
        "share_cta": v_config.get("cta_text") or "CHIA SẺ NHẬN QUÀ",
        "share_text": v_config.get("share_text") or "",
        "share_count": metadata.get("share_count", 0),
        "likes_count": metadata.get("likes", 0)
    }
    
    if not isinstance(metadata.get("share_promotion"), dict):
        metadata["share_promotion"] = {}
        
    metadata["share_promotion"].update({
        "enabled": True,
        "voucher_id": master_id,
        "voucher_label": v_config.get("voucher_label") or voucher.title or "QUÀ TẶNG LAN TỎA",
        "cta_text": v_config.get("cta_text") or "CHIA SẺ NHẬN QUÀ",
        "share_text": v_config.get("share_text") or "",
    })
    
    metadata["viral_suite"]["share_promotion"] = metadata["share_promotion"]
    row_dict["metadata"] = metadata
    row_dict["_master_viral_id"] = master_id
    
    logger.info(f"🧬 [ViralHydration] ULTRA-HYDRATED master {master_id} for product {row_dict.get('id')}")

def sanitize_vouchers_logic(row_dict: Dict) -> None:
    """
    Elite V2.2: Anti-Leakage Protocol (Isolated Logic).
    Lọc bỏ các Voucher Viral khỏi metadata công khai để tránh người dùng 'soi' được mã khi chưa share.
    """
    metadata = row_dict.get("metadata")
    if not isinstance(metadata, dict):
        return
        
    vouchers = metadata.get("vouchers")
    if not isinstance(vouchers, list):
        return
        
    share_promo = metadata.get("share_promotion")
    promo_v_id = share_promo.get("voucher_id") if isinstance(share_promo, dict) else None
    
    filtered = []
    for v in vouchers:
        if isinstance(v, dict):
            v_id = str(v.get("id", "") or "").upper()
            v_label = str(v.get("label", "") or "").upper()
            v_actual_id = str(v.get("id", "") or "")
        else:
            v_id = str(getattr(v, "id", "") or "").upper()
            v_label = str(getattr(v, "label", "") or "").upper()
            v_actual_id = str(getattr(v, "id", "") or "")
            
        # Kiểm tra ID hoặc Nhãn chứa từ khóa nhạy cảm
        is_viral = (promo_v_id and v_actual_id == promo_v_id) or \
                    "VIRAL" in v_id or \
                    "LAN TOA" in v_id or \
                    "LAN TỎA" in v_id or \
                    "LAN TOA" in v_label or \
                    "LAN TỎA" in v_label
        
        if not is_viral:
            filtered.append(v)
    
    metadata["vouchers"] = filtered
