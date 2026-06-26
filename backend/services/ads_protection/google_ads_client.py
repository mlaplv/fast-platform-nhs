import os
import logging
import httpx
import contextvars
from typing import Optional

logger = logging.getLogger(__name__)

# Context variable to store detailed API error messages per request/task
_last_mutate_error: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("last_mutate_error", default=None)

class GoogleAdsClient:
    """
    Core HTTP Client for communicating with the Google Ads API.
    Handles OAuth token refresh, authentication headers, and generic mutate/search operations.
    """
    _API_VERSION = "v24"
    _API_BASE = f"https://googleads.googleapis.com/{_API_VERSION}"
    _OAUTH_URL = "https://oauth2.googleapis.com/token"

    def __init__(self) -> None:
        _raw_cid = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "").split("#")[0].strip()
        _raw_login_cid = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").split("#")[0].strip()

        self._CUSTOMER_ID = "".join(filter(str.isdigit, _raw_cid))
        self._LOGIN_CUSTOMER_ID = "".join(filter(str.isdigit, _raw_login_cid)) or self._CUSTOMER_ID
        self._DEVELOPER_TOKEN = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "").strip()
        self._OAUTH_CLIENT_ID = os.environ.get("GOOGLE_ADS_OAUTH_CLIENT_ID", "").strip()
        self._OAUTH_CLIENT_SECRET = os.environ.get("GOOGLE_ADS_OAUTH_CLIENT_SECRET", "").strip()
        self._REFRESH_TOKEN = os.environ.get("GOOGLE_ADS_REFRESH_TOKEN", "").strip()
        self._background_tasks: set[asyncio.Task[object]] = set()

    def get_last_mutate_error(self) -> Optional[str]:
        """Lấy chi tiết lỗi từ API mutate gần nhất trong context hiện tại."""
        return _last_mutate_error.get()

    def _has_credentials(self) -> bool:
        return all([
            self._DEVELOPER_TOKEN,
            self._OAUTH_CLIENT_ID,
            self._OAUTH_CLIENT_SECRET,
            self._REFRESH_TOKEN,
            self._CUSTOMER_ID,
        ])

    async def _get_access_token(self) -> str:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self._OAUTH_URL, data={
                    "client_id": self._OAUTH_CLIENT_ID,
                    "client_secret": self._OAUTH_CLIENT_SECRET,
                    "refresh_token": self._REFRESH_TOKEN,
                    "grant_type": "refresh_token",
                })
                resp.raise_for_status()
                return str(resp.json()["access_token"])
        except Exception as e:
            logger.error("Failed to acquire Google Ads access token: %s", e)
            return ""

    def _build_headers(self, token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "developer-token": self._DEVELOPER_TOKEN,
            "login-customer-id": self._LOGIN_CUSTOMER_ID,
            "Content-Type": "application/json",
        }

    async def _search(self, token: str, query: str) -> list[dict[str, object]]:
        if not token:
            return []
        url = f"{self._API_BASE}/customers/{self._CUSTOMER_ID}/googleAds:searchStream"
        headers = self._build_headers(token)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, headers=headers, json={"query": query})
                resp.raise_for_status()
                batches: list[dict[str, object]] = resp.json()
                rows: list[dict[str, object]] = []
                for batch in batches:
                    for result in batch.get("results", []):
                        if isinstance(result, dict):
                            rows.append(result)
                return rows
        except Exception as e:
            logger.error("google_ads_search_failed error=%s", e)
            return []

    async def _mutate(
        self, token: str, resource: str, operations: list[dict[str, object]], partial_failure: bool = False
    ) -> list[dict[str, object]]:
        if not token:
            return []
        url = f"{self._API_BASE}/customers/{self._CUSTOMER_ID}/{resource}:mutate"
        headers = self._build_headers(token)
        
        payload_key = "mutateOperations" if resource == "googleAds" else "operations"
        payload = {payload_key: operations}
        if partial_failure:
            payload["partialFailure"] = True
        try:
            _last_mutate_error.set(None)
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data: dict[str, object] = resp.json()
                
                res_key = "mutateOperationResponses" if resource == "googleAds" else "results"
                results = data.get(res_key, [])
                return results if isinstance(results, list) else []
        except httpx.HTTPStatusError as e:
            try:
                err_data = e.response.json()
                details = err_data.get("error", {}).get("details", [])
                err_msg = ""
                if details:
                    all_errors = []
                    for detail in details:
                        for error in detail.get("errors", []):
                            msg = error.get("message", "")
                            location = error.get("location", {})
                            field_path = ""
                            if location:
                                field_path_elements = location.get("fieldPathElements", [])
                                if field_path_elements:
                                    field_path = " at " + ".".join([f"{item.get('fieldName', '')}[{item.get('index', '')}]" if item.get('index') is not None else str(item.get('fieldName', '')) for item in field_path_elements if item.get('fieldName')])
                            all_errors.append(f"{msg}{field_path}")
                    if all_errors:
                        err_msg = " | ".join(all_errors)
                if not err_msg:
                    err_msg = err_data.get("error", {}).get("message", "")
            except Exception as ex:
                logger.warning(f"Could not parse err_data: {ex}")
                err_msg = ""
            if not err_msg:
                err_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error("google_ads_mutate_failed resource=%s error=%s", resource, err_msg)
            _last_mutate_error.set(err_msg)
            return []
        except Exception as e:
            err_msg = str(e)
            logger.error("google_ads_mutate_failed resource=%s error=%s", resource, err_msg)
            _last_mutate_error.set(err_msg)
            return []
