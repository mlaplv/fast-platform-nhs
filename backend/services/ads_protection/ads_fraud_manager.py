import logging
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.ads_protection.google_ads_client import GoogleAdsClient

logger = logging.getLogger(__name__)

class AdsFraudManager(GoogleAdsClient):
    """
    Quản lý các tính năng chống gian lận và bảo vệ chiến dịch:
    - Chặn IP (IP Blacklisting)
    - Quản lý từ khóa phủ định (Negative Keywords) cấp độ Chiến dịch và Tài khoản
    """
    
    async def block_ip(self, campaign_resource_name: str, ip_address: str, is_global: bool = False) -> bool:
        if not self._has_credentials():
            return False
        if is_global:
            # IP blocking is usually per-campaign in Google Ads API via CampaignCriterion
            logger.warning("Global IP blocking not fully supported by standard API. Falling back to Campaign level if needed, or applying to all campaigns. Currently applying to given campaign.")
        return await self._block_single_ip(campaign_resource_name, ip_address)

    async def _block_single_ip(self, campaign_resource_name: str, ip_address: str) -> bool:
        token = await self._get_access_token()
        if not token:
            return False
        op = {
            "create": {
                "campaign": campaign_resource_name,
                "negative": True,
                "ipBlock": {
                    "ipAddress": ip_address
                }
            }
        }
        res = await self._mutate(token, "campaignCriteria", [op], partial_failure=False)
        return len(res) > 0

    async def list_all_blocked_ips(self) -> list[dict]:
        token = await self._get_access_token()
        if not token:
            return []
        query = """
            SELECT
                campaign_criterion.campaign,
                campaign_criterion.ip_block.ip_address
            FROM campaign_criterion
            WHERE campaign_criterion.type = 'IP_BLOCK'
              AND campaign_criterion.negative = TRUE
        """
        rows = await self._search(token, query)
        results = []
        for row in rows:
            crit = row.get("campaignCriterion", {})
            ip_obj = crit.get("ipBlock", {})
            results.append({
                "campaign": crit.get("campaign", ""),
                "ip_address": ip_obj.get("ipAddress", "")
            })
        return results

    async def add_negative_keyword(self, campaign_resource_name: str, keyword: str, match_type: str = "EXACT", is_global: bool = False) -> bool:
        if not self._has_credentials():
            return False
        if is_global:
            return await self.add_account_negative_keywords([keyword])
        return await self._add_single_negative_keyword(campaign_resource_name, keyword, match_type)

    async def _add_single_negative_keyword(self, campaign_resource_name: str, keyword: str, match_type: str) -> bool:
        token = await self._get_access_token()
        if not token:
            return False
        op = {
            "create": {
                "campaign": campaign_resource_name,
                "negative": True,
                "keyword": {
                    "text": keyword,
                    "matchType": match_type
                }
            }
        }
        res = await self._mutate(token, "campaignCriteria", [op], partial_failure=False)
        return len(res) > 0

    async def list_negative_keywords(self, campaign_resource_name: str) -> list[dict]:
        token = await self._get_access_token()
        if not token:
            return []
        query = f"""
            SELECT
                campaign_criterion.keyword.text,
                campaign_criterion.keyword.match_type
            FROM campaign_criterion
            WHERE campaign_criterion.campaign = '{campaign_resource_name}'
              AND campaign_criterion.type = 'KEYWORD'
              AND campaign_criterion.negative = TRUE
        """
        rows = await self._search(token, query)
        results = []
        for row in rows:
            crit = row.get("campaignCriterion", {})
            kw = crit.get("keyword", {})
            results.append({
                "text": kw.get("text", ""),
                "match_type": kw.get("matchType", "")
            })
        return results

    async def list_account_negative_keywords(self) -> list[dict]:
        token = await self._get_access_token()
        if not token:
            return []
        query = """
            SELECT customer_negative_criterion.criterion_id, customer_negative_criterion.type, customer_negative_criterion.keyword.text, customer_negative_criterion.keyword.match_type
            FROM customer_negative_criterion
            WHERE customer_negative_criterion.type = 'KEYWORD'
        """
        rows = await self._search(token, query)
        results = []
        for row in rows:
            crit = row.get("customerNegativeCriterion", {})
            kw = crit.get("keyword", {})
            results.append({
                "text": kw.get("text", ""),
                "match_type": kw.get("matchType", "")
            })
        return results

    async def add_account_negative_keywords(self, keywords: list[str]) -> bool:
        token = await self._get_access_token()
        if not token:
            return False
        operations = []
        for kw in keywords:
            operations.append({
                "create": {
                    "type": "KEYWORD",
                    "keyword": {
                        "text": kw,
                        "matchType": "EXACT"
                    }
                }
            })
        res = await self._mutate(token, "customerNegativeCriteria", operations, partial_failure=True)
        return len(res) > 0
