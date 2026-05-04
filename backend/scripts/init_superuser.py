import os
import sys
import asyncio
import bcrypt
import hashlib
import uuid
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from dotenv import load_dotenv

# Ensure project root is in sys.path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment
load_dotenv(os.path.join(project_root, ".env"))

from backend.database import async_session_maker
from backend.database.models import User, Role, Permission, VoiceProfile
from backend.utils.security import GeminiSecurity

TENANT_ID = "smartshop"

def get_env_gemini_keys() -> list[str]:
    raw = os.getenv("SUPPORT_GEMINI_KEYS", "[]")
    try:
        import json
        keys = json.loads(raw)
        return [k.strip() for k in keys if k.strip()]
    except:
        return [k.strip() for k in raw.split(",") if k.strip()]

GEMINI_KEYS = get_env_gemini_keys()

async def init_superuser():
    print("🚀 Initializing Superuser (Elite 2026 Admin)...")
    
    async with async_session_maker() as session:
        try:
            # 1. Ensure Permissions exist
            print("🔐 Checking Permissions...")
            perms = {}
            perm_defs = [
                ("Full Access", "system:all"),
                ("Product Read", "product:read"),
                ("Product Write", "product:write"),
                ("Order Read", "order:read"),
                ("Order Write", "order:write")
            ]
            for name, code in perm_defs:
                stmt = select(Permission).where(Permission.code == code)
                p = (await session.execute(stmt)).scalar_one_or_none()
                if not p:
                    p = Permission(
                        id=f"perm_{code.replace(':', '_')}",
                        name=name,
                        code=code
                    )
                    session.add(p)
                    print(f"   + Created Permission: {code}")
                perms[code] = p
            await session.flush()

            # 2. Ensure SUPER_ADMIN Role exists
            print("🛡️ Checking SUPER_ADMIN Role...")
            stmt = select(Role).where(Role.code == "SUPER_ADMIN").options(selectinload(Role.permissions))
            s_role = (await session.execute(stmt)).scalar_one_or_none()
            if not s_role:
                s_role = Role(
                    id="role_superadmin",
                    name="Super Admin",
                    code="SUPER_ADMIN",
                    tenant_id=TENANT_ID,
                    permissions=list(perms.values())
                )
                session.add(s_role)
                print("   + Created Role: SUPER_ADMIN")
            else:
                s_role.permissions = list(perms.values())
            await session.flush()

            # 3. Ensure Admin User exists
            print("👤 Checking Admin User...")
            admin_email = os.getenv("ADMIN_EMAIL", "admin@osmo")
            admin_username = os.getenv("ADMIN_USERNAME", "admin")
            admin_pwd = os.getenv("ADMIN_PASSWORD", "admin@123A3%StrongPassword")
            
            stmt = select(User).where(User.email == admin_email).options(selectinload(User.roles))
            admin = (await session.execute(stmt)).scalar_one_or_none()
            
            if not admin:
                # Hash password using app-standard bcrypt over sha256
                hpwd = bcrypt.hashpw(
                    hashlib.sha256(admin_pwd.encode()).hexdigest().encode(),
                    bcrypt.gensalt()
                ).decode()
                
                admin = User(
                    id="user_admin",
                    email=admin_email,
                    username=admin_username,
                    name="osmo Admin",
                    password=hpwd,
                    status="ACTIVE",
                    tenant_id=TENANT_ID
                )
                admin.roles.append(s_role)
                session.add(admin)
                print(f"   + Created Admin User: {admin_email}")
            else:
                if s_role.id not in [r.id for r in admin.roles]:
                    admin.roles.append(s_role)
                    print(f"   + Assigned SUPER_ADMIN role to existing user: {admin_email}")
            await session.flush()

            # 4. Ensure VoiceProfile for Admin
            print("🎙️ Checking Admin Voice Profile...")
            stmt = select(VoiceProfile).where(VoiceProfile.user_id == admin.id)
            vp = (await session.execute(stmt)).scalar_one_or_none()
            if not vp:
                vp = VoiceProfile(
                    id=str(uuid.uuid4()),
                    user_id=admin.id,
                    wake_words=["hey so hi"],
                    sleep_words=["cút"],
                    greeting_template="Bố đây.",
                    capabilities={"READ":True, "COUNT":True, "MUTATE":True, "ANALYZE":True},
                    gemini_keys_enc=GeminiSecurity.encrypt(GEMINI_KEYS),
                    primary_model="gemini-1.5-pro",
                    ai_models=["gemini-1.5-flash"]
                )
                session.add(vp)
                print("   + Created Voice Profile for Admin")
            
            await session.commit()
            print("✨ Superuser Initialization Complete!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(init_superuser())
