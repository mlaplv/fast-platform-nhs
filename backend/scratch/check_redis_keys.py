import asyncio
import os
import sys
import hashlib

# Load .env file manually
def load_env():
    env_path = "/media/lv/data/fast-platform-core/.env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        os.environ[key] = val

load_env()

sys.path.append("/media/lv/data/fast-platform-core")

import redis.asyncio as redis

BLACKLIST_PREFIX = "ai:key:v70:black:"
METADATA_PREFIX = "ai:key:v70:meta:"
MODEL_DAILY_PREFIX = "ai:key:v70:daily:"

def _get_key_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

async def main():
    import json
    support_keys_raw = os.getenv("SUPPORT_GEMINI_KEYS")
    if not support_keys_raw:
        print("No SUPPORT_GEMINI_KEYS in env!")
        return
    
    # Clean raw string
    support_keys_raw = support_keys_raw.strip()
    if (support_keys_raw.startswith("'") and support_keys_raw.endswith("'")) or (support_keys_raw.startswith('"') and support_keys_raw.endswith('"')):
        support_keys_raw = support_keys_raw[1:-1].strip()
    
    keys = json.loads(support_keys_raw)
    
    client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
    
    print("--- REDIS KEY STATUS ---")
    for k in keys:
        kid = _get_key_id(k)
        is_blacklisted = await client.get(f"{BLACKLIST_PREFIX}{kid}")
        meta = await client.hgetall(f"{METADATA_PREFIX}{kid}")
        print(f"Key hash: {kid}")
        print(f"  Blacklisted: {is_blacklisted}")
        print(f"  Meta: {meta}")
        
        # Check daily exhausted for models
        # Scan for MODEL_DAILY_PREFIX + kid + :*
        keys_found = []
        cur = 0
        while True:
            cur, val = await client.scan(cursor=cur, match=f"{MODEL_DAILY_PREFIX}{kid}:*")
            keys_found.extend(val)
            if cur == 0:
                break
        if keys_found:
            print(f"  Daily Exhausted models:")
            for dk in keys_found:
                exp = await client.ttl(dk)
                print(f"    {dk.split(':')[-1]}: TTL={exp}s")

if __name__ == "__main__":
    asyncio.run(main())
