import os
import sys
import asyncio
import bcrypt
import hashlib
from pathlib import Path
from sqlalchemy import select

# Fix python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
except ImportError:
    pass

from backend.database import async_session_maker
from backend.database.models import User, Role

async def verify_admin(password: str):
    async with async_session_maker() as session:
        # Find users with SUPER_ADMIN role
        stmt = select(User).join(User.roles).where(Role.code == "SUPER_ADMIN")
        result = await session.execute(stmt)
        admins = result.scalars().all()
        
        if not admins:
            # Fallback to checking admin from .env if no DB user yet
            admin_pwd = os.getenv("ADMIN_PASSWORD")
            if admin_pwd and password == admin_pwd:
                print("MATCH")
                return True
        
        for admin in admins:
            # Check password using the standard hash
            if admin.password:
                try:
                    # Logic from init_superuser.py
                    if bcrypt.checkpw(
                        hashlib.sha256(password.encode()).hexdigest().encode(),
                        admin.password.encode()
                    ):
                        print("MATCH")
                        return True
                except:
                    continue
    
    print("NO_MATCH")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(verify_admin(sys.argv[1]))
    else:
        print("NO_MATCH")
