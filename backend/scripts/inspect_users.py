import os
import sys
import asyncio
from pathlib import Path
from sqlalchemy import text

# Add project root to python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
except ImportError:
    pass

from backend.database import async_session_maker

async def main():
    async with async_session_maker() as session:
        # Get users and their roles
        query = text("""
            SELECT u.id, u.username, u.email, u.name, u.phone, u.status, u.created_at,
                   STRING_AGG(r.code, ', ') as roles
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            GROUP BY u.id, u.username, u.email, u.name, u.phone, u.status, u.created_at
            ORDER BY u.created_at;
        """)
        
        result = await session.execute(query)
        users = result.fetchall()
        
        print(f"=== USERS LIST ({len(users)} users) ===")
        for u in users:
            print(f"ID: {u[0]} | User: {u[1]} | Email: {u[2]} | Phone: {u[4]} | Status: {u[5]} | Roles: {u[7] or 'None'}")

if __name__ == "__main__":
    asyncio.run(main())
