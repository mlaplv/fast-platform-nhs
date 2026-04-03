import os
import base64
import logging
import secrets
import json
import hashlib
from typing import Union, TypeAlias
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Elite 2026: Clear Type Definitions to avoid 'Any' (Rule R00)
EncryptedData: TypeAlias = Union[str, list[str]]

logger: logging.Logger = logging.getLogger("api-gateway")

class GeminiSecurity:
    """
    R55.4: Unified Elite 2026 Security Standard.
    Uses AES-GCM with PBKDF2-SHA256 (600k iterations) and JSON serialization.
    """
    _key: bytes | None = None

    @classmethod
    def _get_encryption_key(cls) -> bytes:
        """Standard Primary Key from SECURITY_SALT."""
        if cls._key is not None:
            return cls._key

        secret: str = os.getenv("SECRET_KEY", "XOHI_UNSAFE_DEV_SECRET_2026")
        salt_env: str | None = os.getenv("SECURITY_SALT")
        
        # Elite 2026: SECURITY_SALT is MANDATORY for production stability.
        # Fallback for dev only (deterministic based on secret)
        effective_salt: str = salt_env if salt_env else hashlib.sha256(secret.encode()).hexdigest()[:16]

        if not salt_env and os.getenv("ENV") == "production":
            logger.error("[Security] CRITICAL: SECURITY_SALT is missing in production!")

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=effective_salt.encode(),
            iterations=600000, 
        )
        cls._key = kdf.derive(secret.encode())
        return cls._key

    @classmethod
    def encrypt(cls, data: EncryptedData | None) -> str:
        """
        Unified Encryption: Serializes to JSON -> AES-GCM.
        Handles both single strings and lists of keys naturally.
        """
        if data is None:
            return ""

        try:
            # Standardize on JSON to avoid comma-split bugs
            raw_data: bytes = json.dumps(data).encode()
            key: bytes = cls._get_encryption_key()
            aesgcm = AESGCM(key)
            nonce: bytes = secrets.token_bytes(12)
            ciphertext: bytes = aesgcm.encrypt(nonce, raw_data, None)

            return base64.urlsafe_b64encode(nonce + ciphertext).decode()
        except Exception as e:
            logger.error(f"[Security] Unified Encryption Failed: {e}")
            return ""

    @classmethod
    def decrypt(cls, encrypted_str: str) -> EncryptedData | None:
        """
        Unified Decryption: AES-GCM -> JSON Parse.
        """
        if not encrypted_str:
            return None

        try:
            raw_input: bytes = encrypted_str.encode()
            data: bytes = base64.urlsafe_b64decode(raw_input)
            nonce: bytes = data[:12]
            ciphertext: bytes = data[12:]

            aesgcm = AESGCM(cls._get_encryption_key())
            decrypted: str = aesgcm.decrypt(nonce, ciphertext, None).decode()
            
            try:
                # V2026: Try JSON decoding (Standard)
                return json.loads(decrypted)
            except:
                # Fallback for Legacy Era: Return raw string (Comma-separated)
                logger.info("[GeminiSecurity] Legacy key cluster detected. Fallback to raw string.")
                return decrypted
        except Exception as e:
            logger.error(f"[Security] AES-GCM Decryption Failed (Wrong Salt?): {e}")
            return None

