import asyncio
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.database.alchemy_config import alchemy_config
from backend.database.models import User, Role
from backend.services.auth_service import AuthService

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.email == "admin@micsmo.com")
        )
        user = (await db.execute(stmt)).scalar_one_or_none()
        if not user:
            print("Admin user not found!")
            return
            
        roles = [r.code for r in getattr(user, "roles", [])]
        permissions = []
        for r in getattr(user, "roles", []):
            permissions.extend([p.code for p in getattr(r, "permissions", [])])
        permissions = list(set(permissions))
        
        token_data = {
            "id": str(user.id),
            "sub": user.email,
            "roles": roles,
            "perms": permissions,
            "tenant_id": getattr(user, 'tenant_id', 'default'),
            "stamp": getattr(user, "security_stamp", "MISSING"),
            "name": user.name,
            "hpw": user.password is not None,
            "rem": True,
            "dfp": "browser-agent"
        }
        
        token = AuthService.create_access_token(
            data=token_data,
            expires_delta=timedelta(days=7)
        )
        with open("backend/scratch/token.txt", "w") as f:
            f.write(token)
        print("Token written to backend/scratch/token.txt successfully.")

if __name__ == "__main__":
    asyncio.run(main())
