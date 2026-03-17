import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Union

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.utils.text import sanitize_id, normalize_vn

logger = logging.getLogger("api-gateway")

class CampaignService:
    """
    ULTRA-LEAN CAMPAIGN SERVICE (ELITE V2.2)
    ----------------------------------------
    Centralizes all ContentCampaign & CampaignEvent logic.
    Uses Zero-Hydration (Raw SQL) to keep RAM < 2GB.
    """

    async def get_campaign(self, session: AsyncSession, campaign_id: str) -> Optional[Dict[str, object]]:
        """Fetch a single campaign via Scalar Projection."""
        sql = text("""
            SELECT id, user_id, source_input, reviewer_type, current_step, status,
                   category, gold_metadata, topic_data, assets_data, outline_data,
                   draft_content, final_html, search_count, unique_score, tenant_id,
                   created_at, updated_at
            FROM content_campaigns
            WHERE id = :id AND deleted_at IS NULL
        """)
        result = await session.execute(sql, {"id": campaign_id})
        r = result.first()
        if not r:
            return None

        return {
            "id": r[0],
            "user_id": r[1],
            "source_input": r[2],
            "reviewer_type": r[3],
            "current_step": r[4],
            "status": r[5],
            "category": r[6],
            "gold_metadata": r[7] or {},
            "topic_data": r[8] or {},
            "assets_data": r[9] or [],
            "outline_data": r[10] or {},
            "draft_content": r[11] or "",
            "final_html": r[12] or "",
            "search_count": r[13],
            "unique_score": float(r[14]) if r[14] is not None else 1.0,
            "tenant_id": r[15],
            "created_at": r[16],
            "updated_at": r[17]
        }

    async def get_active_campaign(
        self,
        session: AsyncSession,
        user_id: Optional[str] = None,
        tenant_id: str = "default",
        query: Optional[str] = None,
        campaign_id: Optional[str] = None
    ) -> Optional[Dict[str, object]]:
        """Surgical lookup for active campaigns without ORM hydration."""
        user_id = sanitize_id(user_id)
        campaign_id = sanitize_id(campaign_id)

        # 1. Explicit ID lookup
        if campaign_id:
            campaign = await self.get_campaign(session, campaign_id)
            if campaign and campaign["status"] not in ["COMPLETED", "REJECTED"]:
                return campaign

        # 2. Strict scan for unfinished campaigns
        conditions = ["deleted_at IS NULL", "status NOT IN ('COMPLETED', 'REJECTED')"]
        params = {"tenant_id": tenant_id}

        if user_id:
            conditions.append("user_id = :user_id")
            params["user_id"] = user_id

        where_clause = " AND ".join(conditions)
        sql = text(f"""
            SELECT id, user_id, source_input, current_step, status, category, topic_data, created_at, gold_metadata
            FROM content_campaigns
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT 5
        """)

        result = await session.execute(sql, params)
        rows = result.all()
        if not rows:
            return None

        active_campaigns = []
        for r in rows:
            active_campaigns.append({
                "id": r[0],
                "user_id": r[1],
                "source_input": r[2],
                "current_step": r[3],
                "status": r[4],
                "category": r[5],
                "topic_data": r[6] or {},
                "created_at": r[7],
                "gold_metadata": r[8] or {}
            })

        # 3. Query-based matching
        if query:
            q_norm = normalize_vn(query)
            for c in active_campaigns:
                title = normalize_vn(c["topic_data"].get("title", ""))
                source = normalize_vn(c["source_input"])
                if (title and title in q_norm) or (source and source in q_norm):
                    # Re-fetch full if needed, but for now partial is enough for handlers
                    # Let's re-fetch full to be safe as handlers expect full object/dict
                    return await self.get_campaign(session, c["id"])

        # 4. Fallback: Recent active (< 10 mins)
        latest = active_campaigns[0]
        now = datetime.now(timezone.utc)
        created_at = latest["created_at"]
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        if (now - created_at).total_seconds() < 600.0:
            return await self.get_campaign(session, latest["id"])

        return None

    async def create_campaign(
        self,
        session: AsyncSession,
        user_id: Optional[str],
        source_input: str,
        tenant_id: str,
        gold_metadata: Dict[str, object],
        category: str
    ) -> Dict[str, object]:
        """Atomic INSERT via Raw SQL."""
        new_id = str(uuid.uuid4())
        sql = text("""
            INSERT INTO content_campaigns (
                id, user_id, source_input, tenant_id, gold_metadata, category,
                current_step, status, created_at, updated_at
            ) VALUES (
                :id, :user_id, :source_input, :tenant_id, :gold_metadata, :category,
                1, 'PROCESSING', NOW(), NOW()
            )
            RETURNING id, user_id, source_input, current_step, status, category, tenant_id
        """)

        result = await session.execute(sql, {
            "id": new_id,
            "user_id": user_id,
            "source_input": source_input,
            "tenant_id": tenant_id,
            "gold_metadata": json.dumps(gold_metadata),
            "category": category
        })
        r = result.first()
        return {
            "id": r[0],
            "user_id": r[1],
            "source_input": r[2],
            "current_step": r[3],
            "status": r[4],
            "category": r[5],
            "tenant_id": r[6]
        }

    async def update_campaign(self, session: AsyncSession, campaign_id: str, update_data: Dict[str, object]) -> Optional[Dict[str, object]]:
        """Surgical UPDATE via Raw SQL."""
        if not update_data:
            return await self.get_campaign(session, campaign_id)

        set_clauses = []
        params = {"id": campaign_id}

        for key, value in update_data.items():
            db_col = key
            # Mapping schema keys to DB columns if necessary (though usually they match)
            if isinstance(value, (dict, list)):
                params[key] = json.dumps(value)
            else:
                params[key] = value

            set_clauses.append(f"{db_col} = :{key}")

        set_clauses.append("updated_at = NOW()")

        sql = text(f"""
            UPDATE content_campaigns
            SET {', '.join(set_clauses)}
            WHERE id = :id
            RETURNING id, current_step, status, user_id, tenant_id
        """)

        result = await session.execute(sql, params)
        r = result.first()
        if not r:
            return None

        return {
            "id": r[0],
            "current_step": r[1],
            "status": r[2],
            "user_id": r[3],
            "tenant_id": r[4]
        }

    @staticmethod
    def get_gold_config(campaign: Dict[str, object]) -> dict:
        """Returns the creation configuration from gold_metadata or topic_data safely (Zero-Hydration)."""
        gold = campaign.get("gold_metadata") or {}
        config = gold.get("creation_config")
        if config:
            return config

        topic = campaign.get("topic_data") or {}
        return topic.get("creation_config") or {}

    @staticmethod
    def get_gold_val(campaign: Dict[str, object], key: str, fallback: object = None) -> object:
        """Surgically extracts a value from gold_metadata or falls back to topic_data (Zero-Hydration)."""
        gold = campaign.get("gold_metadata") or {}
        if key in gold:
            return gold[key]

        topic = campaign.get("topic_data") or {}
        return topic.get(key, fallback)

    async def add_event(
        self,
        session: AsyncSession,
        campaign_id: str,
        event_type: str,
        payload: Dict[str, object],
        tenant_id: str
    ) -> str:
        """Atomic INSERT for CampaignEvent."""
        new_id = str(uuid.uuid4())
        sql = text("""
            INSERT INTO campaign_events (id, campaign_id, event_type, payload, tenant_id, created_at, updated_at)
            VALUES (:id, :campaign_id, :event_type, :payload, :tenant_id, NOW(), NOW())
            RETURNING id
        """)
        result = await session.execute(sql, {
            "id": new_id,
            "campaign_id": campaign_id,
            "event_type": event_type,
            "payload": json.dumps(payload),
            "tenant_id": tenant_id
        })
        return str(result.scalar())

    async def get_event_count(self, session: AsyncSession, campaign_id: str, event_type: str, step: int) -> int:
        """Fetch event count for backtrack logic."""
        sql = text("""
            SELECT COUNT(*) FROM campaign_events
            WHERE campaign_id = :campaign_id
              AND event_type = :event_type
              AND (payload->>'step')::int = :step
        """)
        result = await session.execute(sql, {
            "campaign_id": campaign_id,
            "event_type": event_type,
            "step": step
        })
        return result.scalar() or 0

campaign_service = CampaignService()
