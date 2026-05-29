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
                            # Fallback comma separated
                            clean = raw.strip("[]")
                            keys.extend([k.strip().strip('"').strip("'") for k in clean.split(",") if k.strip()])
    return keys

def list_models(key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    try:
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode())
            return [m["name"].replace("models/", "") for m in res.get("models", [])]
    except Exception as e:
        return str(e)

def main():
    keys = load_keys()
    if not keys:
        print("No keys found in VPS env!")
        return
    print(f"Loaded {len(keys)} keys from VPS env.")
    for idx, key in enumerate(keys):
        masked = key[:8] + "..." + key[-4:]
        print(f"\n--- Testing Key #{idx+1} ({masked}) ---")
        models = list_models(key)
        if isinstance(models, list):
            print(f"Found {len(models)} models:")
            for m in sorted(models):
                print(f"  - {m}")
            break # Just need one working key to list models
        else:
            print(f"Error: {models}")

if __name__ == "__main__":
    main()
