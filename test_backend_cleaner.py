import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parents[0]))

from backend.utils.noise_cleaner import NoiseCleaner
import logging
import time

# Setup logging
logging.basicConfig(level=logging.DEBUG)

def test_aggressive_clean():
    cleaner = NoiseCleaner()
    
    sample_html = """
    <h1><strong><br></strong></h1>
    <img src="https://nhathuochongson.com/uploads/images/banner-21.jpg" alt="nhà thuốc hồng sơn" width="100%" class="max-w-full mx-auto my-4 shadow-lg flex">
    <h2><strong>Thuốc Đặc Trị Hôi Nách Hồng Sơn (Lọ Lớn 20Ml)</strong></h2>
    <p></p>
    <img src="https://nhathuochongson.com/uploads/images/nach-hs-pp_1587359669.jpg" alt="Đặc trị hôi nách Hồng Sơn" class="max-w-full mx-auto my-4 shadow-lg flex">
    <p><a target="_blank" rel="noopener noreferrer nofollow" class="text-blue-400 underline hover:text-blue-300 transition-colors cursor-pointer" href="https://nhathuochongson.com/thuoc-dac-tri-hoi-nach" title="Thuốc đặc trị hôi nách Hồng Sơn"><span style="color: rgb(0, 0, 0);"><strong>Thuốc đặc&nbsp;trị hôi nách Hồng Sơn</strong></span></a>&nbsp;đã được đăng ký mã vạch trích xuất nguồn gốc sản phẩm, có tem chống hàng giả, tem tròn của bộ công an.&nbsp;Thuốc dạng xịt, thẩm thấu tốt, nhanh khô th
    """

    print("--- ORIGINAL CONTENT ---")
    # print(sample_html)
    
    cleaned = asyncio.run(cleaner.clean(sample_html, mode="aggressive"))
    
    print("\n--- CLEANED CONTENT ---")
    print(cleaned)

    # Assertions
    # Check if empty H1/Strong block is gone
    is_h1_gone = "<h1>" not in cleaned
    is_empty_p_gone = "<p></p>" not in cleaned
    
    print(f"\nResults:")
    print(f"- Empty H1 gone: {is_h1_gone}")
    print(f"- Empty P gone: {is_empty_p_gone}")

    if is_h1_gone and is_empty_p_gone:
        print("\n✅ Expert Mode Cleaning TEST PASSED!")
    else:
        print("\n❌ Expert Mode Cleaning TEST FAILED!")

def test_performance():
    cleaner = NoiseCleaner()
    large_content = "Vâng, đây là bài viết về sức khỏe. " + "Thuốc đặc trị hôi nách Hồng Sơn " * 500
    
    print("\n--- PERFORMANCE TEST (5000+ words) ---")
    start = time.time()
    cleaned = asyncio.run(cleaner.clean(large_content, mode="aggressive"))
    duration = time.time() - start
    
    print(f"Duration: {duration:.4f}s")
    print(f"Cleaned length: {len(cleaned)}")
    
    if duration < 0.5:
        print("✅ PERFORMANCE TEST PASSED! (< 0.5s)")
    else:
        print("❌ PERFORMANCE TEST FAILED! (> 0.5s)")

if __name__ == "__main__":
    test_aggressive_clean()
    test_performance()
