import logging
import json
from typing import List, Optional, Dict, cast
from pydantic import BaseModel, Field
from pydantic_ai import Agent # type: ignore
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge # type: ignore

import redis.asyncio as _redis # type: ignore
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.commerce import ProductBase, ProductVariant # type: ignore
from backend.database.models.promotion import Voucher # type: ignore
from backend.services.commerce.promotion import PromotionService
from sqlalchemy.orm.attributes import flag_modified
import os

logger = logging.getLogger("api-gateway")

class SuggestedProduct(BaseModel):
    id: str
    name: str
    reason: str

class DiagnosticReport(BaseModel):
    severity: str = Field(description="Mức độ biểu hiện: ví dụ Nhẹ, Trung bình, Nặng")
    analysis: str = Field(description="Phân tích chuyên sâu (Bao gồm Điểm đau và Khuếch đại điểm đau)")
    reasoning: str = Field(description="Tổng quan lập luận y khoa: Phân tích Giải pháp Placenta Nhật Bản và thành phần chính giải quyết điểm đau thực tế")
    recommendation: str = Field(description="Giải pháp thực tế, gợi ý gói combo và khuyến mãi (tiếng Việt)")
    suggested_products: List[SuggestedProduct] = Field(description="Danh sách sản phẩm gợi ý")
    quantity: int = Field(description="Số lượng sản phẩm khách cần mua (không tính quà tặng)")
    promotion_label: Optional[str] = Field(description="Nhãn khuyến mãi phù hợp nhất từ hệ thống")
    points_earned: int = Field(description="Số điểm tích lũy dự kiến (100k = 1 điểm)")

class DiagnosticAgent:
    """Elite V2.2: AI Diagnostic Agent using TrinityBridge (Dynamic Data Edition)."""
    def __init__(self, redis_client: Optional[_redis.Redis] = None):
        self.redis = redis_client

    async def analyze(self, db_session: AsyncSession, product_name: str, quiz_data: List[Dict[str, str]]) -> Optional[DiagnosticReport]:
        """Viral 2026: Agentic Clinical Analysis via Centralized Bridge with Real System Data."""
        try:
            # 1. Fetch Product & Real-time Variants (Combos & Pricing)
            query = select(ProductBase).where(ProductBase.name == product_name)
            product = (await db_session.execute(query)).scalar_one_or_none()
            if not product:
                logger.error(f"[DiagnosticAgent] Product not found: {product_name}")
                return None

            base_price = product.discount_price if product.discount_price is not None else product.price
            product_instructions = "Thoa nhẹ và massage đều cho đến khi thẩm thấu."
            ingredients_text = "Giải pháp cốt lõi: Placenta Nhật Bản (Ức chế melanin, tái tạo tế bào gốc)."
            
            if product.product_metadata:
                product_instructions = product.product_metadata.get("instructions", product_instructions)
                featured_ingredients = product.product_metadata.get("featured_ingredients", [])
                if featured_ingredients:
                    ingredients_text += " Kết hợp cùng: " + ", ".join([f"{ing.get('name')}" for ing in featured_ingredients])
            
            v_list = []
            
            # Fetch Combo Deals dynamically from PromotionService
            combo_deals = await PromotionService.get_active_combo_deals(db_session)
            for deal in combo_deals:
                cond = deal.condition_payload or {}
                if product.id in cond.get("product_ids", []):
                    if deal.type == "BUY_X_GET_Y":
                        buy_qty = int(cond.get("buy_qty", 1))
                        get_qty = int((deal.reward_payload or {}).get("get_qty", 1))
                        v_list.append(f"- Ưu đãi {deal.name}: Mua {buy_qty} tặng {get_qty}")
                    elif deal.type == "BUNDLE_PRICE":
                        qty = int(cond.get("qty", 1))
                        bundle_price = float((deal.reward_payload or {}).get("price", 0))
                        v_list.append(f"- {deal.name}: Combo {qty} sản phẩm chỉ với {bundle_price:,.0f}đ")
            
            v_query = select(ProductVariant).where(ProductVariant.product_base_id == product.id)
            variants = (await db_session.execute(v_query)).scalars().all()
            if variants:
                for v in variants:
                    v_qty = v.attributes.get('combo_qty') or v.attributes.get('comboQty') or 1
                    v_gifts = v.attributes.get('gifts', [])
                    gift_str = ", ".join([f"Tặng {g.get('qty')} {g.get('name')}" for g in v_gifts]) if v_gifts else "Không quà"
                    
                    unit_price = v.discount_price if v.discount_price is not None else v.price
                    total_price = unit_price * v_qty
                    
                    v_list.append(f"- Gói {v_qty} sản phẩm: Tổng {total_price:,.0f}đ ({gift_str})")
            
            if not v_list:
                v_list.append(f"- Giá bán lẻ: {base_price:,.0f}đ")
                
            variants_text = "\n".join(v_list)
                
            # 🚀 Elite Persistent Counter Increment (R00: Honesty Protocol)
            try:
                if not product.product_metadata:
                    product.product_metadata = {}
                
                # Persistent field check
                current_count = product.product_metadata.get("diagnostics_count")
                if current_count is None:
                    # Baseline from .envSSOT
                    try:
                        env_base = int(os.getenv("PUBLIC_G_BY_COUNT", "569"))
                    except (ValueError, TypeError):
                        env_base = 500
                    current_count = env_base * 5
                
                product.product_metadata["diagnostics_count"] = int(current_count) + 1
                flag_modified(product, "product_metadata")
                await db_session.commit()
                logger.info(f"[DiagnosticAgent] Persistent counter incremented for {product_name}: {current_count + 1}")
            except Exception as ex:
                logger.error(f"[DiagnosticAgent] Counter sync failed: {ex}")
                await db_session.rollback()

            # 2. Extract Target Area for specialized advice
            target_area = "vùng da nhạy cảm"
            for q in quiz_data:
                if q.get('id') == 'q1' or 'vùng' in q.get('title', '').lower():
                    target_area = q.get('label') or q.get('value') or target_area
                    break

            # 3. Fetch Active Vouchers (Dynamic Offers)
            voucher_query = select(Voucher).where(Voucher.is_active == True)
            vouchers = (await db_session.execute(voucher_query)).scalars().all()
            vouchers_text = "Hiện chưa có mã giảm giá khả dụng."
            if vouchers:
                vouchers_text = "\n".join([
                    f"- Code {v.id}: {v.title} (Giảm {v.value:,.0f}{'%' if v.type=='PERCENT' else 'đ'}, áp dụng cho đơn từ {v.min_spend:,.0f}đ)" 
                    for v in vouchers
                ])

            agent = Agent(
                output_type=DiagnosticReport,
            )
            
            system_prompt = (
                f"Bạn là Chuyên gia Chẩn đoán Lâm sàng Elite 2026.\n"
                "Nhiệm vụ: Thiết lập PHÁC ĐỒ ĐIỀU TRỊ CHUYÊN SÂU dựa trên phân tích sinh lý học da.\n\n"
                "KIẾN THỨC CHUYÊN GIA CHO TỪNG VÙNG (EXPERT KNOWLEDGE):\n"
                "- VÙNG BIKINI: Khu vực có độ pH đặc thù và chịu áp lực ma sát lớn từ trang phục. Cần áp dụng các kỹ thuật nâng cao giúp cân bằng độ pH và khôi phục hệ vi sinh tự nhiên của vùng kín.\n"
                "- VÙNG NÁCH: Khu vực thường xuyên chịu tổn thương cơ học do CẠO, WASH, NHỔ lông và các tác động hóa học từ việc lạm dụng HÓA CHẤT, LĂN NÁCH, THUỐC XỊT KHỬ MÙI. Những yếu tố này phá hủy hàng rào bảo vệ da (skin barrier), gây viêm nang lông và hình thành các vùng da TỐI MÀU. Cần ưu tiên làm dịu và phục hồi các vi tổn thương trước khi tiến hành dưỡng sáng chuyên sâu.\n"
                "- VÙNG NHŨ HOA: Niêm mạc cực kỳ mỏng manh và nhạy cảm. Cần một liệu pháp chuyên sâu để khôi phục sắc tố hồng hào và độ sáng mịn cho khu vực này một cách an toàn tuyệt đối, kích thích vi tuần hoàn tự nhiên.\n"
                "- VÙNG ĐÙI TRONG: Tình trạng DÀY SỪNG NHẸ (stratum corneum) thường xảy ra do ma sát liên tục khi vận động. Cần chú trọng các bước làm mềm biểu bì trước khi tiến hành dưỡng sáng chuyên sâu vào bên dưới tế bào hắc tố.\n\n"
                f"DỮ LIỆU THỰC TẾ (SSOT):\n"
                f"- Khu vực mục tiêu: {target_area}\n"
                f"- Thành phần nổi bật: {ingredients_text}\n"
                f"- Combo khả dụng:\n{variants_text}\n"
                f"- Voucher & Tích điểm: {vouchers_text} | 100k = 1 điểm.\n\n"
                "QUY TẮC TÁC PHONG (CLINICAL ETIQUETTE):\n"
                "1. QUY TRÌNH PHÂN TÍCH (Trường 'analysis'): Trình bày mạch lạc thành MỘT ĐOẠN VĂN DUY NHẤT (không dùng gạch đầu dòng hay ký tự đặc biệt). TUYỆT ĐỐI KHÔNG xuất ra các từ khóa cứng nhắc như 'Điểm đau:', 'Khuếch đại:'. Bắt đầu trực tiếp vào phân tích, TUYỆT ĐỐI KHÔNG chào hỏi (như 'Chào bạn', 'Xin chào'). Lời văn tự nhiên, lồng ghép các yếu tố:\n"
                "   - Chỉ ra chính xác vấn đề thực tế khách hàng đang gặp tại khu vực mục tiêu một cách tinh tế.\n"
                "   - Nêu rõ hậu quả nếu không xử lý kịp thời (Đảm bảo hợp lý thực tế. Tuyệt đối KHÔNG dùng ngữ cảnh sai lệch như 'diện trang phục hở' khi nói về vùng nhạy cảm như Bikini).\n"
                "2. TỔNG QUAN THÀNH PHẦN (Trường 'reasoning'): Trình bày NGẮN GỌN SÚC TÍCH (tối đa 2-3 câu), tuyệt đối KHÔNG dài dòng thừa thãi. Đánh thẳng vào cách ƯU TIÊN HÀNG ĐẦU LÀ PLACENTA NHẬT BẢN kết hợp với các hoạt chất phụ trợ khắc phục trực tiếp Điểm Đau trong hoàn cảnh môi trường của khách.\n"
                "3. ĐIỂM BÁN HÀNG FOMO (SELLING POINTS): Gợi ý trực tiếp các gói COMBO phù hợp cùng với Voucher. Phải tạo tính cấp bách (ví dụ: 'số lượng có hạn', 'chỉ áp dụng hôm nay'), nhấn mạnh lợi ích tiết kiệm thực tế để khách hàng chốt đơn.\n"
                "4. LỆNH CẤM (STRICT BANS): TUYỆT ĐỐI CẤM hướng dẫn chi tiết cách sử dụng, cách thoa sản phẩm. TUYỆT ĐỐI CẤM tâng bốc quá lố không thực tế. TUYỆT ĐỐI CẤM dùng các từ giao tiếp dư thừa (như 'Chào bạn', 'Dạ chào bạn'). Phải đi thẳng vào chuyên môn.\n"
                "5. NGÔN NGỮ ELITE: KHÔNG dùng các từ thô cứng như 'sạm', 'thâm đen', 'sơ cứng', 'thô ráp'. Hãy dùng: 'Khu vực tối màu', 'Kém rạng rỡ', 'Sự tập trung hắc tố', 'Kết cấu da kém mịn màng', 'Tình trạng dày sừng nhẹ'.\n"
                "6. ĐỊNH DẠNG PHÁC ĐỒ (Trường 'recommendation'): Trình bày theo định dạng 1. 2. 3. (TUYỆT ĐỐI KHÔNG dùng ký tự markdown như ** hay #. KHÔNG in ra từ khóa FOMO). Ví dụ:\n"
                "   1. Giải pháp chuyên sâu: [Đưa ra giải pháp hữu dụng trong hoàn cảnh thực tế của khách hàng, giải quyết triệt để vấn đề].\n"
                "   2. Liệu trình tối ưu: [Đề xuất chi tiết gói combo và voucher, nêu bật tính cấp thiết và quyền lợi đặc biệt để chốt đơn ngay].\n"
                "   3. TRANG PHỤC VÀ LỐI SỐNG: Ưu tiên nội y thông thoáng, tránh mặc đồ quá chật gây cản trở lưu thông máu và tạo ma sát gây tình trạng tập trung hắc tố.\n"
                "7. KHÔNG HALLUCINATE: Chỉ dùng dữ liệu Combo, Voucher từ SSOT.\n\n"
                "PHONG THÁI: Một chuyên gia chẩn đoán tận tâm, tinh tế, am tường khoa học da liễu và thấu hiểu khách hàng."
            )

            prompt = f"Dữ liệu khảo sát khách hàng (Quiz Data): {json.dumps(quiz_data, ensure_ascii=False)}"
            
            # Utilize the centralized bridge for military-grade stability
            result = await trinity_bridge.run(
                agent=agent,
                prompt=prompt,
                system_prompt=system_prompt,
                role="fast", 
                timeout=45.0,
                per_model_timeout=12.0
            )
            
            if result:
                return cast(DiagnosticReport, result)
            return None
            
        except Exception as e:
            logger.error(f"[DiagnosticAgent] Fatal Error: {e}")
            return None
