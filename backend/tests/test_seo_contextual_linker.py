import pytest
import uuid
import os
import hashlib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from litestar.testing import AsyncTestClient

from backend.main import app
from backend.database.models.content import Article
from backend.database.models.seo import SeoContextualLink, SeoContextualLinkStatus, SeoNode, SeoEntityType
from backend.database.models import User
from backend.services.seo_contextual_linker import seo_contextual_linker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/fast_platform")

@pytest.mark.asyncio
async def test_seo_contextual_linker_dry_run_and_non_destructive():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Create test article
        article_id = str(uuid.uuid4())
        original_content = "<p>Sữa rửa mặt là sản phẩm làm sạch da hàng ngày.</p>"
        article = Article(
            id=article_id,
            title="Bài viết về sữa rửa mặt",
            slug=f"sua-rua-mat-{article_id[:8]}",
            content=original_content,
            status="PUBLISHED",
            tenant_id="default"
        )
        session.add(article)
        
        # 2. Create target SeoNode first to satisfy foreign key constraint on target_node_id
        node_id = str(uuid.uuid4())
        node = SeoNode(
            id=node_id,
            entity_type=SeoEntityType.PRODUCT,
            entity_id=str(uuid.uuid4()),
            node_label="Sữa rửa mặt Miccosmo",
            node_slug="sua-rua-mat-miccosmo",
            tenant_id="default"
        )
        session.add(node)
        
        # 3. Fetch or create a user for reviewed_by FK constraint
        stmt_user = select(User).limit(1)
        res_user = await session.execute(stmt_user)
        db_user = res_user.scalar_one_or_none()
        
        created_user = False
        if not db_user:
            db_user = User(
                id=str(uuid.uuid4()),
                email="test_seo_reviewer@osmo.vn",
                status="ACTIVE",
                security_stamp="VALID_STAMP_2026",
                tenant_id="default"
            )
            session.add(db_user)
            created_user = True
            
        await session.commit()
        reviewer_id = db_user.id

        # 4. Add approved link recommendation with all non-nullable fields populated
        link_id = str(uuid.uuid4())
        content_hash = hashlib.md5(original_content.encode()).hexdigest()
        link = SeoContextualLink(
            id=link_id,
            tenant_id="default",
            source_article_id=article_id,
            target_node_id=node_id,
            target_url="https://osmo.vn/sua-rua-mat",
            original_sentence="Sữa rửa mặt là sản phẩm làm sạch da hàng ngày.",
            linked_sentence="Sữa rửa mặt là sản phẩm làm sạch da hàng ngày.", # Non-nullable field
            anchor_text="Sữa rửa mặt",
            matched_entity_type="ingredient",
            matched_entity_name="sữa rửa mặt",
            ai_confidence=0.95, # Non-nullable field
            content_hash=content_hash, # Non-nullable field
            sentence_index=0,
            status=SeoContextualLinkStatus.APPROVED,
        )
        session.add(link)
        await session.commit()

        # Call apply_approved_links with reviewer_id
        result = await seo_contextual_linker.apply_approved_links(session, article_id, reviewer_id=reviewer_id)
        
        assert result["applied_count"] == 1
        
        # Verify the database records:
        # 1. The article content MUST remain unchanged (Non-destructive JIT)
        session.expire(article)
        db_article = await session.get(Article, article_id)
        assert db_article.content == original_content

        # 2. The link status must be APPLIED and reviewed_by should equal reviewer_id
        session.expire(link)
        db_link = await session.get(SeoContextualLink, link_id)
        assert db_link.status == SeoContextualLinkStatus.APPLIED
        assert db_link.reviewed_by == reviewer_id

        # Cleanup
        await session.delete(db_link)
        if created_user:
            await session.delete(db_user)
        await session.delete(node)
        await session.delete(db_article)
        await session.commit()
        
    await engine.dispose()

@pytest.mark.asyncio
async def test_client_get_contextual_links_api():
    async with AsyncTestClient(app=app) as client:
        # We can call the client-side API endpoint for contextual-links
        # For a non-existent or dummy article, it should return 200 with empty list
        response = await client.get(f"/api/v1/client/news/{str(uuid.uuid4())}/contextual-links")
        assert response.status_code == 200
        data = response.json()
        assert "links" in data
        assert isinstance(data["links"], list)


def test_calculate_eas_generic_brand_filtering():
    from backend.services.seo_contextual_linker import SentenceLinkSuggestion
    
    pillars = [
        {
            "id": "pillar_1",
            "label": "Miccosmo White Label Premium Placenta Essence 180ml - Tinh chất cấp ẩm, làm dịu da",
            "slug": "miccosmo-white-label-essence",
            "url": "https://osmo.vn/miccosmo-white-label-essence",
            "entity_type": "PRODUCT",
            "pillar_topic": "Essence",
            "entities": [],
        }
    ]
    
    # Generic anchor text suggestion (should fail brand gate -> EAS = 0.0)
    generic_suggestion = SentenceLinkSuggestion(
        sentence_index=0,
        should_link=True,
        original_sentence="Bao bì có bị móp méo hay rò rỉ tinh chất không.",
        anchor_text="rò rỉ tinh chất",
        linked_sentence="Bao bì có bị móp méo hay <a href='pillar_1'>rò rỉ tinh chất</a> không.",
        target_pillar_id="pillar_1",
        matched_entity_type="feature",
        matched_entity_name="Miccosmo White Label Premium Placenta Essence 180ml - Tinh chất cấp ẩm, làm dịu da",
        confidence=0.85,
        reasoning="Cụm từ liên quan đến tinh chất"
    )
    
    score_generic = seo_contextual_linker._calculate_eas(generic_suggestion, pillars)
    assert score_generic == 0.0
    
    # Specific brand-relevant anchor text suggestion (should pass brand gate -> EAS > 0.0)
    brand_suggestion = SentenceLinkSuggestion(
        sentence_index=0,
        should_link=True,
        original_sentence="Bạn có thể dùng tinh chất Placenta Miccosmo để dưỡng da hàng ngày.",
        anchor_text="tinh chất Placenta Miccosmo",
        linked_sentence="Bạn có thể dùng <a href='pillar_1'>tinh chất Placenta Miccosmo</a> để dưỡng da hàng ngày.",
        target_pillar_id="pillar_1",
        matched_entity_type="brand",
        matched_entity_name="Miccosmo White Label Premium Placenta Essence 180ml - Tinh chất cấp ẩm, làm dịu da",
        confidence=0.90,
        reasoning="Nhắc trực tiếp tên thương hiệu và dòng sản phẩm"
    )
    
    score_brand = seo_contextual_linker._calculate_eas(brand_suggestion, pillars)
    assert score_brand > 0.0

    # Test settings configurations (brand_keywords and generic_exclusions)
    custom_brand_suggestion = SentenceLinkSuggestion(
        sentence_index=0,
        should_link=True,
        original_sentence="Bạn nên sử dụng sản phẩm của custombrand để cải thiện.",
        anchor_text="sản phẩm custombrand",
        linked_sentence="Bạn nên sử dụng <a href='pillar_1'>sản phẩm custombrand</a> để cải thiện.",
        target_pillar_id="pillar_1",
        matched_entity_type="brand",
        matched_entity_name="Miccosmo White Label Premium Placenta Essence 180ml - Tinh chất cấp ẩm, làm dịu da",
        confidence=0.90,
        reasoning="Nhắc trực tiếp"
    )

    # Without custom config, "custombrand" is generic/not a brand, so it fails brand gate
    score_no_custom = seo_contextual_linker._calculate_eas(custom_brand_suggestion, pillars)
    assert score_no_custom == 0.0

    # With custom config, it passes
    score_with_custom = seo_contextual_linker._calculate_eas(
        custom_brand_suggestion, 
        pillars, 
        brand_keywords_config=["custombrand"],
        generic_exclusions_config={"sản", "phẩm"}
    )
    assert score_with_custom > 0.0


def test_brand_relevance_multiplier_and_generic_penalties():
    from backend.services.seo_contextual_linker import SeoContextualLinker, SentenceLinkSuggestion
    
    seo_contextual_linker = SeoContextualLinker()
    
    pillars = [
        {
            "id": "pillar_1",
            "label": "Miccosmo White Label Premium Placenta Essence 180ml - Tinh chất cấp ẩm, làm dịu da",
            "entity_type": "PRODUCT",
            "slug": "miccosmo-white-label-essence",
            "url": "/products/miccosmo-white-label-essence.html",
            "pillar_topic": "Essence",
            "entities": [],
        },
        {
            "id": "pillar_2",
            "label": "Miccosmo Hurry Harry Premium Neck Cream Rich 40gr - Kem dưỡng sáng cổ",
            "entity_type": "PRODUCT",
            "slug": "hurry-harry-neck-cream",
            "url": "/products/hurry-harry-neck-cream.html",
            "pillar_topic": "Neck Cream",
            "entities": [],
        }
    ]
    
    # 1. A generic symptom match: "ngừa lão hóa" targeting placenta essence (without brand name)
    symptom_suggestion = SentenceLinkSuggestion(
        sentence_index=0,
        should_link=True,
        original_sentence="Sản phẩm giúp hỗ trợ ngăn ngừa lão hóa hiệu quả.",
        anchor_text="ngăn ngừa lão hóa",
        linked_sentence="Sản phẩm giúp hỗ trợ <a href='pillar_1'>ngăn ngừa lão hóa</a> hiệu quả.",
        target_pillar_id="pillar_1",
        matched_entity_type="symptom",
        matched_entity_name="Miccosmo White Label Premium Placenta Essence 180ml - Tinh chất cấp ẩm, làm dịu da",
        confidence=0.90,
        reasoning="Cụm từ ngăn ngừa lão hóa liên quan đến tính chất của essence"
    )
    
    # Let's verify that the brand gate fails on this generic symptom (returns 0.0)
    score = seo_contextual_linker._calculate_eas(symptom_suggestion, pillars)
    assert score == 0.0
    
    # Verify multiplier applies 0.4 penalty
    mult = seo_contextual_linker._calculate_brand_relevance_multiplier(symptom_suggestion, pillars)
    assert mult == 0.4
    
    # 2. A high-noise case: "kem dưỡng cổ" targeting Neck Cream
    neck_cream_suggestion = SentenceLinkSuggestion(
        sentence_index=0,
        should_link=True,
        original_sentence="Sử dụng kem dưỡng cổ đều đặn mỗi tối.",
        anchor_text="kem dưỡng cổ",
        linked_sentence="Sử dụng <a href='pillar_2'>kem dưỡng cổ</a> đều đặn mỗi tối.",
        target_pillar_id="pillar_2",
        matched_entity_type="feature",
        matched_entity_name="Miccosmo Hurry Harry Premium Neck Cream Rich 40gr - Kem dưỡng sáng cổ",
        confidence=0.95,
        reasoning="Kem dưỡng cổ trỏ về neck cream"
    )
    
    # Brand gate should fail because "kem", "dưỡng", "cổ" are in generic exclusions (or normalized exclusions)
    score_neck = seo_contextual_linker._calculate_eas(neck_cream_suggestion, pillars)
    assert score_neck == 0.0
    
    mult_neck = seo_contextual_linker._calculate_brand_relevance_multiplier(neck_cream_suggestion, pillars)
    assert mult_neck == 0.4

    # 3. Explicit brand match should pass (multiplier = 1.0, EAS > 0.0)
    brand_ok_suggestion = SentenceLinkSuggestion(
        sentence_index=0,
        should_link=True,
        original_sentence="Sử dụng kem dưỡng cổ Hurry Harry đều đặn mỗi tối.",
        anchor_text="kem dưỡng cổ Hurry Harry",
        linked_sentence="Sử dụng <a href='pillar_2'>kem dưỡng cổ Hurry Harry</a> đều đặn mỗi tối.",
        target_pillar_id="pillar_2",
        matched_entity_type="product",
        matched_entity_name="Miccosmo Hurry Harry Premium Neck Cream Rich 40gr - Kem dưỡng sáng cổ",
        confidence=0.95,
        reasoning="Chứa tên thương hiệu Hurry Harry"
    )
    
    score_ok = seo_contextual_linker._calculate_eas(brand_ok_suggestion, pillars)
    assert score_ok > 0.0
    
    mult_ok = seo_contextual_linker._calculate_brand_relevance_multiplier(brand_ok_suggestion, pillars)
    assert mult_ok == 1.0


