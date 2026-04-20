import unicodedata
import logging
from typing import Optional, List, Dict, TypedDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.commerce import Order
from backend.database.models.auth import User

logger = logging.getLogger("api-gateway")

class LookupResult(TypedDict):
    is_recurring: bool
    is_trusted_device: bool
    name_masked: Optional[str]
    address_masked: Optional[str]
    name: Optional[str]
    address: Optional[str]

class VerifyResult(TypedDict):
    verified: bool
    address: Optional[str]

def _normalize_name(s: str) -> str:
    """Normalize VN name for comparison: lowercase, strip accents/whitespace."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower().strip())
        if unicodedata.category(c) != "Mn"
    )

def _mask_name(name: str) -> str:
    if not name: return ""
    parts = name.split()
    if len(parts) == 1:
        return f"{name[0]}***"
    if len(parts) == 2:
        return f"{parts[0][0]}*** {parts[-1]}"
    return f"{parts[0][0]}*** {parts[-1]}"

def _mask_address(addr: str) -> str:
    if not addr: return ""
    parts = addr.split(",")
    if len(parts) < 2:
        return f"{addr[:5]}***"
    street = parts[0].strip()
    masked_street = f"{street[:4]}***"
    return f"{masked_street}, {', '.join(parts[1:])}"

class IdentityShield:
    """Elite V2.2: Recognition & Identity Protection Service."""
    
    @staticmethod
    async def lookup_customer(
        db_session: AsyncSession,
        phone: str,
        ox_cookie: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> LookupResult:
        """Recognition with Identity Shield Cookie V3.0."""
        last_order = None
        
        if user_id:
            stmt = select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc()).limit(1)
            res = await db_session.execute(stmt)
            last_order = res.scalar_one_or_none()

        if not last_order and phone:
            stmt = select(Order).where(Order.customer_phone == phone).order_by(Order.created_at.desc()).limit(1)
            res = await db_session.execute(stmt)
            last_order = res.scalar_one_or_none()

        is_trusted = (last_order.id == ox_cookie) if last_order and ox_cookie else False
        is_authenticated_match = (last_order.user_id == user_id) if last_order and user_id else False

        if last_order:
            return LookupResult(
                is_recurring=True,
                is_trusted_device=is_trusted,
                name_masked=_mask_name(last_order.customer_name),
                address_masked=_mask_address(last_order.customer_address),
                name=last_order.customer_name if is_authenticated_match else None,
                address=last_order.customer_address if is_authenticated_match else None
            )

        user_res = await db_session.execute(select(User).where(User.username == phone).limit(1))
        user = user_res.scalar_one_or_none()
        if user:
            is_match = (user.id == user_id) if user_id else False
            return LookupResult(
                is_recurring=True,
                is_trusted_device=False,
                name_masked=_mask_name(user.name),
                address_masked=None,
                name=user.name if is_match else None,
                address=None
            )

        return LookupResult(
            is_recurring=False, 
            is_trusted_device=False, 
            name_masked=None, 
            address_masked=None,
            name=None,
            address=None
        )

    @staticmethod
    async def verify_identity(
        db_session: AsyncSession,
        phone: str,
        name: str
    ) -> VerifyResult:
        """Verify Phone + Name match to unlock Address (Identity Shield)."""
        res = await db_session.execute(
            select(Order)
            .where(Order.customer_phone == phone)
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        last_order = res.scalar_one_or_none()

        if not last_order:
            return VerifyResult(verified=False, address=None)

        stored_name = _normalize_name(last_order.customer_name or "")
        input_name = _normalize_name(name)

        if input_name == stored_name:
            return VerifyResult(verified=True, address=last_order.customer_address)

        return VerifyResult(verified=False, address=None)

    @staticmethod
    def get_mask_helpers():
        return _mask_name, _mask_address
