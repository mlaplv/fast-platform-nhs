import sys
import os
import asyncio

# Add backend to path
sys.path.append(os.getcwd())

from backend.services.commerce.price_agent import detect_ad_type

def investigate():
    # Real data from miccosmo.vn organic result
    link = "https://miccosmo.vn/beppin-body-virgin-white-serum-giai-phap-lam-hong-vung-kin-nhay-cam-den-tu-nhat-ban-n161850.html"
    snippet = "BEPPIN BODY VIRGIN WHITE SERUM: Giải Pháp Làm Hồng Vùng Kín Nhạy Cảm Đến Từ Nhật Bản. Beppin Body Virgin White Serum là dòng sản phẩm chăm sóc vùng kín cao cấp của Miccosmo Nhật Bản..."
    pagemap = {
        "metatags": [{"og:title": "BEPPIN BODY VIRGIN WHITE SERUM..."}],
        "cse_thumbnail": [{"src": "..."}]
    }
    
    is_ad, ad_type = detect_ad_type(link, snippet, pagemap)
    print(f"Link: {link}")
    print(f"Snippet: {snippet}")
    print(f"Is Ad: {is_ad}, Type: {ad_type}")

if __name__ == "__main__":
    investigate()
