import os
import sys
import logging

# Elite V2.2: Import Debugger
print("DEBUG START")
os.environ["FAST_PLATFORM_TEST"] = "true"

def trace_import(module_name):
    print(f"DEBUG: Importing {module_name}...")
    __import__(module_name)
    print(f"DEBUG: {module_name} OK")

try:
    trace_import("backend.app_logging")
    from backend.app_logging import setup_logging
    setup_logging()
    
    trace_import("dotenv")
    trace_import("litestar")
    trace_import("backend.lifespan")
    trace_import("backend.database")
    trace_import("backend.routers.intent")
    # Add more as needed based on main.py imports
    trace_import("backend.controllers.client.pulse")
    trace_import("backend.controllers.admin_support_inbox")
    trace_import("backend.mcp.tools")
    
    print("DEBUG: Final import of app from main...")
    from backend.main import app
    print("DEBUG: APP IMPORTED SUCCESSFULLY")
except Exception as e:
    print(f"DEBUG ERROR: {e}")
    sys.exit(1)
