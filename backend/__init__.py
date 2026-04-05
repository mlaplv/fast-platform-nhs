import asyncio
import logging
import traceback
import sys
import warnings

# [CNS V8.5 NEURAL TRAP] - Elite Python 3.14 Compatibility Layer
# Elite V2.2: Mandatory Pydantic V1 Warning filter
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality")

# This hook captures exactly which library or module calls get_event_loop()
# during the boot sequence without a running loop.

logger = logging.getLogger("api-gateway")

def trinity_trap_get_event_loop():
    try:
        # Standard behavior: Try to get the running loop
        return _original_get_event_loop()
    except RuntimeError:
        # 🔗 [Neural Bridge] Automatic Loop Restoration (Python 3.14 Compatibility)
        # Instead of crashing, we restore the legacy behavior for third-party libraries (arq, etc.)
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # print(f"🔗 [Neural Bridge] Restored missing event loop for thread '{threading.current_thread().name}'", file=sys.stderr)
            return loop
        except Exception as e:
            print(f"💀 [Neural Bridge] Critical failure restoring loop: {e}", file=sys.stderr)
            raise

import threading
# Only patch if not already patched
if not hasattr(asyncio, "_trinity_trapped"):
    _original_get_event_loop = asyncio.get_event_loop
    asyncio.get_event_loop = trinity_trap_get_event_loop
    asyncio._trinity_trapped = True
    # logger.info("🛡️ [System] Neural Trap (Asyncio Hook) installed.")
