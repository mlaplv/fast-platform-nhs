"""Tests for PermissionGuard — R36 Foreign Key Never Grants Permission."""
import pytest
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from src.guards import PermissionGuard


def _make_conn(user=None):
    """Create a minimal mock connection with scope matching middleware injection."""
    class MockConnection:
        def __init__(self, scope):
            self.scope = scope
    state = {"user": user} if user else {}
    return MockConnection({"state": state})


class TestPermissionGuard:
    """PermissionGuard must enforce explicit permission checks."""

    def test_super_admin_bypasses_all(self, mock_user_payload):
        """SUPER_ADMIN role should bypass all permission checks."""
        guard = PermissionGuard(["product:write", "order:delete"])
        guard(_make_conn(mock_user_payload), None)

    def test_user_with_matching_perms_passes(self, mock_customer_payload):
        """User with required permissions should pass."""
        guard = PermissionGuard("product:read")
        guard(_make_conn(mock_customer_payload), None)

    def test_user_missing_perms_raises(self, mock_customer_payload):
        """User without required permissions should be denied."""
        guard = PermissionGuard("product:write")
        with pytest.raises(PermissionDeniedException):
            guard(_make_conn(mock_customer_payload), None)

    def test_no_user_raises_not_authorized(self):
        """Missing user in scope should raise NotAuthorizedException."""
        guard = PermissionGuard("product:read")
        with pytest.raises(NotAuthorizedException):
            guard(_make_conn(None), None)

    def test_multiple_perms_all_required(self, mock_customer_payload):
        """All required permissions must be present."""
        guard = PermissionGuard(["product:read", "order:create"])
        guard(_make_conn(mock_customer_payload), None)

    def test_multiple_perms_partial_match_fails(self, mock_customer_payload):
        """Partial permission match should fail."""
        guard = PermissionGuard(["product:read", "user:delete"])
        with pytest.raises(PermissionDeniedException):
            guard(_make_conn(mock_customer_payload), None)

    def test_string_input_works(self):
        """Single string permission should work like list of one."""
        guard = PermissionGuard("system:all")
        user = {"sub": "a", "roles": [], "perms": ["system:all"]}
        guard(_make_conn(user), None)
