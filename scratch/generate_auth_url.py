import os
import urllib.parse

# Read client ID from .env
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

if not client_id:
    print("❌ ERROR: GOOGLE_ADS_OAUTH_CLIENT_ID not found in .env!")
    exit(1)

# Scope for Google Ads API
scope = "https://www.googleapis.com/auth/adwords"

# We will use OAuth Playground as redirect URI since it's whitelisted by default
# and extremely easy to use for manual token generation.
redirect_uri = "https://developers.google.com/oauthplayground"

params = {
    "client_id": client_id,
    "scope": scope,
    "access_type": "offline",
    "prompt": "consent",
    "response_type": "code",
    "redirect_uri": redirect_uri
}

auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

print("=" * 80)
print("🔑 GOOGLE ADS OAUTH2 REFRESH TOKEN GENERATOR (ELITE V2.2)")
print("=" * 80)
print("\n👉 STEP 1: Copy and open this URL in your web browser:")
print("-" * 80)
print(auth_url)
print("-" * 80)
print("\n👉 STEP 2: Log in and click 'Allow' / 'Tiếp tục'.")
print("👉 STEP 3: You will be redirected to OAuth Playground. Look at the browser address bar!")
print("   Copy the value of the 'code' parameter in the URL.")
print("   Example: https://developers.google.com/oauthplayground/?code=4/0AdQt8... -> Copy the '4/0AdQt8...' part.")
print("\n👉 STEP 4: Run exchange script to get your new Refresh Token!")
print("=" * 80)
