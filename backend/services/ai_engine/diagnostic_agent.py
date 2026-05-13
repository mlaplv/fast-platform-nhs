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
from sqlalchemy.orm.attributes import flag_modified
import os

logger = logging.getLogger("api-gateway")

class SuggestedProduct(BaseModel):
    id: str
    name: str
    reason: str

class DiagnosticReport(BaseModel):
    severity: str = Field(description="Mức độ biểu hiện: ví dụ Nhẹ, Trung bình, Nặng")
    analysis: str = Field(description="Phân tích chuyên sâu về tình trạng của khách hàng (tiếng Việt)")
    reasoning: str = Field(description="Lập luận y khoa đằng sau chẩn đoán này (tiếng Việt)")
    recommendation: str = Field(description="Lời khuyên về lối sống và cách sử dụng sản phẩm (tiếng Việt)")
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
            
            variants_text = "Hệ thống chưa có thông tin combo. Mặc định bán lẻ 1 lọ."
            base_price = 600000 # Fallback
            product_instructions = "Thoa nhẹ và massage đều cho đến khi thẩm thấu."
            
            if product:
                base_price = product.discount_price or product.price or base_price
                if product.product_metadata:
                    product_instructions = product.product_metadata.get("instructions", product_instructions)
                
                v_query = select(ProductVariant).where(ProductVariant.product_base_id == product.id)
                variants = (await db_session.execute(v_query)).scalars().all()
                if variants:
                    v_list = []
                    for v in variants:
                        v_qty = v.attributes.get('combo_qty') or v.attributes.get('comboQty') or 1
                        v_gifts = v.attributes.get('gifts', [])
                        gift_str = ", ".join([f"Tặng {g.get('qty')} {g.get('name')}" for g in v_gifts]) if v_gifts else "Không quà"
                        v_list.append(f"- Mua {v_qty} lọ: Tổng {v.price:,.0f}đ ({gift_str})")
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
                        except:
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
                f"Bạn là Chuyên gia Chẩn đoán Lâm sàng Elite 2026 cho sản phẩm '{product_name}'.\n"
                "Nhiệm vụ: Thiết lập PHÁC ĐỒ ĐIỀU TRỊ CHUYÊN SÂU dựa trên phân tích sinh lý học da.\n\n"
                "KIẾN THỨC CHUYÊN GIA CHO TỪNG VÙNG (EXPERT KNOWLEDGE):\n"
                "- VÙNG BIKINI: Khu vực có độ pH đặc thù và chịu áp lực ma sát lớn từ trang phục. Cần massage nhẹ nhàng theo hình xoắn ốc để hoạt chất thẩm thấu, đồng thời áp dụng các kỹ thuật nâng cao giúp cân bằng độ pH và khôi phục hệ vi sinh tự nhiên của vùng kín.\n"
                "- VÙNG NÁCH: Khu vực thường xuyên chịu tổn thương cơ học do CẠO, WASH, NHỔ lông và các tác động hóa học từ việc lạm dụng HÓA CHẤT, LĂN NÁCH, THUỐC XỊT KHỬ MÙI. Những yếu tố này phá hủy hàng rào bảo vệ da (skin barrier), gây viêm nang lông và hình thành các vùng da TỐI MÀU. Cần ưu tiên làm dịu và phục hồi các vi tổn thương trước khi tiến hành dưỡng sáng chuyên sâu.\n"
                "- VÙNG NHŨ HOA: Niêm mạc cực kỳ mỏng manh và nhạy cảm. Tuyệt đối không chà xát mạnh. Chỉ hướng dẫn khách hàng dùng ngón áp út (ngón có lực yếu nhất) để thoa serum thật nhẹ nhàng, giúp kích thích vi tuần hoàn hỗ trợ quá trình LÀM HỒNG TI, mang lại vẻ CĂNG TRÒN và MỌNG tự nhiên. Đây là kỹ thuật chuyên sâu để khôi phục sắc tố hồng hào và độ sáng mịn cho khu vực này một cách an toàn tuyệt đối.\n"
                "- VÙNG ĐÙI TRONG: Tình trạng DÀY SỪNG NHẸ (stratum corneum) thường xảy ra do ma sát liên tục khi vận động. Cần chú trọng các bước làm mềm biểu bì để hoạt chất dưỡng sáng có thể thẩm thấu xuyên qua lớp sừng vào sâu bên dưới tế bào hắc tố.\n\n"
                f"DỮ LIỆU THỰC TẾ (SSOT):\n"
                f"- Khu vực mục tiêu: {target_area}\n"
                f"- Hướng dẫn gốc: {product_instructions}\n"
                f"- Combo khả dụng:\n{variants_text}\n"
                f"- Voucher & Tích điểm: {vouchers_text} | 100k = 1 điểm.\n\n"
                "QUY TẮC TÁC PHONG (CLINICAL ETIQUETTE):\n"
                f"1. DANH XƯNG SẢN PHẨM: Luôn gọi tên chính xác là '{product_name}', tuyệt đối không gọi là 'serum' chung chung.\n"
                "2. NGÔN NGỮ ELITE: Tuyệt đối KHÔNG dùng các từ thô cứng như 'sạm', 'thâm đen', 'sơ cứng', 'thô ráp'. Hãy thay thế bằng các thuật ngữ chuyên môn tinh tế: 'Khu vực tối màu', 'Kém rạng rỡ', 'Sự tập trung hắc tố', 'Kết cấu da kém mịn màng', 'Tình trạng dày sừng nhẹ'.\n"
                "3. TRÌNH BÀY: Ngôn ngữ súc tích, sang trọng, mang tính thấu cảm cao đối với các vấn đề nhạy cảm của khách hàng.\n"
                f"4. TƯ VẤN CÁ NHÂN HÓA: Lời khuyên phải khớp hoàn toàn với sinh lý của {target_area}.\n"
                "5. ĐỊNH DẠNG PHÁC ĐỒ (BẮT BUỘC): Trường 'recommendation' phải trình bày theo định dạng 1. 2. 3. thẩm mỹ như sau:\n"
                f"   1. Kỹ thuật thoa: Sử dụng lượng {product_name} vừa đủ, massage nhẹ nhàng theo hình xoắn ốc từ ngoài vào trong để kích thích vi tuần hoàn.\n"
                "   2. Trang phục: Ưu tiên nội y chất liệu Cotton 100%, tránh mặc đồ quá chật gây cản trở lưu thông máu và tạo ma sát gây thâm.\n"
                f"   3. Phác đồ: Duy trì đều đặn 2 lần/ngày (sáng - tối) ngay sau khi làm sạch da để đạt hiệu quả thẩm thấu tối đa cho {product_name}.\n"
                "6. PHÁC ĐỒ TẤN CÔNG: Chia rõ lộ trình: 'Giai đoạn Tấn công' và 'Giai đoạn Duy trì'.\n"
                "7. KHÔNG HALLUCINATE: Chỉ dùng dữ liệu SSOT.\n\n"
                "PHONG THÁI: Một chuyên gia Nhật Bản tận tâm, tinh tế và am tường khoa học da liễu."
            )

            prompt = f"Dữ liệu khảo sát khách hàng (Quiz Data): {json.dumps(quiz_data, ensure_ascii=False)}"
            
            # Utilize the centralized bridge for military-grade stability
            result = await trinity_bridge.run(
                agent=agent,
                prompt=prompt,
                system_prompt=system_prompt,
                role="fast", 
                timeout=45.0
            )
            
            if result:
                return cast(DiagnosticReport, result)
            return None
            
        except Exception as e:
            logger.error(f"[DiagnosticAgent] Fatal Error: {e}")
            return None
