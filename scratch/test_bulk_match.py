import os
import asyncio
import sys

sys.path.insert(0, "/opt/fast-platform")

# Load environment variables from /opt/fast-platform/.env
if os.path.exists("/opt/fast-platform/.env"):
    with open("/opt/fast-platform/.env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                # Strip quotes if present
                if v.startswith('"') and v.endswith('"'):
                    v = v[1:-1]
                if v.startswith("'") and v.endswith("'"):
                    v = v[1:-1]
                os.environ[k] = v

# Override DATABASE_URL and REDIS_URL to connect from VPS host to localhost mapping
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.database import current_tenant_id
from backend.services.seo_matching_service import SeoMatchingService
from backend.services.ai_engine.core.key_rotator import key_rotator

async def main():
    # Set the tenant context so the query filters by osmo.vn
    current_tenant_id.set("osmo.vn")
    
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Load keys from database/env rotation pool
        await key_rotator.load_keys()
        print(f"Loaded {key_rotator.get_count()} Gemini keys into key_rotator.")
        
        service = SeoMatchingService()
        try:
            print("Running bulk AI matching on VPS with key rotator ready...")
            result = await service.bulk_match_unclassified(session)
            print("Bulk matching result:")
            print(result)
        except Exception as e:
            print("Error running bulk matching:")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
