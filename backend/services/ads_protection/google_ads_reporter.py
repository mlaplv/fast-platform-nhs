"""
Google Ads Reporter
Tự động báo cáo invalid clicks + tạo Manual Investigation Request
Dùng Google Ads API v24 (google-ads Python client)
"""
from __future__ import annotations

import csv
import io
import logging
import os
import textwrap
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("ads_protection.google_ads_reporter")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class InvalidClickRecord:
    """Một bản ghi click gian lận cần báo cáo."""
    gclid: str | None
    ip_address: str
    user_agent: str
    timestamp: str
    fraud_score: float
    signals: list[str]                  # danh sách signal tên ngắn
    campaign_id: str | None = None
    ad_group_id: str | None = None
    keyword: str | None = None


@dataclass
class InvestigationReport:
    """Báo cáo hoàn chỉnh gửi Google Support."""
    customer_id: str
    date_from: str
    date_to: str
    total_suspected_clicks: int
    estimated_wasted_budget_vnd: float
    records: list[InvalidClickRecord] = field(default_factory=list)
    csv_path: str = ""
    support_message: str = ""


# ---------------------------------------------------------------------------
# Reporter Service
# ---------------------------------------------------------------------------

class GoogleAdsReporter:
    """
    Tổng hợp invalid clicks và tạo báo cáo gửi Google.
    Hai chế độ:
      1. Tự động qua Google Ads API (nếu có credentials)
      2. Manual Investigation Request — tạo CSV + template email
    """

    # Aggressive cleaning: strip comments and non-digits
    _raw_cid = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "").split("#")[0].strip()
    _raw_login_cid = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").split("#")[0].strip()

    _CUSTOMER_ID: str = "".join(filter(str.isdigit, _raw_cid))
    _LOGIN_CUSTOMER_ID: str = "".join(filter(str.isdigit, _raw_login_cid)) or _CUSTOMER_ID
    _DEVELOPER_TOKEN: str = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "").strip()
    _OAUTH_CLIENT_ID: str = os.getenv("GOOGLE_ADS_OAUTH_CLIENT_ID", "").strip()
    _OAUTH_CLIENT_SECRET: str = os.getenv("GOOGLE_ADS_OAUTH_CLIENT_SECRET", "").strip()
    _REFRESH_TOKEN: str = os.getenv("GOOGLE_ADS_REFRESH_TOKEN", "").strip()

    _API_VERSION = "v24"
    _API_BASE = f"https://googleads.googleapis.com/{_API_VERSION}"

    REPORT_DIR = Path("reports/click_fraud")

    # -----------------------------------------------------------------------
    # Public: tạo báo cáo từ danh sách records
    # -----------------------------------------------------------------------

    async def generate_investigation_report(
        self,
        records: list[InvalidClickRecord],
        date_from: str,
        date_to: str,
        avg_cpc_vnd: float = 5000.0,
        campaign_name: str = "Active Campaign",
        landing_url: str = "https://osmo.vn",
    ) -> InvestigationReport:
        """
        Tạo InvestigationReport đầy đủ:
        - CSV chứng cứ (gclid, ip, timestamp, fraud_score, signals)
        - Email template tiếng Anh gửi Google Ads Support
        """
        self.REPORT_DIR.mkdir(parents=True, exist_ok=True)

        total = len(records)
        wasted = total * avg_cpc_vnd

        csv_path = await self._export_csv(records, date_from, date_to)
        support_msg = self._build_support_message(
            records=records,
            date_from=date_from,
            date_to=date_to,
            csv_filename=csv_path,
            avg_cpc_vnd=avg_cpc_vnd,
            campaign_name=campaign_name,
            landing_url=landing_url,
        )

        report = InvestigationReport(
            customer_id=self._CUSTOMER_ID,
            date_from=date_from,
            date_to=date_to,
            total_suspected_clicks=total,
            estimated_wasted_budget_vnd=wasted,
            records=records,
            csv_path=csv_path,
            support_message=support_msg,
        )

        # Ghi report text ra file
        report_path = self.REPORT_DIR / f"investigation_{date_from}_{date_to}.txt"
        report_path.write_text(support_msg, encoding="utf-8")

        logger.info(
            "investigation_report_generated records=%d wasted_vnd=%.0f path=%s",
            total, wasted, report_path,
        )
        return report

    # -----------------------------------------------------------------------
    # Public: lấy Invalid Click metrics từ Google Ads API
    # -----------------------------------------------------------------------

    async def fetch_invalid_click_metrics(
        self, date_from: str, date_to: str
    ) -> list[dict[str, Any]]:
        try:
            if not self._has_credentials():
                logger.warning("google_ads_credentials_missing — returning empty metrics")
                return []

            access_token = await self._get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "developer-token": self._DEVELOPER_TOKEN,
                "login-customer-id": self._LOGIN_CUSTOMER_ID,
            }

            query = f"""
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    metrics.clicks,
                    metrics.invalid_clicks,
                    metrics.invalid_click_rate,
                    metrics.cost_micros
                FROM campaign
                WHERE campaign.status = 'ENABLED'
                  AND segments.date BETWEEN '{date_from}' AND '{date_to}'
                LIMIT 50
            """.strip()

            url = f"{self._API_BASE}/customers/{self._CUSTOMER_ID}/googleAds:search"

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    url,
                    headers=headers,
                    json={"query": query},
                )
                if resp.status_code != 200:
                    logger.error("GOOGLE_ADS_API_ERROR: status=%d body=%s", resp.status_code, resp.text)
                    resp.raise_for_status()
                
                data = resp.json()

            rows: list[dict[str, Any]] = []
            # data có thể là list (batches) hoặc dict tùy theo proxy/client
            batches = data if isinstance(data, list) else [data]
            
            for batch in batches:
                for result in batch.get("results", []):
                    campaign = result.get("campaign", {})
                    metrics  = result.get("metrics", {})
                    
                    # Google Ads API metrics are strings in REST JSON
                    c = int(metrics.get("clicks", 0))
                    ic = int(metrics.get("invalidClicks", 0))
                    icr = float(metrics.get("invalidClickRate", 0))
                    cm = int(metrics.get("costMicros", 0))
                    
                    # Calculate protected value (avg CPC * invalid clicks)
                    # We use the same currency as account (assume VND for this project)
                    avg_cpc_micros = cm / c if c > 0 else 0
                    protected_micros = avg_cpc_micros * ic
                    protected_vnd = round(protected_micros / 1_000_000)
                    
                    rows.append({
                        "campaign_name": campaign.get("name", "Unknown"),
                        "clicks":         c,
                        "invalid_clicks": ic,
                        "invalid_click_rate": icr,
                        "cost_micros":    cm,
                        "cost_vnd":       protected_vnd,
                    })

            return rows
        except Exception as e:
            logger.error("FAILED_FETCH_GOOGLE_METRICS: %s", e, exc_info=True)
            return [] # Trả về list rỗng thay vì làm crash cả Dashboard

    # -----------------------------------------------------------------------
    # Public: upload offline conversion với status INVALID
    # Dùng để "clean" training data của Smart Bidding
    # -----------------------------------------------------------------------

    async def report_invalid_conversions(
        self, gclids: list[str], conversion_action_name: str
    ) -> dict[str, Any]:
        """
        Upload negative signal cho Google Smart Bidding.
        Với mỗi GCLID được đánh là fraud, upload conversion với
        bộ conversion_value=0 để Smart Bidding không học từ những click này.
        """
        if not gclids or not self._has_credentials():
            return {"status": "skipped", "reason": "no_credentials_or_empty"}

        access_token = await self._get_access_token()
        url = (
            f"https://googleads.googleapis.com/v24/customers/"
            f"{self._CUSTOMER_ID}:uploadClickConversions"
        )

        conversions = [
            {
                "gclid": gclid,
                "conversionAction": (
                    f"customers/{self._CUSTOMER_ID}/conversionActions/{conversion_action_name}"
                ),
                "conversionDateTime": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S+00:00"),
                "conversionValue": 0.0,
                "currencyCode": "VND",
                "externalAttributionData": {
                    "externalAttributionModel": "LAST_CLICK",
                    "externalAttributionCredit": 0.0,
                },
            }
            for gclid in gclids
        ]

        payload = {
            "conversions": conversions,
            "partialFailure": True,
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "developer-token": self._DEVELOPER_TOKEN,
                },
                json=payload,
            )

        if resp.status_code == 200:
            logger.info("invalid_conversions_uploaded count=%d", len(gclids))
            return {"status": "ok", "uploaded": len(gclids)}
        else:
            logger.error("upload_failed status=%d body=%s", resp.status_code, resp.text[:1000])
            return {"status": "error", "http_status": resp.status_code}

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    async def _export_csv(
        self, records: list[InvalidClickRecord], date_from: str, date_to: str
    ) -> str:
        """Xuất CSV bằng chứng để đính kèm vào support ticket."""
        filename = self.REPORT_DIR / f"invalid_clicks_{date_from}_{date_to}.csv"
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=[
                "timestamp", "gclid", "ip_address", "user_agent",
                "fraud_score", "signals", "campaign_id", "keyword",
            ],
        )
        writer.writeheader()
        for r in records:
            writer.writerow({
                "timestamp":   r.timestamp,
                "gclid":       r.gclid or "",
                "ip_address":  r.ip_address,
                "user_agent":  r.user_agent[:80],
                "fraud_score": f"{r.fraud_score:.2f}",
                "signals":     "; ".join(r.signals),
                "campaign_id": r.campaign_id or "",
                "keyword":     r.keyword or "",
            })

        filename.write_text(buf.getvalue(), encoding="utf-8")
        return str(filename)

    def _build_support_message(
        self,
        records: list[InvalidClickRecord],
        date_from: str,
        date_to: str,
        csv_filename: str,
        avg_cpc_vnd: float,
        campaign_name: str = "Active Campaign",
        landing_url: str = "https://osmo.vn",
    ) -> str:
        """Tạo email template tiếng Anh gửi Google Ads Support."""
        total = len(records)
        wasted_vnd = total * avg_cpc_vnd
        wasted_usd = wasted_vnd / 25000

        # Unique IPs
        unique_ips = list({r.ip_address for r in records})[:20]
        ip_list = "\n".join(f"  - {ip}" for ip in unique_ips)

        # Top signals
        from collections import Counter
        all_signals: list[str] = []
        for r in records:
            all_signals.extend(r.signals)
        top_signals = Counter(all_signals).most_common(5)
        signal_text = "\n".join(f"  - {sig}: {cnt} occurrences" for sig, cnt in top_signals)

        return textwrap.dedent(f"""
        ============================================================
        GOOGLE ADS — INVALID CLICK MANUAL INVESTIGATION REQUEST
        ============================================================
        Date Range  : {date_from} → {date_to}
        Customer ID : {self._CUSTOMER_ID or "(your-customer-id)"}
        Campaign    : {campaign_name}
        Landing URL : {landing_url}

        SUMMARY
        -------
        Total suspected invalid clicks : {total}
        Estimated wasted spend         : {wasted_vnd:,.0f} VND (~${wasted_usd:,.2f} USD)
        Evidence CSV attached          : {csv_filename}

        TOP FRAUD SIGNALS DETECTED
        --------------------------
        {signal_text}

        SUSPICIOUS IP ADDRESSES (sample, full list in CSV)
        ---------------------------------------------------
        {ip_list}

        DETECTION METHOD
        ----------------
        We deployed a multi-layer click fraud detection system on our
        landing page (https://osmo.vn) that captures:
          • IP reputation (datacenter, VPN, Tor, proxy detection)
          • Behavioral fingerprinting (mouse events, scroll depth, session time)
          • Rate-based anomaly detection (>5 clicks/IP/hour)
          • Headless browser detection (navigator.webdriver flag)

        All suspicious clicks had a fraud_score >= 0.65 based on a
        14-signal weighted model (full methodology in attached CSV).

        REQUEST
        -------
        We respectfully request:
        1. A full investigation of the above click activity.
        2. Credit/refund for confirmed invalid clicks.
        3. Information on any automated protection already applied
           to this account during the specified period.

        We are happy to provide additional logs or evidence upon request.

        Best regards,
        [Your Name / Company — Osmo.vn]
        [Contact Email]
        [Phone]
        ============================================================
        """).strip()

    def _has_credentials(self) -> bool:
        return all([
            self._DEVELOPER_TOKEN,
            self._OAUTH_CLIENT_ID,
            self._OAUTH_CLIENT_SECRET,
            self._REFRESH_TOKEN,
            self._CUSTOMER_ID,
        ])

    async def _get_access_token(self) -> str:
        """OAuth2 token refresh."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id":     self._OAUTH_CLIENT_ID,
                    "client_secret": self._OAUTH_CLIENT_SECRET,
                    "refresh_token": self._REFRESH_TOKEN,
                    "grant_type":    "refresh_token",
                },
            )
            resp.raise_for_status()
            return resp.json()["access_token"]
