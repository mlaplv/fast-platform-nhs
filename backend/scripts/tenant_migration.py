
import asyncio
import json
import logging
import os
from sqlalchemy import text
from backend.database.alchemy_config import alchemy_config

# Elite V2.2: Dynamic Tenant Migration Engine
# SSOT: APP_DOMAIN from environment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tenant-migration")

async def migrate():
    new_tenant = os.getenv("APP_DOMAIN", "osmo.vn").lower().replace("https://", "").replace("http://", "").rstrip("/")
    
    logger.info(f"🚀 Starting Tenant Migration to: {new_tenant}")
    
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        # 1. Get all tables with tenant_id column
        res = await db.execute(text(
            "SELECT table_name FROM information_schema.columns "
            "WHERE column_name = 'tenant_id' AND table_schema = 'public';"
        ))
        tables = [row[0] for row in res.fetchall()]
        
        # 2. Identify potential old tenants (anything that is NOT the current domain)
        # We also include some common defaults just in case
        res_old = await db.execute(text("SELECT DISTINCT tenant_id FROM product_bases"))
        old_tenants = [row[0] for row in res_old.fetchall() if row[0] != new_tenant]
        
        # Always add 'default' and 'smartshop' to candidates
        for t in ['default', 'osmo.vn', 'osmo']:
            if t != new_tenant and t not in old_tenants:
                old_tenants.append(t)
        
        if not old_tenants:
            logger.info("✅ No old tenants found to migrate. System is already synced.")
            return

        logger.info(f"📦 Found {len(tables)} tables and {len(old_tenants)} candidate old tenants: {old_tenants}")
        
        total_updates = 0
        for table in tables:
            for old in old_tenants:
                stmt = text(f"UPDATE {table} SET tenant_id = :new WHERE tenant_id = :old")
                result = await db.execute(stmt, {"new": new_tenant, "old": old})
                if result.rowcount > 0:
                    logger.info(f"    ✅ Updated {result.rowcount} rows in {table} ({old} -> {new_tenant})")
                    total_updates += result.rowcount
        
        # 3. Branding replacement in system_settings
        logger.info("⚙️ Updating system_settings branding...")
        branding_updates = [
            ("micsmo.com", new_tenant),
            ("micsmo", new_tenant),
            ("Micsmo", new_tenant),
            ("smartshop.test", new_tenant)
        ]
        
        for old_str, new_str in branding_updates:
            if old_str == new_str: continue
            stmt = text("UPDATE system_settings SET value = replace(value::text, :old, :new)::json")
            result = await db.execute(stmt, {"old": old_str, "new": new_str})
            if result.rowcount > 0:
                logger.info(f"    ✅ Replaced '{old_str}' with '{new_str}' in system_settings.")

        await db.commit()
        logger.info(f"✨ Migration Finished! Total rows updated: {total_updates}")

if __name__ == "__main__":
    asyncio.run(migrate())
