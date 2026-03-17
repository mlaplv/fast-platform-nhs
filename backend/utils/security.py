import os
import base64
import logging
import secrets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger("api-gateway")

class GeminiSecurity:
    """
    R55.1: Hardened AES-GCM Encryption for 2026 Standards.
    Uses AES-GCM with PBKDF2-SHA256 (600k iterations).
    """
    _key = None

    @classmethod
    def _get_encryption_key(cls) -> bytes:
        if cls._key:
            return cls._key

        secret = os.getenv("SECRET_KEY", "XOHI_UNSAFE_DEV_SECRET_2026")
        if secret == "XOHI_UNSAFE_DEV_SECRET_2026":
            logger.warning("[Security] Using default SECRET_KEY. Keys are NOT secure in production!")

        # R55.1: Derived dynamic salt to avoid hardcoded constants
        # If SECURITY_SALT is missing, we use a hash of the secret to keep it deterministic but not hardcoded
        salt_env = os.getenv("SECURITY_SALT")
        if salt_env:
            salt = salt_env.encode()
        else:
            # Fallback: Deterministic salt derived from secret (better than hardcoded string)
            salt = hashes.Hash(hashes.SHA256())
            salt.update(secret.encode() + b"_xohi_pepper_2026")
            salt = salt.finalize()[:16]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000, # 2026 Standard (Hardened)
        )
        cls._key = kdf.derive(secret.encode())
        return cls._key

    @classmethod
    def encrypt_keys(cls, keys_list: list[str]) -> str:
        """Encrypts a list of keys using AES-GCM."""
        if not keys_list:
            return ""

        try:
            raw_data = ",".join(keys_list).encode()
            key = cls._get_encryption_key()
            aesgcm = AESGCM(key)
            nonce = secrets.token_bytes(12) # GCM standard nonce size
            ciphertext = aesgcm.encrypt(nonce, raw_data, None)

            # Combine nonce + ciphertext for storage
            return base64.urlsafe_b64encode(nonce + ciphertext).decode()
        except Exception as e:
            logger.error(f"[Security] Encryption Failed: {e}")
            return ""

    @classmethod
    def decrypt_keys(cls, encrypted_str: str) -> list[str]:
        """Decrypts the AES-GCM secure string with Legacy Fernet Fallback."""
        if not encrypted_str:
            return []

        # 1. Try modern AES-GCM
        try:
            data = base64.urlsafe_b64decode(encrypted_str.encode())
            nonce = data[:12]
            ciphertext = data[12:]

            key = cls._get_encryption_key()
            aesgcm = AESGCM(key)
            decrypted = aesgcm.decrypt(nonce, ciphertext, None).decode()

            return [k.strip() for k in decrypted.split(",") if k.strip()]
        except Exception:
            # 2. Legacy Fallback (Fernet, 100k iterations, hardcoded salt)
            try:
                secret = os.getenv("SECRET_KEY", "XOHI_UNSAFE_DEV_SECRET_2026")
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'xohi_salt_2026',
                    iterations=100000,
                )
                legacy_key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
                from cryptography.fernet import Fernet
                f = Fernet(legacy_key)
                decrypted = f.decrypt(encrypted_str.encode()).decode()

                logger.warning("[Security] Legacy Fernet key decrypted successfully. Please re-save settings to upgrade to AES-GCM 2026.")
                return [k.strip() for k in decrypted.split(",") if k.strip()]
            except Exception as e:
                logger.error(f"[Security] Decryption Failed (All Methods): {e}")
                return []
