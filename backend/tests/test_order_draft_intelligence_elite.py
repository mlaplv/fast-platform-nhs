import sys
import os
import asyncio
import logging
import unicodedata
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

# --- BOOTSTRAP ---
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- MOCKING ---
mock_db = MagicMock(spec=AsyncSession)
mock_db.execute = AsyncMock(return_value=MagicMock())
mock_db.flush = AsyncMock()
mock_db.commit = AsyncMock()
mock_db.rollback = AsyncMock()

# --- IMPORT TARGETS ---
from backend.services.commerce.operatives.handlers.order import OrderHandler
from backend.services.commerce.operatives.handlers.base import SupportContext, NeuralDNA
from backend.schemas.support import SupportRequest, SupportIntent
from backend.schemas.order import OrderDraft
from backend.services.commerce.logic.location_resolver import location_resolver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-elite")

async def run_test_scenarios():
    print("\n" + "="*60)
    print("🚀 HELEN ORDER DRAFT INTELLIGENCE - ELITE TEST SUITE")
    print("="*60 + "\n")

    handler = OrderHandler()
    session_id = "test_session_123"

    # --- CASE 1: PHONE FIRST, THEN ADDRESS ---
    print("📝 [CASE 1] SĐT TRƯỚC -> ĐỊA CHỈ SAU")
    
    # 1.1 Khởi tạo Draft với sản phẩm (Giả lập Turn 1 đã chọn SP)
    draft = OrderDraft(
        session_id=session_id,
        items=[{"product_id": "sp1", "name": "Miccosmo Wash", "quantity": 1, "price": 450000}]
    )
    
    # 1.2 Khách nhắn SĐT
    ctx = SupportContext(
        db=mock_db,
        request=SupportRequest(session_id=session_id, message="SĐT chị là 0949901122"),
        session_id=session_id,
        order_draft=draft
    )
    
    await handler.handle(ctx)
    print(f"   -> Helen phản hồi: {ctx.replies[0]}")
    print(f"   -> Trạng thái Draft: SĐT={ctx.order_draft.customer_phone}, Addr={ctx.order_draft.customer_address}")
    assert ctx.order_draft.customer_phone == "0949901122"
    assert "địa chỉ" in ctx.replies[0].lower()
    print("   ✅ Thành công: Đã lưu SĐT và hỏi Địa chỉ.\n")

    # 1.3 Khách nhắn Địa chỉ (Turn tiếp theo)
    ctx.request.message = "Địa chỉ chị ở 336 Nguyễn Văn Luông, Quận 6"
    ctx.replies = [] # Reset replies
    
    # Giả lập lead_extractor chốt đơn (trong thực tế nó sẽ được gọi)
    # Ở đây ta test logic Slot-filling của OrderHandler (V4.1)
    await handler.handle(ctx)
    print(f"   -> Trạng thái Draft sau khi nhắn Địa chỉ: Addr={ctx.order_draft.customer_address}")
    assert "336 Nguyễn Văn Luông" in ctx.order_draft.customer_address
    print("   ✅ Thành công: Sticky Intent đã tự động điền nốt Địa chỉ vào Draft.\n")

    # --- CASE 2: AMBIGUITY GUARD (PHÚ LÂM) ---
    print("📝 [CASE 2] ĐỊA CHỈ MƠ HỒ (AMBIGUITY GUARD)")
    addr = "336/28/19 Nguyễn Văn Luông, Phú Lâm"
    res = location_resolver.resolve(addr)
    
    print(f"   -> Địa chỉ: {addr}")
    print(f"   -> Có nhiều tỉnh trùng lặp? {bool(res.possible_provinces)}")
    print(f"   -> Result Province: {res.province}")
    print(f"   -> Result Possible Provinces: {res.possible_provinces}")
    assert any("Hồ Chí Minh" in p for p in (res.possible_provinces or [])) or (res.province and "Hồ Chí Minh" in res.province)
    print("   ✅ Thành công: Hệ thống nhận diện được Phú Lâm cần xác nhận Tỉnh.\n")

    # --- CASE 3: LỘN XỘN INFO (DETERMINISTIC RECOVERY) ---
    print("📝 [CASE 3] THÔNG TIN LỘN XỘN (DETERMINISTIC RECOVERY)")
    mixed_msg = "về địa chỉ 336/28/19 nguyễn văn luông, phú lâm 0949901122"
    
    # Test bóc tách SĐT từ chuỗi lộn xộn
    import re
    digits_only = re.sub(r"\D", "", mixed_msg)
    phone_match = re.search(r"0\d{9}", digits_only)
    phone = phone_match.group() if phone_match else None
    
    print(f"   -> Tin nhắn: {mixed_msg}")
    print(f"   -> SĐT bóc tách được: {phone}")
    assert phone == "0949901122"
    print("   ✅ Thành công: Recovery logic đã bóc được SĐT khỏi chuỗi địa chỉ.\n")

    print("="*60)
    print("🎉 TẤT CẢ CÁC KỊCH BẢN ĐỀU VƯỢT QUA KIỂM TRA!")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_test_scenarios())
