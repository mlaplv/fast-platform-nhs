import asyncio
from backend.database.alchemy_config import alchemy_config
from backend.controllers.seo import SeoController
from backend.database import current_tenant_id

async def main():
    current_tenant_id.set("osmo.vn")
    controller = SeoController()
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        res = await controller.get_pillar_contextual_links(
            db_session=db,
            pillar_node_id="019eb987-b970-7250-8d1e-7a87a9b626c9"
        )
        print("API Response:")
        print(f"  Pillar Title: {res['pillar_title']}")
        print(f"  Stats: {res['stats']}")
        print(f"  Total links in response: {len(res['links'])}")
        for idx, link in enumerate(res['links']):
            print(f"    [{idx}] ID: {link['id']} | Article: {link['source_article_title']} | Status: {link['status']}")

if __name__ == "__main__":
    asyncio.run(main())
