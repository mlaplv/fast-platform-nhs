"""
[ELITE V2.2] Core Database Config Registry
Synchronized dynamic read-only (Martial Law) helper.
Redundant engine/plugin declarations have been purged in favor of backend.database.alchemy_config.
"""

import os

def is_system_read_only() -> bool:
    """
    [THIẾT QUÂN LUẬT] Dynamic check for System Read-Only state.
    Checks both SYSTEM_READ_ONLY (runtime toggled) and MARTIAL_LAW_READ_ONLY (env set).
    """
    return (
        os.getenv("SYSTEM_READ_ONLY", "false").lower() == "true"
        or os.getenv("MARTIAL_LAW_READ_ONLY", "false").lower() == "true"
    )
