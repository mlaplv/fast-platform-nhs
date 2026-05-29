import logging
import time
from typing import Dict, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import current_tenant_id
from backend.database.models.promotion import Voucher

logger = logging.getLogger("api-gateway")

class CachedVoucher:
    def __init__(self, id: str, title: Optional[str], metadata_json: Optional[dict]):
        self.id = id
        self.title = title
        self.metadata_json = metadata_json

# TTL Cache: {tenant_id: (CachedVoucher, timestamp)}
_viral_voucher_cache: Dict[str, Tuple[Optional[CachedVoucher], float]] = {}
CACHE_TTL = 5.0 # 5 seconds to eliminate N+1 database roundtrips while maintaining rapid configuration syncs

def _get_cached_voucher(tenant: str) -> Tuple[bool, Optional[CachedVoucher]]:
    now = time.time()
    if tenant in _viral_voucher_cache:
        val, expiry = _viral_voucher_cache[tenant]
        if now - expiry < CACHE_TTL:
            return True, val
    return False, None

def _set_cached_voucher(tenant: str, voucher: Optional[CachedVoucher]) -> None:
    _viral_voucher_cache[tenant] = (voucher, time.time())

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
        
    # 1. Check cache first to prevent N+1 query loops
    has_cache, cached_val = _get_cached_voucher(tenant)
    if has_cache:
        voucher = cached_val
    else:
        # Query DB
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
            
        _set_cached_voucher(tenant, voucher)

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
