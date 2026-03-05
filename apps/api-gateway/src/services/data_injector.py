import logging
import os
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from typing import Union, Optional, Dict
from shared.schemas.intent import IntentResponse

logger = logging.getLogger("api-gateway")

class DataInjector:
    """
    [CTO Mode] Trinity Loop: Data Provider.
    Tasks: 
    1. Fetch raw database metrics (counts, revenue).
    2. Populate intent.data with raw values for the Refiner.
    3. Ensure data accuracy by fixing timeframe edge cases.
    """

    async def inject(self, intent: IntentResponse, user_query: str, **kwargs) -> IntentResponse:
        """
        Entry point for data injection.
        [THIẾT QUÂN LUẬT] Uses injected repositories from kwargs (Litestar DI).
        """
        if intent.status != "success":
            return intent

        data_dict = intent.data or {}
        target = data_dict.get("target")
        timeframe = data_dict.get("timeframe", "none")
        status = data_dict.get("status", "none")

        # Robust Timeframe Correction: Only default to 'today' if explicitly asked
        time_keywords = ["nay", "hôm nay", "ngày này", "chiều nay", "sáng nay", "tối nay"]
        if timeframe == "today" and not any(kw in user_query.lower() for kw in time_keywords):
            logger.debug(f"[Data Injector] Downgrading 'today' -> 'none' (Query: {user_query})")
            timeframe = "none"

        if target in ["order", "revenue", "product", "user"]:
            try:
                # Injection: Grounding Data using injected repositories
                count = await self._fetch_count(target, timeframe, status, **kwargs)
                
                intent.data["raw_count"] = count
                intent.data["raw_timeframe"] = timeframe
                intent.data["raw_status"] = status
                intent.data["raw_target"] = target
                
                # [V59.0] Advanced Charting: Always inject series data for revenue queries
                if target == "revenue":
                    # Extract numeric value for legacy charting
                    raw_val = str(count).replace("đ", "").replace(".", "").replace(",", "")
                    try:
                        intent.data["revenue"] = float(raw_val)
                    except ValueError:
                        intent.data["revenue"] = 0.0
                    
                    series_data = await self._fetch_revenue_series(**kwargs)
                    intent.data["series_data"] = series_data

                    period_map = {
                        "today": "hôm nay",
                        "this_week": "tuần này",
                        "this_month": "tháng này",
                        "none": "Hệ thống"
                    }
                    intent.data["period_label"] = period_map.get(timeframe, "Toàn thời gian")

            except Exception as e:
                logger.error(f"[Data Injector] DB Error: {e}", exc_info=True)
                intent.data["db_error"] = str(e)

        return intent

    async def _fetch_revenue_series(self, **repos) -> Dict[str, dict]:
        """
        [V59.3] Fetches multi-level revenue and order count series with tenant isolation.
        - daily: last 30 days
        - monthly: last 12 months
        - quarterly: last 8 quarters
        - yearly: last 5 years
        """
        from sqlalchemy import select, func, cast, Date, text
        from src.database.models import Order
        from src.database import current_tenant_id
        from datetime import datetime, timedelta
        
        repo = repos.get("order_repo")
        if not repo: return {"daily": {"labels": [], "revenue": [], "orders": []}}

        # ═══ TENANT ISOLATION (V59.3) ═══
        tenant_id = current_tenant_id.get() or os.getenv("DEFAULT_TENANT_ID", "default")
        
        now = datetime.now(ZoneInfo(os.getenv("APP_TIMEZONE", "Asia/Ho_Chi_Minh")))
        
        async def fetch_grouped(trunc_unit: str, lookback_days: int, sqlite_fmt: str, label_fmt: str):
            res = {"labels": [], "revenue": [], "orders": []}
            try:
                # 1. Try Postgres date_trunc
                stmt = (
                    select(
                        func.date_trunc(trunc_unit, Order.created_at).label("period"),
                        func.sum(Order.total_amount).label("rev"),
                        func.count(Order.id).label("cnt")
                    )
                    .where(
                        Order.tenant_id == tenant_id,
                        Order.created_at >= (now - timedelta(days=lookback_days)),
                        Order.deleted_at.is_(None)
                    )
                    .group_by(text("1"))
                    .order_by(text("1"))
                )
                rows = await repo.session.execute(stmt)
                for r in rows:
                    if trunc_unit == 'quarter':
                        q = (r.period.month - 1) // 3 + 1
                        res["labels"].append(f"Q{q}/{r.period.strftime('%y')}")
                    else:
                        res["labels"].append(r.period.strftime(label_fmt))
                    res["revenue"].append(float(r.rev or 0))
                    res["orders"].append(int(r.cnt or 0))
            except Exception as e:
                logger.debug(f"[Data Injector] PG grouping failed for {trunc_unit}, trying SQLite logic: {e}")
                
                # 2. Try SQLite strftime Fallback logic
                if trunc_unit == 'quarter':
                    group_expr = text("(strftime('%Y', created_at) || '-Q' || ((CAST(strftime('%m', created_at) AS INTEGER) - 1) / 3 + 1))")
                elif trunc_unit == 'year':
                    group_expr = func.strftime('%Y', Order.created_at)
                elif trunc_unit == 'month':
                    group_expr = func.strftime('%m/%y', Order.created_at)
                else: # 'day'
                    group_expr = func.strftime('%d/%m', Order.created_at)
                
                stmt = (
                    select(
                        group_expr.label("period"),
                        func.sum(Order.total_amount).label("rev"),
                        func.count(Order.id).label("cnt")
                    )
                    .where(
                        Order.tenant_id == tenant_id,
                        Order.created_at >= (now - timedelta(days=lookback_days)),
                        Order.deleted_at.is_(None)
                    )
                    .group_by(text("period"))
                    .order_by(text("period"))
                )
                rows = await repo.session.execute(stmt)
                for r in rows:
                    res["labels"].append(str(r.period))
                    res["revenue"].append(float(r.rev or 0))
                    res["orders"].append(int(r.cnt or 0))
            return res

        return {
            "daily": await fetch_grouped('day', 30, '%d/%m', '%d/%m'),
            "monthly": await fetch_grouped('month', 365, '%m/%y', '%m/%y'),
            "quarterly": await fetch_grouped('quarter', 365 * 2, None, None), 
            "yearly": await fetch_grouped('year', 365 * 5, '%Y', '%Y')
        }

    async def _fetch_count(self, target: str, timeframe: str = "none", status: str = "none", **repos) -> Union[str, int, float, None]:
        """
        [R1.5 Zero-Hydration] Fetches aggregates using scalar queries only.
        CẤM load ORM objects vào RAM cho COUNT/SUM.
        """
        from sqlalchemy import select, func
        from src.database.models import Order, ProductBase, User
        
        now = datetime.now(ZoneInfo(os.getenv("APP_TIMEZONE", "Asia/Ho_Chi_Minh")))
        
        # Build timeframe filter
        time_filter = None
        if timeframe == "today":
            time_filter = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "this_week":
            time_filter = now - timedelta(days=7)
        elif timeframe == "this_month":
            time_filter = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Zero-Hydration: Scalar queries only — no ORM object loading
        if target == "order":
            repo = repos.get("order_repo")
            if not repo: return None
            stmt = select(func.count(Order.id)).where(Order.deleted_at.is_(None))
            if time_filter: stmt = stmt.where(Order.created_at >= time_filter)
            if status and status != "none": stmt = stmt.where(Order.status == status.upper())
            return await repo.session.scalar(stmt)

        if target == "product":
            repo = repos.get("product_repo")
            if not repo: return None
            stmt = select(func.count(ProductBase.id)).where(ProductBase.deleted_at.is_(None))
            if time_filter: stmt = stmt.where(ProductBase.created_at >= time_filter)
            return await repo.session.scalar(stmt)

        if target == "user":
            repo = repos.get("user_repo")
            if not repo: return None
            stmt = select(func.count(User.id)).where(User.deleted_at.is_(None))
            if time_filter: stmt = stmt.where(User.created_at >= time_filter)
            return await repo.session.scalar(stmt)

        if target == "revenue":
            repo = repos.get("order_repo")
            if not repo: return None
            from src.database import current_tenant_id
            tenant_id = current_tenant_id.get() or os.getenv("DEFAULT_TENANT_ID", "default")
            
            stmt = select(func.sum(Order.total_amount)).where(
                Order.tenant_id == tenant_id,
                Order.deleted_at.is_(None)
            )
            if status and status != "none": stmt = stmt.where(Order.status == status.upper())
            if time_filter: stmt = stmt.where(Order.created_at >= time_filter)
            
            total = await repo.session.scalar(stmt) or 0
            return f"{total:,.0f}đ".replace(",", ".")

        return None

data_injector = DataInjector()

