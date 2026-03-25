import asyncio
import os
import bcrypt
import hashlib
import sys
from sqlalchemy import select
from dotenv import load_dotenv

# Path setup
sys.path.insert(0, os.getcwd())

load_dotenv()

from backend.database import async_session_maker
from backend.database.models import User

async def verify_password(password: str) -> bool:
    """Xác thực mật khẩu admin đối với dữ liệu đã băm trong DB."""
    async with async_session_maker() as session:
        try:
            # Lấy user admin (user_admin là ID cố định từ seed)
            stmt = select(User).where(User.id == "user_admin")
            admin = (await session.execute(stmt)).scalar_one_or_none()
            
            if not admin:
                return False
                
            # Quy trình băm (Elite Strategy): SHA256 -> Bcrypt
            # Theo logic trong seed.py: 
            # hpwd = bcrypt.hashpw(hashlib.sha256(pwd.encode()).hexdigest().encode(), bcrypt.gensalt()).decode()
            
            pwd_sha = hashlib.sha256(password.encode()).hexdigest().encode()
            return bcrypt.checkpw(pwd_sha, admin.password.encode())
        except Exception:
            return False
    return False

async def main():
    if len(sys.argv) < 2:
        sys.exit(1)
        
    password = sys.argv[1]
    if await verify_password(password):
        print("MATCH")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
