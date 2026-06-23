"""
SEO Entity Extractor — SGE Intelligence Layer
=============================================
Chuyển từ keyword-based sang entity-based SEO matching.

Extracted entities: Brand, Ingredient, Pain, Symptom, Competitor, Feature, Category
Intent classification: informational_why | informational_how | informational_what
                       | comparison | transactional | pillar | unknown

Design:
- PydanticAI V2 với strict output schema — CẤM 'any' type
- Async, stateless — inject vào SeoMatchingService pipeline
- Results persisted vào seo_nodes.entities_json + seo_nodes.intent_type
- Full-Async I/O, zero blocking calls
"""
import asyncio
import logging
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.models.seo import SeoNode
from backend.database import current_tenant_id

logger = logging.getLogger("api-gateway")

_EXTRACT_TIMEOUT = 20.0
_INTENT_TIMEOUT = 12.0


# ─── Strict Output Types (zero 'any') ─────────────────────────────────────────

class ExtractedEntity(BaseModel):
    """Một thực thể được nhận diện trong nội dung."""
    entity_type: str  # Brand | Ingredient | Pain | Symptom | Competitor | Feature | Category
    name: str
    confidence: float = Field(ge=0.0, le=1.0)


class EntityExtractionResult(BaseModel):
    """Output schema cho PydanticAI entity extraction."""
    entities: list[ExtractedEntity]
    primary_topic: str  # Chủ đề chính của nội dung


class IntentClassificationResult(BaseModel):
    """Output schema cho PydanticAI intent classification."""
    intent_type: str  # informational_why | informational_how | informational_what | comparison | transactional | unknown
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


# ─── Service ──────────────────────────────────────────────────────────────────

class SeoEntityExtractor:
    """
    Extracts structured entities and classifies search intent
    from article/product content using PydanticAI V2.

    Called after a node is registered — enriches seo_nodes with
    SGE-ready entity graph data for schema linking and entity-aware matching.
    """

    async def extract_and_persist(
        self,
        db: AsyncSession,
        node_id: str,
        title: str,
        content: str,
        entity_type: str,  # "article" | "product"
    ) -> tuple[list[dict], str]:
        """
        Main pipeline: extract entities + classify intent, persist to seo_nodes.
        Returns (entities_list, intent_type) for downstream use.
        """
        # Run both tasks concurrently
        entities_result, intent_result = await asyncio.gather(
            self._extract_entities(title, content, entity_type),
            self._classify_intent(title, content),
            return_exceptions=True,
        )

        # Handle partial failures gracefully
        entities: list[dict] = []
        if isinstance(entities_result, EntityExtractionResult):
            entities = [e.model_dump() for e in entities_result.entities]
        elif isinstance(entities_result, Exception):
            logger.warning("[SeoEntity] Entity extraction failed: %s", entities_result)

        intent: str = "unknown"
        if isinstance(intent_result, IntentClassificationResult):
            intent = intent_result.intent_type
        elif isinstance(intent_result, Exception):
            logger.warning("[SeoEntity] Intent classification failed: %s", intent_result)

        # Persist to DB
        await self._persist_to_node(db, node_id, entities, intent)
        logger.info(
            "[SeoEntity] Node %s: %d entities extracted, intent=%s",
            node_id, len(entities), intent
        )
        return entities, intent

    async def _extract_entities(
        self,
        title: str,
        content: str,
        entity_type: str,
    ) -> EntityExtractionResult:
        """
        Tier 1: Extract named entities using PydanticAI with domain-aware prompt.
        """
        from pydantic_ai import Agent
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

        agent: Agent[None, EntityExtractionResult] = Agent(
            system_prompt=(
                "Bạn là chuyên gia phân tích thực thể SEO cho thị trường mỹ phẩm và dược phẩm Việt Nam. "
                "Nhiệm vụ: Nhận diện các thực thể quan trọng trong nội dung. "
                "Entity types được phép: Brand (tên thương hiệu), Ingredient (thành phần hoạt chất), "
                "Pain (nỗi đau/vấn đề của khách hàng), Symptom (triệu chứng), "
                "Competitor (sản phẩm/thương hiệu cạnh tranh được đề cập), "
                "Feature (tính năng/công dụng đặc biệt), Category (danh mục sản phẩm). "
                "Chỉ trả về những thực thể có confidence >= 0.6. Tối đa 15 entities. "
                "Trả về JSON theo schema yêu cầu."
            ),
            output_type=EntityExtractionResult,
        )

        content_preview = content[:800] if content else ""
        prompt = (
            f"Loại nội dung: {entity_type}\n"
            f"Tiêu đề: {title}\n"
            f"Nội dung: {content_preview}\n\n"
            "Hãy nhận diện các thực thể quan trọng và primary_topic của nội dung này."
        )

        result = await trinity_bridge.run(agent, prompt, timeout=_EXTRACT_TIMEOUT)
        return result

    async def _classify_intent(
        self,
        title: str,
        content: str,
    ) -> IntentClassificationResult:
        """
        Tier 2: Classify search intent to drive schema type selection.
        """
        from pydantic_ai import Agent
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

        agent: Agent[None, IntentClassificationResult] = Agent(
            system_prompt=(
                "Bạn là chuyên gia phân loại search intent cho SEO. "
                "Phân loại nội dung vào đúng 1 trong các loại sau:\n"
                "- informational_why: Giải thích nguyên nhân, lý do (Tại sao da bị thâm?)\n"
                "- informational_how: Hướng dẫn thực hiện (Làm thế nào để trị thâm?)\n"
                "- informational_what: Định nghĩa, giới thiệu (Niacinamide là gì?)\n"
                "- comparison: So sánh sản phẩm/thành phần\n"
                "- transactional: Mua hàng, đặt hàng, giá cả\n"
                "- unknown: Không xác định được\n"
                "Trả về JSON theo schema yêu cầu."
            ),
            output_type=IntentClassificationResult,
        )

        content_preview = content[:400] if content else ""
        prompt = f"Tiêu đề: {title}\nNội dung (tóm tắt): {content_preview}"

        result = await trinity_bridge.run(agent, prompt, timeout=_INTENT_TIMEOUT)
        return result

    async def _persist_to_node(
        self,
        db: AsyncSession,
        node_id: str,
        entities: list[dict],
        intent_type: str,
    ) -> None:
        """Persist extracted data to seo_nodes table."""
        node = await db.scalar(
            select(SeoNode).where(
                SeoNode.id == node_id,
                SeoNode.deleted_at.is_(None),
            )
        )
        if not node:
            logger.warning("[SeoEntity] Node %s not found for entity persistence", node_id)
            return

        node.entities_json = entities if entities else None
        node.intent_type = intent_type

    def get_entity_names(
        self,
        entities: list[dict],
        entity_type_filter: Optional[str] = None,
    ) -> list[str]:
        """
        Helper: Extract entity names from entities_json, optionally filtered by type.
        Used by schema builder for 'about' and 'mentions' population.
        """
        if not entities:
            return []
        if entity_type_filter:
            return [
                e["name"] for e in entities
                if e.get("entity_type") == entity_type_filter and e.get("name")
            ]
        return [e["name"] for e in entities if e.get("name")]

    def get_schema_type_for_intent(self, intent_type: Optional[str]) -> str:
        """
        Maps intent_type → optimal JSON-LD @type for SGE.
        SGE prefers specific types over generic 'Article'.
        """
        mapping: dict[str, str] = {
            "informational_why": "FAQPage",
            "informational_how": "HowTo",
            "informational_what": "NewsArticle",
            "comparison": "ItemList",
            "transactional": "Product",
            "pillar": "WebPage",
            "unknown": "Article",
        }
        return mapping.get(intent_type or "unknown", "Article")
