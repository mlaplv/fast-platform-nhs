import urllib.request
import urllib.parse
import json

client_id = "913202366058-muava1de3urkont038afe1mmtuqtrg7g.apps.googleusercontent.com"
client_secret = "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"
refresh_token = "1//04DQfXSkWj9_dCgYIARAAGAQSNwF-L9IrvjczFXXx5EE-peguc7E6MhKV07MN_61vCPh4ZfEt5Kf3Hfykyl0BlnElYitnwSDFxrk"

print("TESTING WEB OAUTH CLIENT ID")
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
