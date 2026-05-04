import os
import sys
import base64
import json
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Set the keys exactly as in .env
os.environ["SECRET_KEY"] = "6e2cb5f398a7844d00c9bd047349281f150616640e2284f6c941b68070b0a75c"
os.environ["SECURITY_SALT"] = "osmo_elite_2026_salt_stable"

def get_key():
    secret = os.environ["SECRET_KEY"]
    salt = os.environ["SECURITY_SALT"]
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt.encode(), iterations=600000)
    return kdf.derive(secret.encode())

def decrypt(enc):
    try:
        data = base64.urlsafe_b64decode(enc.encode())
        nonce = data[:12]
        ciphertext = data[12:]
        aesgcm = AESGCM(get_key())
        decrypted = aesgcm.decrypt(nonce, ciphertext, None).decode()
        return decrypted
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"

# The string from DB
enc_str = "HX7VJFrITcdcAlvFnaSdrRHz3OOyJT_tHPrNQ9B6FVNpFJ-CS8oZNRWVMCJVhMPTqCFzqzmwfKl-RcBO2nqaPAxRs0l6QWdy1SeaOcwiLx4X2oVrkVj_Lpf4cILlPnKJd80hZKC5Ij2bTCg491MSS9AqVVYVct6vE3TBsTYdrcYxuVZ8y4wKqkV1A66PhsZzk6i6eJZ1bAiMiV2ucxi0nC9dmu8VS_n7cNPibHdj_o2VbiCQd40vmfBFSdpV1HZS8Z-QuyMnxvBNEkgeneTBnBSvQ6VEczAB_tKWW_AMUpOCO3frSzvKOAcaCL4dTBKNhS8nQK8VmvO2HAQFA1OHJek9wg6vcTETX-9rc_ISR-9Ds5vlYSt3d4k754XTu43FNQa3_zj203Fo0TNTF_vSqHevKFlYGFMPz6DbJI5QV7Xc5NA99ceTXQGIrlMEN4RhhlVVUK0_VsTeBVdGNasKlIlWDOYH-XowE6LgdxVuKxvZfhm7"

print(f"Result: {decrypt(enc_str)}")
