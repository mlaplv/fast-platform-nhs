import os
import sys
import asyncio

# Add project root to sys.path
sys.path.append(os.getcwd())

# Load .env manually
def load_env():
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key] = value.strip("'").strip('"')

load_env()

# CRITICAL: Set DATABASE_URL and REDIS_URL to use localhost BEFORE ANY IMPORTS
if "DATABASE_URL" in os.environ:
    os.environ["DATABASE_URL"] = os.environ["DATABASE_URL"].replace("@db:", "@localhost:")
if "REDIS_URL" in os.environ:
    os.environ["REDIS_URL"] = os.environ["REDIS_URL"].replace("//redis:", "//localhost:")
else:
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"

async def verify():
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    
    print("Initializing Trinity Bridge...")
    await trinity_bridge.initialize()
    
    print(f"Default model: {trinity_bridge.default_model_name}")
    print(f"Discovered models: {trinity_bridge.discovered[:5]}")
    
    # Simulate building a chain
    models = await trinity_bridge.models_helper.build_chain(None, trinity_bridge.db_primary_model, trinity_bridge.db_waterfall, trinity_bridge.discovered)
    print(f"Model Chain: {models[:5]}")

if __name__ == "__main__":
    asyncio.run(verify())
