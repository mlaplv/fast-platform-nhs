import re
import logging
import uuid
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Union, cast

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update, delete
from sqlalchemy.orm import selectinload

from backend.database.models import Order, User, Draft, ProductBase
from backend.mcp.protocol import mcp_registry
from backend.schemas.intent import IntentAction
from backend.schemas.signal import SignalSchema, SignalSeverity
from backend.services.signal_center import signal_center
from backend.utils.data_stripper import DataStripper
from backend.services.commerce.product_vector import ProductVectorService
from backend.services.article_vector_service import ArticleVectorService

logger = logging.getLogger("api-gateway")

@mcp_registry.register(
    name="get_revenue_stats",
    description="Thống kê doanh thu trong N ngày qua (Rule R5)"
)
async def get_revenue_stats(db_session: AsyncSession, days: int = 30) -> Dict[str, Union[str, float, int]]:
    # ── HELLFIRE: Input validation ──
    if not isinstance(days, int) or days < 1 or days > 365:
        return {"status": "error", "message": "days must be integer between 1 and 365"}
    
    start_date: datetime = datetime.now(timezone.utc) - timedelta(days=days)
    
    stmt = select(Order).where(and_(Order.created_at >= start_date, Order.deleted_at == None))
    res = await db_session.execute(stmt)
    orders: List[Order] = list(res.scalars().all())
    
    total: float = float(sum(o.total_amount for o in orders)) if orders else 0.0
    return {
        "total_revenue": total,
        "order_count": len(orders),
        "days": days,
        "status": "success"
    }

@mcp_registry.register(
    name="create_database_draft",
    description="Tạo bản ghi nháp cho các thay đổi dữ liệu (Rule R11 - The Final Glance)"
)
async def create_database_draft(
    db_session: AsyncSession, 
    target_model: str, 
    target_id: str, 
    payload: Dict[str, object], 
    proposed_by: str = "NanoBot"
) -> Dict[str, str]:
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

    draft_id: str = str(uuid.uuid4())
    
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
    
    # CNS V70: ACTION severity — triggers Patient Voice + Bell sync
    await signal_center.dispatch(
        user_id=proposed_by,
        signal=SignalSchema(
            message=f"AI Sentinel: New Draft mutation proposed for {target_model} (ID: {target_id}). Approval required.",
            severity=SignalSeverity.ACTION,
            signal_type="WARNING"
        ),
        db_session=db_session
    )
    
    await db_session.commit()

    return {"draft_id": draft_id, "status": "PENDING_APPROVAL"}

@mcp_registry.register(
    name="list_orders",
    description="Liệt kê danh sách đơn hàng gần đây"
)
async def list_orders(db_session: AsyncSession, limit: int = 10) -> List[Dict[str, object]]:
    stmt = select(Order).where(Order.deleted_at == None).order_by(Order.created_at.desc()).limit(limit)
    res = await db_session.execute(stmt)
    orders: List[Order] = list(res.scalars().all())
    
    data: List[Dict[str, object]] = [{"id": str(o.id), "amount": float(o.total_amount), "status": str(o.status)} for o in orders]
    
    return cast(List[Dict[str, object]], DataStripper.strip(
        data,
        allowed_fields={"id", "amount", "status"}
    ))

@mcp_registry.register(
    name="get_draft_analysis",
    description="Truy xuất thông tin chi tiết của một bản ghi Draft để phân tích rủi ro (Phase 3)"
)
async def get_draft_analysis(db_session: AsyncSession, draft_id: str) -> Dict[str, object]:
    _SAFE_ID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
    if not _SAFE_ID.match(draft_id):
        return {"status": "error", "message": f"Invalid draft_id format: '{draft_id}'"}
    
    stmt = select(Draft).where(Draft.id == draft_id)
    res = await db_session.execute(stmt)
    draft: Optional[Draft] = res.scalar_one_or_none()
    
    if not draft:
        return {"status": "error", "message": "Draft not found"}
    
    return {
        "id": str(draft.id),
        "proposedBy": str(draft.proposed_by),
        "targetModel": str(draft.target_model),
        "targetId": str(draft.target_id),
        "action": str(draft.action),
        "payload": draft.payload,
        "status": str(draft.status)
    }

@mcp_registry.register(
    name="run_docker_compose",
    description="Thực hiện lệnh docker compose an toàn (ps, logs --tail 20). Rule: Chỉ dành cho sys:admin."
)
async def run_docker_compose(db_session: AsyncSession, command: str = "ps") -> Dict[str, Union[str, int]]:
    # This tool doesn't use the DB, but we accept the session for consistency
    allowed_commands: List[str] = ["ps", "logs --tail 20", "logs -f --tail 10", "version"]
    if command not in allowed_commands:
        return {"status": "error", "message": f"Command '{command}' is restricted for safety."}

    try:
        cmd_parts: List[str] = ["docker", "compose"] + command.split()
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
            "exit_code": proc.returncode or 0
        }
    except Exception as e:
        logger.error(f"[MCP] Docker Compose Error: {e}")
        return {"status": "error", "message": str(e)}

@mcp_registry.register(
    name="decrement_stock",
    description="Doomsday T7: Atomic stock decrement. MUST use this instead of manual update."
)
async def decrement_stock(db_session: AsyncSession, product_id: str, quantity: int = 1) -> Dict[str, Union[str, int]]:
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
        return {"status": "success", "stock_remaining": int(row[0]), "product": str(row[1])}
    except Exception as e:
        logger.error(f"[MCP] Decrement Stock Error: {e}")
        return {"status": "error", "message": str(e)}

@mcp_registry.register(
    name="search_products_semantic",
    description="Tìm kiếm sản phẩm bằng ngữ nghĩa (RAG)"
)
async def search_products_semantic(db_session: AsyncSession, query: str, limit: int = 5) -> Dict[str, object]:
    try:
        vector_service = ProductVectorService()
        results = await vector_service.search_semantic(db_session=db_session, query=query, limit=limit)
        return {"status": "success", "query": query, "results": results}
    except Exception as e:
        logger.error(f"[MCP] Product Search Error: {e}")
        return {"status": "error", "message": f"Lỗi tìm kiếm sản phẩm: {str(e)}"}

@mcp_registry.register(
    name="search_articles_semantic",
    description="Tìm kiếm Bài viết hoặc chính sách bằng ngữ nghĩa (RAG)."
)
async def search_articles_semantic(db_session: AsyncSession, query: str, limit: int = 5) -> Dict[str, object]:
    try:
        vector_service = ArticleVectorService()
        results = await vector_service.search_semantic(db_session=db_session, query=query, limit=limit)
        return {"status": "success", "query": query, "results": results}
    except Exception as e:
        logger.error(f"[MCP] Article Search Error: {e}")
        return {"status": "error", "message": f"Lỗi tìm kiếm bài viết: {str(e)}"}
