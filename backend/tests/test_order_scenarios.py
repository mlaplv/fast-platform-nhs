import sys
import re
from unittest.mock import AsyncMock

# Patch JSONB before importing models
import sqlalchemy.dialects.postgresql
from sqlalchemy import JSON
sqlalchemy.dialects.postgresql.JSONB = JSON

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database.models import Base
from backend.services.commerce.logic.lead_extractor import LeadExtractor

# Use an in-memory database for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_lead_extractor_staff_order_ambiguous(db_session):
    """Scenario: Staff says 'Cho 1 đơn' -> Should NOT force definite purchase (now ambiguous)"""
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    trinity_bridge.run = AsyncMock(return_value={"is_definite_purchase": False, "items": []})

    extractor = LeadExtractor()
    message = "Cho 1 đơn về 336/44 Nguyễn Văn Luông, Phú Lâm 0949901122 Lập"
    result = await extractor.extract_and_convert(db_session, message, "session_staff")

    assert result.is_definite_purchase is False

@pytest.mark.asyncio
async def test_lead_extractor_quantity_force(db_session):
    """Scenario: User says '2 lọ' -> Force is_definite_purchase = True"""
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    trinity_bridge.run = AsyncMock(return_value={"is_definite_purchase": False, "items": []})

    extractor = LeadExtractor()
    message = "2 lọ"
    result = await extractor.extract_and_convert(db_session, message, "session_qty")

    assert result.is_definite_purchase is True

@pytest.mark.asyncio
async def test_lead_extractor_confirmation_keywords(db_session):
    """Scenario: Confirmation words rely on AI extraction"""
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    # AI identifies confirmation
    trinity_bridge.run = AsyncMock(return_value={"is_definite_purchase": True, "items": []})

    extractor = LeadExtractor()
    message = "Ok"
    result = await extractor.extract_and_convert(db_session, message, "session_ok")

    assert result.is_definite_purchase is True

@pytest.mark.asyncio
async def test_lead_extractor_ambiguous_no_force(db_session):
    """Scenario: 'Cho 1 đơn' without units should NOT force definite purchase"""
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    # Mock AI to say it's not a definite purchase
    trinity_bridge.run = AsyncMock(return_value={"is_definite_purchase": False, "items": []})

    extractor = LeadExtractor()
    message = "Cho 1 đơn"
    result = await extractor.extract_and_convert(db_session, message, "session_ambiguous")

    assert result.is_definite_purchase is False
