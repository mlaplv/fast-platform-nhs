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
        
        # Phase 82.55: Health Check — Skip dead or currently limited keys
        initial_index = self.current_index
        import time
        now = time.time()
        
        while self.key_pairs[self.current_index].get("dead") or \
              self.key_pairs[self.current_index].get("limit_until", 0) > now:
            self.current_index = (self.current_index + 1) % len(self.key_pairs)
            if self.current_index == initial_index:
                # All keys are dead or limited
                if self.key_pairs[self.current_index].get("dead"):
                    raise Exception("All Google Search API Keys are FORBIDDEN (403). Check configuration.")
                else:
                    raise Exception("All Google Search API Keys are currently RATE LIMITED (429).")
        
        return self.key_pairs[self.current_index]

    def _rotate_key(self, status_code: Optional[int] = None) -> None:
        if status_code == 403:
            logger.error(f"[DiscoveryHunter] Key index {self.current_index} is FORBIDDEN (403). Marking as DEAD.")
            self.key_pairs[self.current_index]["dead"] = True
        elif status_code == 429:
            import time
            # Rate limited for 15 minutes (CNS V82.55 standard cooldown)
            logger.warning(f"[DiscoveryHunter] Key index {self.current_index} is RATE LIMITED (429). Cooling down...")
            self.key_pairs[self.current_index]["limit_until"] = time.time() + 900
            
        self.current_index = (self.current_index + 1) % len(self.key_pairs)
        logger.info(f"[DiscoveryHunter] Rotating key to index {self.current_index}")

    async def search(self, query: str) -> str:
        """
        Thực hiện duy nhất 01 request (Sếp yêu cầu) để lấy top snippets.
        [CNS V90.0] Sử dụng Shared Search Cache để tiết kiệm Quota.
        """
        if not query:
            return ""

        from .shared_search_cache import get_or_fetch as _cached_search

        async def _do_fetch() -> List[str]:
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

                    logger.info(f"[DiscoveryHunter] Discovery Search Attempt: {query} (Key index {self.current_index})")
                    response = await client.get(url, params=params, timeout=10.0)
                    
                    if response.status_code == 429:
                        logger.warning(f"[DiscoveryHunter] Key limited (429). Rotating...")
                        self._rotate_key(status_code=429)
                        attempts += 1
                        continue
                    
                    if response.status_code == 403:
                        logger.error(f"[DiscoveryHunter] Key forbidden (403). Rotating...")
                        self._rotate_key(status_code=403)
                        attempts += 1
                        continue

                    response.raise_for_status()
                    data = response.json()
                    items = data.get('items', [])
                    
                    if not items:
                        logger.warning(f"[DiscoveryHunter] No results found for: {query}")
                        return ["Không tìm thấy kết quả tìm kiếm thực tế."]

                    # Trích xuất 10 snippets
                    snippets = []
                    for i, item in enumerate(items, 1):
                        title = item.get('title', 'Unknown Title')
                        snippet = item.get('snippet', '').replace('\n', ' ')
                        snippets.append(f"[{i}] {title}: {snippet}")

                    return snippets

                except Exception as e:
                    logger.error(f"[DiscoveryHunter] Search Error: {e}")
                    self._rotate_key()
                    attempts += 1
                    continue
            return ["Cảnh báo: Không thể thực hiện trinh sát thực tế do lỗi API."]

        # [CNS V90.0] Dùng chung cache với SEO & Copyright
        results = await _cached_search(query=query, fetch_fn=_do_fetch, num=10)
        return "\n".join(results)
