import sys
import os
import logging

# Ensure root is in path
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("V61_Audit")

def audit():
    logger.info("=== STARTING V61.0 ARCHITECTURE AUDIT ===")
    
    errors = 0
    
    # 1. Check Constants
    path_constants = "backend/constants/agentic.py"
    if os.path.exists(path_constants):
        logger.info(f"✅ Path: {path_constants} found.")
    else:
        logger.error(f"❌ Path: {path_constants} MISSING.")
        errors += 1
        
    # 2. Check Registry
    path_registry = "backend/services/xohi/creative_studio/registry.py"
    if os.path.exists(path_registry):
        logger.info(f"✅ Path: {path_registry} found.")
    else:
        logger.error(f"❌ Path: {path_registry} MISSING.")
        errors += 1

    # 3. Check Shared Client
    path_client = "backend/utils/http_client.py"
    if os.path.exists(path_client):
        logger.info(f"✅ Path: {path_client} found.")
    else:
        logger.error(f"❌ Path: {path_client} MISSING.")
        errors += 1

    # 4. Logical Check (Regex scan for DI Registry usage in Orchestrator)
    path_orch = "backend/services/xohi/creative_studio/orchestrator.py"
    if os.path.exists(path_orch):
        with open(path_orch, 'r') as f:
            content = f.read()
            if "registry.register(" in content and "registry.get_operative(" in content:
                logger.info("✅ Orchestrator: DI Registry logic found (R107 Compliance).")
            else:
                logger.error("❌ Orchestrator: DI Registry logic MISSING.")
                errors += 1
    
    # 5. Check Pydantic Strict Mode
    path_schemas = "backend/services/xohi/creative_studio/models/schemas.py"
    if os.path.exists(path_schemas):
        with open(path_schemas, 'r') as f:
            if "strict=True" in f.read():
                logger.info("✅ Schemas: Pydantic strict=True found (R105 Compliance).")
            else:
                logger.error("❌ Schemas: Pydantic strict mode MISSING.")
                errors += 1

    if errors == 0:
        logger.info("🚀 AUDIT PASSED: System is V61.0 Compliant.")
        sys.exit(0)
    else:
        logger.error(f"💥 AUDIT FAILED: {errors} major violations found.")
        sys.exit(1)

if __name__ == "__main__":
    audit()
