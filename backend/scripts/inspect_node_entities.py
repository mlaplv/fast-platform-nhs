import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoNode

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        slug = "miccosmo-hurry-harry-premium-neck-cream-rich-40gr-kem-duong-sang-co"
        stmt = select(SeoNode).where(SeoNode.node_slug == slug)
        node = await db.scalar(stmt)
        if node:
            print(f"Node: {node.node_label}")
            print(f"Entities JSON: {node.entities_json}")
        else:
            print("Node not found!")

if __name__ == "__main__":
    asyncio.run(main())
