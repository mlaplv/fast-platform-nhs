import sys
import os

# Add the workspace to sys.path
sys.path.append("/home/lv/Desktop/fast-platform-core")

try:
    from backend.controllers.ads_protection import AdsProtectionController
    print("AdsProtectionController imported successfully")
except Exception as e:
    print(f"Failed to import AdsProtectionController: {e}")
    import traceback
    traceback.print_exc()

try:
    from backend.api.routes.ads_protection_router import ads_protection_router
    print("ads_protection_router imported successfully")
except Exception as e:
    print(f"Failed to import ads_protection_router: {e}")
    import traceback
    traceback.print_exc()
