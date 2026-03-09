import httpx
import logging
from typing import Optional
from backend.constants.agentic import HTTP_TIMEOUT_SECONDS, HTTP_MAX_CONNECTIONS, HTTP_KEEPALIVE_CONNECTIONS

logger = logging.getLogger("xohi.http")

class SharedHttpClient:
    """R106: Shared Client Singleton to avoid TCP/SSL overhead in Viral traffic."""
    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(
                timeout=httpx.Timeout(HTTP_TIMEOUT_SECONDS, connect=10.0),
                limits=httpx.Limits(max_connections=HTTP_MAX_CONNECTIONS, max_keepalive_connections=HTTP_KEEPALIVE_CONNECTIONS)
            )
            logger.info("[HTTP] Shared AsyncClient initialized.")
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client and not cls._client.is_closed:
            await cls._client.aclose()
            logger.info("[HTTP] Shared AsyncClient closed.")

async def get_http_client() -> httpx.AsyncClient:
    return await SharedHttpClient.get_client()
