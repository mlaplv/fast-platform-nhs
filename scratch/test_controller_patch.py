import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import alchemy_config, current_tenant_id
from backend.controllers.seo import SeoController
from backend.database.models.seo import SeoContextualLink, SeoContextualLinkStatus
from sqlalchemy import select

async def run():
    session_maker = alchemy_config.create_session_maker()
    current_tenant_id.set("osmo.vn")
    async with session_maker() as db:
        # Get a pending link
        link_id = "019ebeff-af4d-703a-b62a-b683e20b8f99"
        
        # Instantiate controller
        controller = SeoController(owner=None)
        
        # Test approval via original wrapped function fn
        print("Testing status update to 'approved'...")
        res = await controller.update_contextual_link.fn(
            controller,
            db_session=db,
            link_id=link_id,
            data={"status": "approved"}
        )
        print(f"Result: ok={res.ok}, message={res.message}, data={res.data}")
        
        # Verify status in DB
        db.expire_all()
        link = await db.scalar(select(SeoContextualLink).where(SeoContextualLink.id == link_id))
        print(f"Status in DB after commit/refresh: {link.status} (type: {type(link.status)})")

if __name__ == "__main__":
    asyncio.run(run())
