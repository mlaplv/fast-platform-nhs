import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger("api-gateway")

class GeminiSecurity:
    """
    R55.0: Secure Encryption for Gemini API Keys.
    Uses AES-GCM (via Fernet) with a key derived from system SECRET_KEY.
    """
    _fernet = None

    @classmethod
    def _get_fernet(cls):
        if cls._fernet:
            return cls._fernet
        
        secret = os.getenv("SECRET_KEY", "XOHI_UNSAFE_DEV_SECRET_2026")
        if secret == "XOHI_UNSAFE_DEV_SECRET_2026":
            logger.warning("[Security] Using default SECRET_KEY. Keys are NOT secure in production!")
            
        salt = b'xohi_salt_2026' # Standard salt for key derivation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        cls._fernet = Fernet(key)
        return cls._fernet

    @classmethod
    def encrypt_keys(cls, keys_list: list[str]) -> str:
        """Encrypts a list of keys into a single secure string."""
        if not keys_list:
            return ""
        raw_data = ",".join(keys_list)
        f = cls._get_fernet()
        return f.encrypt(raw_data.encode()).decode()

    @classmethod
    def decrypt_keys(cls, encrypted_str: str) -> list[str]:
        """Decrypts the secure string back into a list of keys."""
        if not encrypted_str:
            return []
        try:
            f = cls._get_fernet()
            decrypted = f.decrypt(encrypted_str.encode()).decode()
            return [k.strip() for k in decrypted.split(",") if k.strip()]
        except Exception as e:
            logger.error(f"[Security] Decryption Failed: {e}")
            return []
