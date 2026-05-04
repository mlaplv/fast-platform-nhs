import os
import json
import httpx

def load_env():
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key] = value.strip("'").strip('"')

load_env()

keys_raw = os.getenv("SUPPORT_GEMINI_KEYS", "[]")
keys = json.loads(keys_raw)

if not keys:
    print("No keys in .env")
    exit()

key = keys[0]
model = "gemini-1.5-flash"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

resp = httpx.post(url, json={"contents": [{"parts":[{"text": "ping"}]}]})
print(f"Status: {resp.status_code}")
print(f"Body: {resp.text}")
