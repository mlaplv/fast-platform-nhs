import re
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update, delete
from sqlalchemy.orm import selectinload

from backend.database.models import Order, User, Draft, Notification, ProductBase
from backend.mcp.protocol import mcp_registry
from backend.schemas.intent import IntentAction
from backend.utils.data_stripper import DataStripper

logger = logging.getLogger("api-gateway")

@mcp_registry.register(
    name="get_revenue_stats",
    description="Thống kê doanh thu trong N ngày qua (Rule R5)"
)
async def get_revenue_stats(db_session: AsyncSession, days: int = 30):
    # ── HELLFIRE: Input validation ──
    if not isinstance(days, int) or days < 1 or days > 365:
        return {"status": "error", "message": "days must be integer between 1 and 365"}
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    stmt = select(Order).where(and_(Order.created_at >= start_date, Order.deleted_at == None))
    res = await db_session.execute(stmt)
    orders = res.scalars().all()
    
    total = sum(o.total_amount for o in orders) if orders else 0
    return {
        "total_revenue": float(total),
        "order_count": len(orders),
        "days": days
    }

@mcp_registry.register(
    name="create_database_draft",
    description="Tạo bản ghi nháp cho các thay đổi dữ liệu (Rule R11 - The Final Glance)"
)
async def create_database_draft(db_session: AsyncSession, target_model: str, target_id: str, payload: dict, proposed_by: str = "NanoBot"):
    # ── HELLFIRE: Input sanitization ──
    _SAFE_ID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
    _SAFE_MODEL = re.compile(r"^[A-Za-z]{1,30}$")
    if not _SAFE_MODEL.match(target_model):
        return {"status": "error", "message": f"Invalid target_model: must be alphabetic, got '{target_model}'"}
    if not _SAFE_ID.match(target_id):
        return {"status": "error", "message": f"Invalid target_id: must be alphanumeric/dash/underscore, got '{target_id}'"}
    if not _SAFE_ID.match(proposed_by):
        return {"status": "error", "message": "Invalid proposed_by"}

    if isinstance(payload, dict):
        payload["is_ai_generated"] = True

    import uuid
    draft_id = str(uuid.uuid4())
    
    draft = Draft(
        id=draft_id,
        proposed_by=proposed_by,
        target_model=target_model,
        target_id=target_id,
        action="UPDATE",
        payload=payload,
        status="PENDING"
    )
    db_session.add(draft)
    
    notification = Notification(
        id=str(uuid.uuid4()),
        type="WARNING",
        message=f"AI Sentinel: New Draft mutation proposed for {target_model} (ID: {target_id}). Approval required."
    )
    db_session.add(notification)
    
    await db_session.commit()

    return {"draft_id": draft_id, "status": "PENDING_APPROVAL"}

@mcp_registry.register(
    name="list_orders",
    description="Liệt kê danh sách đơn hàng gần đây"
)
async def list_orders(db_session: AsyncSession, limit: int = 10):
    stmt = select(Order).where(Order.deleted_at == None).order_by(Order.created_at.desc()).limit(limit)
    res = await db_session.execute(stmt)
    orders = res.scalars().all()
    
    data = [{"id": str(o.id), "amount": float(o.total_amount), "status": o.status} for o in orders]
    
    return DataStripper.strip(
        data,
        allowed_fields={"id", "amount", "status"}
    )

@mcp_registry.register(
    name="get_draft_analysis",
    description="Truy xuất thông tin chi tiết của một bản ghi Draft để phân tích rủi ro (Phase 3)"
)
async def get_draft_analysis(db_session: AsyncSession, draft_id: str):
    _SAFE_ID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
    if not _SAFE_ID.match(draft_id):
        return {"status": "error", "message": f"Invalid draft_id format: '{draft_id}'"}
    
    stmt = select(Draft).where(Draft.id == draft_id)
    res = await db_session.execute(stmt)
    draft = res.scalar_one_or_none()
    
    if not draft:
        return {"status": "error", "message": "Draft not found"}
    
    return {
        "id": str(draft.id),
        "proposedBy": draft.proposed_by,
        "targetModel": draft.target_model,
        "targetId": draft.target_id,
        "action": draft.action,
        "payload": draft.payload,
        "status": draft.status
    }

@mcp_registry.register(
    name="run_docker_compose",
    description="Thực hiện lệnh docker compose an toàn (ps, logs --tail 20). Rule: Chỉ dành cho sys:admin."
)
async def run_docker_compose(db_session: AsyncSession, command: str = "ps"):
    # This tool doesn't use the DB, but we accept the session for consistency
    import asyncio
    
    allowed_commands = ["ps", "logs --tail 20", "logs -f --tail 10", "version"]
    if command not in allowed_commands:
        return {"status": "error", "message": f"Command '{command}' is restricted for safety."}

    try:
        cmd_parts = ["docker", "compose"] + command.split()
        proc = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        except asyncio.TimeoutError:
            proc.kill()
            return {"status": "error", "message": "Command timed out after 10s."}
        
        return {
            "status": "success" if proc.returncode == 0 else "error",
            "stdout": stdout.decode()[-2000:], 
            "stderr": stderr.decode()[-500:],
            "exit_code": proc.returncode
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp_registry.register(
    name="decrement_stock",
    description="Doomsday T7: Atomic stock decrement. MUST use this instead of manual update."
)
async def decrement_stock(db_session: AsyncSession, product_id: str, quantity: int = 1):
    _SAFE_ID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
    if not _SAFE_ID.match(product_id):
        return {"status": "error", "message": "Invalid product_id"}
    if quantity < 1:
        return {"status": "error", "message": "Quantity must be >= 1"}

    try:
        # Atomic update with check to prevent negative stock
        stmt = update(ProductBase).where(
            and_(ProductBase.id == product_id, ProductBase.stock >= quantity)
        ).values(stock=ProductBase.stock - quantity).returning(ProductBase.stock, ProductBase.name)
        
        res = await db_session.execute(stmt)
        row = res.fetchone()
        
        if not row:
            return {"status": "error", "message": "Lỗi: Không đủ hàng trong kho hoặc sản phẩm không tồn tại."}
            
        await db_session.commit()
        return {"status": "success", "stock_remaining": row[0], "product": row[1]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp_registry.register(
    name="search_products_semantic",
    description="Tìm kiếm sản phẩm bằng ngữ nghĩa (RAG)"
)
async def search_products_semantic(db_session: AsyncSession, query: str, limit: int = 5):
    try:
        from backend.services.product_vector_service import product_vector_service
        # For now, we don't use db_session here directly as vector service has its own logic
        # But we could pass it if needed.
        results = await product_vector_service.search_semantic(query=query, limit=limit)
        return {"status": "success", "query": query, "results": results}
    except Exception as e:
        return {"status": "error", "message": f"Lỗi tìm kiếm semantic: {str(e)}"}

@mcp_registry.register(
    name="search_articles_semantic",
    description="Tìm kiếm bài viết, tin tức hoặc chính sách bằng ngữ nghĩa (RAG)."
)
async def search_articles_semantic(db_session: AsyncSession, query: str, limit: int = 5):
    try:
        from backend.services.article_vector_service import article_vector_service
        results = await article_vector_service.search_semantic(query=query, limit=limit)
        return {"status": "success", "query": query, "results": results}
    except Exception as e:
        return {"status": "error", "message": f"Lỗi tìm kiếm bài viết semantic: {str(e)}"}
