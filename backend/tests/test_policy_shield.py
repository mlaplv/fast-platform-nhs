import pytest
from unittest.mock import patch, AsyncMock
from backend.services.ads_protection.policy_shield import policy_shield

@pytest.mark.asyncio
async def test_policy_shield_sensitive_terms():
    # Test sensitive body parts
    res = await policy_shield.validate(
        headlines=["Kem trị thâm nhũ hoa hiệu quả"],
        descriptions=["Chăm sóc da vùng ngực nhạy cảm."],
        keywords=["kem trị thâm nhũ hoa"],
        landing_page_url=""
    )
    
    assert res["status"] == "RISKY"
    assert len(res["sensitive_warnings"]) > 0
    matched_terms = [w["matched_term"] for w in res["sensitive_warnings"]]
    assert "nhũ hoa" in matched_terms

@pytest.mark.asyncio
async def test_policy_shield_medical_claims():
    # Test restricted medical claims / overpromising
    res = await policy_shield.validate(
        headlines=["Đặc trị mụn dứt điểm 100%"],
        descriptions=["Thuốc trị mụn tốt nhất hiện nay."],
        keywords=["thuốc đặc trị mụn"],
        landing_page_url=""
    )
    
    assert res["status"] == "RISKY"
    sensitive_categories = [w["category"] for w in res["sensitive_warnings"]]
    assert "Tuyên bố y tế / Cam kết chữa trị" in sensitive_categories
    assert "Cam kết hiệu quả thái quá" in sensitive_categories

@pytest.mark.asyncio
async def test_policy_shield_cross_matching_mismatch():
    # Test cross-matching with mock cosmetic landing page
    # If the landing page contains cosmetic terms, but keywords have medical claim terms
    with patch("backend.services.ads_protection.ai_strategist.ai_strategist._fetch_page", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = "=== LANDING PAGE CONTENT PREVIEW ===\nMỹ phẩm kem dưỡng lành tính thiên nhiên\n====================================="
        
        res = await policy_shield.validate(
            headlines=["Kem dưỡng trắng hồng"],
            descriptions=["Sản phẩm an toàn lành tính."],
            keywords=["thuốc trị thâm nhũ hoa"],
            landing_page_url="https://example.com/cosmetics-page"
        )
        
        # We expect warnings about concept mismatch because keyword has "thuốc" / "trị"
        assert len(res["landing_page_warnings"]) > 0
        warning_types = [w["type"] for w in res["landing_page_warnings"]]
        assert "MISMATCH_CONCEPT" in warning_types or "MISMATCH_MISSING" in warning_types

@pytest.mark.asyncio
async def test_policy_shield_low_volume_words():
    # Test low search volume detection for extra-long keywords (> 6 words)
    res = await policy_shield.validate(
        headlines=["Kem dưỡng trắng da"],
        descriptions=["Sản phẩm dịu nhẹ thiên nhiên."],
        keywords=["kem dưỡng trắng da ban đêm cho da dầu mụn hiệu quả"],
        landing_page_url=""
    )
    
    assert len(res["low_volume_warnings"]) > 0
    assert "kem dưỡng trắng da ban đêm cho da dầu mụn hiệu quả" in res["low_volume_warnings"][0]["keyword"]
    assert "Lượng tìm kiếm thấp" in res["low_volume_warnings"][0]["message"]
