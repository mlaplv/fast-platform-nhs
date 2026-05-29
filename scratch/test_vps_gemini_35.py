import os
import json
import urllib.request

def load_keys():
    keys = []
    env_path = "/opt/fast-platform/.env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "SUPPORT_GEMINI_KEYS" in line:
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        raw = parts[1].strip().strip('"').strip("'")
                        try:
                            decoded = json.loads(raw)
                            if isinstance(decoded, list):
                                keys.extend([str(k).strip() for k in decoded])
                        except Exception:
                            clean = raw.strip("[]")
                            keys.extend([k.strip().strip('"').strip("'") for k in clean.split(",") if k.strip()])
    return keys

def test_model(key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": "Say OK"}]}]
    }
    data = json.dumps(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode())
            text = res["candidates"][0]["content"]["parts"][0]["text"].strip()
            return True, text
    except Exception as e:
        return False, str(e)

def main():
    keys = load_keys()
    if not keys:
        print("No keys found in VPS env!")
        return
    
    models = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.0-flash"]
    print("=== TESTING MODELS ON VPS ===")
    for model in models:
        print(f"\n--- Testing {model} ---")
        for idx, key in enumerate(keys):
            masked = key[:8] + "..." + key[-4:]
            ok, res = test_model(key, model)
            print(f"  Key #{idx+1} ({masked}): {'✅ SUCCESS' if ok else '❌ FAILED'} -> {res}")
            if ok:
                break

if __name__ == "__main__":
    main()
