import logging
import os
import asyncio
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from typing import Union, Optional, Dict
from sqlalchemy import text, func

from backend.schemas.intent import IntentResponse
from backend.database import current_tenant_id

logger = logging.getLogger("api-gateway")

# --- Performance Hardening Constants (R1.6) ---
TIME_KEYWORDS = ["nay", "hôm nay", "ngày này", "chiều nay", "sáng nay", "tối nay"]
APP_TZ = ZoneInfo(os.getenv("APP_TIMEZONE", "Asia/Ho_Chi_Minh"))
DEFAULT_TENANT = os.getenv("DEFAULT_TENANT_ID", "default")

class DataInjector:
    """
    [CTO Mode] Trinity Loop: Data Provider.
    Single Responsibility: Fetch scalar metrics OR series data.
    Zero-Hydration: Scalar SQL only, no ORM object loading.
    """

    async def inject(self, intent: IntentResponse, user_query: str, db_session: AsyncSession, **kwargs) -> IntentResponse:
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
        if timeframe == "today" and not any(kw in user_query.lower() for kw in TIME_KEYWORDS):
            timeframe = "none"

        if target in ["order", "revenue", "product", "user"]:
            try:
                # 1. Fetch scalar count (Fast Path)
                count = await self._fetch_count(db_session, target, timeframe, status)

                intent.data["raw_count"] = count
                intent.data["injected_count"] = count
                intent.data["raw_timeframe"] = timeframe
                intent.data["raw_target"] = target

                # 2. RESTORE: Fetch ALL revenue series ONLY if explicitly opening the chart
                # This keeps voice counts fast but fills the chart with all tabs when needed.
                if target == "revenue" and ui_action == "show_revenue_chart":
                    logger.info(f"[Data Injector] Target={target}, Action={ui_action} -> Fetching Full Series (D/M/Q/Y)")
                    series = await self._fetch_revenue_series(db_session)
                    intent.data["series_data"] = series
                    logger.info(f"[Data Injector] Full series data fetched: {list(series.keys())}")
                else:
                    intent.data["series_data"] = None

            except Exception as e:
                logger.error(f"[Data Injector] DB Error: {e}", exc_info=True)
                intent.data["db_error"] = str(e)

        return intent

    async def _fetch_revenue_series(self, session: AsyncSession) -> Dict[str, dict]:
        """
        Streamlined series fetcher. Parallel SQL grouping.
        Supports both Postgres (date_trunc) and SQLite (strftime).
        """
        tenant_id = current_tenant_id.get() or DEFAULT_TENANT
        now = datetime.now(APP_TZ)

        async def fetch_grouped(trunc_unit: str, lookback_days: int, pg_label_fmt: str):
            res = {"labels": [], "revenue": [], "orders": []}
            start_date = now - timedelta(days=lookback_days)
            try:
                # 1. Postgres Attempt (date_trunc)
                sql = text(f"""
                    SELECT
                        date_trunc('{trunc_unit}', created_at) as period,
                        SUM(total_amount) as rev,
                        COUNT(id) as cnt
                    FROM orders
                    WHERE tenant_id = :tid
                      AND created_at >= :start
                      AND deleted_at IS NULL
                      AND is_spam IS FALSE
                    GROUP BY 1
                    ORDER BY 1
                """)
                rows = await session.execute(sql, {"tid": tenant_id, "start": start_date})
                for r in rows:
                    period = r[0]
                    rev = float(r[1] or 0)
                    cnt = int(r[2] or 0)
                    if trunc_unit == 'quarter':
                        label = f"Q{(period.month-1)//3+1}/{period.strftime('%y')}"
                    elif trunc_unit == 'year':
                        label = period.strftime('%Y')
                    else:
                        label = period.strftime(pg_label_fmt)
                    res["labels"].append(label)
                    res["revenue"].append(rev)
                    res["orders"].append(cnt)
            except Exception as pg_err:
                logger.debug(f"[Data Injector] Postgres grouping failed for {trunc_unit}, trying SQLite: {pg_err}")
                # 2. SQLite Fallback (strftime)
                try:
                    if trunc_unit == 'year':
                        group_expr = "strftime('%Y', created_at)"
                    elif trunc_unit == 'month':
                        group_expr = "strftime('%m/%y', created_at)"
                    elif trunc_unit == 'quarter':
                        group_expr = "(strftime('%Y', created_at) || '-Q' || ((CAST(strftime('%m', created_at) AS INTEGER) - 1) / 3 + 1))"
                    else: # 'day'
                        group_expr = "strftime('%d/%m', created_at)"

                    sql = text(f"""
                        SELECT
                            {group_expr} as period,
                            SUM(total_amount) as rev,
                            COUNT(id) as cnt
                        FROM orders
                        WHERE tenant_id = :tid
                          AND created_at >= :start
                          AND deleted_at IS NULL
                          AND is_spam IS FALSE
                        GROUP BY period
                        ORDER BY period
                    """)
                    rows = await session.execute(sql, {"tid": tenant_id, "start": start_date})
                    for r in rows:
                        res["labels"].append(str(r[0]))
                        res["revenue"].append(float(r[1] or 0))
                        res["orders"].append(int(r[2] or 0))
                except Exception as sql_err:
                    logger.error(f"[Data Injector] SQLite grouping failed for {trunc_unit}: {sql_err}")
            return res

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

    async def _fetch_count(self, session: AsyncSession, target: str, timeframe: str = "none", status: str = "none") -> Union[int, float, None]:
        now = datetime.now(APP_TZ)

        time_filter = None
        if timeframe == "today":     time_filter = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "this_week": time_filter = now - timedelta(days=7)
        elif timeframe == "this_month": time_filter = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        params = {}
        if time_filter:
            params["t_filter"] = time_filter

        if target == "order":
            where_clauses = ["deleted_at IS NULL", "is_spam IS FALSE"]
            if time_filter: where_clauses.append("created_at >= :t_filter")
            if status and status != "none":
                where_clauses.append("status = :status")
                params["status"] = status.upper()

            sql = text(f"SELECT COUNT(*) FROM orders WHERE {' AND '.join(where_clauses)}")
            return await session.scalar(sql, params) or 0

        if target == "product":
            where_clauses = ["deleted_at IS NULL"]
            if time_filter: where_clauses.append("created_at >= :t_filter")
            sql = text(f"SELECT COUNT(*) FROM product_bases WHERE {' AND '.join(where_clauses)}")
            return await session.scalar(sql, params) or 0

        if target == "user":
            where_clauses = ["deleted_at IS NULL"]
            if time_filter: where_clauses.append("created_at >= :t_filter")
            sql = text(f"SELECT COUNT(*) FROM users WHERE {' AND '.join(where_clauses)}")
            return await session.scalar(sql, params) or 0

        if target == "revenue":
            tenant_id = current_tenant_id.get() or DEFAULT_TENANT
            params["tid"] = tenant_id
            where_clauses = ["tenant_id = :tid", "deleted_at IS NULL", "is_spam IS FALSE"]
            if status and status != "none":
                where_clauses.append("status = :status")
                params["status"] = status.upper()
            if time_filter: where_clauses.append("created_at >= :t_filter")

            sql = text(f"SELECT SUM(total_amount) FROM orders WHERE {' AND '.join(where_clauses)}")
            return await session.scalar(sql, params) or 0
        return None



data_injector = DataInjector()
