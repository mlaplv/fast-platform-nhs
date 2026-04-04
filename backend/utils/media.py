import re
from typing import List, Union, Set, Dict, Optional
import logging

logger = logging.getLogger("api-gateway")

# Elite 2026: Strict Type Definitions for JSON-like structures
JSONPrimitive = Union[str, int, float, bool, None]
JSONStructure = Union[str, List["JSONStructure"], Dict[str, "JSONStructure"], None]

def extract_media_urls(data: JSONStructure) -> Set[str]:
    """
    Elite V2.2: Neural Media URL Extractor (Recursive).
    Trích xuất URL ảnh thông qua việc quét sâu toàn bộ cấu trúc dữ liệu.
    Nhận diện URL dựa trên Pattern thay vì dựa vào hardcoded keys.
    """
    urls: Set[str] = set()
    if data is None:
        return urls

    # Regex nhận diện URL media hệ thống: /storage/..., /uploads/..., URL API nội bộ, URL tuyệt đối, 
    # HOẶC các chuỗi đường dẫn tương đối có đuôi file ảnh phổ biến (Dùng cho mảng images trực tiếp)
    MEDIA_PATTERN = re.compile(r'(/storage/[^\s"\'>]+|/uploads/[^\s"\'>]+|/api/v1/media/[a-fA-F0-9\-]{36}[^\s"\'>]*|https?://[^\s"\'>]+\.(?:jpg|jpeg|png|gif|webp|svg|mp4|webm)|[a-z0-9_\-/]+\.(?:jpg|jpeg|png|gif|webp|svg|mp4|webm))', re.IGNORECASE)

    def _recursive_scan(node: JSONStructure) -> None:
        if node is None:
            return
        if isinstance(node, str):
            # Quét tìm URL hoặc src trong chuỗi
            found = MEDIA_PATTERN.findall(node)
            for f in found:
                # Chuẩn hóa nếu lấy từ trích xuất regex (loại bỏ quote nếu dính)
                clean_url = f.strip().strip('"').strip("'")
                if clean_url:
                    urls.add(clean_url)
        elif isinstance(node, list):
            for item in node:
                _recursive_scan(item)
        elif isinstance(node, dict):
            for val in node.values():
                _recursive_scan(val)

    _recursive_scan(data)
    return urls
