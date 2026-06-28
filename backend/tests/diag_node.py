import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoNode, SeoEdge

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        node = await db.get(SeoNode, "019eb987-b996-7388-8ab2-479eb8f5bdfe")
        if node:
            print(f"Pillar Node: Label={node.node_label} | Slug={node.node_slug} | IsPillar={node.is_pillar} | Type={node.entity_type}")
        else:
            print("Node not found!")
            
        # Get edges where this node is source or target
        res_src = await db.execute(select(SeoEdge).where(SeoEdge.source_node_id == "019eb987-b996-7388-8ab2-479eb8f5bdfe"))
        src_edges = res_src.scalars().all()
        print(f"Edges where this node is SOURCE: {len(src_edges)}")
        for e in src_edges:
            print(f" -> Target: {e.target_node_id}")
            
        res_tgt = await db.execute(select(SeoEdge).where(SeoEdge.target_node_id == "019eb987-b996-7388-8ab2-479eb8f5bdfe"))
        tgt_edges = res_tgt.scalars().all()
        print(f"Edges where this node is TARGET: {len(tgt_edges)}")
        for e in tgt_edges:
            print(f" -> Source: {e.source_node_id}")

if __name__ == "__main__":
    asyncio.run(main())
