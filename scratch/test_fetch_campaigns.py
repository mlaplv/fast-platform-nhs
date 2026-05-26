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
                v = v.strip()
                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                    v = v[1:-1]
                env_vals[k.strip()] = v

client_id = env_vals.get("GOOGLE_ADS_OAUTH_CLIENT_ID", "").strip()
client_secret = env_vals.get("GOOGLE_ADS_OAUTH_CLIENT_SECRET", "").strip()
refresh_token = env_vals.get("GOOGLE_ADS_REFRESH_TOKEN", "").strip()
developer_token = env_vals.get("GOOGLE_ADS_DEVELOPER_TOKEN", "").strip()
customer_id = env_vals.get("GOOGLE_ADS_CUSTOMER_ID", "").strip()
login_customer_id = env_vals.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").strip()

# Strip non-digits from customer IDs
customer_id = "".join(filter(str.isdigit, customer_id))
login_customer_id = "".join(filter(str.isdigit, login_customer_id))

print("CUSTOMER ID:", customer_id)
print("LOGIN CUSTOMER ID:", login_customer_id)

# 1. Get access token
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
        access_token = res["access_token"]
        print("✅ Access token retrieved successfully!")
except Exception as e:
    print("❌ Failed to get access token:", e)
    exit(1)

# 2. Query campaigns
query = """
    SELECT
        campaign.resource_name,
        campaign.id,
        campaign.name,
        campaign.status
    FROM campaign
    WHERE campaign.status != 'REMOVED'
    LIMIT 50
"""

headers = {
    "Authorization": f"Bearer {access_token}",
    "developer-token": developer_token,
    "login-customer-id": login_customer_id,
    "Content-Type": "application/json"
}

url = f"https://googleads.googleapis.com/v24/customers/{customer_id}/googleAds:search"
req_search = urllib.request.Request(
    url,
    data=json.dumps({"query": query}).encode("utf-8"),
    headers=headers,
    method="POST"
)

try:
    with urllib.request.urlopen(req_search) as response:
        res = json.loads(response.read().decode("utf-8"))
        print("✅ Campaigns query successful!")
        print("RESPONSE:", json.dumps(res, indent=2))
except urllib.error.HTTPError as e:
    print("❌ HTTP Error:", e.code)
    print("RESPONSE BODY:", e.read().decode("utf-8"))
except Exception as e:
    print("❌ Error querying campaigns:", e)
