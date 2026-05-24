import os
import sys
import gc
import psutil
import time

def get_ram():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

print(f"Start: {get_ram():.2f} MB")

modules_to_import = [
    ("litestar", "import litestar"),
    ("sqlalchemy", "import sqlalchemy"),
    ("backend.database", "from backend.database import alchemy_config"),
    ("fastembed", "from fastembed import TextEmbedding"),
    ("backend.services.ai_engine.core.encoder_singleton", "from backend.services.ai_engine.core.encoder_singleton import warmup_encoder"),
    ("backend.services.ai_engine.core.trinity_bridge", "from backend.services.ai_engine.core.trinity_bridge import trinity_bridge"),
    ("backend.main", "import backend.main"),
]

for name, cmd in modules_to_import:
    t0 = time.time()
    ram_before = get_ram()
    exec(cmd)
    gc.collect()
    ram_after = get_ram()
    dt = time.time() - t0
    print(f"Import {name:50} -> RAM: {ram_after:.2f} MB (+{ram_after - ram_before:.2f} MB) in {dt:.3f}s")

# Let's call trinity_bridge.initialize()
print("\nRunning trinity_bridge.initialize()...")
t0 = time.time()
ram_before = get_ram()
import asyncio
async def init_trinity():
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    await trinity_bridge.initialize()
asyncio.run(init_trinity())
gc.collect()
ram_after = get_ram()
print(f"After trinity_bridge.initialize() -> RAM: {ram_after:.2f} MB (+{ram_after - ram_before:.2f} MB) in {time.time() - t0:.3f}s")

# Let's call warmup_encoder()
print("\nRunning warmup_encoder()...")
t0 = time.time()
ram_before = get_ram()
async def init_encoder():
    from backend.services.ai_engine.core.encoder_singleton import warmup_encoder
    await warmup_encoder()
asyncio.run(init_encoder())
gc.collect()
ram_after = get_ram()
print(f"After warmup_encoder() -> RAM: {ram_after:.2f} MB (+{ram_after - ram_before:.2f} MB) in {time.time() - t0:.3f}s")

print(f"\nFinal Total RAM: {get_ram():.2f} MB")
