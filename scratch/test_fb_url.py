import os
from urllib.parse import urlencode

def get_fb_url():
    client_id = "1454606482861271"
    redirect_uri = "https://api.micsmo.com/api/v1/auth/oauth/callback/facebook"
    state = "teststate123"
    
    # Test case 1: Space separated
    params_space = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": "public_profile email",
        "response_type": "code"
    }
    url_space = f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params_space)}"
    
    # Test case 2: Comma separated (Legacy/Some SDKs)
    params_comma = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": "public_profile,email",
        "response_type": "code"
    }
    url_comma = f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params_comma)}"
    
    return url_space, url_comma

if __name__ == "__main__":
    u1, u2 = get_fb_url()
    print(f"URL (Space): {u1}")
    print(f"URL (Comma): {u2}")
