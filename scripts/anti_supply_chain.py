import os
import sys
import site
from pathlib import Path

def check_malicious_pth():
    """
    Check for 'litellm_init.pth' in site-packages and other potential locations.
    This file was used in the March 2026 LiteLLM supply chain attack to maintain persistence.
    """
    print("🔍 [SECURITY] Đang quét dấu hiệu mã độc LiteLLM (March 2024 attack)...")
    
    # 1. Check all site-packages
    locations = site.getsitepackages()
    if hasattr(site, 'getusersitepackages'):
        locations.append(site.getusersitepackages())
    
    malicious_found = False
    for loc in locations:
        pth_path = Path(loc) / "litellm_init.pth"
        if pth_path.exists():
            print(f"❌ [ALERT] Phát hiện tệp độc hại: {pth_path}")
            try:
                pth_path.unlink()
                print(f"✅ [CLEAN] Đã xóa tệp độc hại: {pth_path}")
            except Exception as e:
                print(f"🚨 [ERROR] Không thể xóa tệp! Hãy can thiệp thủ công: {e}")
            malicious_found = True
            
    # 2. Check current project venv
    venv_site = Path(".venv/lib/python3.13/site-packages")
    if venv_site.exists():
        pth_path = venv_site / "litellm_init.pth"
        if pth_path.exists():
            print(f"❌ [ALERT] Phát hiện tệp độc hại trong .venv: {pth_path}")
            pth_path.unlink()
            print("✅ [CLEAN] Đã dọn dẹp .venv.")
            malicious_found = True

    if not malicious_found:
        print("🎉 [SAFE] Không tìm thấy dấu hiệu mã độc 'litellm_init.pth'. Hệ thống của Sếp hiện tại sạch sẽ!")
    else:
        print("⚠️ [WARNING] Hệ thống đã phát hiện và xử lý tệp độc hại. Sếp NÊN XOAY VÒNG API KEY NGAY LẬP TỨC.")

if __name__ == "__main__":
    check_malicious_pth()
