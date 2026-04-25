import os
import sys
import asyncio
from pathlib import Path

# Setup project root for imports
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.database import async_session_maker, engine
from backend.database.models import Role, Permission, Base
from backend.constants.permissions import PermissionEnum

# Resolve Tenant ID from environment
TENANT_ID = os.getenv("APP_DOMAIN", "micsmo.com")

async def seed_rbac_v2():
    print(f"🔐 Starting Elite RBAC V2.2 Seeding for Tenant: {TENANT_ID}...")
    
    # 0. Ensure Tables Exist (For fresh initialization)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_maker() as session:
        try:
            # 1. Sync All Permissions from Enum
            all_codes = PermissionEnum.all_codes()
            existing_perms_res = await session.execute(select(Permission))
            existing_perms = {p.code: p for p in existing_perms_res.scalars().all()}
            
            new_perms_count = 0
            for code in all_codes:
                if code not in existing_perms:
                    # Generate a human-friendly name from the code (e.g., "category:write" -> "Category Write")
                    parts = code.split(":")
                    name = " ".join([p.capitalize() for p in parts])
                    
                    p = Permission(
                        id=f"perm_{code.replace(':', '_')}",
                        name=name,
                        code=code
                    )
                    session.add(p)
                    existing_perms[code] = p
                    new_perms_count += 1
            
            await session.flush()
            print(f"✅ Added {new_perms_count} new permissions. Total: {len(existing_perms)}")

            # 2. Update/Create Roles
            roles_to_seed = [
                {
                    "id": "role_superadmin",
                    "code": "SUPER_ADMIN",
                    "name": "Super Admin",
                    "perms": all_codes # Everything
                },
                {
                    "id": "role_manager",
                    "code": "MANAGER",
                    "name": "Store Manager",
                    "perms": ["product:read", "product:write", "order:read", "order:write", "category:read", "category:write", "media:read"]
                },
                {
                    "id": "role_editor",
                    "code": "EDITOR",
                    "name": "Content Editor",
                    "perms": ["content:read", "content:write", "content:publish", "media:read", "media:write"]
                },
                {
                    "id": "role_ai_trainer",
                    "code": "AI_TRAINER",
                    "name": "AI Specialist",
                    "perms": ["ai:train", "ai:config", "sys:admin"]
                },
                {
                    "id": "role_customer",
                    "code": "CUSTOMER",
                    "name": "Customer",
                    "perms": ["product:read", "order:read"]
                }
            ]

            for r_def in roles_to_seed:
                # Check if role exists
                stmt = select(Role).where((Role.code == r_def["code"]) & (Role.tenant_id == TENANT_ID)).options(selectinload(Role.permissions))
                existing_role = (await session.execute(stmt)).scalar_one_or_none()
                
                role_perms = [existing_perms[code] for code in r_def["perms"] if code in existing_perms]
                
                if existing_role:
                    print(f"🔄 Updating Role: {r_def['code']}")
                    existing_role.permissions = role_perms
                else:
                    print(f"✨ Creating Role: {r_def['code']}")
                    new_role = Role(
                        id=r_def["id"] if not r_def["id"].startswith("role_") else f"{r_def['id']}_{TENANT_ID.replace('.', '_')}",
                        code=r_def["code"],
                        name=r_def["name"],
                        tenant_id=TENANT_ID,
                        permissions=role_perms
                    )
                    session.add(new_role)
            
            await session.commit()
            print("🚀 Elite RBAC V2.2 Synchronization Successful!")
            
        except Exception as e:
            print(f"❌ Error during RBAC seed: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed_rbac_v2())
