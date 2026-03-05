"""Shared test fixtures for Fast Platform API Gateway tests."""
import pytest


@pytest.fixture
def mock_scope():
    """Create a minimal ASGI scope for middleware testing."""
    return {
        "type": "http",
        "state": {},
        "headers": [],
    }


@pytest.fixture
def mock_user_payload():
    """Standard JWT-decoded user payload."""
    return {
        "sub": "admin@smartshop.test",
        "roles": ["SUPER_ADMIN"],
        "perms": ["system:all"],
        "tenant_id": "smartshop",
    }


@pytest.fixture
def mock_customer_payload():
    """Standard customer JWT payload without admin perms."""
    return {
        "sub": "customer@test.com",
        "roles": ["CUSTOMER"],
        "perms": ["product:read", "order:create"],
        "tenant_id": "smartshop",
    }


@pytest.fixture
def mock_app_state():
    """Mock Litestar app state with voice_cache."""
    return {
        "voice_cache": {
            "user-123": {
                "wake_words": ["xohi"],
                "sleep_words": ["tam biet"],
                "greeting_template": "Dạ, em nghe đây sếp.",
                "capabilities": {"READ": True, "MUTATE": True, "ANALYZE": True},
            }
        }
    }
