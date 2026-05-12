"""
Campaign Manager — Google Ads API v24
CRUD campaigns, ad groups, và responsive search ads.
Dùng REST API (httpx) thay vì gRPC client để tránh phụ thuộc nặng.
100% async, type-safe, không dùng Any.
"""
from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Optional

import httpx

from backend.services.ads_protection.schemas import (
    AdGroupCreateRequest,
    AdGroupInfo,
    AdInfo,
    CampaignBudgetUpdate,
    CampaignCreateRequest,
    CampaignInfo,
    CampaignOperationResult,
    CampaignStatusUpdate,
    KeywordSuggestion,
    PolicyCheckResult,
    ResponsiveSearchAdCreate,
)
from backend.services.ads_protection.policy_validator import PolicyValidator

logger = logging.getLogger("ads_protection.campaign_manager")




def _vnd_to_micros(vnd: float) -> int:
    """Chuyển đổi VNĐ → micros (đơn vị Google Ads sử dụng theo tiền tệ tài khoản)."""
    return int(vnd * 1_000_000)


def _micros_to_vnd(micros: int) -> float:
    """Chuyển đổi micros → VNĐ (giả định tài khoản dùng tiền tệ VNĐ)."""
    return micros / 1_000_000


class CampaignManager:
    """
    Quản lý chiến dịch Google Ads qua REST API v24.
    Cung cấp CRUD đầy đủ với policy validation tích hợp.
    """

    # Aggressive cleaning (Elite V2.2 Protocol)
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
    _OAUTH_URL = "https://oauth2.googleapis.com/token"

    def __init__(self) -> None:
        self._validator = PolicyValidator()

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC: Campaigns
    # ─────────────────────────────────────────────────────────────────────────

    async def list_campaigns(self) -> list[CampaignInfo]:
        """Lấy danh sách campaigns với metrics và landing page URL."""
        if not self._has_credentials():
            return []

        token = await self._get_access_token()
        
        # 1. Fetch Campaigns
        query = """
            SELECT
                campaign.resource_name,
                campaign.id,
                campaign.name,
                campaign.status,
                campaign_budget.amount_micros,
                campaign.bidding_strategy_type,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_micros,
                metrics.conversions,
                campaign.primary_status
            FROM campaign
            WHERE campaign.status != 'REMOVED'
            ORDER BY metrics.impressions DESC
            LIMIT 50
        """

        # 2. Fetch ENABLED ads to map landing pages
        ad_query = """
            SELECT campaign.resource_name, ad_group_ad.ad.final_urls 
            FROM ad_group_ad 
            WHERE ad_group_ad.status = 'ENABLED'
        """

        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "developer-token": self._DEVELOPER_TOKEN,
                    "login-customer-id": self._LOGIN_CUSTOMER_ID
                }
                
                # Campaigns
                resp = await client.post(
                    f"{self._API_BASE}/customers/{self._CUSTOMER_ID}/googleAds:search",
                    headers=headers,
                    json={"query": query}
                )
                
                # Ads for mapping
                ad_resp = await client.post(
                    f"{self._API_BASE}/customers/{self._CUSTOMER_ID}/googleAds:search",
                    headers=headers,
                    json={"query": ad_query}
                )

                if resp.status_code != 200:
                    logger.error("LIST_CAMPAIGNS_FAILED: %s", resp.text)
                    return []

                data = resp.json()
                ad_data = ad_resp.json() if ad_resp.status_code == 200 else {"results": []}
                
                ad_map = {}
                for row in ad_data.get("results", []):
                    c_res = row["campaign"]["resourceName"]
                    urls = row["adGroupAd"]["ad"].get("finalUrls", [])
                    if urls and c_res not in ad_map:
                        ad_map[c_res] = urls[0]

                results: list[CampaignInfo] = []
                for row in data.get("results", []):
                    c = row["campaign"]
                    m = row.get("metrics", {})
                    b = row.get("campaignBudget", {})
                    
                    results.append(CampaignInfo(
                        resource_name=c["resourceName"],
                        id=c["id"],
                        name=c["name"],
                        status=c["status"],
                        daily_budget_vnd=_micros_to_vnd(int(b.get("amountMicros", 0))),
                        bidding_strategy=c.get("biddingStrategyType", "UNKNOWN"),
                        start_date=c.get("startDate", ""),
                        end_date=c.get("endDate"),
                        impressions=int(m.get("impressions", 0)),
                        clicks=int(m.get("clicks", 0)),
                        ctr=float(m.get("ctr", 0)),
                        avg_cpc_vnd=_micros_to_vnd(int(m.get("averageCpc", 0))),
                        cost_vnd=_micros_to_vnd(int(m.get("costMicros", 0))),
                        conversions=float(m.get("conversions", 0)),
                        policy_status=c.get("primaryStatus", "ELIGIBLE"),
                        landing_page_url=ad_map.get(c["resourceName"])
                    ))
                return results

        except Exception as e:
            logger.error("LIST_CAMPAIGNS_CRITICAL_FAILURE: %s", e)
            return []

    async def create_campaign(
        self, req: CampaignCreateRequest
    ) -> CampaignOperationResult:
        """
        Tạo campaign mới với policy validation bắt buộc.
        Sẽ từ chối nếu có ERROR violations.
        """
        # 1. Pre-validate policy
        policy_result: PolicyCheckResult = self._validator.check_campaign(req)
        if not policy_result.is_compliant:
            return CampaignOperationResult(
                success=False,
                operation="CREATE",
                message=f"Vi phạm chính sách ({len(policy_result.violations)} lỗi). Hãy sửa trước khi submit.",
                policy_check=policy_result,
            )

        if not self._has_credentials():
            return CampaignOperationResult(
                success=False,
                operation="CREATE",
                message="Chưa cấu hình Google Ads API credentials.",
                policy_check=policy_result,
            )

        token = await self._get_access_token()
        budget_micros = _vnd_to_micros(req.budget.daily_budget_vnd)

        # 2. Tạo Campaign Budget trước
        budget_op = {
            "create": {
                "name": f"Budget cho {req.name} — {datetime.now(UTC).strftime('%Y%m%d%H%M')}",
                "amountMicros": str(budget_micros),
                "deliveryMethod": req.budget.delivery_method,
                "explicitlyShared": False,
            }
        }
        budget_result = await self._mutate(token, "campaignBudgets", [budget_op])
        if not budget_result:
            return CampaignOperationResult(
                success=False,
                operation="CREATE",
                message="Không thể tạo Campaign Budget.",
                policy_check=policy_result,
            )
        budget_resource = budget_result[0].get("resourceName", "")

        # 3. Tạo Campaign
        campaign_op: dict[str, object] = {
            "create": {
                "name": req.name,
                "status": "PAUSED",  # Luôn tạo ở trạng thái PAUSED — an toàn
                "campaignBudget": budget_resource,
                "advertisingChannelType": "SEARCH",
                "startDate": req.start_date.replace("-", ""),
                "networkSettings": {
                    "targetGoogleSearch": req.search_network,
                    "targetSearchNetwork": req.search_network,
                    "targetContentNetwork": req.display_network,
                },
            }
        }

        # Gắn bidding strategy
        campaign_op = self._attach_bidding(campaign_op, req)

        if req.end_date:
            campaign_data = campaign_op["create"]
            if isinstance(campaign_data, dict):
                campaign_data["endDate"] = req.end_date.replace("-", "")

        camp_result = await self._mutate(token, "campaigns", [campaign_op])
        if not camp_result:
            return CampaignOperationResult(
                success=False,
                operation="CREATE",
                message="Không thể tạo Campaign trên Google Ads.",
                policy_check=policy_result,
            )

        resource_name: str = camp_result[0].get("resourceName", "")
        logger.info("campaign_created resource=%s name=%s", resource_name, req.name)
        return CampaignOperationResult(
            success=True,
            resource_name=resource_name,
            operation="CREATE",
            message=f"Chiến dịch '{req.name}' đã được tạo ở trạng thái PAUSED. Kiểm tra và ENABLE khi sẵn sàng.",
            policy_check=policy_result,
        )

    async def update_status(
        self, campaign_resource_name: str, req: CampaignStatusUpdate
    ) -> CampaignOperationResult:
        """Bật/Tắt/Xóa campaign."""
        if not self._has_credentials():
            return CampaignOperationResult(success=False, operation="UPDATE", message="Chưa có credentials.")

        token = await self._get_access_token()
        op = {
            "update": {
                "resourceName": campaign_resource_name,
                "status": req.status,
            },
            "updateMask": "status",
        }
        result = await self._mutate(token, "campaigns", [op])
        success = bool(result)
        logger.info("campaign_status_update resource=%s status=%s success=%s", campaign_resource_name, req.status, success)
        return CampaignOperationResult(
            success=success,
            resource_name=campaign_resource_name,
            operation="UPDATE",
            message=f"Campaign đã được {'cập nhật' if success else 'thất bại'} sang trạng thái {req.status}.",
        )

    async def update_budget(
        self, campaign_resource_name: str, req: CampaignBudgetUpdate
    ) -> CampaignOperationResult:
        """Cập nhật ngân sách campaign."""
        if not self._has_credentials():
            return CampaignOperationResult(success=False, operation="UPDATE", message="Chưa có credentials.")

        # Lấy budget resource name từ campaign
        token = await self._get_access_token()
        query = f"""
            SELECT campaign.campaign_budget
            FROM campaign
            WHERE campaign.resource_name = '{campaign_resource_name}'
        """
        rows = await self._search(token, query)
        if not rows:
            return CampaignOperationResult(success=False, operation="UPDATE", message="Không tìm thấy campaign.")

        budget_resource = rows[0].get("campaign", {}).get("campaignBudget", "")
        op = {
            "update": {
                "resourceName": budget_resource,
                "amountMicros": str(_vnd_to_micros(req.daily_budget_vnd)),
            },
            "updateMask": "amount_micros",
        }
        result = await self._mutate(token, "campaignBudgets", [op])
        success = bool(result)
        return CampaignOperationResult(
            success=success,
            resource_name=campaign_resource_name,
            operation="UPDATE",
            message=f"Ngân sách đã cập nhật thành {req.daily_budget_vnd:,.0f}₫/ngày." if success else "Cập nhật thất bại.",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC: Ad Groups
    # ─────────────────────────────────────────────────────────────────────────

    async def list_ad_groups(self, campaign_resource_name: str) -> list[AdGroupInfo]:
        """Danh sách ad groups của một campaign."""
        if not self._has_credentials():
            return []
        token = await self._get_access_token()
        query = f"""
            SELECT
                ad_group.resource_name,
                ad_group.id,
                ad_group.name,
                ad_group.status,
                ad_group.cpc_bid_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros
            FROM ad_group
            WHERE campaign.resource_name = '{campaign_resource_name}'
              AND ad_group.status != 'REMOVED'
        """
        rows = await self._search(token, query)
        return [
            AdGroupInfo(
                resource_name=r.get("adGroup", {}).get("resourceName", ""),
                id=str(r.get("adGroup", {}).get("id", "")),
                name=r.get("adGroup", {}).get("name", ""),
                status=r.get("adGroup", {}).get("status", "UNKNOWN"),
                cpc_bid_vnd=_micros_to_vnd(int(r.get("adGroup", {}).get("cpcBidMicros", 0))),
                impressions=int(r.get("metrics", {}).get("impressions", 0)),
                clicks=int(r.get("metrics", {}).get("clicks", 0)),
                cost_vnd=_micros_to_vnd(int(r.get("metrics", {}).get("costMicros", 0))),
            )
            for r in rows
        ]

    async def create_ad_group(self, req: AdGroupCreateRequest) -> CampaignOperationResult:
        """Tạo ad group + thêm keywords."""
        if not self._has_credentials():
            return CampaignOperationResult(success=False, operation="CREATE", message="Chưa có credentials.")

        token = await self._get_access_token()
        ag_op = {
            "create": {
                "name": req.name,
                "campaign": req.campaign_resource_name,
                "status": "ENABLED",
                "cpcBidMicros": str(_vnd_to_micros(req.cpc_bid_vnd)),
                "type": "SEARCH_STANDARD",
            }
        }
        ag_result = await self._mutate(token, "adGroups", [ag_op])
        if not ag_result:
            return CampaignOperationResult(success=False, operation="CREATE", message="Không thể tạo Ad Group.")

        ag_resource = ag_result[0].get("resourceName", "")

        # Thêm keywords
        kw_match = req.match_types[0] if req.match_types else "EXACT"
        kw_ops = [
            {
                "create": {
                    "adGroup": ag_resource,
                    "status": "ENABLED",
                    "keyword": {"text": kw, "matchType": kw_match},
                }
            }
            for kw in req.keywords
        ]
        await self._mutate(token, "adGroupCriteria", kw_ops)
        logger.info("ad_group_created resource=%s keywords=%d", ag_resource, len(req.keywords))
        return CampaignOperationResult(
            success=True,
            resource_name=ag_resource,
            operation="CREATE",
            message=f"Ad Group '{req.name}' đã tạo với {len(req.keywords)} keywords.",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC: Ads
    # ─────────────────────────────────────────────────────────────────────────

    async def create_responsive_search_ad(
        self, req: ResponsiveSearchAdCreate
    ) -> CampaignOperationResult:
        """Tạo Responsive Search Ad với policy validation bắt buộc."""
        # Policy check
        policy_result = self._validator.check_ad(req)
        if not policy_result.is_compliant:
            return CampaignOperationResult(
                success=False,
                operation="CREATE",
                message=f"Vi phạm chính sách ({len(policy_result.violations)} lỗi). Sửa trước khi submit.",
                policy_check=policy_result,
            )

        if not self._has_credentials():
            return CampaignOperationResult(success=False, operation="CREATE", message="Chưa có credentials.", policy_check=policy_result)

        token = await self._get_access_token()
        ad_op: dict[str, object] = {
            "create": {
                "adGroup": req.ad_group_resource_name,
                "status": "ENABLED",
                "ad": {
                    "responsiveSearchAd": {
                        "headlines": [{"text": h} for h in req.headlines],
                        "descriptions": [{"text": d} for d in req.descriptions],
                        "path1": req.display_path1 or "",
                        "path2": req.display_path2 or "",
                    },
                    "finalUrls": [req.final_url],
                },
            }
        }
        result = await self._mutate(token, "adGroupAds", [ad_op])
        success = bool(result)
        resource = result[0].get("resourceName", "") if result else ""
        logger.info("rsa_created resource=%s success=%s", resource, success)
        return CampaignOperationResult(
            success=success,
            resource_name=resource,
            operation="CREATE",
            message="Responsive Search Ad đã tạo thành công." if success else "Tạo Ad thất bại.",
            policy_check=policy_result,
        )

    async def list_ads(self, ad_group_resource_name: str) -> list[AdInfo]:
        """Danh sách ads của một Ad Group."""
        if not self._has_credentials():
            return []
        token = await self._get_access_token()
        query = f"""
            SELECT
                ad_group_ad.resource_name,
                ad_group_ad.ad.id,
                ad_group_ad.ad.type,
                ad_group_ad.status,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.ad.final_urls,
                ad_group_ad.policy_summary.approval_status
            FROM ad_group_ad
            WHERE ad_group.resource_name = '{ad_group_resource_name}'
              AND ad_group_ad.status != 'REMOVED'
        """
        rows = await self._search(token, query)
        result_ads: list[AdInfo] = []
        for r in rows:
            a = r.get("adGroupAd", {})
            ad = a.get("ad", {})
            rsa = ad.get("responsiveSearchAd", {})
            result_ads.append(AdInfo(
                resource_name=a.get("resourceName", ""),
                id=str(ad.get("id", "")),
                type=ad.get("type", "UNKNOWN"),
                status=a.get("status", "UNKNOWN"),
                headlines=[h.get("text", "") for h in rsa.get("headlines", [])],
                descriptions=[d.get("text", "") for d in rsa.get("descriptions", [])],
                final_url=(ad.get("finalUrls") or [""])[0],
                policy_summary=a.get("policySummary", {}).get("approvalStatus", "ELIGIBLE"),
            ))
        return result_ads

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC: Keyword Suggestions (Keyword Planner)
    # ─────────────────────────────────────────────────────────────────────────

    async def get_keyword_suggestions(
        self,
        seed_keywords: list[str],
        language_code: str = "vi",
        country_code: str = "VN",
    ) -> list[KeywordSuggestion]:
        """
        Gợi ý từ khóa từ Google Keyword Planner API.
        Fallback trả rỗng nếu chưa có credentials.
        """
        if not self._has_credentials():
            logger.warning("keyword_planner_credentials_missing")
            return []

        token = await self._get_access_token()
        url = f"{self._API_BASE}/customers/{self._CUSTOMER_ID}:generateKeywordIdeas"
        payload = {
            "keywordSeed": {"keywords": seed_keywords},
            "language": f"languageConstants/{self._get_language_id(language_code)}",
            "geoTargetConstants": [f"geoTargetConstants/{self._get_geo_id(country_code)}"],
            "keywordPlanNetwork": "GOOGLE_SEARCH_AND_PARTNERS",
        }
        headers = self._build_headers(token)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            suggestions: list[KeywordSuggestion] = []
            for item in data.get("results", []):
                kw = item.get("text", "")
                metrics = item.get("keywordIdeaMetrics", {})
                competition_map = {"UNSPECIFIED": "MEDIUM", "LOW": "LOW", "MEDIUM": "MEDIUM", "HIGH": "HIGH"}
                suggestions.append(KeywordSuggestion(
                    keyword=kw,
                    avg_monthly_searches=metrics.get("avgMonthlySearches"),
                    competition=competition_map.get(metrics.get("competition", "MEDIUM"), "MEDIUM"),
                    avg_cpc_vnd=_micros_to_vnd(int(metrics.get("averageCpcMicros", 0))) or None,
                    suggested_bid_vnd=_micros_to_vnd(int(metrics.get("highTopOfPageBidMicros", 0))) or None,
                ))
            return suggestions
        except httpx.HTTPStatusError as e:
            logger.error("keyword_planner_failed status=%d", e.response.status_code)
            return []


    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC: Fraud Mitigation (IP Blacklist & Negative Keywords)
    # ─────────────────────────────────────────────────────────────────────────

    async def block_ip(self, campaign_resource_name: str, ip_address: str, is_global: bool = False) -> bool:
        """Chặn một IP tại cấp độ Chiến dịch hoặc Toàn cầu."""
        if not self._has_credentials(): return False
        
        if is_global:
            # Chế độ Toàn cầu: Lấy toàn bộ chiến dịch và chặn IP
            campaigns = await self.list_campaigns()
            success_count = 0
            for camp in campaigns:
                if await self._block_single_ip(camp['resource_name'], ip_address):
                    success_count += 1
            return success_count > 0
            
        return await self._block_single_ip(campaign_resource_name, ip_address)

    async def _block_single_ip(self, campaign_resource_name: str, ip_address: str) -> bool:
        """Helper để chặn IP trên một chiến dịch cụ thể."""
        token = await self._get_access_token()
        operation = {
            "create": {
                "campaign": campaign_resource_name,
                "negative": True,
                "ip_block": {"ip_address": ip_address}
            }
        }
        results = await self._mutate(token, "campaignCriteria", [operation])
        return len(results) > 0

    async def add_negative_keyword(self, campaign_resource_name: str, keyword: str, match_type: str = "EXACT", is_global: bool = False) -> bool:
        """Thêm từ khóa phủ định vào Chiến dịch hoặc Toàn cầu."""
        if not self._has_credentials(): return False
        
        if is_global:
            campaigns = await self.list_campaigns()
            success_count = 0
            for camp in campaigns:
                if await self._add_single_negative_keyword(camp['resource_name'], keyword, match_type):
                    success_count += 1
            return success_count > 0
            
        return await self._add_single_negative_keyword(campaign_resource_name, keyword, match_type)

    async def _add_single_negative_keyword(self, campaign_resource_name: str, keyword: str, match_type: str) -> bool:
        """Helper để thêm từ khóa phủ định vào một chiến dịch cụ thể."""
        token = await self._get_access_token()
        operation = {
            "create": {
                "campaign": campaign_resource_name,
                "negative": True,
                "keyword": {
                    "text": keyword,
                    "match_type": match_type
                }
            }
        }
        results = await self._mutate(token, "campaignCriteria", [operation])
        return len(results) > 0

    async def list_negative_keywords(self, campaign_resource_name: str) -> list[dict]:
        """Lấy danh sách từ khóa phủ định hiện tại của một chiến dịch."""
        if not self._has_credentials(): return []
        token = await self._get_access_token()
        query = f"""
            SELECT
                campaign_criterion.criterion_id,
                campaign_criterion.keyword.text,
                campaign_criterion.keyword.match_type
            FROM campaign_criterion
            WHERE campaign.resource_name = '{campaign_resource_name}'
              AND campaign_criterion.type = 'KEYWORD'
              AND campaign_criterion.negative = TRUE
        """
        rows = await self._search(token, query)
        return [
            {
                "id": str(r.get("campaignCriterion", {}).get("criterionId", "")),
                "text": r.get("campaignCriterion", {}).get("keyword", {}).get("text", ""),
                "match_type": r.get("campaignCriterion", {}).get("keyword", {}).get("matchType", "EXACT")
            } for r in rows
        ]

    async def list_account_negative_keywords(self) -> list[dict]:
        """Lấy danh sách từ khóa phủ định cấp TÀI KHOẢN (Shared Sets & Account Level)."""
        if not self._has_credentials(): return []
        token = await self._get_access_token()
        
        # Chiến thuật 1: Quét Shared Sets (Phổ biến nhất cho list từ khóa rác)
        query_shared = """
            SELECT
                shared_criterion.criterion_id,
                shared_criterion.keyword.text,
                shared_criterion.keyword.match_type,
                shared_set.name
            FROM shared_criterion
        """
        
        results = []
        try:
            rows = await self._search(token, query_shared)
            for r in rows:
                results.append({
                    "id": str(r.get("sharedCriterion", {}).get("criterionId", "")),
                    "text": r.get("sharedCriterion", {}).get("keyword", {}).get("text", ""),
                    "match_type": r.get("sharedCriterion", {}).get("keyword", {}).get("matchType", "EXACT"),
                    "set_name": r.get("sharedSet", {}).get("name", "Shared Set")
                })
        except Exception as e:
            logger.error(f"Failed to fetch shared_criterion: {e}")

        return results

    async def add_account_negative_keywords(self, keywords: list[str]) -> bool:
        """
        Thêm từ khóa phủ định vào toàn bộ chiến dịch (Thay thế cho Account Level do v24 schema change).
        """
        if not self._has_credentials() or not keywords: return False
        
        campaigns = await self.list_campaigns()
        total_success = 0
        for kw in keywords:
            for camp in campaigns:
                if await self._add_single_negative_keyword(camp.resource_name, kw, "BROAD"):
                    total_success += 1
        
        logger.info(f"Added {total_success} negative keyword entries across campaigns")
        return total_success > 0

    async def list_all_blocked_ips(self) -> list[dict]:
        """Lấy toàn bộ IP bị chặn trên TẤT CẢ các chiến dịch."""
        if not self._has_credentials(): return []
        token = await self._get_access_token()
        query = """
            SELECT
                campaign.name,
                campaign_criterion.ip_block.ip_address,
                campaign_criterion.criterion_id
            FROM campaign_criterion
            WHERE campaign_criterion.type = 'IP_BLOCK'
        """
        rows = await self._search(token, query)
        return [
            {
                "campaign_name": r.get("campaign", {}).get("name", ""),
                "ip": r.get("campaignCriterion", {}).get("ipBlock", {}).get("ipAddress", ""),
                "id": str(r.get("campaignCriterion", {}).get("criterionId", ""))
            } for r in rows
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC: Policy validation only (không submit)
    # ─────────────────────────────────────────────────────────────────────────

    def validate_ad_policy(self, req: ResponsiveSearchAdCreate) -> PolicyCheckResult:
        """Kiểm tra policy cho ad mà không cần credentials."""
        return self._validator.check_ad(req)

    def validate_campaign_policy(self, req: CampaignCreateRequest) -> PolicyCheckResult:
        """Kiểm tra policy cho campaign mà không cần credentials."""
        return self._validator.check_campaign(req)

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE: HTTP Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _has_credentials(self) -> bool:
        return all([
            self._DEVELOPER_TOKEN,
            self._OAUTH_CLIENT_ID,
            self._OAUTH_CLIENT_SECRET,
            self._REFRESH_TOKEN,
            self._CUSTOMER_ID,
        ])

    async def _get_access_token(self) -> str:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(self._OAUTH_URL, data={
                "client_id": self._OAUTH_CLIENT_ID,
                "client_secret": self._OAUTH_CLIENT_SECRET,
                "refresh_token": self._REFRESH_TOKEN,
                "grant_type": "refresh_token",
            })
            resp.raise_for_status()
            return str(resp.json()["access_token"])

    def _build_headers(self, token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "developer-token": self._DEVELOPER_TOKEN,
            "login-customer-id": self._LOGIN_CUSTOMER_ID,
            "Content-Type": "application/json",
        }

    async def _search(self, token: str, query: str) -> list[dict[str, object]]:
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
        except httpx.HTTPStatusError as e:
            logger.error("google_ads_search_failed status=%d body=%s", e.response.status_code, e.response.text[:1000])
            return []

    async def _mutate(
        self, token: str, resource: str, operations: list[dict[str, object]]
    ) -> list[dict[str, object]]:
        url = f"{self._API_BASE}/customers/{self._CUSTOMER_ID}/{resource}:mutate"
        headers = self._build_headers(token)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, headers=headers, json={"operations": operations})
                resp.raise_for_status()
                data: dict[str, object] = resp.json()
                results = data.get("results", [])
                return results if isinstance(results, list) else []
        except httpx.HTTPStatusError as e:
            logger.error("google_ads_mutate_failed resource=%s status=%d body=%s",
                        resource, e.response.status_code, e.response.text[:300])
            return []

    @staticmethod
    def _get_language_id(code: str) -> int:
        _map = {"vi": 1000, "en": 1000, "zh": 1017, "ja": 1005, "ko": 1012}
        return _map.get(code.lower(), 1000)

    @staticmethod
    def _get_geo_id(code: str) -> int:
        _map = {"VN": 2704, "US": 2840, "TH": 2764, "SG": 2702, "MY": 2458}
        return _map.get(code.upper(), 2704)
