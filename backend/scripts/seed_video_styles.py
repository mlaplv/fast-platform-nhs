import os
import sys
from pathlib import Path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path: sys.path.insert(0, project_root)

import asyncio
from sqlalchemy import select, delete
from dotenv import load_dotenv

load_dotenv(os.path.realpath(os.path.join(os.path.dirname(__file__), "../../.env")))

from backend.database import async_session_maker
from backend.database.models.video_marketing import VideoScriptStyle

INITIAL_STYLES = [
    {
        "id": "tiktok_drama",
        "name": "Drama Kịch Tính TikTok (Chuyển Đổi Cao)",
        "platform": "TikTok",
        "hook_template": "Phát biểu ngược đời hoặc phủ nhận niềm tin cũ của khách hàng trong 3s đầu: 'Ngừng bôi kem chống nắng ngay nếu da bạn đang mụn bọc!', hoặc tạo cảnh cãi vã oái oăm về tình huống sử dụng sản phẩm.",
        "style_instruction": "Tạo kịch tính cực cao, nhịp dựng cực nhanh (1.5 - 3 giây mỗi phân cảnh). Lời thoại (Voiceover) mang tính đối thoại trực diện, có xung đột nhẹ ở phần đầu, sau đó giải quyết vấn đề bằng sản phẩm. Sử dụng hiệu ứng âm thanh dồn dập (Dramatic swoosh, vinyl scratch, record scratch). Kêu gọi hành động (CTA) khẩn cấp với số lượng có hạn.",
        "is_active": True
    },
    {
        "id": "reviewer_experience",
        "name": "Trải Nghiệm Thực Tế (E-E-A-T Reviewer)",
        "platform": "TikTok/Reels",
        "hook_template": "Cận cảnh trải nghiệm thực tế với biểu cảm sửng sốt: 'U là trời, bỏ túi ngay em này nếu không muốn hối hận cả đời!', hoặc đập hộp trực quan không cắt ghép.",
        "style_instruction": "Tập trung vào tính khách quan và khoa học (E-E-A-T). Lời thoại như một người bạn thân chia sẻ bí kíp, giọng điệu tự nhiên, chân thành. Nêu rõ 3 điểm vượt trội của sản phẩm và chỉ ra 1 nhược điểm nhỏ không đáng kể để tăng độ uy tín. Visual cận cảnh chất kem/chi tiết kỹ thuật, hiệu ứng âm thanh lofi nhẹ nhàng.",
        "is_active": True
    },
    {
        "id": "pain_point_solve",
        "name": "Giải Quyết Nỗi Đau Sâu Sắc (PAS Framework)",
        "platform": "Shorts/Reels",
        "hook_template": "Đánh thẳng vào nỗi ám ảnh tồi tệ nhất của khách hàng kèm câu hỏi tu từ: 'Mặt sần sùi mụn thâm làm bạn mất tự tin trước đám đông đúng không?', hiển thị hình ảnh so sánh cực kỳ tương phản.",
        "style_instruction": "Áp dụng công thức PAS (Problem - Agitate - Solve). 30% thời lượng đầu đồng cảm sâu sắc với nỗi sợ hãi hoặc đau đớn của khách hàng. 40% tiếp theo giới thiệu cơ chế hoạt động khoa học của sản phẩm (USP vượt trội so với đối thủ). 30% cuối đưa ra bằng chứng trước/sau (Before/After) thuyết phục và CTA ưu đãi giới hạn.",
        "is_active": True
    },
    {
        "id": "unboxing_asmr",
        "name": "Đập Hộp ASMR Sang Trọng",
        "platform": "TikTok/Shorts",
        "hook_template": "Tập trung 100% vào âm thanh vật lý chất lượng cao (tiếng bóc seal, tiếng cạy nắp sản phẩm thủy tinh kịch tính) trong 3s đầu không nhạc nền.",
        "style_instruction": "Kịch bản đậm chất nghệ thuật và tối giản. Không dùng nhiều lời thoại, tập trung mô tả chi tiết tiếng động vật lý (ASMR) sắc nét. Visual cực kỳ sạch sẽ, tinh tế, sử dụng tone màu pastel/dark sang trọng. Phụ đề xuất hiện chậm rãi, thanh lịch. Nhạc nền lofi/ambient thư thái.",
        "is_active": True
    },
    {
        "id": "product_closeup",
        "name": "Quảng Cáo Cận Cảnh (Không Mặt / Chỉ Cận Cảnh Da & Tay)",
        "platform": "TikTok/Reels/Shorts",
        "hook_template": "Cận cảnh khoảnh khắc ấn tượng nhất của sản phẩm tác động lên da (nhấn đầu xịt sương mịn, giọt serum chảy chậm trên vùng da xỉn màu...) gây kích thích thị giác cực mạnh trong 3 giây đầu.",
        "style_instruction": "Tập trung 100% vào sản phẩm, kết cấu và hiệu quả sử dụng thực tế trên da. KỊCH BẢN KHÔNG ĐƯỢC XUẤT HIỆN GƯƠNG MẶT người, chỉ được phép sử dụng bàn tay thao tác mở nắp, nhấn vòi, và thoa nhẹ chất kem/serum lên vùng da nhạy cảm cần chăm sóc (như nách, bẹn, cánh tay). Visual sử dụng góc quay siêu cận (Extreme Close-up), quay chậm (Slow Motion) từng khoảnh khắc chất kem thẩm thấu nhanh chóng, không để lại vết bết dính. Lời thoại (Voiceover) ngắn gọn, giọng đọc nhẹ nhàng, mô tả chân thực cảm giác mát mịn, khô thoáng và sự thay đổi độ sáng khỏe của làn da tức thì. Nhạc nền hiện đại, êm dịu, tinh tế.",
        "is_active": True
    },
    {
        "id": "closeup_usage_guide",
        "name": "Hướng Dẫn Sử Dụng Cận Cảnh (Closeup Product Guide)",
        "platform": "TikTok/Reels/Shorts",
        "hook_template": "Cận cảnh thao tác bôi/thoa sản phẩm lên vùng da thực tế: 'Dùng sản phẩm này bao lâu rồi nhưng bạn đã chắc bôi đúng cách chưa?', hoặc 'Hướng dẫn dùng sản phẩm chuẩn spa tại nhà để đạt hiệu quả gấp 3 lần!'",
        "style_instruction": "Tập trung vào trải nghiệm hướng dẫn sử dụng sản phẩm cận cảnh và trực quan. Visual mô tả hành động bôi, thoa hoặc massage nhẹ nhàng chất kem, serum, dung dịch lên vùng da/tay. Lưu ý đặc biệt: để bảo vệ tính văn minh và thẩm mỹ của video quảng cáo, đối với các vùng da nhạy cảm (như vùng bikini, nách, bẹn), kịch bản tuyệt đối KHÔNG ĐƯỢC chỉ định quay vùng nhạy cảm thực tế, mà bắt buộc phải hướng dẫn thao tác tượng trưng trên vùng mu bàn tay (ví dụ: bôi thử và massage nhẹ nhàng trên mu bàn tay để mô tả kết cấu, độ thẩm thấu và cách thoa). Lời thoại (Voiceover) chi tiết, hướng dẫn từng bước rõ ràng, khoa học, chỉ ra tần suất và lưu ý khi sử dụng. Nhạc nền lofi nhẹ nhàng, tạo cảm giác thư giãn, uy tín và chuyên nghiệp.",
        "is_active": True
    },
    {
        "id": "scientific_ingredients",
        "name": "Show Thành Phần Khoa Học & Tính Năng Chuyên Nghiệp (Brand Spotlight)",
        "platform": "TikTok/Reels/YouTube",
        "hook_template": "Cận cảnh kết cấu zoom cực cận (Extreme Close-up) hoặc hiệu ứng hoạt cảnh tách phân tử thành phần: 'Đây là lý do tại sao [Thành phần A] lại có thể cứu rỗi làn da của bạn chỉ sau 7 ngày!', hoặc hình ảnh trực quan mô tả tính năng nổi bật của sản phẩm.",
        "style_instruction": "Tập trung giới thiệu các thành phần cốt lõi (key ingredients) và công nghệ/tính năng độc quyền của sản phẩm theo phong cách chuyên nghiệp của các thương hiệu lớn toàn cầu. Visual kết hợp mô tả góc quay cận cảnh sang trọng, ánh sáng studio chuẩn High-Key, cận cảnh chất kem/serum dưới dạng các phân tử hoặc giọt dưỡng chất cô đặc rơi chậm. Có thể mô tả các biểu đồ khoa học, mô hình phân tử 3D hoặc cơ chế tác động trực quan lên lớp biểu bì da để làm nổi bật tính chuyên sâu. Lời thoại (Voiceover) súc tích, chuyên nghiệp, sử dụng ngôn ngữ khoa học đáng tin cậy nhưng dễ hiểu, nhấn mạnh USP độc quyền của sản phẩm so với thị trường. Nhạc nền hiện đại, mang hơi hướng công nghệ (corporate tech hoặc futuristic electronic) nhưng vẫn tinh tế, sang trọng.",
        "is_active": True
    },
    {
        "id": "youtube_widescreen_review",
        "name": "Đánh Giá Chi Tiết Chuyên Sâu (YouTube Widescreen)",
        "platform": "YouTube",
        "hook_template": "Đặt vấn đề thời sự hoặc nhu cầu cấp thiết của thị trường và tóm tắt nhanh 3 bài học đắt giá người xem sẽ nhận được ở video trong 10s đầu.",
        "style_instruction": "Kịch bản chuyên sâu chuẩn định dạng ngang 16:9. Nhịp điệu phân tích vừa phải, chắc chắn (4 - 6 giây mỗi cảnh). Lời thoại cung cấp thông tin giá trị cao, giải thích nguyên lý khoa học đằng sau sản phẩm. Phân tích đối thủ cạnh tranh một cách khách quan để làm nổi bật USP của sản phẩm ta. CTA đăng ký kênh và nhấp link mua hàng.",
        "is_active": True
    }
]

async def seed_video_styles():
    print("🌟 Starting Video Script Styles Seeding...")
    async with async_session_maker() as session:
        try:
            # 1. Add or Update styles (Upsert logic to avoid FK violation)
            print(f"📦 Seeding/Updating {len(INITIAL_STYLES)} video styles...")
            for style_data in INITIAL_STYLES:
                stmt = select(VideoScriptStyle).where(VideoScriptStyle.id == style_data["id"])
                res = await session.execute(stmt)
                style_db = res.scalar_one_or_none()
                
                if style_db:
                    print(f"  🔄 Updating style: {style_data['id']}")
                    style_db.name = style_data["name"]
                    style_db.platform = style_data["platform"]
                    style_db.hook_template = style_data["hook_template"]
                    style_db.style_instruction = style_data["style_instruction"]
                    style_db.is_active = style_data["is_active"]
                else:
                    print(f"  🆕 Inserting new style: {style_data['id']}")
                    style_db = VideoScriptStyle(
                        id=style_data["id"],
                        name=style_data["name"],
                        platform=style_data["platform"],
                        hook_template=style_data["hook_template"],
                        style_instruction=style_data["style_instruction"],
                        is_active=style_data["is_active"]
                    )
                    session.add(style_db)
            
            await session.commit()
            print("✨ Successfully seeded Video Script Styles into database!")
            
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed_video_styles())
