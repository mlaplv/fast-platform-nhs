import asyncio
import os
import sys

sys.path.insert(0, "/app")

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.database.models.seo import SeoNode, SeoEntityType
from backend.utils.uid import new_id_default
from backend.database import current_tenant_id
from backend.services.seo_matching_service import SeoMatchingService
from backend.services.ai_engine.core.encoder_singleton import warmup_encoder

db_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/fast_platform")

async def main():
    engine = create_async_engine(db_url)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    current_tenant_id.set("osmo.vn")
    
    print("Warming up embedding encoder...")
    await warmup_encoder()
    
    matching_service = SeoMatchingService()
    
    async with async_session() as session:
        # 1. Fetch active products from product_bases
        res_prod = await session.execute(text(
            "SELECT id, name, short_description, slug FROM product_bases WHERE deleted_at IS NULL AND tenant_id = 'osmo.vn';"
        ))
        products = res_prod.fetchall()
        print(f"Found {len(products)} active products in product_bases.")
        
        product_nodes_count = 0
        product_nodes = []
        
        # 2. Register/Update all products as pillars
        for prod in products:
            prod_id, name, short_desc, slug = prod
            # Check if exists
            node = await session.scalar(
                select(SeoNode).where(
                    SeoNode.entity_type == SeoEntityType.PRODUCT,
                    SeoNode.entity_id == prod_id,
                    SeoNode.tenant_id == "osmo.vn",
                    SeoNode.deleted_at.is_(None)
                )
            )
            
            ai_summary = f"{name}. {short_desc[:300] if short_desc else ''}"
            url = f"/{slug}"
            
            if not node:
                # Create new product node with is_pillar = True
                node = SeoNode(
                    id=new_id_default(),
                    entity_type=SeoEntityType.PRODUCT,
                    entity_id=prod_id,
                    is_pillar=True,
                    node_label=name,
                    node_slug=slug,
                    node_url=url,
                    ai_summary=ai_summary,
                    tenant_id="osmo.vn"
                )
                session.add(node)
                print(f"Created new product node: {name} as Pillar")
            else:
                # Update existing product node
                node.is_pillar = True
                node.node_label = name
                node.node_slug = slug
                node.node_url = url  # Always enforce correct product URL format: /{slug}
                node.ai_summary = ai_summary
                print(f"Updated existing product node to Pillar: {name}")
                
            product_nodes.append(node)
            product_nodes_count += 1
            
        await session.flush()
        
        # 3. Generate vector embeddings for all product pillars
        print("\nGenerating pgvector embeddings for product pillars...")
        for node in product_nodes:
            await matching_service.upsert_pillar_embedding(
                session,
                node_id=node.id,
                label=node.node_label,
                summary=node.ai_summary
            )
            
        await session.flush()
        
        # 4. Trigger bulk matching for all unclassified nodes
        print("\nRunning AI Matching (clustering) for unclassified nodes...")
        match_result = await matching_service.bulk_match_unclassified(session)
        print(f"AI Matching complete: {match_result}")
        
        await session.commit()
        print(f"\nSuccessfully set {product_nodes_count} products as pillars and ran automatic clustering.")

if __name__ == "__main__":
    asyncio.run(main())
