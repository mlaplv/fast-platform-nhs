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
key = keys[0]

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
resp = httpx.get(url)
print(json.dumps(resp.json(), indent=2))
