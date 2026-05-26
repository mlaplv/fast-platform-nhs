import os
import urllib.request
import urllib.parse
import json
import sys

# Read client ID and secret from .env
env_vals = {}
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                v = v.strip()
                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                    v = v[1:-1]
                env_vals[k.strip()] = v

client_id = env_vals.get("GOOGLE_ADS_OAUTH_CLIENT_ID", "").strip()
client_secret = env_vals.get("GOOGLE_ADS_OAUTH_CLIENT_SECRET", "").strip()

if not client_id or not client_secret:
    print("❌ ERROR: Missing GOOGLE_ADS_OAUTH_CLIENT_ID or GOOGLE_ADS_OAUTH_CLIENT_SECRET in .env!")
    exit(1)

if len(sys.argv) < 2:
    print("❌ ERROR: Please provide the authorization code as an argument!")
    print("Usage: python3 exchange_code.py <YOUR_AUTHORIZATION_CODE>")
    exit(1)

code = sys.argv[1].strip()
redirect_uri = "https://developers.google.com/oauthplayground"

data = urllib.parse.urlencode({
    "code": code,
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": redirect_uri,
    "grant_type": "authorization_code",
}).encode("utf-8")

req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        print("\n" + "=" * 80)
        print("🎉 SUCCESS! YOUR NEW REFRESH TOKEN GENERATED:")
        print("=" * 80)
        print(f"GOOGLE_ADS_REFRESH_TOKEN={res['refresh_token']}")
        print("=" * 80)
        print("\n👉 Action Required: Copy this token and update it in your local and remote .env files!")
        print("👉 Then select Option 8 (RESTART API) in xohi.sh.")
        print("=" * 80)
except urllib.error.HTTPError as e:
    print("\n❌ HTTP ERROR:", e.code)
    print("RESPONSE BODY:", e.read().decode("utf-8"))
except Exception as e:
    print("\n❌ ERROR:", e)
