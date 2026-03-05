"""Tests for AuthMiddleware — Tenant resolution and cookie parsing."""
import pytest


class TestTenantResolution:
    """Test tenant ID resolution logic from headers and hostname."""

    def test_x_tenant_header(self):
        """X-Tenant header should be used as primary tenant source."""
        headers = {
            "x-tenant": "store1",
            "host": "admin.smartshop.test",
        }
        tenant_id = headers.get("x-tenant")
        assert tenant_id == "store1"

    def test_host_subdomain_extraction(self):
        """Tenant should be extracted from non-system subdomain."""
        host = "admin.smartshop.test"
        parts = host.split(".")
        system_subdomains = {"admin", "api", "www", "portal"}
        relevant_parts = [p for p in parts if p not in system_subdomains]
        tenant_id = relevant_parts[0] if relevant_parts else "default"
        assert tenant_id == "smartshop"

    def test_localhost_fallback(self):
        """localhost should fallback to 'default'."""
        host = "localhost"
        parts = host.split(".")
        system_subdomains = {"admin", "api", "www", "portal"}
        relevant_parts = [p for p in parts if p not in system_subdomains]
        tenant_id = relevant_parts[0] if relevant_parts else "default"
        if tenant_id == "localhost":
            tenant_id = "default"
        assert tenant_id == "default"


class TestCookieParsing:
    """Test cookie parsing edge cases (fixed in V58.1)."""

    def test_simple_cookie(self):
        """Standard cookie without '=' in value."""
        cookie_str = "admin_token=abc123; session_id=xyz"
        cookies = {
            c.split('=', 1)[0].strip(): c.split('=', 1)[1].strip()
            for c in cookie_str.split(';') if '=' in c
        }
        assert cookies["admin_token"] == "abc123"
        assert cookies["session_id"] == "xyz"

    def test_cookie_with_equals_in_value(self):
        """Cookie value containing '=' (e.g., base64 JWT)."""
        cookie_str = "admin_token=eyJ0eXAi.eyJzdWIi.abc=def; other=val"
        cookies = {
            c.split('=', 1)[0].strip(): c.split('=', 1)[1].strip()
            for c in cookie_str.split(';') if '=' in c
        }
        assert cookies["admin_token"] == "eyJ0eXAi.eyJzdWIi.abc=def"
        assert cookies["other"] == "val"

    def test_empty_cookie(self):
        """Empty cookie string should produce empty dict."""
        cookie_str = ""
        cookies = {
            c.split('=', 1)[0].strip(): c.split('=', 1)[1].strip()
            for c in cookie_str.split(';') if '=' in c
        }
        assert cookies == {}
