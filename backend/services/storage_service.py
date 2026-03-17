import os
import shutil
import boto3
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger("storage-service")

class StorageProvider(ABC):
    @abstractmethod
    async def upload(self, local_path: str, remote_path: str) -> str:
        """Upload file và trả về public URL hoặc đường dẫn lưu trữ."""
        pass

    @abstractmethod
    async def delete(self, remote_path: str) -> bool:
        """Xóa file khỏi bộ nhớ."""
        pass

    @abstractmethod
    async def exists(self, remote_path: str) -> bool:
        """Kiểm tra file tồn tại."""
        pass

    @abstractmethod
    def get_url(self, remote_path: str) -> str:
        """Trả về URL truy cập file."""
        pass

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = "frontend/static"):
        self.base_dir = base_dir

    async def upload(self, local_path: str, remote_path: str) -> str:
        dest_path = os.path.join(self.base_dir, remote_path.lstrip("/"))
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(local_path, dest_path)
        return f"/{remote_path.lstrip('/')}"

    async def delete(self, remote_path: str) -> bool:
        full_path = os.path.join(self.base_dir, remote_path.lstrip("/"))
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    async def exists(self, remote_path: str) -> bool:
        full_path = os.path.join(self.base_dir, remote_path.lstrip("/"))
        return os.path.exists(full_path)

    def get_url(self, remote_path: str) -> str:
        return f"/{remote_path.lstrip('/')}"

class S3StorageProvider(StorageProvider):
    def __init__(
        self,
        bucket_name: str,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region: str = "auto",
        public_url: Optional[str] = None
    ):
        self.bucket_name = bucket_name
        self.public_url = public_url or endpoint_url
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

    async def upload(self, local_path: str, remote_path: str) -> str:
        remote_path = remote_path.lstrip("/")
        try:
            await asyncio.to_thread(
                self.s3_client.upload_file,
                local_path,
                self.bucket_name,
                remote_path,
                ExtraArgs={"ACL": "public-read"}
            )
            return self.get_url(remote_path)
        except Exception as e:
            logger.error(f"[S3Storage] Upload failed: {e}")
            raise

    async def delete(self, remote_path: str) -> bool:
        remote_path = remote_path.lstrip("/")
        try:
            await asyncio.to_thread(
                self.s3_client.delete_object,
                Bucket=self.bucket_name,
                Key=remote_path
            )
            return True
        except Exception as e:
            logger.error(f"[S3Storage] Delete failed: {e}")
            return False

    async def exists(self, remote_path: str) -> bool:
        remote_path = remote_path.lstrip("/")
        try:
            await asyncio.to_thread(
                self.s3_client.head_object,
                Bucket=self.bucket_name,
                Key=remote_path
            )
            return True
        except:
            return False

    def get_url(self, remote_path: str) -> str:
        return f"{self.public_url.rstrip('/')}/{remote_path.lstrip('/')}"

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
