import asyncio
import os
import sys
from pathlib import Path

# Setup project root
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.database import async_session_maker
from backend.database.models import User, Role

async def apply_roles_to_users():
    print("🚀 Applying Elite RBAC to existing users...")
    async with async_session_maker() as session:
        # 1. Fetch main roles
        stmt = select(Role).options(selectinload(Role.permissions))
        roles_res = await session.execute(stmt)
        roles = {r.code: r for r in roles_res.scalars().all()}
        
        if "SUPER_ADMIN" not in roles:
            print("❌ SUPER_ADMIN role not found. Please run seed_rbac_v2.py first.")
            return

        # 2. Fetch users
        stmt = select(User).options(selectinload(User.roles))
        users_res = await session.execute(stmt)
        users = users_res.scalars().all()
        
        print(f"🔍 Found {len(users)} users.")
        
        for user in users:
            print(f"- {user.email} | {user.username}")
            user_role_codes = [r.code for r in user.roles]
            
            # Elite Admin Detection
            is_admin = user.username in ["admin", "mlap"] or user.email in ["admin@micsmo.com", "boss@micsmo.com"]
            
            if is_admin:
                if "SUPER_ADMIN" not in user_role_codes:
                    print(f"✨ Assigning SUPER_ADMIN to {user.email}")
                    user.roles.append(roles["SUPER_ADMIN"])
                else:
                    print(f"✅ {user.email} already is SUPER_ADMIN")
            
            # Specialty Roles
            if user.email == "agent@micsmo.com" and "AI_TRAINER" not in user_role_codes:
                print(f"🤖 Assigning AI_TRAINER to {user.email}")
                user.roles.append(roles["AI_TRAINER"])
            
            if user.email == "lapmmlv@gmail.com" and "EDITOR" not in user_role_codes:
                print(f"📝 Assigning EDITOR to {user.email}")
                user.roles.append(roles["EDITOR"])

            # Default to CUSTOMER if no roles
            if not user.roles and "CUSTOMER" in roles:
                print(f"👤 Assigning CUSTOMER to {user.email}")
                user.roles.append(roles["CUSTOMER"])
        
        await session.commit()
        print("✅ Roles applied successfully.")

if __name__ == "__main__":
    asyncio.run(apply_roles_to_users())
