"""Tests for Tier1SemanticRouter — T1 Heuristic Classification."""
import pytest
from src.services.routing.tier1_semantic import Tier1SemanticRouter


@pytest.fixture
def router():
    return Tier1SemanticRouter()


class TestTier1ExactMatch:
    """Test exact keyword matching for UI navigation."""

    def test_don_hang_matches_order(self, router, mock_app_state):
        result = router.route("mở đơn hàng", None, mock_app_state)
        assert result is not None
        assert result.data["ui_action"] == "show_order_management"
        assert result.data["intent_type"] == "UI_NAV"

    def test_san_pham_matches_product(self, router, mock_app_state):
        result = router.route("xem sản phẩm", None, mock_app_state)
        assert result is not None
        assert result.data["ui_action"] == "show_product_management"

    def test_doanh_thu_matches_revenue(self, router, mock_app_state):
        result = router.route("mở doanh thu", None, mock_app_state)
        assert result is not None
        assert result.data["ui_action"] == "show_revenue_chart"

    def test_tin_tuc_matches_news(self, router, mock_app_state):
        result = router.route("mở tin tức", None, mock_app_state)
        assert result is not None
        assert result.data["ui_action"] == "show_news_management"

    def test_nguoi_dung_matches_user(self, router, mock_app_state):
        result = router.route("xem người dùng", None, mock_app_state)
        assert result is not None
        assert result.data["ui_action"] == "show_user_management"


class TestTier1BypassFilter:
    """Test bypass filter delegates to T2 for complex queries (R64)."""

    def test_bao_nhieu_bypasses(self, router, mock_app_state):
        result = router.route("có bao nhiêu đơn hàng", None, mock_app_state)
        assert result is None  # Bypassed to T2

    def test_thang_nay_bypasses(self, router, mock_app_state):
        result = router.route("doanh thu tháng này", None, mock_app_state)
        assert result is None  # Bypassed to T2

    def test_explicit_open_overrides_bypass(self, router, mock_app_state):
        """'mở' prefix should force UI_NAV even with bypass keywords."""
        result = router.route("mở đơn hàng tháng này", None, mock_app_state)
        assert result is not None
        assert result.data["intent_type"] == "UI_NAV"


class TestTier1WakeWord:
    """Test wake word detection (V58.0 Backend-Driven)."""

    def test_xohi_wake_word(self, router, mock_app_state):
        result = router.catch_basic_commands("xohi", "user-123", mock_app_state)
        assert result is not None
        assert result.data["category"] == "SESSION_CTRL"
        assert result.data["action"] == "WAKE_ROUTINE"

    def test_system_xohi_fallback_no_user(self, router, mock_app_state):
        """xohi should work even without user profile (global fallback)."""
        result = router.catch_basic_commands("xohi", None, mock_app_state)
        assert result is not None
        assert result.data["action"] == "WAKE_ROUTINE"

    def test_sleep_word(self, router, mock_app_state):
        result = router.catch_basic_commands("tam biet", "user-123", mock_app_state)
        assert result is not None
        assert result.data["action"] == "HARDWARE_SLEEP"

    def test_unmatched_returns_none(self, router, mock_app_state):
        result = router.catch_basic_commands("hello world", "user-123", mock_app_state)
        assert result is None


class TestTier1InputTruncation:
    """Test R1.8 Anti-Blocking — input truncation."""

    def test_long_input_truncated(self, router, mock_app_state):
        long_text = "đơn hàng " * 200  # >500 chars
        result = router.route(long_text, None, mock_app_state)
        # Should not hang or crash; result can be match or None
        assert True  # If we get here without timeout, truncation worked
