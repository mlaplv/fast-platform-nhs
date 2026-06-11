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
                campaign_criterion.resource_name,
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
                "resource_name": crit.get("resourceName", ""),
                "campaign_id": campaign_resource_name,
                "text": kw.get("text", ""),
                "match_type": kw.get("matchType", "")
            })
        return results

    async def list_account_negative_keywords(self) -> list[dict]:
        token = await self._get_access_token()
        if not token:
            return []
        # Query for existing SharedSet of type ACCOUNT_LEVEL_NEGATIVE_KEYWORDS
        query = """
            SELECT shared_set.resource_name, shared_set.id, shared_set.name
            FROM shared_set
            WHERE shared_set.type = 'ACCOUNT_LEVEL_NEGATIVE_KEYWORDS'
        """
        shared_sets = await self._search(token, query)
        if not shared_sets:
            return []
        
        shared_set_resource = shared_sets[0].get("sharedSet", {}).get("resourceName")
        if not shared_set_resource:
            return []
            
        # Retrieve all keywords inside this SharedSet
        q2 = f"""
            SELECT
                shared_criterion.resource_name,
                shared_criterion.keyword.text,
                shared_criterion.keyword.match_type,
                shared_criterion.shared_set
            FROM shared_criterion
            WHERE shared_criterion.shared_set = '{shared_set_resource}'
        """
        rows = await self._search(token, q2)
        results = []
        for row in rows:
            crit = row.get("sharedCriterion", {})
            kw = crit.get("keyword", {})
            results.append({
                "resource_name": crit.get("resourceName", ""),
                "text": kw.get("text", ""),
                "match_type": kw.get("matchType", ""),
                "set_name": "TÀI KHOẢN"
            })
        return results

    async def add_account_negative_keywords(self, keywords: list[str]) -> bool:
        token = await self._get_access_token()
        if not token:
            return False
            
        # 1. Check if the SharedSet of type ACCOUNT_LEVEL_NEGATIVE_KEYWORDS already exists
        query = """
            SELECT shared_set.resource_name, shared_set.id, shared_set.name
            FROM shared_set
            WHERE shared_set.type = 'ACCOUNT_LEVEL_NEGATIVE_KEYWORDS'
        """
        shared_sets = await self._search(token, query)
        
        shared_set_resource = None
        if shared_sets:
            shared_set_resource = shared_sets[0].get("sharedSet", {}).get("resourceName")
        else:
            # Create a new SharedSet
            op = {
                "create": {
                    "name": "Global Account Negative Keywords Set",
                    "type": "ACCOUNT_LEVEL_NEGATIVE_KEYWORDS"
                }
            }
            res = await self._mutate(token, "sharedSets", [op])
            if res:
                shared_set_resource = res[0].get("resourceName")
                # Link it to the customer account via CustomerNegativeCriterion
                link_op = {
                    "create": {
                        "negativeKeywordList": {
                            "sharedSet": shared_set_resource
                        }
                    }
                }
                await self._mutate(token, "customerNegativeCriteria", [link_op])
            else:
                return False
                
        if not shared_set_resource:
            return False
            
        # 2. Add keywords to the SharedSet
        operations = []
        for kw in keywords:
            operations.append({
                "create": {
                    "sharedSet": shared_set_resource,
                    "keyword": {
                        "text": kw,
                        "matchType": "EXACT"
                    }
                }
            })
            
        res = await self._mutate(token, "sharedCriteria", operations, partial_failure=True)
        return len(res) > 0

    async def remove_negative_keyword(self, id: str) -> bool:
        if not self._has_credentials():
            return False
        token = await self._get_access_token()
        if not token:
            return False
            
        # Try removing as shared criterion (account negative keyword)
        shared_resource = f"customers/{self._CUSTOMER_ID}/sharedCriteria/{id}"
        op_shared = {"remove": shared_resource}
        res_shared = await self._mutate(token, "sharedCriteria", [op_shared])
        if res_shared:
            return True
            
        # Try removing as campaign criterion (campaign negative keyword)
        camp_resource = f"customers/{self._CUSTOMER_ID}/campaignCriteria/{id}"
        op_camp = {"remove": camp_resource}
        res_camp = await self._mutate(token, "campaignCriteria", [op_camp])
        return len(res_camp) > 0
