import asyncio
import logging
import re
from typing import Optional
from pydantic import BaseModel

# Mock the context structures
class MockProductInfo(BaseModel):
    name: str
    price: float
    price_display: str

class MockSupportContext:
    def __init__(self, price_display: str, price: float, cart_text: str):
        self.p_info = MockProductInfo(name="Combo Trắng Sáng Beppin", price=price, price_display=price_display)
        self.cart_text = cart_text

# Import the exact logic to verify
from backend.services.commerce.operatives.support_agent import _validate_grounding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-shield")

async def run_tests():
    # Setup test context
    ctx = MockSupportContext(
        price_display="350.000đ",
        price=350000.0,
        cart_text="[GIỎ HÀNG THỰC TẾ]:\n- Combo Trắng Sáng Beppin: 350.000đ\n- Mã KM áp dụng: Mã BEPPIN50K"
    )

    logger.info("🧪 Test 1: Anti-Delusion on Transactional Claims")
    delusion_reply = "Chào chị, đơn hàng của chị đã hủy đơn hàng trên hệ thống rồi ạ. Em đã hoàn tiền cho mình rồi nhé!"
    grounded_reply_1 = _validate_grounding(delusion_reply, ctx)
    logger.info(f"BEFORE: {delusion_reply}")
    logger.info(f"AFTER : {grounded_reply_1}")
    
    # Assert that the delusional completed claims are shifted to "Helen đã ghi nhận yêu cầu"
    assert "đã hủy đơn hàng trên hệ thống rồi" not in grounded_reply_1
    assert "đã hoàn tiền" not in grounded_reply_1
    assert "Helen đã ghi nhận" in grounded_reply_1
    assert "gửi bộ phận CSKH xử lý" in grounded_reply_1

    logger.info("\n🧪 Test 2: Anti-Hallucination on Prices")
    fake_price_reply = "Dạ Combo Trắng Sáng Beppin này giá chỉ còn 120.000đ khi mua lẻ ạ, chị đặt ngay nhé!"
    grounded_reply_2 = _validate_grounding(fake_price_reply, ctx)
    logger.info(f"BEFORE: {fake_price_reply}")
    logger.info(f"AFTER : {grounded_reply_2}")
    assert "120.000" not in grounded_reply_2
    assert "350.000đ" in grounded_reply_2

    logger.info("\n🧪 Test 3: Anti-Hallucination on Voucher Codes")
    fake_voucher_reply = "Chị nhớ nhập mã FAKE99K hoặc mã BEPPIN50K để nhận thêm ưu đãi khủng nha."
    grounded_reply_3 = _validate_grounding(fake_voucher_reply, ctx)
    logger.info(f"BEFORE: {fake_voucher_reply}")
    logger.info(f"AFTER : {grounded_reply_3}")
    assert "FAKE99K" not in grounded_reply_3
    assert "BEPPIN50K" in grounded_reply_3

    logger.info("\n🟢 ALL ADVANCED SHIELD TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_tests())
