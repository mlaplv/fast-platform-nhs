import logging
from typing import List, Dict, Optional
from urllib.parse import quote
from backend.utils.http_client import get_http_client
from backend.constants.agentic import SEARCH_LOCALE_PARAMS

logger = logging.getLogger("api-gateway")

class DiscoveryHunter:
    """
    Step 0/1: Trinh sát thông tin thực tế (Discovery Phase).
    Mục tiêu: Lấy snippets từ Google để AI hiểu đúng ngữ cảnh thực thể (Brand/Product).
    [PHASE 15: DYNAMIC CONTEXT GUARD - R03 ELITE]
    """
    def __init__(self, key_pairs: List[Dict[str, str]]) -> None:
        self.key_pairs = key_pairs
        self.current_index = 0

    def _get_current_pair(self) -> Dict[str, str]:
        if not self.key_pairs:
            raise Exception("No Google Search API Keys configured for Discovery.")
        return self.key_pairs[self.current_index]

    def _rotate_key(self) -> None:
        self.current_index = (self.current_index + 1) % len(self.key_pairs)
        logger.info(f"[DiscoveryHunter] Rotating key to index {self.current_index}")

    async def search(self, query: str) -> str:
        """
        Thực hiện duy nhất 01 request (Sếp yêu cầu) để lấy top snippets.
        Trả về một chuỗi văn bản gộp từ các kết quả tìm kiếm.
        """
        if not query:
            return ""

        url = "https://www.googleapis.com/customsearch/v1"
        client = await get_http_client()
        attempts = 0
        max_attempts = len(self.key_pairs)

        while attempts < max_attempts:
            pair = self._get_current_pair()
            try:
                params = {
                    "key": pair["key"],
                    "cx": pair["cx"],
                    "q": query,
                    "num": 10,  # 1 trang đầu tiên = 10 kết quả
                    "start": 1,
                    **SEARCH_LOCALE_PARAMS
                }

                logger.info(f"[DiscoveryHunter] Discovery Search: {query} (Key index {self.current_index})")
                response = await client.get(url, params=params, timeout=10.0)
                
                if response.status_code == 429:
                    logger.warning(f"[DiscoveryHunter] Key limited (429). Rotating...")
                    self._rotate_key()
                    attempts += 1
                    continue

                response.raise_for_status()
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    logger.warning(f"[DiscoveryHunter] No results found for: {query}")
                    return "Không tìm thấy kết quả tìm kiếm thực tế."

                # Trích xuất 10 snippets
                snippets = []
                for i, item in enumerate(items, 1):
                    title = item.get('title', 'Unknown Title')
                    snippet = item.get('snippet', '').replace('\n', ' ')
                    snippets.append(f"[{i}] {title}: {snippet}")

                context = "\n".join(snippets)
                logger.info(f"[DiscoveryHunter] Discovery successful. Found {len(items)} snippets.")
                return context

            except Exception as e:
                logger.error(f"[DiscoveryHunter] Search Error: {e}")
                self._rotate_key()
                attempts += 1
                continue

        return "Cảnh báo: Không thể thực hiện trinh sát thực tế do lỗi API."
