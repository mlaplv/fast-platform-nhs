import asyncio
import os
import json
import logging
from typing import Any

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neural-test")

# Mocking environment variables if needed, but they should be in the container
# Loading the service
from backend.services.commerce.price_agent import scan_product_price

async def run_test():
    product_name = "Miccosmo Beppin Body Virgin White Serum"
    print(f"\n🚀 [NEURAL RECON V2.6] BẮT ĐẦU KIỂM THỬ TỔNG LỰC: {product_name}\n")
    print("-" * 80)
    
    try:
        # Trigger the Agent
        result = await scan_product_price(product_name)
        
        print("\n✅ [DỮ LIỆU TÌM THẤY]")
        print(f"💰 Giá trung bình: {result.avg_market_price:,.0f} VND" if result.avg_market_price else "💰 Giá trung bình: N/A")
        print(f"💎 Giá thấp nhất: {result.min_market_price:,.0f} VND" if result.min_market_price else "💎 Giá thấp nhất: N/A")
        print(f"📊 Số lượng đối thủ: {result.competitor_count}")
        
        print("\n🌐 [TOP 10 KẾT QUẢ TỰ NHIÊN (ĐÃ QUA NEURAL SCAN)]")
        for i, r in enumerate(result.organic_results):
            price_str = f"{r.price:,.0f} VND" if r.price else "N/A"
            print(f"[{i+1}] {r.platform} | {r.title}")
            print(f"    Giá: {price_str}")
            print(f"    Link: {r.link}")
            print("-" * 40)

        print("\n🧠 [PHÂN TÍCH CHIẾN THUẬT AI]")
        print(f"💡 Tổng quan: {result.analysis_overview}")
        print(f"\n⚠️ Phản biện sắc bén: {result.critical_analysis}")
        print(f"\n🎯 Chiến lược tối ưu: {result.optimization_strategy}")
        
    except Exception as e:
        print(f"❌ LỖI TRONG QUÁ TRÌNH KIỂM THỬ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
