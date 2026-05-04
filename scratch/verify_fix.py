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

# CRITICAL: Set DATABASE_URL to use localhost
if "DATABASE_URL" in os.environ:
    os.environ["DATABASE_URL"] = os.environ["DATABASE_URL"].replace("@db:", "@localhost:")

async def verify():
    from backend.services.ai_engine.core.key_rotator import key_rotator
    
    print("Pre-load count:", len(key_rotator.keys))
    await key_rotator.load_keys()
    print("Post-load count:", len(key_rotator.keys))
    
    for i, k in enumerate(key_rotator.keys):
        print(f"Key #{i}: {k[:8]}...{k[-4:]} (len={len(k)})")

if __name__ == "__main__":
    asyncio.run(verify())
