import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.schemas.product import ProductResponse, ProductMetadata, FaqItem
from backend.services.commerce.product import ProductService

@pytest.mark.asyncio
async def test_faq_hydration_admin_slicing():
    # Arrange
    service = ProductService(vector_service=AsyncMock())
    db_session = AsyncMock()
    
    # Mock database result to return None for voucher to avoid viral configuration errors
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    db_session.execute.return_value = mock_result

    # Create dummy FAQs (5 items)
    faqs = [
        FaqItem(question=f"Q{i}", answer=f"A{i}")
        for i in range(5)
    ]
    metadata = ProductMetadata(faqs=faqs)
    product = ProductResponse(
        id="test-prod-123",
        name="Test Product",
        sku="TEST-SKU",
        price=1000.0,
        stock=10,
        status="ACTIVE",
        category="Test Category",
        categoryId="cat-123",
        slug="test-product",
        images=[],
        attributes={},
        metadata=metadata.model_dump(),  # Pass as dict to satisfy field_validator
        tierVariations=[],
        variants=[],
        created_at="2026-06-22T00:00:00Z"
    )

    # Act (Admin hydration: is_public=False)
    await service._hydrate_product_response(db_session, product, is_public=False)

    # Assert
    assert product.metadata.faqs_total == 5
    assert len(product.metadata.faqs) == 3
    assert product.metadata.faqs[0].question == "Q0"
    assert product.metadata.faqs[2].question == "Q2"

@pytest.mark.asyncio
async def test_faq_hydration_public_full():
    # Arrange
    service = ProductService(vector_service=AsyncMock())
    db_session = AsyncMock()
    
    # Mock database result to return None for voucher to avoid viral configuration errors
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    db_session.execute.return_value = mock_result

    # Create dummy FAQs (5 items)
    faqs = [
        FaqItem(question=f"Q{i}", answer=f"A{i}")
        for i in range(5)
    ]
    metadata = ProductMetadata(faqs=faqs)
    product = ProductResponse(
        id="test-prod-123",
        name="Test Product",
        sku="TEST-SKU",
        price=1000.0,
        stock=10,
        status="ACTIVE",
        category="Test Category",
        categoryId="cat-123",
        slug="test-product",
        images=[],
        attributes={},
        metadata=metadata.model_dump(),  # Pass as dict to satisfy field_validator
        tierVariations=[],
        variants=[],
        created_at="2026-06-22T00:00:00Z"
    )

    # Act (Public hydration: is_public=True)
    await service._hydrate_product_response(db_session, product, is_public=True)

    # Assert
    assert product.metadata.faqs_total == 5
    assert len(product.metadata.faqs) == 5
    assert product.metadata.faqs[4].question == "Q4"
