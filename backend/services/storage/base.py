import os
import shutil
from abc import ABC, abstractmethod
from typing import Optional

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
