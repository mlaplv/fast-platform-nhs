import pytest
from unittest.mock import AsyncMock, patch
import httpx
from backend.services.ads_protection.ai_strategist import ai_strategist

@pytest.mark.asyncio
async def test_boilerplate_stripper():
    # Complex mock HTML with headers, footers, scripts, styles, sidebars, and actual content
    mock_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Sản Phẩm Trị Thâm Beppin Body Nhật Bản</title>
        <meta name="description" content="Kem trị thâm nách bẹn mông Nhật Bản dưỡng sáng da toàn thân tự nhiên">
        <link rel="canonical" href="https://xohi.vn/pages/kem-duong-phuc-hoi-body">
        <style>
            body { background: #000; color: #fff; }
            .sidebar { width: 300px; float: left; }
        </style>
        <script>
            console.log("Tracking script or ads library");
        </script>
    </head>
    <body>
        <header class="site-header-container">
            <nav id="main-navigation">
                <ul>
                    <li><a href="/">Trang chủ</a></li>
                    <li><a href="/about">Giới thiệu</a></li>
                </ul>
            </nav>
        </header>

        <div class="main-layout">
            <aside class="sidebar-wrapper" id="left-sidebar">
                <h3>Danh mục</h3>
                <ul>
                    <li>Sản phẩm bán chạy</li>
                    <li>Khuyến mãi</li>
                </ul>
            </aside>

            <main class="content-body">
                <h1>Kem Dưỡng Beppin Body Phục Hồi Sáng Da Toàn Thân</h1>
                <p>Sản phẩm này chứa chiết xuất tự nhiên an toàn lành tính, dưỡng sáng da hiệu quả cho mọi loại da.</p>
                <img src="/img/beppin.jpg" alt="Beppin Body Nhật Bản">
            </main>
        </div>

        <footer class="footer-layout" id="main-footer">
            <p>&copy; 2026 Xohi Cosmetic. Toàn quyền bảo lưu.</p>
        </footer>
    </body>
    </html>
    """

    mock_response = httpx.Response(
        status_code=200,
        content=mock_html.encode("utf-8"),
        request=httpx.Request("GET", "https://xohi.vn/pages/kem-duong-phuc-hoi-body")
    )

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        # Trigger the fetch page method
        audit_report = await ai_strategist._fetch_page("https://xohi.vn/pages/kem-duong-phuc-hoi-body")

        # Verify that boilerplate has been stripped and target content is parsed correctly
        assert "Sản Phẩm Trị Thâm Beppin Body Nhật Bản" in audit_report
        assert "Kem Dưỡng Beppin Body Phục Hồi Sáng Da Toàn Thân" in audit_report
        
        # Verify that header/footer navigation lists and scripts are excluded from the main preview text
        assert "Trang chủ" not in audit_report
        assert "Giới thiệu" not in audit_report
        assert "Danh mục" not in audit_report
        assert "Toàn quyền bảo lưu" not in audit_report
        assert "Tracking script" not in audit_report
