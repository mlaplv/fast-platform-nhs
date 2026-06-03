import asyncio
from backend.database.alchemy_config import alchemy_config
from backend.database.models.system import Notification
from sqlalchemy import select, desc

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        stmt = select(Notification).order_by(desc(Notification.created_at)).limit(10)
        res = await session.execute(stmt)
        notifications = res.scalars().all()
        print(f"Total returned: {len(notifications)}")
        for n in notifications:
            print(f"ID: {n.id} | Type: {n.type} | Msg: {n.message} | CreatedAt: {n.created_at} | DeletedAt: {n.deleted_at}")

if __name__ == "__main__":
    asyncio.run(main())
