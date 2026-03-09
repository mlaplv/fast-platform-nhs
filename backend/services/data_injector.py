import logging
import os
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from typing import Union, Optional, Dict
from backend.schemas.intent import IntentResponse

logger = logging.getLogger("api-gateway")

class DataInjector:
    """
    [CTO Mode] Trinity Loop: Data Provider.
    Single Responsibility: Fetch scalar metrics OR series data.
    Zero-Hydration: Scalar SQL only, no ORM object loading.
    """

    async def inject(self, intent: IntentResponse, user_query: str, **kwargs) -> IntentResponse:
        """
        Inject a single data point into intent.data.
        One query. One number. Fast.
        """
        if intent.status != "success":
            return intent

        data_dict = intent.data or {}
        target = data_dict.get("target")
        timeframe = data_dict.get("timeframe", "none")
        status = data_dict.get("status", "none")
        ui_action = data_dict.get("ui_action", "")

        # Robust Timeframe Correction
        time_keywords = ["nay", "hôm nay", "ngày này", "chiều nay", "sáng nay", "tối nay"]
        if timeframe == "today" and not any(kw in user_query.lower() for kw in time_keywords):
            timeframe = "none"

        if target in ["order", "revenue", "product", "user"]:
            try:
                # 1. Fetch scalar count (Fast Path)
                count = await self._fetch_count(target, timeframe, status, **kwargs)
                
                intent.data["raw_count"] = count
                intent.data["injected_count"] = count
                intent.data["raw_timeframe"] = timeframe
                intent.data["raw_target"] = target
                
                # 2. RESTORE: Fetch ALL revenue series ONLY if explicitly opening the chart
                # This keeps voice counts fast but fills the chart with all tabs when needed.
                if target == "revenue" and ui_action == "show_revenue_chart":
                    logger.info(f"[Data Injector] Target={target}, Action={ui_action} -> Fetching Full Series (D/M/Q/Y)")
                    series = await self._fetch_revenue_series(**kwargs)
                    intent.data["series_data"] = series
                    logger.info(f"[Data Injector] Full series data fetched: {list(series.keys())}")
                else:
                    intent.data["series_data"] = None

            except Exception as e:
                logger.error(f"[Data Injector] DB Error: {e}", exc_info=True)
                intent.data["db_error"] = str(e)

        return intent

    async def _fetch_revenue_series(self, **repos) -> Dict[str, dict]:
        """
        Streamlined series fetcher. Parallel SQL grouping.
        Supports both Postgres (date_trunc) and SQLite (strftime).
        """
        from sqlalchemy import select, func, text
        from backend.database.models import Order
        from backend.database import current_tenant_id
        
        repo = repos.get("order_repo")
        if not repo: return {"daily": {"labels": [], "revenue": [], "orders": []}}

        tenant_id = current_tenant_id.get() or os.getenv("DEFAULT_TENANT_ID", "default")
        now = datetime.now(ZoneInfo(os.getenv("APP_TIMEZONE", "Asia/Ho_Chi_Minh")))
        
        async def fetch_grouped(trunc_unit: str, lookback_days: int, pg_label_fmt: str):
            res = {"labels": [], "revenue": [], "orders": []}
            try:
                # 1. Postgres Attempt (date_trunc)
                stmt = (
                    select(
                        func.date_trunc(trunc_unit, Order.created_at).label("period"),
                        func.sum(Order.total_amount).label("rev"),
                        func.count(Order.id).label("cnt")
                    )
                    .where(
                        Order.tenant_id == tenant_id,
                        Order.created_at >= (now - timedelta(days=lookback_days)),
                        Order.deleted_at.is_(None),
                        Order.is_spam.is_(False)
                    )
                    .group_by(text("1")).order_by(text("1"))
                )
                rows = await repo.session.execute(stmt)
                for r in rows:
                    if trunc_unit == 'quarter':
                        label = f"Q{(r.period.month-1)//3+1}/{r.period.strftime('%y')}"
                    elif trunc_unit == 'year':
                        label = r.period.strftime('%Y')
                    else:
                        label = r.period.strftime(pg_label_fmt)
                    res["labels"].append(label)
                    res["revenue"].append(float(r.rev or 0))
                    res["orders"].append(int(r.cnt or 0))
            except Exception as pg_err:
                logger.debug(f"[Data Injector] Postgres grouping failed for {trunc_unit}, trying SQLite: {pg_err}")
                # 2. SQLite Fallback (strftime)
                try:
                    if trunc_unit == 'year':
                        group_expr = func.strftime('%Y', Order.created_at)
                    elif trunc_unit == 'month':
                        group_expr = func.strftime('%m/%y', Order.created_at)
                    elif trunc_unit == 'quarter':
                        # SQLite quarter logic: Q + ((month-1)/3 + 1)
                        group_expr = text("(strftime('%Y', created_at) || '-Q' || ((CAST(strftime('%m', created_at) AS INTEGER) - 1) / 3 + 1))")
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
                            Order.deleted_at.is_(None),
                            Order.is_spam.is_(False)
                        )
                        .group_by(text("period")).order_by(text("period"))
                    )
                    rows = await repo.session.execute(stmt)
                    for r in rows:
                        res["labels"].append(str(r.period))
                        res["revenue"].append(float(r.rev or 0))
                        res["orders"].append(int(r.cnt or 0))
                except Exception as sql_err:
                    logger.error(f"[Data Injector] SQLite grouping failed for {trunc_unit}: {sql_err}")
            return res

        import asyncio
        daily, monthly, quarterly, yearly = await asyncio.gather(
            fetch_grouped('day', 30, '%d/%m'),
            fetch_grouped('month', 365, '%m/%y'),
            fetch_grouped('quarter', 365 * 2, None),
            fetch_grouped('year', 365 * 5, '%Y')
        )
        return {
            "daily": daily, 
            "monthly": monthly,
            "quarterly": quarterly,
            "yearly": yearly
        }

    async def _fetch_count(self, target: str, timeframe: str = "none", status: str = "none", **repos) -> Union[int, float, None]:
        from sqlalchemy import select, func
        from backend.database.models import Order, ProductBase, User
        now = datetime.now(ZoneInfo(os.getenv("APP_TIMEZONE", "Asia/Ho_Chi_Minh")))
        
        time_filter = None
        if timeframe == "today":     time_filter = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "this_week": time_filter = now - timedelta(days=7)
        elif timeframe == "this_month": time_filter = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if target == "order":
            repo = repos.get("order_repo")
            if not repo: return None
            stmt = select(func.count(Order.id)).where(Order.deleted_at.is_(None), Order.is_spam.is_(False))
            if time_filter: stmt = stmt.where(Order.created_at >= time_filter)
            if status and status != "none": stmt = stmt.where(Order.status == status.upper())
            return await repo.session.scalar(stmt) or 0

        if target == "product":
            repo = repos.get("product_repo")
            if not repo: return None
            stmt = select(func.count(ProductBase.id)).where(ProductBase.deleted_at.is_(None))
            if time_filter: stmt = stmt.where(ProductBase.created_at >= time_filter)
            return await repo.session.scalar(stmt) or 0

        if target == "user":
            repo = repos.get("user_repo")
            if not repo: return None
            stmt = select(func.count(User.id)).where(User.deleted_at.is_(None))
            if time_filter: stmt = stmt.where(User.created_at >= time_filter)
            return await repo.session.scalar(stmt) or 0

        if target == "revenue":
            repo = repos.get("order_repo")
            if not repo: return None
            from backend.database import current_tenant_id
            tenant_id = current_tenant_id.get() or os.getenv("DEFAULT_TENANT_ID", "default")
            stmt = select(func.sum(Order.total_amount)).where(Order.tenant_id == tenant_id, Order.deleted_at.is_(None), Order.is_spam.is_(False))
            if status and status != "none": stmt = stmt.where(Order.status == status.upper())
            if time_filter: stmt = stmt.where(Order.created_at >= time_filter)
            return await repo.session.scalar(stmt) or 0
        return None

data_injector = DataInjector()
