import os
import urllib.request
import urllib.parse
import json

# Try to read .env manually
env_vals = {}
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                # Strip quotes if present
                v = v.strip()
                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                    v = v[1:-1]
                env_vals[k.strip()] = v

client_id = env_vals.get("GOOGLE_ADS_OAUTH_CLIENT_ID", "").strip()
client_secret = env_vals.get("GOOGLE_ADS_OAUTH_CLIENT_SECRET", "").strip()
refresh_token = env_vals.get("GOOGLE_ADS_REFRESH_TOKEN", "").strip()

print("CLIENT ID:", repr(client_id))
print("CLIENT SECRET:", repr(client_secret))
print("REFRESH TOKEN:", repr(refresh_token))

data = urllib.parse.urlencode({
    "client_id": client_id,
    "client_secret": client_secret,
    "refresh_token": refresh_token,
    "grant_type": "refresh_token",
}).encode("utf-8")

req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        print("STATUS: 200")
        print("RESPONSE:", res)
except urllib.error.HTTPError as e:
    print("STATUS:", e.code)
    print("RESPONSE BODY:", e.read().decode("utf-8"))
except Exception as e:
    print("ERROR:", e)
