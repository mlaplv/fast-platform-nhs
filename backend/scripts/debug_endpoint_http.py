import os
import sys
import hashlib
from pathlib import Path

project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
except ImportError:
    pass

import logging
logging.basicConfig(level=logging.INFO)

from litestar.testing import TestClient
from backend.main import app

def run_test():
    print("\n" + "="*50)
    print("TESTING ENDPOINT VIA LITESTAR TESTCLIENT")
    print("="*50)
    
    with TestClient(app=app) as client:
        # Step 1: Login to get token
        raw_password = "admin@123A3%@Xohii914!"
        hashed_password = hashlib.sha256(raw_password.encode()).hexdigest()
        
        login_payload = {
            "identifier": "mlap",
            "password": hashed_password
        }
        
        # Set Host header to admin.osmo.vn so it registers as admin login
        headers = {
            "Host": "admin.osmo.vn",
            "Content-Type": "application/json"
        }
        
        print("Logging in...")
        login_res = client.post("/api/v1/auth/login", json=login_payload, headers=headers)
        print(f"Login status: {login_res.status_code}")
        if login_res.status_code != 201:
            print(f"Login failed: {login_res.text}")
            return
            
        login_data = login_res.json()
        token = login_data.get("access_token")
        print(f"Got access token: {token[:15]}...")
        
        # Step 2: Make the title-suggest call
        suggest_headers = {
            "Host": "admin.osmo.vn",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        suggest_payload = {
            "category": "Mỹ phẩm",
            "keywords": "kem dưỡng cổ",
            "product_id": ""
        }
        
        print("Sending title suggest request...")
        res = client.post("/api/v1/articles/title-suggest", json=suggest_payload, headers=suggest_headers)
        print(f"Response status code: {res.status_code}")
        print("Response body:")
        import pprint
        try:
            pprint.pprint(res.json())
        except Exception:
            print(res.text)

if __name__ == "__main__":
    run_test()
