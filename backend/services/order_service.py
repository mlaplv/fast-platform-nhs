import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Union, cast
from sqlalchemy import text, select, func, or_, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.event_bus import event_bus
from backend.utils.sql import escape_like

logger = logging.getLogger("api-gateway")

class OrderService:
    """
    ULTRA-LEAN ORDER SERVICE (ELITE V2.2)
    -------------------------------------
    Handles Order CRUD, State Machine transitions, and Anti-Spam triggers.
    Zero-Hydration (Rule 1.5) enforced.
    """

    async def list_orders(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, object]:
        """List orders with total count and customer projection (R76)."""
        conditions = ["o.deleted_at IS NULL"]
        params = {"limit": limit, "offset": offset}

        if status and status != "all":
            conditions.append("o.status = :status")
            params["status"] = status.upper()

        if search:
            safe = escape_like(search)
            conditions.append("(o.id ILIKE :search OR u.name ILIKE :search)")
            params["search"] = f"%{safe}%"

        where_clause = " AND ".join(conditions)

        # 1. COUNT (Zero-Hydration)
        count_sql = text(f"SELECT COUNT(*) FROM orders o LEFT JOIN users u ON o.user_id = u.id WHERE {where_clause}")
        total = await session.scalar(count_sql, params) or 0

        # 2. Scalar Projection Fetch
        sql = text(f"""
            SELECT o.id, o.status, o.total_amount, o.items, o.created_at,
                   o.is_spam, o.spam_score, o.spam_reason, o.fingerprint,
                   u.name as customer_name
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            WHERE {where_clause}
            ORDER BY o.created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await session.execute(sql, params)
        rows = result.all()

        data = [
            {
                "id": str(r[0]),
                "status": r[1].lower() if r[1] else "pending",
                "total": float(r[2]) if r[2] else 0.0,
                "items": len(r[3]) if isinstance(r[3], list) else 0,
                "createdAt": r[4].isoformat() if r[4] else "",
                "isSpam": r[5],
                "spamScore": r[6],
                "spamReason": r[7],
                "fingerprint": r[8],
                "customerName": r[9] or "Storefront Customer",
            }
            for r in rows
        ]

        return {"data": data, "total": total}

    async def get_order(self, session: AsyncSession, order_id: str) -> Dict[str, object]:
        """Get a single order with user details via Scalar Projection (R76)."""
        sql = text("""
            SELECT o.id, o.status, o.total_amount, o.items, o.created_at,
                   o.cancellation_reason, o.is_spam, o.spam_score, o.spam_reason,
                   o.fingerprint, o.history, u.name as customer_name
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            WHERE o.id = :id AND o.deleted_at IS NULL
        """)
        result = await session.execute(sql, {"id": order_id})
        r = result.first()

        if not r:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Order {order_id} not found")

        return {
            "id": str(r[0]),
            "status": r[1].lower() if r[1] else "pending",
            "total": float(r[2]) if r[2] else 0.0,
            "items": r[3],
            "createdAt": r[4].isoformat() if r[4] else "",
            "cancellationReason": r[5],
            "isSpam": r[6],
            "spamScore": r[7],
            "spamReason": r[8],
            "fingerprint": r[9],
            "history": r[10] or [],
            "customerName": r[11] or "Unknown",
        }

    async def create_order(
        self,
        session: AsyncSession,
        data: Dict[str, object],
        ip: str = "unknown",
        ua: str = "unknown"
    ) -> Dict[str, object]:
        """Create order via Scalar Insert (Zero-Hydration) and emit event."""
        new_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        history = [{
            "status": "PENDING",
            "timestamp": now.isoformat(),
            "actor": "Storefront",
            "note": "Order created via checkout"
        }]

        # Rule R1.5: Zero-Hydration Scalar Insert
        await session.execute(
            text("""
                INSERT INTO orders (id, items, total_amount, status, history, created_at, updated_at, tenant_id)
                VALUES (:id, :items, :total, 'PENDING', :history, :now, :now, 'default')
            """),
            {
                "id": new_id,
                "items": json.dumps(data.get("items", [])),
                "total": data.get("total_amount", 0.0),
                "history": json.dumps(history),
                "now": now
            }
        )
        await session.commit()

        # Emit event for XoHiResponder/AntiSpam
        await event_bus.emit("ORDER_CREATED", {
            "id": new_id,
            "ip": ip,
            "user_agent": ua,
            "customer": data.get("customer_name"),
            "phone": data.get("customer_phone"),
            "address": data.get("customer_address"),
            "total_amount": data.get("total_amount"),
        })

        return {"id": new_id, "status": "pending", "success": True}

    async def update_status(
        self,
        session: AsyncSession,
        order_id: str,
        new_status: str,
        actor: str = "System"
    ) -> Dict[str, object]:
        """Handle state machine transitions and history via Raw SQL (Rule 1.5)."""
        # 1. Fetch current state
        sql = text("SELECT status, history, user_id FROM orders WHERE id = :id AND deleted_at IS NULL")
        res = await session.execute(sql, {"id": order_id})
        current = res.first()
        if not current:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Order {order_id} not found")

        current_status = current[0].upper()
        history = list(current[1] or [])
        user_id = current[2]
        new_status = new_status.upper()

        # State Machine R60
        VALID_TRANSITIONS = {
            "PENDING": ["PAID", "CANCELLED"],
            "PAID": ["PROCESSING", "CANCELLED"],
            "PROCESSING": ["SHIPPED"],
            "SHIPPED": ["DELIVERED"],
            "DELIVERED": ["COMPLETED"],
            "COMPLETED": [],
            "CANCELLED": []
        }

        if new_status not in VALID_TRANSITIONS.get(current_status, []):
            from litestar.exceptions import ValidationException
            raise ValidationException(f"Invalid transition from {current_status} to {new_status}")

        history.append({
            "status": new_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "note": "Status updated via admin"
        })

        # 2. Atomic Update
        await session.execute(
            text("UPDATE orders SET status = :status, history = :history, updated_at = NOW() WHERE id = :id"),
            {
                "status": new_status,
                "history": json.dumps(history),
                "id": order_id
            }
        )
        await session.commit()

        await event_bus.emit("ORDER_UPDATED", {
            "id": order_id,
            "status": new_status,
            "tenant_id": user_id
        })

        return {"success": True, "new_status": new_status.lower()}

    async def cancel_order(
        self,
        session: AsyncSession,
        order_id: str,
        reason: str,
        actor: str = "System"
    ) -> Dict[str, object]:
        """Cancel order with reason via Raw SQL."""
        sql = text("SELECT status, history, user_id FROM orders WHERE id = :id AND deleted_at IS NULL")
        res = await session.execute(sql, {"id": order_id})
        current = res.first()
        if not current:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Order {order_id} not found")

        current_status = current[0].upper()
        history = list(current[1] or [])
        user_id = current[2]

        if current_status not in ["PENDING", "PAID"]:
            from litestar.exceptions import ValidationException
            raise ValidationException("Only PENDING or PAID orders can be cancelled")

        history.append({
            "status": "CANCELLED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "note": f"Reason: {reason}"
        })

        await session.execute(
            text("""
                UPDATE orders
                SET status = 'CANCELLED', cancellation_reason = :reason, history = :history, updated_at = NOW()
                WHERE id = :id
            """),
            {
                "reason": reason,
                "history": json.dumps(history),
                "id": order_id
            }
        )
        await session.commit()

        await event_bus.emit("ORDER_CANCELLED", {
            "id": order_id,
            "reason": reason,
            "tenant_id": user_id
        })

        return {"success": True, "new_status": "cancelled"}

    async def toggle_spam(self, session: AsyncSession, order_id: str, actor: str = "System") -> Dict[str, object]:
        """Manual spam toggle override via Raw SQL."""
        sql = text("SELECT is_spam, status, history FROM orders WHERE id = :id AND deleted_at IS NULL")
        res = await session.execute(sql, {"id": order_id})
        current = res.first()
        if not current:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Order {order_id} not found")

        is_spam = current[0]
        status = current[1]
        history = list(current[2] or [])

        new_state = not is_spam
        spam_score = 100.0 if new_state else 0.0
        spam_reason = "Manual Blacklist (Admin)" if new_state else "Manual Whitelist (Admin)"

        history.append({
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "note": f"Manual Spam Override: {'SPAM_MARKED' if new_state else 'SPAM_REMOVED'}"
        })

        await session.execute(
            text("""
                UPDATE orders
                SET is_spam = :is_spam, spam_score = :score, spam_reason = :reason, history = :history, updated_at = NOW()
                WHERE id = :id
            """),
            {
                "is_spam": new_state,
                "score": spam_score,
                "reason": spam_reason,
                "history": json.dumps(history),
                "id": order_id
            }
        )
        await session.commit()

        return {
            "success": True,
            "isSpam": new_state,
            "spamScore": spam_score,
            "spamReason": spam_reason
        }

# Global Instance
order_service = OrderService()
