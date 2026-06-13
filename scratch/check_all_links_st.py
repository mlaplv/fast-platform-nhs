import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import alchemy_config, current_tenant_id

async def run():
    token = current_tenant_id.set("osmo.vn")
    session_maker = alchemy_config.create_session_maker()
    try:
        async with session_maker() as db:
            from sqlalchemy import select
            from backend.database.models.seo import SeoContextualLink
            
            links = (await db.execute(
                select(SeoContextualLink).where(SeoContextualLink.status.in_(['APPROVED', 'REJECTED', 'applied', 'approved', 'rejected']))
            )).scalars().all()
            print(f"Total approved/rejected/applied links loaded: {len(links)}")
            for l in links:
                st = l.status if isinstance(l.status, str) else l.status.value
                print(f"Link ID: {l.id}")
                print(f"  Model status type: {type(l.status)}")
                print(f"  Model status value: {l.status!r}")
                print(f"  st: {st!r} (type: {type(st)})")
                print(f"  st == 'approved': {st == 'approved'}")
                print(f"  st == 'rejected': {st == 'rejected'}")
                print(f"  st == 'applied': {st == 'applied'}")
    finally:
        current_tenant_id.reset(token)

if __name__ == "__main__":
    asyncio.run(run())
