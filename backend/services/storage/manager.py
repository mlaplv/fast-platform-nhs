import os
import logging
from typing import Optional
from backend.services.storage.base import StorageProvider, LocalStorageProvider
from backend.services.storage.s3 import S3StorageProvider

logger = logging.getLogger("storage-manager")

class StorageManager:
    """
    V9.0 Multi-storage Orchestrator.
    Tự động điều phối việc lưu trữ giữa Local và Cloud (R2/S3).
    """
    _instance: Optional[StorageProvider] = None

    @classmethod
    def get_provider(cls) -> StorageProvider:
        if cls._instance is None:
            provider_type = os.getenv("STORAGE_PROVIDER", "local").lower()

            if provider_type == "s3" or provider_type == "r2":
                logger.info(f"[Storage] Initializing S3/R2 Provider (Bucket: {os.getenv('S3_BUCKET')})")
                cls._instance = S3StorageProvider(
                    bucket_name=os.getenv("S3_BUCKET", ""),
                    endpoint_url=os.getenv("S3_ENDPOINT", ""),
                    access_key=os.getenv("S3_ACCESS_KEY", ""),
                    secret_key=os.getenv("S3_SECRET_KEY", ""),
                    region=os.getenv("S3_REGION", "auto"),
                    public_url=os.getenv("S3_PUBLIC_URL")
                )
            else:
                logger.info("[Storage] Initializing Local Storage Provider")
                cls._instance = LocalStorageProvider()

        return cls._instance

# Singleton instance
storage = StorageManager.get_provider()
