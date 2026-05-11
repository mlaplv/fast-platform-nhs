"""
IP Intelligence Service
Tra cứu reputation IP qua IPinfo API + local CIDR blacklist
"""
from __future__ import annotations

import ipaddress
import os
from functools import lru_cache

import time
import httpx
from litestar.exceptions import InternalServerException


# ---------------------------------------------------------------------------
# Datacenter / hosting CIDR blocks (AWS, GCP, Azure, OVH, Vultr, …)
# Cập nhật định kỳ từ: https://github.com/client9/ipcat
# ---------------------------------------------------------------------------
_DATACENTER_CIDRS: list[str] = [
    # Amazon AWS
    "3.0.0.0/8", "13.32.0.0/15", "13.224.0.0/14", "52.0.0.0/11",
    "54.64.0.0/11", "54.144.0.0/12", "54.192.0.0/12", "54.208.0.0/13",
    # Google Cloud
    "34.64.0.0/10", "34.128.0.0/10", "35.184.0.0/13", "35.192.0.0/12",
    # Microsoft Azure
    "13.64.0.0/11", "13.96.0.0/13", "20.0.0.0/8", "40.64.0.0/10",
    # DigitalOcean
    "64.225.0.0/16", "134.122.0.0/15", "143.198.0.0/16",
    # Vultr / Choopa
    "64.237.0.0/16", "108.61.0.0/16",
    # OVH
    "51.68.0.0/16", "54.36.0.0/14", "137.74.0.0/16",
    # Cloudflare (proxy)
    "104.16.0.0/12", "172.64.0.0/13", "162.158.0.0/15",
    # Linode
    "45.33.0.0/17", "45.56.0.0/21", "45.79.0.0/16",
]

_DATACENTER_NETWORKS: list[ipaddress.IPv4Network] = [
    ipaddress.ip_network(cidr, strict=False) for cidr in _DATACENTER_CIDRS
]


from .schemas import IPReport

class IPIntelligenceService:
    """
    Tra cứu danh tiếng IP.
    Dùng IPinfo.io (có free tier 50k req/tháng).
    Fallback về local CIDR check nếu API không khả dụng.
    """

    _IPINFO_TOKEN: str = os.getenv("IPINFO_TOKEN", "")
    _IPINFO_BASE = "https://ipinfo.io"
    _TIMEOUT = 3.0          # giây — không để block event loop

    _cache: dict[str, tuple[float, IPReport]] = {}
    _CACHE_TTL = 86400  # 24 giờ

    async def analyze(self, ip: str) -> IPReport:
        """
        Trả về IPReport đầy đủ cho một địa chỉ IP.
        Ưu tiên: Cache → local CIDR check → IPinfo API
        """
        # 1. Kiểm tra Cache
        now = time.time()
        if ip in self._cache:
            ts, report = self._cache[ip]
            if now - ts < self._CACHE_TTL:
                return report

        is_dc_local = self._is_datacenter_local(ip)

        if self._IPINFO_TOKEN:
            try:
                api_data = await self._call_ipinfo(ip)
                report = self._build_report(ip, api_data, is_dc_local)
                self._cache[ip] = (now, report)
                return report
            except Exception:
                pass  # fallback

        # fallback: chỉ dùng local check
        return IPReport(
            ip=ip,
            is_datacenter=is_dc_local,
            is_vpn=False,
            is_tor=False,
            is_proxy=False,
            country="unknown",
            org="unknown",
            abuse_score=0.8 if is_dc_local else 0.0,
            fraud_score=0.7 if is_dc_local else 0.1,
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _is_datacenter_local(ip: str) -> bool:
        try:
            ip_obj = ipaddress.ip_address(ip)
            return any(ip_obj in net for net in _DATACENTER_NETWORKS)
        except ValueError:
            return True  # IP không hợp lệ → suspicious

    async def _call_ipinfo(self, ip: str) -> dict[str, Any]:
        url = f"{self._IPINFO_BASE}/{ip}/json?token={self._IPINFO_TOKEN}"
        async with httpx.AsyncClient(timeout=self._TIMEOUT) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            return data

    @staticmethod
    def _build_report(ip: str, data: dict[str, Any], is_dc_local: bool) -> IPReport:
        org: str = data.get("org", "")
        privacy: dict[str, Any] = data.get("privacy", {})

        is_vpn     = bool(privacy.get("vpn", False))
        is_tor     = bool(privacy.get("tor", False))
        is_proxy   = bool(privacy.get("proxy", False))
        is_dc_api  = bool(privacy.get("hosting", False)) or is_dc_local

        # Tính abuse_score đơn giản
        flags = [is_dc_api, is_vpn, is_tor, is_proxy]
        abuse_score = round(sum(flags) / len(flags), 2)

        # fraud_score = weighted
        fraud_score = round(
            (0.4 if is_dc_api else 0.0)
            + (0.3 if is_vpn  else 0.0)
            + (0.2 if is_tor  else 0.0)
            + (0.1 if is_proxy else 0.0),
            2,
        )

        return IPReport(
            ip=ip,
            is_datacenter=is_dc_api,
            is_vpn=is_vpn,
            is_tor=is_tor,
            is_proxy=is_proxy,
            country=data.get("country", "unknown"),
            org=org,
            abuse_score=abuse_score,
            fraud_score=fraud_score,
        )
