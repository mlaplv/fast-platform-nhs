import asyncio
import logging
import sys

# Elite V2.2: Transparent Logging for Debugging
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s - %(asctime)s - %(name)s - %(message)s",
    stream=sys.stdout
)

from backend.services.xohi.creative_studio.operatives.surgeon_booster import run_surgeon_boost

async def test():
    content = """
    <h1>Cách chăm sóc da mặt chuẩn chuyên gia</h1>
    <p>Chăm sóc da mặt là quy trình quan trọng để duy trì vẻ đẹp và sự tươi trẻ. Bạn cần thực hiện đúng các bước để đạt hiệu quả tốt nhất.</p>
    <h2>Bước 1: Làm sạch da</h2>
    <p>Sử dụng sữa rửa mặt phù hợp để loại bỏ bụi bẩn và dầu thừa.</p>
    <h2>Bước 2: Dưỡng ẩm</h2>
    <p>Kem dưỡng ẩm giúp da luôn mịn màng và không bị khô ráp.</p>
    """
    topic = "Chăm sóc da mặt"
    
    print("Running Surgeon Booster...")
    result = await run_surgeon_boost(content, topic)
    
    print(f"Summary: {result.summary}")
    print(f"Patches found: {len(result.patches)}")
    for i, patch in enumerate(result.patches):
        print(f"Patch {i+1}:")
        print(f"  Rationale: {patch.rationale}")
        print(f"  Search: {patch.search_string[:50]}...")
        print(f"  Replace: {patch.new_text[:50]}...")
    
    print("\nLogs:")
    for log in result.logs:
        print(f"  - {log}")

if __name__ == "__main__":
    asyncio.run(test())
