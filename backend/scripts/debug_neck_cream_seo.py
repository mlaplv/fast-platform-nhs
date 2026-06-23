import asyncio
from sqlalchemy import select, text
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoNode, SeoEdge, SeoContextualLink

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        # Find product by slug
        slug = "miccosmo-hurry-harry-premium-neck-cream-rich-40gr-kem-duong-sang-co"
        p_row = (await db.execute(
            text("SELECT id, name, slug FROM product_bases WHERE slug = :slug"),
            {"slug": slug}
        )).mappings().first()
        
        if not p_row:
            # Let's search by prefix or name
            print("Product not found by slug. Let's search all products containing neck-cream...")
            rows = (await db.execute(
                text("SELECT id, name, slug FROM product_bases WHERE slug LIKE '%neck-cream%'")
            )).mappings().all()
            for r in rows:
                print(f"  Found: {r['name']} | slug: {r['slug']} | id: {r['id']}")
            return
            
        print(f"Product ID: {p_row['id']}")
        print(f"Product Name: {p_row['name']}")
        
        # Find SEO Node
        stmt_node = select(SeoNode).where(SeoNode.entity_id == p_row["id"])
        node = await db.scalar(stmt_node)
        if node:
            print("\n--- SEO Node ---")
            print(f"Node ID: {node.id}")
            print(f"Node Label: {node.node_label}")
            print(f"Node Slug: {node.node_slug}")
            print(f"Is Pillar: {node.is_pillar}")
            print(f"Intent Type: {node.intent_type}")
            print(f"Entities JSON: {node.entities_json}")
            
            # Find incoming & outgoing edges
            stmt_out = select(SeoEdge).where(SeoEdge.source_node_id == node.id)
            out_edges = (await db.execute(stmt_out)).scalars().all()
            print(f"Outgoing Edges count: {len(out_edges)}")
            for e in out_edges:
                print(f"  Edge: {e.source_node_id} -> {e.target_node_id} | type: {e.link_type} | confirmed: {e.is_confirmed}")
                
            stmt_in = select(SeoEdge).where(SeoEdge.target_node_id == node.id)
            in_edges = (await db.execute(stmt_in)).scalars().all()
            print(f"Incoming Edges count: {len(in_edges)}")
            for e in in_edges:
                print(f"  Edge: {e.source_node_id} -> {e.target_node_id} | type: {e.link_type} | confirmed: {e.is_confirmed}")
                
            # Find contextual links pointing to this node
            stmt_ctx = select(SeoContextualLink).where(SeoContextualLink.target_node_id == node.id)
            ctx_links = (await db.execute(stmt_ctx)).scalars().all()
            print(f"Contextual Links count: {len(ctx_links)}")
            for cl in ctx_links:
                print(f"  Contextual Link: id={cl.id} | source_article_id={cl.source_article_id} | status={cl.status} | anchor={cl.anchor_text}")
        else:
            print("\nSEO Node NOT found for this product ID!")

if __name__ == "__main__":
    asyncio.run(main())
