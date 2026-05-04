import hashlib
import json
import os

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

for k in keys:
    kid = hashlib.sha256(k.encode()).hexdigest()[:16]
    print(f"Key: {k[:8]}...{k[-4:]} ID: {kid}")
