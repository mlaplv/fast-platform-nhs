import os
import boto3
import asyncio
import logging
from typing import Optional
from backend.services.storage.base import StorageProvider

logger = logging.getLogger("storage-provider")

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
                ExtraArgs={"ACL": "public-read"} # R2/S3 Public access
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
