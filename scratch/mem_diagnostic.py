import os
import sys
import gc
import psutil
import logging

def get_process_memory():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

print("="*60)
print("🧠 MEMORY DIAGNOSTIC FOR CONTAINER API")
print("="*60)
print(f"PID: {os.getpid()}")
print(f"Current RAM (RSS): {get_process_memory():.2f} MB")

# Force Garbage Collection
gc.collect()
print(f"RAM after gc.collect(): {get_process_memory():.2f} MB")

# Check imported modules
print("\n📦 Top imported modules:")
imported_modules = {}
for name, val in sys.modules.items():
    if val is not None:
        try:
            # Estimate size
            size = sys.getsizeof(val)
            imported_modules[name] = size
        except:
            pass

sorted_modules = sorted(imported_modules.items(), key=lambda x: x[1], reverse=True)
for name, size in sorted_modules[:30]:
    print(f" - {name}: {size} bytes")

print("\n🤖 Checking FastEmbed Singleton...")
try:
    from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder, CACHE_DIR
    encoder = get_shared_encoder()
    if encoder is not None:
        print(f"✅ FastEmbed is loaded in memory! Cache dir: {CACHE_DIR}")
        print(f"Model: {encoder.model_name}")
    else:
        print("❌ FastEmbed is NOT loaded in memory!")
except Exception as e:
    print(f"⚠️ Error checking FastEmbed: {e}")

print("\n🔌 Checking SQL Alchemy pool status...")
try:
    from backend.database import alchemy_config
    engine = alchemy_config.engine
    print(f"Pool size: {engine.pool.size()}")
    print(f"Checked in connections: {engine.pool.checkedin()}")
    print(f"Checked out connections: {engine.pool.checkedout()}")
    print(f"Overflow: {engine.pool.overflow()}")
except Exception as e:
    print(f"⚠️ Error checking SQLAlchemy: {e}")

print("="*60)
