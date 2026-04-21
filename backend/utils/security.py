import os
import base64
import logging
import secrets
import json
import hashlib
import socket
from typing import Union, TypeAlias
from urllib.parse import urlparse
import ipaddress

# Elite 2026: Cryptography (Rule R00 compliance)
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Elite 2026: Clear Type Definitions to avoid 'Any' (Rule R00)
EncryptedData: TypeAlias = Union[str, list[str]]

logger: logging.Logger = logging.getLogger("security-utility")

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
                result: object = json.loads(decrypted)
                
                # CNS V2.2: Explicit Type Safety — Ensure result is str or list[str]
                if isinstance(result, str):
                    return result
                if isinstance(result, list):
                    return [str(item) for item in result]
                
                return str(result)
            except (json.JSONDecodeError, ValueError):
                # Fallback for Legacy Era: Return raw string (Comma-separated or plain)
                logger.info("[GeminiSecurity] Legacy key cluster detected. Fallback to raw string.")
                return decrypted
        except Exception:
            # Fallback for Legacy Era: If decryption fails (e.g. data is plain text), 
            # return the original string to maintain reverse compatibility.
            return encrypted_str


def mask_pii(event_name: str, payload: dict[str, object]) -> dict[str, object]:
    """
    R82.33: Security Shield — Mask Personally Identifiable Information (PII) 
    in broadcast events to protect user privacy.
    (Elite V2.2: Fixed 'Any' to 'object' for strict typing).
    """
    if event_name == "ORDER_CREATED":
        p = dict(payload)
        
        # Mask phone: 094***1122
        phone = p.get("phone", "")
        if isinstance(phone, str) and len(phone) > 6:
            p["phone"] = f"{phone[:3]}***{phone[-4:]}"
        
        # Mask customer name: N*** A** Tuan
        name = p.get("customer", "")
        if isinstance(name, str) and name:
            parts = name.split()
            if len(parts) > 1:
                p["customer"] = f"{parts[0][0]}*** {parts[-1]}"
            else:
                p["customer"] = f"{name[0]}***"
        
        # Mask address: 123 Street... -> 123...
        addr = p.get("address", "")
        if isinstance(addr, str) and addr:
            p["address"] = f"{addr[:6]}..."
            
        # Remove IP and User Agent from broadcast
        p.pop("ip", None)
        p.pop("user_agent", None)
        return p
        
    return payload


def is_safe_url(url: str) -> bool:
    """
    R55.5: SSRF Protection — Validates URL and prevents access to private IP ranges.
    Returns True if the URL is considered safe (public), False otherwise.
    """
    if not url:
        return False

    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # 1. Block literal IP addresses in private ranges
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
                logger.warning(f"[Security] Blocked private IP access attempt: {hostname}")
                return False
        except ValueError:
            # Not an IP literal, continue to DNS resolution check
            pass

        # 2. DNS Resolution Check (Defense against DNS Rebinding)
        try:
            # Note: This is a basic check. In high-security production,
            # we should use a custom httpx resolver or bind to a specific interface.
            # For Fast Platform Core 2026, we enforce this check at the service level.
            ips = socket.getaddrinfo(hostname, None)
            for item in ips:
                addr = item[4][0]
                ip = ipaddress.ip_address(addr)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
                    logger.warning(f"[Security] Blocked access to hostname resolving to private IP: {hostname} ({addr})")
                    return False
        except socket.gaierror:
            # Hostname doesn't resolve, let the fetch attempt fail normally
            return True

        return True
    except Exception as e:
        logger.error(f"[Security] URL Safety Check Failed: {e}")
        return False
