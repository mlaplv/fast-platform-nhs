import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.commerce.support_knowledge import SupportKnowledgeService
from backend.database.repositories import SupportKnowledgeRepository

# Elite V2.2: 3-Layer Memory Test Suite (Integration)

@pytest.mark.asyncio
async def test_knowledge_index_caching():
    """Verify Layer 1 (Index) Redis caching logic."""
    db = AsyncMock(spec=AsyncSession)
    repo = MagicMock(spec=SupportKnowledgeRepository)
    service = SupportKnowledgeService(repo=repo)
    
    # Mock xohi_memory methods
    from backend.services.xohi_memory import xohi_memory
    xohi_memory.get_kb_layer1 = AsyncMock()
    xohi_memory.set_kb_layer1 = AsyncMock()
    
    # CASE 1: Cache Miss -> DB Query
    xohi_memory.get_kb_layer1.return_value = None
    
    # Mock DB Query result
    mock_row = MagicMock()
    mock_row.id = "123"
    mock_row.category = "FAQ"
    mock_row.question = "Test Question"
    mock_row.priority = 10
    
    mock_res = MagicMock()
    mock_res.all.return_value = [mock_row]
    db.execute.return_value = mock_res
    
    index = await service.get_knowledge_index(db)
    
    assert "Test Question" in index
    db.execute.assert_called_once() # DB hit
    xohi_memory.set_kb_layer1.assert_called_once() # Cache set
    
    # CASE 2: Cache Hit -> No DB Query
    db.execute.reset_mock()
    xohi_memory.get_kb_layer1.return_value = "CACHED INDEX DATA"
    
    index_cached = await service.get_knowledge_index(db)
    
    assert index_cached == "CACHED INDEX DATA"
    db.execute.assert_not_called() # NO DB HIT!

@pytest.mark.asyncio
async def test_topic_details_fetch():
    """Verify Layer 2 (Topics) detail retrieval."""
    repo = MagicMock(spec=SupportKnowledgeRepository)
    service = SupportKnowledgeService(repo=repo)
    db = AsyncMock(spec=AsyncSession)
    
    mock_item = MagicMock()
    mock_item.id = "456"
    mock_item.question = "How to use?"
    mock_item.answer = "Apply to skin."
    mock_item.deleted_at = None
    mock_item.is_active = True
    
    repo.get_one_or_none.return_value = mock_item
    
    details = await service.get_topic_details(db, "456")
    
    assert "Apply to skin." in details
    repo.get_one_or_none.assert_called_with(id="456")
