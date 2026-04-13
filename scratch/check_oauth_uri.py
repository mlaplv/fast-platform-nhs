import os
import sys
from pathlib import Path

# Thêm backend vào path để load module
sys.path.insert(0, str(Path(__file__).parent))

# Load .env bằng tay để giả lập môi trường
from dotenv import load_dotenv
load_dotenv()

from backend.services.oauth_service import oauth2_service

print(f"DEBUG - API_URL: {os.getenv('API_URL')}")
print(f"DEBUG - FRONTEND_URL: {os.getenv('FRONTEND_URL')}")
print(f"DEBUG - Google Redirect URI: {oauth2_service._get_redirect_uri('google')}")
print(f"DEBUG - Facebook Redirect URI: {oauth2_service._get_redirect_uri('facebook')}")
