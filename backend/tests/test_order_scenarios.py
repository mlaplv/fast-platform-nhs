import sys
import re
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

# Patch JSONB before importing models
import sqlalchemy.dialects.postgresql
from sqlalchemy import JSON
sqlalchemy.dialects.postgresql.JSONB = JSON

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database.models import Base
from backend.services.commerce.logic.lead_extractor import LeadExtractor, ExtractedLead, LeadOrderItem
from backend.database.models.commerce import ProductBase

# Use an in-memory database for testing
DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_lead_extractor_staff_order_ambiguous(db_session: AsyncSession) -> None:
    """Scenario: Staff says 'Cho 1 đơn' -> Should NOT force definite purchase (now ambiguous)"""
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    trinity_bridge.run = AsyncMock(return_value={"is_definite_purchase": False, "items": []})

    extractor: LeadExtractor = LeadExtractor()
    message: str = "Cho 1 đơn về 336/44 Nguyễn Văn Luông, Phú Lâm 0949901122 Lập"
    result: ExtractedLead = await extractor.extract_and_convert(db_session, message, "session_staff")

    assert result.is_definite_purchase is False

@pytest.mark.asyncio
async def test_lead_extractor_quantity_force(db_session: AsyncSession) -> None:
    """Scenario: User says '2 lọ' -> Force is_definite_purchase = True"""
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    # Mock AI to return the extracted items
    trinity_bridge.run = AsyncMock(return_value={"is_definite_purchase": True, "items": [{"name": "lọ", "quantity": 2}]})

    extractor: LeadExtractor = LeadExtractor()
    message: str = "2 lọ"
    result: ExtractedLead = await extractor.extract_and_convert(db_session, message, "session_qty")

    assert result.is_definite_purchase is True

@pytest.mark.asyncio
async def test_lead_extractor_confirmation_keywords(db_session: AsyncSession) -> None:
    """Scenario: Confirmation words rely on AI extraction and history hydration"""
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    # AI identifies confirmation
    trinity_bridge.run = AsyncMock(return_value={"is_definite_purchase": True, "items": []})

    # Add the product to the mock DB
    prod = ProductBase(id="sp1", name="Miccosmo", price=450000, discount_price=450000, slug="sp1", stock=100)
    db_session.add(prod)
    await db_session.commit()

    extractor: LeadExtractor = LeadExtractor()
    message: str = "Ok"
    
    # Mock history hydration to return previous items
    async def mock_hydrate_history(db: AsyncSession, session_id: str, lead: ExtractedLead) -> ExtractedLead:
        lead.items = [LeadOrderItem(id="sp1", name="Miccosmo", quantity=1)]
        lead.customer_phone = "0949901122"
        return lead

    with patch("backend.services.xohi_memory.xohi_memory.client", None):
        with patch("backend.services.commerce.logic.lead_extractor.LeadExtractor._hydrate_from_history", side_effect=mock_hydrate_history):
            result: ExtractedLead = await extractor.extract_and_convert(db_session, message, "session_ok")

    assert result.is_definite_purchase is True

@pytest.mark.asyncio
async def test_lead_extractor_ambiguous_no_force(db_session: AsyncSession) -> None:
    """Scenario: 'Cho 1 đơn' without units should NOT force definite purchase"""
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    # Mock AI to say it's not a definite purchase
    trinity_bridge.run = AsyncMock(return_value={"is_definite_purchase": False, "items": []})

    extractor: LeadExtractor = LeadExtractor()
    message: str = "Cho 1 đơn"
    result: ExtractedLead = await extractor.extract_and_convert(db_session, message, "session_ambiguous")

    assert result.is_definite_purchase is False
