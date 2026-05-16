import logging
from typing import Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import current_tenant_id
from backend.database.models.promotion import Voucher

logger = logging.getLogger("api-gateway")

async def hydrate_viral_config_logic(db_session: AsyncSession, row_dict: Dict) -> None:
    """
    Elite V2.2: Dynamic hydration from the Promotion system (Isolated Logic).
    Uses the 'Single-Active-Viral' voucher as the Global Source of Truth (SSOT).
    """
    metadata = row_dict.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        
    share_promo = metadata.get("share_promotion")
    if not isinstance(share_promo, dict) or not share_promo.get("enabled"):
        return
        
    tenant = current_tenant_id.get()
    if not tenant:
        tenant = str(row_dict.get("tenant_id", "osmo.vn"))
        
    stmt = select(Voucher).where(
        Voucher.is_viral == True,
        Voucher.is_active == True,
        Voucher.tenant_id == tenant
    ).limit(1)
    res = await db_session.execute(stmt)
    voucher = res.scalar_one_or_none()
    
    if not voucher:
        stmt = select(Voucher).where(Voucher.is_viral == True, Voucher.is_active == True).limit(1)
        res = await db_session.execute(stmt)
        voucher = res.scalar_one_or_none()

    if voucher and voucher.metadata_json:
        v_config = voucher.metadata_json.get("viral_suite", {})
        master_id = str(voucher.id)
        
        metadata["viral_suite"] = {
            "enabled": True,
            "voucher_id": master_id,
            "share_target": v_config.get("share_target", 10),
            "share_reward_label": v_config.get("voucher_label", voucher.title or "QUÀ TẶNG LAN TỎA"),
            "share_cta": v_config.get("cta_text", "CHIA SẺ NHẬN QUÀ"),
            "share_text": v_config.get("share_text", ""),
            "share_count": metadata.get("share_count", 0),
            "likes_count": metadata.get("likes", 0)
        }
        
        if not isinstance(metadata.get("share_promotion"), dict):
            metadata["share_promotion"] = {}
            
        metadata["share_promotion"].update({
            "enabled": True,
            "voucher_id": master_id,
            "voucher_label": v_config.get("voucher_label", metadata["share_promotion"].get("voucher_label")),
            "cta_text": v_config.get("cta_text", metadata["share_promotion"].get("cta_text")),
            "share_text": v_config.get("share_text", metadata["share_promotion"].get("share_text")),
        })
        
        metadata["viral_suite"]["share_promotion"] = metadata["share_promotion"]
        row_dict["metadata"] = metadata
        row_dict["_master_viral_id"] = master_id
        
        logger.info(f"🧬 [ViralHydration] ULTRA-HYDRATED master {master_id} for product {row_dict.get('id')}")
    else:
        logger.warning(f"⚠️ [ViralHydration] No active master viral voucher found for tenant {tenant}")

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
        v_id = str(v.get("id", "")).upper()
        v_label = str(v.get("label", "")).upper()
        
        # Kiểm tra ID hoặc Nhãn chứa từ khóa nhạy cảm
        is_viral = (promo_v_id and str(v.get("id", "")) == promo_v_id) or \
                    "VIRAL" in v_id or \
                    "LAN TOA" in v_id or \
                    "LAN TỎA" in v_id or \
                    "LAN TOA" in v_label or \
                    "LAN TỎA" in v_label
        
        if not is_viral:
            filtered.append(v)
    
    metadata["vouchers"] = filtered
