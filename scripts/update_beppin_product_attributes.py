import asyncio
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))

from backend.database.alchemy_config import alchemy_config
from backend.database.models.commerce import ProductBase
from sqlalchemy import select

async def main():
    async_session = alchemy_config.create_session_maker()
    async with async_session() as session:
        # Tìm sản phẩm Beppin Body
        stmt = select(ProductBase).where(ProductBase.name.like("%Beppin Body%"))
        res = await session.execute(stmt)
        products = res.scalars().all()
        
        if not products:
            print("Không tìm thấy sản phẩm Beppin Body nào trong Database!")
            return
            
        for product in products:
            print(f"Đang cập nhật sản phẩm: {product.name} (ID: {product.id})")
            
            # Khởi tạo hoặc cập nhật attributes
            attrs = product.attributes or {}
            attrs.update({
                "bao_bi": "Tuýp nhựa mềm màu trắng nằm ngang",
                "nap": "Nắp vặn hình trụ dẹt màu trắng ở đáy tuýp (bottom cap), không phải nắp bật",
                "dau_lay_san_pham": "Đầu vòi nhỏ nhọn (pointed nozzle tip)",
                "the_chat_san_pham": "Gel serum màu hồng nhạt (pink-tinted gel-serum)"
            })
            product.attributes = attrs
            
            # Cập nhật thông số bao bì vào cuối mô tả ngắn để đảm bảo LLM luôn đọc được
            packaging_specs = (
                "\n\n[THÔNG SỐ BAO BÌ VẬT LÝ]:\n"
                "- Dạng bao bì: Tuýp nhựa mềm màu trắng nằm ngang.\n"
                "- Loại nắp: Nắp vặn hình trụ dẹt màu trắng ở đáy tuýp (bottom cap), không phải nắp bật.\n"
                "- Đầu lấy sản phẩm: Đầu vòi nhỏ nhọn (pointed nozzle tip).\n"
                "- Thể chất sản phẩm: Gel serum màu hồng nhạt."
            )
            
            if "THÔNG SỐ BAO BÌ VẬT LÝ" not in (product.short_description or ""):
                product.short_description = (product.short_description or "") + packaging_specs
            if "THÔNG SỐ BAO BÌ VẬT LÝ" not in (product.description or ""):
                product.description = (product.description or "") + packaging_specs
                
            session.add(product)
            print(f"Cập nhật thành công attributes & description cho: {product.name}")
            
        await session.commit()
        print("Đã commit toàn bộ thay đổi vào Database!")

if __name__ == "__main__":
    asyncio.run(main())
