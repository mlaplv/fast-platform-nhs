"""
Elite V2.2: Dynamic Tenant Configuration (EMERGENCY PATCH).
Expanded mapping to include admin and api subdomains.
"""
import os

# Rule R00: APP_DOMAIN is the single source of truth for the primary tenant
APP_DOMAIN = os.getenv("APP_DOMAIN", "nhathuochongson.com").lower().replace("https://", "").replace("http://", "").rstrip("/")
ADMIN_DOMAIN = os.getenv("ADMIN_DOMAIN", "admin.nhathuochongson.com").lower().replace("https://", "").replace("http://", "").rstrip("/")
API_DOMAIN = os.getenv("API_DOMAIN", "api.nhathuochongson.com").lower().replace("https://", "").replace("http://", "").rstrip("/")

# Mapping of public domains to tenant codes (Dynamic)
# Elite V2.2: Grouping all subdomains under the primary tenant
DOMAIN_TENANT_MAP: dict[str, str] = {
    APP_DOMAIN: APP_DOMAIN,
    ADMIN_DOMAIN: APP_DOMAIN,
    API_DOMAIN: APP_DOMAIN,
    "nhathuochongson.com": APP_DOMAIN,
    "admin.nhathuochongson.com": APP_DOMAIN,
    "api.nhathuochongson.com": APP_DOMAIN,
    #"localhost": APP_DOMAIN, # Dev fallback to primary data
}

DEFAULT_TENANT_ID = APP_DOMAIN
